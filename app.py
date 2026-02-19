import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date

# --- إعداد الصفحة ---
st.set_page_config(page_title="نظام متابعة المهام", layout="wide")

# --- إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('tasks_app.db')
    c = conn.cursor()
    
    # جداول النظام
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, group_name TEXT, points INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks 
                 (id INTEGER PRIMARY KEY, title TEXT, task_type TEXT, points_per_unit INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_tasks 
                 (user_id INTEGER, task_id INTEGER, units_completed INTEGER DEFAULT 0, is_completed BOOLEAN, date TEXT)''')
    
    # إضافة حساب مدير افتراضي إذا كانت القاعدة فارغة
    c.execute("SELECT * FROM users WHERE role='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role, group_name) VALUES ('admin', 'admin123', 'admin', 'الإدارة')")
        
    conn.commit()
    return conn

conn = init_db()

# --- نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''
    st.session_state['role'] = ''
    st.session_state['user_id'] = None
    st.session_state['group_name'] = ''

def login():
    st.title("تسجيل الدخول")
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        c = conn.cursor()
        c.execute("SELECT id, role, group_name FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        if user:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.session_state['user_id'] = user[0]
            st.session_state['role'] = user[1]
            st.session_state['group_name'] = user[2]
            st.rerun()
        else:
            st.error("بيانات الدخول غير صحيحة")

# --- واجهة المدير (Admin) ---
def admin_dashboard():
    st.title("لوحة تحكم المسؤول (Admin)")
    
    tab1, tab2, tab3 = st.tabs(["إضافة مهام", "إدارة المستخدمين", "التقدم العام"])
    
    with tab1:
        st.subheader("إضافة مهمة جديدة للجميع")
        title = st.text_input("اسم المهمة (مثال: قراءة كتاب)")
        task_type = st.selectbox("نوع المهمة", ["كمّي (نقاط لكل إنجاز)", "عادي (مهمة تنجز بنعم/لا)"])
        points = st.number_input("النقاط (لكل وحدة إنجاز أو للمهمة كاملة)", min_value=1, value=1)
        
        if st.button("حفظ المهمة"):
            t_type = 'quantitative' if task_type.startswith("كمّي") else 'boolean'
            c = conn.cursor()
            c.execute("INSERT INTO tasks (title, task_type, points_per_unit) VALUES (?, ?, ?)", (title, t_type, points))
            conn.commit()
            st.success("تمت إضافة المهمة بنجاح!")

    with tab2:
        st.subheader("إضافة مستخدم جديد")
        new_user = st.text_input("اسم المستخدم الجديد")
        new_pass = st.text_input("كلمة مرور المستخدم")
        new_group = st.text_input("اسم المجموعة (مثال: فريق التسويق)")
        if st.button("إضافة المستخدم"):
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password, role, group_name) VALUES (?, ?, 'user', ?)", (new_user, new_pass, new_group))
            conn.commit()
            st.success("تمت الإضافة!")

    with tab3:
        st.subheader("مراقبة أداء المجموعات والأفراد")
        df_users = pd.read_sql_query("SELECT username, group_name, points FROM users WHERE role='user'", conn)
        
        if not df_users.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.write("تقدم الأفراد")
                fig_users = px.bar(df_users, x='username', y='points', color='username', title="النقاط لكل فرد")
                st.plotly_chart(fig_users, use_container_width=True)
            with col2:
                st.write("تقدم المجموعات")
                df_groups = df_users.groupby('group_name')['points'].sum().reset_index()
                fig_groups = px.bar(df_groups, x='group_name', y='points', color='group_name', title="مجموع النقاط لكل مجموعة")
                st.plotly_chart(fig_groups, use_container_width=True)
        else:
            st.info("لا يوجد بيانات لعرضها حتى الآن.")

# --- واجهة المستخدم (User) ---
def user_dashboard():
    st.title(f"مرحباً {st.session_state['username']} - ({st.session_state['group_name']})")
    
    # عرض إحصائيات سريعة
    c = conn.cursor()
    c.execute("SELECT points FROM users WHERE id=?", (st.session_state['user_id'],))
    my_points = c.fetchone()[0]
    st.metric(label="إجمالي نقاطي", value=my_points)
    
    st.divider()
    st.subheader("مهام اليوم")
    
    tasks_df = pd.read_sql_query("SELECT * FROM tasks", conn)
    today = str(date.today())
    
    for index, row in tasks_df.iterrows():
        st.write(f"**{row['title']}** (النقاط: {row['points_per_unit']} لكل إنجاز)")
        
        # التحقق مما إذا كان المستخدم قد أنجزها اليوم
        c.execute("SELECT * FROM user_tasks WHERE user_id=? AND task_id=? AND date=?", (st.session_state['user_id'], row['id'], today))
        completed_task = c.fetchone()
        
        if completed_task and completed_task[3]: # is_completed = True
            st.success(f"تم الإنجاز اليوم! ✓ (سجلت: {completed_task[2]} وحدة)")
        else:
            col1, col2 = st.columns([3, 1])
            with col1:
                if row['task_type'] == 'quantitative':
                    units = st.number_input(f"كم أنجزت؟", min_value=1, value=1, key=f"unit_{row['id']}")
                else:
                    units = 1 # المهمة العادية تعتبر وحدة واحدة
            with col2:
                if st.button("تسجيل الإنجاز", key=f"btn_{row['id']}"):
                    earned_points = units * row['points_per_unit']
                    # تحديث إنجاز المهمة
                    c.execute("INSERT INTO user_tasks (user_id, task_id, units_completed, is_completed, date) VALUES (?, ?, ?, ?, ?)", 
                              (st.session_state['user_id'], row['id'], units, True, today))
                    # تحديث نقاط المستخدم
                    c.execute("UPDATE users SET points = points + ? WHERE id=?", (earned_points, st.session_state['user_id']))
                    conn.commit()
                    st.rerun()
        st.write("---")

# --- التوجيه الرئيسي ---
if not st.session_state['logged_in']:
    login()
else:
    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("خروج"):
            st.session_state.clear()
            st.rerun()
            
    if st.session_state['role'] == 'admin':
        admin_dashboard()
    else:
        user_dashboard()