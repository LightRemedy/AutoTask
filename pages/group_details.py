import streamlit as st
from db import get_connection
import datetime

def show():
    if "current_view_group" not in st.session_state:
        st.error("No group selected")
        return

    # Back button handling
    if st.button("← Back to Groups"):
        st.session_state.current_page = "Group Page"
        st.session_state.pop("current_view_group", None)
        st.rerun()

    group_id = st.session_state.current_view_group
    conn = get_connection()
    c = conn.cursor()

    # Group details display
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

    # Status Section
    st.subheader("📊 Group Status")
    status = get_group_status(conn, group_id)
    st.markdown(f"**Current Status:** {get_status_badge(status)}", unsafe_allow_html=True)

    # Add Task Section
    
    # Add Task Section (updated with prerequisites)
    # In the Add Task Section
    with st.expander("➕ Add New Task", expanded=False):
        with st.form("add_task_form"):  # Line 44
            # INDENT EVERYTHING INSIDE THE FORM BY 4 SPACES
            task_name = st.text_input("Task Name*", max_chars=100)
            due_date = st.date_input("Due Date*", min_value=datetime.date.today())
            notification_days = st.selectbox(
                "Notification Days*",
                options=[0, 1, 3, 7, 14],
                format_func=lambda x: f"{x} days before" if x > 0 else "On due date"
            )
            
            # Prerequisite selection
            c.execute('''
                SELECT task_id, task_name, due_date 
                FROM tasks 
                WHERE group_id = ? AND due_date < ?
                ORDER BY due_date
            ''', (group_id, due_date))
            prerequisites = c.fetchall()
            prereq_options = {t[0]: f"{t[1]} ({t[2]})" for t in prerequisites}
            
            selected_prereqs = st.multiselect(
                "Prerequisite Tasks",
                options=list(prereq_options.keys()),
                format_func=lambda x: prereq_options[x]
            )

            if st.form_submit_button("Create Task"):
                if task_name and due_date:
                    try:
                        # Insert task
                        c.execute('''
                            INSERT INTO tasks 
                            (task_name, due_date, notification_days, group_id, created_by)
                            VALUES (?,?,?,?,?)
                        ''', (task_name, due_date, notification_days, 
                            group_id, st.session_state.username))
                        new_task_id = c.lastrowid
                        
                        # Insert prerequisites
                        for prereq_id in selected_prereqs:
                            c.execute('''
                                INSERT INTO task_link (task_id, pre_task_id)
                                VALUES (?,?)
                            ''', (new_task_id, prereq_id))
                        
                        conn.commit()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating task: {str(e)}")


    # Tasks List
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
            task_id, name, due_date, completed, prerequisites = task
            with st.container(border=True):
                cols = st.columns([5, 1, 1, 1, 1])  # Reduced to 5 columns
                
                status = get_task_status(conn, task_id)
                formatted_date = datetime.date.fromisoformat(due_date).strftime('%d %b %Y')
                prereq_list = [p.strip() for p in prerequisites.split('|||') if p.strip()] if prerequisites else []

                with cols[0]:
                    st.markdown(f"**{name}**")
                    st.markdown(get_status_badge(status), unsafe_allow_html=True)
                    st.caption(f"📅 {formatted_date}")

                # Complete button moved to first position
                with cols[1]:
                    if not completed and status != "offtrack":
                        if st.button("✅", key=f"complete_{task_id}"):
                            c.execute("UPDATE tasks SET completed=1 WHERE task_id=?", (task_id,))
                            conn.commit()
                            st.rerun()

                # View button moved next to Edit
                with cols[2]:
                    if st.button("👁️", key=f"view_{task_id}"):
                        st.session_state.view_task = task_id
                        st.rerun()

                # Edit button
                with cols[3]:
                    if st.button("✏️", key=f"edit_{task_id}"):
                        st.session_state.edit_task = task_id
                        st.rerun()

                # Delete button
                with cols[4]:
                    if st.button("🗑️", key=f"del_{task_id}"):
                        st.session_state.delete_task = task_id
                        st.rerun()

    else:
        st.info("No tasks found in this group")

    # Handle modals AFTER processing click events
    handle_modals()
    
    conn.close()

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
            name, due_date, completed, notif_days, prerequisites = task_data
            formatted_date = datetime.date.fromisoformat(due_date).strftime('%d %b %Y')
            
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
                due_date = st.date_input("Due Date", 
                                       value=datetime.date.fromisoformat(task_data[1]))
                notif_days = st.selectbox(
                    "Notification Days",
                    options=[0, 1, 3, 7, 14],
                    index=[0, 1, 3, 7, 14].index(task_data[2]),
                    format_func=lambda x: f"{x} days before" if x > 0 else "On due date"
                )
                completed = st.toggle("Completed", value=bool(task_data[3]))

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Save"):
                        c.execute('''
                            UPDATE tasks SET
                                task_name = ?,
                                due_date = ?,
                                notification_days = ?,
                                completed = ?
                            WHERE task_id = ?
                        ''', (task_name, due_date, notif_days, 
                             int(completed), task_id))
                        conn.commit()
                        st.session_state.pop("edit_task", None)
                        st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        st.session_state.pop("edit_task", None)
                        st.rerun()
    finally:
        conn.close()

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

# Helper functions remain unchanged


# Helper Functions
def get_task_status(conn, task_id):
    c = conn.cursor()
    c.execute("SELECT completed, due_date FROM tasks WHERE task_id=?", (task_id,))
    completed, due_date = c.fetchone()
    
    if completed:
        return "completed"
    
    due_date = datetime.date.fromisoformat(due_date)
    if due_date < datetime.date.today():
        return "offtrack"
    
    c.execute('''
        SELECT COUNT(*) FROM task_link
        WHERE task_id = ? AND pre_task_id IN (
            SELECT task_id FROM tasks WHERE completed = 0
        )
    ''', (task_id,))
    return "offtrack" if c.fetchone()[0] > 0 else "ontrack"

def get_group_status(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=0 AND due_date < date('now')", (group_id,))
    if c.fetchone()[0] > 0: return "offtrack"
    
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=0", (group_id,))
    if c.fetchone()[0] > 0: return "ontrack"
    
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    return "completed" if c.fetchone()[0] > 0 else "inactive"

def get_status_badge(status):
    style = "border-radius:9px; padding:0 7px; font-size:13px; color:white;"
    colors = {
        "offtrack": "#e74c3c", 
        "ontrack": "#f1c40f",
        "completed": "#2ecc71",
        "inactive": "#95a5a6"
    }
    return f'<span style="{style} background-color:{colors[status]}">{status.title()}</span>'

def get_task_count(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=1", (group_id,))
    completed = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    return completed, c.fetchone()[0]
