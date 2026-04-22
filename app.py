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
    st.write(f"<div style='text-align: center; font-size: 1.2rem;'>{text}</div>", unsafe_allow_html=True)
    st.write("") 
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
        sheet_uni = spreadsheet.worksheet("University")
        sheet_agency = spreadsheet.worksheet("Agency")
        
        # ดึงข้อมูลทั้งหมดมาทำระบบ Auto-fill
        all_uni_data = sheet_uni.get_all_records()
        all_agency_data = sheet_agency.get_all_records()
        
        list_uni = sorted([str(d['มหาวิทยาลัย']) for d in all_uni_data if d.get('มหาวิทยาลัย')])
        list_agency = sorted([str(d['หน่วยงาน']) for d in all_agency_data if d.get('หน่วยงาน')])
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
    
    with st.form("user_form", clear_on_submit=True):
        st.markdown("#### 📝 ฟอร์มส่งวารสาร")
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้า", ["นาย", "นางสาว", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์"])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")
        
        # --- ส่วนที่ 1: มหาวิทยาลัย ---
        col_u1, col_u2 = st.columns([3, 1])
        with col_u1:
            uni_select = st.selectbox("มหาวิทยาลัย / สถาบัน", options=list_uni, index=None, placeholder="พิมพ์ค้นหาชื่อมหาวิทยาลัย...")
        with col_u2:
            st.write("") # จัดระยะ
            new_uni_check = st.checkbox("ไม่มีในรายการ? (เพิ่มใหม่)", key="new_uni")

        # ถ้าเลือกเพิ่มใหม่ ให้โชว์ช่องกรอกชื่อ
        if new_uni_check:
            uni_name = st.text_input("ระบุชื่อมหาวิทยาลัยใหม่:")
        else:
            uni_name = uni_select

        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")
        
        # --- ส่วนที่ 2: หน่วยงาน ---
        col_a1, col_a2 = st.columns([3, 1])
        with col_a1:
            agency_select = st.selectbox("สังกัด / หน่วยงาน", options=list_agency, index=None, placeholder="พิมพ์ค้นหาชื่อหน่วยงาน...")
        with col_a2:
            st.write("") # จัดระยะ
            new_agency_check = st.checkbox("ไม่มีในรายการ? (เพิ่มใหม่)", key="new_agency")

        if new_agency_check:
            agency_name = st.text_input("ระบุชื่อหน่วยงานใหม่:")
        else:
            agency_name = agency_select

        # --- ส่วนที่ 3: ดึงข้อมูลอัตโนมัติ (Auto-fill) ---
        default_addr, default_phone, default_email = "", "", ""
        
        # ถ้าเลือกจากลิสต์ (และไม่ใช่การเพิ่มใหม่) ให้ดึงข้อมูลมาใส่
        if uni_select and not new_uni_check:
            match = next((item for item in all_uni_data if item['มหาวิทยาลัย'] == uni_select), None)
            if match:
                default_addr = match.get('ที่อยู่', '')
                default_phone = match.get('ข้อมูลติดต่อ', '')
                default_email = match.get('E-mail', '')
        elif agency_select and not new_agency_check:
            match = next((item for item in all_agency_data if item['หน่วยงาน'] == agency_select), None)
            if match:
                default_addr = match.get('ที่อยู่', '')
                default_phone = match.get('ข้อมูลติดต่อ', '')
                default_email = match.get('E-mail', '')

        address = st.text_input("ที่อยู่", value=default_addr)
        col_t, col_e = st.columns(2)
        phone = col_t.text_input("เบอร์โทรศัพท์", value=default_phone)
        email = col_e.text_input("E-mail", value=default_email)
        
        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx", "doc"])
        work_link = st.text_input("🔗 ลิงก์ผลงาน (ถ้ามี)", placeholder="https://example.com/your-work")
        
        if st.form_submit_button("ส่งข้อมูล", type="primary"):
            if not (up_file and f_name and phone and uni_name and agency_name):
                st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")
            else:
                try:
                    # 1. บันทึกข้อมูลเข้า Sheet หลัก
                    folder_path = "uploaded_journals"
                    if not os.path.exists(folder_path): os.makedirs(folder_path)
                    file_path = os.path.join(folder_path, up_file.name)
                    with open(file_path, "wb") as f: f.write(up_file.getbuffer())
                    
                    new_row = [prefix, f_name, l_name, uni_name, faculty, major, agency_name, address, phone, email, article_type, up_file.name, work_link]
                    sheet.append_row(new_row)

                    # 2. กรณีเป็นรายชื่อใหม่ ให้บันทึกลง Sheet University/Agency ด้วย
                    if new_uni_check and uni_name:
                        sheet_uni.append_row([uni_name, address, phone, email])
                    if new_agency_check and agency_name:
                        sheet_agency.append_row([agency_name, address, phone, email])

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
                show_message_modal("🔓 เข้าสู่ระบบสำเร็จ")
            else:
                st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    else:
        col_title, col_logout = st.columns([8, 1.5])
        col_title.markdown(f"## 🖥️ {page}")
        if col_logout.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            show_message_modal("🚪 ออกจากระบบเรียบร้อย")
        st.divider()

        if page == "หน้าสำหรับ Admin":
            try:
                raw_data = sheet.get_all_values()
                if len(raw_data) > 1:
                    df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                    st.markdown("### 📊 ตารางข้อมูลวารสาร")
                    st.dataframe(df, use_container_width=True)
                    st.write("---")
                    col_name = "Filename" if "Filename" in df.columns else df.columns[11]
                    file_list = df[col_name].dropna().unique().tolist()
                    selected_file = st.selectbox("เลือกรายการ:", options=file_list, index=None)
                    if selected_file:
                        row_info = df[df[col_name] == selected_file].iloc[0]
                        c1, c2 = st.columns(2)
                        with c1:
                            f_path = os.path.join("uploaded_journals", str(selected_file))
                            if os.path.exists(f_path):
                                with open(f_path, "rb") as f:
                                    st.download_button(label="💾 ดาวน์โหลดไฟล์", data=f, file_name=str(selected_file), use_container_width=True)
                        with c2:
                            link_val = row_info.iloc[-1]
                            if str(link_val).startswith("http"):
                                st.link_button(f"🔗 เปิดลิงก์ผลงาน", str(link_val), use_container_width=True)
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
        else:
            target_sheet = sheet_uni if page == "จัดการรายชื่อมหาวิทยาลัย" else sheet_agency
            label = "มหาวิทยาลัย" if page == "จัดการรายชื่อมหาวิทยาลัย" else "หน่วยงาน"
            st.subheader(f"➕ เพิ่มข้อมูล{label}")
            with st.form(f"add_form_{page}", clear_on_submit=True):
                new_name = st.text_input(f"ชื่อ{label}:")
                new_addr = st.text_area("ที่อยู่:")
                new_contact = st.text_input("ข้อมูลติดต่อ (เบอร์โทร):")
                new_mail = st.text_input("E-mail:")
                if st.form_submit_button(f"🚀 บันทึกข้อมูล{label}", type="primary"):
                    if new_name:
                        target_sheet.append_row([new_name, new_addr, new_contact, new_mail])
                        show_message_modal("✅ เพิ่มข้อมูลเรียบร้อย")
                    else:
                        st.warning(f"⚠️ กรุณากรอกชื่อ{label}")
            st.write("---")
            st.write(f"📂 รายชื่อปัจจุบัน:")
            data_list = target_sheet.get_all_values()
            if len(data_list) > 1:
                st.table(pd.DataFrame(data_list[1:], columns=data_list[0]))

st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
