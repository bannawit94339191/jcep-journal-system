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
        sheet = spreadsheet.sheet1
        # เชื่อมต่อ Sheet สำหรับเก็บรายชื่อ Admin
        try:
            admin_sheet = spreadsheet.worksheet("Admin_Users")
        except:
            st.warning("กรุณาสร้างแผ่นงานชื่อ 'Admin_Users' ใน Google Sheet ด้วยครับ")
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")

# --- 3. ระบบจัดการ Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False

def logout():
    st.session_state.logged_in = False
    st.session_state.show_add_form = False
    st.rerun()

# --- 4. แถบเมนูด้านข้าง ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=200)
    st.title("เมนูหลัก")
    page = st.radio("ไปที่หน้า:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin"])

# --- 5. หน้าสำหรับ User (13 ข้อเหมือนเดิม) ---
if page == "หน้าสำหรับ User":
    st.header("ระบบจัดเก็บข้อมูลวารสารสหกิจศึกษาก้าวหน้า")
    try:
        next_id = len(sheet.get_all_values())
    except: next_id = 1

    with st.form("user_form"):
        st.info(f"1. ลำดับที่: {next_id}")
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("2. คำนำหน้า", ["นาย", "นางสาว", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์"])
        first_name = col_f.text_input("3. ชื่อ")
        last_name = col_l.text_input("4. นามสกุล")
        uni = st.text_input("5. มหาวิทยาลัย / สถาบัน")
        faculty = st.text_input("6. คณะ")
        major = st.text_input("7. สาขาวิชา")
        org = st.text_input("8. สังกัด / หน่วยงาน")
        addr = st.text_area("9. ที่อยู่")
        phone = st.text_input("10. เบอร์โทรศัพท์")
        email_user = st.text_input("11. E-mail")

        st.write("12. ประเภทบทความ")
        c1, c2, c3 = st.columns(3)
        t_res, t_acad, t_other = c1.checkbox("บทความวิจัย"), c2.checkbox("บทความวิชาการ"), c3.checkbox("อื่นๆ")
        other_detail = st.text_input("ระบุอื่นๆ") if t_other else ""

        up_file = st.file_uploader("13. แนบไฟล์วารสาร", type=["pdf", "docx"])

        st.markdown("<br>", unsafe_allow_html=True)
        btn_col1, btn_col2, _ = st.columns([1, 1, 4])
        if btn_col1.form_submit_button("Send", type="primary"):
            if up_file:
                save_dir = "uploaded_journals"
                if not os.path.exists(save_dir): os.makedirs(save_dir)
                with open(os.path.join(save_dir, up_file.name), "wb") as f: f.write(up_file.getvalue())
                
                sel_types = []
                if t_res: sel_types.append("บทความวิจัย")
                if t_acad: sel_types.append("บทความวิชาการ")
                if t_other: sel_types.append(f"อื่นๆ({other_detail})")
                
                sheet.append_row([next_id, prefix, first_name, last_name, uni, faculty, major, org, addr, phone, email_user, ", ".join(sel_types), up_file.name])
                st.success("ส่งข้อมูลสำเร็จ!")
            else: st.error("กรุณาแนบไฟล์")

# --- 6. หน้าสำหรับ Admin ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.logged_in:
        st.subheader("Login สำหรับผู้ดูแลระบบ")
        user_input = st.text_input("Username")
        pass_input = st.text_input("Password", type="password")
        if st.button("เข้าสู่ระบบ"):
            # ตรวจสอบสิทธิ์จาก Google Sheet (Admin_Users)
            try:
                admins = admin_sheet.get_all_records()
                found = next((a for a in admins if str(a['Username']) == user_input and str(a['Password']) == pass_input), None)
                
                if found:
                    st.session_state.logged_in = True
                    st.session_state.current_admin = found['Name']
                    st.rerun()
                # กรณี Master Admin (สำรอง)
                elif user_input == "bannawit.s" and pass_input == "adminjcep":
                    st.session_state.logged_in = True
                    st.session_state.current_admin = "Master Admin"
                    st.rerun()
                else: st.error("ข้อมูลไม่ถูกต้อง")
            except:
                # กรณีครั้งแรกที่ยังไม่มี Admin_Users Sheet
                if user_input == "bannawit.s" and pass_input == "adminjcep":
                    st.session_state.logged_in = True
                    st.session_state.current_admin = "Master Admin"
                    st.rerun()
                else: st.error("ไม่สามารถเชื่อมต่อฐานข้อมูล Admin ได้")
    else:
        # แถบด้านบน: ชื่อ Admin | ปุ่ม Add Admin | ปุ่ม Logout
        col_name, col_add, col_out = st.columns([4, 1, 1])
        col_name.write(f"ผู้ใช้งาน: **{st.session_state.current_admin}**")
        
        if col_add.button("➕ Add Admin", type="primary"):
            st.session_state.show_add_form = not st.session_state.show_add_form
            
        if col_out.button("Logout", type="secondary"): logout()

        # ส่วนฟอร์มเพิ่ม Admin (จะแสดงเมื่อกดปุ่ม Add Admin)
        if st.session_state.show_add_form:
            with st.expander("📝 เพิ่มผู้ดูแลระบบรายใหม่", expanded=True):
                with st.form("add_admin_form"):
                    new_user = st.text_input("1. Username")
                    new_pass = st.text_input("2. Password", type="password")
                    new_name = st.text_input("3. ชื่อ - นามสกุล")
                    new_mail = st.text_input("4. E-mail")
                    if st.form_submit_button("บันทึกข้อมูล Admin"):
                        if new_user and new_pass:
                            admin_sheet.append_row([new_user, new_pass, new_name, new_mail])
                            st.success(f"เพิ่มคุณ {new_name} เรียบร้อยแล้ว!")
                            st.session_state.show_add_form = False
                        else: st.error("กรุณากรอก Username และ Password")

        st.header("Admin Dashboard")
        try:
            data = pd.DataFrame(sheet.get_all_records())
            st.dataframe(data)
        except: st.info("ยังไม่มีข้อมูลวารสาร")

        st.divider()
        st.subheader("📁 จัดการไฟล์วารสาร")
        save_dir = "uploaded_journals"
        if os.path.exists(save_dir):
            files = os.listdir(save_dir)
            if files:
                sel_file = st.selectbox("เลือกไฟล์:", files)
                with open(os.path.join(save_dir, sel_file), "rb") as f:
                    st.download_button(f"💾 Download {sel_file}", f, file_name=sel_file)

# --- 7. Footer สีเขียว ตัวหนังสือขาว ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
