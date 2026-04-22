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

# --- 2. ฟังก์ชันเสริม (Validation & ID) ---
def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def validate_phone(phone):
    return re.match(r"^[0-9]{9,10}$", phone)

def generate_unique_id(last_row_index):
    year = datetime.now().year
    return f"JCEP-{year}-{last_row_index+1:03d}"

# --- 3. ระบบดึงข้อมูลและ Cache (ป้องกัน Quota Exceeded) ---
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

# --- 5. ระบบ Session Timeout (1 ชั่วโมง) ---
if st.session_state.get('logged_in', False):
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = time.time()
    if time.time() - st.session_state.last_activity > 3600:
        st.session_state.logged_in = False
        st.rerun()

# --- 6. ฟังก์ชัน Popup และการล้างค่า ---
@st.dialog("🔔 การแจ้งเตือนจากระบบ")
def show_message_modal(text):
    st.write(f"<div style='text-align: center; font-size: 1.1rem;'>{text}</div>", unsafe_allow_html=True)
    if st.button("ปิดหน้าต่างและส่งใหม่", use_container_width=True):
        st.cache_data.clear()
        # ล้างค่าในฟอร์มเพื่อเริ่มใหม่
        for key in list(st.session_state.keys()):
            if key not in ['nav_state', 'logged_in', 'last_activity']:
                del st.session_state[key]
        st.rerun()

# --- 7. Sidebar ---
with st.sidebar:
    st.markdown("## 🏠 HOME")
    try:
        current_idx = menu_options.index(st.session_state.nav_state)
    except:
        current_idx = 0
    page = st.selectbox("เลือกเมนูการใช้งาน:", menu_options, index=current_idx)
    if page != st.session_state.nav_state:
        st.session_state.nav_state = page
        st.rerun()
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://www.rmutk.ac.th/")
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/")
    st.link_button("📘 วารสาร JCEP", "https://jcep.rmutk.ac.th/")

# --- 8. หน้าสำหรับกรอกข้อมูล (ถอดปุ่มล่างออกแล้ว) ---
if st.session_state.nav_state == "หน้าสำหรับกรอกข้อมูล":
    st.markdown("# 📘 ระบบส่งวารสาร JCEP")
    st.info("💡 หากไม่พบรายชื่อหน่วยงานในรายการ โปรดเลือกเมนูเพิ่มข้อมูลที่แถบด้านข้าง (Sidebar)")
    
    with st.container(border=True):
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้าชื่อ", ["นาย", "นางสาว", "ผศ.", "รศ.", "ศ."])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")
        
        uni = st.selectbox("มหาวิทยาลัย / สถาบัน", options=list_uni, index=None, placeholder="เลือกมหาวิทยาลัย...")
        affiliation = st.selectbox("สังกัด / หน่วยงาน", options=list_agency, index=None, placeholder="เลือกหน่วยงาน...")

        # Auto-fill Logic
        auto_addr, auto_phone, auto_email = "", "", ""
        if affiliation and not df_agency.empty:
            row = df_agency[df_agency.iloc[:, 0] == affiliation]
            if not row.empty: auto_addr, auto_phone, auto_email = row.iloc[0, 1], row.iloc[0, 2], row.iloc[0, 3]
        elif uni and not df_uni.empty:
            row = df_uni[df_uni.iloc[:, 0] == uni]
            if not row.empty: auto_addr, auto_phone, auto_email = row.iloc[0, 1], row.iloc[0, 2], row.iloc[0, 3]

        address = st.text_area("ที่อยู่จัดส่งเอกสาร", value=auto_addr)
        col_t, col_e = st.columns(2)
        phone = col_t.text_input("เบอร์โทรศัพท์ (ระบุเฉพาะตัวเลข)", value=auto_phone)
        email = col_e.text_input("E-mail", value=auto_email)
        
        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx"])
        work_link = st.text_input("🔗 ลิงก์ผลงาน (ถ้ามี)")

        if st.button("🚀 ส่งข้อมูลวารสาร", type="primary", use_container_width=True):
            if not (f_name and phone and email and up_file):
                st.warning("⚠️ กรุณากรอกข้อมูลและแนบไฟล์ให้ครบถ้วน")
            elif not validate_email(email):
                st.error("❌ รูปแบบอีเมลไม่ถูกต้อง")
            elif not validate_phone(phone):
                st.error("❌ เบอร์โทรศัพท์ต้องเป็นตัวเลข 9-10 หลัก")
            else:
                try:
                    info = st.secrets["google_auth"]
                    creds = service_account.Credentials.from_service_account_info(info)
                    client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
                    sheet = client.open("JCEP_Data").worksheet("Data_2026")
                    
                    data_rows = sheet.get_all_values()
                    unique_id = generate_unique_id(len(data_rows))
                    
                    # บันทึกข้อมูล (ID, คำนำหน้า, ชื่อ, นามสกุล, มหาลัย, สังกัด, ที่อยู่, เบอร์, เมล, ประเภท, ไฟล์, ลิงก์, วันที่)
                    sheet.append_row([
                        unique_id, prefix, f_name, l_name, uni, affiliation, 
                        address, phone, email, article_type, up_file.name, 
                        work_link, datetime.now().strftime("%Y-%m-%d %H:%M")
                    ])
                    
                    show_message_modal(f"✅ บันทึกข้อมูลสำเร็จ!<br>เลขที่รับเรื่องของคุณคือ: <b>{unique_id}</b>")
                except Exception as e: st.error(f"Error: {e}")

# --- 9. หน้าสำหรับ Admin (Dashboard + Search) ---
elif st.session_state.nav_state == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        st.markdown("### 🔐 Admin Login")
        u, p = st.text_input("Username"), st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u == "bannawit.s" and p == "adminjcep":
                st.session_state.logged_in = True
                st.session_state.last_activity = time.time()
                st.rerun()
            else: st.error("❌ ข้อมูลไม่ถูกต้อง")
    else:
        st.session_state.last_activity = time.time()
        col_t, col_l = st.columns([8, 2])
        col_t.markdown("## 🖥️ แผงควบคุม Admin")
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
                
                # กราฟประเภทบทความ
                st.markdown("### 📊 สรุปประเภทบทความ")
                counts = df['ประเภทบทความ'].value_counts().reset_index()
                counts.columns = ['ประเภท', 'จำนวน']
                fig = px.bar(counts, x='ประเภท', y='จำนวน', color='ประเภท',
                             color_discrete_map={"บทความวิจัย": "#1E3A8A", "บทความวิชาการ": "#28a745", "อื่นๆ": "#dc3545"})
                st.plotly_chart(fig, use_container_width=True)
                
                # ระบบ Search
                search = st.text_input("🔍 ค้นหา (ชื่อ หรือ ID):")
                df_filtered = df[df.iloc[:, 2].str.contains(search, case=False) | df.iloc[:, 0].str.contains(search, case=False)]
                st.dataframe(df_filtered, use_container_width=True)
            else: st.info("ℹ️ ยังไม่มีข้อมูลในระบบ")
        except Exception as e: st.error(f"Error: {e}")

# --- 10. หน้าจัดการรายชื่อสถาบัน/หน่วยงาน ---
elif st.session_state.nav_state in ["เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน", "เพิ่มข้อมูลหน่วยงาน/สังกัด"]:
    target = "University" if st.session_state.nav_state == "เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน" else "Agency"
    st.markdown(f"## ⚙️ จัดการรายชื่อ{target}")
    if st.button("⬅️ กลับหน้าส่งวารสาร"):
        st.session_state.nav_state = menu_options[0]
        st.rerun()

    with st.form("add_list_form", clear_on_submit=True):
        n = st.text_input(f"ชื่อ{target}:")
        a, p, m = st.text_area("ที่อยู่:"), st.text_input("เบอร์โทร:"), st.text_input("E-mail:")
        if st.form_submit_button("🚀 บันทึก", type="primary"):
            if n:
                try:
                    info = st.secrets["google_auth"]
                    creds = service_account.Credentials.from_service_account_info(info)
                    client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
                    client.open("JCEP_Data").worksheet(target).append_row([n, a, p, m])
                    show_message_modal(f"✅ เพิ่มข้อมูล {n} สำเร็จ")
                except: st.error("⚠️ บันทึกไม่ได้ กรุณาลองใหม่")

st.markdown('<div class="footer">Create by OCE - RMUTK</div>', unsafe_allow_html=True)
