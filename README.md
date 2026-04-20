

# ReadPaper

在线答题辅助系统 | Online Exam Assistant

## 项目简介

ReadPaper 是一个基于 FastAPI 构建的在线答题辅助系统，支持用户注册登录、创建和管理答题任务、自动化在线答题等功能。

## 技术栈

- **后端框架**: FastAPI
- **数据库**: SQLite (SQLAlchemy)
- **前端**: HTML + Bootstrap 5
- **任务调度**: Python threading

## 功能特性

### 用户管理
- 用户注册与登录
- 会话管理
- 权限控制

### 任务管理
- 创建答题任务（支持配置课程ID、题目ID等参数）
- 启动/停止任务
- 删除任务
- 实时任务进度查看
- 任务日志输出

### 核心功能
- 在线答题自动化（OnlineMark）
- 多题目自动获取
- 答题进度实时跟踪

## 项目结构

```
.
├── app/
│   ├── __init__.py       # 应用入口
│   ├── auth.py           # 认证模块
│   ├── main.py           # 主路由和业务逻辑
│   ├── models.py         # 数据模型
│   ├── online_mark.py    # 在线答题核心类
│   ├── task_runner.py    # 任务运行器
│   └── templates/        # HTML模板
│       ├── base.html
│       ├── create_task.html
│       ├── index.html
│       ├── login.html
│       ├── register.html
│       └── task_detail.html
├── onlineExam3.0.py      # 独立答题脚本
├── requirements.txt      # 依赖
├── run.py               # 启动文件
└── data.db              # SQLite数据库
```

## 安装部署

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python run.py
```

服务将在 `http://localhost:8000` 启动。

## 使用指南

### 1. 注册登录
访问系统首页，点击注册创建账号，然后登录系统。

### 2. 创建任务
登录后，点击"创建任务"，填写以下参数：
- 目标网站URL
- 用户名/密码
- 课程ID
- 题目ID范围

### 3. 执行任务
创建任务后，点击"开始"按钮启动自动化答题，系统将实时显示答题进度和日志。

## 依赖说明

主要依赖包括：
- fastapi
- sqlalchemy
- uvicorn
- jinja2
- python-multipart
- pydantic

详见 `requirements.txt`

## 注意事项

1. 请确保目标网站支持自动化操作
2. 合理设置请求间隔，避免对目标网站造成压力
3. 妥善保管用户凭证