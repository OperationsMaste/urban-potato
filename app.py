
import streamlit as st
from pages.Events import Events
from pages.Organizer import Organizer
from pages.Admin import Admin
from pages.MyAccount import MyAccount

st.set_page_config(
    page_title="Urban Potato ERP",
    page_icon="🥔",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("<h1 style='text-align: center;'>Urban Potato ERP</h1>", unsafe_allow_html=True)
def main():
    pages = {
        "Events": Events,
        "Organizer": Organizer,
        "Admin": Admin,
        "MyAccount": MyAccount
    }
    
    st.sidebar.title("Navigation")
    selection = st.sidebar.selectbox("Go to", list(pages.keys()))
    
    page = pages[selection]
    page.main()
if __name__ == "__main__":
    main()
