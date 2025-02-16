import streamlit as st
from db import get_connection

def show_group_page():
    st.title("📦 Task Groups")
    username = st.session_state.get("username")

    if not username:
        st.warning("Please log in to view task groups.")
        return

    conn = get_connection()
    c = conn.cursor()

    # --- Add Group Modal ---
    add_group_modal()

    # --- List Groups ---
    st.subheader("📚 List of Task Groups")
    c.execute("SELECT group_id, group_name, color, remarks FROM groups WHERE created_by=?", (username,))
    groups = c.fetchall()

    if groups:
        for group_id, group_name, color, remarks in groups:
            group_color = color  # Use existing color from database
            with st.container(border=True):
                col1, col2 = st.columns([0.02, 0.98])  # Adjust the column ratios as needed
                with col1:
                    st.markdown(f'<div style="width: 3px; background-color: {group_color}; height: 100%;"></div>', unsafe_allow_html=True)  # Colored line

                with col2:
                    # Determine Group Status and Badge
                    status = get_group_status(conn, group_id)
                    badge = get_status_badge(status)
                    st.markdown(f"**{group_name} {badge}**", unsafe_allow_html=True)

                    # Task count display
                    task_count = get_task_count(conn, group_id)
                    st.caption(f"{task_count[0]}/{task_count[1]} tasks completed")

                    col_edit, col_delete = st.columns([1, 1])

                    with col_edit:
                        edit_group_modal(group_id, group_name, color, remarks)  # Opens popup modal

                    with col_delete:
                        if st.button("🗑️ Delete", key=f"delete_{group_id}"):
                            st.session_state[f"confirm_delete_{group_id}"] = True #must open confirm popup before deleting

                            if f"confirm_delete_{group_id}" in st.session_state and st.session_state[f"confirm_delete_{group_id}"]:
                                if st.warning(f"Are you sure you want to delete {group_name}?", icon="⚠️"):
                                    if st.button("Confirm Delete", key=f"confirm_delete_confirmed{group_id}"):
                                        delete_group(group_id)
                                        del st.session_state[f"confirm_delete_{group_id}"]
                                        st.rerun() #force refresh and prevent from stuck

    else:
        st.info("No task groups found. Add one below!")

def add_group_modal():
    add_group = st.expander("➕ Add New Task Group")
    with add_group:
        with st.form("add_group_form"):
            group_name = st.text_input("Task Group Name", max_chars=50)
            color = st.color_picker("Color", value="#8E44AD")  # Color picker added back
            remarks = st.text_area("Remarks", max_chars=200)
            submitted = st.form_submit_button("Create Task Group")

            if submitted:
                username = st.session_state.get("username")
                conn = get_connection()
                c = conn.cursor()
                c.execute(
                    "INSERT INTO groups (group_name, created_by, color, remarks) VALUES (?,?,?,?)",
                    (group_name, username, color, remarks),
                )
                conn.commit()
                st.success(f"Task Group '{group_name}' created!")
                st.rerun()

def edit_group_modal(group_id, group_name, color, remarks):
    if f"modal_open_{group_id}" not in st.session_state:
        st.session_state[f"modal_open_{group_id}"] = False

    def open_modal():
        st.session_state[f"modal_open_{group_id}"] = True

    def close_modal():
        st.session_state[f"modal_open_{group_id}"] = False

    st.button("✏️ Edit", on_click=open_modal, key=f"edit_button_{group_id}")

    if st.session_state[f"modal_open_{group_id}"]:
        with st.container():  # Style this container as desired
            st.subheader(f"Edit Task Group: {group_name}")
            new_group_name = st.text_input("New Task Group Name", value=group_name)
            new_color = st.color_picker("Color", value=color)
            new_remarks = st.text_area("Remarks", value=remarks)

            col_save, col_cancel = st.columns([1, 1])
            with col_save:
                if st.button("Save", key=f"save_edit_{group_id}"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute(
                        "UPDATE groups SET group_name=?, color=?, remarks=? WHERE group_id=?",
                        (new_group_name, new_color, new_remarks, group_id),
                    )
                    conn.commit()
                    close_modal()
                    st.rerun() #rerun entire script
            with col_cancel:
                if st.button("Cancel", on_click=close_modal, key=f"cancel_edit_{group_id}"):
                    pass  # Close the modal

def delete_group(group_id):
    username = st.session_state.get("username")
    conn = get_connection()
    c = conn.cursor()

    # Delete tasks associated with the group first (optional, but recommended)
    c.execute("DELETE FROM tasks WHERE group_id=?", (group_id,))
    conn.commit()

    # Then delete the group
    c.execute("DELETE FROM groups WHERE group_id=? AND created_by=?", (group_id, username))
    conn.commit()
    st.success(f"Task Group deleted!")

def get_group_status(conn, group_id):
    c = conn.cursor()
    # Check for overdue tasks
    c.execute(
        """
        SELECT COUNT(*) FROM tasks 
        WHERE group_id=? AND completed=0 AND due_date < date('now')
        """,
        (group_id,)
    )
    overdue_tasks = c.fetchone()[0]

    if overdue_tasks > 0:
        return "offtrack"

    # Check for pending tasks
    c.execute(
        """
        SELECT COUNT(*) FROM tasks 
        WHERE group_id=? AND completed=0
        """,
        (group_id,)
    )
    pending_tasks = c.fetchone()[0]

    if pending_tasks > 0:
        return "ontrack"

    # Check if all tasks are completed
    c.execute(
        """
        SELECT COUNT(*) FROM tasks 
        WHERE group_id=?
        """,
        (group_id,)
    )
    total_tasks = c.fetchone()[0]

    if total_tasks == 0:
        return "inactive"
    else:
        return "completed"

def get_status_badge(status):
    style = """
        border-radius: 9px;
        padding-left: 7px;
        padding-right: 7px;
        font-size: 13px;
        color: white;
    """
    if status == "offtrack":
        return f'<span class="badge" style="{style} background-color: red;">Off Track</span>'
    elif status == "ontrack":
        return f'<span class="badge" style="{style} background-color: orange;">On Track</span>'  # Changed to orange
    elif status == "completed":
        return f'<span class="badge" style="{style} background-color: green;">Completed</span>'
    else:
        return f'<span class="badge" style="{style} background-color: gray;">Inactive</span>'

def get_group_color(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT color FROM groups WHERE group_id=?", (group_id,))
    result = c.fetchone()
    if result:
        return result[0]
    else:
        return "#8E44AD" # Default color

def get_task_count(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=1", (group_id,))
    completed_tasks = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    total_tasks = c.fetchone()[0]
    return completed_tasks, total_tasks
