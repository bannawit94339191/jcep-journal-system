import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import io
import os
import smtplib
from email.message import EmailMessage


# --- ฟังก์ชันสำหรับส่งอีเมล ---
def send_email(sender_email, sender_password, receiver_email, subject, body, file_name, file_bytes):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg.set_content(body)

    # แนบไฟล์ไปกับอีเมล
    msg.add_attachment(file_bytes, maintype='application', subtype='octet-stream', filename=file_name)

    try:
        # เชื่อมต่อกับเซิร์ฟเวอร์ Gmail
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการส่งอีเมล: {e}")
        return False


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

# --- 2. การเชื่อมต่อ Google Services (เหลือแค่ Sheets) ---
if "google_auth" in st.secrets:
    info = st.secrets["google_auth"]
    creds = service_account.Credentials.from_service_account_info(info)
    # ขอบเขตการใช้งาน (เอา Drive ออก เหลือแค่ Sheets)
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds_with_scope = creds.with_scopes(scope)

    # เชื่อมต่อ Sheets
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

    # ดึงลำดับล่าสุดจาก Google Sheet
    try:
        existing_data = sheet.get_all_values()
        next_id = len(existing_data)  # รันเลขต่อจากแถวที่มีอยู่
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
            file_link = "ไม่มีไฟล์แนบ"

            if up_file:
                # --- ส่วนที่ 1: เซฟลงเครื่อง (Local Folder) ---
                save_dir = "uploaded_journals"
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)  # สร้างโฟลเดอร์ถ้ายังไม่มี

                file_path = os.path.join(save_dir, up_file.name)

                # เขียนไฟล์ลงไปในโฟลเดอร์
                with open(file_path, "wb") as f:
                    f.write(up_file.getvalue())

                file_link = f"บันทึกในเครื่อง: {file_path}"

                # --- ส่วนที่ 2: ส่งเข้าอีเมล ---
                if "email_config" in st.secrets:
                    sender_email = st.secrets["email_config"]["sender_email"]
                    sender_password = st.secrets["email_config"]["sender_password"]
                    receiver_email = st.secrets["email_config"]["receiver_email"]

                    subject = f"มีวารสารใหม่ส่งเข้ามาจาก: {name}"
                    body = f"รายละเอียดผู้ส่ง:\nชื่อ: {name}\nสถาบัน: {uni}\nประเภทบทความ: {final_type}\nเบอร์โทร: {phone}\nอีเมล: {email}"

                    with st.spinner('กำลังส่งข้อมูลและไฟล์เข้าอีเมล...'):
                        is_sent = send_email(sender_email, sender_password, receiver_email, subject, body, up_file.name,
                                             up_file.getvalue())

                    if is_sent:
                        file_link = "ส่งเข้าอีเมลสำเร็จแล้ว"
                    else:
                        file_link = "บันทึกในเครื่องแล้ว (แต่ส่งอีเมลไม่สำเร็จ)"
                else:
                    st.warning("ระบบเซฟไฟล์ลงเครื่องแล้ว แต่ยังไม่ได้ตั้งค่า Secrets สำหรับส่งอีเมล")

            # บันทึกลง Google Sheet
            sheet.append_row([next_id, name, uni, faculty, major, org, addr, phone, email, final_type, file_link])
            st.success("ส่งข้อมูลสำเร็จ! ระบบได้บันทึกข้อมูลและไฟล์เรียบร้อยแล้ว 🎉")

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

# --- Footer
