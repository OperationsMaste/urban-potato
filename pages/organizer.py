# pages/3_Organizer.py
import streamlit as st
from utils.db import get_db, sync_to_gsheets
from datetime import datetime, time, date
from utils.auth import require_login

require_login()  # Ensure user is logged in

st.title("🎤 Organizer Panel")
conn = get_db()
username = st.session_state["user"]["username"]

# Create Event Form
st.subheader("📅 Create New Event")
with st.form("create_event_form"):
    col1, col2 = st.columns(2)

    with col1:
        title = st.text_input("Title", key="event_title")
        description = st.text_area("Description", key="event_desc")

        # Date and time inputs (compatible with all Streamlit versions)
        event_date = st.date_input("Event Date", key="event_date")
        event_start_time = st.time_input("Start Time", key="event_start_time")
        event_end_time = st.time_input("End Time", key="event_end_time")

    with col2:
        capacity = st.number_input("Capacity", min_value=1, value=50, key="event_capacity")
        fee = st.number_input("Fee (₹)", min_value=0.0, value=0.0, key="event_fee")

    submitted = st.form_submit_button("Create Event")

    if submitted:
        try:
            # Combine date and time
            start_dt = datetime.combine(event_date, event_start_time)
            end_dt = datetime.combine(event_date, event_end_time)

            if start_dt >= end_dt:
                st.error("End time must be after start time")
            else:
                cur = conn.cursor()
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
try:
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
                        if not reg['paid'] and st.button(f"Mark {reg['name']} as paid"):
                            cur.execute("UPDATE registrations SET paid = 1 WHERE id = ?", (reg['id'],))
                            conn.commit()
                            sync_to_gsheets()
                            st.rerun()
                else:
                    st.info("No registrations yet")

finally:
    conn.close()
