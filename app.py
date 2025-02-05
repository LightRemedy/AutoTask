# app.py
import streamlit as st
import datetime
from db import get_connection, create_tables, insert_presets
from auth import login, register
from tasks import get_tasks_by_template, mark_task_complete, check_notifications

# Initialize database and insert presets
conn = get_connection()
create_tables(conn)
insert_presets(conn)

# User Authentication
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("Login")
    auth_mode = st.radio("Select Option", ("Login", "Register"))
    if auth_mode == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login(username, password):
                st.success("Logged in successfully!")
            else:
                st.error("Invalid username or password.")
    else:
        st.title("Register")
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        full_name = st.text_input("Full Name")
        address = st.text_input("Address")
        gender = st.selectbox("Gender", ("Male", "Female", "Other"))
        contact = st.text_input("Contact")
        if st.button("Register"):
            register(new_username, new_password, full_name, address, gender, contact)
    st.stop()

# Mock Time Control Section
if "mock_now" not in st.session_state:
    st.session_state["mock_now"] = datetime.date.today()

st.sidebar.header("Time Control")
current_date = st.sidebar.date_input("Current Time", st.session_state["mock_now"])
st.session_state["mock_now"] = current_date

if st.sidebar.button("Fast Forward 1 Day"):
    st.session_state["mock_now"] += datetime.timedelta(days=1)
    st.sidebar.success(f"Time advanced to {st.session_state['mock_now']}")

st.sidebar.write("Current Mock Time:", st.session_state["mock_now"])

# Check and send notifications based on the mock time
check_notifications(st.session_state["mock_now"])

# Main Dashboard
st.title("Task Manager Dashboard")
st.sidebar.header("User Profile")
st.sidebar.write("Username:", st.session_state.get("username", ""))

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

st.subheader("Overdue Tasks")
today_str = st.session_state["mock_now"].strftime('%Y-%m-%d')
c.execute(
    "SELECT task_id, task_name, due_date FROM tasks WHERE due_date < ? AND completed=0", 
    (today_str,)
)
overdue_tasks = c.fetchall()
if overdue_tasks:
    for task in overdue_tasks:
        task_id, task_name, due_date = task
        st.error(f"Overdue: {task_name} (Due: {due_date})")
else:
    st.success("No overdue tasks.")
