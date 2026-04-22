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
    .helper-text { 
        font-size: 0.95rem; color: #555; text-align: center; 
        margin-top: 15px; padding: 15px; background-color: #f8f9fa; 
        border-radius: 10px; border: 1px dashed #ccc;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. ระบบ Navigation (ใช้ Callback เพื่อความแม่นยำ) ---
if 'page_nav' not in st.session_state:
    st.session_state.page_nav = "หน้าสำหรับ User"

def change_page(target):
    st.session_state.page_nav = target

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
    
    # ใช้ index ที่ผูกกับ session_state โดยตรง
    current_idx = menu_options.index(st.session_state.page_nav)
    
    # เมื่อเลือกจาก Sidebar ให้ update page_nav ทันที
    page = st.selectbox("เลือกเมนูการใช้งาน:", menu_options, index=current_idx, key="main_nav_box")
    if page != st.session_state.page_nav:
        st.session_state.page_nav = page
        st.rerun()

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://rmutk.ac.th", use_container_width=True)
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/", use_container_width=True)
    st.link_button("📘 วารสารสหกิจก้าวหน้า (JCEP)", "https://jcep.rmutk.ac.th/", use_container_width=True)

# ฟังก์ชันแจ้งเตือน
@st.dialog("🔔 การแจ้งเตือนจากระบบ")
def show_message_modal(text):
    st.write(f"<div style='text-align: center; font-size: 1.2rem;'>{text}</div>", unsafe_allow_html=True)
    if st.button("ปิดหน้าต่าง", use_container_width=True):
        st.rerun()

# --- 5. หน้าสำหรับ User ---
if st.session_state.page_nav == "หน้าสำหรับ User":
    st.markdown("# 📘 ระบบส่งวารสารสหกิจศึกษาก้าวหน้า")
    st.markdown("#### 📝 ฟอร์มส่งวารสาร")
    
    with st.container(border=True):
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้าชื่อ", ["นาย", "นางสาว", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์"])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")
        
        uni = st.selectbox("มหาวิทยาลัย / สถาบัน", options=list_uni, index=None, placeholder="เลือกมหาวิทยาลัย...")
        
        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")
        
        affiliation = st.selectbox("สังกัด / หน่วยงาน", options=list_agency, index=None, placeholder="เลือกหน่วยงาน...")
        address = st.text_input("ที่อยู่")
        
        col_t, col_e = st.columns(2)
        phone = col_t.text_input("เบอร์โทรศัพท์")
        email = col_e.text_input("E-mail")
        
        article_type_option = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        other_type = ""
        if article_type_option == "อื่นๆ":
            other_type = st.text_input("โปรดระบุประเภทบทความอื่นๆ:", placeholder="ระบุประเภทที่นี่...")
        
        final_article_type = other_type if article_type_option == "อื่นๆ" else article_type_option
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx", "doc"])
        work_link = st.text_input("🔗 ลิงก์ผลงาน (ถ้ามี)")
        
        if st.button("🚀 ส่งข้อมูลวารสาร", type="primary", use_container_width=True):
            if not (up_file and f_name and phone and final_article_type):
                st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")
            else:
                try:
                    if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                    with open(os.path.join("uploaded_journals", up_file.name), "wb") as f: f.write(up_file.getbuffer())
                    all_rows = sheet.get_all_values()
                    new_row = [len(all_rows), prefix, f_name, l_name, uni, faculty, major, affiliation, address, phone, email, final_article_type, up_file.name]
                    sheet.append_row(new_row)
                    show_message_modal("✅ บันทึกข้อมูลเรียบร้อย")
                except Exception as e: st.error(f"ผิดพลาด: {e}")

        # --- ส่วนที่เน้นแก้ไข: ใช้ on_click เพื่อเปลี่ยนหน้า ---
        st.markdown('<div class="helper-text">💡 <b>หากไม่พบรายชื่อหน่วยงานของท่าน</b> <br>กรุณากดปุ่มเพื่อไปหน้าเพิ่มข้อมูลด้านล่างนี้</div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        c1.button("🏫 ไปหน้า: เพิ่มมหาวิทยาลัย", use_container_width=True, on_click=change_page, args=("จัดการรายชื่อมหาวิทยาลัย",))
        c2.button("🏢 ไปหน้า: เพิ่มหน่วยงาน", use_container_width=True, on_click=change_page, args=("จัดการรายชื่อหน่วยงาน",))

# --- 6. หน้าจัดการรายชื่อ (เพิ่มปุ่มกลับ) ---
elif st.session_state.page_nav in ["จัดการรายชื่อมหาวิทยาลัย", "จัดการรายชื่อหน่วยงาน"]:
    target_sheet = sheet_uni if st.session_state.page_nav == "จัดการรายชื่อมหาวิทยาลัย" else sheet_agency
    current_list = list_uni if st.session_state.page_nav == "จัดการรายชื่อมหาวิทยาลัย" else list_agency
    label = "มหาวิทยาลัย" if st.session_state.page_nav == "จัดการรายชื่อมหาวิทยาลัย" else "หน่วยงาน"
    
    st.markdown(f"## ⚙️ {st.session_state.page_nav}")
    st.button("⬅️ กลับไปหน้าฟอร์มส่งวารสาร", on_click=change_page, args=("หน้าสำหรับ User",))

    with st.form("add_list_form", clear_on_submit=True):
        st.subheader(f"➕ เพิ่มข้อมูล{label}")
        new_name = st.text_input(f"ชื่อ{label}:").strip()
        new_addr = st.text_area("ที่อยู่:")
        new_contact = st.text_input("เบอร์โทรศัพท์:")
        new_mail = st.text_input("E-mail:")
        
        if st.form_submit_button(f"🚀 บันทึกข้อมูล{label}", type="primary"):
            if new_name and new_name.lower() not in [n.lower() for n in current_list]:
                try:
                    target_sheet.append_row([new_name, new_addr, new_contact, new_mail])
                    show_message_modal(f"✅ เพิ่มข้อมูล{label}สำเร็จ")
                except Exception as e: st.error(f"บันทึกไม่ได้: {e}")
            else: st.warning("ข้อมูลซ้ำหรือไม่ได้กรอกชื่อ")
    
    st.divider()
    try:
        data_list = target_sheet.get_all_values()
        if len(data_list) > 1: st.table(pd.DataFrame(data_list[1:], columns=data_list[0]))
    except: pass

# --- 7. หน้าสำหรับ Admin ---
elif st.session_state.page_nav == "หน้าสำหรับ Admin":
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
        if st.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()
        try:
            raw_data = sheet.get_all_values()
            if len(raw_data) > 1:
                st.dataframe(pd.DataFrame(raw_data[1:], columns=raw_data[0]), use_container_width=True)
        except Exception as e: st.error(f"โหลดข้อมูลไม่ได้: {e}")

st.markdown('<div class="footer">Create by OCE - RMUTK</div>', unsafe_allow_html=True)
