# pages/1_Events.py
import streamlit as st
from utils.db import get_db, sync_to_gsheets
from utils.email import send_email
from utils.qr import generate_qr_code
from datetime import datetime

st.title("📅 Events")
conn = get_db()
cur = conn.cursor()

# Show events
cur.execute("SELECT * FROM events ORDER BY start_dt")
events = cur.fetchall()

for event in events:
    st.subheader(event["title"])
    st.write(event["description"])
    st.write(f"**When:** {event['start_dt']} to {event['end_dt']}")
    st.write(f"**Capacity:** {event['capacity']} | **Fee:** ₹{event['fee']}")

    cur.execute("SELECT COUNT(*) as cnt FROM registrations WHERE event_id = ?", (event["id"],))
    registered = cur.fetchone()["cnt"]
    st.write(f"**Registered:** {registered}/{event['capacity']}")

    if "user" in st.session_state and registered < event["capacity"]:
        if st.button(f"Register for {event['title']}"):
            with st.form(f"reg_{event['id']}"):
                name = st.text_input("Full Name", value=st.session_state.user.get("full_name", ""))
                email = st.text_input("Email", value=st.session_state.user.get("email", ""))
                phone = st.text_input("Phone")
                if st.form_submit_button("Submit"):
                    cur.execute("""
                        INSERT INTO registrations (event_id, username, name, email, phone, amount, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (event["id"], st.session_state.user["username"], name, email, phone, event["fee"], datetime.now().isoformat()))
                    conn.commit()
                    sync_to_gsheets()

                    # Send confirmation email
                    send_email(
                        email,
                        f"Registered for {event['title']}",
                        f"Hi {name},\n\nYou've registered for {event['title']}!\n\nEvent Date: {event['start_dt']}\nFee: ₹{event['fee']}"
                    )

                    # Show QR code
                    qr = generate_qr_code(f"Event: {event['title']}\nName: {name}\nEmail: {email}")
                    st.image(qr, caption="Your Ticket QR Code", width=200)
                    st.success("Registration successful!")
