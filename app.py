# app.py
import streamlit as st
from utils.db import init_db
from utils.auth import login_ui, logout
from pages import events, admin, organizer, participant

# Initialize app with enhanced configuration
st.set_page_config(
    page_title="Fest ERP - Inter-College Festival Management",
    layout="wide",
    page_icon="🎉",
    initial_sidebar_state="collapsed"
)

# Initialize database
init_db()

# Custom CSS for better styling
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: nowrap;
        padding: 0 20px;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .error-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .info-box {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Show login form in the main content area (not sidebar)
def show_login_area():
    """Display login/signup area at the top of the page"""
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        login_ui()
    return

# Main navigation tabs (top bar)
def show_main_content():
    """Display the main content based on user role"""
    if "user" in st.session_state:
        role = st.session_state["user"]["role"]

        # Create tabs based on user role
        tabs = ["🏠 Home", "📅 Events", "👤 My Account"]
        if role == "admin":
            tabs.insert(2, "📊 Admin Dashboard")
        elif role == "organizer":
            tabs.insert(2, "🎤 Organizer Panel")
        elif role == "participant":
            tabs.insert(2, "🎟️ My Registrations")

        # Create the tabs
        tab1, tab2, tab3, *rest_tabs = st.tabs(tabs)

        with tab1:
            st.title("🎉 Inter-College Festival ERP")
            st.markdown("""
            <div class="info-box">
            <h3>Welcome to Fest ERP!</h3>
            <p>Use the tabs above to navigate through the system.</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            **Key Features:**
            - ✅ Role-based access control (Admin/Organizer/Participant)
            - ✅ Event creation, management and registration
            - ✅ QR code ticket generation
            - ✅ Email notifications for registrations
            - ✅ Google Sheets synchronization
            - ✅ Data export capabilities
            """)

        with tab2:
            events.show()

        with tab3:
            st.subheader("👤 Your Account")
            st.markdown(f"""
            <div class="info-box">
            <p><strong>Username:</strong> {st.session_state.user['username']}</p>
            <p><strong>Role:</strong> {st.session_state.user['role'].capitalize()}</p>
            <p><strong>Name:</strong> {st.session_state.user['full_name']}</p>
            <p><strong>Email:</strong> {st.session_state.user['email']}</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🔐 Logout", key="logout_button"):
                logout()
                st.rerun()

        # Role-specific content
        if role == "admin" and len(rest_tabs) > 0:
            with rest_tabs[0]:
                admin.show()
        elif role == "organizer" and len(rest_tabs) > 0:
            with rest_tabs[0]:
                organizer.show()
        elif role == "participant" and len(rest_tabs) > 0:
            with rest_tabs[0]:
                participant.show()

    else:
        # Guest view
        st.title("🎉 Inter-College Festival ERP")
        st.markdown("""
        <div class="info-box">
        <p>Please login to access all features of the Fest ERP system.</p>
        </div>
        """, unsafe_allow_html=True)
        events.show_guest()

# Main app flow
show_login_area()
show_main_content()

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>Fest ERP © 2023 | Inter-College Festival Management System</div>", unsafe_allow_html=True)
