import streamlit as st
from db import get_connection

def show_task_page1():
    st.title("📝 Task Page")
    username = st.session_state.get("username")

    if not username:
        st.warning("Please log in to view tasks.")
        return

    conn = get_connection()
    c = conn.cursor()

    # --- Group Management ---
    st.subheader("➕ Create New Group")
    new_group_name = st.text_input("Group Name")
    if st.button("Create Group"):
        c.execute("INSERT INTO groups (group_name, created_by) VALUES (?,?)", (new_group_name, username))
        conn.commit()
        st.success(f"Group '{new_group_name}' created!")

    # --- Task Management ---
    st.subheader("➕ Add Task")
    c.execute("SELECT group_id, group_name FROM groups WHERE created_by=?", (username,))
    groups = c.fetchall()
    group_options = {name: gid for gid, name in groups}
    selected_group = st.selectbox("Choose Group", list(group_options.keys()))

    task_name = st.text_input("Task Name")
    notification_days = st.number_input("Notification Days Before Due", min_value=0, max_value=365, value=7)
    due_date = st.date_input("Due Date")

    if st.button("Add Task"):
        c.execute(
            "INSERT INTO tasks (group_id, task_name, notification_days, due_date, created_by) VALUES (?,?,?,?,?)",
            (group_options[selected_group], task_name, notification_days, due_date.strftime('%Y-%m-%d'), username)
        )
        conn.commit()
        st.success(f"Task '{task_name}' added to '{selected_group}'!")

    # --- Display Tasks ---
    st.subheader("📋 Task List")
    c.execute(
        """
        SELECT task_id, group_id, task_name, due_date, completed FROM tasks 
        WHERE created_by=?
        """,
        (username,)
    )
    tasks = c.fetchall()

    for task in tasks:
        task_id, group_id, task_name, due_date, completed = task
        col1, col2, col3 = st.columns([6, 2, 2])
        with col1:
            if completed:
                st.markdown(f"~~{task_name}~~")
            else:
                st.write(task_name)
            st.caption("Due: " + due_date)
        with col2:
            if not completed:
                if st.button("Complete", key=f"complete_{task_id}"):
                    c.execute("UPDATE tasks SET completed=1 WHERE task_id=?", (task_id,))
                    conn.commit()
                    st.rerun()
            else:
                st.write("Done")
        with col3:
            if st.button("Send Reminder", key=f"reminder_{task_id}"):
                st.info(f"Reminder sent for task: {task_name}")
