# pages/dashboard.py
import streamlit as st
from db import get_connection
from tasks import get_tasks_by_template, mark_task_complete

def show_dashboard():
    print("show_dashboard() function called") #debug
    st.write("Dashboard Page Loaded")  # This is critical for debugging
    st.title("Task Manager Dashboard")

    # Template selection (for simplicity, loading all templates)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT template_id, template_name FROM templates")
    templates = c.fetchall()
    template_options = {name: tid for tid, name in templates}
    selected_template = st.selectbox("Choose Template", list(template_options.keys()))

    st.subheader(f"Tasks for Template: {selected_template}")
    tasks = get_tasks_by_template(template_options[selected_template])
    for task in tasks:
        task_id, task_name, due_date, completed = task
        col1, col2, col3 = st.columns([6, 2, 2])
        with col1:
            if completed:
                st.markdown(f"~~{task_name}~~")
            else:
                st.write(task_name)
            st.caption("Due: " + due_date)
        with col2:
            if not completed:
                if st.button("Complete", key=f"complete_{task_id}"):
                    mark_task_complete(task_id)
                    st.experimental_rerun()
            else:
                st.write("Done")
        with col3:
            if st.button("Send Reminder", key=f"reminder_{task_id}"):
                st.info(f"Reminder sent for task: {task_name}")

if __name__ == "__main__": #only runs if calling script directly
    show_dashboard()
