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
            df_uni = pd.DataFrame(spreadsheet.worksheet("University").get_all_records())
            df_agency = pd.DataFrame(spreadsheet.worksheet("Agency").get_all_records())
            return df_uni, df_agency
        except:
            return pd.DataFrame(), pd.DataFrame()
    return pd.DataFrame(), pd.DataFrame()

df_uni, df_agency = get_google_data()
list_uni = sorted(df_uni.iloc[:, 0].tolist()) if not df_uni.empty else []
list_agency = sorted(df_agency.iloc[:, 0].tolist()) if not df_agency.empty else []

# --- 4. Navigation & State Management ---
if 'nav_state' not in st.session_state:
    st.session_state.nav_state = "หน้าสำหรับกรอกข้อมูล"
if 'form_id' not in st.session_state:
    st.session_state.form_id = 0  # ใช้สำหรับ Reset หน้ากรอกข้อมูล

# --- 5. ฟังก์ชัน Popup ---
@st.dialog("🔔 การแจ้งเตือนจากระบบ")
def show_message_modal(text):
    st.write(f"<div style='text-align: center; font-size: 1.1rem;'>{text}</div>", unsafe_allow_html=True)
    if st.button("ตกลง", use_container_width=True):
        # เมื่อกดตกลง ให้เพิ่ม form_id เพื่อบังคับให้วาด Widget ใหม่ (ล้างค่า)
        st.session_state.form_id += 1
        st.rerun()

# --- 6. Sidebar ---
with st.sidebar:
    st.markdown("## 🏠 HOME")
    menu_options = ["หน้าสำหรับกรอกข้อมูล", "หน้าสำหรับ Admin", "เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน", "เพิ่มข้อมูลหน่วยงาน/สังกัด"]
    page = st.selectbox("เลือกเมนูการใช้งาน:", menu_options, index=menu_options.index(st.session_state.nav_state))
    if page != st.session_state.nav_state:
        st.session_state.nav_state = page
        st.rerun()
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://www.rmutk.ac.th/")
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/")
    st.link_button("📘 วารสาร JCEP", "https://jcep.rmutk.ac.th/")

# --- 7. หน้าสำหรับกรอกข้อมูลส่งวารสาร ---
if st.session_state.nav_state == "หน้าสำหรับกรอกข้อมูล":
    st.markdown("# 📘 ระบบส่งวารสาร JCEP")
    
    # ใช้ container และ Key ที่เปลี่ยนตาม form_id เพื่อล้างค่า
    with st.container(border=True):
        st.markdown("### 📝 ฟอร์มส่งวารสาร")
        
        # คีย์ของทุก Widget จะถูกต่อท้ายด้วย form_id
        fid = st.session_state.form_id
        
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้าชื่อ", ["นาย", "นางสาว", "ผศ.", "รศ.", "ศ."], key=f"prefix_{fid}")
        f_name = col_f.text_input("ชื่อ", key=f"fname_{fid}")
        l_name = col_l.text_input("นามสกุล", key=f"lname_{fid}")
        
        uni = st.selectbox("มหาวิทยาลัย / สถาบัน", options=list_uni, index=None, placeholder="เลือกมหาวิทยาลัย...", key=f"uni_{fid}")
        
        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ", key=f"faculty_{fid}")
        major = col_maj.text_input("สาขาวิชา", key=f"major_{fid}")
        
        affiliation = st.selectbox("สังกัด / หน่วยงาน", options=list_agency, index=None, placeholder="เลือกหน่วยงาน...", key=f"agency_{fid}")

        # ดึงข้อมูลที่อยู่/เบอร์/เมล อัตโนมัติจากชื่อมหาลัย
        auto_addr, auto_phone, auto_email = "", "", ""
        if uni and not df_uni.empty:
            row = df_uni[df_uni.iloc[:, 0] == uni]
            if not row.empty:
                auto_addr = row.iloc[0, 1] if len(row.columns) > 1 else ""
                auto_phone = row.iloc[0, 2] if len(row.columns) > 2 else ""
                auto_email = row.iloc[0, 3] if len(row.columns) > 3 else ""

        address = st.text_area("ที่อยู่จัดส่งเอกสาร", value=auto_addr, key=f"addr_{fid}")
        col_tel, col_mail = st.columns(2)
        phone = col_tel.text_input("เบอร์โทรศัพท์", value=auto_phone, key=f"phone_{fid}")
        email = col_mail.text_input("E-mail", value=auto_email, key=f"email_{fid}")
        
        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True, key=f"atype_{fid}")
        final_article_type = article_type
        if article_type == "อื่นๆ":
            other_detail = st.text_input("โปรดระบุประเภทบทความอื่นๆ:", key=f"other_{fid}")
            final_article_type = f"อื่นๆ ({other_detail})" if other_detail else "อื่นๆ"

        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx"], key=f"file_{fid}")
        work_link = st.text_input("🔗 ลิงก์ผลงาน (ถ้ามี)", key=f"link_{fid}")

        if st.button("🚀 ส่งข้อมูลวารสาร", type="primary", use_container_width=True):
            if not (f_name and l_name and phone and email and up_file and uni):
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
                    
                    # บันทึกข้อมูลลง Sheet ตามลำดับคอลัมน์
                    sheet.append_row([
                        unique_id, prefix, f_name, l_name, uni, faculty, major, affiliation, 
                        address, phone, email, final_article_type, up_file.name, datetime.now().strftime("%Y-%m-%d %H:%M")
                    ])
                    
                    # เรียก Popup (การล้างค่าจะเกิดขึ้นเมื่อกด "ตกลง" ใน Popup)
                    show_message_modal(f"✅ ส่งข้อมูลสำเร็จ!<br>เลขรับเรื่อง: <b>{unique_id}</b>")
                except Exception as e: st.error(f"Error: {e}")

# --- 8. หน้า Admin ---
elif st.session_state.nav_state == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        st.markdown("### 🔐 Admin Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
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
                df['ประเภทสรุป'] = df['ประเภทบทความ'].apply(lambda x: "อื่นๆ" if "อื่นๆ" in str(x) else x)
                counts = df['ประเภทสรุป'].value_counts().reset_index()
                counts.columns = ['ประเภท', 'จำนวน']
                fig = px.bar(counts, x='ประเภท', y='จำนวน', color='ประเภท',
                             color_discrete_map={"บทความวิจัย": "#1E3A8A", "บทความวิชาการ": "#28a745", "อื่นๆ": "#dc3545"})
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
        except: st.error("ดึงข้อมูลไม่สำเร็จ")

# --- 9. หน้าเพิ่มข้อมูลมหาวิทยาลัย / หน่วยงาน ---
elif st.session_state.nav_state in ["เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน", "เพิ่มข้อมูลหน่วยงาน/สังกัด"]:
    is_uni = st.session_state.nav_state == "เพิ่มข้อมูลมหาวิทยาลัย/สถาบัน"
    target = "มหาวิทยาลัย/สถาบัน" if is_uni else "หน่วยงาน/สังกัด"
    sheet_name = "University" if is_uni else "Agency"
    current_df = df_uni if is_uni else df_agency
    
    st.markdown(f"# ⚙️ จัดการข้อมูล{target}")
    
    if st.button("⬅️ กลับหน้าส่งวารสาร"):
        st.session_state.nav_state = "หน้าสำหรับกรอกข้อมูล"
        st.rerun()
    
    # ระบบล้างฟอร์มสำหรับหน้าย่อย
    if "sub_form_counter" not in st.session_state: st.session_state.sub_form_counter = 0
    
    with st.form(key=f"sub_form_{st.session_state.sub_form_counter}", clear_on_submit=True):
        st.markdown(f"#### ➕ เพิ่มข้อมูล{target}ใหม่")
        n = st.text_input(f"ชื่อ{target}:")
        a = st.text_area("ที่อยู่:")
        p = st.text_input("เบอร์โทร:")
        m = st.text_input("E-mail:")
        
        if st.form_submit_button("🚀 บันทึกข้อมูล", type="primary"):
            if n:
                try:
                    info = st.secrets["google_auth"]
                    creds = service_account.Credentials.from_service_account_info(info)
                    client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
                    client.open("JCEP_Data").worksheet(sheet_name).append_row([n, a, p, m])
                    
                    st.cache_data.clear()
                    st.session_state.sub_form_counter += 1
                    st.success(f"✅ บันทึกข้อมูล {n} สำเร็จ")
                    time.sleep(1)
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")
            else:
                st.warning("กรุณากรอกชื่อสถาบัน")

    st.markdown("---")
    st.markdown(f"#### 📋 รายชื่อ {target} ทั้งหมด")
    if not current_df.empty:
        search = st.text_input(f"🔍 ค้นหารายชื่อ{target}:")
        filtered_df = current_df[current_df.iloc[:, 0].astype(str).str.contains(search, case=False)]
        st.dataframe(filtered_df, use_container_width=True)

st.markdown('<div class="footer">Create by OCE - RMUTK</div>', unsafe_allow_html=True)
