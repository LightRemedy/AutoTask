import streamlit as st
from db import get_connection

### Overdue Tasks Module
# This module handles the display and management of overdue tasks
# Provides quick access to view and complete tasks that are past their due date

def show_overdue_tasks():
    ### Main function to display overdue tasks
    # Shows all incomplete tasks with due dates in the past
    # Provides option to mark tasks as complete
    
    st.title("⚠️ Overdue Tasks")
    
    conn = get_connection()
    c = conn.cursor()
    
    ### Fetch Overdue Tasks
    # Retrieves all incomplete tasks where due date is earlier than current date
    c.execute("""
        SELECT task_id, task_name, due_date 
        FROM tasks 
        WHERE due_date < date('now') 
        AND completed = 0
    """)
    
    overdue_tasks = c.fetchall()
    
    ### Display Logic
    # Shows success message if no overdue tasks
    # Otherwise displays each task with completion button
    if not overdue_tasks:
        st.success("🎉 No overdue tasks!")
        return
        
    ### Task Display Loop
    # Creates a container for each overdue task showing:
    # * Task name
    # * Due date
    # * Mark complete button
    for task in overdue_tasks:
        task_id, task_name, due_date = task
        with st.container(border=True):
            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown(f"**{task_name}**")
                st.caption(f"Due: {due_date}")
            with cols[1]:
                if st.button("Mark Complete", key=f"complete_{task_id}"):
                    mark_task_complete(task_id)
                    st.rerun()

def mark_task_complete(task_id):
    ### Task Completion Handler
    # Updates the task's completion status in the database
    # Parameters:
    #   - task_id: The ID of the task to mark as complete
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE tasks SET completed = 1 WHERE task_id = ?", (task_id,))
    conn.commit()
