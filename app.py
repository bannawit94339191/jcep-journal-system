import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

# --- 1. ตั้งค่าพื้นฐานและการตกแต่ง CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    /* ปุ่มส่งข้อมูลสีน้ำเงินเข้ม */
    .stButton>button[kind="primary"] { background-color: #1E3A8A; color: white; border-radius: 8px; border: none; }
    /* ปุ่มยกเลิกสีแดง */
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border-radius: 8px; border: none; }
    
    /* ตกแต่ง Sidebar โทนสีฟ้าอ่อน */
    section[data-testid="stSidebar"] { background-color: #F0F9FF; }
    [data-testid="stSidebar"] h3 { color: #1E3A8A; }
    
    /* จัดการโลโก้หน้า User ให้อยู่กึ่งกลาง */
    .user-header-logo {
        display: flex;
        justify-content: center;
        margin-bottom: 25px;
    }

    /* Footer สีเขียวสดใส (ตามใจคุณ!) */
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        background-color: #28a745; color: white; text-align: center; 
        padding: 10px; font-weight: bold; z-index: 100;
    }
    .main { padding-bottom: 80px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Google Services ---
if "google_auth" in st.secrets:
    try:
        info = st.secrets["google_auth"]
        creds = service_account.Credentials.from_service_account_info(info)
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_with_scope = creds.with_scopes(scope)
        client = gspread.authorize(creds_with_scope)
        spreadsheet = client.open("JCEP_Data")
        
        try:
            sheet = spreadsheet.worksheet("Data_2026")
        except:
            sheet = spreadsheet.sheet1
        try:
            admin_sheet = spreadsheet.worksheet("Admin_Users")
        except:
            admin_sheet = None
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")

# --- 3. ระบบจัดการ Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- 4. แถบเมนูด้านข้าง (ลบรูปเก่า เปลี่ยนเป็น Dropdown "หน้าหลัก") ---
with st.sidebar:
    st.markdown("### 🏠 หน้าหลัก")
    # เปลี่ยนจาก Radio เป็น Selectbox (Dropdown) ตามที่คุยกันไว้
    page = st.selectbox(
        "เลือกเมนูการใช้งาน:",
        ["หน้าสำหรับ User", "หน้าสำหรับ Admin"]
    )
    st.markdown("<hr style='border-top: 1px solid #1E3A8A;'>", unsafe_allow_html=True)

# --- 5. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    # ✅ ใส่รูปภาพใหม่แทนที่ข้อความหัวข้อเดิม
    if os.path.exists("coop_logo.png"):
        st.markdown('<div class="user-header-logo">', unsafe_allow_html=True)
        st.image("coop_logo.gif", width=350) # ปรับขนาดรูปได้ตามความเหมาะสม
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.header("📘 ระบบจัดเก็บข้อมูลวารสารสหกิจศึกษาก้าวหน้า")

    try:
        next_id = len(sheet.get_all_values())
    except: next_id = 1

    with st.form("user_form"):
        st.info(f"📍 ลำดับที่: {next_id}")
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้า", ["นาย", "นางสาว", "ผศ.", "รศ.", "ศ."])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")
        
        uni = st.text_input("มหาวิทยาลัย / สถาบัน")
        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")
        org = st.text_input("สังกัด / หน่วยงาน")
        addr = st.text_area("ที่อยู่สำหรับการจัดส่งเอกสาร")
        
        col_tel, col_email = st.columns(2)
        phone = col_tel.text_input("เบอร์โทรศัพท์")
        email_u = col_email.text_input("E-mail")

        st.write("---")
        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        other_detail = st.text_input("รายละเอียดอื่นๆ (ถ้ามี)")

        st.write("---")
        up_file = st.file_uploader("แนบไฟล์ต้นฉบับ (PDF/Word)", type=["pdf", "docx", "doc"])

        st.markdown("<br>", unsafe_allow_html=True)
        btn1, btn2, _ = st.columns([1, 1, 4])
        
        if btn1.form_submit_button("ส่งข้อมูล", type="primary"):
            if up_file:
                final_type = article_type if article_type != "อื่นๆ" else f"อื่นๆ: {other_detail}"
                if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                with open(os.path.join("uploaded_journals", up_file.name), "wb") as f: f.write(up_file.getvalue())
                sheet.append_row([next_id, prefix, f_name, l_name, uni, faculty, major, org, addr, phone, email_u, final_type, up_file.name])
                st.success("🎉 บันทึกข้อมูลสำเร็จ!")
            else: st.error("⚠️ กรุณาแนบไฟล์ก่อนส่ง")
        
        if btn2.form_submit_button("ยกเลิก", type="secondary"):
            st.rerun()

# --- 6. หน้าสำหรับ Admin ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.logged_in:
        st.subheader("🔐 เข้าสู่ระบบผู้ดูแลระบบ")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In", type="primary"):
            if u_in == "bannawit.s" and p_in == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("ข้อมูลไม่ถูกต้อง")
    else:
        if st.button("ออกจากระบบ", type="secondary"): logout()

        st.header("🖥️ แผงควบคุมผู้ดูแลระบบ")
        try:
            df = pd.DataFrame(sheet.get_all_records())
            st.dataframe(df, use_container_width=True)
        except: st.info("ยังไม่มีข้อมูล")

        st.divider()
        st.subheader("📁 จัดการไฟล์วารสาร")
        if os.path.exists("uploaded_journals"):
            files = os.listdir("uploaded_journals")
            if files:
                sel = st.selectbox("เลือกไฟล์ที่ต้องการดาวน์โหลด:", files)
                with open(os.path.join("uploaded_journals", sel), "rb") as f:
                    st.download_button(f"💾 ดาวน์โหลดไฟล์ {sel}", f, file_name=sel)

# --- 7. Footer สีเขียวสดใส ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
