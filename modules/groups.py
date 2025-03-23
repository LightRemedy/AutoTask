#modules/groups.py
import streamlit as st
import datetime
from core.database import get_connection
from utils.status_helpers import get_group_status, get_status_badge, get_task_completion_count


def show_group_page():
    st.title("🗂️ Task Groups")
    username = st.session_state.get("username")
    conn = get_connection()
    c = conn.cursor()

    _handle_modals()

    with st.expander("➕ Add New Task Group", expanded=False):
        group_type = st.radio("Group Type", ("Create New", "Import Template"), horizontal=True)
        group_name = st.text_input("Group Name*")
        colour = st.color_picker("Group Colour", "#8E44AD")
        remarks = st.text_area("Remarks")

        is_template = False
        selected_template, new_start_date = None, None

        if group_type == "Import Template":
            c.execute("SELECT group_id, group_name FROM groups WHERE isTemplate = 1")
            templates = c.fetchall()
            if templates:
                selected_template = st.selectbox(
                    "Select Template",
                    options=[t[0] for t in templates],
                    format_func=lambda x: next(t[1] for t in templates if t[0] == x)
                )
                new_start_date = st.date_input("Project Start Date")
            else:
                st.warning("No template groups available.")

        if group_type == "Create New":
            is_template = st.checkbox("Mark as Template Group")

        if st.button("Create Group"):
            try:
                c.execute("""
                    INSERT INTO groups (group_name, color, remarks, isTemplate, created_by)
                    VALUES (?, ?, ?, ?, ?)
                """, (group_name, colour, remarks, is_template, username))
                new_group_id = c.lastrowid

                if group_type == "Import Template" and selected_template and new_start_date:
                    _import_template_tasks(c, selected_template, new_group_id, new_start_date, username)

                conn.commit()
                st.success(f"Group '{group_name}' created successfully!")
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(f"Failed to create group: {e}")

    st.subheader("📋 Your Groups")
    c.execute("SELECT group_id, group_name, color, remarks, isTemplate FROM groups WHERE created_by=?", (username,))
    groups = c.fetchall()

    if groups:
        for group in groups:
            _render_group_card(conn, group)
    else:
        st.info("No groups found. Please create one above.")

    conn.close()


def _render_group_card(conn, group):
    group_id, name, colour, remarks, is_template = group
    st.markdown(f"""
        <style>
            .circle-{group_id} {{
                position: absolute; top: -5px; left: -5px;
                width: 15px; height: 15px;
                border-radius: 50%;
                background-color: {colour};
            }}
            .group-box {{
                position: relative; padding-left: 20px;
                display: flex; align-items: center; gap: 1rem;
            }}
        </style>
        <div class="circle-{group_id}"></div>
        <div class="group-box">
    """, unsafe_allow_html=True)

    cols = st.columns([4, 1, 1, 1])
    with cols[0]:
        status = get_group_status(conn, group_id)
        st.markdown(f"**{'📁 ' if is_template else ''}{name}** {get_status_badge(status)}", unsafe_allow_html=True)
        done, total = get_task_completion_count(conn, group_id)
        st.caption(f"Tasks: {done}/{total} completed")

    with cols[1]:
        if st.button("👁️", key=f"view_{group_id}"):
            st.session_state.current_page = "Group Details"
            st.session_state.current_view_group = group_id
            st.rerun()

    with cols[2]:
        if st.button("✏️", key=f"edit_{group_id}"):
            st.session_state.edit_group = (group_id, name, colour, remarks, is_template)
            st.rerun()

    with cols[3]:
        if st.button("🗑️", key=f"del_{group_id}"):
            st.session_state.delete_group = group_id
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def _import_template_tasks(cursor, template_id, new_group_id, start_date, username):
    cursor.execute("SELECT task_name, due_date, notification_days FROM tasks WHERE group_id=?", (template_id,))
    tasks = cursor.fetchall()

    cursor.execute("SELECT MIN(due_date) FROM tasks WHERE group_id=?", (template_id,))
    base_date = datetime.datetime.strptime(cursor.fetchone()[0], "%Y-%m-%d").date()
    offset = (start_date - base_date).days

    for name, due, notify in tasks:
        new_due = datetime.datetime.strptime(due, "%Y-%m-%d").date() + datetime.timedelta(days=offset)
        cursor.execute("""
            INSERT INTO tasks (group_id, task_name, due_date, notification_days, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (new_group_id, name, new_due.isoformat(), notify, username))


def _handle_modals():
    if "delete_group" in st.session_state:
        _delete_group_modal()
    elif "edit_group" in st.session_state:
        _edit_group_modal()
        
def show_group_details():
    group_id = st.session_state.get("current_view_group")
    if not group_id:
        st.error("No group selected.")
        return

    conn = get_connection()
    c = conn.cursor()

    st.title("📦 Group Details")

    c.execute("SELECT group_name, color, remarks, isTemplate FROM groups WHERE group_id=?", (group_id,))
    group = c.fetchone()

    if not group:
        st.error("Group not found.")
        return

    name, colour, remarks, is_template = group

    st.markdown(f"### {'📁 ' if is_template else ''}{name}")
    st.markdown(f"**Colour:** {colour}")
    st.markdown(f"**Remarks:** {remarks or 'No remarks'}")

    st.divider()
    st.subheader("📋 Tasks in This Group")
    c.execute("""
        SELECT task_name, due_date, completed
        FROM tasks WHERE group_id=?
        ORDER BY due_date
    """, (group_id,))
    tasks = c.fetchall()

    if not tasks:
        st.info("This group has no tasks.")
    else:
        for task_name, due_date, completed in tasks:
            st.markdown(f"- {'✅' if completed else '🔄'} **{task_name}** (Due: {due_date})")

    if st.button("🔙 Back to Groups"):
        st.session_state.current_page = "Group Page"
        st.session_state.pop("current_view_group", None)
        st.rerun()

    conn.close()



@st.dialog("Edit Group")
def _edit_group_modal():
    group_id, name, colour, remarks, is_template = st.session_state.edit_group
    conn = get_connection()
    try:
        with st.form(key=f"edit_group_form_{group_id}"):
            new_name = st.text_input("Group Name", value=name)
            new_colour = st.color_picker("Group Colour", value=colour)
            new_remarks = st.text_area("Remarks", value=remarks)
            new_template = st.checkbox("Template Group", value=is_template)

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save"):
                    c = conn.cursor()
                    c.execute("""
                        UPDATE groups SET group_name=?, color=?, remarks=?, isTemplate=?
                        WHERE group_id=?
                    """, (new_name, new_colour, new_remarks, new_template, group_id))
                    conn.commit()
                    st.session_state.pop("edit_group")
                    st.rerun()

            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.pop("edit_group")
                    st.rerun()
    finally:
        conn.close()


@st.dialog("Confirm Deletion")
def _delete_group_modal():
    group_id = st.session_state.delete_group
    st.warning("This will permanently delete the group and its tasks.")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Confirm"):
            conn = get_connection()
            try:
                c = conn.cursor()
                c.execute("DELETE FROM tasks WHERE group_id = ?", (group_id,))
                c.execute("DELETE FROM groups WHERE group_id = ?", (group_id,))
                conn.commit()
                st.session_state.pop("delete_group")
                st.rerun()
            finally:
                conn.close()

    with col2:
        if st.button("❌ Cancel"):
            st.session_state.pop("delete_group")
            st.rerun()
