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

# --- 3. Sidebar (เมนูด้านข้าง) ---
with st.sidebar:
    st.markdown("### 🏠 หน้าหลัก") # หัวข้อหน้าหลัก
    page = st.selectbox(
        "เลือกเมนูการใช้งาน:",
        ["หน้าสำหรับ User", "หน้าสำหรับ Admin"]
    )
    # เส้นคั่นสีน้ำเงิน
    st.markdown("<hr style='border-top: 2px solid #1E3A8A; margin-top: 0px;'>", unsafe_allow_html=True)
    
    # ✅ ย้ายโลโก้มาไว้ตรงนี้ (ใต้เส้นคั่นใน Sidebar)
    if os.path.exists("logo.png"):
        st.markdown("<br>", unsafe_allow_html=True)
        # แสดงรูปภาพและทำเป็นลิงก์ไปในตัว
        st.image("logo.png", use_container_width=True)
        st.link_button("🌐 ไปที่เว็บไซต์สำนักงาน", "https://oce.rmutk.ac.th", use_container_width=True)

# --- 4. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    # ✅ กลับมาใช้ข้อความหัวเรื่อง (เอารูปแบนเนอร์ออกตามสั่ง)
    st.header("📘 ระบบจัดเก็บข้อมูลวารสารสหกิจศึกษาก้าวหน้า")
    st.write("---")

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
        # ประเภทบทความ (Radio)
        article_type = st.radio("**12. ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        other_detail = st.text_input("โปรดระบุ (หากเลือกอื่นๆ)")

        st.write("---")
        # แนบไฟล์
        up_file = st.file_uploader("13. แนบไฟล์ (PDF/Word)", type=["pdf", "docx", "doc"])

        st.markdown("<br>", unsafe_allow_html=True)
        btn1, btn2, _ = st.columns([1, 1, 4])
        
        if btn1.form_submit_button("ส่งข้อมูล", type="primary"):
            if up_file:
                final_type = article_type if article_type != "อื่นๆ" else f"อื่นๆ: {other_detail}"
                sheet.append_row([next_id, prefix, f_name, l_name, uni, faculty, major, org, addr, phone, email_u, final_type, up_file.name])
                st.success("🎉 บันทึกข้อมูลเรียบร้อย!")
            else: st.error("⚠️ กรุณาแนบไฟล์ก่อนส่ง")
        
        if btn2.form_submit_button("ยกเลิก", type="secondary"):
            st.rerun()

# --- 5. หน้าสำหรับ Admin ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        st.subheader("🔐 Login Admin")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u_in == "bannawit.s" and p_in == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
    else:
        if st.button("Logout"): 
            st.session_state.logged_in = False
            st.rerun()
        st.header("🖥️ Dashboard")
        df = pd.DataFrame(sheet.get_all_records())
        st.dataframe(df, use_container_width=True)

# --- 6. Footer สีเขียว ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
