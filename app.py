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
if "user" in st.session_state:
    role = st.session_state["user"]["role"]
    if role == "admin":
        st.sidebar.page_link("pages/2_Admin.py", label="Admin Dashboard")
    elif role == "organizer":
        st.sidebar.page_link("pages/3_Organizer.py", label="Organizer Panel")
    st.sidebar.page_link("pages/1_Events.py", label="Events")
    st.sidebar.page_link("pages/4_Participant.py", label="My Registrations")
    if st.sidebar.button("Logout"):
        st.session_state.pop("user")
        st.rerun()
else:
    st.sidebar.page_link("pages/1_Events.py", label="Events")
    st.sidebar.markdown("Login to access more features")

# Home page
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
