import streamlit as st
import datetime
from db import get_connection
from streamlit_calendar import calendar as st_calendar

### Dashboard Module ,This module provides a dashboard interface for users to view their tasks and manage their viewing preferences (calendar/list view)

def show_dashboard():
    ### Main dashboard function that displays:
    # 1. User statistics (pending and completed tasks)
    # 2. View preference selection (calendar/list view)
    # 3. Interactive calendar/list component with task visualization
    
    st.title("📊 Dashboard")
    username = st.session_state.get("username")

    if not username:
        st.warning("Please log in to view the dashboard.")
        return

    conn = get_connection()
    c = conn.cursor()

    ### Statistics Section
    # Displays clickable buttons showing pending and completed task counts
    # Clicking these buttons navigates to the Task Page with appropriate filters
    st.subheader("📊 Statistics")
    col1, col2 = st.columns(2)

    # Total pending tasks
    c.execute("SELECT COUNT(*) FROM tasks WHERE created_by=? AND completed=0", (username,))
    pending_tasks = c.fetchone()[0]
    if col1.button(f"🔄 Pending Tasks: {pending_tasks}", use_container_width=True):
        st.session_state.task_filter = "pending"
        st.session_state.current_page = "Task Page"
        st.rerun()

    # Total completed tasks
    c.execute("SELECT COUNT(*) FROM tasks WHERE created_by=? AND completed=1", (username,))
    completed_tasks = c.fetchone()[0]
    if col2.button(f"✅ Completed Tasks: {completed_tasks}", use_container_width=True):
        st.session_state.task_filter = "completed"
        st.session_state.current_page = "Task Page"
        st.rerun()

    ### View Preference Section
    # Allows users to switch between calendar and list views
    # Saves the preference in the database for future sessions
    st.subheader("📅 Task View")
    c.execute("SELECT view_preference FROM users WHERE username=?", (username,))
    result = c.fetchone()
    view_preference = result[0] if result else 'calendar'

    new_view = st.radio("Display Mode", 
                      ["📅 Calendar View", "📋 List View"],
                      index=0 if view_preference == 'calendar' else 1,
                      horizontal=True)

    # Update view preference in database
    if new_view == "📅 Calendar View" and view_preference != 'calendar':
        c.execute("UPDATE users SET view_preference=? WHERE username=?", ('calendar', username))
        conn.commit()
        st.rerun()
    elif new_view == "📋 List View" and view_preference != 'list':
        c.execute("UPDATE users SET view_preference=? WHERE username=?", ('list', username))
        conn.commit()
        st.rerun()

    ### Calendar Configuration
    # Sets up the display options for both calendar and list views
    # Calendar view shows a monthly grid
    # List view shows tasks in a linear format
    events = get_events(username)
    
    if view_preference == 'calendar':
        calendar_options = {
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,dayGridWeek,dayGridDay"
            },
            "initialView": "dayGridMonth",
            "navLinks": True,
            "selectable": True,
            "editable": False,
            "height": 600
        }
    else:  # List view configuration
        calendar_options = {
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "listDay,listWeek,listMonth"
            },
            "initialView": "listMonth",
            "navLinks": True,
            "height": 600
        }

    ### Render Calendar Component
    # Attempts to render the calendar/list view with error handling
    try:
        calendar_component = st_calendar(
            events=events,
            options=calendar_options,
            key=f"calendar_{view_preference}"
        )
        st.write("")  # Force re-render
        st.write("")  # Second re-render trigger
    except Exception as e:
        st.error(f"Error rendering view: {str(e)}")

def get_events(username):
    ### Helper function to fetch and format task data for calendar display
    # Retrieves tasks from database and converts them to calendar events
    # Returns: List of event dictionaries with:
    #   - title: Task name
    #   - start: Due date
    #   - allDay: Always set to True
    #   - color: Green for completed tasks, orange for pending
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT task_name, due_date, completed 
        FROM tasks 
        WHERE created_by=?
    """, (username,))
    
    events = []
    for task in c.fetchall():
        events.append({
            "title": f"{'✅' if task[2] else '🔄'} {task[0]}",
            "start": task[1],
            "allDay": True,
            "color": "#4CAF50" if task[2] else "#FF5722"  # Green for completed, orange for pending
        })
    return events
