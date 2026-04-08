import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os

# --- 1. ตั้งค่าพื้นฐานและการตกแต่ง CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    /* ปุ่มส่งข้อมูลสีน้ำเงินเข้ม */
    .stButton>button[kind="primary"] { background-color: #1E3A8A; color: white; border-radius: 8px; border: none; }
    /* ปุ่มยกเลิกสีแดง */
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border-radius: 8px; border: none; }
    
    /* ตกแต่ง Sidebar โทนสีน้ำเงิน-ฟ้า */
    section[data-testid="stSidebar"] { background-color: #F0F9FF; }
    [data-testid="stSidebar"] h1 { color: #1E3A8A; font-size: 24px; }
    
    /* จัดการโลโก้กึ่งกลาง */
    .logo-container { display: flex; justify-content: center; padding: 20px 0; }

    /* Footer สีเขียวสดใส (ตามใจคุณ!) */
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        background-color: #28a745; color: white; text-align: center; 
        padding: 10px; font-weight: bold; z-index: 100;
    }
    .main { padding-bottom: 80px; }
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
        
        # ดึง Sheet ตามชื่อปี
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

# --- 4. แถบเมนูด้านข้าง (เปลี่ยนเป็น Dropdown ตามคำขอ) ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        st.image("logo.png", width=140) # ปรับขนาดให้เล็กลงหน่อย
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<hr style='border-top: 2px solid #1E3A8A;'>", unsafe_allow_html=True)
    st.markdown("### 🧭 เมนู")
    
    # แก้ไขจุดนี้: เปลี่ยนจาก radio เป็น selectbox (Dropdown)
    page = st.selectbox(
        "กรุณาเลือกเมนูที่ต้องการ:",
        ["หน้าสำหรับ User", "หน้าสำหรับ Admin"],
        index=0
    )
    st.markdown("<br><br>", unsafe_allow_html=True)

# --- 5. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    st.header("📘 ระบบจัดเก็บข้อมูลวารสารสหกิจศึกษาก้าวหน้า")
    try:
        next_id = len(sheet.get_all_values())
    except: next_id = 1

    with st.form("user_form"):
        st.info(f"📍 ลำดับที่: {next_id}")
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้า", ["นาย", "นางสาว", "ผศ.", "รศ.", "ศ."])
        f_name = col_f.text_input("ชื่อ")
        l_name = col_l.text_input("นามสกุล")
        
        uni = st.text_input("มหาวิทยาลัย / สถาบัน")
        col_fac, col_maj = st.columns(2)
        faculty = col_fac.text_input("คณะ")
        major = col_maj.text_input("สาขาวิชา")
        org = st.text_input("สังกัด / หน่วยงาน")
        addr = st.text_area("ที่อยู่สำหรับการจัดส่งเอกสาร")
        
        col_tel, col_email = st.columns(2)
        phone = col_tel.text_input("เบอร์โทรศัพท์")
        email_u = col_email.text_input("E-mail")

        st.write("---")
        article_type = st.radio("**ประเภทบทความ (เลือก 1 รายการ)**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        other_detail = st.text_input("ระบุรายละเอียดเพิ่มเติม (ถ้าเลือก 'อื่นๆ')")

        st.write("---")
        up_file = st.file_uploader("แนบไฟล์ต้นฉบับ (PDF/Word)", type=["pdf", "docx", "doc"])

        st.markdown("<br>", unsafe_allow_html=True)
        btn1, btn2, _ = st.columns([1, 1, 4])
        
        if btn1.form_submit_button("ส่งข้อมูล", type="primary"):
            if up_file:
                final_type = article_type if article_type != "อื่นๆ" else f"อื่นๆ: {other_detail}"
                if article_type == "อื่นๆ" and not other_detail:
                    st.error("⚠️ กรุณาระบุรายละเอียดในช่องอื่นๆ")
                else:
                    if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                    with open(os.path.join("uploaded_journals", up_file.name), "wb") as f: f.write(up_file.getvalue())
                    sheet.append_row([next_id, prefix, f_name, l_name, uni, faculty, major, org, addr, phone, email_u, final_type, up_file.name])
                    st.success("🎉 บันทึกข้อมูลสำเร็จ!")
            else: st.error("⚠️ กรุณาแนบไฟล์ก่อนส่ง")
        
        if btn2.form_submit_button("ยกเลิก", type="secondary"):
            st.rerun()

# --- 6. หน้าสำหรับ Admin ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.logged_in:
        st.subheader("🔐 เข้าสู่ระบบผู้ดูแลระบบ")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In", type="primary"):
            admins = admin_sheet.get_all_records() if admin_sheet else []
            found = next((a for a in admins if str(a['Username']) == u_in and str(a['Password']) == p_in), None)
            if found or (u_in == "bannawit.s" and p_in == "adminjcep"):
                st.session_state.logged_in = True
                st.session_state.current_admin = found['Name'] if found else "Master Admin"
                st.session_state.admin_role = found['Role'] if found else "Master Admin"
                st.rerun()
            else: st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    else:
        col_n, col_a, col_o = st.columns([3, 1, 1])
        col_n.write(f"👤 ผู้ใช้: **{st.session_state.current_admin}** | 🛡️ สิทธิ์: **{st.session_state.admin_role}**")
        if st.session_state.admin_role == "Master Admin":
            if col_a.button("➕ เพิ่ม Admin", type="primary"):
                st.session_state.show_add_form = not st.session_state.show_add_form
        if col_o.button("ออกจากระบบ", type="secondary"): logout()

        if st.session_state.show_add_form:
            with st.expander("📝 ลงทะเบียน Admin ใหม่", expanded=True):
                with st.form("add_admin_form"):
                    n_user = st.text_input("Username")
                    n_pass = st.text_input("Password", type="password")
                    n_name = st.text_input("ชื่อ-นามสกุล")
                    n_mail = st.text_input("E-mail")
                    n_role = st.selectbox("กำหนดสิทธิ์", ["Master Admin", "Admin (Viewer)"])
                    if st.form_submit_button("บันทึกข้อมูล"):
                        admin_sheet.append_row([n_user, n_pass, n_name, n_mail, n_role])
                        st.success("เพิ่ม Admin เรียบร้อย!")
                        st.session_state.show_add_form = False

        st.header("🖥️ แผงควบคุมผู้ดูแลระบบ")
        try:
            df = pd.DataFrame(sheet.get_all_records())
            st.dataframe(df, use_container_width=True)
        except: st.info("ยังไม่มีข้อมูล")

        if st.session_state.admin_role == "Master Admin":
            st.divider()
            st.subheader("📁 จัดการไฟล์วารสาร")
            if os.path.exists("uploaded_journals"):
                files = os.listdir("uploaded_journals")
                if files:
                    sel = st.selectbox("เลือกไฟล์ที่ต้องการดาวน์โหลด:", files)
                    with open(os.path.join("uploaded_journals", sel), "rb") as f:
                        st.download_button(f"💾 ดาวน์โหลดไฟล์ {sel}", f, file_name=sel)

# --- 7. Footer สีเขียว ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
