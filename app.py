import streamlit as st
import pandas as pd
import re
import psycopg2

VALID_USERNAME = "admin"
VALID_PASSWORD = "1234"



def get_connection():
    return psycopg2.connect(
        host="aws-0-eu-north-1.pooler.supabase.com",
        database="postgres",
        user="postgres.cvflgatlyuenklwnrgwt",
        password="BIO_YOU_228",
        port=6543
    )

def register_student(name, phone, parent, stage, group):
    conn = get_connection()
    cursor = conn.cursor()

    # Get StageID
    cursor.execute("SELECT StageID FROM Stages WHERE StageName = %s", (stage,))
    stage_id = cursor.fetchone()[0]

    # Get GroupID
    cursor.execute("""
        SELECT g.GroupID 
        FROM Groups g 
        JOIN Stages s ON g.Stage_id = s.StageID 
        WHERE g.GroupName = %s AND s.StageName = %s
    """, (group, stage))
    group_id = cursor.fetchone()[0]

    # تسجيل الطالب مباشرة
    cursor.execute("""
        INSERT INTO Students (FullName, PhoneNumber, ParentPhone, StageID, GroupID)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, phone, parent, stage_id, group_id))

    conn.commit()
    conn.close()

def load_students():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT s.StudentID, s.FullName AS الاسم, s.PhoneNumber AS 'رقم الطالب',
               s.ParentPhone AS 'رقم ولي الأمر', st.StageName AS المرحلة,
               g.GroupName AS المجموعة, s.AccessCode AS 'كود الدخول'
        FROM Students s
        JOIN Stages st ON s.StageID = st.StageID
        JOIN Groups g ON s.GroupID = g.GroupID
    """, conn)
    conn.close()
    return df

def get_groups_by_stage(stage_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.GroupName 
        FROM Groups g
        JOIN Stages s ON g.Stage_id = s.StageID
        WHERE s.StageName = %s
    """, (stage_name,))
    groups = [row[0] for row in cursor.fetchall()]
    conn.close()
    return groups


# إعداد الصفحة
st.set_page_config(page_title="تسجيل طلاب الأحياء", layout="centered")
st.title("📚 تسجيل طلاب الأحياء")

# حالة الدخول الخاصة بعرض الطلاب فقط
if "view_logged_in" not in st.session_state:
    st.session_state.view_logged_in = False

# Tabs
tab1, tab2 = st.tabs(["➕ تسجيل طالب جديد", "📋 عرض الطلاب"])

# ✅ تبويب تسجيل طالب
with tab1:
    st.subheader("📝 سجل طالب جديد")

    name = st.text_input("اسم الطالب")
    phone = st.text_input("رقم التليفون")
    parent = st.text_input("رقم ولي الأمر")
    stage = st.selectbox("المرحلة", ["الصف الأول", "الصف الثاني", "الصف الثالث"])

    group = None
    group_options = []

    if stage:
        group_options = get_groups_by_stage(stage)
        if group_options:
            group = st.selectbox("المجموعة", group_options)
        else:
            st.warning("❗ لا توجد مجموعات متاحة لهذه المرحلة.")
            group = None

    if st.button("تسجيل الطالب"):
        if not name.strip():
             st.error("❌ يرجى إدخال اسم الطالب.")
        elif not re.match(r'^[\u0600-\u06FF\s]+$', name):
             st.error("❌ الاسم يجب أن يحتوي على حروف عربية فقط.")
        elif len(name.strip().split()) < 3:
             st.error("❌ الاسم يجب أن يكون ثلاثيًا على الأقل (مثال: محمد أحمد علي).")

        elif not phone.isdigit() or len(phone) != 11:
            st.error("❌ رقم التليفون يجب أن يحتوي على 11 رقم.")
        elif not parent.isdigit() or len(parent) != 11:
            st.error("❌ رقم ولي الأمر يجب أن يحتوي على 11 رقم.")
        elif not stage or not group:
            st.error("❌ يرجى اختيار المرحلة والمجموعة.")
        else:
            try:
                register_student(name, phone, parent, stage, group)
                st.success("✅ تم تسجيل الطالب بنجاح.")
            except Exception as e:
                st.error(f"❌ حدث خطأ أثناء التسجيل: {e}")

# ✅ تبويب عرض الطلاب (بداخله تسجيل دخول داخلي)
with tab2:
    if not st.session_state.view_logged_in:
        st.subheader("🔐 تسجيل الدخول لعرض الطلاب")
        username = st.text_input("اسم المستخدم", key="view_user")
        password = st.text_input("كلمة المرور", type="password", key="view_pass")

        if st.button("تسجيل الدخول", key="view_login_btn"):
            if username == VALID_USERNAME and password == VALID_PASSWORD:
                st.session_state.view_logged_in = True
                st.success("✅ تم تسجيل الدخول بنجاح لعرض الطلاب.")
            else:
                st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة.")
    else:
        st.subheader("📋 جميع الطلاب المسجلين")
        df = load_students()

        search = st.text_input("🔍 ابحث بالاسم أو كود الدخول:")
        if search:
            df = df[df["الاسم"].str.contains(search, na=False) | df["كود الدخول"].str.contains(search, na=False)]

        st.dataframe(df, use_container_width=True)

        if st.download_button("📥 تحميل كـ Excel", df.to_csv(index=False).encode('utf-8'), file_name="الطلاب.csv"):
            st.success("✅ تم تنزيل الملف.")
