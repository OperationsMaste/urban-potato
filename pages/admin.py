# pages/admin.py
import streamlit as st
from utils.db import get_db, sync_to_gsheets
from utils.auth import hash_password
from datetime import datetime

def show():
    conn = get_db()
    cur = conn.cursor()

    # User Management
    st.subheader("👥 User Management")
    with st.expander("Create New User"):
        with st.form("create_user"):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Username")
                full_name = st.text_input("Full Name")
                email = st.text_input("Email")
            with col2:
                role = st.selectbox("Role", ["admin", "organizer", "participant"])
                password = st.text_input("Password", type="password")

            if st.form_submit_button("Create User"):
                if not all([username, full_name, email, password]):
                    st.error("Please fill all fields")
                else:
                    try:
                        cur.execute("""
                            INSERT INTO users (username, password_hash, role, full_name, email)
                            VALUES (?, ?, ?, ?, ?)
                        """, (username, hash_password(password), role, full_name, email))
                        conn.commit()
                        sync_to_gsheets()
                        st.success(f"✅ User {username} created as {role}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # Event Management
    st.subheader("🎭 Event Management")
    with st.expander("Create New Event"):
        with st.form("create_event"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Title")
                description = st.text_area("Description")
                start_dt = st.datetime_input("Start Date/Time")
            with col2:
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
                st.success("✅ Event created successfully")

    # Data Export
    st.subheader("📤 Data Export")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export Users CSV"):
            users = pd.DataFrame(conn.execute("SELECT * FROM users").fetchall())
            st.download_button("Download users.csv", users.to_csv(index=False).encode('utf-8'), "users.csv")
    with col2:
        if st.button("Export Events CSV"):
            events = pd.DataFrame(conn.execute("SELECT * FROM events").fetchall())
            st.download_button("Download events.csv", events.to_csv(index=False).encode('utf-8'), "events.csv")

    # Show all events
    st.subheader("📋 All Events")
    cur.execute("SELECT * FROM events ORDER BY start_dt")
    events = pd.DataFrame(cur.fetchall())
    st.dataframe(events)
