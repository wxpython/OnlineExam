# ReadPaper

Online Exam Assistant

## Project Overview

ReadPaper is an online exam assistant system built on FastAPI, supporting user registration and login, creation and management of exam tasks, and automated online answering.

## Technology Stack

- **Backend Framework**: FastAPI
- **Database**: SQLite (SQLAlchemy)
- **Frontend**: HTML + Bootstrap 5
- **Task Scheduling**: Python threading

## Features

### User Management
- User registration and login
- Session management
- Access control

### Task Management
- Create exam tasks (support configuration of course ID, question ID, etc.)
- Start/stop tasks
- Delete tasks
- Real-time task progress monitoring
- Task log output

### Core Functionality
- Automated online answering (OnlineMark)
- Automatic retrieval of multiple questions
- Real-time tracking of answering progress

## Project Structure

```
.
├── app/
│   ├── __init__.py       # Application entry
│   ├── auth.py           # Authentication module
│   ├── main.py           # Main routes and business logic
│   ├── models.py         # Data models
│   ├── online_mark.py    # Core class for online answering
│   ├── task_runner.py    # Task runner
│   └── templates/        # HTML templates
│       ├── base.html
│       ├── create_task.html
│       ├── index.html
│       ├── login.html
│       ├── register.html
│       └── task_detail.html
├── onlineExam3.0.py      # Standalone answering script
├── requirements.txt      # Dependencies
├── run.py                # Startup file
└── data.db               # SQLite database
```

## Installation & Deployment

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Service

```bash
python run.py
```

The service will be available at `http://localhost:8000`.

## Usage Guide

### 1. Register and Login
Visit the homepage, click "Register" to create an account, then log in.

### 2. Create a Task
After logging in, click "Create Task" and fill in the following parameters:
- Target website URL
- Username/Password
- Course ID
- Question ID range

### 3. Execute the Task
After creating the task, click the "Start" button to initiate automated answering. The system will display the answering progress and logs in real time.

## Dependencies

Primary dependencies include:
- fastapi
- sqlalchemy
- uvicorn
- jinja2
- python-multipart
- pydantic

See `requirements.txt` for details.

## Notes

1. Ensure the target website supports automated operations.
2. Set appropriate request intervals to avoid overloading the target website.
3. Safely store user credentials.