import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

# --- 1. การตั้งค่าพื้นฐานและ CSS (บังคับปุ่ม + เป็นสีเขียวเข้ม) ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    /* บังคับปุ่มที่มีเครื่องหมาย + ให้เป็นสีเขียวและตัวหนังสือขาว */
    button[data-testid="baseButton-secondary"]:has(div:contains("➕")),
    button[p-id="➕"] {
        background-color: #28a745 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }
    /* สไตล์ปุ่มส่งข้อมูล (Primary) */
    .stButton>button[kind="primary"] { background-color: #1E3A8A; color: white; border-radius: 8px; }
    
    section[data-testid="stSidebar"] { background-color: #F0F9FF; }
    .sidebar-divider { border-top: 3px solid #000000; margin: 10px 0; }
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        background-color: #28a745; color: white; text-align: center; 
        padding: 10px; font-weight: bold; z-index: 100;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. ฟังก์ชันโหลดข้อมูล (ใช้ Session State ป้องกันรายชื่อหาย) ---
def load_gsheets_data():
    if 'gsheets_loaded' not in st.session_state:
        try:
            info = st.secrets["google_auth"]
            creds = service_account.Credentials.from_service_account_info(info)
            client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
            ss = client.open("JCEP_Data")
            
            st.session_state.sheet_main = ss.worksheet("Data_2026")
            st.session_state.sheet_uni = ss.worksheet("University")
            st.session_state.sheet_agency = ss.worksheet("Agency")
            
            # ดึงรายชื่อมาเก็บไว้ใน Session State
            st.session_state.all_uni = st.session_state.sheet_uni.get_all_records()
            st.session_state.all_agency = st.session_state.sheet_agency.get_all_records()
            st.session_state.list_uni = sorted([str(d['มหาวิทยาลัย']) for d in st.session_state.all_uni if d.get('มหาวิทยาลัย')])
            st.session_state.list_agency = sorted([str(d['หน่วยงาน']) for d in st.session_state.all_agency if d.get('หน่วยงาน')])
            st.session_state.gsheets_loaded = True
        except Exception as e:
            st.error(f"เชื่อมต่อ Sheets ไม่ได้: {e}")

load_gsheets_data()

# ฟังก์ชัน Popup
@st.dialog("🔔 แจ้งเตือน")
def show_msg(text):
    st.write(f"### {text}")
    if st.button("ตกลง", use_container_width=True):
        # ล้างสถานะโหลดเพื่อให้โหลดรายชื่อใหม่หลังบันทึก
        if 'gsheets_loaded' in st.session_state: del st.session_state['gsheets_loaded']
        st.rerun()

# --- 3. Sidebar (ครบทุกฟังก์ชัน) ---
with st.sidebar:
    st.markdown("## 🏠 HOME")
    page = st.selectbox("เลือกเมนูการใช้งาน:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin", "จัดการรายชื่อมหาวิทยาลัย", "จัดการรายชื่อหน่วยงาน"])
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

        # --- มหาวิทยาลัย (ปุ่มบวกเขียว + สลับช่องกรอก) ---
        col_u1, col_u2 = st.columns([8, 1])
        with col_u1:
            if not st.session_state.get('mode_u', False):
                uni_val = st.selectbox("มหาวิทยาลัย / สถาบัน", options=st.session_state.get('list_uni', []), index=None, placeholder="เลือกมหาวิทยาลัย...")
            else:
                uni_val = st.text_input("✨ ระบุชื่อมหาวิทยาลัยใหม่:", key="new_u_input")
        with col_u2:
            st.write("เพิ่มใหม่")
            if st.button("➕", key="plus_u"):
                st.session_state.mode_u = not st.session_state.get('mode_u', False)
                st.rerun()

        # --- หน่วยงาน (ปุ่มบวกเขียว + สลับช่องกรอก) ---
        col_a1, col_a2 = st.columns([8, 1])
        with col_a1:
            if not st.session_state.get('mode_a', False):
                agency_val = st.selectbox("สังกัด / หน่วยงาน", options=st.session_state.get('list_agency', []), index=None, placeholder="เลือกหน่วยงาน...")
            else:
                agency_val = st.text_input("✨ ระบุชื่อหน่วยงานใหม่:", key="new_a_input")
        with col_a2:
            st.write("เพิ่มใหม่")
            if st.button("➕", key="plus_a"):
                st.session_state.mode_a = not st.session_state.get('mode_a', False)
                st.rerun()

        faculty = st.text_input("คณะ")
        major = st.text_input("สาขาวิชา")

        # --- Auto-fill ---
        d_addr, d_phone, d_mail = "", "", ""
        if uni_val and not st.session_state.get('mode_u', False):
            m = next((i for i in st.session_state.all_uni if str(i['มหาวิทยาลัย']) == uni_val), None)
            if m: d_addr, d_phone, d_mail = m.get('ที่อยู่',''), m.get('ข้อมูลติดต่อ',''), m.get('E-mail','')
        elif agency_val and not st.session_state.get('mode_a', False):
            m = next((i for i in st.session_state.all_agency if str(i['หน่วยงาน']) == agency_val), None)
            if m: d_addr, d_phone, d_mail = m.get('ที่อยู่',''), m.get('ข้อมูลติดต่อ',''), m.get('E-mail','')

        address = st.text_input("ที่อยู่", value=d_addr)
        phone = st.text_input("เบอร์โทรศัพท์", value=d_phone)
        email = st.text_input("E-mail", value=d_mail)
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx"])

        # --- Logic ส่งข้อมูล (เช็ค มหาลัย หรือ หน่วยงาน) ---
        if st.button("🚀 ส่งข้อมูลวารสาร", type="primary", use_container_width=True):
            # ตรวจสอบว่าต้องมี (ชื่อ) และ (เบอร์) และ (ไฟล์) และ (มหาลัย OR หน่วยงาน)
            has_org = (uni_val and str(uni_val).strip() != "") or (agency_val and str(agency_val).strip() != "")
            
            if not (f_name and phone and up_file and has_org):
                st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน (ต้องระบุมหาวิทยาลัยหรือหน่วยงานอย่างใดอย่างหนึ่ง)")
            else:
                try:
                    f_name_save = up_file.name
                    if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                    with open(os.path.join("uploaded_journals", f_name_save), "wb") as f: f.write(up_file.getbuffer())
                    
                    # บันทึกลง Sheet หลัก
                    st.session_state.sheet_main.append_row([prefix, f_name, l_name, uni_val if uni_val else "-", faculty, major, agency_val if agency_val else "-", address, phone, email, "-", f_name_save, "-"])
                    
                    # บันทึกรายชื่อใหม่ (ถ้าใช้โหมดปุ่มบวก)
                    if st.session_state.get('mode_u', False) and uni_val:
                        st.session_state.sheet_uni.append_row([uni_val, address, phone, email])
                    if st.session_state.get('mode_a', False) and agency_val:
                        st.session_state.sheet_agency.append_row([agency_val, address, phone, email])

                    show_msg("✅ ส่งข้อมูลและอัปเดตรายชื่อสำเร็จ!")
                except Exception as e:
                    st.error(f"ผิดพลาด: {e}")

# --- หน้า Admin (ฟังก์ชันเดิมครบ) ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u == "bannawit.s" and p == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
    else:
        st.write("## 🖥️ ข้อมูลการส่งวารสาร")
        if st.button("🚪 ออกจากระบบ"): st.session_state.logged_in = False; st.rerun()
        data = st.session_state.sheet_main.get_all_values()
        if len(data) > 1:
            st.dataframe(pd.DataFrame(data[1:], columns=data[0]), use_container_width=True)

# --- หน้าจัดการรายชื่อ (ฟังก์ชันเดิมครบ) ---
elif page in ["จัดการรายชื่อมหาวิทยาลัย", "จัดการรายชื่อหน่วยงาน"]:
    if st.session_state.get('logged_in', False):
        target = st.session_state.sheet_uni if page == "จัดการรายชื่อมหาวิทยาลัย" else st.session_state.sheet_agency
        st.write(f"## ⚙️ {page}")
        with st.form("add_list"):
            n = st.text_input("ชื่อ:")
            a = st.text_area("ที่อยู่:")
            if st.form_submit_button("🚀 บันทึก"):
                if n: target.append_row([n, a, "", ""]); show_msg("บันทึกสำเร็จ")
    else: st.warning("🔐 กรุณาเข้าสู่ระบบหน้า Admin")

st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
