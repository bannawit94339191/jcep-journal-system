# --- ส่วนจัดการรายชื่อ (University / Agency) ที่เพิ่มระบบ Clear ค่า ---

# (ใช้โค้ดส่วนบนเหมือนเดิมจนถึงหน้าจัดการรายชื่อ)

else:
    target_sheet = sheet_uni if page == "จัดการรายชื่อมหาวิทยาลัย" else sheet_agency
    label = "มหาวิทยาลัย" if page == "จัดการรายชื่อมหาวิทยาลัย" else "หน่วยงาน"
    
    # 1. ตั้งค่า Key สำหรับเก็บค่าใน Session State เพื่อใช้ในการเคลียร์
    if f"name_{page}" not in st.session_state: st.session_state[f"name_{page}"] = ""
    if f"addr_{page}" not in st.session_state: st.session_state[f"addr_{page}"] = ""
    if f"cont_{page}" not in st.session_state: st.session_state[f"cont_{page}"] = ""
    if f"mail_{page}" not in st.session_state: st.session_state[f"mail_{page}"] = ""

    st.subheader(f"➕ เพิ่มข้อมูล{label}")
    with st.container(border=True):
        # 2. ผูกช่องกรอกกับ Session State
        new_name = st.text_input(f"ชื่อ{label}:", key=f"input_name_{page}", value=st.session_state[f"name_{page}"])
        new_addr = st.text_area("ที่อยู่:", key=f"input_addr_{page}", value=st.session_state[f"addr_{page}"])
        new_contact = st.text_input("ข้อมูลติดต่อ (เบอร์โทร):", key=f"input_cont_{page}", value=st.session_state[f"cont_{page}"])
        new_mail = st.text_input("E-mail:", key=f"input_mail_{page}", value=st.session_state[f"mail_{page}"])
        
        if st.button(f"🚀 บันทึกข้อมูล{label}", type="primary"):
            if new_name:
                try:
                    # บันทึกลง Google Sheets
                    target_sheet.append_row([new_name, new_addr, new_contact, new_mail])
                    
                    # 3. ล้างค่าใน Session State หลังจากบันทึกสำเร็จ
                    # วิธีการล้างคือล้าง Key ที่ผูกกับ widget
                    st.session_state[f"input_name_{page}"] = ""
                    st.session_state[f"input_addr_{page}"] = ""
                    st.session_state[f"input_cont_{page}"] = ""
                    st.session_state[f"input_mail_{page}"] = ""
                    
                    # แสดง Popup
                    show_message_modal("✅ เพิ่มข้อมูลเรียบร้อย")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")
            else:
                st.warning(f"⚠️ กรุณากรอกชื่อ{label}")
    
    st.write("---")
    # แสดงตารางข้อมูลด้านล่าง
    # ... (ส่วนแสดงตารางเหมือนเดิม)
