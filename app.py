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
    .stButton>button[kind="primary"] { background-color: #1E3A8A; color: white; border-radius: 8px; border: none; }
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border-radius: 8px; border: none; }
    section[data-testid="stSidebar"] { background-color: #F0F9FF; }
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        background-color: #28a745; color: white; text-align: center; 
        padding: 10px; font-weight: bold; z-index: 100;
    }
    div.stButton > button { width: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ฟังก์ชันจัดการ Popup ต่างๆ ---
@st.dialog("➕ เพิ่มผู้ดูแลระบบใหม่ (Add Admin)")
def add_admin_modal(admin_sheet):
    with st.form("add_admin_form", clear_on_submit=True):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        fn = st.text_input("ชื่อ-นามสกุล")
        em = st.text_input("E-mail")
        rl = st.selectbox("ตำแหน่ง (Role)", ["Super Admin", "Editor", "Viewer"])
        if st.form_submit_button("บันทึก Admin ใหม่", type="primary"):
            if u and p:
                admin_sheet.append_row([u, p, fn, em, rl])
                st.success("บันทึก Admin ใหม่สำเร็จ!")
                time.sleep(1)
                st.rerun()
            else: st.error("กรุณากรอกข้อมูลให้ครบ")

# --- 3. การเชื่อมต่อ Google Services ---
if "google_auth" in st.secrets:
    try:
        info = st.secrets["google_auth"]
        creds = service_account.Credentials.from_service_account_info(info)
        client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
        spreadsheet = client.open("JCEP_Data")
        sheet = spreadsheet.worksheet("Data_2026")
        try: admin_sheet = spreadsheet.worksheet("Admin_Users")
        except: admin_sheet = None
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")

# --- 4. Sidebar ---
with st.sidebar:
    st.markdown("### 🏠 หน้าหลัก")
    page = st.selectbox("เลือกเมนูการใช้งาน:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin"])
    st.markdown("<hr style='border-top: 2px solid #000000; margin-top: 0px;'>", unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://rmutk.ac.th", use_container_width=True)
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/", use_container_width=True)
    st.link_button("📘 วารสารสหกิจก้าวหน้า (JCEP)", "https://jcep.rmutk.ac.th/", use_container_width=True)

# --- 5. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    if os.path.exists("logo.gif"): st.image("logo.gif", use_container_width=True)
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
        org, addr = st.text_input("สังกัด"), st.text_area("ที่อยู่ส่งเอกสาร")
        col_t, col_e = st.columns(2)
        phone, email_u = col_t.text_input("เบอร์โทร"), col_e.text_input("E-mail")
        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์ (PDF/Word)", type=["pdf", "docx", "doc"])
        if st.form_submit_button("ส่งข้อมูล", type="primary"):
            if up_file:
                sheet.append_row([next_id, prefix, f_name, l_name, uni, faculty, major, org, addr, phone, email_u, article_type, up_file.name])
                st.success("✅ บันทึกข้อมูลสำเร็จ!")
                st.balloons()
            else: st.error("⚠️ กรุณาแนบไฟล์")

# --- 6. หน้าสำหรับ Admin ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        u_in, p_in = st.text_input("Username"), st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u_in == "bannawit.s" and p_in == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
    else:
        # ส่วนหัว Dashboard
        c1, c2, c3, c4 = st.columns([6, 1.5, 1.5, 1])
        c1.header("🖥️ Dashboard")
        if c2.button("➕ เพิ่ม Admin", type="primary"): add_admin_modal(admin_sheet)
        if c3.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()

        # ตารางข้อมูลวารสาร
        st.subheader("📊 ตารางข้อมูลวารสาร")
        data = sheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            # ระบบดาวน์โหลดเอกสาร
            st.subheader("📁 ดาวน์โหลดไฟล์")
            file_col = df.columns[-1]
            selected_file = st.selectbox("เลือกไฟล์:", df[file_col].unique())
            st.download_button(f"💾 ดาวน์โหลด: {selected_file}", data=b"", file_name=str(selected_file))
        else: st.info("ไม่มีข้อมูล")

# --- 7. Footer ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
