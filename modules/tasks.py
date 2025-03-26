#modules/tasks.py
import streamlit as st
import datetime
from core.database import get_connection


def show_task_page():
    st.title("📝 Task Page")
    username = st.session_state.get("username")

    if not username:
        st.warning("Please log in to view your tasks.")
        return

    conn = get_connection()
    c = conn.cursor()

    today = datetime.date.today()
    if "task_date" not in st.session_state:
        st.session_state.task_date = today

    st.subheader("📅 Select Date")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⏪ Previous Day"):
            st.session_state.task_date -= datetime.timedelta(days=1)
            st.rerun()
    with col2:
        st.write(st.session_state.task_date.strftime("%A, %d %B %Y"))
    with col3:
        if st.button("⏩ Next Day"):
            st.session_state.task_date += datetime.timedelta(days=1)
            st.rerun()

    st.subheader("👓 View Mode")
    view_type = st.radio("Show:", ["📅 Upcoming Tasks", "📋 Tasks for Selected Day"], horizontal=True)

    selected_date = st.session_state.task_date.strftime("%Y-%m-%d")

    if view_type == "📅 Upcoming Tasks":
        c.execute("""
            SELECT task_id, group_id, task_name, due_date, completed
            FROM tasks
            WHERE created_by = ? AND due_date >= ?
            ORDER BY due_date ASC LIMIT 5
        """, (username, selected_date))
    else:
        c.execute("""
            SELECT task_id, group_id, task_name, due_date, completed
            FROM tasks
            WHERE created_by = ? AND due_date = ?
        """, (username, selected_date))

    tasks = c.fetchall()

    st.subheader("📋 Your Tasks")
    if tasks:
        for task_id, group_id, name, due_date, completed in tasks:
            col1, col2, col3 = st.columns([6, 2, 2])
            with col1:
                st.markdown(f"**{'~~' + name + '~~' if completed else name}**")
                st.caption(f"Due: {due_date}")

            with col2:
                if not completed:
                    if st.button("✅ Complete", key=f"done_{task_id}"):
                        c.execute("UPDATE tasks SET completed = 1 WHERE task_id = ?", (task_id,))
                        conn.commit()
                        st.rerun()
                else:
                    st.write("✅ Done")

            with col3:
                if st.button("⏰ Reminder", key=f"reminder_{task_id}"):
                    st.success(f"Reminder set for task: {name}")

        if view_type == "📅 Upcoming Tasks":
            c.execute("SELECT COUNT(*) FROM tasks WHERE created_by = ? AND due_date >= ?", (username, selected_date))
            total = c.fetchone()[0]
            if total > len(tasks):
                if st.button("Load More"):
                    st.info("Pagination not implemented yet.")
    else:
        st.info("No tasks found for this selection.")

    if st.button("➕ Add Task"):
        st.info("Task creation coming soon.")
        