"""网上阅卷Web系统 - 启动入口"""
import uvicorn
from app import create_app

app = create_app()

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=80)
