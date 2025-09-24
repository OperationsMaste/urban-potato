# app.py
import streamlit as st
from db import init_db
from auth import login_ui
from utils import local_css

def main():
    st.set_page_config(page_title="Fest ERP", layout="wide", initial_sidebar_state="expanded")
    init_db()
    local_css()

    c1, c2 = st.columns([5,1])
    with c1:
        st.markdown("<h1 style='margin:0'>🎉 Fest ERP — Inter-College Portal</h1>", unsafe_allow_html=True)
        st.markdown("Manage events, registrations, tickets, and analytics — multi-page Streamlit app.")
    with c2:
        if "user" in st.session_state:
            u = st.session_state["user"]
            st.markdown(f"**{u['full_name']}**  \n_{u['role']}_")
        else:
            st.markdown("**Not signed in**")

    st.markdown("---")
    login_ui()

    st.sidebar.markdown("### Navigation")
    st.sidebar.info("Use the Pages menu (top-left) to switch between portal pages.")
    st.caption("Tip: Sign up as a participant or sign in as admin (admin/admin123) to see all features.")

if __name__ == "__main__":
    main()
