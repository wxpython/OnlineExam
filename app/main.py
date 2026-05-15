"""主业务路由 - 任务管理"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.models import get_session, MarkTask
from app.task_runner import run_mark_task, stop_task, get_running_tasks

router = APIRouter()


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def login_required(request: Request):
    if 'user_id' not in request.session:
        raise HTTPException(status_code=303, headers={'Location': '/login'})


def get_templates(request: Request):
    return request.app.state.templates


def get_flash_messages(request: Request):
    msgs = request.session.pop('flash_messages', [])
    return msgs


@router.get('/', response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    login_required(request)
    templates = get_templates(request)
    user_id = request.session['user_id']
    tasks = db.query(MarkTask).filter_by(user_id=user_id).order_by(MarkTask.created_at.desc()).all()
    running_ids = get_running_tasks()
    flash_messages = get_flash_messages(request)
    return templates.TemplateResponse(request, 'index.html', {
        'tasks': tasks, 'running_ids': running_ids,
        'flash_messages': flash_messages, 'session': request.session
    })


@router.get('/task/create', response_class=HTMLResponse)
@router.post('/task/create', response_class=HTMLResponse)
async def create_task(request: Request, db: Session = Depends(get_db)):
    login_required(request)
    templates = get_templates(request)
    if request.method == 'POST':
        form = await request.form()
        task_name = form.get('task_name', '').strip()
        first_accounts = form.get('first_accounts', '').strip()
        second_account = form.get('second_account', '').strip()
        mark_password = form.get('mark_password', '').strip()
        second_password = form.get('second_password', '').strip()
        question_name = form.get('question_name', '').strip()
        server_url = form.get('server_url', 'http://xyyj.jsleascent.com').strip()
        refresh_delay = form.get('refresh_delay', '3').strip()

        if not all([task_name, first_accounts, second_account, mark_password, second_password, question_name]):
            return templates.TemplateResponse(request, 'create_task.html', {
                'flash_messages': [('error', '请填写所有必填项')],
                'session': request.session
            })

        task = MarkTask(
            user_id=request.session['user_id'],
            task_name=task_name,
            first_accounts=first_accounts,
            second_account=second_account,
            mark_password=mark_password,
            second_password=second_password,
            question_name=question_name,
            server_url=server_url,
            refresh_delay=int(refresh_delay) if refresh_delay.isdigit() else 2,
        )
        db.add(task)
        db.commit()

        request.session['flash_messages'] = [('success', '任务创建成功')]
        return RedirectResponse(url='/', status_code=303)

    flash_messages = get_flash_messages(request)
    return templates.TemplateResponse(request, 'create_task.html', {
        'flash_messages': flash_messages, 'session': request.session
    })


@router.get('/task/{task_id}', response_class=HTMLResponse)
async def task_detail(task_id: int, request: Request, db: Session = Depends(get_db)):
    login_required(request)
    templates = get_templates(request)
    task = db.query(MarkTask).filter_by(id=task_id, user_id=request.session['user_id']).first()
    if not task:
        raise HTTPException(status_code=404)
    running_ids = get_running_tasks()
    flash_messages = get_flash_messages(request)
    return templates.TemplateResponse(request, 'task_detail.html', {
        'task': task, 'is_running': task_id in running_ids,
        'flash_messages': flash_messages, 'session': request.session
    })


@router.post('/task/{task_id}/start')
async def start_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    login_required(request)
    task = db.query(MarkTask).filter_by(id=task_id, user_id=request.session['user_id']).first()
    if not task:
        raise HTTPException(status_code=404)

    if task.status == 'running':
        return JSONResponse({'error': '任务已在运行中'}, status_code=400)

    # 重置任务状态
    task.status = 'pending'
    task.progress = 0
    task.marked_papers = 0
    task.log_text = ''
    db.commit()

    run_mark_task(request.app, task_id)
    return JSONResponse({'status': 'started'})


@router.post('/task/{task_id}/stop')
async def stop_task_route(task_id: int, request: Request, db: Session = Depends(get_db)):
    login_required(request)
    task = db.query(MarkTask).filter_by(id=task_id, user_id=request.session['user_id']).first()
    if not task:
        raise HTTPException(status_code=404)

    if task.status not in ('running', 'pending'):
        return JSONResponse({'status': task.status})

    if stop_task(task_id):
        task.status = 'stopped'
        db.commit()
        return JSONResponse({'status': 'stopped'})

    db.refresh(task)
    if task.status in ('running', 'pending'):
        task.status = 'stopped'
        db.commit()
    return JSONResponse({'status': task.status})


@router.post('/task/{task_id}/delete')
async def delete_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    login_required(request)
    task = db.query(MarkTask).filter_by(id=task_id, user_id=request.session['user_id']).first()
    if not task:
        raise HTTPException(status_code=404)

    if task.status == 'running':
        return JSONResponse({'error': '请先停止任务再删除'}, status_code=400)

    db.delete(task)
    db.commit()
    return JSONResponse({'status': 'deleted'})


@router.get('/api/task/{task_id}/status')
async def task_status_api(task_id: int, request: Request, db: Session = Depends(get_db)):
    login_required(request)
    task = db.query(MarkTask).filter_by(id=task_id, user_id=request.session['user_id']).first()
    if not task:
        raise HTTPException(status_code=404)
    db.refresh(task)
    return JSONResponse({
        'status': task.status,
        'progress': task.progress,
        'total_papers': task.total_papers,
        'marked_papers': task.marked_papers,
        'log': task.log_text,
    })
