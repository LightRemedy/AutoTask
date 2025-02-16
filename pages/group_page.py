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

    # Handle modals
    if "edit_group" in st.session_state:
        edit_group_modal(st.session_state.edit_group)
    if "delete_group" in st.session_state:
        delete_confirmation_modal(st.session_state.delete_group)

    add_group_modal()

    st.subheader("📚 List of Task Groups")
    c.execute("SELECT group_id, group_name, color, remarks FROM groups WHERE created_by=?", (username,))
    groups = c.fetchall()

    if groups:
        for group in groups:
            group_id, group_name, color, remarks = group
            with st.container(border=True) as container:
                # Apply color to container border
                st.markdown(f"""
                    <style>
                        div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="element-container"]:first-child {{
                            border-left: 5px solid {color} !important;
                        }}
                    </style>
                """, unsafe_allow_html=True)
                
                cols = st.columns([6, 2, 2])
                with cols[0]:
                    status = get_group_status(conn, group_id)
                    st.markdown(f"**{group_name}** {get_status_badge(status)}", unsafe_allow_html=True)
                    completed, total = get_task_count(conn, group_id)
                    st.caption(f"Tasks: {completed}/{total} completed")
                
                with cols[1]:
                    if st.button("✏️ Edit", key=f"edit_{group_id}"):
                        st.session_state.edit_group = group
                        st.rerun()
                
                with cols[2]:
                    if st.button("🗑️ Delete", key=f"del_{group_id}"):
                        st.session_state.delete_group = group
                        st.rerun()

    else:
        st.info("No task groups found. Add one below!")

def delete_confirmation_modal(group_data):
    group_id, group_name, color, remarks = group_data
    
    @st.dialog(f"Delete {group_name}?", width="large")
    def confirmation_dialog():
        st.warning("Are you sure you want to delete this task group? All associated tasks will be removed!")
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("✅ Confirm Delete", type="primary", use_container_width=True):
                try:
                    username = st.session_state.get("username")
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("DELETE FROM tasks WHERE group_id=?", (group_id,))
                    c.execute("DELETE FROM groups WHERE group_id=? AND created_by=?", (group_id, username))
                    conn.commit()
                    st.success("Deleted successfully!")
                    st.session_state.pop("delete_group", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    conn.rollback()
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.pop("delete_group", None)
                st.rerun()
    
    confirmation_dialog()

def delete_group(group_id):
    # Remove any modal-related code from this function
    # Just keep the database operations
    username = st.session_state.get("username")
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM tasks WHERE group_id=?", (group_id,))
        c.execute("DELETE FROM groups WHERE group_id=? AND created_by=?", (group_id, username))
        conn.commit()
        st.success("Task group and associated tasks deleted successfully!")
    except Exception as e:
        st.error(f"Error deleting group: {str(e)}")
        conn.rollback()

# In pages/group_page.py
def edit_group_modal(group_data):
    group_id, old_name, color, remarks = group_data
    
    @st.dialog(f"Edit Task Group: {old_name}", width="large")
    def edit_dialog():
        with st.form(key=f"edit_form_{group_id}"):
            new_name = st.text_input("Group Name", value=old_name)
            new_color = st.color_picker("Color", value=color)
            new_remarks = st.text_area("Remarks", value=remarks)
            
            if st.form_submit_button("💾 Save Changes"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("""
                    UPDATE groups 
                    SET group_name=?, color=?, remarks=?
                    WHERE group_id=?
                """, (new_name, new_color, new_remarks, group_id))
                conn.commit()
                st.session_state.pop("edit_group", None)
                st.rerun()
        
        if st.button("❌ Cancel"):
            st.session_state.pop("edit_group", None)
            st.rerun()
    
    # Open the dialog
    edit_dialog()


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
        return "#8E44AD"

def get_task_count(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=1", (group_id,))
    completed_tasks = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    total_tasks = c.fetchone()[0]
    return completed_tasks, total_tasks
