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
    
    /* Footer สีเขียวสดใส */
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
        sheet = spreadsheet.worksheet("Data_2026")
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")

# --- 3. ระบบจัดการ Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- 4. Sidebar (Dropdown คลีนๆ) ---
with st.sidebar:
    st.markdown("### 🏠 หน้าหลัก")
    page = st.selectbox(
        "เลือกเมนูการใช้งาน:",
        ["หน้าสำหรับ User", "หน้าสำหรับ Admin"]
    )
    st.markdown("<hr style='border-top: 1px solid #1E3A8A;'>", unsafe_allow_html=True)

# --- 5. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    # ✅ กลับมาใช้ข้อความหัวเรื่องตามสั่ง (เอารูปแบนเนอร์ออก)
    st.header("📘 ระบบจัดเก็บข้อมูลวารสารสหกิจศึกษาก้าวหน้า")
    st.subheader("Journal of Cooperative Education Progress")

    # ✅ ส่วนโลโก้ OCE ใต้เส้นคั่น + Link ไปเว็บไซต์
    st.write("---")
    if os.path.exists("logo.png"):
        col_img1, col_img2, col_img3 = st.columns([2, 1, 2])
        with col_img2:
            # ใช้ st.link_button เพื่อความเสถียรในการกดลิงก์
            st.image("logo.png", width=120)
            st.link_button("🌐 เว็บไซต์ OCE", "https://oce.rmutk.ac.th")
    
    st.markdown("<br>", unsafe_allow_html=True)

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
        # 12. ประเภทบทความ (Radio ตามภาพ image_eaa67c.png)
        article_type = st.radio("**12. ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        other_detail = st.text_input("โปรดเลือกประเภทบทความ (หากเลือกอื่นๆ)")

        st.write("---")
        # 13. แนบไฟล์ (ตามภาพ image_eaa67c.png)
        up_file = st.file_uploader("13. แนบไฟล์ (PDF/Word)", type=["pdf", "docx", "doc"])

        st.markdown("<br>", unsafe_allow_html=True)
        btn1, btn2, _ = st.columns([1, 1, 4])
        
        if btn1.form_submit_button("ส่งข้อมูล (Send)", type="primary"):
            if up_file:
                final_type = article_type if article_type != "อื่นๆ" else f"อื่นๆ: {other_detail}"
                if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                with open(os.path.join("uploaded_journals", up_file.name), "wb") as f: f.write(up_file.getvalue())
                sheet.append_row([next_id, prefix, f_name, l_name, uni, faculty, major, org, addr, phone, email_u, final_type, up_file.name])
                st.success("🎉 บันทึกข้อมูลเรียบร้อย!")
            else: st.error("⚠️ กรุณาแนบไฟล์ก่อนส่ง")
        
        if btn2.form_submit_button("ยกเลิก (Cancel)", type="secondary"):
            st.rerun()

# --- 6. หน้าสำหรับ Admin ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.logged_in:
        st.subheader("🔐 Login Admin")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In", type="primary"):
            if u_in == "bannawit.s" and p_in == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("ข้อมูลไม่ถูกต้อง")
    else:
        if st.button("Logout"): 
            st.session_state.logged_in = False
            st.rerun()
        st.header("🖥️ Dashboard")
        df = pd.DataFrame(sheet.get_all_records())
        st.dataframe(df, use_container_width=True)

# --- 7. Footer สีเขียว ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
