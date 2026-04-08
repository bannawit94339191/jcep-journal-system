import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

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

# --- 2. ฟังก์ชัน Popup แจ้งเตือน ---
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
    st.markdown("## 🏠 หน้าหลัก")
    page = st.selectbox("เลือกเมนูการใช้งาน:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin"])
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://rmutk.ac.th", use_container_width=True)
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/", use_container_width=True)
    st.link_button("📘 วารสารสหกิจก้าวหน้า (JCEP)", "https://jcep.rmutk.ac.th/", use_container_width=True)

# --- 5. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    st.markdown("# 📘 ระบบส่งบทความวารสาร JCEP")
    st.markdown("### สำนักงานสหกิจศึกษา มทร.กรุงเทพ")
    
    with st.form("user_form", clear_on_submit=True):
        st.markdown("#### 📝 ฟอร์มส่งวารสาร")
        
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้า", ["นาย", "นางสาว", "ผศ.", "รศ.", "ศ."])
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
                    # 1. บันทึกไฟล์ลง Folder ทันที
                    folder_path = "uploaded_journals"
                    if not os.path.exists(folder_path): os.makedirs(folder_path)
                    file_path = os.path.join(folder_path, up_file.name)
                    with open(file_path, "wb") as f:
                        f.write(up_file.getbuffer())
                    
                    # 2. บันทึกลง Google Sheet (ลำดับ A-M ให้ตรงภาพ f655a3)
                    row_count = len(sheet.get_all_values())
                    new_row = [
                        row_count, prefix, f_name, l_name, uni, 
                        faculty, major, affiliation, address, 
                        phone, email, article_type, up_file.name
                    ]
                    sheet.append_row(new_row)
                    
                    show_message_modal(f"✅ บันทึกข้อมูลเรียบร้อยแล้ว!")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการบันทึก: {e}")
            else:
                st.warning("⚠️ กรุณากรอกข้อมูลสำคัญและแนบไฟล์ให้ครบถ้วน")

# --- 6. หน้าสำหรับ Admin (กู้คืนระบบดาวน์โหลด) ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        st.markdown("### 🔐 เข้าสู่ระบบ Admin")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u_in == "bannawit.s" and p_in == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
    else:
        col_title, col_logout = st.columns([8, 1.5])
        col_title.markdown("## 🖥️ Dashboard")
        if col_logout.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()

        st.divider()

        try:
            # ดึงข้อมูลใหม่สดๆ
            data = sheet.get_all_records()
            if data:
                df = pd.DataFrame(data)
                st.markdown("### 📊 ตารางข้อมูลวารสาร")
                st.dataframe(df, use_container_width=True)
                
                st.write("---")
                
                # ✅ กู้คืนระบบดาวน์โหลดไฟล์
                st.markdown("### 📁 ดาวน์โหลดไฟล์บทความ")
                
                # ตรวจสอบชื่อคอลัมน์เก็บไฟล์ (ต้องตรงกับหัวตาราง 'Filename' ในภาพ f655a3)
                column_name = "Filename" 
                if column_name in df.columns:
                    file_list = df[column_name].dropna().unique().tolist()
                    
                    selected_file = st.selectbox(
                        "เลือกไฟล์ที่ต้องการดาวน์โหลด:", 
                        options=file_list,
                        index=None,
                        placeholder="ค้นหาชื่อไฟล์จากรายการนี้..."
                    )
                    
                    if selected_file:
                        f_path = os.path.join("uploaded_journals", str(selected_file))
                        
                        if os.path.exists(f_path):
                            with open(f_path, "rb") as f:
                                st.download_button(
                                    label=f"💾 ดาวน์โหลด: {selected_file}",
                                    data=f,
                                    file_name=str(selected_file),
                                    mime="application/octet-stream",
                                    use_container_width=True # ขยายปุ่มให้เต็มหน้าจอตามภาพ f5fc22
                                )
                        else:
                            st.error(f"❌ ไม่พบไฟล์ต้นฉบับในเครื่อง (Path: {f_path})")
                else:
                    st.warning("⚠️ ไม่พบคอลัมน์ 'Filename' ในฐานข้อมูล กรุณาตรวจสอบหัวตาราง")
            else:
                st.info("ℹ️ ยังไม่มีข้อมูลในระบบ")
        except Exception as e:
            st.error(f"ไม่สามารถโหลดข้อมูลได้: {e}")

# --- 7. Footer ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
