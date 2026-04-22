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
    st.write(f"### {text}")
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
        sheet_uni = spreadsheet.worksheet("University")
        sheet_agency = spreadsheet.worksheet("Agency")
        
        # ดึงข้อมูลทั้งหมดมาเตรียมไว้
        all_uni_data = sheet_uni.get_all_records()
        all_agency_data = sheet_agency.get_all_records()
        
        list_uni = sorted([str(d['มหาวิทยาลัย']) for d in all_uni_data if d.get('มหาวิทยาลัย')])
        list_agency = sorted([str(d['หน่วยงาน']) for d in all_agency_data if d.get('หน่วยงาน')])
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")

# --- 4. Sidebar (เมนูเดิมครบ) ---
with st.sidebar:
    st.markdown("## 🏠 HOME")
    menu_options = ["หน้าสำหรับ User", "หน้าสำหรับ Admin", "จัดการรายชื่อมหาวิทยาลัย", "จัดการรายชื่อหน่วยงาน"]
    page = st.selectbox("เลือกเมนูการใช้งาน:", menu_options)
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://rmutk.ac.th", use_container_width=True)
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/", use_container_width=True)
    st.link_button("📘 วารสารสหกิจก้าวหน้า (JCEP)", "https://jcep.rmutk.ac.th/", use_container_width=True)

# --- 5. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    st.markdown("# 📘 ระบบส่งวารสารสหกิจศึกษาก้าวหน้า")
    
    with st.container(border=True):
        st.markdown("#### 📝 ฟอร์มส่งวารสาร")
        
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้า", ["นาย", "นางสาว", "ผศ.", "รองศาสตราจารย์", "ศาสตราจารย์"])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")

        # --- ส่วนมหาวิทยาลัย (มีปุ่มบวก) ---
        col_u1, col_u2 = st.columns([8, 1])
        with col_u1:
            uni_select = st.selectbox("มหาวิทยาลัย / สถาบัน", options=list_uni, index=None, placeholder="พิมพ์ค้นหาชื่อมหาวิทยาลัย...")
        with col_u2:
            st.write("เพิ่มใหม่")
            if st.button("➕", key="btn_u"):
                st.session_state.mode_u = not st.session_state.get('mode_u', False)
        
        uni_final = uni_select
        if st.session_state.get('mode_u', False):
            uni_final = st.text_input("✨ ระบุชื่อมหาวิทยาลัยใหม่ (ข้อมูลจะบันทึกลงฐานรายชื่อให้อัตโนมัติ)")
        
        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")

        # --- ส่วนหน่วยงาน (มีปุ่มบวก) ---
        col_a1, col_a2 = st.columns([8, 1])
        with col_a1:
            agency_select = st.selectbox("สังกัด / หน่วยงาน", options=list_agency, index=None, placeholder="พิมพ์ค้นหาชื่อหน่วยงาน...")
        with col_a2:
            st.write("เพิ่มใหม่")
            if st.button("➕", key="btn_a"):
                st.session_state.mode_a = not st.session_state.get('mode_a', False)

        agency_final = agency_select
        if st.session_state.get('mode_a', False):
            agency_final = st.text_input("✨ ระบุชื่อหน่วยงานใหม่ (ข้อมูลจะบันทึกลงฐานรายชื่อให้อัตโนมัติ)")

        # --- Auto-fill ข้อมูลติดต่อ ---
        d_addr, d_phone, d_mail = "", "", ""
        if uni_select and not st.session_state.get('mode_u', False):
            match = next((i for i in all_uni_data if str(i['มหาวิทยาลัย']) == uni_select), None)
            if match: d_addr, d_phone, d_mail = match.get('ที่อยู่',''), match.get('ข้อมูลติดต่อ',''), match.get('E-mail','')
        elif agency_select and not st.session_state.get('mode_a', False):
            match = next((i for i in all_agency_data if str(i['หน่วยงาน']) == agency_select), None)
            if match: d_addr, d_phone, d_mail = match.get('ที่อยู่',''), match.get('ข้อมูลติดต่อ',''), match.get('E-mail','')

        address = st.text_input("ที่อยู่", value=d_addr)
        col_t, col_e = st.columns(2)
        phone = col_t.text_input("เบอร์โทรศัพท์", value=d_phone)
        email = col_e.text_input("E-mail", value=d_mail)

        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx", "doc"])
        work_link = st.text_input("🔗 ลิงก์ผลงาน (ถ้ามี)")

        if st.button("🚀 ส่งข้อมูลวารสาร", type="primary", use_container_width=True):
            if not (up_file and f_name and uni_final and agency_final):
                st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")
            else:
                try:
                    # บันทึกไฟล์
                    folder = "uploaded_journals"
                    if not os.path.exists(folder): os.makedirs(folder)
                    with open(os.path.join(folder, up_file.name), "wb") as f: f.write(up_file.getbuffer())
                    
                    # บันทึกลง Sheet หลัก
                    new_row = [prefix, f_name, l_name, uni_final, faculty, major, agency_final, address, phone, email, article_type, up_file.name, work_link]
                    sheet.append_row(new_row)

                    # บันทึกลงฐานรายชื่อ (ถ้ากดปุ่มบวก)
                    if st.session_state.get('mode_u', False):
                        sheet_uni.append_row([uni_final, address, phone, email])
                    if st.session_state.get('mode_a', False):
                        sheet_agency.append_row([agency_final, address, phone, email])

                    show_message_modal("✅ ส่งข้อมูลและอัปเดตรายชื่อสำเร็จ!")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")

# --- 6. หน้าสำหรับ Admin (ฟังก์ชันเดิมทั้งหมดกลับมาแล้ว) ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        st.markdown("### 🔐 กรุณาเข้าสู่ระบบ")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u_in == "bannawit.s" and p_in == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("❌ รหัสผ่านไม่ถูกต้อง")
    else:
        col_title, col_logout = st.columns([8, 1.5])
        col_title.markdown("## 🖥️ หน้าสำหรับ Admin")
        if col_logout.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()
        
        try:
            raw_data = sheet.get_all_values()
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                st.dataframe(df, use_container_width=True)
                st.divider()
                st.markdown("### 📁 จัดการไฟล์")
                col_file_idx = "Filename" if "Filename" in df.columns else df.columns[11]
                selected_file = st.selectbox("เลือกไฟล์เพื่อดาวน์โหลด:", options=df[col_file_idx].unique(), index=None)
                if selected_file:
                    f_path = os.path.join("uploaded_journals", str(selected_file))
                    if os.path.exists(f_path):
                        with open(f_path, "rb") as f:
                            st.download_button("💾 ดาวน์โหลดไฟล์", f, file_name=str(selected_file))
            else: st.info("ยังไม่มีข้อมูล")
        except Exception as e: st.error(f"Error: {e}")

# --- 7. หน้าจัดการรายชื่อ (ฟังก์ชันเดิมทั้งหมดกลับมาแล้ว) ---
elif page in ["จัดการรายชื่อมหาวิทยาลัย", "จัดการรายชื่อหน่วยงาน"]:
    if not st.session_state.get('logged_in', False):
        st.warning("🔐 กรุณาเข้าสู่ระบบที่หน้า Admin ก่อน")
    else:
        target_sheet = sheet_uni if page == "จัดการรายชื่อมหาวิทยาลัย" else sheet_agency
        label = "มหาวิทยาลัย" if page == "จัดการรายชื่อมหาวิทยาลัย" else "หน่วยงาน"
        
        st.markdown(f"## ⚙️ {page}")
        with st.form("admin_add_form", clear_on_submit=True):
            st.subheader(f"➕ เพิ่มรายชื่อ{label}")
            n = st.text_input(f"ชื่อ{label}:")
            a = st.text_area("ที่อยู่:")
            c = st.text_input("เบอร์โทร:")
            e = st.text_input("อีเมล:")
            if st.form_submit_button("🚀 บันทึกข้อมูล"):
                if n:
                    target_sheet.append_row([n, a, c, e])
                    show_message_modal("บันทึกข้อมูลสำเร็จ")
        
        st.divider()
        st.write(f"📂 รายชื่อ{label}ปัจจุบัน")
        rows = target_sheet.get_all_values()
        if len(rows) > 1:
            st.table(pd.DataFrame(rows[1:], columns=rows[0]))

st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
