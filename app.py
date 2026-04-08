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
        
        # --- ดึงแผ่นงานตามชื่อ (ย้ายตำแหน่งได้ ข้อมูลไม่สลับ) ---
        # 1. แผ่นข้อมูลวารสาร
        try:
            sheet = spreadsheet.worksheet("Data_2026") # เปลี่ยนชื่อปีตรงนี้ได้เลย
        except:
            sheet = spreadsheet.sheet1 # สำรองเผื่อหาชื่อไม่เจอ
            
        # 2. แผ่นข้อมูล Admin
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
    for key in list(st.session_state.keys()):
        del st.session_state[key]
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

        st.write("12. ประเภทบทความ")
        c1, c2, c3 = st.columns(3)
        t1, t2, t3 = c1.checkbox("บทความวิจัย"), c2.checkbox("บทความวิชาการ"), c3.checkbox("อื่นๆ")
        other_d = st.text_input("ระบุอื่นๆ") if t3 else ""

        up_file = st.file_uploader("13. แนบไฟล์ (PDF/Word)", type=["pdf", "docx", "doc"])

        st.markdown("<br>", unsafe_allow_html=True)
        btn1, btn2, _ = st.columns([1, 1, 4])
        if btn1.form_submit_button("Send", type="primary"):
            if up_file:
                save_dir = "uploaded_journals"
                if not os.path.exists(save_dir): os.makedirs(save_dir)
                with open(os.path.join(save_dir, up_file.name), "wb") as f: f.write(up_file.getvalue())
                
                types = [t for t, v in zip(["วิจัย", "วิชาการ", f"อื่นๆ({other_d})"], [t1, t2, t3]) if v]
                sheet.append_row([next_id, prefix, f_name, l_name, uni, faculty, major, org, addr, phone, email_u, ", ".join(types), up_file.name])
                st.success("บันทึกสำเร็จ!")
            else: st.error("กรุณาแนบไฟล์")
        
        if btn2.form_submit_button("Cancel", type="secondary"):
            st.rerun()

# --- 6. หน้าสำหรับ Admin (สิทธิ์ Master Admin / Viewer) ---
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
                st.session_state.admin_role = found['Role'] if found else "Master Admin"
                st.rerun()
            else: st.error("ข้อมูลไม่ถูกต้อง")
    else:
        # แถบควบคุมบน
        col_n, col_a, col_o = st.columns([3, 1, 1])
        col_n.write(f"ผู้ใช้: **{st.session_state.current_admin}** | สิทธิ์: **{st.session_state.admin_role}**")
        
        # เฉพาะ Master Admin ที่เพิ่มคนอื่นได้
        if st.session_state.admin_role == "Master Admin":
            if col_a.button("➕ Add Admin", type="primary"):
                st.session_state.show_add_form = not st.session_state.show_add_form
            
        if col_o.button("Logout", type="secondary"): logout()

        if st.session_state.show_add_form:
            with st.expander("📝 เพิ่มผู้ดูแลระบบและกำหนดสิทธิ์", expanded=True):
                with st.form("add_admin_form"):
                    n_user = st.text_input("Username")
                    n_pass = st.text_input("Password", type="password")
                    n_name = st.text_input("ชื่อ-นามสกุล")
                    n_mail = st.text_input("E-mail")
                    n_role = st.selectbox("สิทธิ์การใช้งาน", ["Master Admin", "Admin (Viewer)"])
                    if st.form_submit_button("บันทึก Admin"):
                        admin_sheet.append_row([n_user, n_pass, n_name, n_mail, n_role])
                        st.success("เพิ่มข้อมูลสำเร็จ!")
                        st.session_state.show_add_form = False

        st.header("Admin Dashboard")
        try:
            df = pd.DataFrame(sheet.get_all_records())
            st.dataframe(df, use_container_width=True)
        except: st.info("ยังไม่มีข้อมูลใน Sheet")

        st.divider()
        # เช็คสิทธิ์ดาวน์โหลดไฟล์
        if st.session_state.admin_role == "Master Admin":
            st.subheader("📁 ดาวน์โหลดไฟล์ (สิทธิ์ Master)")
            save_dir = "uploaded_journals"
            if os.path.exists(save_dir):
                files = os.listdir(save_dir)
                if files:
                    sel = st.selectbox("เลือกไฟล์:", files)
                    with open(os.path.join(save_dir, sel), "rb") as f:
                        st.download_button(f"💾 Download {sel}", f, file_name=sel)
                else: st.info("ไม่มีไฟล์ในโฟลเดอร์")
        else:
            st.warning("🔒 สิทธิ์ Viewer: ดูได้เฉพาะตารางข้อมูล (ไม่สามารถดาวน์โหลดไฟล์ได้)")

st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
