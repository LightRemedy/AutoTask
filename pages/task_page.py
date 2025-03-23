import streamlit as st
import datetime
from db import get_connection

### Task Page Module
# This module handles the task list view and management, providing:
# * Date-based task navigation
# * Multiple view options for tasks
# * Task completion and reminder functionality
# * Pagination for upcoming tasks

def show_task_page():
    ### Main Task Display Function
    # Shows tasks based on date selection and view preference
    
    st.title("📝 Task Page")
    username = st.session_state.get("username")

    ### Authentication Check
    # Ensures user is logged in before showing tasks
    if not username:
        st.warning("Please log in to view tasks.")
        return

    conn = get_connection()
    c = conn.cursor()

    ### Date Navigation Section
    # Allows users to move between dates
    # Maintains selected date in session state
    st.subheader("📅 Task Date")
    today = datetime.date.today()
    if "task_date" not in st.session_state:
        st.session_state.task_date = today

    ### Date Navigation Controls
    # Previous day, current date display, next day buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⏪ Previous Day"):
            st.session_state.task_date -= datetime.timedelta(days=1)
            st.rerun()
    with col2:
        st.write(st.session_state.task_date.strftime("%Y-%m-%d"))
    with col3:
        if st.button("⏩ Next Day"):
            st.session_state.task_date += datetime.timedelta(days=1)
            st.rerun()

    ### View Selection Section
    # Allows switching between upcoming tasks and daily view
    st.subheader("👓 View Options")
    view_options = ["📅 Upcoming Tasks", "📅 All Tasks for Day"]
    selected_view = st.radio("Select View", view_options, horizontal=True)

    ### Task List Section
    st.subheader("📋 Task List")

    ### Task Query Logic
    # Fetches tasks based on selected view:
    # - Upcoming Tasks: Next 5 tasks from selected date
    # - All Tasks: All tasks for selected date
    task_date_str = st.session_state.task_date.strftime("%Y-%m-%d")
    if selected_view == "📅 Upcoming Tasks":
        c.execute(
            """
            SELECT task_id, group_id, task_name, due_date, completed FROM tasks
            WHERE created_by=? AND due_date >= ?
            ORDER BY due_date ASC
            LIMIT 5
            """,
            (username, task_date_str)
        )
    else:  # All Tasks for Day
        c.execute(
            """
            SELECT task_id, group_id, task_name, due_date, completed FROM tasks
            WHERE created_by=? AND due_date = ?
            """,
            (username, task_date_str)
        )
    tasks = c.fetchall()

    ### Task Display Loop
    # Shows each task with:
    # * Task name (strikethrough if completed)
    # * Due date
    # * Complete button (if not completed)
    # * Reminder button
    if tasks:
        for task in tasks:
            task_id, group_id, task_name, due_date, completed = task
            col1, col2, col3 = st.columns([6, 2, 2])
            with col1:
                if completed:
                    st.markdown(f"~~{task_name}~~")
                else:
                    st.write(task_name)
                st.caption(f"Due: {due_date}")
            with col2:
                if not completed:
                    if st.button("✅ Complete", key=f"complete_{task_id}"):
                        c.execute("UPDATE tasks SET completed=1 WHERE task_id=?", (task_id,))
                        conn.commit()
                        st.rerun()
                else:
                    st.write("Done")
            with col3:
                if st.button("⏰ Reminder", key=f"reminder_{task_id}"):
                    st.info(f"Reminder sent for task: {task_name}")

        ### Pagination Section
        # Shows 'Load More' button for upcoming tasks view
        # when more tasks are available
        if selected_view == "📅 Upcoming Tasks":
            c.execute(
                """
                SELECT COUNT(*) FROM tasks
                WHERE created_by=? AND due_date >= ?
                """,
                (username, task_date_str)
            )
            total_upcoming_tasks = c.fetchone()[0]
            if total_upcoming_tasks > len(tasks):
                if st.button("Load More"):
                    # TODO: Implement proper pagination logic
                    st.info("Loading more tasks (functionality to be implemented)")

    else:
        st.info("No tasks found for the selected date.")

    ### Task Creation Section
    # Button to add new tasks (placeholder for future implementation)
    if st.button("➕ Add Task"):
        # TODO: Implement Add Task functionality
        st.info("Adding task (functionality to be implemented)")
