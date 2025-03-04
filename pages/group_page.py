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

    # Handle feedback messages
    if "group_feedback" in st.session_state:
        if st.session_state.group_feedback["type"] == "success":
            st.success(st.session_state.group_feedback["message"])
        else:
            st.error(st.session_state.group_feedback["message"])
        del st.session_state.group_feedback

    # Handle modals
    if "edit_group" in st.session_state:
        edit_group_modal(st.session_state.edit_group)
    if "delete_group" in st.session_state:
        delete_confirmation_modal(st.session_state.delete_group)

    # Add Group Section
    with st.expander("➕ Add New Task Group", expanded=False):
        with st.form("add_group_form"):
            group_name = st.text_input("Group Name", max_chars=50)
            color = st.color_picker("Color", value="#8E44AD")
            remarks = st.text_area("Remarks", max_chars=200)
            is_template = st.checkbox("Mark as Template Group")
            
            submitted = st.form_submit_button("Create Task Group")
            
            if submitted:
                try:
                    c.execute(
                        "INSERT INTO groups (group_name, created_by, color, remarks, isTemplate) VALUES (?,?,?,?,?)",
                        (group_name, username, color, remarks, 1 if is_template else 0),
                    )
                    conn.commit()
                    st.session_state.group_feedback = {
                        "type": "success",
                        "message": f"Group '{group_name}' created successfully!"
                    }
                    st.rerun()
                except Exception as e:
                    st.session_state.group_feedback = {
                        "type": "error",
                        "message": f"Error creating group: {str(e)}"
                    }
                    st.rerun()

    # List of Groups
    st.subheader("📚 List of Task Groups")
    c.execute("SELECT group_id, group_name, color, remarks, isTemplate FROM groups WHERE created_by=?", (username,))
    groups = c.fetchall()

    if groups:
        for group in groups:
            group_id, group_name, color, remarks, is_template = group
            with st.container(border=True):
                template_badge = "📁 " if is_template else ""
                st.markdown(f"""
                    <style>
                        .floating-circle-{group_id} {{
                            position: absolute;
                            top: -5px;
                            left: -5px;
                            width: 15px;
                            height: 15px;
                            border-radius: 50%;
                            background-color: {color};
                        }}
                        .group-content {{
                            position: relative;
                            padding-left: 20px;
                            display: flex;
                            align-items: center;
                            gap: 1rem;
                        }}
                    </style>
                    <div class="floating-circle-{group_id}"></div>
                    <div class="group-content">
                """, unsafe_allow_html=True)

                cols = st.columns([4, 2, 2, 2])
                with cols[0]:
                    status = get_group_status(conn, group_id)
                    st.markdown(f"**{template_badge}{group_name}** {get_status_badge(status)}", unsafe_allow_html=True)
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
                with cols[3]:
                    if st.button("👁️ View", key=f"view_{group_id}"):
                        st.session_state.current_page = "Group Details"
                        st.session_state.current_view_group = group_id
                        st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No task groups found. Add one using the form above!")
    
    conn.close()

def delete_confirmation_modal(group_data):
    group_id, group_name, color, remarks, _ = group_data
    
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
                finally:
                    conn.close()
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.pop("delete_group", None)
                st.rerun()
    
    confirmation_dialog()

def edit_group_modal(group_data):
    group_id, old_name, color, remarks, is_template = group_data
    
    @st.dialog(f"Edit Task Group: {old_name}", width="large")
    def edit_dialog():
        conn = get_connection()
        try:
            with st.form(key=f"edit_form_{group_id}"):
                new_name = st.text_input("Group Name", value=old_name)
                new_color = st.color_picker("Color", value=color)
                new_remarks = st.text_area("Remarks", value=remarks)
                new_is_template = st.checkbox("Template Group", value=bool(is_template))
                
                if st.form_submit_button("💾 Save Changes"):
                    c = conn.cursor()
                    c.execute("""
                        UPDATE groups 
                        SET group_name=?, color=?, remarks=?, isTemplate=?
                        WHERE group_id=?
                    """, (new_name, new_color, new_remarks, 
                        1 if new_is_template else 0, group_id))
                    conn.commit()
                    st.session_state.pop("edit_group", None)
                    st.rerun()
            
            if st.button("❌ Cancel"):
                st.session_state.pop("edit_group", None)
                st.rerun()
        finally:
            conn.close()
    
    edit_dialog()

def get_group_status(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=0 AND due_date < date('now')", (group_id,))
    overdue_tasks = c.fetchone()[0]

    if overdue_tasks > 0:
        return "offtrack"

    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=0", (group_id,))
    pending_tasks = c.fetchone()[0]

    if pending_tasks > 0:
        return "ontrack"

    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    total_tasks = c.fetchone()[0]

    if total_tasks == 0:
        return "inactive"
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
        return f'<span style="{style} background-color: red;">Off Track</span>'
    elif status == "ontrack":
        return f'<span style="{style} background-color: orange;">On Track</span>'
    elif status == "completed":
        return f'<span style="{style} background-color: green;">Completed</span>'
    return f'<span style="{style} background-color: gray;">Inactive</span>'

def get_task_count(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=1", (group_id,))
    completed = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    total = c.fetchone()[0]
    return completed, total
