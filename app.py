# app.py
import streamlit as st
from utils.db import init_db
from utils.auth import login_ui, logout, require_login
from pages import events, admin, organizer, participant

# Initialize app with professional configuration
st.set_page_config(
    page_title="Fest ERP | Inter-College Festival Management",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize database
init_db()

# Custom CSS for professional styling
def inject_custom_css():
    st.markdown("""
    <style>
        /* Main container styling */
        .main {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Header styling */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            margin-bottom: 20px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 45px;
            padding: 0 25px;
            font-weight: 500;
            border-radius: 6px 6px 0 0;
            margin-right: 5px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #fff;
            border-bottom-color: #fff;
            color: #007bff;
        }

        /* Button styling */
        .stButton>button {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.3s;
        }

        .stButton>button:hover {
            background-color: #0069d9;
            color: white;
        }

        /* Card styling */
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }

        /* Info boxes */
        .info-box {
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
        }

        .info-box.blue {
            background-color: #d1ecf1;
            border-left: 4px solid #17a2b8;
        }

        .info-box.green {
            background-color: #d4edda;
            border-left: 4px solid #28a745;
        }

        .info-box.red {
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
        }

        /* Footer styling */
        .footer {
            margin-top: 40px;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
            border-top: 1px solid #eee;
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
            .stTabs [data-baseweb="tab"] {
                padding: 0 15px;
                font-size: 14px;
            }
        }
    </style>
    """, unsafe_allow_html=True)

# Display login area at the top
def show_login_area():
    """Display login/signup area at the top of the page"""
    with st.container():
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("### 🔑 Authentication")
            login_ui()
        with col2:
            if "user" in st.session_state:
                st.markdown(f"""
                <div class="info-box green">
                    <p><strong>Welcome back, {st.session_state.user['full_name']}!</strong></p>
                    <p>Role: {st.session_state.user['role'].capitalize()}</p>
                </div>
                """, unsafe_allow_html=True)

# Main navigation and content
def show_main_content():
    """Display the main content based on user role"""
    if "user" in st.session_state:
        role = st.session_state["user"]["role"]

        # Base tabs for all logged-in users
        tabs = ["🏠 Home", "📅 Events", "👤 My Account"]

        # Add role-specific tabs
        if role == "admin":
            tabs.insert(1, "📊 Admin Dashboard")
        elif role == "organizer":
            tabs.insert(1, "🎤 Organizer Panel")
        elif role == "participant":
            tabs.insert(1, "🎟️ My Registrations")

        # Create tabs
        tab_objects = st.tabs(tabs)

        # Home tab content
        with tab_objects[0]:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.title("🎉 Fest ERP Dashboard")
            st.markdown("""
            Welcome to the **Inter-College Festival Management System**!

            **Key Features:**
            - ✅ Role-based access control (Admin/Organizer/Participant)
            - ✅ Comprehensive event management
            - ✅ Participant registration with QR code tickets
            - ✅ Automated email notifications
            - ✅ Google Sheets synchronization
            - ✅ Data export capabilities
            """)
            st.markdown("</div>", unsafe_allow_html=True)

        # Events tab content
        with tab_objects[1 if role != "participant" else 2]:
            events.show()

        # Account tab content
        with tab_objects[-1]:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("👤 Your Account Information")

            st.markdown(f"""
            <div class="info-box blue">
                <p><strong>Username:</strong> {st.session_state.user['username']}</p>
                <p><strong>Role:</strong> {st.session_state.user['role'].capitalize()}</p>
                <p><strong>Name:</strong> {st.session_state.user['full_name']}</p>
                <p><strong>Email:</strong> {st.session_state.user['email']}</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🔐 Logout", key="logout_button"):
                logout()
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # Role-specific content
        if role == "admin" and len(tab_objects) > 3:
            with tab_objects[1]:
                admin.show()
        elif role == "organizer" and len(tab_objects) > 3:
            with tab_objects[1]:
                organizer.show()
        elif role == "participant" and len(tab_objects) > 3:
            with tab_objects[1]:
                participant.show()

    else:
        # Guest view
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.title("🎉 Fest ERP - Inter-College Festival Management")
        st.markdown("""
        <div class="info-box blue">
            <p>Please login to access all features of the Fest ERP system.</p>
            <p>As a guest, you can only view available events.</p>
        </div>
        """, unsafe_allow_html=True)
        events.show_guest()
        st.markdown("</div>", unsafe_allow_html=True)

# Main app execution
inject_custom_css()
show_login_area()
show_main_content()

# Footer
st.markdown("""
<div class="footer">
    <p>Fest ERP © 2023 | Inter-College Festival Management System</p>
    <p>Developed with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)
