import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os
import re
import time
from datetime import datetime
import plotly.express as px # เพิ่มสำหรับทำกราฟแยกสี

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

# --- 3. ระบบ Session Timeout (1 ชั่วโมง) ---
if 'last_activity' not in st.session_state:
    st.session_state.last_activity = time.time()

# ตรวจสอบเวลาว่าง (Inactivity)
if st.session_state.get('logged_in', False):
    elapsed_time = time.time() - st.session_state.last_activity
    if elapsed_time > 3600: # 1 ชม.
        st.session_state.logged_in = False
        st.session_state.last_activity = time.time()
        st.warning("เซสชันหมดอายุเนื่องจากไม่มีการเคลื่อนไหวเกิน 1 ชั่วโมง กรุณาเข้าสู่ระบบใหม่")
        st.rerun()

# --- 4. ระบบดึงข้อมูลและ Cache ---
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

# --- 5. Navigation ---
menu_options = ["หน้าสำหรับกรอกข้อมูล", "หน้าสำหรับ Admin", "เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน", "เพิ่มข้อมูลหน่วยงาน/สังกัด"]
if 'nav_state' not in st.session_state:
    st.session_state.nav_state = menu_options[0]

# --- 6. ฟังก์ชัน Popup ---
@st.dialog("🔔 การแจ้งเตือนจากระบบ")
def show_message_modal(text):
    st.write(f"<div style='text-align: center; font-size: 1.1rem;'>{text}</div>", unsafe_allow_html=True)
    if st.button("ปิดหน้าต่าง", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- 7. Sidebar ---
with st.sidebar:
    st.markdown("## 🏠 HOME")
    page = st.selectbox("เลือกเมนูการใช้งาน:", menu_options, index=menu_options.index(st.session_state.nav_state))
    if page != st.session_state.nav_state:
        st.session_state.nav_state = page
        st.rerun()
    if st.button("🔄 Clear System Cache", use_container_width=True):
        st.cache_data.clear()
        st.success("เคลียร์ข้อมูลเรียบร้อย")
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

# --- 8. หน้าสำหรับกรอกข้อมูล ---
if st.session_state.nav_state == "หน้าสำหรับกรอกข้อมูล":
    st.markdown("# 📘 ระบบส่งวารสาร JCEP")
    st.markdown("#### 📝 ฟอร์มส่งวารสาร")
    
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

        address = st.text_area("ที่อยู่สำหรับจัดส่งเอกสาร", value=auto_addr)
        col_t, col_e = st.columns(2)
        phone = col_t.text_input("เบอร์โทรศัพท์ (ระบุเฉพาะตัวเลข)", value=auto_phone)
        email = col_e.text_input("E-mail", value=auto_email)
        
        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx"])
        
        if st.button("✅ ส่งข้อมูลวารสาร", type="primary", use_container_width=True):
            if not (f_name and phone and email and up_file):
                st.warning("⚠️ กรุณากรอกข้อมูลและแนบไฟล์ให้ครบถ้วน")
            elif not validate_email(email):
                st.error("❌ รูปแบบ E-mail ไม่ถูกต้อง")
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
                    
                    if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                    with open(os.path.join("uploaded_journals", up_file.name), "wb") as f: f.write(up_file.getbuffer())
                    
                    sheet.append_row([unique_id, prefix, f_name, l_name, uni, affiliation, address, phone, email, article_type, up_file.name, datetime.now().strftime("%Y-%m-%d %H:%M")])
                    
                    show_message_modal(f"✅ บันทึกข้อมูลสำเร็จ!<br>เลขที่รับเรื่องของคุณคือ: <b>{unique_id}</b><br>โปรดจดจำเลขนี้เพื่อใช้ติดตามสถานะ")
                except Exception as e: st.error(f"Error: {e}")

# --- 9. หน้าสำหรับ Admin (Search + Dashboard) ---
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
        st.session_state.last_activity = time.time() # Update Activity
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
                
                # --- กราฟแยกสี 3 ประเภท (Plotly) ---
                st.markdown("### 📊 สถิติประเภทบทความ")
                type_counts = df['ประเภทบทความ'].value_counts().reset_index()
                type_counts.columns = ['ประเภท', 'จำนวน']
                
                fig = px.bar(type_counts, x='ประเภท', y='จำนวน', 
                             color='ประเภท',
                             color_discrete_map={
                                 "บทความวิจัย": "#1E3A8A",   # น้ำเงิน
                                 "บทความวิชาการ": "#28a745", # เขียว
                                 "อื่นๆ": "#dc3545"           # แดง
                             })
                st.plotly_chart(fig, use_container_width=True)
                
                # --- Search & Filter ---
                st.divider()
                col_s1, col_s2 = st.columns([2, 1])
                search_query = col_s1.text_input("🔍 ค้นหา (ชื่อ-สกุล หรือ Unique ID):")
                filter_type = col_s2.multiselect("กรองประเภท:", options=["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], default=["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"])
                
                mask = (df['ชื่อ'].str.contains(search_query, case=False) | 
                        df['เลขที่รับเรื่อง'].str.contains(search_query, case=False) if 'เลขที่รับเรื่อง' in df.columns else df.iloc[:,0].str.contains(search_query, case=False))
                mask &= df['ประเภทบทความ'].isin(filter_type)
                
                st.dataframe(df[mask], use_container_width=True)
            else:
                st.info("ℹ️ ยังไม่มีข้อมูลการส่งวารสารในระบบ")
        except Exception as e: st.error(f"ดึงข้อมูลไม่ได้: {e}")

# --- 10. หน้าเพิ่มข้อมูลสถาบัน/หน่วยงาน ---
elif st.session_state.nav_state in ["เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน", "เพิ่มข้อมูลหน่วยงาน/สังกัด"]:
    target_name = "University" if st.session_state.nav_state == "เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน" else "Agency"
    label = "มหาวิทยาลัย/สถาบัน" if target_name == "University" else "หน่วยงาน/สังกัด"
    current_df = df_uni if target_name == "University" else df_agency
    
    st.markdown(f"## ⚙️ {st.session_state.nav_state}")
    if st.button("⬅️ กลับหน้าสำหรับกรอกข้อมูล"):
        st.session_state.nav_state = "หน้าสำหรับกรอกข้อมูล"
        st.rerun()

    with st.form("add_list_form", clear_on_submit=True):
        st.subheader(f"➕ เพิ่มข้อมูล{label}")
        new_name = st.text_input(f"ชื่อ{label}:").strip()
        new_addr, new_contact, new_mail = st.text_area("ที่อยู่:"), st.text_input("เบอร์โทร:"), st.text_input("E-mail:")
        if st.form_submit_button("🚀 บันทึก", type="primary"):
            if new_name:
                try:
                    info = st.secrets["google_auth"]
                    creds = service_account.Credentials.from_service_account_info(info)
                    client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
                    client.open("JCEP_Data").worksheet(target_name).append_row([new_name, new_addr, new_contact, new_mail])
                    show_message_modal(f"✅ บันทึกข้อมูล{label}สำเร็จ")
                except Exception as e: st.error(f"บันทึกไม่ได้: {e}")
            else: st.error("กรุณากรอกชื่อ")
    
    st.divider()
    st.markdown(f"### 📋 รายชื่อ{label}ทั้งหมดในระบบ")
    st.dataframe(current_df, use_container_width=True)

st.markdown('<div class="footer">Create by OCE - RMUTK</div>', unsafe_allow_html=True)
