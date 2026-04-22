import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os
import re
import time
from datetime import datetime
import plotly.express as px

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

# --- 2. ฟังก์ชันเสริม ---
def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def validate_phone(phone):
    return re.match(r"^[0-9]{9,10}$", phone)

def generate_unique_id(last_row_index):
    year = datetime.now().year
    return f"JCEP-{year}-{last_row_index+1:03d}"

# --- 3. ระบบดึงข้อมูลและ Cache ---
@st.cache_data(ttl=600)
def get_google_data():
    if "google_auth" in st.secrets:
        try:
            info = st.secrets["google_auth"]
            creds = service_account.Credentials.from_service_account_info(info)
            client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
            spreadsheet = client.open("JCEP_Data")
            df_uni = pd.DataFrame(spreadsheet.worksheet("University").get_all_records())
            df_agency = pd.DataFrame(spreadsheet.worksheet("Agency").get_all_records())
            return df_uni, df_agency
        except:
            return pd.DataFrame(), pd.DataFrame()
    return pd.DataFrame(), pd.DataFrame()

df_uni, df_agency = get_google_data()
list_uni = sorted(df_uni.iloc[:, 0].tolist()) if not df_uni.empty else []
list_agency = sorted(df_agency.iloc[:, 0].tolist()) if not df_agency.empty else []

# --- 4. Navigation ---
menu_options = ["หน้าสำหรับกรอกข้อมูล", "หน้าสำหรับ Admin", "เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน", "เพิ่มข้อมูลหน่วยงาน/สังกัด"]
if 'nav_state' not in st.session_state:
    st.session_state.nav_state = menu_options[0]

# --- 5. ฟังก์ชัน Popup & ล้างค่า ---
@st.dialog("🔔 การแจ้งเตือนจากระบบ")
def show_message_modal(text):
    st.write(f"<div style='text-align: center; font-size: 1.1rem;'>{text}</div>", unsafe_allow_html=True)
    if st.button("ปิดหน้าต่างและล้างค่าฟอร์ม", use_container_width=True):
        st.cache_data.clear()
        # ล้างค่า session state เพื่อ Reset ฟอร์มกรอกข้อมูล
        for key in list(st.session_state.keys()):
            if key not in ['nav_state', 'logged_in', 'last_activity']:
                del st.session_state[key]
        st.rerun()

# --- 6. Sidebar ---
with st.sidebar:
    st.markdown("## 🏠 HOME")
    try: current_idx = menu_options.index(st.session_state.nav_state)
    except: current_idx = 0
    page = st.selectbox("เลือกเมนูการใช้งาน:", menu_options, index=current_idx)
    if page != st.session_state.nav_state:
        st.session_state.nav_state = page
        st.rerun()
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://www.rmutk.ac.th/")
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/")
    st.link_button("📘 วารสาร JCEP", "https://jcep.rmutk.ac.th/")

# --- 7. หน้าสำหรับกรอกข้อมูล (ปรับให้ตรงกับหัวตาราง A-M) ---
if st.session_state.nav_state == "หน้าสำหรับกรอกข้อมูล":
    st.markdown("# 📘 ระบบส่งวารสาร JCEP")
    st.info("💡 กรุณากรอกข้อมูลให้ครบถ้วน ข้อมูลจะถูกจัดเก็บลงในฐานข้อมูลวารสารปี 2026")
    
    with st.container(border=True):
        # แถวที่ 1: ชื่อ-สกุล
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้าชื่อ", ["นาย", "นางสาว", "ผศ.", "รศ.", "ศ."])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")
        
        # แถวที่ 2: มหาวิทยาลัย และ สังกัด
        uni = st.selectbox("มหาวิทยาลัย / สถาบัน", options=list_uni, index=None, placeholder="เลือกมหาวิทยาลัย...")
        
        # แถวที่ 3: คณะ และ สาขาวิชา (เพิ่มตามหัวตาราง E, F, G)
        col_c, col_d = st.columns(2)
        faculty = col_c.text_input("คณะ")
        major = col_d.text_input("สาขาวิชา")
        
        affiliation = st.selectbox("สังกัด / หน่วยงาน (ถ้ามี)", options=list_agency, index=None, placeholder="เลือกหน่วยงาน...")

        # Auto-fill จากฐานข้อมูลสถาบัน
        auto_addr, auto_phone, auto_email = "", "", ""
        if uni and not df_uni.empty:
            row = df_uni[df_uni.iloc[:, 0] == uni]
            if not row.empty: auto_addr, auto_phone, auto_email = row.iloc[0, 1], row.iloc[0, 2], row.iloc[0, 3]

        # แถวที่ 4: ที่อยู่
        address = st.text_area("ที่อยู่สำหรับจัดส่งเอกสาร", value=auto_addr)
        
        # แถวที่ 5: ติดต่อ
        col_t, col_e = st.columns(2)
        phone = col_t.text_input("เบอร์โทรศัพท์ (ระบุตัวเลขเท่านั้น)", value=auto_phone)
        email = col_e.text_input("E-mail", value=auto_email)
        
        # แถวที่ 6: ประเภทและไฟล์
        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx"])
        
        if st.button("🚀 ส่งข้อมูลวารสาร", type="primary", use_container_width=True):
            if not (f_name and phone and email and up_file and uni):
                st.warning("⚠️ กรุณากรอกข้อมูลสำคัญ (ชื่อ, มหาวิทยาลัย, เบอร์โทร, อีเมล, ไฟล์) ให้ครบถ้วน")
            elif not validate_email(email):
                st.error("❌ รูปแบบอีเมลไม่ถูกต้อง")
            else:
                try:
                    info = st.secrets["google_auth"]
                    creds = service_account.Credentials.from_service_account_info(info)
                    client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
                    sheet = client.open("JCEP_Data").worksheet("Data_2026")
                    
                    data_rows = sheet.get_all_values()
                    unique_id = generate_unique_id(len(data_rows))
                    
                    # บันทึกข้อมูลลง Google Sheet เรียงตามหัวตาราง A-M (ภาพ image_399e27.png)
                    # A: ลำดับที่(ID), B: คำนำหน้า, C: ชื่อ, D: นามสกุล, E: มหาลัย, F: คณะ, G: สาขา, H: สังกัด, I: ที่อยู่, J: เบอร์, K: Email, L: ประเภท, M: Filename
                    sheet.append_row([
                        unique_id, prefix, f_name, l_name, uni, faculty, major, affiliation, 
                        address, phone, email, article_type, up_file.name, datetime.now().strftime("%Y-%m-%d %H:%M")
                    ])
                    
                    show_message_modal(f"✅ บันทึกข้อมูลสำเร็จ!<br>เลขรับเรื่องของคุณคือ: <b>{unique_id}</b>")
                except Exception as e: st.error(f"Error: {e}")

    # --- ปุ่มทางลัด 2 ปุ่มด้านล่าง (กลับมาครบ) ---
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    if col1.button("🏫 ไปหน้า: เพิ่มมหาวิทยาลัย/สถาบัน", type="secondary", use_container_width=True):
        st.session_state.nav_state = "เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน"
        st.rerun()
    if col2.button("🏢 ไปหน้า: เพิ่มหน่วยงาน/สังกัด", type="secondary", use_container_width=True):
        st.session_state.nav_state = "เพิ่มข้อมูลหน่วยงาน/สังกัด"
        st.rerun()

# --- 8. หน้าสำหรับ Admin (Dashboard + กราฟแยกสี) ---
elif st.session_state.nav_state == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        st.markdown("### 🔐 Admin Login")
        u, p = st.text_input("Username"), st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u == "bannawit.s" and p == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("❌ ข้อมูลไม่ถูกต้อง")
    else:
        col_t, col_l = st.columns([8, 2])
        col_t.markdown("## 🖥️ แผงควบคุมสำหรับ Admin")
        if col_l.button("🚪 ออกจากระบบ", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
        
        try:
            info = st.secrets["google_auth"]
            creds = service_account.Credentials.from_service_account_info(info)
            client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
            raw_data = client.open("JCEP_Data").worksheet("Data_2026").get_all_values()
            
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                
                # กราฟแยกสี 3 สี (Plotly)
                st.markdown("### 📊 สถิติแยกตามประเภทบทความ")
                counts = df['ประเภทบทความ'].value_counts().reset_index()
                counts.columns = ['ประเภท', 'จำนวน']
                fig = px.bar(counts, x='ประเภท', y='จำนวน', color='ประเภท',
                             color_discrete_map={"บทความวิจัย": "#1E3A8A", "บทความวิชาการ": "#28a745", "อื่นๆ": "#dc3545"})
                st.plotly_chart(fig, use_container_width=True)
                
                # ตารางข้อมูล
                search = st.text_input("🔍 ค้นหา (ชื่อ หรือ เลขรับเรื่อง):")
                df_filtered = df[df.iloc[:, 2].str.contains(search, case=False) | df.iloc[:, 0].str.contains(search, case=False)]
                st.dataframe(df_filtered, use_container_width=True)
            else: st.info("ยังไม่มีข้อมูลในฐานข้อมูล")
        except Exception as e: st.error(f"Error: {e}")

# --- 9. หน้าเพิ่มข้อมูลสถาบัน/หน่วยงาน ---
elif st.session_state.nav_state in ["เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน", "เพิ่มข้อมูลหน่วยงาน/สังกัด"]:
    target = "University" if st.session_state.nav_state == "เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน" else "Agency"
    st.markdown(f"## ⚙️ จัดการรายชื่อ {target}")
    if st.button("⬅️ กลับหน้าสำหรับกรอกข้อมูล"):
        st.session_state.nav_state = menu_options[0]
        st.rerun()

    with st.form("add_form", clear_on_submit=True):
        n = st.text_input(f"ชื่อ{target}:")
        a, p, m = st.text_area("ที่อยู่:"), st.text_input("เบอร์โทร:"), st.text_input("E-mail:")
        if st.form_submit_button("🚀 บันทึก", type="primary"):
            if n:
                try:
                    info = st.secrets["google_auth"]
                    creds = service_account.Credentials.from_service_account_info(info)
                    client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
                    client.open("JCEP_Data").worksheet(target).append_row([n, a, p, m])
                    show_message_modal("✅ เพิ่มข้อมูลรายชื่อสำเร็จ")
                except: st.error("ไม่สามารถเชื่อมต่อฐานข้อมูลได้")

st.markdown('<div class="footer">Create by OCE - RMUTK</div>', unsafe_allow_html=True)
