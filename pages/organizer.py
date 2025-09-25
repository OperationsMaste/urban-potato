# pages/organizer.py
import streamlit as st
from utils.db import get_db, sync_to_gsheets
from datetime import datetime

def show():
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

    # Show organizer's events
    cur.execute("SELECT * FROM events WHERE organizer_username = ? ORDER BY start_dt", (st.session_state.user["username"],))
    events = cur.fetchall()
    st.dataframe(events)
