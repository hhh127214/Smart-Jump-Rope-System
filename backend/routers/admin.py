"""Admin 管理端 API 路由"""

from fastapi import APIRouter, Body, Depends, HTTPException, Header
from typing import Any

from backend.services.admin_service import (
    admin_login,
    admin_logout,
    verify_token,
    dashboard_stats,
    dashboard_trend,
    schools_list,
    school_create,
    school_update,
    school_delete,
    grades_list,
    grade_create,
    grade_update,
    grade_delete,
    classes_list,
    class_create,
    class_update,
    class_delete,
    students_list,
    student_create,
    student_update,
    student_delete,
    student_detail,
    faces_list,
    face_upload,
    face_set_primary,
    face_delete,
    venues_list,
    venue_create,
    venue_update,
    venue_delete,
    devices_list,
    device_create,
    device_update,
    device_delete,
    tasks_list,
    task_create,
    task_update,
    task_publish,
    task_cancel,
    scores_list,
    score_detail,
    score_review,
    score_batch_review,
    score_stats,
    exceptions_list,
    exception_resolve,
    exception_batch_resolve,
    settings_get,
    settings_update,
    operation_logs_list,
    login_logs_list,
)

router = APIRouter(prefix='/api/admin', tags=['admin'])


def admin_auth(authorization: str = Header('')) -> dict[str, Any]:
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='UNAUTHORIZED')
    token = authorization[7:]
    entry = verify_token(token)
    if not entry:
        raise HTTPException(status_code=401, detail='TOKEN_EXPIRED')
    return entry


# --- Auth ---

@router.post('/auth/login')
def login(payload: dict = Body(default_factory=dict)) -> dict:
    username = str(payload.get('username') or '')
    password = str(payload.get('password') or '')
    result = admin_login(username, password)
    if not result:
        raise HTTPException(status_code=401, detail='用户名或密码错误')
    return {'code': 0, 'data': result, 'message': 'ok'}


@router.post('/auth/logout')
def logout(user=Depends(admin_auth)) -> dict:
    # user contains the auth info, token is in the header but we don't need to clear it here since it's stateless
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.get('/auth/me')
def me(user=Depends(admin_auth)) -> dict:
    return {'code': 0, 'data': {'username': user['username'], 'role': user['role'], 'name': user['name']}, 'message': 'ok'}


# --- Dashboard ---

@router.get('/dashboard/stats')
def get_dashboard_stats(user=Depends(admin_auth)) -> dict:
    data = dashboard_stats()
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.get('/dashboard/trend')
def get_dashboard_trend(days: int = 7, user=Depends(admin_auth)) -> dict:
    data = dashboard_trend(days)
    return {'code': 0, 'data': data, 'message': 'ok'}


# --- Schools ---

@router.get('/schools')
def get_schools(page: int = 1, page_size: int = 20, search: str = '', user=Depends(admin_auth)) -> dict:
    return {'code': 0, 'data': schools_list(page, page_size, search), 'message': 'ok'}


@router.post('/schools')
def post_school(payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    data = school_create(payload)
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.put('/schools/{sid}')
def put_school(sid: str, payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    data = school_update(sid, payload)
    if not data:
        raise HTTPException(status_code=404, detail='学校不存在')
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.delete('/schools/{sid}')
def del_school(sid: str, user=Depends(admin_auth)) -> dict:
    if not school_delete(sid):
        raise HTTPException(status_code=400, detail='该学校下存在年级，无法删除')
    return {'code': 0, 'data': None, 'message': 'ok'}


# --- Grades ---

@router.get('/grades')
def get_grades(page: int = 1, page_size: int = 20, school_id: str = '', search: str = '', user=Depends(admin_auth)) -> dict:
    return {'code': 0, 'data': grades_list(page, page_size, school_id, search), 'message': 'ok'}


@router.post('/grades')
def post_grade(payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    data = grade_create(payload)
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.put('/grades/{gid}')
def put_grade(gid: str, payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    data = grade_update(gid, payload)
    if not data:
        raise HTTPException(status_code=404, detail='年级不存在')
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.delete('/grades/{gid}')
def del_grade(gid: str, user=Depends(admin_auth)) -> dict:
    if not grade_delete(gid):
        raise HTTPException(status_code=400, detail='该年级下存在班级，无法删除')
    return {'code': 0, 'data': None, 'message': 'ok'}


# --- Classes ---

@router.get('/classes')
def get_classes(page: int = 1, page_size: int = 20, grade_id: str = '', search: str = '', user=Depends(admin_auth)) -> dict:
    return {'code': 0, 'data': classes_list(page, page_size, grade_id, search), 'message': 'ok'}


@router.post('/classes')
def post_class(payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    data = class_create(payload)
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.put('/classes/{cid}')
def put_class(cid: str, payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    data = class_update(cid, payload)
    if not data:
        raise HTTPException(status_code=404, detail='班级不存在')
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.delete('/classes/{cid}')
def del_class(cid: str, user=Depends(admin_auth)) -> dict:
    if not class_delete(cid):
        raise HTTPException(status_code=400, detail='该班级下存在学生，无法删除')
    return {'code': 0, 'data': None, 'message': 'ok'}


# --- Students ---

@router.get('/students')
def get_students(
    page: int = 1, page_size: int = 20,
    class_id: str = '', grade_id: str = '', school_id: str = '',
    search: str = '', user=Depends(admin_auth),
) -> dict:
    return {'code': 0, 'data': students_list(page, page_size, class_id, search, grade_id, school_id), 'message': 'ok'}


@router.post('/students')
def post_student(payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    data = student_create(payload)
    if not data:
        raise HTTPException(status_code=400, detail='班级不存在')
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.put('/students/{sid}')
def put_student(sid: str, payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    data = student_update(sid, payload)
    if not data:
        raise HTTPException(status_code=404, detail='学生或班级不存在')
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.delete('/students/{sid}')
def del_student(sid: str, user=Depends(admin_auth)) -> dict:
    student_delete(sid)
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.get('/students/{sid}')
def get_student_detail(sid: str, user=Depends(admin_auth)) -> dict:
    data = student_detail(sid)
    if not data:
        raise HTTPException(status_code=404, detail='学生不存在')
    return {'code': 0, 'data': data, 'message': 'ok'}


# --- Faces ---

@router.get('/students/{student_id}/faces')
def get_faces(student_id: str, user=Depends(admin_auth)) -> dict:
    return {'code': 0, 'data': faces_list(student_id), 'message': 'ok'}


@router.post('/students/{student_id}/faces')
def post_face(student_id: str, payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    image_url = str(payload.get('image_url') or '')
    quality_score = float(payload.get('quality_score') or 80.0)
    data = face_upload(student_id, image_url, quality_score)
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.put('/faces/{face_id}/primary')
def put_face_primary(face_id: str, user=Depends(admin_auth)) -> dict:
    if not face_set_primary(face_id):
        raise HTTPException(status_code=404, detail='人脸样本不存在')
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.delete('/faces/{face_id}')
def del_face(face_id: str, user=Depends(admin_auth)) -> dict:
    face_delete(face_id)
    return {'code': 0, 'data': None, 'message': 'ok'}


# --- Venues ---

@router.get('/venues')
def get_venues(page: int = 1, page_size: int = 20, school_id: str = '', search: str = '', user=Depends(admin_auth)) -> dict:
    return {'code': 0, 'data': venues_list(page, page_size, school_id, search), 'message': 'ok'}


@router.post('/venues')
def post_venue(payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    data = venue_create(payload)
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.put('/venues/{vid}')
def put_venue(vid: str, payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    data = venue_update(vid, payload)
    if not data:
        raise HTTPException(status_code=404, detail='考场不存在')
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.delete('/venues/{vid}')
def del_venue(vid: str, user=Depends(admin_auth)) -> dict:
    if not venue_delete(vid):
        raise HTTPException(status_code=400, detail='该考场下存在设备，无法删除')
    return {'code': 0, 'data': None, 'message': 'ok'}


# --- Devices ---

@router.get('/devices')
def get_devices(page: int = 1, page_size: int = 20, venue_id: str = '', search: str = '', user=Depends(admin_auth)) -> dict:
    return {'code': 0, 'data': devices_list(page, page_size, venue_id, search), 'message': 'ok'}


@router.post('/devices')
def post_device(payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    data = device_create(payload)
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.put('/devices/{did}')
def put_device(did: str, payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    data = device_update(did, payload)
    if not data:
        raise HTTPException(status_code=404, detail='设备不存在')
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.delete('/devices/{did}')
def del_device(did: str, user=Depends(admin_auth)) -> dict:
    device_delete(did)
    return {'code': 0, 'data': None, 'message': 'ok'}


# --- Tasks ---

@router.get('/tasks')
def get_tasks(page: int = 1, page_size: int = 20, status: str = '', search: str = '', user=Depends(admin_auth)) -> dict:
    return {'code': 0, 'data': tasks_list(page, page_size, status, search), 'message': 'ok'}


@router.post('/tasks')
def post_task(payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    data = task_create(payload)
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.put('/tasks/{tid}')
def put_task(tid: str, payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    data = task_update(tid, payload)
    if not data:
        raise HTTPException(status_code=404, detail='任务不存在')
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.post('/tasks/{tid}/publish')
def publish_task(tid: str, user=Depends(admin_auth)) -> dict:
    data = task_publish(tid)
    if not data:
        raise HTTPException(status_code=404, detail='任务不存在')
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.post('/tasks/{tid}/cancel')
def cancel_task(tid: str, user=Depends(admin_auth)) -> dict:
    data = task_cancel(tid)
    if not data:
        raise HTTPException(status_code=404, detail='任务不存在')
    return {'code': 0, 'data': data, 'message': 'ok'}


# --- Scores ---

@router.get('/scores')
def get_scores(
    page: int = 1, page_size: int = 20,
    student_id: str = '', class_id: str = '', grade_id: str = '', school_id: str = '',
    venue_id: str = '', task_id: str = '', search: str = '',
    start_date: int = 0, end_date: int = 0,
    user=Depends(admin_auth),
) -> dict:
    return {
        'code': 0,
        'data': scores_list(page, page_size, student_id, class_id, grade_id, school_id, venue_id, task_id, search, start_date, end_date),
        'message': 'ok',
    }


@router.get('/scores/{score_id}')
def get_score_detail(score_id: str, user=Depends(admin_auth)) -> dict:
    data = score_detail(score_id)
    if not data:
        raise HTTPException(status_code=404, detail='成绩不存在')
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.put('/scores/{score_id}/review')
def review_score(score_id: str, payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    review_status = str(payload.get('review_status') or '')
    remark = str(payload.get('remark') or '')
    data = score_review(score_id, review_status, remark)
    if not data:
        raise HTTPException(status_code=404, detail='成绩不存在')
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.post('/scores/batch-review')
def batch_review_scores(payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    ids = payload.get('ids', [])
    review_status = str(payload.get('review_status') or '')
    count = score_batch_review(ids, review_status)
    return {'code': 0, 'data': {'count': count}, 'message': 'ok'}


@router.get('/scores/stats')
def get_score_stats(class_id: str = '', grade_id: str = '', school_id: str = '', user=Depends(admin_auth)) -> dict:
    return {'code': 0, 'data': score_stats(class_id, grade_id, school_id), 'message': 'ok'}


# --- Exceptions ---

@router.get('/exceptions')
def get_exceptions(page: int = 1, page_size: int = 20, type: str = '', level: str = '', status: str = '', user=Depends(admin_auth)) -> dict:
    return {'code': 0, 'data': exceptions_list(page, page_size, type, level, status), 'message': 'ok'}


@router.put('/exceptions/{exc_id}')
def resolve_exception(exc_id: str, payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    remark = str(payload.get('remark') or '')
    data = exception_resolve(exc_id, remark)
    if not data:
        raise HTTPException(status_code=404, detail='异常记录不存在')
    return {'code': 0, 'data': data, 'message': 'ok'}


@router.post('/exceptions/batch')
def batch_resolve_exceptions(payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    ids = payload.get('ids', [])
    count = exception_batch_resolve(ids)
    return {'code': 0, 'data': {'count': count}, 'message': 'ok'}


# --- Settings ---

@router.get('/settings')
def get_settings(user=Depends(admin_auth)) -> dict:
    return {'code': 0, 'data': settings_get(), 'message': 'ok'}


@router.put('/settings')
def put_settings(payload: dict = Body(default_factory=dict), user=Depends(admin_auth)) -> dict:
    for key, value in payload.items():
        settings_update(key, value)
    return {'code': 0, 'data': settings_get(), 'message': 'ok'}


# --- Logs ---

@router.get('/logs/operation')
def get_operation_logs(page: int = 1, page_size: int = 20, module: str = '', action: str = '', user=Depends(admin_auth)) -> dict:
    return {'code': 0, 'data': operation_logs_list(page, page_size, module, action), 'message': 'ok'}


@router.get('/logs/login')
def get_login_logs(page: int = 1, page_size: int = 20, user=Depends(admin_auth)) -> dict:
    return {'code': 0, 'data': login_logs_list(page, page_size), 'message': 'ok'}
