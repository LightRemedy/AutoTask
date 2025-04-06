from typing import List, Tuple, Optional, Dict
import streamlit as st
from core.database import get_connection
import datetime
from modules.task_detail import show_group_details
from modules.dashboard import get_task_status

### Group Page Module
### This module manages the main group listing page, providing functionality for:
# - Creating new task groups
# - Importing groups from templates
# - Managing existing groups (view, edit, delete)
# - Displaying group status and progress

class TaskGroup:
    """Represents a task group with its properties and operations."""
    
    def __init__(self, group_id: int, name: str, color: str, remarks: str, is_template: bool):
        self.group_id = group_id
        self.name = name
        self.color = color
        self.remarks = remarks
        self.is_template = is_template

    @staticmethod
    def create_from_template(
        conn,
        template_id: int,
        new_group_id: int,
        start_date: datetime.date,
        username: str,
        enable_notifications: bool
    ) -> None:
        """
        Creates tasks in a new group based on a template.
        """
        c = conn.cursor()
        try:
            # Get template tasks
            c.execute("""
                SELECT task_id, task_name, description, notification_days, 
                       due_date, recurrence_pattern, recurrence_end_date,
                       priority, estimated_duration
                FROM tasks 
                WHERE group_id=?
                ORDER BY due_date
            """, (template_id,))
            template_tasks = c.fetchall()

            if not template_tasks:
                return

            # Calculate date offset from first task
            first_task_date = datetime.datetime.strptime(template_tasks[0][4], "%Y-%m-%d").date()
            date_offset = (start_date - first_task_date).days

            # Copy tasks with new dates
            task_id_map = {}  # Map old task IDs to new ones
            for task in template_tasks:
                old_task_id, name, desc, notif_days, due_date_str, rec_pattern, rec_end, priority, duration = task
                
                # Calculate new due date based on individual task dates
                task_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
                new_due_date = task_date + datetime.timedelta(days=date_offset)
                
                c.execute("""
                    INSERT INTO tasks (
                        group_id, task_name, description, notification_days,
                        due_date, recurrence_pattern, recurrence_end_date,
                        priority, estimated_duration, created_by, telegram_notify
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    new_group_id, name, desc, notif_days,
                    new_due_date.isoformat(), rec_pattern, rec_end,
                    priority, duration, username, enable_notifications
                ))
                task_id_map[old_task_id] = c.lastrowid

            # Copy task dependencies
            TaskGroup._copy_task_dependencies(conn, task_id_map)

        except Exception as e:
            raise Exception(f"Error copying template tasks: {str(e)}")

    @staticmethod
    def _copy_task_dependencies(conn, task_id_map: Dict[int, int]) -> None:
        """
        Copies task dependencies from template to new group.
        """
        if not task_id_map:
            return
            
        c = conn.cursor()
        try:
            task_ids = list(task_id_map.keys())
            placeholders = ','.join(['?' for _ in task_ids])
            c.execute(f"""
                SELECT task_id, pre_task_id, link_type 
                FROM task_link 
                WHERE task_id IN ({placeholders})
                ORDER BY task_id
            """, task_ids)
            
            for task_id, pre_task_id, link_type in c.fetchall():
                if task_id in task_id_map and pre_task_id in task_id_map:
                    c.execute("""
                        INSERT INTO task_link (task_id, pre_task_id, link_type)
                        VALUES (?,?,?)
                    """, (task_id_map[task_id], task_id_map[pre_task_id], link_type))
        except Exception as e:
            raise Exception(f"Error copying task dependencies: {str(e)}")

def show_group_page() -> None:
    """Main function to display and manage tasks."""
    st.title("🗒 Tasks")
    username = st.session_state.get("username")
    
    # Handle modals first
    handle_modals()

    # Show group creation form
    with st.expander("➕ Add New Task Group", expanded=False):
        create_group_form(username)

    # List existing groups
    display_group_list(username)

def create_group_form(username: str) -> None:
    """
    Displays and handles the group creation form.
    """
    conn = get_connection()
    try:
        with st.form("add_group_form", clear_on_submit=True):
            # Basic group information
            group_name = st.text_input("Group Name*", max_chars=50)
            color = st.color_picker("Color", "#4CAF50")
            remarks = st.text_area("Remarks", max_chars=200)
            
            # Template selection
            templates = get_templates(conn)
            template_options = [("0", "Create Empty Group")] + [(str(t[0]), t[1]) for t in templates]
            selected_template_id = st.selectbox(
                "Create from Template",
                options=[t[0] for t in template_options],
                format_func=lambda x: next(t[1] for t in template_options if t[0] == x),
                key="template_selector"
            )
            
            # Show template description if available
            if selected_template_id != "0":
                template = next((t for t in templates if str(t[0]) == selected_template_id), None)
                if template and template[2]:
                    st.info(template[2])
            
            # Common fields for all groups
            new_start_date = st.date_input(
                "Start Date*",
                min_value=datetime.date.today()
            )
            enable_notifications = st.checkbox("Enable Telegram Notifications", value=True)

            # Form submission
            if st.form_submit_button("Create Group"):
                create_group(
                    conn=conn,
                    username=username,
                    group_name=group_name,
                    color=color,
                    remarks=remarks,
                    start_date=new_start_date,
                    selected_template_id=selected_template_id,
                    enable_notifications=enable_notifications
                )
    finally:
        conn.close()

def get_templates(conn) -> List[Tuple]:
    """Fetches all available task templates from the database."""
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT g.group_id, g.group_name, g.remarks 
        FROM groups g
        WHERE g.isTemplate=1
        GROUP BY g.group_name
        ORDER BY g.group_name
    """)
    return c.fetchall()

def create_group(
    conn,
    username: str,
    group_name: str,
    color: str,
    remarks: str,
    start_date: datetime.date,
    selected_template_id: str,
    enable_notifications: bool
) -> None:
    """Creates a new task group, optionally based on a template."""
    if not group_name.strip():
        st.error("Group name is required")
        return

    try:
        conn.execute("BEGIN TRANSACTION")
        c = conn.cursor()
        
        # Create new group
        c.execute("""
            INSERT INTO groups (group_name, color, remarks, created_by, isTemplate, start_date)
            VALUES (?,?,?,?,?,?)
        """, (group_name, color, remarks, username, 0, start_date.isoformat()))
        new_group_id = c.lastrowid

        # Copy template if selected
        if selected_template_id != "0":
            TaskGroup.create_from_template(
                conn=conn,
                template_id=int(selected_template_id),
                new_group_id=new_group_id,
                start_date=start_date,
                username=username,
                enable_notifications=enable_notifications
            )

        conn.commit()
        st.success(f"Group '{group_name}' created successfully!")
        st.rerun()
        
    except Exception as e:
        conn.rollback()
        st.error(f"Error creating group: {str(e)}")

def display_group_list(username: str) -> None:
    """Shows a list of all task groups for the current user."""
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT group_id, group_name, color, remarks, isTemplate 
            FROM groups 
            WHERE created_by=? AND isTemplate=0
            ORDER BY group_name
        """, (username,))
        groups = c.fetchall()

        st.subheader("📚 Task Groups")
        if not groups:
            st.info("No recurring tasks yet. Create one to get started!")
        else:
            for group_data in groups:
                group = TaskGroup(*group_data)
                display_group(group, conn)
    finally:
        conn.close()

def display_group(group: TaskGroup, conn) -> None:
    """
    Displays a single group with its progress and actions.
    """
    with st.container(border=True):
        cols = st.columns([4, 1, 1, 1])
        
        with cols[0]:
            st.markdown(f"**{group.name}**")
            if group.remarks:
                st.caption(group.remarks)
            
            # Get completion stats and status
            completed, total = get_task_count(conn, group.group_id)
            status = get_group_status(conn, group.group_id)
            
            # Show progress and status
            if total > 0:
                st.progress(completed/total, text=f"Progress: {completed}/{total} tasks")
                st.markdown(get_status_badge(status), unsafe_allow_html=True)
            else:
                st.info("No tasks in this group yet")
        
        with cols[1]:
            if st.button("👁️ View", key=f"view_{group.group_id}", use_container_width=True):
                st.session_state.current_view_group = group.group_id
                st.session_state.current_page = "Group Details"
                st.rerun()
        
        with cols[2]:
            if st.button("✏️ Edit", key=f"edit_{group.group_id}", use_container_width=True):
                st.session_state.edit_group = (
                    group.group_id, group.name, group.color, 
                    group.remarks, group.is_template
                )
                st.rerun()
        
        with cols[3]:
            if st.button("🗑️ Delete", key=f"del_{group.group_id}", use_container_width=True):
                st.session_state.delete_group = group.group_id
                st.rerun()

def get_task_count(conn, group_id: int) -> Tuple[int, int]:
    """
    Calculates completion statistics for a group.
    """
    c = conn.cursor()
    
    # Get completed tasks count
    c.execute("""
        SELECT COUNT(*) 
        FROM tasks 
        WHERE group_id=? AND completed=1
    """, (group_id,))
    completed = c.fetchone()[0]
    
    # Get total tasks count
    c.execute("""
        SELECT COUNT(*) 
        FROM tasks 
        WHERE group_id=?
    """, (group_id,))
    total = c.fetchone()[0]
    
    return completed, total

def get_group_status(conn, group_id: int) -> str:
    """Determines the current status of a task group (completed, offtrack, ontrack, or inactive)."""
    c = conn.cursor()
    current_date = st.session_state.get('mock_now', datetime.datetime.now().date())
    
    # Check if any tasks are overdue (past due date)
    c.execute("""
        SELECT COUNT(*) 
        FROM tasks 
        WHERE group_id = ? 
        AND completed = 0 
        AND due_date < ?
    """, (group_id, current_date.strftime("%Y-%m-%d")))
    
    if c.fetchone()[0] > 0:
        return "offtrack"
    
    # If no tasks are offtrack, check if there are any pending tasks
    c.execute("""
        SELECT COUNT(*) 
        FROM tasks 
        WHERE group_id = ? AND completed = 0
    """, (group_id,))
    pending = c.fetchone()[0]
    if pending > 0:
        return "ontrack"

    # Check if any tasks exist
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id = ?", (group_id,))
    total = c.fetchone()[0]
    return "completed" if total > 0 else "inactive"

def get_status_badge(status: str) -> str:
    """Creates a colored status badge for displaying group status."""
    style = """
        border-radius: 9px;
        padding: 2px 8px;
        font-size: 12px;
        color: white;
        margin-left: 8px;
        display: inline-block;
    """
    
    colors = {
        "offtrack": "#e74c3c",  # Red
        "ontrack": "#f1c40f",   # Yellow
        "completed": "#2ecc71",  # Green
        "inactive": "#95a5a6"    # Grey
    }
    
    labels = {
        "offtrack": "⚠️ Off Track",
        "ontrack": "✓ On Track",
        "completed": "✅ Completed",
        "inactive": "⚪ No Tasks"
    }
    
    return f'<span style="{style} background-color:{colors[status]}">{labels[status]}</span>'

def handle_modals() -> None:
    """Manages the display of modal dialogs for group operations."""
    if "delete_group" in st.session_state:
        delete_group_modal()
    elif "edit_group" in st.session_state:
        edit_group_modal()

@st.dialog("Edit Group", width="large")
def edit_group_modal() -> None:
    """Shows a dialog for editing group properties."""
    group_id, name, color, remarks, is_template = st.session_state.edit_group
    conn = get_connection()
    try:
        with st.form(key=f"edit_group_{group_id}"):
            new_name = st.text_input("Group Name", value=name)
            new_color = st.color_picker("Color", value=color)
            new_remarks = st.text_area("Remarks", value=remarks)
            new_template = st.checkbox("Template Group", value=is_template)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save"):
                    update_group(conn, group_id, new_name, new_color, new_remarks, new_template)
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.pop("edit_group", None)
                    st.rerun()
    finally:
        conn.close()

def update_group(
    conn,
    group_id: int,
    name: str,
    color: str,
    remarks: str,
    is_template: bool
) -> None:
    """Updates the properties of an existing task group."""
    try:
        c = conn.cursor()
        c.execute('''
            UPDATE groups 
            SET group_name=?, color=?, remarks=?, isTemplate=?
            WHERE group_id=?
        ''', (name, color, remarks, is_template, group_id))
        conn.commit()
        st.session_state.pop("edit_group", None)
        st.rerun()
    except Exception as e:
        st.error(f"Error updating group: {str(e)}")

@st.dialog("Confirm Deletion", width="small")
def delete_group_modal() -> None:
    """Shows a confirmation dialog for deleting a group."""
    group_id = st.session_state.delete_group
    st.warning("This will permanently delete the group and all its tasks!")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Confirm"):
            delete_group(group_id)
    
    with col2:
        if st.button("❌ Cancel"):
            st.session_state.pop("delete_group", None)
            st.rerun()

def delete_group(group_id: int) -> None:
    """Deletes a group and all its associated tasks."""
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE group_id=?", (group_id,))
        c.execute("DELETE FROM groups WHERE group_id=?", (group_id,))
        conn.commit()
        st.session_state.pop("delete_group", None)
        st.rerun()
    except Exception as e:
        st.error(f"Error deleting group: {str(e)}")
    finally:
        conn.close()