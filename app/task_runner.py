"""异步任务执行器 - 在后台线程中执行阅卷任务"""
import threading
import json
import time
import subprocess
from datetime import datetime
from app.models import get_session, MarkTask
from app.online_mark import OnlineMark, getHost, merge_paper_data

# 全局任务管理: task_id -> OnlineMark 实例
_running_tasks = {}
_task_lock = threading.Lock()


def _ping_host(host, timeout=3):
    """检测host是否在线，host格式如 121.43.68.39:9090"""
    ip = host.split(':')[0]
    try:
        result = subprocess.run(
            ['ping', '-n', '1', '-w', str(timeout * 1000), ip],
            capture_output=True, timeout=timeout + 2
        )
        return result.returncode == 0
    except Exception:
        return False


def get_running_tasks():
    """获取当前正在运行的任务ID列表"""
    with _task_lock:
        return list(_running_tasks.keys())


def stop_task(task_id):
    """请求停止指定任务"""
    with _task_lock:
        if task_id in _running_tasks:
            _running_tasks[task_id].stop()
            return True
    return False


def run_mark_task(app, task_id):
    """在后台线程中启动阅卷任务"""
    thread = threading.Thread(
        target=_execute_task,
        args=(task_id,),
        daemon=True
    )
    thread.start()
    return True


def _execute_task(task_id):
    """执行阅卷任务的核心逻辑（在后台线程中运行）"""
    db = get_session()
    try:
        task = db.query(MarkTask).get(task_id)
        if not task:
            return

        # 更新任务状态
        task.status = 'running'
        task.started_at = datetime.utcnow()
        task.log_text = ''
        db.commit()

        def log(msg):
            task.append_log(msg)
            db.commit()
            db.refresh(task)

        try:
            # 解析配置
            first_accounts = [a.strip() for a in task.first_accounts.split(',') if a.strip()]
            second_account = task.second_account
            mark_pwd = task.mark_password
            second_pwd = task.second_password
            q_name = task.question_name

            log(f'任务开始: 一评账号 {len(first_accounts)} 个, 二评账号 {second_account}, 试题 {q_name}')

            # 获取可用服务器
            log(f'获取服务器列表: {task.server_url}')
            try:
                all_hosts = getHost(task.server_url)
            except Exception as e:
                log(f'获取服务器列表失败: {e}')
                task.status = 'failed'
                db.commit()
                return

            if not all_hosts:
                log('未找到可用服务器')
                task.status = 'failed'
                db.commit()
                return

            # ===== 第一阶段: 用一评账号获取已批改数据 =====
            all_paper_data = []
            host = ''

            for name in first_accounts:
                if task.status == 'stopped':
                    return

                found = False
                for h in all_hosts:
                    if not _ping_host(h):
                        log(f'服务器 {h} 不在线，跳过')
                        continue
                    on_mark = OnlineMark(name, mark_pwd, h, log_callback=log)
                    # 注册到全局任务管理
                    with _task_lock:
                        _running_tasks[task_id] = on_mark

                    if on_mark.login():
                        host = h
                        lesson_id, ques_id = on_mark.getTestID(q_name)
                        if lesson_id:
                            log(f'一评账号 {name}: TestID={lesson_id}, QuesID={ques_id}')
                            dic = on_mark.getPaper(lesson_id, ques_id)
                            on_mark.logout()
                            if dic:
                                all_paper_data.append(dic)
                            found = True
                            break
                    time.sleep(1.5)

                if not found:
                    log(f'一评账号 {name} 登录失败或未找到试题')

            if not all_paper_data:
                log('未获取到任何一评数据，任务结束')
                task.status = 'failed'
                db.commit()
                return

            # 合并一评数据
            if len(all_paper_data) > 1:
                merged_data = merge_paper_data(all_paper_data)
                log(f'合并一评数据: 共 {len(merged_data)} 份试卷')
            else:
                merged_data = all_paper_data[0]
                log(f'一评数据: 共 {len(merged_data)} 份试卷')

            # 保存结果数据
            task.result_data = json.dumps(merged_data, ensure_ascii=False)
            task.total_papers = len(merged_data)
            db.commit()

            # ===== 第二阶段: 用二评账号提交评分 =====
            log(f'开始二评提交, 账号: {second_account}')

            def on_progress(marked):
                task.marked_papers = marked
                if task.total_papers > 0:
                    task.progress = int(marked / task.total_papers * 100)
                db.commit()
                db.refresh(task)

            def on_progress_from_api(lesson_id, ques_id):
                progress = other_mark.getProgress(lesson_id, ques_id)
                if progress and progress.get('total', 0) > 0:
                    total = progress['total']
                    marked = progress['marked']
                    task.total_papers = total
                    task.marked_papers = marked
                    task.progress = int(marked / total * 100)
                    db.commit()
                    db.refresh(task)

            other_mark = None
            if host:
                if not _ping_host(host):
                    log(f'服务器 {host} 不在线，尝试其他服务器')
                else:
                    other_mark = OnlineMark(second_account, second_pwd, host, log_callback=log)
                    if not other_mark.login():
                        log(f'二评账号 {second_account} 登录失败')
                        other_mark = None
            if not other_mark:
                for h in all_hosts:
                    if h == host:
                        continue
                    if not _ping_host(h):
                        log(f'服务器 {h} 不在线，跳过')
                        continue
                    other_mark = OnlineMark(second_account, second_pwd, h, log_callback=log)
                    if other_mark.login():
                        host = h
                        break
                    other_mark = None
                    time.sleep(1.5)

            if not other_mark:
                log('二评账号登录失败')
                task.status = 'failed'
                db.commit()
                return

            with _task_lock:
                _running_tasks[task_id] = other_mark

            lesson_id, ques_id = other_mark.getTestID(q_name)
            if lesson_id:
                other_mark.getQuestion(lesson_id, ques_id, merged_data, progress_callback=on_progress, progress_api_callback=on_progress_from_api, refresh_delay=task.refresh_delay)
            else:
                log('二评账号未找到试题')

            other_mark.logout()

            # 任务完成
            if task.status != 'stopped':
                task.status = 'completed'
                task.progress = 100
                task.finished_at = datetime.utcnow()
                db.commit()
                log('任务完成!')

        except Exception as e:
            log(f'任务异常: {str(e)}')
            task.status = 'failed'
            task.finished_at = datetime.utcnow()
            db.commit()

        finally:
            # 清理全局任务管理
            with _task_lock:
                _running_tasks.pop(task_id, None)
    finally:
        db.close()
