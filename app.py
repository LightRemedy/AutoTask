import streamlit as st
import datetime
from db import get_connection, create_tables, insert_presets
from auth import login, register
from tasks import check_notifications
from pages import dashboard, profile, overdue_tasks, task_page1, group_page
from pathlib import Path

# ========== FIRST AND ONLY set_page_config ==========
st.set_page_config(
    page_title="AutoTask",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Get Base Directory (the directory where this script is located)
BASE_DIRECTORY = Path(__file__).resolve().parent

# Define the path to the company logo image
logo_file_path = BASE_DIRECTORY / "assets" / "icon.png"

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.update({
        "logged_in": False,
        "show_register": False,
        "username": None,
        "mock_now": datetime.date.today(),
        "current_page": "Dashboard",
        "task_filter": None,
        "view_preference": None
    })

# Only display the company logo if the user is logged in
if st.session_state.logged_in:
    st.sidebar.image(str(logo_file_path), width=150)  # Adjust the width as needed

# Initialize database
conn = get_connection()
create_tables(conn)
insert_presets(conn)

# Authentication check
if not st.session_state.logged_in:
    st.markdown("""
        <style>
            [data-testid="collapsedControl"] { display: none; }
            .main > div { max-width: 800px; padding: 2rem; }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col2:
        st.title("AutoTask Login" if not st.session_state.show_register else "User Registration")

        if st.session_state.show_register:
            with st.form("register_form"):
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")  # Fixed password field
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
            
            if st.button("← Back to Login"):  # Moved outside form
                st.session_state.show_register = False
                st.rerun()
        else:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")  # Fixed password field

                if st.form_submit_button("Login"):
                    if login(username, password):
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("SELECT view_preference FROM users WHERE username=?", (username,))
                        result = c.fetchone()
                        
                        st.session_state.update({
                            "logged_in": True,
                            "username": username,
                            "view_preference": result[0] if result else "calendar",
                            "current_page": "Dashboard"
                        })
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
            
            if st.button("Create New Account"):  # Moved outside form
                st.session_state.show_register = True
                st.rerun()
    
    st.stop()

# Main app layout
with st.sidebar:
    st.title("AutoTask Navigation")
    
    # Original navigation buttons
    nav_mapping = {
        "📊 Dashboard": "Dashboard",
        "📝 Tasks": "Task Page1", 
        "🗂️ Task Groups": "Group Page",
        "⚠️ Overdue Tasks": "Overdue Tasks",
        "👤 User Profile": "User Profile"
    }
    
    for btn_text, page_name in nav_mapping.items():
        if st.button(btn_text, use_container_width=True):
            st.session_state.current_page = page_name

    # Admin time controls
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

# Page routing
check_notifications(st.session_state.mock_now)

if st.session_state.current_page == "Dashboard":
    dashboard.show_dashboard()
elif st.session_state.current_page == "Task Page1":
    task_page1.show_task_page1()
elif st.session_state.current_page == "Group Page":
    group_page.show_group_page()
elif st.session_state.current_page == "Overdue Tasks":
    overdue_tasks.show_overdue_tasks()
elif st.session_state.current_page == "User Profile":
    profile.show_profile()

conn.close()
