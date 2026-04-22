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
    .add-btn { margin-top: 28px; }
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
    
    # ใช้ Container หุ้มเพื่อให้ดูเหมือนฟอร์มเดียวกัน
    with st.container(border=True):
        st.markdown("#### 📝 ฟอร์มส่งวารสาร")
        
        # ส่วนชื่อ-นามสกุล
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้า", ["นาย", "นางสาว", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์"])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")
        
        # --- มหาวิทยาลัย (ปุ่มบวก) ---
        col_u1, col_u2 = st.columns([8, 1])
        with col_u1:
            uni_select = st.selectbox("มหาวิทยาลัย / สถาบัน", options=list_uni, index=None, placeholder="พิมพ์ค้นหาชื่อมหาวิทยาลัย...")
        with col_u2:
            # ใช้ปุ่มกดเพื่อสลับโหมด (Toggle)
            add_new_uni = st.button("➕", key="btn_uni", help="เพิ่มมหาวิทยาลัยใหม่")
            if add_new_uni:
                st.session_state.mode_uni = not st.session_state.get('mode_uni', False)
        
        # ช่องกรอกชื่อใหม่จะเด้งขึ้นมาถ้ากดปุ่มบวก
        uni_final = uni_select
        if st.session_state.get('mode_uni', False):
            uni_final = st.text_input("✨ ระบุชื่อมหาวิทยาลัยใหม่:", placeholder="กรอกชื่อมหาวิทยาลัยที่ไม่มีในรายการ...")
            st.info("💡 คุณกำลังเพิ่มมหาวิทยาลัยใหม่เข้าสู่ระบบ")

        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")

        # --- หน่วยงาน (ปุ่มบวก) ---
        col_a1, col_a2 = st.columns([8, 1])
        with col_a1:
            agency_select = st.selectbox("สังกัด / หน่วยงาน", options=list_agency, index=None, placeholder="พิมพ์ค้นหาชื่อหน่วยงาน...")
        with col_a2:
            add_new_agency = st.button("➕", key="btn_agency", help="เพิ่มหน่วยงานใหม่")
            if add_new_agency:
                st.session_state.mode_agency = not st.session_state.get('mode_agency', False)

        agency_final = agency_select
        if st.session_state.get('mode_agency', False):
            agency_final = st.text_input("✨ ระบุชื่อหน่วยงานใหม่:", placeholder="กรอกชื่อหน่วยงานที่ไม่มีในรายการ...")
            st.info("💡 คุณกำลังเพิ่มหน่วยงานใหม่เข้าสู่ระบบ")

        # --- ระบบ Auto-fill ---
        d_addr, d_phone, d_mail = "", "", ""
        # ดึงข้อมูลถ้าเลือกจากที่มีอยู่ และไม่ได้อยู่ในโหมดเพิ่มใหม่
        if uni_select and not st.session_state.get('mode_uni', False):
            m = next((i for i in all_uni_data if i['มหาวิทยาลัย'] == uni_select), None)
            if m: d_addr, d_phone, d_mail = m.get('ที่อยู่',''), m.get('ข้อมูลติดต่อ',''), m.get('E-mail','')
        elif agency_select and not st.session_state.get('mode_agency', False):
            m = next((i for i in all_agency_data if i['หน่วยงาน'] == agency_select), None)
            if m: d_addr, d_phone, d_mail = m.get('ที่อยู่',''), m.get('ข้อมูลติดต่อ',''), m.get('E-mail','')

        address = st.text_input("ที่อยู่", value=d_addr)
        col_t, col_e = st.columns(2)
        phone = col_t.text_input("เบอร์โทรศัพท์", value=d_phone)
        email = col_e.text_input("E-mail", value=d_mail)
        
        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx", "doc"])
        work_link = st.text_input("🔗 ลิงก์ผลงาน (ถ้ามี)", placeholder="https://example.com/your-work")
        
        # ปุ่มส่งข้อมูล (อยู่นอก st.form เพื่อให้การกดปุ่มบวกทำงานได้ทันที)
        if st.button("ส่งข้อมูลวารสาร", type="primary", use_container_width=True):
            if not (up_file and f_name and phone and uni_final and agency_final):
                st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน (ตรวจสอบชื่อมหาวิทยาลัยและหน่วยงาน)")
            else:
                try:
                    # บันทึกไฟล์
                    f_name_save = up_file.name
                    folder = "uploaded_journals"
                    if not os.path.exists(folder): os.makedirs(folder)
                    with open(os.path.join(folder, f_name_save), "wb") as f: f.write(up_file.getbuffer())
                    
                    # บันทึกลง Sheet หลัก
                    new_row = [prefix, f_name, l_name, uni_final, faculty, major, agency_final, address, phone, email, article_type, f_name_save, work_link]
                    sheet.append_row(new_row)

                    # บันทึกลงฐานรายชื่อ (ถ้าเป็นของใหม่)
                    if st.session_state.get('mode_uni', False):
                        sheet_uni.append_row([uni_final, address, phone, email])
                    if st.session_state.get('mode_agency', False):
                        sheet_agency.append_row([agency_final, address, phone, email])

                    # ล้างสถานะปุ่มบวก
                    st.session_state.mode_uni = False
                    st.session_state.mode_agency = False
                    
                    show_message_modal("✅ ส่งข้อมูลและอัปเดตฐานข้อมูลรายชื่อเรียบร้อยแล้ว")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")

# --- หน้า Admin (ฟังก์ชันเดิมครบถ้วน) ---
elif page in ["หน้าสำหรับ Admin", "จัดการรายชื่อมหาวิทยาลัย", "จัดการรายชื่อหน่วยงาน"]:
    if not st.session_state.get('logged_in', False):
        st.markdown("### 🔐 กรุณาเข้าสู่ระบบ")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In"):
            if u_in == "bannawit.s" and p_in == "adminjcep":
                st.session_state.logged_in = True
                show_message_modal("🔓 เข้าสู่ระบบสำเร็จ")
            else: st.error("❌ รหัสผ่านไม่ถูกต้อง")
    else:
        col_t, col_l = st.columns([8, 1.5])
        col_t.markdown(f"## 🖥️ {page}")
        if col_l.button("🚪 ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            show_message_modal("ออกจากระบบเรียบร้อย")
        
        if page == "หน้าสำหรับ Admin":
            raw = sheet.get_all_values()
            if len(raw) > 1:
                df = pd.DataFrame(raw[1:], columns=raw[0])
                st.dataframe(df, use_container_width=True)
                # ระบบจัดการไฟล์เดิม...
                col_n = "Filename" if "Filename" in df.columns else df.columns[11]
                sel = st.selectbox("เลือกไฟล์:", options=df[col_n].unique(), index=None)
                if sel:
                    row = df[df[col_n] == sel].iloc[0]
                    path = os.path.join("uploaded_journals", str(sel))
                    if os.path.exists(path):
                        with open(path, "rb") as f: st.download_button("💾 โหลดไฟล์", f, file_name=str(sel))
                    if str(row.iloc[-1]).startswith("http"): st.link_button("🔗 ลิงก์", str(row.iloc[-1]))
        else:
            t_sheet = sheet_uni if page == "จัดการรายชื่อมหาวิทยาลัย" else sheet_agency
            with st.form(f"admin_add_{page}", clear_on_submit=True):
                n = st.text_input("ชื่อ:")
                a = st.text_area("ที่อยู่:")
                c = st.text_input("ติดต่อ:")
                e = st.text_input("อีเมล:")
                if st.form_submit_button("🚀 บันทึก"):
                    if n:
                        t_sheet.append_row([n, a, c, e])
                        show_message_modal("เพิ่มข้อมูลสำเร็จ")
            data = t_sheet.get_all_values()
            if len(data) > 1: st.table(pd.DataFrame(data[1:], columns=data[0]))

st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
