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

# --- 2. ฟังก์ชัน Popup แจ้งเตือน (ปุ่มอยู่ตรงกลาง) ---
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
        
        # เชื่อมต่อหน้าชีทต่างๆ
        sheet = spreadsheet.worksheet("Data_2026")
        sheet_uni = spreadsheet.worksheet("University")
        sheet_agency = spreadsheet.worksheet("Agency")
        
        # ดึงข้อมูลสำหรับ Dropdown (ใช้คอลัมน์ A ข้ามหัวตาราง)
        list_uni = [item for item in sheet_uni.col_values(1)[1:] if item]
        list_agency = [item for item in sheet_agency.col_values(1)[1:] if item]
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
    st.markdown("### สำนักงานสหกิจศึกษา มหาวิทยาลัยเทคโนโลยีราชมงคลกรุงเทพ")
    
    with st.form("user_form", clear_on_submit=True):
        st.markdown("#### 📝 ฟอร์มส่งวารสาร")
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้า", ["นาย", "นางสาว", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์"])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")
        
        uni = st.selectbox("มหาวิทยาลัย / สถาบัน", options=["-- เลือกมหาวิทยาลัย --"] + list_uni)
        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")
        
        affiliation = st.selectbox("สังกัด / หน่วยงาน", options=["-- เลือกหน่วยงาน --"] + list_agency)
        address = st.text_input("ที่อยู่")
        
        col_t, col_e = st.columns(2)
        phone = col_t.text_input("เบอร์โทรศัพท์")
        email = col_e.text_input("E-mail")
        
        article_type = st.radio("**ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        up_file = st.file_uploader("แนบไฟล์บทความ (PDF/Word)", type=["pdf", "docx", "doc"])
        work_link = st.text_input("🔗 ลิงก์ผลงาน (ถ้ามี)", placeholder="https://example.com/your-work")
        
        if st.form_submit_button("ส่งข้อมูล", type="primary"):
            if not (up_file and f_name and phone and uni != "-- เลือกมหาวิทยาลัย --" and affiliation != "-- เลือกหน่วยงาน --"):
                st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")
            else:
                try:
                    folder_path = "uploaded_journals"
                    if not os.path.exists(folder_path): os.makedirs(folder_path)
                    file_path = os.path.join(folder_path, up_file.name)
                    with open(file_path, "wb") as f:
                        f.write(up_file.getbuffer())
                    
                    row_count = len(sheet.get_all_values())
                    new_row = [row_count, prefix, f_name, l_name, uni, faculty, major, affiliation, address, phone, email, article_type, up_file.name, work_link]
                    sheet.append_row(new_row)
                    show_message_modal("✅ บันทึกข้อมูลของท่านเรียบร้อย")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")

# --- 6. หน้าสำหรับ Admin & จัดการรายชื่อ (ต้อง Login) ---
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

        # --- Dashboard หลัก ---
        if page == "หน้าสำหรับ Admin":
            try:
                data = sheet.get_all_records()
                if data:
                    df = pd.DataFrame(data)
                    st.markdown("### 📊 ตารางข้อมูลวารสาร")
                    st.dataframe(df, use_container_width=True)
                    st.write("---")
                    st.markdown("### 📁 จัดการไฟล์และลิงก์")
                    if "Filename" in df.columns:
                        file_list = df["Filename"].dropna().unique().tolist()
                        selected_file = st.selectbox("เลือกรายการที่ต้องการตรวจสอบ:", options=file_list, index=None)
                        if selected_file:
                            row_info = df[df["Filename"] == selected_file].iloc[0]
                            c1, c2 = st.columns(2)
                            with c1:
                                f_path = os.path.join("uploaded_journals", str(selected_file))
                                if os.path.exists(f_path):
                                    with open(f_path, "rb") as f:
                                        st.download_button(label="💾 ดาวน์โหลดไฟล์บทความ", data=f, file_name=str(selected_file), use_container_width=True)
                            with c2:
                                # แสดงลิงก์ผลงาน
                                link_val = row_info.get("work_link", "")
                                if link_val and str(link_val).startswith("http"):
                                    st.link_button(f"🔗 เปิดลิงก์ผลงาน", str(link_val), use_container_width=True)
                                else:
                                    st.button("🚫 ไม่มีลิงก์แนบมา", disabled=True, use_container_width=True)
                else:
                    st.info("ℹ️ ยังไม่มีข้อมูลในระบบ")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")

        # --- ส่วนจัดการรายชื่อมหาวิทยาลัย/หน่วยงาน (พร้อมระบบ Clear ค่า) ---
        else:
            target_sheet = sheet_uni if page == "จัดการรายชื่อมหาวิทยาลัย" else sheet_agency
            label = "มหาวิทยาลัย" if page == "จัดการรายชื่อมหาวิทยาลัย" else "หน่วยงาน"
            
            # เตรียม Key สำหรับ Clear ค่า
            if f"name_{page}" not in st.session_state: st.session_state[f"name_{page}"] = ""
            if f"addr_{page}" not in st.session_state: st.session_state[f"addr_{page}"] = ""
            if f"cont_{page}" not in st.session_state: st.session_state[f"cont_{page}"] = ""
            if f"mail_{page}" not in st.session_state: st.session_state[f"mail_{page}"] = ""

            st.subheader(f"➕ เพิ่มข้อมูล{label}")
            with st.container(border=True):
                # ใช้ key ผูกกับ widget เพื่อให้สั่งล้างค่าได้
                new_name = st.text_input(f"ชื่อ{label}:", key=f"input_name_{page}")
                new_addr = st.text_area("ที่อยู่:", key=f"input_addr_{page}")
                new_contact = st.text_input("ข้อมูลติดต่อ (เบอร์โทร):", key=f"input_cont_{page}")
                new_mail = st.text_input("E-mail:", key=f"input_mail_{page}")
                
                if st.button(f"🚀 บันทึกข้อมูล{label}", type="primary"):
                    if new_name:
                        try:
                            # บันทึกลง GSheet (4 คอลัมน์)
                            target_sheet.append_row([new_name, new_addr, new_contact, new_mail])
                            
                            # เคลียร์ค่าใน Widget ผ่าน Session State
                            st.session_state[f"input_name_{page}"] = ""
                            st.session_state[f"input_addr_{page}"] = ""
                            st.session_state[f"input_cont_{page}"] = ""
                            st.session_state[f"input_mail_{page}"] = ""
                            
                            show_message_modal("✅ เพิ่มข้อมูลเรียบร้อย")
                        except Exception as e:
                            st.error(f"ผิดพลาด: {e}")
                    else:
                        st.warning(f"⚠️ กรุณากรอกชื่อ{label}")
            
            st.write("---")
            st.write(f"📂 รายชื่อและรายละเอียด{label}ปัจจุบัน:")
            try:
                data_list = target_sheet.get_all_records()
                if data_list:
                    st.table(pd.DataFrame(data_list))
                else:
                    st.info("ยังไม่มีข้อมูล")
            except:
                st.info("ยังไม่มีข้อมูลรายชื่อ")

# --- 7. Footer ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
