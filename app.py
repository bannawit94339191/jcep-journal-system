import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

# --- 1. ตั้งค่าพื้นฐานและการตกแต่ง CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    .stButton>button[kind="primary"] { background-color: #1E3A8A; color: white; border-radius: 8px; border: none; }
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border-radius: 8px; border: none; }
    section[data-testid="stSidebar"] { background-color: #F0F9FF; }
    .sidebar-divider { border-top: 3px solid #000000; margin: 10px 0; }
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        background-color: #28a745; color: white; text-align: center; 
        padding: 10px; font-weight: bold; z-index: 100;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Popup แจ้งเตือนกลางจอ ---
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
                # บันทึกไฟล์ลงโฟลเดอร์
                if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                with open(os.path.join("uploaded_journals", up_file.name), "wb") as f:
                    f.write(up_file.getbuffer())
                # บันทึกลง Sheet
                sheet.append_row([f_name, up_file.name])
                show_message_modal("บันทึกข้อมูลเรียบร้อยแล้ว!")
            else:
                st.warning("กรุณากรอกข้อมูลให้ครบ")

# --- 6. หน้าสำหรับ Admin (ย้ายปุ่มดาวน์โหลดเข้าตาราง) ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        u_in, p_in = st.text_input("Username"), st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u_in == "bannawit.s" and p_in == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
    else:
        # ✅ Dashboard Header
        col_title, col_add, col_out = st.columns([6, 1.5, 1.5])
        col_title.header("🖥️ Dashboard")
        if col_add.button("➕ เพิ่ม Admin", type="primary"):
            show_message_modal("ระบบจัดการ Admin กำลังอยู่ระหว่างการพัฒนา")
        if col_out.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()

        st.divider()

        # ✅ การแสดงผลตารางพร้อมปุ่มดาวน์โหลดในตัว
        st.subheader("📊 รายการส่งวารสาร (กดดาวน์โหลดได้ที่ชื่อไฟล์)")
        try:
            data = sheet.get_all_records()
            if data:
                df = pd.DataFrame(data)
                
                # แสดงตารางหลักก่อน (แบบ Read-only)
                st.dataframe(df, use_container_width=True)
                
                st.markdown("---")
                st.subheader("📁 จัดการไฟล์รายบุคคล")
                
                # วนลูปสร้างแถวปุ่มดาวน์โหลด (ย้ายจาก Dropdown มาเป็นรายบรรทัด)
                for index, row in df.iterrows():
                    file_name = str(row[df.columns[-1]]) # คอลัมน์สุดท้ายคือชื่อไฟล์
                    col_info, col_btn = st.columns([7, 3])
                    
                    with col_info:
                        st.write(f"📄 **{row[df.columns[0]]}** ({file_name})") # แสดงชื่อผู้ส่ง
                    
                    with col_btn:
                        file_path = f"uploaded_journals/{file_name}"
                        if os.path.exists(file_path):
                            with open(file_path, "rb") as f:
                                st.download_button(
                                    label=f"💾 โหลดไฟล์ของ {row[df.columns[0]]}",
                                    data=f,
                                    file_name=file_name,
                                    key=f"btn_{index}" # Key ต้องไม่ซ้ำกัน
                                )
                        else:
                            st.caption("🚫 ไม่พบไฟล์ในเซิร์ฟเวอร์")
            else:
                st.info("ยังไม่มีข้อมูลในฐานข้อมูล")
        except Exception as e:
            st.error(f"ไม่สามารถดึงข้อมูลได้: {e}")

# --- 7. Footer ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
