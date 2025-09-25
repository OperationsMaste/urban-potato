# pages/2_Admin.py
import streamlit as st
from utils.db import get_db, sync_to_gsheets
from datetime import datetime

st.title("📊 Admin Dashboard")
conn = get_db()
cur = conn.cursor()

# User Management
st.subheader("👥 User Management")
with st.expander("Create User"):
    with st.form("create_user"):
        username = st.text_input("Username")
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        role = st.selectbox("Role", ["admin", "organizer", "participant"])
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Create User"):
            if not all([username, full_name, email, password]):
                st.error("❌ Fill all fields")
            else:
                try:
                    cur.execute("""
                        INSERT INTO users (username, password_hash, role, full_name, email)
                        VALUES (?, ?, ?, ?, ?)
                    """, (username, hash_password(password), role, full_name, email))
                    conn.commit()
                    sync_to_gsheets()
                    st.success(f"✅ User {username} created as {role}")
                except sqlite3.IntegrityError:
                    st.error("❌ Username exists")

# Event Management
st.subheader("🎭 Event Management")
with st.expander("Create Event"):
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

# Show all events
cur.execute("SELECT * FROM events ORDER BY start_dt")
events = cur.fetchall()
st.dataframe(events)
