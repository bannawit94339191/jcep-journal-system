import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

# --- 1. การตั้งค่าพื้นฐานและ CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    /* ตกแต่งปุ่ม Dashboard */
    .stButton>button[kind="primary"] { background-color: #1E3A8A; color: white; border-radius: 8px; }
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border-radius: 8px; }
    
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

# --- 2. ฟังก์ชัน Popup แจ้งเตือน (ปุ่มอยู่ตรงกลาง) ---
@st.dialog("🔔 การแจ้งเตือนจากระบบ")
def show_message_modal(text):
    st.write(f"<div style='text-align: center;'>{text}</div>", unsafe_allow_html=True)
    st.write("") 
    
    # จัดปุ่มไว้ตรงกลางโดยใช้ columns
    left, center, right = st.columns([1, 2, 1])
    with center:
        if st.button("ปิดหน้าต่าง", use_container_width=True):
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
    st.markdown("## 🏠 HOME")
    page = st.selectbox("เลือกเมนูการใช้งาน:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin"])
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://rmutk.ac.th", use_container_width=True)
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/", use_container_width=True)
    st.link_button("📘 วารสารสหกิจก้าวหน้า (JCEP)", "https://jcep.rmutk.ac.th/", use_container_width=True)

# --- 5. หน้าสำหรับ User (บันทึกข้อมูลเรียงตาม A-M) ---
if page == "หน้าสำหรับ User":
    st.markdown("# 📘 ระบบส่งวารสารสหกิจศึกษาก้าวหน้า")
    st.markdown("### สำนักงานสหกิจศึกษา มหาวิทยาลัยเทคโนโลยีราชมงคลกรุงเทพ")
    
    with st.form("user_form", clear_on_submit=True):
        st.markdown("#### 📝 ฟอร์มส่งวารสาร")
        
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้า", ["นาย", "นางสาว", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์"])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")
        
        uni = st.text_input("มหาวิทยาลัย / สถาบัน")
        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")
        
        affiliation = st.text_input("สังกัด / หน่วยงาน")
        address = st.text_input("ที่อยู่")
        
        col_t, col_e = st.columns(2)
        phone = col_t.text_input("เบอร์โทรศัพท์")
        email = col_e.text_input("E-mail")
        
        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx", "doc"])
        
        if st.form_submit_button("ส่งข้อมูล", type="primary"):
            if up_file and f_name and phone:
                try:
                    folder_path = "uploaded_journals"
                    if not os.path.exists(folder_path): os.makedirs(folder_path)
                    file_path = os.path.join(folder_path, up_file.name)
                    with open(file_path, "wb") as f:
                        f.write(up_file.getbuffer())
                    
                    row_count = len(sheet.get_all_values())
                    # เรียงลำดับให้ตรงตาม Google Sheets (A: ลำดับ, B: คำนำหน้าชื่อ, C: ชื่อ, D: นามสกุล ...)
                    new_row = [
                        row_count, prefix, f_name, l_name, uni, 
                        faculty, major, affiliation, address, 
                        phone, email, article_type, up_file.name
                    ]
                    sheet.append_row(new_row)
                    show_message_modal(f"✅ บันทึกข้อมูลเรียบร้อยแล้ว!")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")
            else:
                st.warning("⚠️ กรุณากรอกข้อมูลและแนบไฟล์ให้ครบถ้วน")

# --- 6. หน้าสำหรับ Admin (กู้คืนระบบเลือกไฟล์ดาวน์โหลด) ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        st.markdown("### 🔐 เข้าสู่ระบบ Admin")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u_in == "bannawit.s" and p_in == "adminjcep"
            if u_in == "oris.m" and p_in == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
    else:
        col_title, col_add, col_logout = st.columns([6, 1.5, 1.5])
        col_title.markdown("## 🖥️ Dashboard")
        
        if col_add.button("➕ เพิ่ม Admin", type="primary"):
            show_message_modal("ขณะนี้ท่านสามารถจัดการรายชื่อผู้ดูแลได้โดยตรงผ่าน Google Sheets")
            
        if col_logout.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()

        st.divider()

        try:
            data = sheet.get_all_records()
            if data:
                df = pd.DataFrame(data)
                st.markdown("### 📊 ตารางข้อมูลวารสาร")
                st.dataframe(df, use_container_width=True)
                
                st.write("---")
                # ส่วนดาวน์โหลดที่กลับมาให้เลือกไฟล์ได้เหมือนเดิม
                st.markdown("### 📁 ดาวน์โหลดไฟล์บทความ")
                
                # ตรวจสอบชื่อคอลัมน์ "Filename" ให้ตรงกับใน Sheet
                if "Filename" in df.columns:
                    file_list = df["Filename"].dropna().unique().tolist()
                    selected_file = st.selectbox("เลือกไฟล์ที่ต้องการดาวน์โหลด:", options=file_list, index=None, placeholder="คลิกเพื่อเลือกไฟล์...")
                    
                    if selected_file:
                        f_path = os.path.join("uploaded_journals", str(selected_file))
                        if os.path.exists(f_path):
                            with open(f_path, "rb") as f:
                                st.download_button(
                                    label=f"💾 ดาวน์โหลด: {selected_file}",
                                    data=f,
                                    file_name=str(selected_file),
                                    mime="application/octet-stream",
                                    use_container_width=True
                                )
                        else:
                            st.error(f"❌ ไม่พบไฟล์ต้นฉบับในโฟลเดอร์ uploaded_journals")
                else:
                    st.warning("⚠️ ไม่พบคอลัมน์ 'Filename' ในฐานข้อมูล")
            else:
                st.info("ℹ️ ยังไม่มีข้อมูลในระบบ")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")

# --- 7. Footer ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
