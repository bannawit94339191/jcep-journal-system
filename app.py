import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

# --- 1. ตั้งค่าพื้นฐานและการตกแต่ง CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    .stButton>button[kind="primary"] { background-color: #28a745; color: white; border: none; }
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border: none; }
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        background-color: #28a745; color: white; text-align: center; 
        padding: 10px; font-weight: bold; z-index: 100;
    }
    .main { padding-bottom: 70px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Google Services ---
if "google_auth" in st.secrets:
    try:
        info = st.secrets["google_auth"]
        creds = service_account.Credentials.from_service_account_info(info)
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_with_scope = creds.with_scopes(scope)
        client = gspread.authorize(creds_with_scope)
        spreadsheet = client.open("JCEP_Data")
        
        # เชื่อมต่อแผ่นงานตามชื่อ (ย้ายตำแหน่งได้ ข้อมูลไม่สลับ)
        try:
            sheet = spreadsheet.worksheet("Data_2026")
        except:
            sheet = spreadsheet.sheet1
            
        try:
            admin_sheet = spreadsheet.worksheet("Admin_Users")
        except:
            admin_sheet = None
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")

# --- 3. ระบบจัดการ Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- 4. แถบเมนู ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", width=200)
    st.title("เมนูหลัก")
    page = st.radio("ไปที่หน้า:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin"])

# --- 5. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    st.header("ระบบจัดเก็บข้อมูลวารสารสหกิจศึกษาก้าวหน้า")
    try:
        next_id = len(sheet.get_all_values())
    except: next_id = 1

    with st.form("user_form"):
        st.info(f"1. ลำดับที่: {next_id}")
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("2. คำนำหน้า", ["นาย", "นางสาว", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์"])
        f_name = col_f.text_input("3. ชื่อ")
        l_name = col_l.text_input("4. นามสกุล")
        uni = st.text_input("5. มหาวิทยาลัย / สถาบัน")
        faculty = st.text_input("6. คณะ")
        major = st.text_input("7. สาขาวิชา")
        org = st.text_input("8. สังกัด / หน่วยงาน")
        addr = st.text_area("9. ที่อยู่")
        phone = st.text_input("10. เบอร์โทรศัพท์")
        email_u = st.text_input("11. E-mail")

        # แก้ไข: ประเภทบทความ (ใช้ Radio ให้เลือกได้อันเดียว)
        st.write("12. ประเภทบทความ")
        article_type = st.radio(
            "โปรดเลือกประเภทบทความ", 
            ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"],
            horizontal=True,
            key="type_radio"
        )
        
        # แก้ไข: ช่องกรอก "อื่นๆ" จะปรากฏเมื่อเลือก radio "อื่นๆ"
        # หมายเหตุ: ใน st.form ช่องนี้จะโผล่ตลอดแต่เราจะเช็คค่าตอนส่ง
        other_detail = st.text_input("ระบุประเภทบทความอื่นๆ (หากเลือกข้อ อื่นๆ)")

        up_file = st.file_uploader("13. แนบไฟล์ (PDF/Word)", type=["pdf", "docx", "doc"])

        st.markdown("<br>", unsafe_allow_html=True)
        btn1, btn2, _ = st.columns([1, 1, 4])
        
        if btn1.form_submit_button("Send", type="primary"):
            if up_file:
                # จัดการประเภทบทความ
                final_type = article_type
                if article_type == "อื่นๆ":
                    if other_detail.strip() != "":
                        final_type = f"อื่นๆ: {other_detail}"
                    else:
                        st.error("กรุณาระบุรายละเอียดในช่อง อื่นๆ")
                        st.stop()

                if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                with open(os.path.join("uploaded_journals", up_file.name), "wb") as f: f.write(up_file.getvalue())
                
                sheet.append_row([next_
