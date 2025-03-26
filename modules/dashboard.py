#modules/dashboard.py
import streamlit as st
from core.database import get_connection
from utils.calendar import get_events_for_user
from streamlit_calendar import calendar as st_calendar


def show_dashboard():
    st.title("📊 Dashboard")
    username = st.session_state.get("username")

    if not username:
        st.warning("Please log in to view the dashboard.")
        return

    conn = get_connection()
    c = conn.cursor()

    # --- Task Summary ---
    st.subheader("📊 Your Task Summary")
    col1, col2 = st.columns(2)

    c.execute("SELECT COUNT(*) FROM tasks WHERE created_by=? AND completed=0", (username,))
    pending = c.fetchone()[0]
    if col1.button(f"🔄 Pending Tasks: {pending}", use_container_width=True):
        st.session_state.task_filter = "pending"
        st.session_state.current_page = "Task Page"
        st.rerun()

    c.execute("SELECT COUNT(*) FROM tasks WHERE created_by=? AND completed=1", (username,))
    completed = c.fetchone()[0]
    if col2.button(f"✅ Completed Tasks: {completed}", use_container_width=True):
        st.session_state.task_filter = "completed"
        st.session_state.current_page = "Task Page"
        st.rerun()

    # --- View Preference ---
    st.subheader("🗂️ View Preference")
    c.execute("SELECT view_preference FROM users WHERE username=?", (username,))
    result = c.fetchone()
    view_preference = result[0] if result else 'calendar'

    new_view = st.radio(
        "Display Mode",
        ["📅 Calendar View", "📋 List View"],
        index=0 if view_preference == 'calendar' else 1,
        horizontal=True
    )

    updated_pref = 'calendar' if new_view == "📅 Calendar View" else 'list'
    if updated_pref != view_preference:
        c.execute("UPDATE users SET view_preference = ? WHERE username = ?", (updated_pref, username))
        conn.commit()
        st.rerun()

    # --- Calendar Configuration ---
    events = get_events_for_user(username)
    calendar_options = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": ("dayGridMonth,dayGridWeek,dayGridDay" if updated_pref == 'calendar'
                       else "listDay,listWeek,listMonth")
        },
        "initialView": ("dayGridMonth" if updated_pref == 'calendar' else "listMonth"),
        "navLinks": True,
        "selectable": True,
        "editable": False,
        "height": 600
    }

    try:
        calendar_component = st_calendar(
            events=events,
            options=calendar_options,
            key=f"calendar_{updated_pref}"
        )
    except Exception as e:
        st.error(f"Failed to load calendar view: {e}")

