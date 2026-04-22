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
    .helper-box {
        background-color: #f8f9fa; padding: 15px; border-radius: 10px;
        border: 1px dashed #ccc; text-align: center; margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. ระบบ Navigation ด้วย Callback (แก้ไขเพื่อให้ปุ่มลิงก์ทำงาน) ---
if 'page_nav' not in st.session_state:
    st.session_state.page_nav = "หน้าสำหรับ User"

def move_to(page_name):
    st.session_state.page_nav = page_name

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
        
        list_uni = sorted([item for item in sheet_uni.col_values(1)[1:] if item])
        list_agency = sorted([item for item in sheet_agency.col_values(1)[1:] if item])
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")

# --- 4. ฟังก์ชัน Popup แจ้งเตือน ---
@st.dialog("🔔 การแจ้งเตือนจากระบบ")
def show_message_modal(text):
    st.write(f"<div style='text-align: center; font-size: 1.2rem;'>{text}</div>", unsafe_allow_html=True)
    if st.button("ปิดหน้าต่าง", use_container_width=True):
        st.rerun()

# --- 5. Sidebar ---
with st.sidebar:
    st.markdown("## 🏠 HOME")
    menu_options = ["หน้าสำหรับ User", "หน้าสำหรับ Admin", "จัดการรายชื่อมหาวิทยาลัย", "จัดการรายชื่อหน่วยงาน"]
    
    # อ้างอิง index จาก session_state เพื่อให้ Selectbox เปลี่ยนตามปุ่มที่กด
    current_idx = menu_options.index(st.session_state.page_nav)
    page_select = st.selectbox("เลือกเมนูการใช้งาน:", menu_options, index=current_idx, key="sidebar_selection")
    
    # ถ้าผู้ใช้คลิกเลือกจาก Sidebar โดยตรง
    if page_select != st.session_state.page_nav:
        st.session_state.page_nav = page_select
        st.rerun()

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://rmutk.ac.th", use_container_width=True)
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/", use_container_width=True)
    st.link_button("📘 วารสารสหกิจก้าวหน้า (JCEP)", "https://jcep.rmutk.ac.th/", use_container_width=True)

# --- 6. หน้าสำหรับ User ---
if st.session_state.page_nav == "หน้าสำหรับ User":
    st.markdown("# 📘 ระบบส่งวารสารสหกิจศึกษาก้าวหน้า")
    st.markdown("#### 📝 ฟอร์มส่งวารสาร")
    
    with st.container(border=True):
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้าชื่อ", ["นาย", "นางสาว", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์"])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")
        
        uni = st.selectbox("มหาวิทยาลัย / สถาบัน", options=list_uni, index=None, placeholder="เลือกมหาวิทยาลัย...")
        
        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")
        
        affiliation = st.selectbox("สังกัด / หน่วยงาน", options=list_agency, index=None, placeholder="เลือกหน่วยงาน...")
        address = st.text_input("ที่อยู่")
        
        col_t, col_e = st.columns(2)
        phone = col_t.text_input("เบอร์โทรศัพท์")
        email = col_e.text_input("E-mail")
        
        article_type_option = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        other_type = ""
        if article_type_option == "อื่นๆ":
            other_type = st.text_input("โปรดระบุประเภทบทความอื่นๆ:", placeholder="ระบุประเภทบทความที่นี่...")
        
        final_article_type = other_type if article_type_option == "อื่นๆ" else article_type_option
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx", "doc"])
        work_link = st.text_input("🔗 ลิงก์ผลงาน (ถ้ามี)")
        
        if st.button("✅ ส่งข้อมูลวารสาร", type="primary", use_container_width=True):
            if not (up_file and f_name and phone and final_article_type):
                st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")
            else:
                try:
                    if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                    with open(os.path.join("uploaded_journals", up_file.name), "wb") as f: f.write(up_file.getbuffer())
                    all_rows = sheet.get_all_values()
                    new_row = [len(all_rows), prefix, f_name, l_name, uni, faculty, major, affiliation, address, phone, email, final_article_type, up_file.name]
                    sheet.append_row(new_row)
                    show_message_modal("✅ บันทึกข้อมูลของท่านเรียบร้อย")
                except Exception as e: st.error(f"เกิดข้อผิดพลาด: {e}")

        # --- ส่วนที่เน้นแก้ไข: ปุ่มลิงก์ที่ทำงานทันที ---
        st.markdown("""
            <div class="helper-box">
                💡 <b>หากไม่พบรายชื่อมหาวิทยาลัยหรือหน่วยงานของท่าน</b><br>
                กรุณากดปุ่มด้านล่างเพื่อไปหน้าเพิ่มข้อมูล
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        c1.button("🏫 ไปหน้า: เพิ่มรายชื่อมหาวิทยาลัย", use_container_width=True, type="secondary", on_click=move_to, args=("จัดการรายชื่อมหาวิทยาลัย",))
        c2.button("🏢 ไปหน้า: เพิ่มรายชื่อหน่วยงาน", use_container_width=True, type="secondary", on_click=move_to, args=("จัดการรายชื่อหน่วยงาน",))

# --- 7. หน้าจัดการรายชื่อ ---
elif st.session_state.page_nav in ["จัดการรายชื่อมหาวิทยาลัย", "จัดการรายชื่อหน่วยงาน"]:
    target_sheet = sheet_uni if st.session_state.page_nav == "จัดการรายชื่อมหาวิทยาลัย" else sheet_agency
    current_list = list_uni if st.session_state.page_nav == "จัดการรายชื่อมหาวิทยาลัย" else list_agency
    label = "มหาวิทยาลัย" if st.session_state.page_nav == "จัดการรายชื่อมหาวิทยาลัย" else "หน่วยงาน"
    
    st.markdown(f"## ⚙️ {st.session_state.page_nav}")
    st.button("⬅️ กลับหน้าส่งฟอร์มวารสาร", on_click=move_to, args=("หน้าสำหรับ User",))

    with st.form("add_form", clear_on_submit=True):
        st.subheader(f"➕ เพิ่มข้อมูล{label}")
        new_name = st.text_input(f"ชื่อ{label}:").strip()
        new_addr = st.text_area("ที่อยู่:")
        new_contact = st.text_input("เบอร์โทรศัพท์:")
        new_mail = st.text_input("E-mail:")
        
        if st.form_submit_button(f"🚀 บันทึกข้อมูล{label}", type="primary"):
            if new_name:
                if new_name.lower() in [n.lower() for n in current_list]:
                    st.error(f"❌ มีชื่อ '{new_name}' ในระบบแล้ว")
                else:
                    target_sheet.append_row([new_name, new_addr, new_contact, new_mail])
                    show_message_modal(f"✅ เพิ่มข้อมูล{label}เรียบร้อย")
            else: st.warning(f"⚠️ กรุณาระบุชื่อ{label}")
    
    st.divider()
    try:
        data = target_sheet.get_all_values()
        if len(data) > 1: st.table(pd.DataFrame(data[1:], columns=data[0]))
    except: pass

# --- 8. หน้าสำหรับ Admin ---
elif st.session_state.page_nav == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        st.markdown("### 🔐 เข้าสู่ระบบสำหรับ Admin")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u == "bannawit.s" and p == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("❌ ข้อมูลไม่ถูกต้อง")
    else:
        if st.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()
        raw = sheet.get_all_values()
        if len(raw) > 1:
            df = pd.DataFrame(raw[1:], columns=raw[0])
            st.dataframe(df, use_container_width=True)
            
            file_list = df[df.columns[-1]].dropna().unique().tolist()
            sel_file = st.selectbox("ดาวน์โหลดไฟล์:", options=file_list, index=None)
            if sel_file:
                path = os.path.join("uploaded_journals", str(sel_file))
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        st.download_button(f"💾 ดาวน์โหลด: {sel_file}", f, file_name=str(sel_file))

st.markdown('<div class="footer">Create by OCE - RMUTK</div>', unsafe_allow_html=True)
