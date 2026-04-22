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
            # ดึงข้อมูลจาก Sheet University และ Agency
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

# --- 5. ฟังก์ชัน Popup & ล้างค่าฟอร์ม ---
@st.dialog("🔔 การแจ้งเตือนจากระบบ")
def show_message_modal(text):
    st.write(f"<div style='text-align: center; font-size: 1.1rem;'>{text}</div>", unsafe_allow_html=True)
    if st.button("ตกลงและล้างค่าหน้าจอ", use_container_width=True):
        st.cache_data.clear()
        for key in list(st.session_state.keys()):
            if key not in ['nav_state', 'logged_in']:
                del st.session_state[key]
        st.rerun()

# --- 6. Sidebar ---
with st.sidebar:
    st.markdown("## 🏠 HOME")
    try: idx = menu_options.index(st.session_state.nav_state)
    except: idx = 0
    page = st.selectbox("เลือกเมนูการใช้งาน:", menu_options, index=idx)
    if page != st.session_state.nav_state:
        st.session_state.nav_state = page
        st.rerun()
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://www.rmutk.ac.th/")
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/")
    st.link_button("📘 วารสาร JCEP", "https://jcep.rmutk.ac.th/")

# --- 7. หน้าสำหรับกรอกข้อมูล ---
if st.session_state.nav_state == "หน้าสำหรับกรอกข้อมูล":
    st.markdown("# 📘 ระบบส่งวารสาร JCEP")
    
    with st.container(border=True):
        st.markdown("### 📝 ฟอร์มส่งวารสาร")
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้าชื่อ", ["นาย", "นางสาว", "ผศ.", "รศ.", "ศ."])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")
        
        uni = st.selectbox("มหาวิทยาลัย / สถาบัน", options=list_uni, index=None, placeholder="เลือกมหาวิทยาลัย...")
        
        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")
        
        affiliation = st.selectbox("สังกัด / หน่วยงาน", options=list_agency, index=None, placeholder="เลือกหน่วยงาน...")

        # Auto-fill Logic
        auto_addr, auto_phone, auto_email = "", "", ""
        if uni and not df_uni.empty:
            row = df_uni[df_uni.iloc[:, 0] == uni]
            if not row.empty: auto_addr, auto_phone, auto_email = row.iloc[0, 1], row.iloc[0, 2], row.iloc[0, 3]

        address = st.text_area("ที่อยู่จัดส่งเอกสาร", value=auto_addr)
        col_tel, col_mail = st.columns(2)
        phone = col_tel.text_input("เบอร์โทรศัพท์", value=auto_phone)
        email = col_mail.text_input("E-mail", value=auto_email)
        
        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        final_article_type = article_type
        if article_type == "อื่นๆ":
            other_detail = st.text_input("โปรดระบุประเภทบทความอื่นๆ:")
            final_article_type = f"อื่นๆ ({other_detail})" if other_detail else "อื่นๆ"

        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx"])
        work_link = st.text_input("🔗 ลิงก์ผลงาน (ถ้ามี)")

        if st.button("🚀 ส่งข้อมูลวารสาร", type="primary", use_container_width=True):
            if not (f_name and phone and email and up_file and uni):
                st.warning("⚠️ กรุณากรอกข้อมูลสำคัญให้ครบถ้วน")
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
                    
                    sheet.append_row([
                        unique_id, prefix, f_name, l_name, uni, faculty, major, affiliation, 
                        address, phone, email, final_article_type, up_file.name, datetime.now().strftime("%Y-%m-%d %H:%M")
                    ])
                    
                    show_message_modal(f"✅ ส่งข้อมูลสำเร็จ!<br>เลขรับเรื่อง: <b>{unique_id}</b>")
                except Exception as e: st.error(f"Error: {e}")

# --- 8. หน้า Admin และ อื่นๆ ---
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
                st.markdown("### 📊 สรุปประเภทบทความ")
                df['ประเภทสรุป'] = df['ประเภทบทความ'].apply(lambda x: "อื่นๆ" if "อื่นๆ" in x else x)
                counts = df['ประเภทสรุป'].value_counts().reset_index()
                counts.columns = ['ประเภท', 'จำนวน']
                fig = px.bar(counts, x='ประเภท', y='จำนวน', color='ประเภท',
                             color_discrete_map={"บทความวิจัย": "#1E3A8A", "บทความวิชาการ": "#28a745", "อื่นๆ": "#dc3545"})
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
        except: st.error("ดึงข้อมูลไม่สำเร็จ")

# --- 9. หน้าเพิ่มข้อมูลมหาวิทยาลัย และ หน่วยงาน (เพิ่มตารางแสดงผล) ---
elif st.session_state.nav_state in ["เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน", "เพิ่มข้อมูลหน่วยงาน/สังกัด"]:
    is_uni = st.session_state.nav_state == "เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน"
    target = "University" if is_uni else "Agency"
    current_df = df_uni if is_uni else df_agency
    
    st.markdown(f"## ⚙️ จัดการรายชื่อ {target}")
    if st.button("⬅️ กลับหน้าส่งวารสาร"):
        st.session_state.nav_state = menu_options[0]
        st.rerun()
    
    # ส่วนของฟอร์มกรอกข้อมูล
    with st.form("add_form", clear_on_submit=True):
        st.markdown(f"#### ➕ เพิ่มข้อมูล{target}ใหม่")
        n = st.text_input(f"ชื่อ{target}:")
        a, p, m = st.text_area("ที่อยู่:"), st.text_input("เบอร์โทร:"), st.text_input("E-mail:")
        if st.form_submit_button("🚀 บันทึกข้อมูล"):
            if n:
                try:
                    info = st.secrets["google_auth"]
                    creds = service_account.Credentials.from_service_account_info(info)
                    client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
                    client.open("JCEP_Data").worksheet(target).append_row([n, a, p, m])
                    st.cache_data.clear() # ล้าง Cache เพื่อให้ดึงข้อมูลใหม่มาแสดง
                    st.success("บันทึกข้อมูลสำเร็จ ระบบจะแสดงข้อมูลใหม่หลัง Refresh")
                    time.sleep(1)
                    st.rerun()
                except: st.error("บันทึกไม่สำเร็จ")
    
    # --- ส่วนที่เพิ่มเข้ามา: ตารางแสดงรายชื่อที่มีอยู่แล้ว ---
    st.markdown("---")
    st.markdown(f"#### 📋 รายชื่อ {target} ทั้งหมดในระบบ")
    if not current_df.empty:
        # ช่องค้นหาภายในตาราง
        search_term = st.text_input(f"🔍 ค้นหารายชื่อ{target}:", placeholder="พิมพ์ชื่อเพื่อค้นหา...")
        if search_term:
            # ค้นหาจากคอลัมน์แรก (ชื่อ)
            filtered_df = current_df[current_df.iloc[:, 0].astype(str).str.contains(search_term, case=False)]
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.dataframe(current_df, use_container_width=True)
    else:
        st.info(f"ยังไม่มีข้อมูลรายชื่อ {target} ในระบบ")

st.markdown('<div class="footer">Create by OCE - RMUTK</div>', unsafe_allow_html=True)
