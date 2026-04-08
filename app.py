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
if 'admin_role' not in st.session_state:
    st.session_state.admin_role = "Viewer"

def logout():
    st.session_state.logged_in = False
    st.session_state.show_add_form = False
    st.session_state.admin_role = "Viewer"
    st.rerun()

# --- 4. แถบเมนูด้านข้าง ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", width=200)
    st.title("เมนูหลัก")
    page = st.radio("ไปที่หน้า:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin"])

# --- 5. หน้าสำหรับ User (ฟอร์ม 13 ข้อ) ---
if page == "หน้าสำหรับ User":
    st.header("ระบบจัดเก็บข้อมูลวารสารสหกิจศึกษาก้าวหน้า")
    try:
        next_id = len(sheet.get_all_values())
    except: next_id = 1

    with st.form("user_form"):
        st.info(f"1. ลำดับที่: {next_id}")
        c_p, c_f, c_l = st.columns([1, 2, 2])
        prefix = c_p.selectbox("2. คำนำหน้า", ["นาย", "นางสาว", "ผศ.", "รศ.", "ศ."])
        f_name = c_f.text_input("3. ชื่อ")
        l_name = c_l.text_input("4. นามสกุล")
        uni = st.text_input("5. มหาวิทยาลัย")
        faculty = st.text_input("6. คณะ")
        major = st.text_input("7. สาขาวิชา")
        org = st.text_input("8. สังกัด")
        addr = st.text_area("9. ที่อยู่")
        phone = st.text_input("10. เบอร์โทรศัพท์")
        email_u = st.text_input("11. E-mail")

        st.write("12. ประเภทบทความ")
        c1, c2, c3 = st.columns(3)
        t1, t2, t3 = c1.checkbox("บทความวิจัย"), c2.checkbox("บทความวิชาการ"), c3.checkbox("อื่นๆ")
        other_d = st.text_input("ระบุอื่นๆ") if t3 else ""

        up_file = st.file_uploader("13. แนบไฟล์", type=["pdf", "docx"])

        st.markdown("<br>", unsafe_allow_html=True)
        btn1, btn2, _ = st.columns([1, 1, 4])
        if btn1.form_submit_button("Send", type="primary"):
            if up_file:
                if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                with open(os.path.join("uploaded_journals", up_file.name), "wb") as f: f.write(up_file.getvalue())
                
                types = [t for t, v in zip(["วิจัย", "วิชาการ", f"อื่นๆ({other_d})"], [t1, t2, t3]) if v]
                sheet.append_row([next_id, prefix, f_name, l_name, uni, faculty, major, org, addr, phone, email_u, ", ".join(types), up_file.name])
                st.success("บันทึกข้อมูลเรียบร้อยแล้ว!")
            else: st.error("กรุณาแนบไฟล์")

# --- 6. หน้าสำหรับ Admin (แบ่งสิทธิ์การใช้งาน) ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.logged_in:
        st.subheader("Login สำหรับผู้ดูแลระบบ")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("เข้าสู่ระบบ"):
            admins = admin_sheet.get_all_records() if admin_sheet else []
            found = next((a for a in admins if str(a['Username']) == u_in and str(a['Password']) == p_in), None)
            
            if found or (u_in == "bannawit.s" and p_in == "adminjcep"):
                st.session_state.logged_in = True
                st.session_state.current_admin = found['Name'] if found else "Master Admin"
                # ตรวจสอบสิทธิ์ (ถ้า Master Admin ให้สิทธิ์สูงสุด)
                st.session_state.admin_role = found['Role'] if found else "Master Admin"
                st.rerun()
            else: st.error("ข้อมูลไม่ถูกต้อง")
    else:
        # แถบเมนูบน
        col_n, col_a, col_o = st.columns([3, 1, 1])
        col_n.write(f"สวัสดี: **{st.session_state.current_admin}** (สิทธิ์: {st.session_state.admin_role})")
        
        # เฉพาะ Master Admin เท่านั้นที่เพิ่มคนอื่นได้
        if st.session_state.admin_role == "Master Admin":
            if col_a.button("➕ Add Admin"): st.session_state.show_add_form = not st.session_state.show_add_form
            
        if col_o.button("Logout"): logout()

        # ฟอร์มเพิ่ม Admin (มี Dropdown สิทธิ์)
        if st.session_state.show_add_form:
            with st.expander("📝 เพิ่ม Admin และกำหนดสิทธิ์", expanded=True):
                with st.form("add_admin_form"):
                    n_user = st.text_input("Username")
                    n_pass = st.text_input("Password", type="password")
                    n_name = st.text_input("ชื่อ - นามสกุล")
                    n_mail = st.text_input("E-mail")
                    n_role = st.selectbox("กำหนดสิทธิ์การใช้งาน", ["Master Admin", "Admin (Viewer)"])
                    if st.form_submit_button("บันทึก"):
                        admin_sheet.append_row([n_user, n_pass, n_name, n_mail, n_role])
                        st.success(f"เพิ่มคุณ {n_name} เป็น {n_role} แล้ว!")
                        st.session_state.show_add_form = False

        st.header("Admin Dashboard")
        try:
            df = pd.DataFrame(sheet.get_all_records())
            st.dataframe(df)
        except: st.info("ยังไม่มีข้อมูลวารสาร")

        st.divider()
        # --- ตรวจสอบสิทธิ์ดาวน์โหลดไฟล์ ---
        if st.session_state.admin_role == "Master Admin":
            st.subheader("📁 จัดการไฟล์วารสาร (สิทธิ์ Master)")
            save_dir = "uploaded_journals"
            if os.path.exists(save_dir):
                files = os.listdir(save_dir)
                if files:
                    sel = st.selectbox("เลือกไฟล์:", files)
                    with open(os.path.join(save_dir, sel), "rb") as f:
                        st.download_button(f"💾 Download {sel}", f, file_name=sel)
                else: st.info("ไม่มีไฟล์ในระบบ")
        else:
            st.warning("🔒 คุณมีสิทธิ์ Viewer (ดูข้อมูลได้เท่านั้น ไม่สามารถดาวน์โหลดไฟล์ได้)")

st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
