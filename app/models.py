"""数据库模型 - 支持多用户数据隔离"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from passlib.context import CryptContext
import hashlib

Base = declarative_base()
# 支持 pbkdf2_sha256（werkzeug 格式）和 bcrypt，兼容旧数据库
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")

engine = None
SessionLocal = None


def init_db(database_url: str):
    """初始化数据库引擎和会话工厂"""
    global engine, SessionLocal
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """获取数据库会话"""
    return SessionLocal()


class User(Base):
    """系统用户表 - 每个用户独立的数据空间"""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联的阅卷任务
    tasks = relationship('MarkTask', backref='user', lazy='dynamic',
                         cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = pwd_context.hash(password)

    def check_password(self, password):
        return pwd_context.verify(password, self.password_hash)


class MarkTask(Base):
    """阅卷任务表 - 每个用户可创建多个任务，数据隔离"""
    __tablename__ = 'mark_tasks'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # 任务配置
    task_name = Column(String(200), nullable=False)
    first_accounts = Column(Text, nullable=False)   # 一评账号，逗号分隔
    second_account = Column(String(100), nullable=False)  # 二评账号
    mark_password = Column(String(200), nullable=False)   # 一评账号密码
    second_password = Column(String(200), nullable=False)  # 二评账号密码
    question_name = Column(String(50), nullable=False)    # 试题名称
    server_url = Column(String(300), default='http://xyyj.jsleascent.com')
    refresh_delay = Column(Integer, default=3)   # 刷新任务时的延迟（秒）

    # 任务状态
    status = Column(String(20), default='pending')  # pending/running/completed/failed/stopped
    progress = Column(Integer, default=0)            # 进度百分比
    total_papers = Column(Integer, default=0)        # 总试卷数
    marked_papers = Column(Integer, default=0)       # 已批改数
    log_text = Column(Text, default='')              # 运行日志

    # 阅卷结果数据 (JSON格式存储)
    result_data = Column(Text, default='')

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)

    def append_log(self, msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text = self.log_text + f"[{timestamp}] {msg}\n"
        # 保留最近500行日志
        lines = self.log_text.split('\n')
        if len(lines) > 500:
            self.log_text = '\n'.join(lines[-500:])
