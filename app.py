import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import gspread
import io

# --- 1. ตั้งค่าพื้นฐานและการตกแต่ง CSS ---
st.set_page_config(page_title="JCEP Journal System", layout="wide")

st.markdown("""
    <style>
    .stButton>button[kind="primary"] { background-color: #28a745; color: white; border: none; } /* สีเขียว */
    .stButton>button[kind="secondary"] { background-color: #dc3545; color: white; border: none; } /* สีแดง */
    .logout-btn { background-color: #808080 !important; color: white !important; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; padding: 10px; background: white; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Google Services ---
# (ดึงข้อมูลจาก Streamlit Secrets เมื่อ Deploy ออนไลน์)
if "google_auth" in st.secrets:
    info = st.secrets["google_auth"]
    creds = service_account.Credentials.from_service_account_info(info)
    # ขอบเขตการใช้งาน
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_with_scope = creds.with_scopes(scope)

    # เชื่อมต่อ Sheets
    client = gspread.authorize(creds_with_scope)
    sheet = client.open("JCEP_Data").sheet1  # เปลี่ยนชื่อไฟล์ให้ตรง

    # เชื่อมต่อ Drive
    drive_service = build('drive', 'v3', credentials=creds_with_scope)
    DRIVE_FOLDER_ID = "1O6YiaFonrDWCmdwDr94522qG4iCoIf6M"

# --- 3. ระบบจัดการ Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False


def logout():
    st.session_state.logged_in = False
    st.rerun()


# --- 4. แถบเมนูด้านข้าง ---
with st.sidebar:
    if "logo.png":
        st.image("logo.png", width=200)
    st.title("เมนูหลัก")
    page = st.radio("ไปที่หน้า:", ["หน้าสำหรับ User", "หน้าสำหรับ Admin"])

# --- 5. หน้าสำหรับ User ---
if page == "หน้าสำหรับ User":
    st.header("ระบบจัดเก็บข้อมูลวารสารสหกิจศึกษาก้าวหน้า")
    st.subheader("Journal of Cooperative Education Progress")

    # ดึงลำดับล่าสุดจาก Google Sheet
    existing_data = sheet.get_all_values()
    next_id = len(existing_data)  # รันเลขต่อจากแถวที่มีอยู่

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

        # 10. ประเภทบทความ (เลือกได้ 1 อย่าง)
        article_type = st.radio("10. ประเภทบทความ", ["บทความวิจัย", "บทความวิชาการ", "อื่นๆ"])
        other_type = ""
        if article_type == "อื่นๆ":
            other_type = st.text_input("กรุณาระบุประเภทบทความ")

        final_type = other_type if article_type == "อื่นๆ" else article_type

        # 11. แนบไฟล์
        up_file = st.file_uploader("11. แนบไฟล์วารสาร")

        col1, col2, _ = st.columns([1, 1, 4])
        with col1:
            submit = st.form_submit_button("Send", type="primary")
        with col2:
            cancel = st.form_submit_button("Cancel", type="secondary")

        if submit:
            file_link = ""
            if up_file:
                # อัปโหลดไฟล์ไป Google Drive
                file_metadata = {'name': up_file.name, 'parents': [DRIVE_FOLDER_ID]}
                media = MediaIoBaseUpload(io.BytesIO(up_file.getvalue()), mimetype=up_file.type)
                file = drive_service.files().create(body=file_metadata, media_body=media,
                                                    fields='id, webViewLink').execute()
                file_link = file.get('webViewLink')

            # บันทึกลง Google Sheet
            sheet.append_row([next_id, name, uni, faculty, major, org, addr, phone, email, final_type, file_link])
            st.success("ส่งข้อมูลสำเร็จ!")

# --- 6. หน้าสำหรับ Admin ---
elif page == "หน้าสำหรับ Admin":
    if not st.session_state.logged_in:
        # ส่วน Login
        st.subheader("Login สำหรับผู้ดูแลระบบ")
        user_input = st.text_input("Username", placeholder="กรุณาใส่ Username")
        pass_input = st.text_input("Password", type="password", placeholder="กรุณาใส่ Password")

        if st.button("เข้าสู่ระบบ"):
            if user_input == "bannawit.s" and pass_input == "adminjcep":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("ข้อมูลไม่ถูกต้อง")
    else:
        # ส่วน Logout มุมขวาบน
        col_title, col_logout = st.columns([5, 1])
        with col_logout:
            if st.button("Logout", help="กดเพื่อออกจากระบบ"):
                logout()

        st.header("Admin Dashboard")
        data = pd.DataFrame(sheet.get_all_records())
        st.dataframe(data)

        # ปุ่มดึงข้อมูลออกมาเป็น CSV
        csv = data.to_csv(index=False).encode('utf-8-sig')
        st.download_button("ดาวน์โหลดข้อมูลทั้งหมด", data=csv, file_name="journal_summary.csv", mime="text/csv")

# --- Footer ---
st.markdown('<div class="footer">Update by Bannawit S. (OCE - RMUTK)</div>', unsafe_allow_html=True)