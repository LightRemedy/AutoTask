import streamlit as st
import datetime
from pathlib import Path

from core.database import get_connection, create_tables, insert_presets
from core.notification import check_notifications
from modules import dashboard, group_page, login, tasks, overdue, profile,group_details

# App Configuration
st.set_page_config(
    page_title="AutoTask",
    page_icon="📋",
    layout="centered"
)

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "icon.png"

# Session Defaults
if "logged_in" not in st.session_state:
    st.session_state.update({
        "logged_in": False,
        "username": None,
        "show_register": False,
        "mock_now": datetime.date.today(),
        "current_page": "Dashboard",
        "task_filter": None,
        "view_preference": None
    })

# Database Setup
conn = get_connection()
create_tables(conn)
insert_presets(conn)

# Logo
if st.session_state.logged_in:
    st.sidebar.image(str(LOGO_PATH), width=240)

# Auth Flow
if not st.session_state.logged_in:
    login.show_login_page()
    st.stop()

# Navigation Menu
with st.sidebar:
    st.title("AutoTask Navigation")
    nav_map = {
        "📊 Dashboard": "Dashboard",
        "📝 Tasks": "Task Page",
        "🗂️ Task Groups": "Group Page",
        "⚠️ Overdue Tasks": "Overdue Tasks",
        "👤 User Profile": "User Profile"
    }
    for label, target in nav_map.items():
        if st.button(label, use_container_width=True):
            st.session_state.current_page = target

    if st.session_state.username == "admin":
        st.divider()
        st.header("⏰ Debug Controls")
        new_date = st.date_input("Mock Date", st.session_state.mock_now)
        if new_date != st.session_state.mock_now:
            st.session_state.mock_now = new_date
            st.rerun()
        if st.button("⏩ Advance 1 Day"):
            st.session_state.mock_now += datetime.timedelta(days=1)
            st.rerun()

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

# Notifications
check_notifications(st.session_state.mock_now)

# Page Routing
page = st.session_state.current_page
if page == "Dashboard":
    dashboard.show_dashboard()
elif page == "Task Page":
    tasks.show_task_page()
elif page == "Group Page":
    group_page.show_group_page()
elif page == "Overdue Tasks":
    overdue.show_overdue_tasks()
elif page == "User Profile":
    profile.show_profile()
elif page == "Group Details":
    group_details.show_group_details()

conn.close()