# AutoTask 🗂️

Welcome to AutoTask - Your Intelligent Task and Group Scheduling Solution

## 📖 Overview

AutoTask is a sophisticated task and group scheduling application built with Streamlit. It's designed to streamline your workflow and enhance productivity through intelligent task management.

### ✨ Key Features

- 📅 **Calendar & List Views**
  - Visualise your tasks in multiple formats
  - Toggle between calendar and list views for optimal planning
  - Intuitive interface for quick task overview

- ✅ **Task Management**
  - Track task completion status
  - Automated overdue task notifications
  - Priority-based task organisation

- 🧱 **Smart Prerequisites**
  - Set up task dependencies
  - Logical task sequencing
  - Automated prerequisite tracking

- 🗂️ **Group Management**
  - Create and manage task groups
  - Customisable group templates
  - Collaborative task sharing

- 👤 **User Profiles**
  - Personalised account settings
  - Profile customisation options
  - Activity tracking

- 🔐 **Security Features**
  - Secure login system
  - User registration
  - Data protection

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/LightRemedy/AutoTask.git
   cd autotask
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch the application:
   ```bash
   streamlit run app.py
   ```

4. Web Demo(optional)
   ```bash
   https://autotask.streamlit.app/
   ```


## 🗂️ Project Structure

```
autotaskv2/
├── app.py             # Main application entry point
├── core/              # Core functionality
│   ├── database      # Database operations
│   └── auth          # Authentication services
├── modules/          # Feature modules
│   ├── dashboard     # Main dashboard
│   ├── groups        # Group management
│   └── tasks         # Task operations
├── utils/            # Utility functions
├── assets/           # Static resources
├── .streamlit/       # Streamlit configuration
├── task_manager.db   # SQLite database (auto-generated)
└── requirements.txt  # Project dependencies
```

## 🛠️ Technical Stack

- **Frontend Framework**: Streamlit
- **Backend**: Python 3.9+
- **Database**: SQLite (built-in)

## 🤝 Contributing

We welcome contributions! Please feel free to submit a Pull Request.

## 🆘 Support

If you encounter any issues or need assistance:
1. Check the documentation
2. Submit an issue on GitHub
3. Contact the development team

## 🙏 Acknowledgements

- Streamlit community
- All contributors and users

---

*Built with ❤️ using Streamlit and Python*

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the Streamlit app
streamlit run app.py
```

---

## 🗂️ Project Structure

```
autotask/
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
