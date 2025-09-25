# pages/3_Organizer.py
import streamlit as st
from utils.db import get_db, sync_to_gsheets
from datetime import datetime
from utils.auth import require_login

require_login()  # Ensure user is logged in

st.title("🎤 Organizer Panel")
conn = get_db()
cur = conn.cursor()
username = st.session_state["user"]["username"]

# Create Event Form
st.subheader("📅 Create New Event")
with st.form("create_event_form"):
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Title")
        description = st.text_area("Description")
        start_dt = st.datetime_input("Start Date/Time")
    with col2:
        end_dt = st.datetime_input("End Date/Time")
        capacity = st.number_input("Capacity", min_value=1, value=50)
        fee = st.number_input("Fee (₹)", min_value=0.0, value=0.0)

    submitted = st.form_submit_button("Create Event")
    if submitted:
        try:
            cur.execute("""
                INSERT INTO events (title, description, start_dt, end_dt, capacity, organizer_username, fee)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, description, start_dt.isoformat(), end_dt.isoformat(), capacity, username, fee))
            conn.commit()
            sync_to_gsheets()
            st.success("✅ Event created successfully!")
        except Exception as e:
            st.error(f"Error creating event: {str(e)}")
        finally:
            conn.close()

# My Events Section
st.subheader("📋 My Events")
cur = conn.cursor()
cur.execute("SELECT * FROM events WHERE organizer_username = ? ORDER BY start_dt", (username,))
events = cur.fetchall()

if not events:
    st.info("You haven't created any events yet.")
else:
    for event in events:
        with st.expander(f"🎭 {event['title']}"):
            st.write(f"**Description:** {event['description']}")
            st.write(f"**When:** {event['start_dt']} to {event['end_dt']}")
            st.write(f"**Capacity:** {event['capacity']} | **Fee:** ₹{event['fee']}")

            # Show registrations
            cur.execute("SELECT * FROM registrations WHERE event_id = ?", (event['id'],))
            registrations = cur.fetchall()

            if registrations:
                st.subheader("📝 Registrations")
                for reg in registrations:
                    st.write(f"- {reg['name']} ({reg['email']}) - {'Paid' if reg['paid'] else 'Pending'}")
            else:
                st.info("No registrations yet")
