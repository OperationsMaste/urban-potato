# app.py
import streamlit as st
from utils.db import init_db
from utils.auth import login_ui
from pages import events, admin, .3_Organizer , .4_Particpants

# Initialize app
st.set_page_config(page_title="Fest ERP", layout="wide", page_icon="🎉")
init_db()

# Show login form in top bar
login_ui()

# Main navigation tabs (top bar)
if "user" in st.session_state:
    role = st.session_state["user"]["role"]

    # Always visible tabs
    tab1, tab2, tab3 = st.tabs(["🏠 Home", "📅 Events", "👤 My Account"])

    with tab1:
        st.title("🎉 Inter-College Festival ERP")
        st.write("Welcome! Use the tabs above to navigate.")
        st.markdown("""
        **Features:**
        - Role-based access (Admin/Organizer/Participant)
        - Event creation & registration
        - QR code tickets
        - Email notifications
        - Google Sheets sync
        """)

    with tab2:
        events.show()

    with tab3:
        st.subheader("Your Account")
        st.write("Logged in as:", st.session_state.user)
        if st.button("Logout"):
            st.session_state.pop("user")
            st.rerun()

    # Role-specific tabs
    if role == "admin":
        with st.expander("📊 Admin Dashboard", expanded=True):
            admin.show()

    elif role == "organizer":
        with st.expander("🎤 Organizer Panel", expanded=True):
            organizer.show()

    elif role == "participant":
        with st.expander("🎟️ My Registrations", expanded=True):
            participant.show()

else:
    # Guest view
    st.title("🎉 Inter-College Festival ERP")
    st.write("Please login to access all features")
    events.show_guest()
