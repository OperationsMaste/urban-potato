import streamlit as st
from db import init_db
from auth import login_ui

def main():
    st.set_page_config(page_title="Fest ERP", layout="wide")
    init_db()
    st.title("🎉 Inter-College Festival ERP")
    st.markdown("""
    Welcome to the official portal.  
    - **Participants**: Browse and register for events.  
    - **Organizers**: Create and manage your events.  
    - **Admins**: Oversee the entire festival ERP.  
    """)

    login_ui()

if __name__ == "__main__":
    main()
