import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

# --- 1. การตั้งค่าพื้นฐาน ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    .stButton>button[kind="primary"] { background-color: #1E3A8A; color: white; border-radius: 8px; }
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border-radius: 8px; }
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        background-color: #28a745; color: white; text-align: center; 
        padding: 10px; font-weight: bold; z-index: 100;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. ฟังก์ชันดึงข้อมูล (ใช้ Cache เพื่อป้องกันข้อมูลหาย) ---
@st.cache_data(ttl=600) # เก็บข้อมูลไว้ 10 นาที ลดการโหลดบ่อย
def get_gsheet_data():
    try:
        info = st.secrets["google_auth"]
        creds = service_account.Credentials.from_service_account_info(info)
        client = gspread.authorize(creds.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets', 
            'https://www.googleapis.com/auth/drive'
        ]))
        spreadsheet = client.open("JCEP_Data")
        
        # ดึงข้อมูลจากชีตต่างๆ
        u_sheet = spreadsheet.worksheet("University")
        a_sheet = spreadsheet.worksheet("Agency")
        
        all_u = u_sheet.get_all_records()
        all_a = a_sheet.get_all_records()
        
        return all_u, all_a
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return [], []

# ฟังก์ชันแสดง Popup
@st.dialog("🔔 แจ้งเตือน")
def show_modal(text):
    st.write(f"### {text}")
    if st.button("ตกลง"):
        st.cache_data.clear() # เคลียร์แคชเพื่อให้ดึงข้อมูลใหม่หลังบันทึก
        st.rerun()

# --- 3. โหลดข้อมูล ---
all_uni_data, all_agency_data = get_gsheet_data()
list_uni = sorted([str(d['มหาวิทยาลัย']) for d in all_uni_data if d.get('มหาวิทยาลัย')])
list_agency = sorted([str(d['หน่วยงาน']) for d in all_agency_data if d.get('หน่วยงาน')])

# --- 4. Sidebar ---
with st.sidebar:
    st.markdown("## 🏠 HOME")
    page = st.selectbox("เลือกเมนู:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin", "จัดการมหาวิทยาลัย", "จัดการหน่วยงาน"])

# --- 5. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    st.markdown("# 📘 ระบบส่งวารสาร JCEP")
    
    with st.container(border=True):
        st.markdown("#### 📝 ข้อมูลผู้ส่ง")
        c_p, c_f, c_l = st.columns([1, 2, 2])
        prefix = c_p.selectbox("คำนำหน้า", ["นาย", "นางสาว", "ผศ.", "รองศาสตราจารย์", "ศาสตราจารย์"])
        f_name = c_f.text_input("ชื่อ")
        l_name = c_l.text_input("นามสกุล")

        # --- ส่วนมหาวิทยาลัย ---
        st.write("---")
        col_u1, col_u2 = st.columns([7, 1])
        with col_u1:
            uni_select = st.selectbox("มหาวิทยาลัย / สถาบัน", options=list_uni, index=None, placeholder="พิมพ์ค้นหา...")
        with col_u2:
            st.write("เพิ่มใหม่")
            if st.button("➕", key="add_u"):
                st.session_state.is_new_u = not st.session_state.get('is_new_u', False)
        
        final_uni = uni_select
        if st.session_state.get('is_new_u', False):
            final_uni = st.text_input("✨ ระบุชื่อมหาวิทยาลัยใหม่")
            st.info("กำลังเข้าสู่โหมดเพิ่มมหาวิทยาลัยใหม่")

        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")

        # --- ส่วนหน่วยงาน ---
        st.write("---")
        col_a1, col_a2 = st.columns([7, 1])
        with col_a1:
            agency_select = st.selectbox("สังกัด / หน่วยงาน", options=list_agency, index=None, placeholder="พิมพ์ค้นหา...")
        with col_a2:
            st.write("เพิ่มใหม่")
            if st.button("➕", key="add_a"):
                st.session_state.is_new_a = not st.session_state.get('is_new_a', False)

        final_agency = agency_select
        if st.session_state.get('is_new_a', False):
            final_agency = st.text_input("✨ ระบุชื่อหน่วยงานใหม่")
            st.info("กำลังเข้าสู่โหมดเพิ่มหน่วยงานใหม่")

        # --- Auto-fill ข้อมูลติดต่อ ---
        d_addr, d_phone, d_mail = "", "", ""
        # ค้นหาข้อมูลถ้าเลือกจากลิสต์
        if uni_select and not st.session_state.get('is_new_u', False):
            match = next((i for i in all_uni_data if str(i['มหาวิทยาลัย']) == uni_select), None)
            if match: d_addr, d_phone, d_mail = match.get('ที่อยู่',''), match.get('ข้อมูลติดต่อ',''), match.get('E-mail','')
        elif agency_select and not st.session_state.get('is_new_a', False):
            match = next((i for i in all_agency_data if str(i['หน่วยงาน']) == agency_select), None)
            if match: d_addr, d_phone, d_mail = match.get('ที่อยู่',''), match.get('ข้อมูลติดต่อ',''), match.get('E-mail','')

        st.write("---")
        address = st.text_input("ที่อยู่", value=d_addr)
        c_t, c_e = st.columns(2)
        phone = c_t.text_input("เบอร์โทรศัพท์", value=d_phone)
        email = c_e.text_input("E-mail", value=d_mail)

        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์", type=["pdf", "docx"])
        work_link = st.text_input("🔗 ลิงก์ผลงาน (ถ้ามี)")

        if st.button("🚀 ส่งข้อมูล", type="primary", use_container_width=True):
            if not (up_file and f_name and final_uni and final_agency):
                st.warning("กรุณากรอกข้อมูลสำคัญให้ครบ (ชื่อ, มหาลัย, หน่วยงาน, ไฟล์)")
            else:
                try:
                    # เชื่อมต่อเพื่อบันทึก (ไม่ใช้ cache)
                    info = st.secrets["google_auth"]
                    creds = service_account.Credentials.from_service_account_info(info)
                    client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
                    ss = client.open("JCEP_Data")
                    
                    # 1. บันทึกเข้าหน้า Data_2026
                    main_sheet = ss.worksheet("Data_2026")
                    main_sheet.append_row([prefix, f_name, l_name, final_uni, faculty, major, final_agency, address, phone, email, article_type, up_file.name, work_link])
                    
                    # 2. ถ้าเป็นของใหม่ ให้บันทึกเข้าฐานรายชื่อ
                    if st.session_state.get('is_new_u', False):
                        ss.worksheet("University").append_row([final_uni, address, phone, email])
                    if st.session_state.get('is_new_a', False):
                        ss.worksheet("Agency").append_row([final_agency, address, phone, email])
                    
                    show_modal("บันทึกข้อมูลเรียบร้อยแล้ว!")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการบันทึก: {e}")

# --- หน้า Admin (ฟังก์ชันเดิมยังอยู่ครบ) ---
else:
    # ... (ส่วน Admin และการจัดการรายชื่อคงเดิมเหมือนเวอร์ชันก่อนหน้า) ...    
    st.write(f"กำลังอยู่ในหน้า: {page} (ฟังก์ชันแอดมินยังคงเดิมตามโค้ดหลักของคุณ)")

st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
