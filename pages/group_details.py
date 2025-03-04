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

    # Get group details
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

    # Status Section at Top
    st.subheader("📊 Group Status")
    status = get_group_status(conn, group_id)
    st.markdown(f"**Current Status:** {get_status_badge(status)}", unsafe_allow_html=True)

    # Add Task Section
    with st.expander("➕ Add New Task", expanded=False):
        with st.form("add_task_form"):
            # Form fields
            task_name = st.text_input("Task Name*", max_chars=100)
            task_remarks = st.text_area("Remarks", max_chars=200)
            due_date = st.date_input("Due Date*", min_value=datetime.date.today())
            notification_days = st.selectbox(
                "Notification Days*",
                options=[0, 1, 3, 7, 14],
                format_func=lambda x: f"{x} days before" if x > 0 else "On due date"
            )
            
            # Get eligible prerequisites
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
                if not task_name or not due_date:
                    st.error("Required fields marked with *")
                else:
                    try:
                        # Insert task
                        c.execute('''
                            INSERT INTO tasks 
                            (task_name, remarks, due_date, notification_days, group_id, created_by)
                            VALUES (?,?,?,?,?,?)
                        ''', (task_name, task_remarks, due_date, notification_days, 
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
                        conn.rollback()
                        st.error(f"Error creating task: {str(e)}")

    # Tasks List Section
    st.subheader("📋 Tasks")
    c.execute('''
        SELECT t.task_id, t.task_name, t.due_date, t.completed, t.remarks,
               GROUP_CONCAT(p.task_name, ', ') as prerequisites
        FROM tasks t
        LEFT JOIN task_link tl ON t.task_id = tl.task_id
        LEFT JOIN tasks p ON tl.pre_task_id = p.task_id
        WHERE t.group_id = ?
        GROUP BY t.task_id
        ORDER BY t.due_date
    ''', (group_id,))
    tasks = c.fetchall()

    if tasks:
        # Progress bar
        completed, total = get_task_count(conn, group_id)
        st.progress(completed/total if total > 0 else 0)
        st.caption(f"Completed: {completed}/{total} tasks")

        for task in tasks:
            task_id, name, due_date, completed, remarks, prerequisites = task
            with st.container(border=True):
                cols = st.columns([6, 1, 1, 1, 1])
                
                # Status determination
                today = datetime.date.today()
                due = datetime.date.fromisoformat(due_date)
                status = "✅ Completed" if completed else ""
                
                if not completed:
                    if due < today:
                        status = "⚠️ Overdue"
                    else:
                        # Check prerequisites
                        c.execute('''
                            SELECT COUNT(*) FROM task_link
                            WHERE task_id = ? AND pre_task_id IN (
                                SELECT task_id FROM tasks WHERE completed = 0
                            )
                        ''', (task_id,))
                        incomplete_prereqs = c.fetchone()[0]
                        if incomplete_prereqs > 0:
                            status = "⛔ Prereqs Incomplete"
                        else:
                            status = "⏳ Pending"

                with cols[0]:
                    st.markdown(f"**{name}**  \n{status}")
                    st.caption(f"Due: {due_date}")
                    if prerequisites:
                        st.caption(f"Requires: {prerequisites}")

                # Action buttons
                with cols[1]:
                    if not completed and status != "⛔ Prereqs Incomplete":
                        if st.button("✅", key=f"complete_{task_id}"):
                            c.execute("UPDATE tasks SET completed=1 WHERE task_id=?", (task_id,))
                            conn.commit()
                            st.rerun()
                
                with cols[2]:
                    if st.button("✏️", key=f"edit_{task_id}"):
                        st.session_state.edit_task = task_id
                
                with cols[3]:
                    if st.button("🗑️", key=f"del_{task_id}"):
                        c.execute("DELETE FROM tasks WHERE task_id=?", (task_id,))
                        c.execute("DELETE FROM task_link WHERE task_id=?", (task_id,))
                        conn.commit()
                        st.rerun()
                
                with cols[4]:
                    if st.button("📄", key=f"remarks_{task_id}"):
                        with st.popover("Task Remarks"):
                            st.write(remarks or "No remarks available")

    else:
        st.info("No tasks found in this group")

    conn.close()

# Helper functions from group_page.py
def get_group_status(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=0 AND due_date < date('now')", (group_id,))
    overdue = c.fetchone()[0]
    if overdue > 0: return "offtrack"

    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=0", (group_id,))
    pending = c.fetchone()[0]
    if pending > 0: return "ontrack"

    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    total = c.fetchone()[0]
    return "completed" if total > 0 else "inactive"

def get_status_badge(status):
    style = "border-radius:9px; padding:0 7px; font-size:13px; color:white;"
    colors = {
        "offtrack": "#e74c3c", 
        "ontrack": "#f1c40f",
        "completed": "#2ecc71",
        "inactive": "#95a5a6"
    }
    labels = {
        "offtrack": "Off Track",
        "ontrack": "On Track",
        "completed": "Completed",
        "inactive": "Inactive"
    }
    return f'<span style="{style} background-color:{colors[status]}">{labels[status]}</span>'

def get_task_count(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=1", (group_id,))
    completed = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    total = c.fetchone()[0]
    return completed, total
