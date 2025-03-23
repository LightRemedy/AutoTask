import streamlit as st
from db import get_connection
import datetime

def show():
    if "current_view_group" not in st.session_state:
        st.error("No group selected")
        return

    if st.button("← Back to Groups"):
        st.session_state.current_page = "Group Page"
        st.session_state.pop("current_view_group", None)
        st.rerun()

    group_id = st.session_state.current_view_group
    conn = get_connection()
    c = conn.cursor()

    c.execute('''
        SELECT group_id, group_name, created_by, color, remarks, isTemplate 
        FROM groups WHERE group_id = ?
    ''', (group_id,))
    group = c.fetchone()
    
    if not group:
        st.error("Group not found")
        conn.close()
        return
        
    group_id, group_name, created_by, color, remarks, is_template = group

    st.title(f"📦 {group_name}")
    if is_template:
        st.markdown("🏷️ **Template Group**")

    st.subheader("📊 Group Status")
    status = get_group_status(conn, group_id)
    st.markdown(f"**Current Status:** {get_status_badge(status)}", unsafe_allow_html=True)

    # Add Task Section
    with st.expander("➕ Add New Task", expanded=False):
        with st.form("add_task_form", clear_on_submit=True):
            task_name = st.text_input("Task Name*", max_chars=100)
            due_date = st.date_input("Due Date*", min_value=datetime.date.today())
            due_date_str = due_date.strftime("%Y-%m-%d")
            notification_days = st.selectbox(
                "Notification Days*",
                options=[0, 1, 3, 7, 14],
                format_func=lambda x: f"{x} days before" if x > 0 else "On due date"
            )
            
            # Get all existing tasks for prerequisites
            c.execute('''
                SELECT task_id, task_name, due_date 
                FROM tasks 
                WHERE group_id = ?
            ''', (group_id,))
            existing_tasks = c.fetchall()
            
            # Show all tasks as selectable prerequisites
            selected_prereqs = st.multiselect(
                "Prerequisite Tasks",
                options=[t[0] for t in existing_tasks],
                format_func=lambda x: next(f"{t[1]} ({t[2]})" for t in existing_tasks if t[0] == x)
            )

            # Form submission
            if st.form_submit_button("Create Task"):
                validation_errors = []
                invalid_prereqs = []

                # Validate required fields
                if not task_name.strip():
                    validation_errors.append("Task name is required")
                
                # Validate prerequisites
                for p_id in selected_prereqs:
                    c.execute("SELECT due_date FROM tasks WHERE task_id=?", (p_id,))
                    result = c.fetchone()
                    if not result:
                        validation_errors.append(f"Prerequisite task {p_id} not found")
                        continue
                        
                    prereq_date_str = result[0]
                    try:
                        prereq_date = datetime.datetime.strptime(prereq_date_str, "%Y-%m-%d").date()
                        if prereq_date > due_date:
                            invalid_prereqs.append(f"Task {p_id} ({prereq_date_str})")
                    except ValueError:
                        validation_errors.append(f"Invalid date format in task {p_id}")

                # Show errors and ABORT if any issues
                if validation_errors or invalid_prereqs:
                    for err in validation_errors:
                        st.error(err)
                    for invalid in invalid_prereqs:
                        st.error(f"Invalid prerequisite: {invalid} > New task date ({due_date_str})")
                    return  # Critical: Stop execution here

                # Only proceed if validation passed
                try:
                    conn.execute("BEGIN TRANSACTION")
                    
                    # Insert main task
                    c.execute('''
                        INSERT INTO tasks 
                        (task_name, due_date, notification_days, group_id, created_by)
                        VALUES (?,?,?,?,?)
                    ''', (task_name, due_date_str, notification_days, 
                        group_id, st.session_state.username))
                    new_task_id = c.lastrowid
                    
                    # Insert validated prerequisites
                    for p_id in selected_prereqs:
                        c.execute('''
                            INSERT INTO task_link (task_id, pre_task_id)
                            VALUES (?,?)
                        ''', (new_task_id, p_id))
                    
                    conn.commit()
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"Database error: {str(e)}")

    # Tasks List (remaining code unchanged)
    st.subheader("📋 Tasks")
    c.execute('''
        SELECT t.task_id, t.task_name, t.due_date, t.completed,
               GROUP_CONCAT(p.task_name, '|||') as prerequisites
        FROM tasks t
        LEFT JOIN task_link tl ON t.task_id = tl.task_id
        LEFT JOIN tasks p ON tl.pre_task_id = p.task_id
        WHERE t.group_id = ?
        GROUP BY t.task_id
        ORDER BY t.due_date
    ''', (group_id,))
    tasks = c.fetchall()

    if tasks:
        completed, total = get_task_count(conn, group_id)
        st.progress(completed/total if total > 0 else 0)
        st.caption(f"Completed: {completed}/{total} tasks")

        for task in tasks:
            task_id, name, due_date_str, completed, prerequisites = task
            with st.container(border=True):
                cols = st.columns([4, 1, 1, 1, 1])
                
                status = get_task_status(conn, task_id)
                try:
                    due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
                    formatted_date = due_date.strftime('%d %b %Y')
                except ValueError:
                    st.error(f"Invalid date format for task {task_id}: {due_date_str}")
                    continue

                with cols[0]:
                    st.markdown(f"**{name}**")
                    st.markdown(get_status_badge(status), unsafe_allow_html=True)
                    st.caption(f"📅 Due: {formatted_date}")

                with cols[1]:
                    if not completed:
                        if st.button("✅", key=f"complete_{task_id}"):
                            handle_task_completion(conn, task_id)
                            st.rerun()
                    else:
                        st.write("")

                with cols[2]:
                    if st.button("👁️", key=f"view_{task_id}"):
                        st.session_state.view_task = task_id
                        st.rerun()

                with cols[3]:
                    if st.button("✏️", key=f"edit_{task_id}"):
                        st.session_state.edit_task = task_id
                        st.rerun()

                with cols[4]:
                    if st.button("🗑️", key=f"del_{task_id}"):
                        st.session_state.delete_task = task_id
                        st.rerun()

    else:
        st.info("No tasks found in this group")

    handle_modals()
    conn.close()

# [Rest of the code remains unchanged from your original version]


@st.dialog("Edit Task")
def edit_task_modal():
    task_id = st.session_state.edit_task
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute('''
            SELECT task_name, due_date, notification_days, completed
            FROM tasks WHERE task_id=?
        ''', (task_id,))
        task_data = c.fetchone()
        
        if task_data:
            with st.form(key=f"edit_{task_id}"):
                task_name = st.text_input("Task Name", value=task_data[0])
                
                try:
                    original_due = datetime.datetime.strptime(task_data[1], "%Y-%m-%d").date()
                except ValueError:
                    st.error(f"Invalid date format: {task_data[1]}")
                    original_due = datetime.date.today()
                
                new_due = st.date_input("Due Date", value=original_due)
                notification_days = st.selectbox(
                    "Notification Days",
                    options=[0, 1, 3, 7, 14],
                    index=[0, 1, 3, 7, 14].index(task_data[2]),
                    format_func=lambda x: f"{x} days before" if x > 0 else "On due date"
                )
                
                # Get all tasks for prerequisites
                c.execute('''
                    SELECT task_id, task_name, due_date 
                    FROM tasks 
                    WHERE group_id = (
                        SELECT group_id FROM tasks WHERE task_id = ?
                    ) AND task_id != ?
                ''', (task_id, task_id))
                all_tasks = c.fetchall()
                
                # Get current prerequisites
                c.execute('''
                    SELECT pre_task_id FROM task_link
                    WHERE task_id = ?
                ''', (task_id,))
                current_prereqs = [row[0] for row in c.fetchall()]
                
                # Show all tasks as selectable prerequisites
                selected_prereqs = st.multiselect(
                    "Prerequisite Tasks",
                    options=[t[0] for t in all_tasks],
                    default=current_prereqs,
                    format_func=lambda x: next(f"{t[1]} ({t[2]})" for t in all_tasks if t[0] == x)
                )

                completed = st.toggle("Completed", value=bool(task_data[3]))

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Save"):
                        validation_errors = []
                        invalid_prereqs = []

                        # Validate prerequisites
                        for p_id in selected_prereqs:
                            c.execute("SELECT due_date FROM tasks WHERE task_id=?", (p_id,))
                            result = c.fetchone()
                            if not result:
                                validation_errors.append(f"Prerequisite task {p_id} not found")
                                continue
                                
                            prereq_date_str = result[0]
                            try:
                                prereq_date = datetime.datetime.strptime(prereq_date_str, "%Y-%m-%d").date()
                                if prereq_date > new_due:
                                    invalid_prereqs.append(f"Task {p_id} ({prereq_date_str})")
                            except ValueError:
                                validation_errors.append(f"Invalid date format in task {p_id}")

                        # Show errors and abort
                        if validation_errors or invalid_prereqs:
                            for err in validation_errors:
                                st.error(err)
                            for invalid in invalid_prereqs:
                                st.error(f"Invalid prerequisite: {invalid} > Task due date ({new_due})")
                            return

                        # Proceed with update if validation passed
                        try:
                            conn.execute("BEGIN TRANSACTION")
                            
                            # Update main task
                            c.execute('''
                                UPDATE tasks SET
                                    task_name=?,
                                    due_date=?,
                                    notification_days=?,
                                    completed=?
                                WHERE task_id=?
                            ''', (task_name, new_due.strftime("%Y-%m-%d"), 
                                notification_days, int(completed), task_id))
                            
                            # Update prerequisites
                            c.execute('DELETE FROM task_link WHERE task_id=?', (task_id,))
                            for p_id in selected_prereqs:
                                c.execute('''
                                    INSERT INTO task_link (task_id, pre_task_id)
                                    VALUES (?,?)
                                ''', (task_id, p_id))
                            
                            conn.commit()
                            st.session_state.pop("edit_task", None)
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Database error: {str(e)}")
                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        st.session_state.pop("edit_task", None)
                        st.rerun()
    finally:
        conn.close()

def get_total_delay(conn, task_id):
    """Calculate total delay from all prerequisites recursively"""
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
    c = conn.cursor()
    current_date = st.session_state.get("mock_now", datetime.date.today())
    
    # Check prerequisites
    c.execute('''
        SELECT p.task_id, p.task_name, p.completed 
        FROM task_link tl
        JOIN tasks p ON tl.pre_task_id = p.task_id
        WHERE tl.task_id = ?
    ''', (task_id,))
    prerequisites = c.fetchall()
    
    incomplete_prereqs = [p for p in prerequisites if not p[2]]
    
    if incomplete_prereqs:
        st.session_state.confirm_prereq_completion = {
            "task_id": task_id,
            "prereqs": incomplete_prereqs
        }
        st.rerun()
    else:
        complete_task(conn, task_id)
        st.rerun()

@st.dialog("Confirm Prerequisite Completion")
def confirm_prereq_completion():
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
    c = conn.cursor()
    current_date = st.session_state.get("mock_now", datetime.date.today())
    
    c.execute("SELECT due_date FROM tasks WHERE task_id=?", (task_id,))
    due_date_str = c.fetchone()[0]
    due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
    
    delay_days = max((current_date - due_date).days, 0)
    
    c.execute('''
        UPDATE tasks 
        SET completed=1, 
            completed_date=?,
            delay_days=?
        WHERE task_id=?
    ''', (current_date.strftime("%Y-%m-%d"), delay_days, task_id))
    
    update_dependent_tasks(conn, task_id, delay_days)
    conn.commit()

def update_dependent_tasks(conn, task_id, delay_days):
    c = conn.cursor()
    c.execute('''
        SELECT t.task_id, t.due_date 
        FROM task_link tl
        JOIN tasks t ON tl.task_id = t.task_id
        WHERE tl.pre_task_id = ?
    ''', (task_id,))
    
    for dependent in c.fetchall():
        dep_id, dep_due_str = dependent
        dep_due = datetime.datetime.strptime(dep_due_str, "%Y-%m-%d").date()
        new_due = dep_due + datetime.timedelta(days=delay_days)
        
        c.execute('''
            UPDATE tasks
            SET due_date=?
            WHERE task_id=?
        ''', (new_due.strftime("%Y-%m-%d"), dep_id))

def get_task_status(conn, task_id):
    c = conn.cursor()
    current_date = st.session_state.get("mock_now", datetime.date.today()).strftime("%Y-%m-%d")
    
    c.execute("SELECT completed, due_date, delay_days FROM tasks WHERE task_id=?", (task_id,))
    result = c.fetchone()
    if not result:
        return "inactive"
        
    completed, due_date_str, delay_days = result
    
    if completed:
        if delay_days and delay_days > 0:
            return "completed_late"
        return "completed"
        
    if due_date_str < current_date:
        return "offtrack"
        
    c.execute('''
        SELECT COUNT(*) FROM task_link
        WHERE task_id=? AND pre_task_id IN (
            SELECT task_id FROM tasks WHERE completed=0
        )
    ''', (task_id,))
    if c.fetchone()[0] > 0:
        return "offtrack"
        
    return "ontrack"

@st.dialog("Confirm Deletion")
def delete_task_modal():
    task_id = st.session_state.delete_task
    st.warning("This will permanently delete the task and its dependencies!")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Confirm"):
            conn = get_connection()
            try:
                c = conn.cursor()
                c.execute("DELETE FROM task_link WHERE task_id=?", (task_id,))
                c.execute("DELETE FROM tasks WHERE task_id=?", (task_id,))
                conn.commit()
                st.session_state.pop("delete_task", None)
                st.rerun()
            finally:
                conn.close()
    
    with col2:
        if st.button("❌ Cancel"):
            st.session_state.pop("delete_task", None)
            st.rerun()

def get_group_status(conn, group_id):
    c = conn.cursor()
    current_date = st.session_state.get("mock_now", datetime.date.today()).strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=0 AND due_date < ?", (group_id, current_date))
    if c.fetchone()[0] > 0: return "offtrack"
    
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=0", (group_id,))
    if c.fetchone()[0] > 0: return "ontrack"
    
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    return "completed" if c.fetchone()[0] > 0 else "inactive"

def get_task_count(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=1", (group_id,))
    completed = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    return completed, c.fetchone()[0]

def get_status_badge(status):
    style = "border-radius:9px; padding:0 7px; font-size:13px; color:white;"
    colors = {
        "offtrack": "#e74c3c", 
        "ontrack": "#f1c40f",
        "completed": "#2ecc71",
        "completed_late": "#f39c12",  # Orange for late completion
        "inactive": "#95a5a6"
    }
    return f'<span style="{style} background-color:{colors[status]}">{status.title().replace("_", " ")}</span>'

def handle_modals():
    if "delete_task" in st.session_state:
        delete_task_modal()
    elif "edit_task" in st.session_state:
        edit_task_modal()
    elif "view_task" in st.session_state:
        view_task_modal()

@st.dialog("Task Details")
def view_task_modal():
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
