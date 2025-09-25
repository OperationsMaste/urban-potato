# pages/events.py
import streamlit as st
from utils.db import get_db, sync_to_gsheets
from utils.email import send_email
from utils.qr import generate_qr_code
from datetime import datetime

def show():
    st.title("📅 Events")
    conn = get_db()
    cur = conn.cursor()

    # Search and filter
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Search events")
    with col2:
        free_only = st.checkbox("Free events only")

    # Show events
    query = "SELECT * FROM events ORDER BY start_dt"
    if search:
        query += f" WHERE title LIKE '%{search}%' OR description LIKE '%{search}%'"
    if free_only:
        query += " AND fee = 0" if "WHERE" in query else " WHERE fee = 0"

    cur.execute(query)
    events = cur.fetchall()

    if not events:
        st.info("No events found")
        return

    for event in events:
        with st.expander(f"🎭 {event['title']}", expanded=True):
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
                        if st.form_submit_button("Submit Registration"):
                            cur.execute("""
                                INSERT INTO registrations (event_id, username, name, email, phone, amount, timestamp)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (event["id"], st.session_state.user["username"], name, email, phone, event["fee"], datetime.now().isoformat()))
                            conn.commit()
                            sync_to_gsheets()

                            # Send confirmation email
                            send_email(
                                email,
                                f"Registration Confirmation: {event['title']}",
                                f"""Hi {name},

                                You have successfully registered for {event['title']}!

                                Event Details:
                                - Date: {event['start_dt']} to {event['end_dt']}
                                - Fee: ₹{event['fee']}

                                Thank you for registering!
                                """
                            )

                            # Show QR code
                            qr = generate_qr_code(f"Event: {event['title']}\nName: {name}\nEmail: {email}")
                            st.image(qr, caption="Your Ticket QR Code", width=200)
                            st.success("✅ Registration successful! Check your email for confirmation.")

def show_guest():
    st.title("📅 Events")
    conn = get_db()
    cur = conn.cursor()

    # Show events (read-only for guests)
    cur.execute("SELECT * FROM events ORDER BY start_dt")
    events = cur.fetchall()

    if not events:
        st.info("No events available")
        return

    for event in events:
        with st.expander(f"🎭 {event['title']}"):
            st.write(event["description"])
            st.write(f"**When:** {event['start_dt']} to {event['end_dt']}")
            st.write(f"**Capacity:** {event['capacity']} | **Fee:** ₹{event['fee']}")

            cur.execute("SELECT COUNT(*) as cnt FROM registrations WHERE event_id = ?", (event["id"],))
            registered = cur.fetchone()["cnt"]
            st.write(f"**Registered:** {registered}/{event['capacity']}")

            st.warning("Please login to register for events")
