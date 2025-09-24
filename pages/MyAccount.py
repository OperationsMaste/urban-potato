import streamlit as st

def my_account():
    st.title("👤 My Account")

    if "user" not in st.session_state:
        st.warning("⚠️ Please login first.")
        st.stop()

    user = st.session_state["user"]

    st.write(f"**Full Name:** {user['full_name']}")
    st.write(f"**Username:** {user['username']}")
    st.write(f"**Role:** {user['role']}")

    if st.button("🚪 Logout"):
        del st.session_state["user"]
        st.success("You have been logged out.")
        st.rerun()   # ✅ FIXED
