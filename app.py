import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

# --- 1. ตั้งค่าพื้นฐานและการตกแต่ง CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    /* ปุ่ม Send สีเขียว */
    .stButton>button[kind="primary"] { background-color: #28a745; color: white; border: none; }
    /* ปุ่ม Cancel สีแดง */
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border: none; }
    
    /* ปรับแต่ง Footer สีเขียว ตัวหนังสือขาว */
    .footer { 
        position: fixed; 
        left: 0; 
        bottom: 0; 
        width: 100%; 
        background-color: #28a745; 
        color: white; 
        text-align: center; 
        padding: 10px; 
        font-weight: bold;
        z-index: 100;
    }
    .main { padding-bottom: 70px; } /* เว้นที่ว่างด้านล่างไม่ให้ Footer ทับเนื้อหา */
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Google Services (Sheets & Drive) ---
if "google_auth" in st.secrets:
    try:
        info = st.secrets["google_auth"]
        creds = service_account.Credentials.from_service_account_info(info)
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_with_scope = creds.with_scopes(scope)
        client = gspread.authorize(creds_with_scope)
        sheet = client.open("JCEP_Data").sheet1
    except Exception as e:
        st.error(f"การเชื่อมต่อ Google Sheets ผิดพลาด: {e}")

# --- 3. ระบบจัดการ Session State สำหรับ Admin ---
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

# --- 5. หน้าสำหรับ User (ฟอร์มกรอกข้อมูล 13 ข้อ) ---
if page == "หน้าสำหรับ User":
    st.header("ระบบจัดเก็บข้อมูลวารสารสหกิจศึกษาก้าวหน้า")
    st.subheader("Journal of Cooperative Education Progress")

    # 1. ลำดับที่ (รันอัตโนมัติ)
    try:
        existing_data = sheet.get_all_values()
        next_id = len(existing_data)
    except:
        next_id = 1

    with st.form("user_form"):
        st.info(f"1. ลำดับที่: {next_id} (ระบบบันทึกให้อัตโนมัติ)")
        
        # 2-4. ชื่อ-นามสกุล
        col_prefix, col_fname, col_lname = st.columns([1, 2, 2])
        with col_prefix:
            prefix = st.selectbox("2. คำนำหน้า", ["นาย", "นางสาว", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์"])
        with col_fname:
            first_name = st.text_input("3. ชื่อ")
        with col_lname:
            last_name = st.text_input("4. นามสกุล")
            
        # 5-8. ข้อมูลหน่วยงาน
        uni = st.text_input("5. มหาวิทยาลัย / สถาบัน")
        faculty = st.text_input("6. คณะ")
        major = st.text_input("7. สาขาวิชา")
        org = st.text_input("8. สังกัด / หน่วยงาน")
        
        # 9. ที่อยู่
        addr = st.text_area("9. ที่อยู่")
        
        # 10-11. การติดต่อ
        col_tel, col_email = st.columns(2)
        with col_tel:
            phone = st.text_input("10. ช่องทางการติดต่อกลับ (เบอร์โทร)")
        with col_email:
            email_user = st.text_input("11. ช่องทางการติดต่อกลับ (E-mail)")

        # 12. ประเภทบทความ (Checkbox)
        st.write("12. ประเภทบทความ")
        c1, c2, c3 = st.columns(3)
        type_res = c1.checkbox("บทความวิจัย")
        type_acad = c2.checkbox("บทความวิชาการ")
        type_other = c3.checkbox("อื่นๆ")
        
        other_detail = ""
        if type_other:
            other_detail = st.text_input("โปรดระบุประเภทบทความอื่นๆ (ถ้ามี)")

        # 13. แนบไฟล์
        up_file = st.file_uploader("13. แนบไฟล์วารสาร (PDF หรือ Word)", type=["pdf", "docx", "doc"])

        st.markdown("<br>", unsafe_allow_html=True)
        # ปุ่ม Send และ Cancel
        btn_col1, btn_col2, _ = st.columns([1, 1, 4])
        with btn_col1:
            submit = st.form_submit_button("Send", type="primary")
        with btn_col2:
            cancel = st.form_submit_button("Cancel", type="secondary")

        if submit:
            # รวมประเภทบทความ
            selected_types = []
            if type_res: selected_types.append("บทความวิจัย")
            if type_acad: selected_types.append("บทความวิชาการ")
            if type_other: selected_types.append(f"อื่นๆ ({other_detail})")
            final_type = ", ".join(selected_types)

            if up_file:
                # บันทึกไฟล์ลงเครื่อง (Server)
                save_dir = "uploaded_journals"
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                
                file_path = os.path.join(save_dir, up_file.name)
                with open(file_path, "wb") as f:
                    f.write(up_file.getvalue())

                # บันทึกลง Google Sheet
                # ลำดับคอลัมน์: ID, คำนำหน้า, ชื่อ, นามสกุล, มหาลัย, คณะ, สาขา, สังกัด, ที่อยู่, เบอร์โทร, อีเมล, ประเภท, ชื่อไฟล์
                sheet.append_row([
                    next_id, prefix, first_name, last_name, uni, 
                    faculty, major, org, addr, phone, 
                    email_user, final_type, up_file.name
                ])
                st.success(f"ส่งข้อมูลสำเร็จ! ระบบบันทึกไฟล์ {up_file.name} เรียบร้อยแล้ว")
            else:
                st.error("กรุณาแนบไฟล์วารสารก่อนกด Send")

# --- 6. หน้าสำหรับ Admin (ตารางข้อมูล & ปุ่มดาวน์โหลด) ---
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
        if st.button("Logout"):
            logout()
        
        st.header("Admin Dashboard")
        st.subheader("📊 ข้อมูลการส่งวารสารทั้งหมด")
        try:
            data = pd.DataFrame(sheet.get_all_records())
            st.dataframe(data)
        except:
            st.info("ยังไม่มีข้อมูลในระบบ")

        st.divider()
        st.subheader("📁 ดาวน์โหลดไฟล์จากเครื่อง")
        save_dir = "uploaded_journals"
        if os.path.exists(save_dir):
            files = os.listdir(save_dir)
            if files:
                selected_file = st.selectbox("เลือกไฟล์ที่ต้องการดาวน์โหลด:", files)
                with open(os.path.join(save_dir, selected_file), "rb") as f:
                    st.download_button(
                        label=f"💾 ดาวน์โหลดไฟล์ {selected_file}",
                        data=f,
                        file_name=selected_file,
                        mime="application/octet-stream"
                    )
            else:
                st.info("ยังไม่มีไฟล์ถูกอัปโหลดเข้ามา")
        else:
            st.info("โฟลเดอร์เก็บไฟล์จะถูกสร้างเมื่อมีการส่งไฟล์ครั้งแรก")

# --- 7. Footer สีเขียว ตัวหนังสือขาว ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
