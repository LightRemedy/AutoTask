import streamlit as st
from db import get_connection
import datetime

def show_group_page():
    st.title("📦 Task Groups")
    username = st.session_state.get("username")
    conn = get_connection()
    c = conn.cursor()

    # Handle modals first
    handle_modals()

    # Add Group Section
    with st.expander("➕ Add New Task Group", expanded=True):
        group_type = st.radio(
            "Group Type", 
            ("Create New", "Import Template"),
            horizontal=True,
            key="grp_type"
        )
        
        group_name = st.text_input("Group Name*")
        color = st.color_picker("Group Color", "#8E44AD")
        remarks = st.text_area("Remarks")
        
        selected_template = None
        new_start_date = None
        
        if group_type == "Import Template":
            c.execute("SELECT group_id, group_name FROM groups WHERE isTemplate=1")
            templates = c.fetchall()
            
            if templates:
                selected_template = st.selectbox(
                    "Select Template",
                    options=[t[0] for t in templates],
                    format_func=lambda x: next(t[1] for t in templates if t[0] == x)
                )
                new_start_date = st.date_input("Project Start Date")
            else:
                st.warning("No templates available. Create a template group first!")

        is_template = st.checkbox("Mark as Template Group") if group_type == "Create New" else False

        if st.button("Create Group"):
            try:
                c.execute(
                    "INSERT INTO groups (group_name, color, remarks, isTemplate, created_by) "
                    "VALUES (?,?,?,?,?)",
                    (group_name, color, remarks, is_template, username)
                )
                new_group_id = c.lastrowid

                if group_type == "Import Template" and selected_template and new_start_date:
                    c.execute("SELECT task_name, due_date, notification_days FROM tasks WHERE group_id=?", (selected_template,))
                    tasks = c.fetchall()
                    
                    c.execute("SELECT MIN(due_date) FROM tasks WHERE group_id=?", (selected_template,))
                    template_start = datetime.datetime.strptime(c.fetchone()[0], "%Y-%m-%d").date()
                    date_offset = (new_start_date - template_start).days
                    
                    for task in tasks:
                        task_name, due_date, notif_days = task
                        original_date = datetime.datetime.strptime(due_date, "%Y-%m-%d").date()
                        new_date = original_date + datetime.timedelta(days=date_offset)
                        
                        c.execute(
                            "INSERT INTO tasks (group_id, task_name, due_date, notification_days, created_by) "
                            "VALUES (?,?,?,?,?)",
                            (new_group_id, task_name, new_date, notif_days, username)
                        )

                conn.commit()
                st.success(f"Group '{group_name}' created!")
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(f"Error: {str(e)}")
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

                cols = st.columns([4, 1, 1, 1])
                with cols[0]:
                    status = get_group_status(conn, group_id)
                    st.markdown(f"**{template_badge}{group_name}** {get_status_badge(status)}", unsafe_allow_html=True)
                    completed, total = get_task_count(conn, group_id)
                    st.caption(f"Tasks: {completed}/{total} completed")
                
                with cols[1]:
                    if st.button("👁️", key=f"view_{group_id}"):
                        st.session_state.current_page = "Group Details"  # ADD THIS LINE
                        st.session_state.current_view_group = group_id
                        st.rerun()
                        
                with cols[2]:
                    if st.button("✏️", key=f"edit_{group_id}"):
                        st.session_state.edit_group = (group_id, group_name, color, remarks, is_template)
                        st.rerun()
                        
                with cols[3]:
                    if st.button("🗑️", key=f"del_{group_id}"):
                        st.session_state.delete_group = group_id
                        st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No task groups found. Add one using the form above!")
    
    conn.close()

def handle_modals():
    if "delete_group" in st.session_state:
        delete_group_modal()
    elif "edit_group" in st.session_state:
        edit_group_modal()

@st.dialog("Edit Group", width="large")
def edit_group_modal():
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
                    c = conn.cursor()
                    c.execute('''
                        UPDATE groups 
                        SET group_name=?, color=?, remarks=?, isTemplate=?
                        WHERE group_id=?
                    ''', (new_name, new_color, new_remarks, new_template, group_id))
                    conn.commit()
                    st.session_state.pop("edit_group", None)
                    st.rerun()
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.pop("edit_group", None)
                    st.rerun()
    finally:
        conn.close()

@st.dialog("Confirm Deletion", width="small")
def delete_group_modal():
    group_id = st.session_state.delete_group
    st.warning("This will permanently delete the group and all its tasks!")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Confirm"):
            conn = get_connection()
            try:
                c = conn.cursor()
                c.execute("DELETE FROM tasks WHERE group_id=?", (group_id,))
                c.execute("DELETE FROM groups WHERE group_id=?", (group_id,))
                conn.commit()
                st.session_state.pop("delete_group", None)
                st.rerun()
            finally:
                conn.close()
    
    with col2:
        if st.button("❌ Cancel"):
            st.session_state.pop("delete_group", None)
            st.rerun()

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
    return f'<span style="{style} background-color:{colors[status]}">{status.title()}</span>'

def get_task_count(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=1", (group_id,))
    completed = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    total = c.fetchone()[0]
    return completed, total
