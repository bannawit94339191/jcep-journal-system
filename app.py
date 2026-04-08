import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os
import time

# --- 1. ตั้งค่า CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")
st.markdown("""
    <style>
    .stButton>button[kind="primary"] { background-color: #1E3A8A; color: white; border-radius: 8px; }
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border-radius: 8px; }
    section[data-testid="stSidebar"] { background-color: #F0F9FF; }
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        background-color: #28a745; color: white; text-align: center; 
        padding: 10px; font-weight: bold; z-index: 100;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Google Services ---
if "google_auth" in st.secrets:
    try:
        info = st.secrets["google_auth"]
        creds = service_account.Credentials.from_service_account_info(info)
        client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
        spreadsheet = client.open("JCEP_Data")
        sheet = spreadsheet.worksheet("Data_2026")
        try: admin_sheet = spreadsheet.worksheet("Admin_Users")
        except: admin_sheet = None
    except Exception as e: st.error(f"Error: {e}")

# --- 3. Sidebar ---
with st.sidebar:
    st.markdown("### 🏠 หน้าหลัก")
    page = st.selectbox("เลือกเมนูการใช้งาน:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin"])
    st.markdown("<hr style='border-top: 2px solid #000000; margin-top: 0px;'>", unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://rmutk.ac.th", use_container_width=True)
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/", use_container_width=True)
    st.link_button("📘 วารสารสหกิจก้าวหน้า (JCEP)", "https://jcep.rmutk.ac.th/", use_container_width=True)

# --- 4. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    if os.path.exists("logo.gif"): st.image("logo.gif", use_container_width=True)
    # ... (ส่วนฟอร์ม User เหมือนเดิม) ...

# --- 5. หน้าสำหรับ Admin ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        # ... (ส่วน Login เหมือนเดิม) ...
        pass
    else:
        # ✅ ส่วนหัว: ปุ่ม Add Admin ชิดกับ Logout
        col_h1, col_btn1, col_btn2, col_spacer = st.columns([6, 1.5, 1.5, 1])
        col_h1.header("🖥️ Dashboard")
        
        if col_btn1.button("➕ เพิ่ม Admin", type="primary"):
            # เรียกใช้ฟังก์ชัน Dialog เพื่อเพิ่ม Admin
            pass
            
        if col_btn2.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()

        st.divider()

        # ✅ ตารางข้อมูลวารสาร
        st.subheader("📊 ตารางข้อมูลวารสาร")
        try:
            data = sheet.get_all_records()
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
                
                # ✅ กู้คืนปุ่มดาวน์โหลดเอกสาร (Download Section)
                st.markdown("### 📁 ดาวน์โหลดไฟล์ต้นฉบับ")
                # สมมติว่าชื่อไฟล์อยู่ในคอลัมน์สุดท้ายของ Sheets
                file_column = df.columns[-1] 
                selected_file = st.selectbox("เลือกไฟล์ที่ต้องการดาวน์โหลด:", df[file_column].unique())
                
                # สร้าง Path สำหรับดาวน์โหลด
                file_path = os.path.join("uploaded_journals", str(selected_file))
                
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"💾 กดที่นี่เพื่อดาวน์โหลด: {selected_file}",
                            data=f,
                            file_name=str(selected_file),
                            mime="application/octet-stream"
                        )
                else:
                    st.warning(f"⚠️ ไม่พบไฟล์ {selected_file} ในระบบเซิร์ฟเวอร์")
            else:
                st.info("ยังไม่มีข้อมูลการส่งวารสาร")
        except Exception as e:
            st.error(f"ไม่สามารถดึงข้อมูลได้: {e}")

# --- 6. Footer ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
