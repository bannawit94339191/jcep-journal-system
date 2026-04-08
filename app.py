import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import os
import time

# --- 1. การตั้งค่าหน้าจอและ CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    .stButton>button[kind="primary"] { background-color: #1E3A8A; color: white; border-radius: 8px; }
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border-radius: 8px; }
    section[data-testid="stSidebar"] { background-color: #F0F9FF; }
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        background-color: #28a745; color: white; text-align: center; 
        padding: 10px; font-weight: bold; z-index: 100;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. ฟังก์ชันจัดการ Popup (Modal) ---
@st.dialog("ผลการบันทึกข้อมูล")
def show_result_modal(status, message):
    if status == "success":
        st.success(message)
        st.balloons()
    else:
        st.error(message)
    if st.button("ตกลง"):
        st.rerun()

# --- 3. การเชื่อมต่อ Google Services ---
if "google_auth" in st.secrets:
    try:
        info = st.secrets["google_auth"]
        creds = service_account.Credentials.from_service_account_info(info)
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        client = gspread.authorize(creds.with_scopes(scope))
        spreadsheet = client.open("JCEP_Data")
        sheet = spreadsheet.worksheet("Data_2026")
        # เช็คว่ามี sheet สำหรับ Admin ไหม ถ้าไม่มีให้ใช้ sheet1 หรือสร้างใหม่
        try: admin_sheet = spreadsheet.worksheet("Admin_Users")
        except: admin_sheet = None
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")

# --- 4. Sidebar พร้อมปุ่ม Link 3 ปุ่ม ---
with st.sidebar:
    st.markdown("### 🏠 HOME")
    page = st.selectbox("เลือกเมนูการใช้งาน:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin"])
    st.markdown("<hr style='border-top: 2px solid #000000; margin-top: 0px;'>", unsafe_allow_html=True)
    
    st.markdown("🔗 **ลิงก์ที่เกี่ยวข้อง**")
    st.link_button("🏫 มทร.กรุงเทพ (RMUTK)", "https://rmutk.ac.th", use_container_width=True)
    st.link_button("🏢 สำนักงานสหกิจศึกษา (OCE)", "https://oce.rmutk.ac.th/", use_container_width=True)
    st.link_button("📘 วารสารสหกิจก้าวหน้า (JCEP)", "https://jcep.rmutk.ac.th/", use_container_width=True)

# --- 5. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    if os.path.exists("logo.gif"):
        st.image("logo.gif", use_container_width=True)
        st.write("---")

    try: next_id = len(sheet.get_all_values())
    except: next_id = 1

    with st.form("user_form", clear_on_submit=True):
        st.info(f"📍 ลำดับที่: {next_id}")
        col_p, col_f, col_l = st.columns([1, 2, 2])
        prefix = col_p.selectbox("คำนำหน้า", ["นาย", "นางสาว", "ผศ.", "รศ.", "ศ."])
        f_name, l_name = col_f.text_input("ชื่อ"), col_l.text_input("นามสกุล")
        uni = st.text_input("มหาวิทยาลัย / สถาบัน")
        col_fac, col_maj = st.columns(2)
        faculty, major = col_fac.text_input("คณะ"), col_maj.text_input("สาขาวิชา")
        org = st.text_input("สังกัด / หน่วยงาน")
        addr = st.text_area("ที่อยู่สำหรับการจัดส่งเอกสาร")
        col_tel, col_email = st.columns(2)
        phone, email_u = col_tel.text_input("เบอร์โทรศัพท์"), col_email.text_input("E-mail")

        st.write("---")
        article_type = st.radio("**12. ประเภทบทความ**", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"], horizontal=True)
        other_detail = st.text_input("โปรดระบุ (หากเลือกอื่นๆ)")

        st.write("---")
        up_file = st.file_uploader("13. แนบไฟล์ (PDF/Word)", type=["pdf", "docx", "doc"])

        btn1, btn2, _ = st.columns([1, 1, 4])
        if btn1.form_submit_button("ส่งข้อมูล", type="primary"):
            if up_file:
                try:
                    final_type = article_type if article_type != "อื่นๆ" else f"อื่นๆ: {other_detail}"
                    if not os.path.exists("uploaded_journals"): os.makedirs("uploaded_journals")
                    with open(os.path.join("uploaded_journals", up_file.name), "wb") as f: f.write(up_file.getvalue())
                    
                    sheet.append_row([next_id, prefix, f_name, l_name, uni, faculty, major, org, addr, phone, email_u, final_type, up_file.name])
                    show_result_modal("success", "บันทึกข้อมูลสำเร็จเรียบร้อยแล้ว!")
                except Exception as e:
                    show_result_modal("error", f"เกิดข้อผิดพลาด: {e}")
            else:
                st.warning("⚠️ กรุณาแนบไฟล์ก่อนส่ง")

# --- 6. หน้าสำหรับ Admin (กู้คืนตารางและปุ่มต่างๆ) ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.get('logged_in', False):
        st.subheader("🔐 เข้าสู่ระบบผู้ดูแลระบบ")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In", type="primary"):
            if u_in == "bannawit.s" and p_in == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Username หรือ Password ไม่ถูกต้อง")
    else:
        # ส่วนหัว Admin
        col_h1, col_h2 = st.columns([8, 2])
        col_h1.header("🖥️ แผงควบคุมผู้ดูแลระบบ (Admin Dashboard)")
        if col_h2.button("ออกจากระบบ", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()

        # ✅ 1. ตารางข้อมูล (กู้คืนมาแล้ว!)
        st.subheader("📊 ตารางข้อมูลวารสาร")
        try:
            data = sheet.get_all_records()
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
                
                # ✅ 2. ปุ่มดาวน์โหลดเอกสาร (กู้คืนมาแล้ว!)
                st.divider()
                st.subheader("📁 จัดการไฟล์แนบ")
                file_to_download = st.selectbox("เลือกไฟล์ที่ต้องการดาวน์โหลด:", df[df.columns[-1]].unique())
                file_path = os.path.join("uploaded_journals", str(file_to_download))
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        st.download_button(label=f"💾 ดาวน์โหลด {file_to_download}", data=f, file_name=str(file_to_download))
                else:
                    st.info("ไม่พบไฟล์ในระบบ (อาจยังไม่ได้อัปโหลดไฟล์จริงลงเซิร์ฟเวอร์)")
            else:
                st.info("ยังไม่มีข้อมูลในระบบ")
        except Exception as e:
            st.error(f"ไม่สามารถโหลดข้อมูลจาก Google Sheets ได้: {e}")

        # ✅ 3. ปุ่ม Add Admin (กู้คืนมาแล้ว!)
        st.divider()
        with st.expander("➕ เพิ่มผู้ดูแลระบบใหม่ (Add Admin)"):
            new_user = st.text_input("New Admin Username")
            new_pass = st.text_input("New Admin Password", type="password")
            if st.button("บันทึก Admin ใหม่"):
                if admin_sheet:
                    admin_sheet.append_row([new_user, new_pass])
                    st.success(f"เพิ่ม Admin: {new_user} สำเร็จ!")
                else:
                    st.error("ไม่พบ Sheet สำหรับเก็บข้อมูล Admin")

# --- 7. Footer สีเขียว ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)
