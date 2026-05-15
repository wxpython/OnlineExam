"""网上阅卷Web系统 - 启动入口"""
import os
import uvicorn
from app import create_app

app = create_app()

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ssl_cert = os.path.join(base_dir, 'ssl', 'fullchain.cer')
    ssl_key = os.path.join(base_dir, 'ssl', '221400.xyz.key')
    if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        uvicorn.run(app, host='0.0.0.0', port=443, ssl_certfile=ssl_cert, ssl_keyfile=ssl_key)
    else:
        uvicorn.run(app, host='0.0.0.0', port=80)
