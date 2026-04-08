import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

# --- 1. ตั้งค่าพื้นฐานและการตกแต่ง CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    /* ปุ่ม Dashboard */
    .stButton>button[kind="primary"] { background-color: #1E3A8A; color: white; border-radius: 8px; border: none; }
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border-radius: 8px; border: none; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #F0F9FF; }
    .sidebar-divider { border-top: 3px solid #000000; margin: 10px 0; }
    
    /* Footer */
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        background-color: #28a745; color: white; text-align: center; 
        padding: 10px; font-weight: bold; z-index: 100;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Popup แจ้งเตือนกลางจอพร้อมปุ่มปิด ---
@st.dialog("🔔 การแจ้งเตือนจากระบบ")
def show_message_modal(text):
    st.write(text)
    if st.button("ตกลง / ปิดหน้าต่าง"):
        st.rerun()

# --- 3. การเชื่อมต่อ Google Services ---
if "google_auth" in st.secrets:
    try:
        info = st.secrets["google_auth"]
        creds = service_account.Credentials.from_service_account_info(info)
        client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
        spreadsheet = client.open("JCEP_Data")
        sheet = spreadsheet.worksheet("Data_2026")
    except Exception as e:
        st.error(f"Error: {e}")

# --- 4. Sidebar ---
with st.sidebar:
    st.markdown("### 🏠 หน้าหลัก")
    page = st.selectbox("เลือกเมนูการใช้งาน:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin"])
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://rmutk.ac.th", use_container_width=True)
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/", use_container_width=True)
    st.link_button("📘 วารสารสหกิจก้าวหน้า (JCEP)", "https://jcep.rmutk.ac.th/", use_container_width=True)

# --- 5. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    st.image("logo.png", width=300)
    with st.form("user_form", clear_on_submit=True):
        st.subheader("📝 ฟอร์มส่งวารสาร")
        f_name = st.text_input("ชื่อ-นามสกุล")
        up_file = st.file_uploader("แนบไฟล์", type=["pdf", "docx"])
        if st.form_submit_button("ส่งข้อมูล", type="primary"):
            if up_file and f_name:
                sheet.append_row([f_name, up_file.name])
                show_message_modal("บันทึกข้อมูลเรียบร้อยแล้ว!")
            else:
                st.warning("กรุณากรอกข้อมูลให้ครบ")

# --- 6. หน้าสำหรับ Admin (ส่วนกลางกลับมาแล้ว!) ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        u_in, p_in = st.text_input("Username"), st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u_in == "bannawit.s" and p_in == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
    else:
        # ✅ ส่วนหัว Dashboard
        col_title, col_add, col_out = st.columns([6, 1.5, 1.5])
        col_title.header("🖥️ Dashboard")
        if col_add.button("➕ เพิ่ม Admin", type="primary"):
            show_message_modal("ฟังก์ชันนี้กำลังพัฒนา")
        if col_out.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()

        st.divider()

        # ✅ ข้อมูลส่วนกลาง (Main Area)
        try:
            data = sheet.get_all_records()
            if data:
                df = pd.DataFrame(data)
                
                # 1. แสดงตารางข้อมูลวารสาร
                st.subheader("📊 ตารางข้อมูลวารสาร")
                st.dataframe(df, use_container_width=True)
                
                st.write("---")
                
                # 2. แสดงระบบดาวน์โหลดไฟล์
                st.subheader("📁 ดาวน์โหลดไฟล์")
                file_col = df.columns[-1] # คอลัมน์ชื่อไฟล์
                selected_file = st.selectbox("เลือกไฟล์ที่ต้องการ:", df[file_col].unique())
                
                if selected_file:
                    file_path = f"uploaded_journals/{selected_file}"
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            st.download_button(f"💾 ดาวน์โหลด: {selected_file}", f, file_name=selected_file)
                    else:
                        st.warning("ไม่พบไฟล์ในระบบ")
            else:
                st.info("ยังไม่มีข้อมูล")
        except Exception as e:
            st.error(f"ดึงข้อมูลไม่ได้: {e}")

# --- 7. Footer ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
