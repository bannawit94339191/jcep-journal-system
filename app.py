import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import io
import os

# --- 1. ตั้งค่าพื้นฐานและการตกแต่ง CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    .stButton>button[kind="primary"] { background-color: #28a745; color: white; border: none; }
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border: none; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; padding: 10px; background: white; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Google Services (Sheets และ Drive) ---
if "google_auth" in st.secrets:
    info = st.secrets["google_auth"]
    creds = service_account.Credentials.from_service_account_info(info)
    # ใส่ Scope ทั้ง Sheets และ Drive เพื่อให้ gspread ค้นหาชื่อไฟล์เจอ
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_with_scope = creds.with_scopes(scope)
    client = gspread.authorize(creds_with_scope)
    sheet = client.open("JCEP_Data").sheet1

# --- 3. ระบบจัดการ Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def logout():
    st.session_state.logged_in = False
    st.rerun()

# --- 4. แถบเมนูด้านข้าง ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=200)
    st.title("เมนูหลัก")
    page = st.radio("ไปที่หน้า:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin"])

# --- 5. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    st.header("ระบบจัดเก็บข้อมูลวารสารสหกิจศึกษาก้าวหน้า")
    st.subheader("Journal of Cooperative Education Progress")

    # ดึงลำดับล่าสุด
    try:
        existing_data = sheet.get_all_values()
        next_id = len(existing_data)
    except:
        next_id = 1

    with st.form("user_form"):
        st.text_input("1. ลำดับที่", value=str(next_id), disabled=True)
        name = st.text_input("2. ชื่อ - นามสกุล")
        uni = st.text_input("3. มหาวิทยาลัย / สถาบัน")
        faculty = st.text_input("4. คณะ")
        major = st.text_input("5. สาขาวิชา")
        org = st.text_input("6. สังกัด / หน่วยงาน")
        addr = st.text_area("7. ที่อยู่")
        phone = st.text_input("8. ช่องทางการติดต่อกลับ (เบอร์โทร)")
        email = st.text_input("9. ช่องทางการติดต่อกลับ (E-mail)")
        article_type = st.radio("10. ประเภทบทความ", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"])
        up_file = st.file_uploader("11. แนบไฟล์วารสาร")

        submit = st.form_submit_button("Send", type="primary")

        if submit:
            file_link = "ไม่มีไฟล์แนบ"
            if up_file:
                # สร้างโฟลเดอร์เก็บไฟล์ในเครื่องเซิร์ฟเวอร์
                save_dir = "uploaded_journals"
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                
                file_path = os.path.join(save_dir, up_file.name)
                with open(file_path, "wb") as f:
                    f.write(up_file.getvalue())
                file_link = f"Local: {up_file.name}"

            # บันทึกลง Google Sheet
            sheet.append_row([next_id, name, uni, faculty, major, org, addr, phone, email, article_type, file_link])
            st.success("ส่งข้อมูลสำเร็จ! ระบบได้บันทึกไฟล์ไว้เรียบร้อยแล้ว 🎉")

# --- 6. หน้าสำหรับ Admin ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.logged_in:
        st.subheader("Login สำหรับผู้ดูแลระบบ")
        user_input = st.text_input("Username")
        pass_input = st.text_input("Password", type="password")
        if st.button("เข้าสู่ระบบ"):
            if user_input == "bannawit.s" and pass_input == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("ข้อมูลไม่ถูกต้อง")
    else:
        col_title, col_logout = st.columns([5, 1])
        with col_logout:
            if st.button("Logout"):
                logout()

        st.header("Admin Dashboard")
        
        # ส่วนที่ 1: ตารางข้อมูลจาก Google Sheet
        st.subheader("📊 ข้อมูลการสมัครทั้งหมด")
        data = pd.DataFrame(sheet.get_all_records())
        st.dataframe(data)

        # ส่วนที่ 2: ปุ่มดาวน์โหลดไฟล์ (📁 ไฟล์ที่ถูกเก็บไว้ในเครื่อง)
        st.divider()
        st.subheader("📁 จัดการไฟล์ที่อัปโหลดเข้าเครื่อง")
        
        save_dir = "uploaded_journals"
        if os.path.exists(save_dir):
            files = os.listdir(save_dir)
            if files:
                selected_file = st.selectbox("เลือกไฟล์ที่ต้องการดาวน์โหลดลงเครื่องคุณ:", files)
                file_path = os.path.join(save_dir, selected_file)
                
                with open(file_path, "rb") as f:
                    st.download_button(
                        label=f"💾 ดาวน์โหลดไฟล์ {selected_file}",
                        data=f,
                        file_name=selected_file,
                        mime="application/octet-stream",
                        type="primary"
                    )
            else:
                st.info("ยังไม่มีไฟล์ที่ถูกอัปโหลดเข้ามาในโฟลเดอร์")
        else:
            st.info("ระบบยังไม่ได้สร้างโฟลเดอร์สำหรับเก็บไฟล์ (จะสร้างเมื่อมีการส่งไฟล์ครั้งแรก)")

# --- Footer ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
