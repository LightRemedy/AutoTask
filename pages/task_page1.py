import streamlit as st
import datetime
from db import get_connection

def show_task_page1():
    st.title("📝 Task Page")
    username = st.session_state.get("username")

    if not username:
        st.warning("Please log in to view tasks.")
        return

    conn = get_connection()
    c = conn.cursor()

    # --- Date Navigation ---
    st.subheader("📅 Task Date")
    today = datetime.date.today()
    if "task_date" not in st.session_state:
        st.session_state.task_date = today

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

    # --- View Selection ---
    st.subheader("👓 View Options")
    view_options = ["📅 Upcoming Tasks", "📅 All Tasks for Day"]
    selected_view = st.radio("Select View", view_options, horizontal=True)

    # --- Task Display ---
    st.subheader("📋 Task List")

    # Load tasks based on selected view
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

    # Display tasks
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

        # Load More Button (if applicable)
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

    # --- Add Task Button ---
    if st.button("➕ Add Task"):
        # TODO: Implement Add Task functionality
        st.info("Adding task (functionality to be implemented)")
