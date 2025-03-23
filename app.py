import streamlit as st
import datetime
from db import get_connection, create_tables, insert_presets
from auth import login, register
from tasks import check_notifications
from pages import dashboard, profile, overdue_tasks, task_page, group_page, group_details, login_page
from pathlib import Path

# ========== FIRST AND ONLY set_page_config ==========
st.set_page_config(
    page_title="AutoTask",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="auto"
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
    st.sidebar.image(str(logo_file_path), width=250)  # Adjust the width as needed

# Initialize database
conn = get_connection()
create_tables(conn)
insert_presets(conn)

# Authentication check
if not st.session_state.logged_in:
    login_page.show_login_page()
    st.stop()

# Main app layout
with st.sidebar:
    st.title("AutoTask Navigation")
    
    # Original navigation buttons
    nav_mapping = {
        "📊 Dashboard": "Dashboard",
        "📝 Tasks": "Task Page", 
        "🗂️ Task Groups": "Group Page",
        "⚠️ Overdue Tasks": "Overdue Tasks",
        "👤 User Profile": "User Profile"
    }
    
    for btn_text, page_name in nav_mapping.items():
        if st.button(btn_text, use_container_width=True):
            st.session_state.current_page = page_name

    # Admin time controls
    if st.session_state.username == "admin" :
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
elif st.session_state.current_page == "Task Page":
    task_page.show_task_page()
elif st.session_state.current_page == "Group Page":
    group_page.show_group_page()
elif st.session_state.current_page == "Overdue Tasks":
    overdue_tasks.show_overdue_tasks()
elif st.session_state.current_page == "User Profile":
    profile.show_profile()
elif st.session_state.current_page == "Group Details":
    group_details.show()

conn.close()
