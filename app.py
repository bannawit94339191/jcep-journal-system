import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

# --- 1. การตั้งค่าพื้นฐานและ CSS ---
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

# --- 2. ฟังก์ชัน Popup แจ้งเตือนกลางจอ (Modal) ---
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
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")

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
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx"])
        if st.form_submit_button("ส่งข้อมูล", type="primary"):
            if up_file and f_name:
                # บันทึกไฟล์เข้าโฟลเดอร์เครื่อง
                if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                with open(os.path.join("uploaded_journals", up_file.name), "wb") as f:
                    f.write(up_file.getbuffer())
                # บันทึกชื่อไฟล์ลง Google Sheet
                sheet.append_row([f_name, up_file.name])
                show_message_modal("✅ ระบบได้ทำการบันทึกข้อมูลเรียบร้อยแล้ว!")
            else:
                st.warning("กรุณากรอกข้อมูลและแนบไฟล์ให้ครบถ้วน")

# --- 6. หน้าสำหรับ Admin ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u_in == "bannawit.s" and p_in == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
    else:
        # ✅ Dashboard Header: ปุ่มจัดชิดกันทางขวา
        col_title, col_add, col_logout = st.columns([6, 1.5, 1.5])
        col_title.header("🖥️ Dashboard")
        if col_add.button("➕ เพิ่ม Admin", type="primary"):
            show_message_modal("ระบบจัดการ Admin กำลังอยู่ในช่วงพัฒนา")
        if col_logout.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()

        st.divider()

        # ✅ การแสดงผลส่วนกลาง (ตารางและระบบดาวน์โหลด)
        try:
            data = sheet.get_all_records()
            if data:
                df = pd.DataFrame(data)
                
                # แสดงตารางข้อมูลวารสาร
                st.subheader("📊 ตารางข้อมูลวารสาร")
                st.dataframe(df, use_container_width=True)
                
                st.write("---")
                
                # ✅ ระบบดาวน์โหลดไฟล์แบบเลือกรายชื่อ
                st.subheader("📁 ดาวน์โหลดไฟล์")
                
                # ดึงรายชื่อไฟล์จากคอลัมน์สุดท้ายของ Sheet มาทำรายการให้เลือก
                file_column = df.columns[-1] 
                file_list = df[file_column].unique().tolist()
                
                selected_file = st.selectbox(
                    "เลือกไฟล์ที่ต้องการดาวน์โหลดเข้าเครื่อง:", 
                    options=file_list,
                    index=None,
                    placeholder="คลิกเพื่อเลือกไฟล์..."
                )
                
                if selected_file:
                    file_path = f"uploaded_journals/{selected_file}"
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label=f"💾 กดดาวน์โหลด: {selected_file}",
                                data=f,
                                file_name=str(selected_file),
                                mime="application/octet-stream"
                            )
                    else:
                        st.warning(f"⚠️ ไม่พบไฟล์ {selected_file} ในเครื่อง (กรุณาตรวจสอบโฟลเดอร์ uploaded_journals)")
            else:
                st.info("ยังไม่มีข้อมูลวารสารในระบบ")
        except Exception as e:
            st.error(f"ไม่สามารถดึงข้อมูลจาก Sheets ได้: {e}")

# --- 7. Footer ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
