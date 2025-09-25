# pages/3_Organizer.py
import streamlit as st
from utils.db import get_db, sync_to_gsheets
from utils.auth import require_login
from datetime import datetime

require_login()
st.title("🎤 Organizer Dashboard")
conn = get_db()
cur = conn.cursor()

# Create Event
st.subheader("📅 Create Event")
with st.form("create_event"):
    title = st.text_input("Title")
    description = st.text_area("Description")
    start_dt = st.datetime_input("Start Date/Time")
    end_dt = st.datetime_input("End Date/Time")
    capacity = st.number_input("Capacity", min_value=1)
    fee = st.number_input("Fee (₹)", min_value=0.0)
    if st.form_submit_button("Create Event"):
        cur.execute("""
            INSERT INTO events (title, description, start_dt, end_dt, capacity, organizer_username, fee)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, description, start_dt.isoformat(), end_dt.isoformat(), capacity, st.session_state.user["username"], fee))
        conn.commit()
        sync_to_gsheets()
        st.success("✅ Event created")

# My Events
st.subheader("📋 Your Events")
cur.execute("SELECT * FROM events WHERE organizer_username = ? ORDER BY start_dt", (st.session_state.user["username"],))
events = cur.fetchall()
for event in events:
    st.subheader(event["title"])
    st.write(event["description"])
    st.write(f"**When:** {event['start_dt']} to {event['end_dt']}")
    st.write(f"**Capacity:** {event['capacity']} | **Fee:** ₹{event['fee']}")

    if st.button(f"View Registrations for {event['title']}"):
        cur.execute("SELECT * FROM registrations WHERE event_id = ?", (event["id"],))
        registrations = cur.fetchall()
        st.dataframe(registrations)
