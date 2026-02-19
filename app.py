import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date
import time

# --- إعداد الصفحة (يجب أن يكون أول سطر) ---
st.set_page_config(page_title="نظام المهام الذكي", page_icon="🚀", layout="wide")

# --- CSS متقدم لواجهة احترافية (Premium UI) ---
st.markdown("""
    <style>
    /* استيراد خط القاهرة العصري */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
    
    /* إخفاء قوائم Streamlit الافتراضية لمظهر تطبيق حقيقي */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ضبط الخط والاتجاه */
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    /* تصميم بطاقات الإحصائيات (Metrics Cards) */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 20px 25px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.03);
        border-right: 5px solid #6366F1; /* خط جانبي ملون يعطي طابعاً احترافياً */
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.08);
    }
    div[data-testid="stMetricValue"] {
        color: #4F46E5 !important;
        font-weight: 800 !important;
        font-size: 2.5rem !important;
    }
    
    /* تصميم الأزرار الاحترافية (Gradients & Shadows) */
    .stButton > button {
        background: linear-gradient(90deg, #6366F1 0%, #8B5CF6 100%);
        color: white !important;
        border-radius: 30px;
        border: none;
        padding: 10px 25px;
        font-weight: 700;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.03);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
    }
    
    /* تصميم الحقول والنصوص */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        padding: 12px;
        background-color: #F9FAFB;
        text-align: right;
    }
    .stTextInput>div>div>input:focus {
        border-color: #6366F1;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }
    
    /* تحسين مظهر التبويبات (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    /* فواصل ناعمة */
    hr {
        border-color: #E5E7EB;
        margin: 2.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('tasks_app.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, group_name TEXT, points INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT, task_type TEXT, points_per_unit INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_tasks (user_id INTEGER, task_id INTEGER, units_completed INTEGER DEFAULT 0, is_completed BOOLEAN, date TEXT)''')
    
    c.execute("SELECT * FROM users WHERE role='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role, group_name) VALUES ('admin', 'admin123', 'admin', 'الإدارة')")
    conn.commit()
    return conn

conn = init_db()

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': '', 'role': '', 'user_id': None, 'group_name': ''})

# --- صفحة تسجيل الدخول ---
def login():
    # تصميم صندوق تسجيل الدخول في المنتصف
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True) # مسافة علوية
        st.markdown("<h1 style='text-align: center; color: #1F2937;'>🚀 منصة إنجاز</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6B7280; margin-bottom: 30px;'>سجل دخولك لمتابعة مهامك وتحقيق أهدافك</p>", unsafe_allow_html=True)
        
        username = st.text_input("👤 اسم المستخدم")
        password = st.text_input("🔒 كلمة المرور", type="password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("تسجيل الدخول", use_container_width=True):
            c = conn.cursor()
            c.execute("SELECT id, role, group_name FROM users WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
            if user:
                st.session_state.update({'logged_in': True, 'username': username, 'user_id': user[0], 'role': user[1], 'group_name': user[2]})
                st.rerun()
            else:
                st.error("⚠️ بيانات الدخول غير صحيحة، يرجى المحاولة مرة أخرى.")

# --- واجهة المدير ---
def admin_dashboard():
    st.markdown("<h1>👑 لوحة تحكم الإدارة</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280;'>أهلاً بك.. من هنا يمكنك إدارة النظام بالكامل</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 نظرة عامة والتقارير", "📝 إدارة المهام", "👥 إضافة مستخدمين"])
    
    with tab1:
        st.subheader("مؤشرات الأداء")
        df_users = pd.read_sql_query("SELECT username, group_name, points FROM users WHERE role='user'", conn)
        
        if not df_users.empty:
            col1, col2 = st.columns(2)
            with col1:
                # رسم بياني احترافي بخلفية شفافة
                fig_users = px.bar(df_users, x='username', y='points', color='username', title="النقاط الفردية", text='points')
                fig_users.update_traces(textposition='outside', textfont_size=14)
                fig_users.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                st.plotly_chart(fig_users, use_container_width=True)
            with col2:
                df_groups = df_users.groupby('group_name')['points'].sum().reset_index()
                fig_groups = px.pie(df_groups, names='group_name', values='points', title="أداء المجموعات", hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_groups.update_traces(textposition='inside', textinfo='percent+label')
                fig_groups.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_groups, use_container_width=True)
        else:
            st.info("💡 لا يوجد بيانات لعرضها حتى الآن. أضف مستخدمين ليبدأ التفاعل!")

    with tab2:
        with st.container():
            st.subheader("إضافة مهمة جديدة للمنصة")
            title = st.text_input("اسم المهمة (مثال: قراءة 10 صفحات، تمرين رياضي)")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                task_type = st.selectbox("نوع المهمة", ["كمّي (يحتسب نقاط متعددة حسب الإدخال)", "عادي (إنجاز بنعم/لا)"])
            with col_t2:
                points = st.number_input("النقاط المكتسبة لكل وحدة", min_value=1, value=5)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ حفظ واعتماد المهمة"):
                t_type = 'quantitative' if task_type.startswith("كمّي") else 'boolean'
                c = conn.cursor()
                c.execute("INSERT INTO tasks (title, task_type, points_per_unit) VALUES (?, ?, ?)", (title, t_type, points))
                conn.commit()
                st.success("تمت إضافة المهمة بنجاح وتعميمها على الجميع! 🎉")

    with tab3:
        st.subheader("تسجيل مستخدم جديد في النظام")
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            new_user = st.text_input("اسم المستخدم")
            new_group = st.text_input("اسم الفريق / المجموعة")
        with col_u2:
            new_pass = st.text_input("كلمة المرور")
            st.markdown("<br><br>", unsafe_allow_html=True) # لضبط المحاذاة
            if st.button("👤 إنشاء الحساب", use_container_width=True):
                c = conn.cursor()
                c.execute("INSERT INTO users (username, password, role, group_name) VALUES (?, ?, 'user', ?)", (new_user, new_pass, new_group))
                conn.commit()
                st.success(f"تم إنشاء حساب للمستخدم {new_user} بنجاح! ✅")

# --- واجهة المستخدم ---
def user_dashboard():
    # قسم الترحيب العلوي
    col_welcome, col_logout = st.columns([8, 1])
    with col_welcome:
        st.markdown(f"<h1>👋 مرحباً، <span style='color: #6366F1;'>{st.session_state['username']}</span></h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #6B7280; font-size: 1.1rem;'>عضو في فريق: <b>{st.session_state['group_name']}</b></p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # قسم البطاقات (Metrics)
    c = conn.cursor()
    c.execute("SELECT points FROM users WHERE id=?", (st.session_state['user_id'],))
    my_points = c.fetchone()[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="إجمالي نقاطي 🌟", value=my_points)
    with col2:
        c.execute("SELECT SUM(points) FROM users WHERE group_name=?", (st.session_state['group_name'],))
        group_points = c.fetchone()[0] or 0
        st.metric(label="نقاط الفريق 🤝", value=group_points)
    with col3:
        st.metric(label="تاريخ اليوم 📅", value=str(date.today()))
    
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    st.subheader("📋 المهام المطلوبة اليوم")
    
    tasks_df = pd.read_sql_query("SELECT * FROM tasks", conn)
    today = str(date.today())
    
    if tasks_df.empty:
        st.info("لا توجد مهام مسجلة حالياً، استمتع بيومك! ☕")
        
    for index, row in tasks_df.iterrows():
        # صندوق المهمة
        with st.container():
            st.markdown(f"### 📌 {row['title']}")
            st.markdown(f"<span style='color: #10B981; font-weight: bold;'>+{row['points_per_unit']} نقطة</span> للإنجاز الواحد", unsafe_allow_html=True)
            
            c.execute("SELECT * FROM user_tasks WHERE user_id=? AND task_id=? AND date=?", (st.session_state['user_id'], row['id'], today))
            completed_task = c.fetchone()
            
            if completed_task and completed_task[3]:
                st.success(f"أنجزتها اليوم بنجاح! ✓ (سجلت: {completed_task[2]} إنجاز)")
            else:
                col_input, col_btn = st.columns([2, 1])
                with col_input:
                    if row['task_type'] == 'quantitative':
                        units = st.number_input("الكمية المنجزة (مثال: عدد الصفحات)", min_value=1, value=1, key=f"unit_{row['id']}")
                    else:
                        units = 1 
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("اعتماد الإنجاز ✔️", key=f"btn_{row['id']}", use_container_width=True):
                        earned_points = units * row['points_per_unit']
                        c.execute("INSERT INTO user_tasks (user_id, task_id, units_completed, is_completed, date) VALUES (?, ?, ?, ?, ?)", 
                                  (st.session_state['user_id'], row['id'], units, True, today))
                        c.execute("UPDATE users SET points = points + ? WHERE id=?", (earned_points, st.session_state['user_id']))
                        conn.commit()
                        
                        st.toast(f'عمل رائع! كسبت {earned_points} نقطة 🔥', icon='🚀')
                        st.balloons()
                        time.sleep(1.5)
                        st.rerun()
            st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

# --- التوجيه الرئيسي للتطبيق ---
if not st.session_state['logged_in']:
    login()
else:
    # شريط علوي لتسجيل الخروج
    col_space, col_exit = st.columns([10, 1])
    with col_exit:
        if st.button("خروج 🚪"):
            st.session_state.clear()
            st.rerun()
            
    if st.session_state['role'] == 'admin':
        admin_dashboard()
    else:
        user_dashboard()
