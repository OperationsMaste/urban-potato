# pages/1_Events.py
import streamlit as st
from utils.db import get_db, sync_to_gsheets
from utils.email import send_email
from utils.qr import generate_qr_code

st.title("📅 Events")
conn = get_db()
cur = conn.cursor()

# Show events
cur.execute("SELECT * FROM events ORDER BY start_dt")
events = cur.fetchall()

for event in events:
    st.subheader(event["title"])
    st.write(event["description"])
    if st.button(f"Register for {event['title']}"):
        # Registration form
        with st.form(f"reg_{event['id']}"):
            name = st.text_input("Full Name", value=st.session_state.user.get("full_name", ""))
            email = st.text_input("Email", value=st.session_state.user.get("email", ""))
            phone = st.text_input("Phone")
            if st.form_submit_button("Submit"):
                cur.execute("""
                    INSERT INTO registrations (event_id, username, name, email, phone)
                    VALUES (?, ?, ?, ?, ?)
                """, (event["id"], st.session_state.user["username"], name, email, phone))
                conn.commit()
                sync_to_gsheets()

                # Send confirmation email
                send_email(
                    email,
                    f"Registered for {event['title']}",
                    f"Hi {name},\n\nYou've registered for {event['title']}!"
                )

                # Show QR code
                qr = generate_qr_code(f"Event: {event['title']}\nName: {name}")
                st.image(qr, width=200)
                st.success("Registration successful!")
