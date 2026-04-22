import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os
import re
import time
from datetime import datetime
import plotly.express as px # อย่าลืมใส่ requirements.txt

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

# --- 3. ระบบดึงข้อมูลและ Cache (ป้องกัน Error 429) ---
@st.cache_data(ttl=600)
def get_google_data():
    df_empty = pd.DataFrame()
    if "google_auth" in st.secrets:
        try:
            info = st.secrets["google_auth"]
            creds = service_account.Credentials.from_service_account_info(info)
            client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
            spreadsheet = client.open("JCEP_Data")
            df_uni = pd.DataFrame(spreadsheet.worksheet("University").get_all_records())
            df_agency = pd.DataFrame(spreadsheet.worksheet("Agency").get_all_records())
            return df_uni, df_agency
        except Exception as e:
            st.warning(f"⚠️ ไม่สามารถดึงข้อมูลสดได้ (ติด Quota): {e}")
            return df_empty, df_empty
    return df_empty, df_empty

# ดึงข้อมูลและป้องกันตัวแปรหาย
df_uni, df_agency = get_google_data()
list_uni = sorted(df_uni.iloc[:, 0].tolist()) if not df_uni.empty else []
list_agency = sorted(df_agency.iloc[:, 0].tolist()) if not df_agency.empty else []

# --- 4. Navigation Control ---
menu_options = ["หน้าสำหรับกรอกข้อมูล", "หน้าสำหรับ Admin", "เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน", "เพิ่มข้อมูลหน่วยงาน/สังกัด"]

if 'nav_state' not in st.session_state:
    st.session_state.nav_state = menu_options[0]

# --- 5. ระบบ Session Timeout (1 ชั่วโมง) ---
if st.session_state.get('logged_in', False):
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = time.time()
    
    if time.time() - st.session_state.last_activity > 3600:
        st.session_state.logged_in = False
        st.warning("เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่")
        st.rerun()

# --- 6. ฟังก์ชัน Popup ---
@st.dialog("🔔 การแจ้งเตือน")
def show_message_modal(text):
    st.write(f"<div style='text-align: center;'>{text}</div>", unsafe_allow_html=True)
    if st.button("ปิดหน้าต่าง", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- 7. Sidebar ---
with st.sidebar:
    st.markdown("## 🏠 HOME")
    # แก้ปัญหา ValueError จากรูปที่ 5
    try:
        idx = menu_options.index(st.session_state.nav_state)
    except:
        idx = 0
    
    page = st.selectbox("เลือกเมนู:", menu_options, index=idx)
    if page != st.session_state.nav_state:
        st.session_state.nav_state = page
        st.rerun()
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://rmutk.ac.th", use_container_width=True)

# --- 8. หน้าสำหรับกรอกข้อมูล ---
if st.session_state.nav_state == "หน้าสำหรับกรอกข้อมูล":
    st.markdown("# 📘 ระบบส่งวารสารสหกิจศึกษาก้าวหน้า")
    st.info("💡 กรณีไม่พบรายชื่อในรายการ โปรดเลือกเมนูเพิ่มข้อมูลที่แถบด้านข้าง (Sidebar)")
    
    with st.container(border=True):
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้าชื่อ", ["นาย", "นางสาว", "ผศ.", "รศ.", "ศ."])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")
        
        # แก้ NameError จากรูปที่ 8 (ใส่ออปชั่นเสริมเป็น list ว่าง)
        uni = st.selectbox("มหาวิทยาลัย / สถาบัน", options=list_uni if list_uni else ["--ไม่พบข้อมูล--"], index=None, placeholder="เลือกมหาวิทยาลัย...")
        affiliation = st.selectbox("สังกัด / หน่วยงาน", options=list_agency if list_agency else ["--ไม่พบข้อมูล--"], index=None, placeholder="เลือกหน่วยงาน...")

        # Auto-fill
        auto_addr, auto_phone, auto_email = "", "", ""
        if affiliation and affiliation != "--ไม่พบข้อมูล--" and not df_agency.empty:
            row = df_agency[df_agency.iloc[:, 0] == affiliation]
            if not row.empty: auto_addr, auto_phone, auto_email = row.iloc[0, 1], row.iloc[0, 2], row.iloc[0, 3]
        elif uni and uni != "--ไม่พบข้อมูล--" and not df_uni.empty:
            row = df_uni[df_uni.iloc[:, 0] == uni]
            if not row.empty: auto_addr, auto_phone, auto_email = row.iloc[0, 1], row.iloc[0, 2], row.iloc[0, 3]

        address = st.text_area("ที่อยู่", value=auto_addr)
        col_t, col_e = st.columns(2)
        phone = col_t.text_input("เบอร์โทรศัพท์", value=auto_phone)
        email = col_e.text_input("E-mail", value=auto_email)
        
        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx"])
        work_link = st.text_input("🔗 ลิงก์ผลงาน (ถ้ามี)") # เติมกลับมาให้ตามรูปภาพ
        
        if st.button("🚀 ส่งข้อมูลวารสาร", type="primary", use_container_width=True):
            if not (f_name and phone and email and up_file):
                st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")
            elif not validate_email(email):
                st.error("❌ อีเมลไม่ถูกต้อง")
            else:
                try:
                    info = st.secrets["google_auth"]
                    creds = service_account.Credentials.from_service_account_info(info)
                    client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
                    sheet = client.open("JCEP_Data").worksheet("Data_2026")
                    
                    data_rows = sheet.get_all_values()
                    unique_id = generate_unique_id(len(data_rows))
                    
                    if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                    with open(os.path.join("uploaded_journals", up_file.name), "wb") as f: f.write(up_file.getbuffer())
                    
                    sheet.append_row([unique_id, prefix, f_name, l_name, uni, affiliation, address, phone, email, article_type, up_file.name, work_link, datetime.now().strftime("%Y-%m-%d %H:%M")])
                    
                    show_message_modal(f"✅ บันทึกสำเร็จ!<br>เลขรับเรื่อง: <b>{unique_id}</b>")
                except Exception as e: st.error(f"Error: {e}")

# --- 9. หน้าสำหรับ Admin (Dashboard) ---
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
        col_t.markdown("## 🖥️ แผงควบคุมสำหรับ Admin")
        if col_l.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()
        
        try:
            info = st.secrets["google_auth"]
            creds = service_account.Credentials.from_service_account_info(info)
            client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
            raw_data = client.open("JCEP_Data").worksheet("Data_2026").get_all_values()
            
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                
                # กราฟ Plotly แยกสี
                st.markdown("### 📊 สถิติการส่ง")
                counts = df['ประเภทบทความ'].value_counts().reset_index()
                counts.columns = ['ประเภท', 'จำนวน']
                fig = px.bar(counts, x='ประเภท', y='จำนวน', color='ประเภท',
                             color_discrete_map={"บทความวิจัย": "#1E3A8A", "บทความวิชาการ": "#28a745", "อื่นๆ": "#dc3545"})
                st.plotly_chart(fig, use_container_width=True)
                
                # Search
                search = st.text_input("🔍 ค้นหา (ชื่อ/เลขรับเรื่อง):")
                df_filtered = df[df.iloc[:, 2].str.contains(search, case=False) | df.iloc[:, 0].str.contains(search, case=False)]
                st.dataframe(df_filtered, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูล")
        except Exception as e: st.error(f"โหลดข้อมูลไม่ได้: {e}")

# --- 10. หน้าจัดการรายชื่อ (สถาบัน/หน่วยงาน) ---
elif st.session_state.nav_state in ["เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน", "เพิ่มข้อมูลหน่วยงาน/สังกัด"]:
    target = "University" if st.session_state.nav_state == "เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน" else "Agency"
    st.markdown(f"## ⚙️ {st.session_state.nav_state}")
    
    if st.button("⬅️ กลับหน้าส่งวารสาร"):
        st.session_state.nav_state = menu_options[0]
        st.rerun()

    with st.form("add_form", clear_on_submit=True):
        n = st.text_input("ชื่อสถาบัน/หน่วยงาน:")
        a, p, m = st.text_area("ที่อยู่:"), st.text_input("เบอร์โทร:"), st.text_input("E-mail:")
        if st.form_submit_button("🚀 บันทึก", type="primary"):
            if n:
                try:
                    info = st.secrets["google_auth"]
                    creds = service_account.Credentials.from_service_account_info(info)
                    client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
                    client.open("JCEP_Data").worksheet(target).append_row([n, a, p, m])
                    show_message_modal("✅ บันทึกรายชื่อสำเร็จ")
                except: st.error("บันทึกไม่ได้")
    
    st.divider()
    st.dataframe(df_uni if target == "University" else df_agency, use_container_width=True)

st.markdown('<div class="footer">Create by OCE - RMUTK</div>', unsafe_allow_html=True)
