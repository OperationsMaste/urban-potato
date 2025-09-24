1# pages/4_MyAccount.py
import streamlit as st
from auth import require_login
from db import get_db

def main():
    if "user" not in st.session_state:
        st.warning("Login to view account.")
        return
    user = st.session_state['user']
    st.title("👤 My Account")
    st.write("Name:", user['full_name'])
    st.write("Username:", user['username'])
    st.write("Role:", user['role'])

    if st.button("Logout"):
        st.session_state.pop("user")
        st.success("Logged out. Refreshing...")
        st.experimental_rerun()

    st.markdown("---")
    st.subheader("Danger zone")
    st.write("Admins can delete accounts from admin panel. Use caution.")
