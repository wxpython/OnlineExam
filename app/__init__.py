"""FastAPI应用工厂"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.models import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="网上阅卷系统")

    # 配置
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    database_url = 'sqlite:///' + os.path.join(base_dir, 'data.db')
    secret_key = os.environ.get('SECRET_KEY', 'online-mark-secret-key-2024')

    # 初始化数据库
    init_db(database_url)

    # Session中间件
    app.add_middleware(SessionMiddleware, secret_key=secret_key)

    # 静态文件和模板
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    app.mount('/static', StaticFiles(directory=static_dir), name='static')
    templates = Jinja2Templates(directory=templates_dir)
    app.state.templates = templates

    # 注册路由
    from app.auth import router as auth_router
    from app.main import router as main_router
    app.include_router(auth_router)
    app.include_router(main_router)

    return app
