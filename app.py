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
    
    /* บังคับปุ่มบวกให้เป็นสีเขียว ตัวอักษรขาว */
    div[data-testid="column"] button {
        border-radius: 8px !important;
    }
    .green-btn button {
        background-color: #28a745 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
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

# --- 2. ฟังก์ชันดึงข้อมูล (ใช้ Singleton เพื่อให้ข้อมูลนิ่ง) ---
@st.cache_resource
def get_ss_connection():
    try:
        info = st.secrets["google_auth"]
        creds = service_account.Credentials.from_service_account_info(info)
        client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
        return client.open("JCEP_Data")
    except:
        return None

ss = get_ss_connection()

if ss:
    sheet_main = ss.worksheet("Data_2026")
    sheet_uni = ss.worksheet("University")
    sheet_agency = ss.worksheet("Agency")
    
    # ดึงข้อมูลใส่ Session State เพื่อไม่ให้หาย (No Results)
    if 'data_u' not in st.session_state:
        st.session_state.data_u = sheet_uni.get_all_records()
        st.session_state.list_u = sorted([str(d['มหาวิทยาลัย']) for d in st.session_state.data_u if d.get('มหาวิทยาลัย')])
    if 'data_a' not in st.session_state:
        st.session_state.data_a = sheet_agency.get_all_records()
        st.session_state.list_a = sorted([str(d['หน่วยงาน']) for d in st.session_state.data_a if d.get('หน่วยงาน')])

# ฟังก์ชัน Popup
@st.dialog("🔔 แจ้งเตือน")
def show_msg(text):
    st.write(f"### {text}")
    if st.button("ตกลง", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

# --- 3. Sidebar ---
with st.sidebar:
    st.markdown("## 🏠 HOME")
    page = st.selectbox("เลือกเมนู:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin", "จัดการรายชื่อมหาวิทยาลัย", "จัดการรายชื่อหน่วยงาน"])
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ", "https://rmutk.ac.th", use_container_width=True)

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
            uni_sel = st.selectbox("มหาวิทยาลัย / สถาบัน", options=st.session_state.get('list_u', []), index=None, placeholder="เลือกมหาวิทยาลัย...")
        with col_u2:
            st.write("เพิ่มใหม่")
            st.markdown('<div class="green-btn">', unsafe_allow_html=True)
            if st.button("➕", key="btn_add_u"):
                st.session_state.mode_new_u = not st.session_state.get('mode_new_u', False)
            st.markdown('</div>', unsafe_allow_html=True)

        final_u = uni_sel
        if st.session_state.get('mode_new_u', False):
            final_u = st.text_input("✨ ระบุชื่อมหาวิทยาลัยใหม่:")

        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")

        # --- ส่วนหน่วยงาน ---
        col_a1, col_a2 = st.columns([8, 1])
        with col_a1:
            agency_sel = st.selectbox("สังกัด / หน่วยงาน", options=st.session_state.get('list_a', []), index=None, placeholder="เลือกหน่วยงาน...")
        with col_a2:
            st.write("เพิ่มใหม่")
            st.markdown('<div class="green-btn">', unsafe_allow_html=True)
            if st.button("➕", key="btn_add_a"):
                st.session_state.mode_new_a = not st.session_state.get('mode_new_a', False)
            st.markdown('</div>', unsafe_allow_html=True)

        final_a = agency_sel
        if st.session_state.get('mode_new_a', False):
            final_a = st.text_input("✨ ระบุชื่อหน่วยงานใหม่:")

        # --- Auto-fill ข้อมูลติดต่อ ---
        d_addr, d_phone, d_mail = "", "", ""
        if uni_sel and not st.session_state.get('mode_new_u', False):
            m = next((i for i in st.session_state.data_u if str(i['มหาวิทยาลัย']) == uni_sel), None)
            if m: d_addr, d_phone, d_mail = m.get('ที่อยู่',''), m.get('ข้อมูลติดต่อ',''), m.get('E-mail','')
        elif agency_sel and not st.session_state.get('mode_new_a', False):
            m = next((i for i in st.session_state.data_a if str(i['หน่วยงาน']) == agency_sel), None)
            if m: d_addr, d_phone, d_mail = m.get('ที่อยู่',''), m.get('ข้อมูลติดต่อ',''), m.get('E-mail','')

        address = st.text_input("ที่อยู่", value=d_addr)
        c_t, c_e = st.columns(2)
        phone = c_t.text_input("เบอร์โทรศัพท์", value=d_phone)
        email = c_e.text_input("E-mail", value=d_mail)

        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx"])
        work_link = st.text_input("🔗 ลิงก์ผลงาน (ถ้ามี)")

        # --- ส่วนการส่งข้อมูล (เอาตัวเช็คกรอกครบออกแล้ว) ---
        if st.button("🚀 ส่งข้อมูลวารสาร", type="primary", use_container_width=True):
            try:
                # จัดการไฟล์ (ถ้ามี)
                f_save_name = up_file.name if up_file else "-"
                if up_file:
                    if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                    with open(os.path.join("uploaded_journals", f_save_name), "wb") as f: f.write(up_file.getbuffer())
                
                # บันทึกเข้า Sheet หลัก
                sheet_main.append_row([prefix, f_name, l_name, final_u if final_u else "-", faculty, major, final_a if final_a else "-", address, phone, email, article_type, f_save_name, work_link])

                # บันทึกรายชื่อใหม่ (ถ้ามีการกดปุ่มบวกและกรอกชื่อไว้)
                if st.session_state.get('mode_new_u', False) and final_u:
                    sheet_uni.append_row([final_u, address, phone, email])
                if st.session_state.get('mode_new_a', False) and final_a:
                    sheet_agency.append_row([final_a, address, phone, email])

                show_msg("✅ บันทึกข้อมูลเรียบร้อยแล้ว!")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")

# --- หน้า Admin (ฟังก์ชันเดิมครบ) ---
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
            sel = st.selectbox("เลือกไฟล์:", options=df[df.columns[11]].unique(), index=None)
            if sel and sel != "-":
                path = os.path.join("uploaded_journals", str(sel))
                if os.path.exists(path):
                    with open(path, "rb") as f: st.download_button("💾 ดาวน์โหลดไฟล์", f, file_name=str(sel))

# --- หน้าจัดการรายชื่อ (ฟังก์ชันเดิมครบ) ---
elif page in ["จัดการรายชื่อมหาวิทยาลัย", "จัดการรายชื่อหน่วยงาน"]:
    if not st.session_state.get('logged_in', False):
        st.warning("🔐 กรุณาเข้าสู่ระบบที่หน้า Admin ก่อน")
    else:
        t_s = sheet_uni if page == "จัดการรายชื่อมหาวิทยาลัย" else sheet_agency
        label = "มหาวิทยาลัย" if page == "จัดการรายชื่อมหาวิทยาลัย" else "หน่วยงาน"
        st.markdown(f"## ⚙️ {page}")
        with st.form("admin_add", clear_on_submit=True):
            n = st.text_input(f"ชื่อ{label}:")
            a = st.text_area("ที่อยู่:")
            c = st.text_input("เบอร์โทร:")
            e = st.text_input("อีเมล:")
            if st.form_submit_button("🚀 บันทึก"):
                if n:
                    t_s.append_row([n, a, c, e])
                    show_msg("บันทึกสำเร็จ")

st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
