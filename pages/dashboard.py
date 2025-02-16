import streamlit as st
import datetime
from db import get_connection
import calendar
from streamlit_calendar import calendar as st_calendar

def show_dashboard():
    st.title("📊 Dashboard")
    username = st.session_state.get("username")

    if not username:
        st.warning("Please log in to view the dashboard.")
        return

    conn = get_connection()
    c = conn.cursor()

    # --- Stats Section ---
    st.subheader("📊 Statistics")
    col1, col2 = st.columns(2)

    # Total pending tasks
    c.execute("SELECT COUNT(*) FROM tasks WHERE created_by=? AND completed=0", (username,))
    pending_tasks = c.fetchone()[0]
    col1.metric("Pending Tasks", value=pending_tasks)

    # Total completed tasks
    c.execute("SELECT COUNT(*) FROM tasks WHERE created_by=? AND completed=1", (username,))
    completed_tasks = c.fetchone()[0]
    col2.metric("Completed Tasks", value=completed_tasks)

    # --- Calendar Section ---
    st.subheader("📅 Interactive Calendar")
    events = get_events(username)

    calendar_options = {
        "defaultView": "month",
        "initialDate": datetime.date.today().strftime("%Y-%m-%d"),
        "editable": False,
        "height": 600,
    }

    calendar = st_calendar(events=events, options=calendar_options)

def get_events(username):
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        """
        SELECT task_name, due_date FROM tasks 
        WHERE created_by=?
        """,
        (username,)
    )
    tasks = c.fetchall()

    events = []
    for task in tasks:
        task_name = task[0]
        due_date_str = task[1]
        due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()

        events.append({
            "start": due_date.isoformat(),
            "end": (due_date + datetime.timedelta(days=1)).isoformat(), #to show whole day on calendar
            "title": task_name,
        })
    return events
