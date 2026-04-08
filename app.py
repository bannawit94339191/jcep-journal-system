import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

# --- 1. การตั้งค่าพื้นฐานและการตกแต่ง CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    /* ตกแต่งปุ่ม Dashboard */
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
    st.markdown("## 🏠 หน้าหลัก")
    page = st.selectbox("เลือกเมนูการใช้งาน:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin"])
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://rmutk.ac.th", use_container_width=True)
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/", use_container_width=True)
    st.link_button("📘 วารสารสหกิจก้าวหน้า (JCEP)", "https://jcep.rmutk.ac.th/", use_container_width=True)

# --- 5. หน้าสำหรับ User (ฟอร์มครบตามภาพ f5ec84) ---
if page == "หน้าสำหรับ User":
    st.markdown("# 📘 ระบบส่งบทความวารสาร JCEP")
    st.markdown("### สำนักงานสหกิจศึกษา มทร.กรุงเทพ")
    
    with st.form("user_form", clear_on_submit=True):
        st.markdown("#### 📝 ฟอร์มส่งวารสาร")
        
        # ส่วนข้อมูลส่วนตัว
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้า", ["นาย", "นางสาว", "ผศ.", "รศ.", "ศ."])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")
        
        uni = st.text_input("มหาวิทยาลัย / สถาบัน")
        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")
        
        col_t, col_e = st.columns(2)
        phone = col_t.text_input("เบอร์โทรศัพท์")
        email = col_e.text_input("E-mail")
        
        # ส่วนข้อมูลบทความ
        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx", "doc"])
        
        if st.form_submit_button("ส่งข้อมูล", type="primary"):
            if up_file and f_name and phone:
                try:
                    # บันทึกไฟล์ลง Folder
                    if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                    file_path = os.path.join("uploaded_journals", up_file.name)
                    with open(file_path, "wb") as f:
                        f.write(up_file.getbuffer())
                    
                    # บันทึกลง Google Sheet
                    sheet.append_row([prefix, f_name, l_name, uni, faculty, major, phone, email, article_type, up_file.name])
                    
                    show_message_modal(f"✅ บันทึกข้อมูลเรียบร้อยแล้ว! ขอบคุณคุณ {f_name}")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")
            else:
                st.warning("⚠️ กรุณากรอกข้อมูลสำคัญและแนบไฟล์ให้ครบถ้วน")

# --- 6. หน้าสำหรับ Admin ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        st.markdown("### 🔐 เข้าสู่ระบบผู้ดูแลระบบ")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u_in == "bannawit.s" and p_in == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("ข้อมูลไม่ถูกต้อง")
    else:
        # ✅ Dashboard Header
        col_title, col_add, col_logout = st.columns([6, 1.5, 1.5])
        col_title.markdown("## 🖥️ Dashboard")
        
        if col_add.button("➕ เพิ่ม Admin", type="primary"):
            show_message_modal("ขณะนี้ท่านสามารถจัดการรายชื่อผู้ดูแลได้โดยตรงผ่าน Google Sheets")
            
        if col_logout.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()

        st.divider()

        # ✅ ตารางข้อมูลและระบบดาวน์โหลด
        try:
            # ดึงข้อมูลใหม่สดๆ ทุกครั้งที่เปิดหน้า
            data = sheet.get_all_records()
            if data:
                df = pd.DataFrame(data)
                st.markdown("### 📊 ตารางข้อมูลวารสาร")
                st.dataframe(df, use_container_width=True)
                
                st.write("---")
                
                # ✅ ระบบดาวน์โหลดไฟล์ (แก้ไขจุดที่เพื่อนแจ้งว่าไฟล์ไม่ขึ้น)
                st.markdown("### 📁 ดาวน์โหลดไฟล์")
                
                # บังคับเลือกจากคอลัมน์สุดท้ายของตาราง (ที่เก็บชื่อไฟล์)
                file_options = df.iloc[:, -1].dropna().unique().tolist()
                
                selected_file = st.selectbox(
                    "เลือกไฟล์ที่ต้องการดาวน์โหลดจากระบบ:", 
                    options=file_options,
                    index=None,
                    placeholder="คลิกเพื่อค้นหารายชื่อไฟล์..."
                )
                
                # แสดงปุ่มดาวน์โหลดเฉพาะเมื่อมีการเลือกไฟล์แล้วเท่านั้น
                if selected_file:
                    f_path = f"uploaded_journals/{selected_file}"
                    if os.path.exists(f_path):
                        with open(f_path, "rb") as f:
                            st.download_button(
                                label=f"💾 ดาวน์โหลดไฟล์: {selected_file}",
                                data=f,
                                file_name=str(selected_file),
                                mime="application/octet-stream",
                                use_container_width=True # ขยายปุ่มให้เต็มหน้าจอตามภาพ f5fc22
                            )
                    else:
                        st.error(f"❌ ไม่พบไฟล์ต้นฉบับ '{selected_file}' ในโฟลเดอร์เครื่อง (กรุณาเช็คโฟลเดอร์ uploaded_journals)")
            else:
                st.info("ℹ️ ยังไม่มีข้อมูลในระบบ")
        except Exception as e:
            st.error(f"ไม่สามารถดึงข้อมูลได้: {e}")

# --- 7. Footer ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
