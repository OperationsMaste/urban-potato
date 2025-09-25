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
    st.sidebar.markdown("[Events](1_Events)", unsafe_allow_html=True)

    if role == "admin":
        st.sidebar.markdown("[Admin Dashboard](2_Admin)", unsafe_allow_html=True)
    elif role == "organizer":
        st.sidebar.markdown("[Organizer Panel](3_Organizer)", unsafe_allow_html=True)

    st.sidebar.markdown("[My Registrations](4_Participant)", unsafe_allow_html=True)

    if st.sidebar.button("Logout"):
        st.session_state.pop("user")
        st.rerun()
else:
    st.sidebar.markdown("[Events](1_Events)", unsafe_allow_html=True)
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
