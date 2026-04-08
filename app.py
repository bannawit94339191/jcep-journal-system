import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os
import time

# --- 1. ตั้งค่าพื้นฐานและการตกแต่ง CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    .stButton>button[kind="primary"] { background-color: #1E3A8A; color: white; border-radius: 8px; }
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border-radius: 8px; }
    section[data-testid="stSidebar"] { background-color: #F0F9FF; }
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        background-color: #28a745; color: white; text-align: center; 
        padding: 10px; font-weight: bold; z-index: 100;
    }
    /* ปรับแต่งปุ่มให้ดูเรียบร้อยขึ้น */
    div.stButton > button { width: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Google Services (กู้คืนช่องข้อมูลที่หายไป!) ---
if "google_auth" in st.secrets:
    try:
        info = st.secrets["google_auth"]
        creds = service_account.Credentials.from_service_account_info(info)
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        client = gspread.authorize(creds.with_scopes(scope))
        spreadsheet = client.open("JCEP_Data")
        sheet = spreadsheet.worksheet("Data_2026")
        try: admin_sheet = spreadsheet.worksheet("Admin_Users")
        except: admin_sheet = None
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")

# --- 3. ฟังก์ชัน Modal สำหรับเพิ่ม Admin ---
@st.dialog("➕ เพิ่มผู้ดูแลระบบใหม่ (Add Admin)")
def add_admin_modal():
    with st.form("add_admin_form", clear_on_submit=True):
        col_a1, col_a2 = st.columns(2)
        adm_user = col_a1.text_input("Username")
        adm_pass = col_a2.text_input("Password", type="password")
        
        adm_fullname = st.text_input("ชื่อ-นามสกุล")
        adm_email = st.text_input("E-mail")
        adm_role = st.selectbox("ตำแหน่ง (Role)", ["Super Admin", "Editor", "Viewer"])
        
        if st.form_submit_button("บันทึก Admin ใหม่", type="primary"):
            if adm_user and adm_pass:
                if admin_sheet:
                    admin_sheet.append_row([adm_user, adm_pass, adm_fullname, adm_email, adm_role])
                    st.success(f"เพิ่ม {adm_fullname} สำเร็จ!")
                    time.sleep(1)
                    st.rerun()
                else: st.error("ไม่พบฐานข้อมูล Admin")
            else: st.error("กรุณากรอกข้อมูลให้ครบถ้วน")

# --- 4. Sidebar พร้อมปุ่ม Link 3 ปุ่ม ---
with st.sidebar:
    st.markdown("### 🏠 HOME")
    page = st.selectbox("เลือกเมนูการใช้งาน:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin"])
    st.markdown("<hr style='border-top: 2px solid #000000; margin-top: 0px;'>", unsafe_allow_html=True)
    
    st.markdown("🔗 **ลิงก์ที่เกี่ยวข้อง**")
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://rmutk.ac.th", use_container_width=True)
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/", use_container_width=True)
    st.link_button("📘 วารสารสหกิจก้าวหน้า (JCEP)", "https://jcep.rmutk.ac.th/", use_container_width=True)

# --- 5. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    if os.path.exists("logo.gif"):
        st.image("logo.gif", use_container_width=True)
        st.write("---")

    try: next_id = len(sheet.get_all_values())
    except: next_id = 1

    with st.form("user_form", clear_on_submit=True):
        st.info(f"📍 ลำดับที่: {next_id}")
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้า", ["นาย", "นางสาว", "ผศ.", "รศ.", "ศ."])
        f_name, l_name = col_f.text_input("ชื่อ"), col_l.text_input("นามสกุล")
        uni = st.text_input("มหาวิทยาลัย / สถาบัน")
        col_fac, col_maj = st.columns(2)
        faculty, major = col_fac.text_input("คณะ"), col_maj.text_input("สาขาวิชา")
        org = st.text_input("สังกัด / หน่วยงาน")
        addr = st.text_area("ที่อยู่สำหรับการจัดส่งเอกสาร")
        col_tel, col_email = st.columns(2)
        phone, email_u = col_tel.text_input("เบอร์โทรศัพท์"), col_email.text_input("E-mail")

        st.write("---")
        article_type = st.radio("**12. ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        other_detail = st.text_input("โปรดเลือกประเภทบทความ (หากเลือกอื่นๆ)")

        st.write("---")
        up_file = st.file_uploader("13. แนบไฟล์ (PDF/Word)", type=["pdf", "docx", "doc"])

        if st.form_submit_button("ส่งข้อมูล", type="primary"):
            if up_file:
                try:
                    final_type = article_type if article_type != "อื่นๆ" else f"อื่นๆ: {other_detail}"
                    sheet.append_row([next_id, prefix, f_name, l_name, uni, faculty, major, org, addr, phone, email_u, final_type, up_file.name])
                    st.success("✅ บันทึกข้อมูลสำเร็จ!")
                    st.balloons()
                except Exception as e: st.error(f"เกิดข้อผิดพลาด: {e}")
            else: st.warning("⚠️ กรุณาแนบไฟล์ก่อนส่ง")

# --- 6. หน้าสำหรับ Admin (ปรับปุ่ม Add Admin ไว้ข้าง Logout) ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        st.subheader("🔐 เข้าสู่ระบบผู้ดูแลระบบ")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In", type="primary"):
            if u_in ==
