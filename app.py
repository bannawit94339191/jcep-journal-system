import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

# --- 1. การตั้งค่าพื้นฐาน ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

# CSS: บังคับปุ่มบวกเป็นสีเขียว และแต่ง Sidebar
st.markdown("""
    <style>
    .stButton>button[kind="primary"] { background-color: #1E3A8A; color: white; border-radius: 8px; }
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border-radius: 8px; }
    
    /* บังคับปุ่มบวกให้เป็นสีเขียว */
    div.stButton > button:first-child:contains("➕") {
        background-color: #28a745 !important;
        color: white !important;
        border: none !important;
    }
    
    section[data-testid="stSidebar"] { background-color: #F0F9FF; }
    .sidebar-divider { border-top: 3px solid #000000; margin: 10px 0; }
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        background-color: #28a745; color: white; text-align: center; 
        padding: 10px; font-weight: bold; z-index: 100;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Google Sheets (แบบเสถียร) ---
def connect_gsheet():
    try:
        info = st.secrets["google_auth"]
        creds = service_account.Credentials.from_service_account_info(info)
        client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
        ss = client.open("JCEP_Data")
        return ss
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")
        return None

ss = connect_gsheet()

# โหลดข้อมูลรายชื่อ (ป้องกัน No Results)
if ss:
    sheet_main = ss.worksheet("Data_2026")
    sheet_uni = ss.worksheet("University")
    sheet_agency = ss.worksheet("Agency")
    
    # ดึงข้อมูลใหม่ทุกครั้งที่รันหน้า User เพื่อความชัวร์
    all_u_data = sheet_uni.get_all_records()
    all_a_data = sheet_agency.get_all_records()
    list_uni = sorted([str(d['มหาวิทยาลัย']) for d in all_u_data if d.get('มหาวิทยาลัย')])
    list_agency = sorted([str(d['หน่วยงาน']) for d in all_a_data if d.get('หน่วยงาน')])
else:
    list_uni, list_agency = [], []

# ฟังก์ชัน Popup
@st.dialog("🔔 แจ้งเตือน")
def show_msg(text):
    st.write(f"### {text}")
    if st.button("ตกลง", use_container_width=True):
        st.rerun()

# --- 3. Sidebar (ฟังก์ชันดั้งเดิมครบถ้วน) ---
with st.sidebar:
    st.markdown("## 🏠 HOME")
    menu_options = ["หน้าสำหรับ User", "หน้าสำหรับ Admin", "จัดการรายชื่อมหาวิทยาลัย", "จัดการรายชื่อหน่วยงาน"]
    page = st.selectbox("เลือกเมนูการใช้งาน:", menu_options)
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://rmutk.ac.th", use_container_width=True)
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/", use_container_width=True)
    st.link_button("📘 วารสารสหกิจก้าวหน้า (JCEP)", "https://jcep.rmutk.ac.th/", use_container_width=True)

# --- 4. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    st.markdown("# 📘 ระบบส่งวารสารสหกิจศึกษาก้าวหน้า")
    
    with st.container(border=True):
        st.markdown("#### 📝 ฟอร์มส่งวารสาร")
        
        c_p, c_f, c_l = st.columns([1, 2, 2])
        prefix = c_p.selectbox("คำนำหน้า", ["นาย", "นางสาว", "ผศ.", "รศ.", "ศ."])
        f_name = c_f.text_input("ชื่อ")
        l_name = c_l.text_input("นามสกุล")

        # --- ส่วนมหาวิทยาลัย ---
        col_u1, col_u2 = st.columns([8, 1])
        with col_u1:
            uni_sel = st.selectbox("มหาวิทยาลัย / สถาบัน", options=list_uni, index=None, placeholder="เลือกมหาวิทยาลัย...")
        with col_u2:
            st.write("เพิ่มใหม่")
            if st.button("➕", key="btn_u"):
                st.session_state.is_new_u = not st.session_state.get('is_new_u', False)
        
        final_u = uni_sel
        if st.session_state.get('is_new_u', False):
            final_u = st.text_input("✨ ระบุชื่อมหาวิทยาลัยใหม่:")

        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")

        # --- ส่วนหน่วยงาน ---
        col_a1, col_a2 = st.columns([8, 1])
        with col_a1:
            agency_sel = st.selectbox("สังกัด / หน่วยงาน", options=list_agency, index=None, placeholder="เลือกหน่วยงาน...")
        with col_a2:
            st.write("เพิ่มใหม่")
            if st.button("➕", key="btn_a"):
                st.session_state.is_new_a = not st.session_state.get('is_new_a', False)

        final_a = agency_sel
        if st.session_state.get('is_new_a', False):
            final_a = st.text_input("✨ ระบุชื่อหน่วยงานใหม่:")

        # --- ระบบ Auto-fill (ดึงข้อมูลติดต่อจาก Sheet) ---
        d_addr, d_phone, d_mail = "", "", ""
        if uni_sel and not st.session_state.get('is_new_u', False):
            m = next((i for i in all_u_data if str(i['มหาวิทยาลัย']) == uni_sel), None)
            if m: d_addr, d_phone, d_mail = m.get('ที่อยู่',''), m.get('ข้อมูลติดต่อ',''), m.get('E-mail','')
        elif agency_sel and not st.session_state.get('is_new_a', False):
            m = next((i for i in all_a_data if str(i['หน่วยงาน']) == agency_sel), None)
            if m: d_addr, d_phone, d_mail = m.get('ที่อยู่',''), m.get('ข้อมูลติดต่อ',''), m.get('E-mail','')

        address = st.text_input("ที่อยู่", value=d_addr)
        c_t, c_e = st.columns(2)
        phone = c_t.text_input("เบอร์โทรศัพท์", value=d_phone)
        email = c_e.text_input("E-mail", value=d_mail)

        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx"])
        work_link = st.text_input("🔗 ลิงก์ผลงาน (ถ้ามี)")

        # ปุ่มส่งข้อมูล (ไม่บังคับกรอกครบ)
        if st.button("🚀 ส่งข้อมูลวารสาร", type="primary", use_container_width=True):
            try:
                f_name_save = up_file.name if up_file else "-"
                if up_file:
                    if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                    with open(os.path.join("uploaded_journals", f_name_save), "wb") as f: f.write(up_file.getbuffer())
                
                sheet_main.append_row([prefix, f_name, l_name, final_u, faculty, major, final_a, address, phone, email, article_type, f_name_save, work_link])
                
                # บันทึกรายชื่อใหม่ถ้ากดปุ่มบวก
                if st.session_state.get('is_new_u', False) and final_u:
                    sheet_uni.append_row([final_u, address, phone, email])
                if st.session_state.get('is_new_a', False) and final_a:
                    sheet_agency.append_row([final_a, address, phone, email])

                show_msg("✅ ส่งข้อมูลเรียบร้อยแล้ว!")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")

# --- 5. หน้าสำหรับ Admin (ฟังก์ชันเดิมครบถ้วน) ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        st.markdown("### 🔐 กรุณาเข้าสู่ระบบ")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u_in == "bannawit.s" and p_in == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("❌ ข้อมูลไม่ถูกต้อง")
    else:
        col_t, col_l = st.columns([8, 1.5])
        col_t.markdown("## 🖥️ หน้าสำหรับ Admin")
        if col_l.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()
        
        raw = sheet_main.get_all_values()
        if len(raw) > 1:
            df = pd.DataFrame(raw[1:], columns=raw[0])
            st.dataframe(df, use_container_width=True)
            st.divider()
            col_idx = 11 if len(df.columns) > 11 else -1
            sel = st.selectbox("เลือกไฟล์:", options=df.iloc[:, col_idx].unique(), index=None)
            if sel and sel != "-":
                path = os.path.join("uploaded_journals", str(sel))
                if os.path.exists(path):
                    with open(path, "rb") as f: st.download_button("💾 โหลดไฟล์", f, file_name=str(sel))

# --- 6. หน้าจัดการรายชื่อ (ฟังก์ชันเดิมครบถ้วน) ---
elif page in ["จัดการรายชื่อมหาวิทยาลัย", "จัดการรายชื่อหน่วยงาน"]:
    if not st.session_state.get('logged_in', False):
        st.warning("🔐 กรุณาเข้าสู่ระบบที่หน้า Admin")
    else:
        target_s = sheet_uni if page == "จัดการรายชื่อมหาวิทยาลัย" else sheet_agency
        label = "มหาวิทยาลัย" if page == "จัดการรายชื่อมหาวิทยาลัย" else "หน่วยงาน"
        st.markdown(f"## ⚙️ {page}")
        with st.form("admin_add_form", clear_on_submit=True):
            n = st.text_input(f"ชื่อ{label}:")
            a = st.text_area("ที่อยู่:")
            c = st.text_input("เบอร์โทร:")
            e = st.text_input("อีเมล:")
            if st.form_submit_button("🚀 บันทึก"):
                if n:
                    target_s.append_row([n, a, c, e])
                    show_msg("บันทึกสำเร็จ")
        
        rows = target_s.get_all_values()
        if len(rows) > 1: st.table(pd.DataFrame(rows[1:], columns=rows[0]))

st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
