"""用户认证路由"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.models import get_session, User

router = APIRouter()


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def get_templates(request: Request):
    return request.app.state.templates


@router.get('/login', response_class=HTMLResponse)
@router.post('/login', response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    templates = get_templates(request)
    if request.method == 'POST':
        form = await request.form()
        username = form.get('username', '').strip()
        password = form.get('password', '')
        if not username or not password:
            return templates.TemplateResponse(request, 'login.html', {
                'flash_messages': [('error', '请输入用户名和密码')],
                'session': request.session
            })

        user = db.query(User).filter_by(username=username).first()
        if user and user.check_password(password):
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            request.session['flash_messages'] = [('success', '登录成功')]
            return RedirectResponse(url='/', status_code=303)
        else:
            return templates.TemplateResponse(request, 'login.html', {
                'flash_messages': [('error', '用户名或密码错误')],
                'session': request.session
            })

    return templates.TemplateResponse(request, 'login.html', {
        'flash_messages': [], 'session': request.session
    })


@router.get('/register', response_class=HTMLResponse)
@router.post('/register', response_class=HTMLResponse)
async def register(request: Request, db: Session = Depends(get_db)):
    templates = get_templates(request)
    if request.method == 'POST':
        form = await request.form()
        username = form.get('username', '').strip()
        password = form.get('password', '')
        password2 = form.get('password2', '')

        if not username or not password:
            return templates.TemplateResponse(request, 'register.html', {
                'flash_messages': [('error', '请输入用户名和密码')],
                'session': request.session
            })
        if password != password2:
            return templates.TemplateResponse(request, 'register.html', {
                'flash_messages': [('error', '两次密码不一致')],
                'session': request.session
            })

        if db.query(User).filter_by(username=username).first():
            return templates.TemplateResponse(request, 'register.html', {
                'flash_messages': [('error', '用户名已存在')],
                'session': request.session
            })

        user = User(username=username)
        user.set_password(password)
        db.add(user)
        db.commit()

        request.session['flash_messages'] = [('success', '注册成功，请登录')]
        return RedirectResponse(url='/login', status_code=303)

    return templates.TemplateResponse(request, 'register.html', {
        'flash_messages': [], 'session': request.session
    })


@router.get('/logout')
async def logout(request: Request):
    request.session.pop('user_id', None)
    request.session.pop('username', None)
    request.session['flash_messages'] = [('success', '已退出登录')]
    return RedirectResponse(url='/login', status_code=303)
