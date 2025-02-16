import streamlit as st
import datetime
from db import get_connection, create_tables, insert_presets
from auth import login, register
from tasks import check_notifications
from pages import dashboard, profile, overdue_tasks, task_page1

# Initialize database
conn = get_connection()
create_tables(conn)
insert_presets(conn)

# Session state initialization
if "logged_in" not in st.session_state:
    st.session_state.update({
        "logged_in": False,
        "show_register": False,
        "username": None,
        "mock_now": datetime.date.today(),
        "current_page": "Dashboard"
    })

# Authentication check
if not st.session_state.logged_in:
    st.set_page_config(initial_sidebar_state="collapsed")
    st.markdown("""
        <style>
            [data-testid="collapsedControl"] { display: none; }
        </style>
    """, unsafe_allow_html=True)

    # Login/Register Page
    col1, col2 = st.columns([1, 2])
    with col2:
        st.title("AutoTask Login" if not st.session_state.show_register else "User Registration")

        if st.session_state.show_register:
            with st.form("register_form"):
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                full_name = st.text_input("Full Name")
                email = st.text_input("Email")
                address = st.text_input("Address")
                gender = st.selectbox("Gender", ("Male", "Female", "Other"))
                contact = st.text_input("Contact")

                if st.form_submit_button("Register"):
                    if register(new_username, new_password, full_name, email, address, gender, contact):
                        st.success("Registration successful! Please login.")
                        st.session_state.show_register = False
                        st.rerun()
        else:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")

                if st.form_submit_button("Login"):
                    if login(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.current_page = "Dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

        if st.button("Create New Account"):
            st.session_state.show_register = True
            st.rerun()
    st.stop()

# Main app layout
st.set_page_config(initial_sidebar_state="expanded")

# Single sidebar navigation implementation
with st.sidebar:
    st.title("AutoTask Navigation")

    # Main navigation menu
    nav_options = {
        "📊 Dashboard": "Dashboard",
        "📝 Tasks": "Task Page1",
        "⚠️ Overdue Tasks": "Overdue Tasks",
        "👤 User Profile": "User Profile"
    }

    # Create navigation buttons
    for display_name, page_name in nav_options.items():
        if st.button(display_name, use_container_width=True):
            st.session_state.current_page = page_name

    # Admin-only time controls
    if st.session_state.username == "admin":
        st.divider()
        st.header("⏰ Debug Controls")
        new_date = st.date_input("Mock Date", st.session_state.mock_now)
        if new_date != st.session_state.mock_now:
            st.session_state.mock_now = new_date
            st.rerun()

        if st.button("⏩ Fast Forward 1 Day"):
            st.session_state.mock_now += datetime.timedelta(days=1)
            st.rerun()

    # Logout button
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

# Page content routing
check_notifications(st.session_state.mock_now)

if st.session_state.current_page == "Dashboard":
    dashboard.show_dashboard()
elif st.session_state.current_page == "Task Page1":
    task_page1.show_task_page1()
elif st.session_state.current_page == "Overdue Tasks":
    overdue_tasks.show_overdue_tasks()
elif st.session_state.current_page == "User Profile":
    profile.show_profile()
