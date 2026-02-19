import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date
import time

# --- إعداد الصفحة ---
st.set_page_config(page_title="نظام متابعة المهام", page_icon="🎯", layout="wide")

# --- تصميم الواجهة (CSS) ودعم اللغة العربية ---
st.markdown("""
    <style>
    /* استيراد خط تجوال العصري */
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
    
    /* تطبيق الخط ودعم الاتجاه من اليمين لليسار */
    html, body, [class*="css"] {
        font-family: 'Tajawal', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    /* إصلاح اتجاه بعض العناصر في Streamlit لتناسب العربية */
    .stTextInput > div > div > input, .stNumberInput > div > div > input {
        text-align: right;
    }
    .stSelectbox > div > div > div {
        direction: rtl;
        text-align: right;
    }
    
    /* تحسين شكل الأزرار وتأثير التمرير */
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        font-weight: bold;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }

    /* تحسين كروت الإحصائيات (Metrics) */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #f0f2f6;
        text-align: center;
    }
    div[data-testid="stMetricValue"] {
        color: #4F46E5; /* لون مميز للأرقام */
    }
    
    /* تنسيق الفواصل */
    hr {
        margin-top: 2rem;
        margin-bottom: 2rem;
        border-color: #e5e7eb;
    }
    </style>
""", unsafe_allow_html=True)

# --- إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('tasks_app.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, group_name TEXT, points INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks 
                 (id INTEGER PRIMARY KEY, title TEXT, task_type TEXT, points_per_unit INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_tasks 
                 (user_id INTEGER, task_id INTEGER, units_completed INTEGER DEFAULT 0, is_completed BOOLEAN, date TEXT)''')
    
    c.execute("SELECT * FROM users WHERE role='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role, group_name) VALUES ('admin', 'admin123', 'admin', 'الإدارة')")
        
    conn.commit()
    return conn

conn = init_db()

# --- نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': '', 'role': '', 'user_id': None, 'group_name': ''})

def login():
    st.title("🎯 مرحباً بك في نظام إنجاز المهام")
    st.markdown("يرجى تسجيل الدخول للمتابعة")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            username = st.text_input("اسم المستخدم")
            password = st.text_input("كلمة المرور", type="password")
            if st.button("دخول", use_container_width=True):
                c = conn.cursor()
                c.execute("SELECT id, role, group_name FROM users WHERE username=? AND password=?", (username, password))
                user = c.fetchone()
                if user:
                    st.session_state.update({'logged_in': True, 'username': username, 'user_id': user[0], 'role': user[1], 'group_name': user[2]})
                    st.rerun()
                else:
                    st.error("بيانات الدخول غير صحيحة")

# --- واجهة المدير (Admin) ---
def admin_dashboard():
    st.title("⚙️ لوحة تحكم المسؤول")
    
    tab1, tab2, tab3 = st.tabs(["📝 إضافة مهام", "👥 إدارة المستخدمين", "📊 التقدم العام"])
    
    with tab1:
        st.subheader("إضافة مهمة جديدة")
        title = st.text_input("اسم المهمة (مثال: قراءة كتاب، حضور اجتماع)")
        task_type = st.selectbox("نوع المهمة", ["كمّي (نقاط تتضاعف حسب الإنجاز)", "عادي (مهمة تنجز بنعم/لا)"])
        points = st.number_input("النقاط المكتسبة (لكل وحدة إنجاز أو للمهمة كاملة)", min_value=1, value=1)
        
        if st.button("حفظ المهمة"):
            t_type = 'quantitative' if task_type.startswith("كمّي") else 'boolean'
            c = conn.cursor()
            c.execute("INSERT INTO tasks (title, task_type, points_per_unit) VALUES (?, ?, ?)", (title, t_type, points))
            conn.commit()
            st.success("تمت إضافة المهمة بنجاح! 🎉")

    with tab2:
        st.subheader("إضافة مستخدم جديد")
        new_user = st.text_input("اسم المستخدم الجديد")
        new_pass = st.text_input("كلمة مرور المستخدم")
        new_group = st.text_input("اسم المجموعة (مثال: فريق التسويق، المجموعة أ)")
        if st.button("إضافة المستخدم"):
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password, role, group_name) VALUES (?, ?, 'user', ?)", (new_user, new_pass, new_group))
            conn.commit()
            st.success("تم إضافة المستخدم بنجاح! ✅")

    with tab3:
        st.subheader("مراقبة أداء المجموعات والأفراد")
        df_users = pd.read_sql_query("SELECT username, group_name, points FROM users WHERE role='user'", conn)
        
        if not df_users.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig_users = px.bar(df_users, x='username', y='points', color='username', title="النقاط لكل فرد", template="plotly_white")
                st.plotly_chart(fig_users, use_container_width=True)
            with col2:
                df_groups = df_users.groupby('group_name')['points'].sum().reset_index()
                # تحويل الرسم البياني للمجموعات إلى دائري (Pie Chart) ليكون عصرياً أكثر
                fig_groups = px.pie(df_groups, names='group_name', values='points', title="مساهمة المجموعات في إجمالي النقاط", hole=0.4, template="plotly_white")
                st.plotly_chart(fig_groups, use_container_width=True)
        else:
            st.info("لا يوجد بيانات لعرضها حتى الآن. أضف مستخدمين ليبدأ التنافس!")

# --- واجهة المستخدم (User) ---
def user_dashboard():
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.title(f"👋 مرحباً، {st.session_state['username']}")
        st.caption(f"فريق: {st.session_state['group_name']}")
    
    # عرض الإحصائيات في كروت
    c = conn.cursor()
    c.execute("SELECT points FROM users WHERE id=?", (st.session_state['user_id'],))
    my_points = c.fetchone()[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="إجمالي نقاطي 🌟", value=my_points)
    with col2:
        c.execute("SELECT SUM(points) FROM users WHERE group_name=?", (st.session_state['group_name'],))
        group_points = c.fetchone()[0] or 0
        st.metric(label="نقاط مجموعتي 🤝", value=group_points)
    with col3:
        st.metric(label="تاريخ اليوم 📅", value=str(date.today()))
    
    st.divider()
    st.subheader("📋 مهام اليوم")
    
    tasks_df = pd.read_sql_query("SELECT * FROM tasks", conn)
    today = str(date.today())
    
    if tasks_df.empty:
        st.info("لا توجد مهام مسجلة حالياً.")
        
    for index, row in tasks_df.iterrows():
        st.markdown(f"**{row['title']}** (النقاط: {row['points_per_unit']} لكل إنجاز)")
        
        c.execute("SELECT * FROM user_tasks WHERE user_id=? AND task_id=? AND date=?", (st.session_state['user_id'], row['id'], today))
        completed_task = c.fetchone()
        
        if completed_task and completed_task[3]:
            st.success(f"تم الإنجاز اليوم! ✓ (سجلت: {completed_task[2]} وحدة)")
        else:
            col_input, col_btn = st.columns([3, 1])
            with col_input:
                if row['task_type'] == 'quantitative':
                    units = st.number_input(f"كم وحدة/صفحة أنجزت؟", min_value=1, value=1, key=f"unit_{row['id']}")
                else:
                    units = 1 
            with col_btn:
                # محاذاة الزر للأسفل
                st.write("")
                st.write("")
                if st.button("تسجيل الإنجاز ✔️", key=f"btn_{row['id']}", use_container_width=True):
                    earned_points = units * row['points_per_unit']
                    c.execute("INSERT INTO user_tasks (user_id, task_id, units_completed, is_completed, date) VALUES (?, ?, ?, ?, ?)", 
                              (st.session_state['user_id'], row['id'], units, True, today))
                    c.execute("UPDATE users SET points = points + ? WHERE id=?", (earned_points, st.session_state['user_id']))
                    conn.commit()
                    
                    # نظام المكافآت التفاعلية
                    st.toast(f'بطل! أضفت {earned_points} نقطة لرصيدك 👏', icon='🎉')
                    st.balloons()
                    time.sleep(1.5)
                    st.rerun()
        st.write("---")

# --- التوجيه الرئيسي ---
if not st.session_state['logged_in']:
    login()
else:
    # زر تسجيل الخروج في الأعلى يساراً
    col1, col2 = st.columns([10, 1])
    with col2:
        if st.button("خروج 🚪"):
            st.session_state.clear()
            st.rerun()
            
    if st.session_state['role'] == 'admin':
        admin_dashboard()
    else:
        user_dashboard()
