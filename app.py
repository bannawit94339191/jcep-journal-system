import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

# --- 1. ตั้งค่าพื้นฐานและการตกแต่ง CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    /* ปุ่มส่งข้อมูลสีน้ำเงินเข้ม */
    .stButton>button[kind="primary"] { background-color: #1E3A8A; color: white; border-radius: 8px; border: none; }
    /* ปุ่มยกเลิกสีแดง */
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border-radius: 8px; border: none; }
    
    /* ตกแต่ง Sidebar */
    section[data-testid="stSidebar"] { background-color: #F0F9FF; }
    [data-testid="stSidebar"] h3 { color: #1E3A8A; font-weight: bold; }

    /* Footer สีเขียว */
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        background-color: #28a745; color: white; text-align: center; 
        padding: 10px; font-weight: bold; z-index: 100;
    }
    .main { padding-bottom: 80px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Google Services (ส่วนนี้เหมือนเดิม) ---
if "google_auth" in st.secrets:
    try:
        info = st.secrets["google_auth"]
        creds = service_account.Credentials.from_service_account_info(info)
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_with_scope = creds.with_scopes(scope)
        client = gspread.authorize(creds_with_scope)
        spreadsheet = client.open("JCEP_Data")
        sheet = spreadsheet.worksheet("Data_2026")
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")

# --- 3. Sidebar (เมนูด้านข้างพร้อมปุ่ม Link) ---
with st.sidebar:
    # หัวข้อหน้าหลัก
    st.markdown("### 🏠 HOME")
    
    page = st.selectbox(
        "เลือกเมนูการใช้งาน:",
        ["หน้าสำหรับ User", "หน้าสำหรับ Admin"]
    )
    
    # เส้นคั่น
    st.markdown("<hr style='border-top: 2px solid #000000; margin-top: 0px;'>", unsafe_allow_html=True)
    
    # ✅ ส่วนปุ่ม Link ทั้ง 3 ปุ่ม (ใช้ st.link_button เพื่อความสวยงาม)
    st.markdown("🔗 **ลิงก์ที่เกี่ยวข้อง**")
    
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://rmutk.ac.th", use_container_width=True)
    
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/", use_container_width=True)
    
    st.link_button("📘 วารสารสหกิจก้าวหน้า (JCEP)", "https://jcep.rmutk.ac.th/", use_container_width=True)

# --- 4. หน้าสำหรับ User ---
