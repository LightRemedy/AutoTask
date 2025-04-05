#modules/dashboard.py
import streamlit as st
from core.database import get_connection
from utils.calendar import get_events_for_user
from streamlit_calendar import calendar as st_calendar
import datetime

def format_date(date_str: str) -> str:
    """Formats a date string into a readable format."""
    try:
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        return date.strftime("%d %b %Y")
    except ValueError:
        return date_str

def get_task_status(conn, task_id):
    """Determines the current status of a task (completed, offtrack, ontrack, or inactive)."""
    c = conn.cursor()
    mock_date = st.session_state.get("mock_now", datetime.date.today())
    
    c.execute("""
        SELECT t.completed, t.due_date, GROUP_CONCAT(tl.pre_task_id) as prereq_ids
        FROM tasks t
        LEFT JOIN task_link tl ON t.task_id = tl.task_id
        WHERE t.task_id = ?
        GROUP BY t.task_id
    """, (task_id,))
    result = c.fetchone()
    
    if not result:
        return "inactive"
        
    completed, due_date_str, prereq_ids = result
    
    if completed:
        return "completed"
    
    # Check if task is overdue
    due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
    if due_date < mock_date:
        return "offtrack"
    
    # Check prerequisites
    if prereq_ids:
        prereq_list = [int(x) for x in prereq_ids.split(',') if x]
        for prereq_id in prereq_list:
            prereq_status = get_task_status(conn, prereq_id)
            if prereq_status == "offtrack":
                return "offtrack"
    
    return "ontrack"

def show_dashboard():
    """Displays the main dashboard with task summary and calendar view."""
    st.title("📊 Dashboard")
    username = st.session_state.get("username")

    if not username:
        st.warning("Please log in to view the dashboard.")
        return

    conn = get_connection()
    c = conn.cursor()

    # Initialize view state in session if not present
    if "dashboard_view" not in st.session_state:
        st.session_state.dashboard_view = "main"
    
    # Back button for summary views
    if st.session_state.dashboard_view in ["pending", "completed"]:
        if st.button("← Back to Dashboard"):
            st.session_state.dashboard_view = "main"
            st.rerun()

    # Show appropriate view based on state
    if st.session_state.dashboard_view == "main":
        # --- Task Summary ---
        st.subheader("📊 Your Task Summary")
        col1, col2 = st.columns(2)

        # Get count of tasks in active groups (not completed and not templates)
        c.execute("""
            SELECT COUNT(DISTINCT t.task_id) 
            FROM tasks t
            JOIN groups g ON t.group_id = g.group_id
            WHERE t.created_by = ? 
            AND t.completed = 0
            AND g.isTemplate = 0
        """, (username,))
        pending = c.fetchone()[0]
        if col1.button(f"🔄 Pending Tasks: {pending}", use_container_width=True):
            st.session_state.dashboard_view = "pending"
            st.rerun()

        c.execute("SELECT COUNT(*) FROM tasks WHERE created_by=? AND completed=1", (username,))
        completed = c.fetchone()[0]
        if col2.button(f"✅ Completed Tasks: {completed}", use_container_width=True):
            st.session_state.dashboard_view = "completed"
            st.rerun()

        # --- View Preference ---
        show_calendar_section(conn, username)
    
    elif st.session_state.dashboard_view == "pending":
        display_task_summary(username, completed=False)
    
    elif st.session_state.dashboard_view == "completed":
        display_task_summary(username, completed=True)

    conn.close()

def show_calendar_section(conn, username):
    """Shows the calendar view section of the dashboard."""
    st.subheader("🗂️ View Preference")
    c = conn.cursor()
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
                       else "timeGridDay,timeGridWeek,dayGridMonth")
        },
        "initialView": ("dayGridMonth" if updated_pref == 'calendar' else "timeGridDay"),
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


def display_task_summary(username: str, completed: bool) -> None:
    """Shows a summary of tasks based on their completion status."""
    conn = get_connection()
    try:
        c = conn.cursor()
        
        # Get tasks with their group information, filtering for active groups only
        c.execute("""
            SELECT t.task_name, t.due_date, g.group_name, t.task_id
            FROM tasks t
            JOIN groups g ON t.group_id = g.group_id
            WHERE t.created_by = ? 
            AND t.completed = ?
            AND g.isTemplate = 0  -- Exclude template groups
            AND EXISTS (
                SELECT 1 
                FROM tasks t2 
                WHERE t2.group_id = g.group_id 
                AND t2.completed = 0
            )  -- Only include groups with active tasks
            ORDER BY t.due_date
        """, (username, int(completed)))
        
        tasks = c.fetchall()
        
        if not tasks:
            st.info("No active tasks found" if completed else "No pending active tasks")
            return
            
        # Display tasks grouped by their status
        st.subheader("📋 Active Task Summary")
        
        # Group tasks by their group name for better organization
        tasks_by_group = {}
        for task in tasks:
            task_name, due_date, group_name, task_id = task
            if group_name not in tasks_by_group:
                tasks_by_group[group_name] = []
            tasks_by_group[group_name].append((task_name, due_date, task_id))
        
        # Display tasks organized by group
        for group_name, group_tasks in tasks_by_group.items():
            st.markdown(f"**📦 {group_name}**")
            
            for task_name, due_date, task_id in group_tasks:
                status = get_task_status(conn, task_id)
                
                with st.container(border=True):
                    # Add colored status box using markdown
                    status_colors = {
                        "ontrack": "🟡 Ontrack",
                        "offtrack": "🔴 Offtrack",
                        "completed": "🟢 Completed"
                    }
                    status_text = status_colors.get(status.lower(), "⚪ Unknown")
                    
                    cols = st.columns([1, 2])
                    with cols[0]:
                        st.markdown(f"{status_text}")
                    with cols[1]:
                        st.markdown(f"**{task_name}**")
                        st.caption(f"📅 Due: {format_date(due_date)}")
                
    finally:
        conn.close()

