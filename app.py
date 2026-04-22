import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

# --- 1. การตั้งค่าพื้นฐานและ CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    /* ปุ่มส่งข้อมูลและปุ่มหลัก */
    .stButton>button[kind="primary"] { background-color: #1E3A8A; color: white; border-radius: 8px; }
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border-radius: 8px; }
    
    /* สไตล์สำหรับปุ่มบวก (+) สีเขียว */
    div[data-testid="column"] button:has(div:contains("➕")) {
        background-color: #28a745 !important;
        color: white !important;
        border-radius: 8px !important;
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

# --- 2. ฟังก์ชัน Popup แจ้งเตือน ---
@st.dialog("🔔 การแจ้งเตือนจากระบบ")
def show_message_modal(text):
    st.write(f"<div style='text-align: center; font-size: 1.2rem;'>{text}</div>", unsafe_allow_html=True)
    if st.button("ปิดหน้าต่าง", use_container_width=True):
        st.rerun()

# --- 3. การเชื่อมต่อ Google Services (ย้ายใส่ Session State เพื่อไม่ให้ข้อมูลหาย) ---
if "google_auth" in st.secrets:
    if 'list_uni' not in st.session_state:
        try:
            info = st.secrets["google_auth"]
            creds = service_account.Credentials.from_service_account_info(info)
            client = gspread.authorize(creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
            spreadsheet = client.open("JCEP_Data")
            
            st.session_state.sheet = spreadsheet.worksheet("Data_2026")
            st.session_state.sheet_uni = spreadsheet.worksheet("University")
            st.session_state.sheet_agency = spreadsheet.worksheet("Agency")
            
            st.session_state.all_uni_data = st.session_state.sheet_uni.get_all_records()
            st.session_state.all_agency_data = st.session_state.sheet_agency.get_all_records()
            
            st.session_state.list_uni = sorted([str(d['มหาวิทยาลัย']) for d in st.session_state.all_uni_data if d.get('มหาวิทยาลัย')])
            st.session_state.list_agency = sorted([str(d['หน่วยงาน']) for d in st.session_state.all_agency_data if d.get('หน่วยงาน')])
        except Exception as e:
            st.error(f"การเชื่อมต่อผิดพลาด: {e}")

# --- 4. Sidebar ---
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
    
    # ใช้ Container แทน Form เพื่อให้ปุ่มบวกทำงานได้ทันทีโดยไม่ต้องกด Submit
    with st.container(border=True):
        st.markdown("#### 📝 ฟอร์มส่งวารสาร")
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้า", ["นาย", "นางสาว", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์"])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")
        
        # --- มหาวิทยาลัย (ปุ่มบวกสีเขียว) ---
        col_u1, col_u2 = st.columns([8, 1])
        with col_u1:
            if not st.session_state.get('add_mode_uni', False):
                uni_select = st.selectbox("มหาวิทยาลัย / สถาบัน", options=st.session_state.get('list_uni', []), index=None, placeholder="พิมพ์ค้นหาชื่อมหาวิทยาลัย...")
                uni_name = uni_select
            else:
                uni_name = st.text_input("ระบุชื่อมหาวิทยาลัยใหม่:", placeholder="พิมพ์ชื่อมหาวิทยาลัยที่นี่...")
        with col_u2:
            st.write("เพิ่มใหม่")
            if st.button("➕", key="btn_u"):
                st.session_state.add_mode_uni = not st.session_state.get('add_mode_uni', False)
                st.rerun()

        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")
        
        # --- หน่วยงาน (ปุ่มบวกสีเขียว) ---
        col_a1, col_a2 = st.columns([8, 1])
        with col_a1:
            if not st.session_state.get('add_mode_agency', False):
                agency_select = st.selectbox("สังกัด / หน่วยงาน", options=st.session_state.get('list_agency', []), index=None, placeholder="พิมพ์ค้นหาชื่อหน่วยงาน...")
                agency_name = agency_select
            else:
                agency_name = st.text_input("ระบุชื่อหน่วยงานใหม่:", placeholder="พิมพ์ชื่อหน่วยงานที่นี่...")
        with col_a2:
            st.write("เพิ่มใหม่")
            if st.button("➕", key="btn_a"):
                st.session_state.add_mode_agency = not st.session_state.get('add_mode_agency', False)
                st.rerun()

        # --- ระบบ Auto-fill ---
        d_addr, d_phone, d_mail = "", "", ""
        if not st.session_state.get('add_mode_uni', False) and uni_name:
            match = next((item for item in st.session_state.all_uni_data if item['มหาวิทยาลัย'] == uni_name), None)
            if match: d_addr, d_phone, d_mail = match.get('ที่อยู่', ''), match.get('ข้อมูลติดต่อ', ''), match.get('E-mail', '')
        elif not st.session_state.get('add_mode_agency', False) and agency_name:
            match = next((item for item in st.session_state.all_agency_data if item['หน่วยงาน'] == agency_name), None)
            if match: d_addr, d_phone, d_mail = match.get('ที่อยู่', ''), match.get('ข้อมูลติดต่อ', ''), match.get('E-mail', '')

        address = st.text_input("ที่อยู่", value=d_addr)
        col_t, col_e = st.columns(2)
        phone = col_t.text_input("เบอร์โทรศัพท์", value=d_phone)
        email = col_e.text_input("E-mail", value=d_mail)
        
        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx", "doc"])
        work_link = st.text_input("🔗 ลิงก์ผลงาน (ถ้ามี)", placeholder="https://example.com/your-work")
        
        if st.button("ส่งข้อมูล", type="primary", use_container_width=True):
            # LOGIC เช็คกรอกครบ: ต้องมี (มหาลัย OR หน่วยงาน) AND (ชื่อ, เบอร์, ไฟล์)
            has_org = (uni_name and uni_name.strip() != "") or (agency_name and agency_name.strip() != "")
            
            if not (has_org and f_name and phone and up_file):
                st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน (ต้องระบุมหาวิทยาลัยหรือหน่วยงานอย่างใดอย่างหนึ่ง)")
            else:
                try:
                    folder_path = "uploaded_journals"
                    if not os.path.exists(folder_path): os.makedirs(folder_path)
                    file_path = os.path.join(folder_path, up_file.name)
                    with open(file_path, "wb") as f: f.write(up_file.getbuffer())
                    
                    new_row = [prefix, f_name, l_name, uni_name if uni_name else "-", faculty, major, agency_name if agency_name else "-", address, phone, email, article_type, up_file.name, work_link]
                    st.session_state.sheet.append_row(new_row)

                    # บันทึกรายชื่อใหม่ถ้าอยู่ในโหมดเพิ่มใหม่
                    if st.session_state.get('add_mode_uni', False) and uni_name:
                        st.session_state.sheet_uni.append_row([uni_name, address, phone, email])
                    if st.session_state.get('add_mode_agency', False) and agency_name:
                        st.session_state.sheet_agency.append_row([agency_name, address, phone, email])

                    # ล้างค่าโหมดเพิ่มใหม่หลังส่งสำเร็จ
                    st.session_state.add_mode_uni = False
                    st.session_state.add_mode_agency = False
                    del st.session_state['list_uni'] # บังคับโหลดรายชื่อใหม่รอบหน้า
                    
                    show_message_modal("✅ บันทึกข้อมูลและอัปเดตรายชื่อเรียบร้อย")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")

# --- ส่วน Admin & จัดการรายชื่อ (คงเดิมทุกฟังก์ชัน) ---
elif page in ["หน้าสำหรับ Admin", "จัดการรายชื่อมหาวิทยาลัย", "จัดการรายชื่อหน่วยงาน"]:
    if not st.session_state.get('logged_in', False):
        st.markdown(f"### 🔐 กรุณาเข้าสู่ระบบเพื่อใช้งานเมนู '{page}'")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u_in == "bannawit.s" and p_in == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    else:
        col_title, col_logout = st.columns([8, 1.5])
        col_title.markdown(f"## 🖥️ {page}")
        if col_logout.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()

        if page == "หน้าสำหรับ Admin":
            try:
                raw_data = st.session_state.sheet.get_all_values()
                if len(raw_data) > 1:
                    df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                    st.dataframe(df, use_container_width=True)
                    st.divider()
                    col_name = "Filename" if "Filename" in df.columns else df.columns[11]
                    selected_file = st.selectbox("เลือกไฟล์เพื่อดาวน์โหลด:", options=df[col_name].dropna().unique().tolist(), index=None)
                    if selected_file:
                        f_path = os.path.join("uploaded_journals", str(selected_file))
                        if os.path.exists(f_path):
                            with open(f_path, "rb") as f:
                                st.download_button(label="💾 ดาวน์โหลดไฟล์", data=f, file_name=str(selected_file))
            except Exception as e: st.error(f"Error: {e}")
        else:
            target_sheet = st.session_state.sheet_uni if page == "จัดการรายชื่อมหาวิทยาลัย" else st.session_state.sheet_agency
            label = "มหาวิทยาลัย" if page == "จัดการรายชื่อมหาวิทยาลัย" else "หน่วยงาน"
            st.subheader(f"➕ เพิ่มข้อมูล{label}")
            with st.form(f"add_form_{page}", clear_on_submit=True):
                new_name = st.text_input(f"ชื่อ{label}:")
                new_addr = st.text_area("ที่อยู่:")
                new_contact = st.text_input("เบอร์โทร:")
                new_mail = st.text_input("E-mail:")
                if st.form_submit_button(f"🚀 บันทึกข้อมูล{label}"):
                    if new_name:
                        target_sheet.append_row([new_name, new_addr, new_contact, new_mail])
                        del st.session_state['list_uni'] # เคลียร์แคชเพื่อให้โหลดใหม่
                        show_message_modal("✅ เพิ่มข้อมูลเรียบร้อย")
            st.divider()
            data_list = target_sheet.get_all_values()
            if len(data_list) > 1: st.table(pd.DataFrame(data_list[1:], columns=data_list[0]))

st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
