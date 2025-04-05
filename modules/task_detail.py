import streamlit as st
from core.database import get_connection
from datetime import datetime, date
from typing import Optional, List
from core.date_utils import get_current_date, format_date

def show_group_details():
    """Displays detailed information about a specific task group."""
    # Check if a group is selected
    if "current_view_group" not in st.session_state:
        st.error("No group selected")
        st.session_state.current_page = "Group Page"
        st.rerun()
        return

    # Navigation
    col1, col2 = st.columns([1, 11])
    with col1:
        if st.button("←", use_container_width=True):
            st.session_state.current_page = "Group Page"
            st.session_state.pop("current_view_group", None)
            st.rerun()
    with col2:
        st.title("Group Details")

    # Get group information
    group_id = st.session_state.current_view_group
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute('''
            SELECT group_id, group_name, created_by, color, remarks, isTemplate 
            FROM groups WHERE group_id = ?
        ''', (group_id,))
        group = c.fetchone()
        
        if not group:
            st.error("Group not found")
            st.session_state.current_page = "Group Page"
            st.rerun()
            return
            
        group_id, group_name, created_by, color, remarks, is_template = group

        # Group header
        st.header(f"📦 {group_name}")
        if remarks:
            st.caption(remarks)
        if is_template:
            st.markdown("🏷️ **Template Group**")

        # Group status
        st.subheader("📊 Group Status")
        status = get_group_status(conn, group_id)
        completed, total = get_task_count(conn, group_id)
        
        # Show progress and status
        if total > 0:
            st.progress(completed/total, text=f"Progress: {completed}/{total} tasks")
            st.markdown(get_status_badge(status), unsafe_allow_html=True)
        else:
            st.info("No tasks in this group yet")

        # Tasks section
        st.subheader("📋 Tasks")
        
        # Add task button
        if st.button("➕ Add New Task", use_container_width=True):
            st.session_state.show_add_task = True
            st.rerun()

        # Add task form
        if st.session_state.get("show_add_task", False):
            add_task_form(conn, group_id)

        # List tasks
        display_tasks(conn, group_id)

    finally:
        conn.close()

def add_task_form(conn, group_id: int) -> None:
    """Shows a form for adding a new task to a group."""
    with st.form("add_task_form", clear_on_submit=True):
        # Basic task information
        task_name = st.text_input("Task Name*", max_chars=100)
        due_date = st.date_input("Due Date*", min_value=get_current_date())
        
        # Notification options
        col1, col2 = st.columns(2)
        with col1:
            notification_days = st.selectbox(
                "Notification Days*",
                options=[0, 1, 3, 7, 14, 30, 60],
                format_func=lambda x: f"{x} days before" if x > 0 else "On due date"
            )
        with col2:
            telegram_notify = st.checkbox("Enable Telegram Notifications", value=True)
        
        # Prerequisites
        c = conn.cursor()
        c.execute('''
            SELECT task_id, task_name, due_date 
            FROM tasks 
            WHERE group_id = ? AND completed = 0
            ORDER BY due_date
        ''', (group_id,))
        existing_tasks = c.fetchall()
        
        if existing_tasks:
            selected_prereqs = st.multiselect(
                "Prerequisite Tasks",
                options=[t[0] for t in existing_tasks],
                format_func=lambda x: next(
                    f"{t[1]} (Due: {format_date(t[2])})" 
                    for t in existing_tasks if t[0] == x
                )
            )
        else:
            selected_prereqs = []

        # Form submission
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Create Task", use_container_width=True)
        with col2:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.pop("show_add_task", None)
                st.rerun()

        if submit:
            create_task(
                conn=conn,
                group_id=group_id,
                task_name=task_name,
                due_date=due_date,
                notification_days=notification_days,
                telegram_notify=telegram_notify,
                prerequisites=selected_prereqs
            )

def create_task(
    conn,
    group_id: int,
    task_name: str,
    due_date: datetime.date,
    notification_days: int,
    telegram_notify: bool,
    prerequisites: List[int] = None
) -> None:
    """Creates a new task with optional prerequisites."""
    if not task_name.strip():
        st.error("Task name is required")
        return

    # Validate prerequisites
    if prerequisites:
        c = conn.cursor()
        for p_id in prerequisites:
            c.execute("SELECT due_date FROM tasks WHERE task_id=?", (p_id,))
            result = c.fetchone()
            if not result:
                st.error(f"Prerequisite task {p_id} not found")
                return
                
            prereq_date = datetime.datetime.strptime(result[0], "%Y-%m-%d").date()
            if prereq_date > due_date:
                st.error(
                    f"Invalid prerequisite: Task due on {format_date(result[0])} "
                    f"cannot be a prerequisite for task due on {format_date(due_date)}"
                )
                return

    try:
        conn.execute("BEGIN TRANSACTION")
        c = conn.cursor()
        
        # Insert task
        c.execute('''
            INSERT INTO tasks (
                task_name, due_date, notification_days, group_id,
                created_by, telegram_notify
            ) VALUES (?,?,?,?,?,?)
        ''', (
            task_name,
            due_date.isoformat(),
            notification_days,
            group_id,
            st.session_state.username,
            int(telegram_notify)
        ))
        new_task_id = c.lastrowid
        
        # Insert prerequisites
        if prerequisites:
            for p_id in prerequisites:
                c.execute('''
                    INSERT INTO task_link (task_id, pre_task_id)
                    VALUES (?,?)
                ''', (new_task_id, p_id))
        
        conn.commit()
        st.session_state.pop("show_add_task", None)
        st.success(f"Task '{task_name}' created successfully!")
        st.rerun()
        
    except Exception as e:
        conn.rollback()
        st.error(f"Error creating task: {str(e)}")

def display_tasks(conn, group_id: int) -> None:
    """Shows all tasks in a group with their status and actions."""
    c = conn.cursor()
    c.execute('''
        SELECT t.task_id, t.task_name, t.due_date, t.completed,
               GROUP_CONCAT(p.task_name, '|||') as prerequisites
        FROM tasks t
        LEFT JOIN task_link tl ON t.task_id = tl.task_id
        LEFT JOIN tasks p ON tl.pre_task_id = p.task_id
        WHERE t.group_id = ?
        GROUP BY t.task_id
        ORDER BY t.completed, t.due_date
    ''', (group_id,))
    tasks = c.fetchall()

    if not tasks:
        st.info("No tasks found in this group")
        return

    for task in tasks:
        task_id, name, due_date_str, completed, prerequisites = task
        status = get_task_status(conn, task_id)
        
        with st.container(border=True):
            cols = st.columns([3, 1])
            with cols[0]:
                # Add colored status box using markdown
                status_colors = {
                    "ontrack": "🟡 Ontrack",
                    "offtrack": "🔴 Offtrack",
                    "completed": "🟢 Completed"
                }
                status_text = status_colors.get(status.lower(), "⚪ Unknown")
                st.markdown(f"{status_text}")
                
                st.markdown(f"**{name}**")
                st.caption(f"Due: {due_date_str}")
                if prerequisites:
                    st.caption("Prerequisites: " + ", ".join(prerequisites.split("|||")))
            
            with cols[1]:
                st.checkbox(
                    "Complete",
                    value=completed,
                    key=f"complete_{task_id}",
                    on_change=handle_task_completion,
                    args=(st.session_state.db_conn, task_id)
                )
                
                # Remove the view/modify/delete buttons for sub-tasks
                # The original code likely had these buttons here

def format_date_display(date_str: str) -> str:
    """Formats a date string into a readable format."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        return date_obj.strftime("%d %b %Y")
    except ValueError:
        return date_str

def get_total_delay(conn, task_id):
    """Calculates the total delay from all prerequisite tasks."""
    c = conn.cursor()
    c.execute('''
        WITH RECURSIVE dep_chain(task_id, delay) AS (
            SELECT tl.pre_task_id, t.delay_days
            FROM task_link tl
            JOIN tasks t ON tl.pre_task_id = t.task_id
            WHERE tl.task_id = ?
            UNION ALL
            SELECT tl2.pre_task_id, dc.delay + t2.delay_days
            FROM dep_chain dc
            JOIN task_link tl2 ON dc.task_id = tl2.task_id
            JOIN tasks t2 ON tl2.pre_task_id = t2.task_id
        )
        SELECT MAX(delay) FROM dep_chain
    ''', (task_id,))
    total_delay = c.fetchone()[0] or 0
    return total_delay

def handle_task_completion(conn, task_id):
    """Handles the completion status of a task."""
    try:
        c = conn.cursor()
        
        # Get current completion status
        c.execute("SELECT completed FROM tasks WHERE task_id = ?", (task_id,))
        current_status = c.fetchone()[0]
        
        # Toggle completion status
        new_status = 0 if current_status else 1
        completion_date = format_date(get_current_date()) if new_status else None
        
        # Update task
        c.execute("""
            UPDATE tasks 
            SET completed = ?, completion_date = ?
            WHERE task_id = ?
        """, (new_status, completion_date, task_id))
        
        # Add to task history
        status_change = "completed" if new_status else "reopened"
        c.execute("""
            INSERT INTO task_history (
                task_id, status_change, changed_at, changed_by
            ) VALUES (?, ?, ?, ?)
        """, (
            task_id,
            status_change,
            format_date(get_current_date()),
            st.session_state.username
        ))
        
        conn.commit()
    except Exception as e:
        st.error(f"Error updating task completion: {str(e)}")
        conn.rollback()

@st.dialog("Confirm Prerequisite Completion")
def confirm_prereq_completion():
    """Shows a dialog to confirm completing prerequisite tasks."""
    if "confirm_prereq_completion" not in st.session_state:
        return
    
    config = st.session_state.confirm_prereq_completion
    st.warning("Some prerequisites are incomplete!")
    
    st.markdown("**Incomplete Prerequisites:**")
    for p in config["prereqs"]:
        st.markdown(f"- {p[1]} (ID: {p[0]})")
    
    if st.button("Auto-complete prerequisites and continue"):
        conn = get_connection()
        try:
            for p in config["prereqs"]:
                complete_task(conn, p[0])
            complete_task(conn, config["task_id"])
            conn.commit()
        finally:
            conn.close()
        st.session_state.pop("confirm_prereq_completion", None)
        st.rerun()
    
    if st.button("Cancel"):
        st.session_state.pop("confirm_prereq_completion", None)
        st.rerun()

def complete_task(conn, task_id):
    """Marks a task as completed in the database."""
    c = conn.cursor()
    c.execute('''
        UPDATE tasks 
        SET completed=1
        WHERE task_id=?
    ''', (task_id,))
    conn.commit()

def get_task_status(conn, task_id):
    """Determines the current status of a task (completed, offtrack, ontrack, or inactive)."""
    c = conn.cursor()
    current_date = get_current_date()
    
    c.execute("""
        SELECT t.completed, t.due_date
        FROM tasks t
        WHERE t.task_id = ?
    """, (task_id,))
    result = c.fetchone()
    
    if not result:
        return "inactive"
        
    completed, due_date_str = result
    
    if completed:
        return "completed"
    
    # Convert due_date string to datetime.date object
    try:
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    except ValueError:
        st.error(f"Invalid due date format: {due_date_str}")
        return "offtrack"
    
    # Check if task is overdue based on mock date
    is_overdue = due_date < current_date
    
    # Determine status based on due date only
    if is_overdue:
        return "offtrack"
    else:
        return "ontrack"

@st.dialog("Confirm Deletion")
def delete_task_modal():
    """Shows a confirmation dialog for deleting a task."""
    task_id = st.session_state.delete_task
    conn = get_connection()
    try:
        # Check if task has dependent tasks
        c = conn.cursor()
        c.execute("""
            SELECT t.task_name 
            FROM tasks t
            JOIN task_link tl ON t.task_id = tl.task_id
            WHERE tl.pre_task_id = ?
        """, (task_id,))
        dependent_tasks = c.fetchall()
        
        if dependent_tasks:
            st.error("Cannot delete this task because other tasks depend on it:")
            for task in dependent_tasks:
                st.markdown(f"- {task[0]}")
            if st.button("❌ Close"):
                st.session_state.pop("delete_task", None)
                st.rerun()
            return
            
        st.warning("This will permanently delete the task!")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Confirm"):
                # Delete task links first
                c.execute("DELETE FROM task_link WHERE task_id=? OR pre_task_id=?", 
                         (task_id, task_id))
                # Then delete the task
                c.execute("DELETE FROM tasks WHERE task_id=?", (task_id,))
                conn.commit()
                st.session_state.pop("delete_task", None)
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel"):
                st.session_state.pop("delete_task", None)
                st.rerun()
    finally:
        conn.close()

@st.dialog("Edit Task")
def edit_task_modal():
    """Shows a dialog for editing task properties."""
    task_id = st.session_state.edit_task
    conn = get_connection()
    try:
        c = conn.cursor()
        
        # Get task details including dependencies
        c.execute('''
            SELECT t.task_name, t.due_date, t.notification_days, t.completed,
                   t.group_id, g.group_name
            FROM tasks t
            JOIN groups g ON t.group_id = g.group_id
            WHERE t.task_id = ?
        ''', (task_id,))
        task_data = c.fetchone()
        
        if not task_data:
            st.error("Task not found!")
            return
            
        task_name, due_date_str, notif_days, completed, group_id, group_name = task_data
        
        # Check if task has dependent tasks
        c.execute("""
            SELECT t.task_id, t.task_name, t.due_date
            FROM tasks t
            JOIN task_link tl ON t.task_id = tl.task_id
            WHERE tl.pre_task_id = ?
        """, (task_id,))
        dependent_tasks = c.fetchall()
        
        if dependent_tasks:
            st.warning("⚠️ This task has dependent tasks. Changes may affect them:")
            for dep in dependent_tasks:
                st.markdown(f"- {dep[1]} (Due: {format_date(dep[2])})")
            st.divider()
        
        with st.form(key=f"edit_{task_id}"):
            task_name = st.text_input("Task Name", value=task_name)
            
            try:
                original_due = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
            except ValueError:
                st.error(f"Invalid date format: {due_date_str}")
                original_due = datetime.date.today()
            
            new_due = st.date_input("Due Date", value=original_due)
            
            # Get all potential prerequisite tasks
            c.execute('''
                SELECT t.task_id, t.task_name, t.due_date 
                FROM tasks t
                WHERE t.group_id = ? 
                AND t.task_id != ?
                AND t.task_id NOT IN (
                    -- Exclude tasks that depend on this task
                    SELECT t2.task_id
                    FROM tasks t2
                    JOIN task_link tl ON t2.task_id = tl.task_id
                    WHERE tl.pre_task_id = ?
                )
                ORDER BY t.due_date
            ''', (group_id, task_id, task_id))
            available_tasks = c.fetchall()
            
            # Get current prerequisites
            c.execute('''
                SELECT pre_task_id FROM task_link
                WHERE task_id = ?
            ''', (task_id,))
            current_prereqs = [row[0] for row in c.fetchall()]
            
            notification_days = st.selectbox(
                "Notification Days",
                options=[0, 1, 3, 7, 14, 30],
                index=[0, 1, 3, 7, 14, 30].index(notif_days),
                format_func=lambda x: f"{x} days before" if x > 0 else "On due date"
            )
            
            # Show available tasks as prerequisites
            if available_tasks:
                selected_prereqs = st.multiselect(
                    "Prerequisite Tasks",
                    options=[t[0] for t in available_tasks],
                    default=current_prereqs,
                    format_func=lambda x: next(
                        f"{t[1]} (Due: {format_date(t[2])})" 
                        for t in available_tasks if t[0] == x
                    )
                )
            else:
                selected_prereqs = []
                st.info("No available tasks to set as prerequisites")

            completed = st.toggle("Completed", value=bool(completed))

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save"):
                    # Validate prerequisites
                    validation_errors = []
                    for p_id in selected_prereqs:
                        c.execute("SELECT due_date FROM tasks WHERE task_id=?", (p_id,))
                        result = c.fetchone()
                        if not result:
                            validation_errors.append(f"Prerequisite task {p_id} not found")
                            continue
                            
                        prereq_date = datetime.datetime.strptime(result[0], "%Y-%m-%d").date()
                        if prereq_date > new_due:
                            validation_errors.append(
                                f"Task due on {format_date(result[0])} cannot be a "
                                f"prerequisite for task due on {format_date(new_due)}"
                            )

                    if validation_errors:
                        for err in validation_errors:
                            st.error(err)
                        return

                    try:
                        conn.execute("BEGIN TRANSACTION")
                        
                        # Update task
                        c.execute('''
                            UPDATE tasks SET
                                task_name=?,
                                due_date=?,
                                notification_days=?,
                                completed=?
                            WHERE task_id=?
                        ''', (
                            task_name, 
                            new_due.strftime("%Y-%m-%d"), 
                            notification_days,
                            int(completed),
                            task_id
                        ))
                        
                        # Update prerequisites
                        c.execute('DELETE FROM task_link WHERE task_id=?', (task_id,))
                        for p_id in selected_prereqs:
                            c.execute('''
                                INSERT INTO task_link (task_id, pre_task_id)
                                VALUES (?,?)
                            ''', (task_id, p_id))
                        
                        # If the due date changed and there are dependent tasks,
                        # adjust their dates proportionally
                        if dependent_tasks and new_due != original_due:
                            days_diff = (new_due - original_due).days
                            for dep_id, _, _ in dependent_tasks:
                                c.execute("""
                                    UPDATE tasks 
                                    SET due_date = date(due_date, ?) 
                                    WHERE task_id = ?
                                """, (f"{days_diff:+d} days", dep_id))
                        
                        conn.commit()
                        st.session_state.pop("edit_task", None)
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error updating task: {str(e)}")
            
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.pop("edit_task", None)
                    st.rerun()
    finally:
        conn.close()

def get_group_status(conn, group_id):
    """Determines the current status of a group based on its tasks."""
    c = conn.cursor()
    current_date = format_date(get_current_date())
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=0 AND due_date < ?", (group_id, current_date))
    if c.fetchone()[0] > 0: return "offtrack"
    
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=0", (group_id,))
    if c.fetchone()[0] > 0: return "ontrack"
    
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    return "completed" if c.fetchone()[0] > 0 else "inactive"

def get_task_count(conn, group_id):
    """Counts the number of completed and total tasks in a group."""
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=1", (group_id,))
    completed = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    return completed, c.fetchone()[0]

def get_status_badge(status):
    """Creates a colored status badge for displaying task status."""
    style = "border-radius:9px; padding:0 7px; font-size:13px; color:white;"
    colors = {
        "offtrack": "#e74c3c", 
        "ontrack": "#f1c40f",
        "completed": "#2ecc71",
        "inactive": "#95a5a6"
    }
    return f'<span style="{style} background-color:{colors[status]}">{status.title()}</span>'

def handle_modals():
    """Manages the display of task-related modal dialogs."""
    if "delete_task" in st.session_state:
        delete_task_modal()
    elif "edit_task" in st.session_state:
        edit_task_modal()
    elif "view_task" in st.session_state:
        view_task_modal()

@st.dialog("Task Details")
def view_task_modal():
    """Shows detailed information about a specific task."""
    task_id = st.session_state.view_task
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute('''
            SELECT t.task_name, t.due_date, t.completed, t.notification_days, 
                   GROUP_CONCAT(p.task_name, '|||')
            FROM tasks t
            LEFT JOIN task_link tl ON t.task_id = tl.task_id
            LEFT JOIN tasks p ON tl.pre_task_id = p.task_id
            WHERE t.task_id = ?
        ''', (task_id,))
        task_data = c.fetchone()
        
        if task_data:
            name, due_date_str, completed, notif_days, prerequisites = task_data
            try:
                due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
                formatted_date = due_date.strftime('%d %b %Y')
            except ValueError:
                st.error(f"Invalid date format: {due_date_str}")
                return
            
            st.markdown(f"### {name}")
            st.markdown(f"**Status:** {'Completed ✅' if completed else 'Pending ⏳'}")
            st.markdown(f"**Due Date:** {formatted_date}")
            st.markdown(f"**Notifications:** {notif_days} days before due date")
            
            if prerequisites:
                st.divider()
                st.markdown("**Prerequisites:**")
                for p in prerequisites.split('|||'):
                    if p.strip(): st.markdown(f"- {p.strip()}")
            
            if st.button("Close"):
                st.session_state.pop("view_task", None)
                st.rerun()
    finally:
        conn.close()