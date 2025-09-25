# app.py
import streamlit as st
from utils.db import init_db
from utils.auth import login_ui

# Initialize app
st.set_page_config(page_title="Fest ERP", layout="wide", page_icon="🎉")
init_db()

# Always show login sidebar
login_ui()

# Navigation
st.sidebar.title("Navigation")
page = None

if "user" in st.session_state:
    role = st.session_state["user"]["role"]
    if role == "admin":
        page = st.sidebar.radio("Go to:", ["Home", "Admin Dashboard", "Events", "My Registrations"])
    elif role == "organizer":
        page = st.sidebar.radio("Go to:", ["Home", "Organizer Panel", "Events", "My Registrations"])
    else:  # participant
        page = st.sidebar.radio("Go to:", ["Home", "Events", "My Registrations"])

    if st.sidebar.button("Logout"):
        st.session_state.pop("user")
        st.rerun()
else:
    page = st.sidebar.radio("Go to:", ["Home", "Events"])

# Home page
if page == "Home":
    st.title("🎉 Inter-College Festival ERP")
    st.write("Welcome! Use the sidebar to navigate.")
    st.markdown("""
    **Features:**
    - Role-based access (Admin/Organizer/Participant)
    - Event creation & registration
    - QR code tickets
    - Email notifications
    - Google Sheets sync
    """)

# Admin page
elif page == "Admin Dashboard" and st.session_state.get("user", {}).get("role") == "admin":
    from pages import admin
    admin.show()

# Organizer page
elif page == "Organizer Panel" and st.session_state.get("user", {}).get("role") == "organizer":
    from pages import organizer
    organizer.show()

# Events page
elif page == "Events":
    from pages import events
    events.show()

# Participant page
elif page == "My Registrations":
    from pages import participant
    participant.show()
