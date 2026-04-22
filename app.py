import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

# --- 1. การตั้งค่าพื้นฐานและ CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    .stButton>button[kind="primary"] { background-color: #1E3A8A; color: white; border-radius: 8px; }
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border-radius: 8px; }
    section[data-testid="stSidebar"] { background-color: #F0F9FF; }
    .sidebar-divider { border-top: 3px solid #000000; margin: 10px 0; }
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        background-color: #28a745; color: white; text-align: center; 
        padding: 10px; font-weight: bold; z-index: 100;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. ฟังก์ชัน Popup แจ้งเตือน ---
@st.dialog("🔔 การแจ้งเตือนจากระบบ")
def show_message_modal(text):
    st.write(f"<div style='text-align: center; font-size: 1.2rem;'>{text}</div>", unsafe_allow_html=True)
    st.write("") 
    if st.button("ปิดหน้าต่าง", use_container_width=True):
        st.rerun()

# --- 3. การเชื่อมต่อ Google Services ---
if "google_auth" in st.secrets:
    try:
        info = st.secrets["google_auth"]
        creds = service_account.Credentials.from_service_account_info(info)
        client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
        spreadsheet = client.open("JCEP_Data")
        sheet = spreadsheet.worksheet("Data_2026")
        sheet_uni = spreadsheet.worksheet("University")
        sheet_agency = spreadsheet.worksheet("Agency")
        
        list_uni = sorted([item for item in sheet_uni.col_values(1)[1:] if item])
        list_agency = sorted([item for item in sheet_agency.col_values(1)[1:] if item])
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")

# --- 4. Sidebar ---
with st.sidebar:
    st.markdown("## 🏠 HOME")
    menu_options = ["หน้าสำหรับ User", "หน้าสำหรับ Admin", "จัดการรายชื่อมหาวิทยาลัย", "จัดการรายชื่อหน่วยงาน"]
    page = st.selectbox("เลือกเมนูการใช้งาน:", menu_options)
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://rmutk.ac.th", use_container_width=True)
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/", use_container_width=True)
    st.link_button("📘 วารสารสหกิจก้าวหน้า (JCEP)", "https://jcep.rmutk.ac.th/", use_container_width=True)

# --- 5. [อิสระ] หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    st.markdown("# 📘 ระบบส่งวารสารสหกิจศึกษาก้าวหน้า")
    with st.form("user_form", clear_on_submit=True):
        st.markdown("#### 📝 ฟอร์มส่งวารสาร")
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้า", ["นาย", "นางสาว", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์"])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")
        uni = st.selectbox("มหาวิทยาลัย / สถาบัน", options=list_uni, index=None, placeholder="พิมพ์เพื่อค้นหา...")
        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")
        affiliation = st.selectbox("สังกัด / หน่วยงาน", options=list_agency, index=None, placeholder="พิมพ์เพื่อค้นหา...")
        address = st.text_input("ที่อยู่")
        col_t, col_e = st.columns(2)
        phone = col_t.text_input("เบอร์โทรศัพท์")
        email = col_e.text_input("E-mail")
        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx", "doc"])
        work_link = st.text_input("🔗 ลิงก์ผลงาน (ถ้ามี)")
        
        if st.form_submit_button("ส่งข้อมูล", type="primary"):
            if not (up_file and f_name and phone and (uni or affiliation)):
                st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")
            else:
                try:
                    if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                    with open(os.path.join("uploaded_journals", up_file.name), "wb") as f: f.write(up_file.getbuffer())
                    sheet.append_row([prefix, f_name, l_name, uni, faculty, major, affiliation, address, phone, email, article_type, up_file.name, work_link])
                    show_message_modal("✅ บันทึกข้อมูลเรียบร้อย")
                except Exception as e: st.error(f"ผิดพลาด: {e}")

# --- 6. [อิสระ] หน้าจัดการรายชื่อ (ไม่มี LOGIN แล้ว) ---
elif page in ["จัดการรายชื่อมหาวิทยาลัย", "จัดการรายชื่อหน่วยงาน"]:
    target_sheet = sheet_uni if page == "จัดการรายชื่อมหาวิทยาลัย" else sheet_agency
    label = "มหาวิทยาลัย" if page == "จัดการรายชื่อมหาวิทยาลัย" else "หน่วยงาน"
    
    st.markdown(f"## ⚙️ {page}")
    st.info(f"💡 หน้าสำหรับเพิ่มรายชื่อ{label}ใหม่เข้าสู่ระบบ")
    
    with st.form(f"add_form_{page}", clear_on_submit=True):
        new_name = st.text_input(f"ชื่อ{label}:")
        new_addr = st.text_area("ที่อยู่:")
        new_contact = st.text_input("ข้อมูลติดต่อ (เบอร์โทร):")
        new_mail = st.text_input("E-mail:")
        if st.form_submit_button(f"🚀 บันทึกข้อมูล{label}", type="primary"):
            if new_name:
                target_sheet.append_row([new_name, new_addr, new_contact, new_mail])
                show_message_modal(f"✅ เพิ่มรายชื่อ{label}เรียบร้อย")
            else: st.warning(f"⚠️ กรุณาระบุชื่อ{label}")
    
    st.write("---")
    st.markdown("#### 📂 รายชื่อปัจจุบันในระบบ")
    data_list = target_sheet.get_all_values()
    if len(data_list) > 1:
        st.table(pd.DataFrame(data_list[1:], columns=data_list[0]))

# --- 7. [จำกัดสิทธิ์] หน้าสำหรับ Admin (ต้อง LOGIN เท่านั้น) ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        st.markdown("### 🔐 กรุณาเข้าสู่ระบบสำหรับ Admin")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u_in == "bannawit.s" and p_in == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("❌ ข้อมูลไม่ถูกต้อง")
    else:
        col_t, col_l = st.columns([8, 2])
        col_t.markdown("## 🖥️ หน้าสำหรับ Admin")
        if col_l.button("🚪 ออกจากระบบ"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        # ส่วนแสดงตาราง Admin
        raw_data = sheet.get_all_values()
        if len(raw_data) > 1:
            df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
            st.dataframe(df, use_container_width=True)

st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
