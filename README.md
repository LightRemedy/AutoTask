# AutoTask V2 🗂️

AutoTask is a task and group scheduling app built with Streamlit. It features:

- 📅 Calendar & list views
- ✅ Task completion & overdue tracking
- 🧱 Prerequisite task logic
- 🗂️ Group management & templates
- 👤 Profile and account updates
- 🔐 Login / register functionality

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the Streamlit app
streamlit run app.py
```

---

## 🗂️ Project Structure

```
autotaskv2/
├── app.py             # Main launcher
├── core/              # DB and authentication logic
├── modules/           # Feature pages (dashboard, groups, tasks...)
├── utils/             # Shared tools
├── assets/            # Images and logo
├── .streamlit/        # Configs
├── task_manager.db    # SQLite file (auto-generated)
└── requirements.txt   # Dependencies
```

---

## 👨‍💻 Tech Stack

- Python 3.9+
- Streamlit
- SQLite (built-in)
