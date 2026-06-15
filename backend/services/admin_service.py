"""Admin 管理端业务逻辑层"""

import hashlib
import hmac
import json
import secrets
import time
import uuid
from typing import Any

from backend.db import (
    db_connect,
    execute,
    execute_many,
    fetch_row,
    list_rows,
    log_operation,
    now_ms,
    _recount_class_sizes,
)

# --- Auth ---

ADMIN_USERS = {
    'admin': {
        'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(),
        'role': 'admin',
        'name': '管理员',
    },
}

TOKEN_SECRET = secrets.token_hex(32)
TOKEN_STORE: dict[str, dict[str, Any]] = {}
TOKEN_TTL_SEC = 24 * 3600  # 24 hours


def admin_login(username: str, password: str) -> dict[str, Any] | None:
    user = ADMIN_USERS.get(username)
    if not user:
        return None
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    if not hmac.compare_digest(pw_hash, user['password_hash']):
        return None

    token = secrets.token_hex(32)
    expires_at = now_ms() + TOKEN_TTL_SEC * 1000
    TOKEN_STORE[token] = {
        'username': username,
        'role': user['role'],
        'name': user['name'],
        'expires_at': expires_at,
    }
    log_operation('auth', 'login', username, {'role': user['role']})
    return {'token': token, 'username': username, 'role': user['role'], 'name': user['name']}


def admin_logout(token: str) -> None:
    TOKEN_STORE.pop(token, None)


def verify_token(token: str) -> dict[str, Any] | None:
    entry = TOKEN_STORE.get(token)
    if not entry:
        return None
    if now_ms() > entry['expires_at']:
        TOKEN_STORE.pop(token, None)
        return None
    return entry


# --- Dashboard ---

def dashboard_stats() -> dict[str, Any]:
    schools = fetch_row('SELECT COUNT(*) AS c FROM schools') or {}
    students = fetch_row('SELECT COUNT(*) AS c FROM students WHERE status = ?', ('active',)) or {}
    today_runs = fetch_row(
        "SELECT COUNT(*) AS c FROM test_runs WHERE started_at_ms >= ?",
        (int(time.time() * 1000) - 86400000,),
    ) or {}
    total_runs = fetch_row('SELECT COUNT(*) AS c FROM test_runs') or {}
    online_devices = fetch_row(
        "SELECT COUNT(*) AS c FROM devices WHERE status = 'online'"
    ) or {}
    offline_devices = fetch_row(
        "SELECT COUNT(*) AS c FROM devices WHERE status = 'offline'"
    ) or {}
    pending_exceptions = fetch_row(
        "SELECT COUNT(*) AS c FROM exceptions WHERE status = 'unresolved'"
    ) or {}

    recent_runs = list_rows(
        'SELECT run_id, venue_id, started_at_ms, duration_sec FROM test_runs ORDER BY started_at_ms DESC LIMIT 10'
    )
    for r in recent_runs:
        venue = fetch_row('SELECT name FROM venues WHERE id = ?', (r.get('venue_id', ''),))
        r['venue_name'] = venue['name'] if venue else ''

    return {
        'schoolCount': schools.get('c', 0),
        'studentCount': students.get('c', 0),
        'todayTestCount': today_runs.get('c', 0),
        'totalTestCount': total_runs.get('c', 0),
        'onlineDeviceCount': online_devices.get('c', 0),
        'offlineDeviceCount': offline_devices.get('c', 0),
        'pendingExceptionCount': pending_exceptions.get('c', 0),
        'recentRuns': recent_runs,
    }


def dashboard_trend(days: int = 7) -> list[dict[str, Any]]:
    ms_per_day = 86400000
    now = time.time() * 1000
    result = []
    for i in range(days - 1, -1, -1):
        day_start = int(now - (i + 1) * ms_per_day)
        day_end = int(now - i * ms_per_day)
        row = fetch_row(
            'SELECT COUNT(*) AS c FROM test_runs WHERE started_at_ms >= ? AND started_at_ms < ?',
            (day_start, day_end),
        )
        result.append({'date': day_start, 'count': row['c'] if row else 0})
    return result


# --- CRUD Helpers ---

def _gen_id(prefix: str) -> str:
    return f'{prefix}_{uuid.uuid4().hex[:8]}'


def _paginate(sql_base: str, params: tuple, page: int, page_size: int) -> dict[str, Any]:
    count_row = fetch_row(f'SELECT COUNT(*) AS c FROM ({sql_base})', params)
    total = count_row['c'] if count_row else 0
    rows = list_rows(f'{sql_base} LIMIT ? OFFSET ?', params + (page_size, (page - 1) * page_size))
    return {'list': rows, 'total': total, 'page': page, 'pageSize': page_size}


# --- Schools ---

def schools_list(page: int = 1, page_size: int = 20, search: str = '') -> dict[str, Any]:
    sql = 'SELECT * FROM schools WHERE 1=1'
    params: tuple = ()
    if search:
        sql += ' AND (name LIKE ? OR code LIKE ?)'
        params = (f'%{search}%', f'%{search}%')
    sql += ' ORDER BY created_at_ms DESC'
    return _paginate(sql, params, page, page_size)


def school_create(data: dict) -> dict:
    sid = _gen_id('school')
    ts = now_ms()
    execute(
        'INSERT INTO schools (id,name,code,contact_name,contact_phone,status,created_at_ms) VALUES (?,?,?,?,?,?,?)',
        (sid, data['name'], data['code'], data.get('contact_name', ''), data.get('contact_phone', ''), data.get('status', 'enabled'), ts),
    )
    log_operation('school', 'create', sid, {'name': data['name']})
    return fetch_row('SELECT * FROM schools WHERE id = ?', (sid,)) or {}


def school_update(sid: str, data: dict) -> dict | None:
    execute(
        'UPDATE schools SET name=?, code=?, contact_name=?, contact_phone=?, status=? WHERE id=?',
        (data['name'], data['code'], data.get('contact_name', ''), data.get('contact_phone', ''), data.get('status', 'enabled'), sid),
    )
    log_operation('school', 'update', sid, data)
    return fetch_row('SELECT * FROM schools WHERE id = ?', (sid,))


def school_delete(sid: str) -> bool:
    grade = fetch_row('SELECT COUNT(*) AS c FROM grades WHERE school_id = ?', (sid,))
    if grade and grade['c'] > 0:
        return False
    execute('DELETE FROM schools WHERE id = ?', (sid,))
    log_operation('school', 'delete', sid, {})
    return True


# --- Grades ---

def grades_list(page: int = 1, page_size: int = 20, school_id: str = '', search: str = '') -> dict[str, Any]:
    sql = 'SELECT g.*, s.name AS school_name FROM grades g LEFT JOIN schools s ON g.school_id = s.id WHERE 1=1'
    params: tuple = ()
    if school_id:
        sql += ' AND g.school_id = ?'
        params += (school_id,)
    if search:
        sql += ' AND g.name LIKE ?'
        params += (f'%{search}%',)
    sql += ' ORDER BY g.sort_order ASC, g.created_at_ms DESC'
    return _paginate(sql, params, page, page_size)


def grade_create(data: dict) -> dict:
    gid = _gen_id('grade')
    ts = now_ms()
    execute(
        'INSERT INTO grades (id,school_id,name,sort_order,status,created_at_ms) VALUES (?,?,?,?,?,?)',
        (gid, data['school_id'], data['name'], data.get('sort_order', 0), data.get('status', 'enabled'), ts),
    )
    log_operation('grade', 'create', gid, {'name': data['name']})
    return fetch_row('SELECT g.*, s.name AS school_name FROM grades g LEFT JOIN schools s ON g.school_id = s.id WHERE g.id = ?', (gid,)) or {}


def grade_update(gid: str, data: dict) -> dict | None:
    execute(
        'UPDATE grades SET school_id=?, name=?, sort_order=?, status=? WHERE id=?',
        (data['school_id'], data['name'], data.get('sort_order', 0), data.get('status', 'enabled'), gid),
    )
    log_operation('grade', 'update', gid, data)
    return fetch_row('SELECT g.*, s.name AS school_name FROM grades g LEFT JOIN schools s ON g.school_id = s.id WHERE g.id = ?', (gid,))


def grade_delete(gid: str) -> bool:
    cls = fetch_row('SELECT COUNT(*) AS c FROM classes WHERE grade_id = ?', (gid,))
    if cls and cls['c'] > 0:
        return False
    execute('DELETE FROM grades WHERE id = ?', (gid,))
    log_operation('grade', 'delete', gid, {})
    return True


# --- Classes ---

def classes_list(page: int = 1, page_size: int = 20, grade_id: str = '', search: str = '') -> dict[str, Any]:
    sql = 'SELECT c.*, g.name AS grade_name, s.name AS school_name FROM classes c LEFT JOIN grades g ON c.grade_id = g.id LEFT JOIN schools s ON g.school_id = s.id WHERE 1=1'
    params: tuple = ()
    if grade_id:
        sql += ' AND c.grade_id = ?'
        params += (grade_id,)
    if search:
        sql += ' AND c.name LIKE ?'
        params += (f'%{search}%',)
    sql += ' ORDER BY c.created_at_ms DESC'
    return _paginate(sql, params, page, page_size)


def class_create(data: dict) -> dict:
    cid = _gen_id('class')
    ts = now_ms()
    grade = fetch_row('SELECT name FROM grades WHERE id = ?', (data['grade_id'],))
    execute(
        'INSERT INTO classes (id,grade_id,name,teacher_name,student_count,status,created_at_ms) VALUES (?,?,?,?,?,?,?)',
        (cid, data['grade_id'], data['name'], data.get('teacher_name', ''), 0, data.get('status', 'enabled'), ts),
    )
    log_operation('class', 'create', cid, {'name': data['name']})
    return fetch_row('SELECT c.*, g.name AS grade_name, s.name AS school_name FROM classes c LEFT JOIN grades g ON c.grade_id = g.id LEFT JOIN schools s ON g.school_id = s.id WHERE c.id = ?', (cid,)) or {}


def class_update(cid: str, data: dict) -> dict | None:
    execute(
        'UPDATE classes SET grade_id=?, name=?, teacher_name=?, status=? WHERE id=?',
        (data['grade_id'], data['name'], data.get('teacher_name', ''), data.get('status', 'enabled'), cid),
    )
    log_operation('class', 'update', cid, data)
    return fetch_row('SELECT c.*, g.name AS grade_name, s.name AS school_name FROM classes c LEFT JOIN grades g ON c.grade_id = g.id LEFT JOIN schools s ON g.school_id = s.id WHERE c.id = ?', (cid,)) or {}


def class_delete(cid: str) -> bool:
    stu = fetch_row('SELECT COUNT(*) AS c FROM students WHERE class_id = ?', (cid,))
    if stu and stu['c'] > 0:
        return False
    execute('DELETE FROM classes WHERE id = ?', (cid,))
    log_operation('class', 'delete', cid, {})
    return True


# --- Students ---

def students_list(page: int = 1, page_size: int = 20, class_id: str = '', search: str = '', grade_id: str = '', school_id: str = '') -> dict[str, Any]:
    sql = 'SELECT s.*, g.name AS grade_name, sc.name AS school_name FROM students s LEFT JOIN classes c ON s.class_id = c.id LEFT JOIN grades g ON c.grade_id = g.id LEFT JOIN schools sc ON g.school_id = sc.id WHERE s.status = ?'
    params: tuple = ('active',)
    if class_id:
        sql += ' AND s.class_id = ?'
        params += (class_id,)
    if grade_id:
        sql += ' AND c.grade_id = ?'
        params += (grade_id,)
    if school_id:
        sql += ' AND g.school_id = ?'
        params += (school_id,)
    if search:
        sql += ' AND (s.name LIKE ? OR s.student_no LIKE ?)'
        params += (f'%{search}%', f'%{search}%')
    sql += ' ORDER BY s.created_at_ms DESC'
    return _paginate(sql, params, page, page_size)


def student_create(data: dict) -> dict | None:
    sid = _gen_id('stu')
    ts = now_ms()
    cls = fetch_row('SELECT id, name, grade_id FROM classes WHERE id = ?', (data['class_id'],))
    if not cls:
        return None
    grade = fetch_row('SELECT name FROM grades WHERE id = ?', (cls['grade_id'],))
    execute(
        'INSERT INTO students (id,student_no,name,gender,birth_date,grade_name,class_id,class_name,status,face_status,last_test_at_ms,created_at_ms) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
        (sid, data['student_no'], data['name'], data.get('gender', '男'), data.get('birth_date', ''), grade['name'] if grade else '', data['class_id'], cls['name'], 'active', 'pending', 0, ts),
    )
    _recount_class_sizes(db_connect().cursor())
    log_operation('student', 'create', sid, {'name': data['name'], 'student_no': data['student_no']})
    conn = db_connect()
    try:
        return dict(conn.cursor().execute(
            'SELECT s.*, c.name AS class_label FROM students s LEFT JOIN classes c ON s.class_id = c.id WHERE s.id = ?', (sid,)
        ).fetchone())
    finally:
        conn.close()


def student_update(sid: str, data: dict) -> dict | None:
    cls = fetch_row('SELECT id, name, grade_id FROM classes WHERE id = ?', (data['class_id'],))
    if not cls:
        return None
    grade = fetch_row('SELECT name FROM grades WHERE id = ?', (cls['grade_id'],))
    execute(
        'UPDATE students SET student_no=?, name=?, gender=?, birth_date=?, grade_name=?, class_id=?, class_name=? WHERE id=?',
        (data['student_no'], data['name'], data.get('gender', '男'), data.get('birth_date', ''), grade['name'] if grade else '', data['class_id'], cls['name'], sid),
    )
    _recount_class_sizes(db_connect().cursor())
    log_operation('student', 'update', sid, data)
    conn = db_connect()
    try:
        return dict(conn.cursor().execute(
            'SELECT s.*, c.name AS class_label FROM students s LEFT JOIN classes c ON s.class_id = c.id WHERE s.id = ?', (sid,)
        ).fetchone())
    finally:
        conn.close()


def student_delete(sid: str) -> bool:
    execute("UPDATE students SET status = 'inactive' WHERE id = ?", (sid,))
    _recount_class_sizes(db_connect().cursor())
    log_operation('student', 'delete', sid, {})
    return True


def student_detail(sid: str) -> dict | None:
    student = fetch_row(
        'SELECT s.*, g.name AS grade_name, sc.name AS school_name, c.id AS class_id_confirm FROM students s LEFT JOIN classes c ON s.class_id = c.id LEFT JOIN grades g ON c.grade_id = g.id LEFT JOIN schools sc ON g.school_id = sc.id WHERE s.id = ?',
        (sid,),
    )
    if not student:
        return None
    faces = list_rows('SELECT * FROM face_samples WHERE student_id = ? ORDER BY is_primary DESC', (sid,))
    scores = list_rows(
        'SELECT sc.*, tr.duration_sec FROM scores sc LEFT JOIN test_runs tr ON sc.run_id = tr.run_id WHERE sc.student_id = ? ORDER BY sc.tested_at_ms DESC LIMIT 50',
        (sid,),
    )
    return {'student': student, 'faces': faces, 'scores': scores}


# --- Faces ---

def faces_list(student_id: str) -> list[dict]:
    return list_rows('SELECT * FROM face_samples WHERE student_id = ? ORDER BY is_primary DESC', (student_id,))


def face_upload(student_id: str, image_url: str, quality_score: float = 80.0) -> dict:
    fid = _gen_id('face')
    ts = now_ms()
    execute(
        'INSERT INTO face_samples (id,student_id,image_url,quality_score,is_primary,status,created_at_ms,updated_at_ms) VALUES (?,?,?,?,?,?,?,?)',
        (fid, student_id, image_url, quality_score, 0, 'ready', ts, ts),
    )
    log_operation('face', 'upload', fid, {'student_id': student_id})
    return fetch_row('SELECT * FROM face_samples WHERE id = ?', (fid,)) or {}


def face_set_primary(face_id: str) -> bool:
    face = fetch_row('SELECT student_id FROM face_samples WHERE id = ?', (face_id,))
    if not face:
        return False
    execute('UPDATE face_samples SET is_primary = 0 WHERE student_id = ?', (face['student_id'],))
    execute('UPDATE face_samples SET is_primary = 1, updated_at_ms = ? WHERE id = ?', (now_ms(), face_id))
    log_operation('face', 'set_primary', face_id, {'student_id': face['student_id']})
    return True


def face_delete(face_id: str) -> bool:
    execute('DELETE FROM face_samples WHERE id = ?', (face_id,))
    log_operation('face', 'delete', face_id, {})
    return True


# --- Venues ---

def venues_list(page: int = 1, page_size: int = 20, school_id: str = '', search: str = '') -> dict[str, Any]:
    sql = 'SELECT v.*, s.name AS school_name FROM venues v LEFT JOIN schools s ON v.school_id = s.id WHERE 1=1'
    params: tuple = ()
    if school_id:
        sql += ' AND v.school_id = ?'
        params += (school_id,)
    if search:
        sql += ' AND (v.name LIKE ? OR v.code LIKE ?)'
        params += (f'%{search}%', f'%{search}%')
    sql += ' ORDER BY v.created_at_ms DESC'
    return _paginate(sql, params, page, page_size)


def venue_create(data: dict) -> dict:
    vid = _gen_id('venue')
    ts = now_ms()
    execute(
        'INSERT INTO venues (id,school_id,name,code,status,last_test_at_ms,created_at_ms) VALUES (?,?,?,?,?,?,?)',
        (vid, data['school_id'], data['name'], data.get('code', ''), data.get('status', 'online'), 0, ts),
    )
    log_operation('venue', 'create', vid, {'name': data['name']})
    return fetch_row('SELECT v.*, s.name AS school_name FROM venues v LEFT JOIN schools s ON v.school_id = s.id WHERE v.id = ?', (vid,)) or {}


def venue_update(vid: str, data: dict) -> dict | None:
    execute(
        'UPDATE venues SET school_id=?, name=?, code=?, status=? WHERE id=?',
        (data['school_id'], data['name'], data.get('code', ''), data.get('status', 'online'), vid),
    )
    log_operation('venue', 'update', vid, data)
    return fetch_row('SELECT v.*, s.name AS school_name FROM venues v LEFT JOIN schools s ON v.school_id = s.id WHERE v.id = ?', (vid,))


def venue_delete(vid: str) -> bool:
    dev = fetch_row('SELECT COUNT(*) AS c FROM devices WHERE venue_id = ?', (vid,))
    if dev and dev['c'] > 0:
        return False
    execute('DELETE FROM venues WHERE id = ?', (vid,))
    log_operation('venue', 'delete', vid, {})
    return True


# --- Devices ---

def devices_list(page: int = 1, page_size: int = 20, venue_id: str = '', search: str = '') -> dict[str, Any]:
    sql = 'SELECT d.*, v.name AS venue_name FROM devices d LEFT JOIN venues v ON d.venue_id = v.id WHERE 1=1'
    params: tuple = ()
    if venue_id:
        sql += ' AND d.venue_id = ?'
        params += (venue_id,)
    if search:
        sql += ' AND (d.name LIKE ? OR d.device_no LIKE ?)'
        params += (f'%{search}%', f'%{search}%')
    sql += ' ORDER BY d.created_at_ms DESC'
    return _paginate(sql, params, page, page_size)


def device_create(data: dict) -> dict:
    did = _gen_id('device')
    ts = now_ms()
    execute(
        'INSERT INTO devices (id,venue_id,device_no,name,type,ip_address,version,status,last_heartbeat_at_ms,created_at_ms) VALUES (?,?,?,?,?,?,?,?,?,?)',
        (did, data['venue_id'], data['device_no'], data['name'], data.get('type', 'camera'), data.get('ip_address', ''), data.get('version', '1.0.0'), data.get('status', 'offline'), ts, ts),
    )
    log_operation('device', 'create', did, {'name': data['name']})
    return fetch_row('SELECT d.*, v.name AS venue_name FROM devices d LEFT JOIN venues v ON d.venue_id = v.id WHERE d.id = ?', (did,)) or {}


def device_update(did: str, data: dict) -> dict | None:
    execute(
        'UPDATE devices SET venue_id=?, device_no=?, name=?, type=?, ip_address=?, version=?, status=? WHERE id=?',
        (data['venue_id'], data['device_no'], data['name'], data.get('type', 'camera'), data.get('ip_address', ''), data.get('version', '1.0.0'), data.get('status', 'offline'), did),
    )
    log_operation('device', 'update', did, data)
    return fetch_row('SELECT d.*, v.name AS venue_name FROM devices d LEFT JOIN venues v ON d.venue_id = v.id WHERE d.id = ?', (did,))


def device_delete(did: str) -> bool:
    execute('DELETE FROM devices WHERE id = ?', (did,))
    log_operation('device', 'delete', did, {})
    return True


# --- Tasks ---

def tasks_list(page: int = 1, page_size: int = 20, status: str = '', search: str = '') -> dict[str, Any]:
    sql = 'SELECT t.*, v.name AS venue_name FROM tasks t LEFT JOIN venues v ON t.venue_id = v.id WHERE 1=1'
    params: tuple = ()
    if status:
        sql += ' AND t.status = ?'
        params += (status,)
    if search:
        sql += ' AND t.name LIKE ?'
        params += (f'%{search}%',)
    sql += ' ORDER BY t.created_at_ms DESC'
    return _paginate(sql, params, page, page_size)


def task_create(data: dict) -> dict:
    tid = _gen_id('task')
    ts = now_ms()
    device_ids_json = json.dumps(data.get('device_ids', []), ensure_ascii=False)
    execute(
        'INSERT INTO tasks (id,name,test_item,test_date,time_range,target_type,target_ref,venue_id,device_ids_json,duration_sec,countdown_sec,binding_action,status,created_at_ms) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        (tid, data['name'], data.get('test_item', 'jump_rope'), data.get('test_date', ''), data.get('time_range', ''), data.get('target_type', 'class'), data.get('target_ref', ''), data.get('venue_id', ''), device_ids_json, data.get('duration_sec', 60), data.get('countdown_sec', 5), data.get('binding_action', 'wave'), data.get('status', 'draft'), ts),
    )
    log_operation('task', 'create', tid, {'name': data['name']})
    return fetch_row('SELECT t.*, v.name AS venue_name FROM tasks t LEFT JOIN venues v ON t.venue_id = v.id WHERE t.id = ?', (tid,)) or {}


def task_update(tid: str, data: dict) -> dict | None:
    device_ids_json = json.dumps(data.get('device_ids', []), ensure_ascii=False)
    execute(
        'UPDATE tasks SET name=?, test_item=?, test_date=?, time_range=?, target_type=?, target_ref=?, venue_id=?, device_ids_json=?, duration_sec=?, countdown_sec=?, binding_action=?, status=? WHERE id=?',
        (data['name'], data.get('test_item', 'jump_rope'), data.get('test_date', ''), data.get('time_range', ''), data.get('target_type', 'class'), data.get('target_ref', ''), data.get('venue_id', ''), device_ids_json, data.get('duration_sec', 60), data.get('countdown_sec', 5), data.get('binding_action', 'wave'), data.get('status', 'draft'), tid),
    )
    log_operation('task', 'update', tid, data)
    return fetch_row('SELECT t.*, v.name AS venue_name FROM tasks t LEFT JOIN venues v ON t.venue_id = v.id WHERE t.id = ?', (tid,))


def task_publish(tid: str) -> dict | None:
    execute("UPDATE tasks SET status = 'published' WHERE id = ?", (tid,))
    log_operation('task', 'publish', tid, {})
    return fetch_row('SELECT t.*, v.name AS venue_name FROM tasks t LEFT JOIN venues v ON t.venue_id = v.id WHERE t.id = ?', (tid,))


def task_cancel(tid: str) -> dict | None:
    execute("UPDATE tasks SET status = 'cancelled' WHERE id = ?", (tid,))
    log_operation('task', 'cancel', tid, {})
    return fetch_row('SELECT t.*, v.name AS venue_name FROM tasks t LEFT JOIN venues v ON t.venue_id = v.id WHERE t.id = ?', (tid,))


# --- Scores ---

def scores_list(
    page: int = 1, page_size: int = 20,
    student_id: str = '', class_id: str = '', grade_id: str = '', school_id: str = '',
    venue_id: str = '', task_id: str = '', search: str = '',
    start_date: int = 0, end_date: int = 0,
) -> dict[str, Any]:
    sql = '''
        SELECT sc.*, tr.duration_sec, s.name AS student_name, s.student_no, s.class_name,
               c.grade_id, g.name AS grade_name, g.school_id, sch.name AS school_name,
               v.name AS venue_name
        FROM scores sc
        LEFT JOIN test_runs tr ON sc.run_id = tr.run_id
        LEFT JOIN students s ON sc.student_id = s.id
        LEFT JOIN classes c ON s.class_id = c.id
        LEFT JOIN grades g ON c.grade_id = g.id
        LEFT JOIN schools sch ON g.school_id = sch.id
        LEFT JOIN venues v ON sc.venue_id = v.id
        WHERE 1=1
    '''
    params: tuple = ()
    if student_id:
        sql += ' AND sc.student_id = ?'
        params += (student_id,)
    if class_id:
        sql += ' AND s.class_id = ?'
        params += (class_id,)
    if grade_id:
        sql += ' AND c.grade_id = ?'
        params += (grade_id,)
    if school_id:
        sql += ' AND g.school_id = ?'
        params += (school_id,)
    if venue_id:
        sql += ' AND sc.venue_id = ?'
        params += (venue_id,)
    if task_id:
        sql += ' AND sc.task_id = ?'
        params += (task_id,)
    if search:
        sql += ' AND (s.name LIKE ? OR s.student_no LIKE ?)'
        params += (f'%{search}%', f'%{search}%')
    if start_date:
        sql += ' AND sc.tested_at_ms >= ?'
        params += (start_date,)
    if end_date:
        sql += ' AND sc.tested_at_ms <= ?'
        params += (end_date,)
    sql += ' ORDER BY sc.tested_at_ms DESC'
    return _paginate(sql, params, page, page_size)


def score_detail(score_id: str) -> dict | None:
    score = fetch_row(
        '''
        SELECT sc.*, tr.duration_sec, tr.started_at_ms, tr.ended_at_ms,
               s.name AS student_name, s.student_no, s.class_name,
               v.name AS venue_name, t.name AS task_name
        FROM scores sc
        LEFT JOIN test_runs tr ON sc.run_id = tr.run_id
        LEFT JOIN students s ON sc.student_id = s.id
        LEFT JOIN venues v ON sc.venue_id = v.id
        LEFT JOIN tasks t ON sc.task_id = t.id
        WHERE sc.id = ?
        ''',
        (score_id,),
    )
    if not score:
        return None
    run_slots = list_rows('SELECT * FROM test_run_slots WHERE run_id = ? ORDER BY slot', (score['run_id'],))
    for slot in run_slots:
        try:
            slot['points'] = json.loads(slot['points_json'])
        except (json.JSONDecodeError, KeyError):
            slot['points'] = []
        student = fetch_row('SELECT name FROM students WHERE id = ?', (slot['user_id'],)) if slot.get('user_id') else None
        slot['student_name'] = student['name'] if student else ''
    exceptions = list_rows('SELECT * FROM exceptions WHERE run_id = ?', (score['run_id'],))
    return {'score': score, 'slots': run_slots, 'exceptions': exceptions}


def score_review(score_id: str, review_status: str, remark: str = '') -> dict | None:
    execute(
        'UPDATE scores SET review_status = ? WHERE id = ?',
        (review_status, score_id),
    )
    if remark:
        exceptions = list_rows('SELECT id FROM exceptions WHERE run_id = (SELECT run_id FROM scores WHERE id = ?)', (score_id,))
        for ex in exceptions:
            execute('UPDATE exceptions SET handle_remark = ? WHERE id = ?', (remark, ex['id']))
    log_operation('score', 'review', score_id, {'review_status': review_status, 'remark': remark})
    return fetch_row(
        'SELECT sc.*, s.name AS student_name, s.student_no FROM scores sc LEFT JOIN students s ON sc.student_id = s.id WHERE sc.id = ?',
        (score_id,),
    )


def score_batch_review(score_ids: list[str], review_status: str) -> int:
    placeholders = ','.join(['?' for _ in score_ids])
    execute(f'UPDATE scores SET review_status = ? WHERE id IN ({placeholders})', (review_status, *score_ids))
    log_operation('score', 'batch_review', '', {'ids': score_ids, 'review_status': review_status})
    return len(score_ids)


def score_stats(class_id: str = '', grade_id: str = '', school_id: str = '') -> dict[str, Any]:
    sql = '''
        SELECT s.class_id, s.class_name,
               COUNT(sc.id) AS participant_count,
               AVG(sc.final_count) AS avg_count,
               MAX(sc.final_count) AS max_count,
               MIN(sc.final_count) AS min_count
        FROM scores sc
        LEFT JOIN students s ON sc.student_id = s.id
        LEFT JOIN classes c ON s.class_id = c.id
        LEFT JOIN grades g ON c.grade_id = g.id
        WHERE 1=1
    '''
    params: tuple = ()
    if class_id:
        sql += ' AND s.class_id = ?'
        params += (class_id,)
    if grade_id:
        sql += ' AND c.grade_id = ?'
        params += (grade_id,)
    if school_id:
        sql += ' AND g.school_id = ?'
        params += (school_id,)
    sql += ' GROUP BY s.class_id ORDER BY avg_count DESC'
    return {'list': list_rows(sql, params)}


# --- Exceptions ---

def exceptions_list(page: int = 1, page_size: int = 20, exc_type: str = '', level: str = '', status: str = '') -> dict[str, Any]:
    sql = 'SELECT * FROM exceptions WHERE 1=1'
    params: tuple = ()
    if exc_type:
        sql += ' AND type = ?'
        params += (exc_type,)
    if level:
        sql += ' AND level = ?'
        params += (level,)
    if status:
        sql += ' AND status = ?'
        params += (status,)
    sql += ' ORDER BY created_at_ms DESC'
    return _paginate(sql, params, page, page_size)


def exception_resolve(exc_id: str, remark: str = '') -> dict | None:
    execute("UPDATE exceptions SET status = 'resolved', handle_remark = ? WHERE id = ?", (remark, exc_id))
    log_operation('exception', 'resolve', exc_id, {'remark': remark})
    return fetch_row('SELECT * FROM exceptions WHERE id = ?', (exc_id,))


def exception_batch_resolve(exc_ids: list[str]) -> int:
    placeholders = ','.join(['?' for _ in exc_ids])
    execute(f"UPDATE exceptions SET status = 'resolved' WHERE id IN ({placeholders})", tuple(exc_ids))
    log_operation('exception', 'batch_resolve', '', {'ids': exc_ids})
    return len(exc_ids)


# --- Settings ---

def settings_get() -> dict[str, Any]:
    rows = list_rows('SELECT key, value_json FROM settings')
    result = {}
    for row in rows:
        try:
            result[row['key']] = json.loads(row['value_json'])
        except (json.JSONDecodeError, KeyError):
            result[row['key']] = {}
    return result


def settings_update(key: str, value: dict) -> None:
    ts = now_ms()
    execute(
        'INSERT INTO settings (key,value_json,updated_at_ms) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at_ms=excluded.updated_at_ms',
        (key, json.dumps(value, ensure_ascii=False), ts),
    )
    log_operation('settings', 'update', key, value)


# --- Logs ---

def operation_logs_list(page: int = 1, page_size: int = 20, module: str = '', action: str = '') -> dict[str, Any]:
    sql = 'SELECT * FROM operation_logs WHERE 1=1'
    params: tuple = ()
    if module:
        sql += ' AND module = ?'
        params += (module,)
    if action:
        sql += ' AND action = ?'
        params += (action,)
    sql += ' ORDER BY created_at_ms DESC'
    return _paginate(sql, params, page, page_size)


def login_logs_list(page: int = 1, page_size: int = 20) -> dict[str, Any]:
    sql = 'SELECT * FROM login_logs ORDER BY created_at_ms DESC'
    return _paginate(sql, (), page, page_size)
