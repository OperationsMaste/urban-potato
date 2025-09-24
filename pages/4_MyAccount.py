import streamlit as st

def main():
    if "user" not in st.session_state:
        st.warning("Login to view account")
        return
    st.title("👤 My Account")
    st.write(st.session_state["user"])
    if st.button("Logout"):
        st.session_state.pop("user")
        st.success("Logged out!")

if __name__ == "__main__":
    main()
