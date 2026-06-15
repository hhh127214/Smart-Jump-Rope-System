import json
import sqlite3
import time
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'rope.db'


def now_ms() -> int:
    return int(time.time() * 1000)


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _seed_if_empty(cur: sqlite3.Cursor, table: str, sql: str, rows: list[tuple]) -> None:
    cur.execute(f'SELECT COUNT(*) AS c FROM {table}')
    if int(cur.fetchone()['c']) == 0:
        cur.executemany(sql, rows)


def _recount_class_sizes(cur: sqlite3.Cursor) -> None:
    cur.execute('UPDATE classes SET student_count = 0')
    cur.execute(
        '''
        UPDATE classes
        SET student_count = (
          SELECT COUNT(*) FROM students s WHERE s.class_id = classes.id AND s.status = 'active'
        )
        '''
    )


def db_init() -> None:
    conn = db_connect()
    try:
        cur = conn.cursor()

        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS schools (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              code TEXT NOT NULL,
              contact_name TEXT NOT NULL,
              contact_phone TEXT NOT NULL,
              status TEXT NOT NULL,
              created_at_ms INTEGER NOT NULL
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS grades (
              id TEXT PRIMARY KEY,
              school_id TEXT NOT NULL,
              name TEXT NOT NULL,
              sort_order INTEGER NOT NULL DEFAULT 0,
              status TEXT NOT NULL,
              created_at_ms INTEGER NOT NULL
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS classes (
              id TEXT PRIMARY KEY,
              grade_id TEXT NOT NULL,
              name TEXT NOT NULL,
              teacher_name TEXT NOT NULL DEFAULT '',
              student_count INTEGER NOT NULL DEFAULT 0,
              status TEXT NOT NULL,
              created_at_ms INTEGER NOT NULL
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS students (
              id TEXT PRIMARY KEY,
              student_no TEXT NOT NULL UNIQUE,
              name TEXT NOT NULL,
              gender TEXT NOT NULL,
              birth_date TEXT NOT NULL DEFAULT '',
              grade_name TEXT NOT NULL,
              class_id TEXT NOT NULL,
              class_name TEXT NOT NULL,
              status TEXT NOT NULL,
              face_status TEXT NOT NULL,
              last_test_at_ms INTEGER NOT NULL DEFAULT 0,
              created_at_ms INTEGER NOT NULL
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS face_samples (
              id TEXT PRIMARY KEY,
              student_id TEXT NOT NULL,
              image_url TEXT NOT NULL,
              quality_score REAL NOT NULL,
              is_primary INTEGER NOT NULL,
              status TEXT NOT NULL,
              created_at_ms INTEGER NOT NULL,
              updated_at_ms INTEGER NOT NULL
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS venues (
              id TEXT PRIMARY KEY,
              school_id TEXT NOT NULL,
              name TEXT NOT NULL,
              code TEXT NOT NULL,
              status TEXT NOT NULL,
              last_test_at_ms INTEGER NOT NULL DEFAULT 0,
              created_at_ms INTEGER NOT NULL
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS devices (
              id TEXT PRIMARY KEY,
              venue_id TEXT NOT NULL,
              device_no TEXT NOT NULL UNIQUE,
              name TEXT NOT NULL,
              type TEXT NOT NULL,
              ip_address TEXT NOT NULL,
              version TEXT NOT NULL,
              status TEXT NOT NULL,
              last_heartbeat_at_ms INTEGER NOT NULL DEFAULT 0,
              created_at_ms INTEGER NOT NULL
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS tasks (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              test_item TEXT NOT NULL,
              test_date TEXT NOT NULL,
              time_range TEXT NOT NULL,
              target_type TEXT NOT NULL,
              target_ref TEXT NOT NULL,
              venue_id TEXT NOT NULL,
              device_ids_json TEXT NOT NULL,
              duration_sec INTEGER NOT NULL,
              countdown_sec INTEGER NOT NULL,
              binding_action TEXT NOT NULL,
              status TEXT NOT NULL,
              created_at_ms INTEGER NOT NULL
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS test_runs (
              run_id TEXT PRIMARY KEY,
              task_id TEXT NOT NULL DEFAULT '',
              venue_id TEXT NOT NULL DEFAULT '',
              started_at_ms INTEGER NOT NULL,
              ended_at_ms INTEGER NOT NULL,
              duration_sec INTEGER NOT NULL
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS test_run_slots (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id TEXT NOT NULL,
              slot INTEGER NOT NULL,
              user_id TEXT NOT NULL,
              count INTEGER NOT NULL,
              points_json TEXT NOT NULL
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS scores (
              id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              task_id TEXT NOT NULL,
              venue_id TEXT NOT NULL,
              student_id TEXT NOT NULL,
              slot INTEGER NOT NULL,
              final_count INTEGER NOT NULL,
              status TEXT NOT NULL,
              review_status TEXT NOT NULL,
              tested_at_ms INTEGER NOT NULL
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS exceptions (
              id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              task_id TEXT NOT NULL,
              venue_id TEXT NOT NULL,
              type TEXT NOT NULL,
              level TEXT NOT NULL,
              description TEXT NOT NULL,
              status TEXT NOT NULL,
              handle_remark TEXT NOT NULL DEFAULT '',
              created_at_ms INTEGER NOT NULL
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS settings (
              key TEXT PRIMARY KEY,
              value_json TEXT NOT NULL,
              updated_at_ms INTEGER NOT NULL
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS operation_logs (
              id TEXT PRIMARY KEY,
              module TEXT NOT NULL,
              action TEXT NOT NULL,
              target TEXT NOT NULL,
              detail_json TEXT NOT NULL,
              created_at_ms INTEGER NOT NULL
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS login_logs (
              id TEXT PRIMARY KEY,
              account TEXT NOT NULL,
              result TEXT NOT NULL,
              login_ip TEXT NOT NULL,
              created_at_ms INTEGER NOT NULL
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS flow_logs (
              id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              venue_id TEXT NOT NULL,
              phase TEXT NOT NULL,
              event_type TEXT NOT NULL,
              description TEXT NOT NULL,
              created_at_ms INTEGER NOT NULL
            )
            '''
        )

        ts = now_ms()
        _seed_if_empty(
            cur,
            'schools',
            'INSERT INTO schools (id,name,code,contact_name,contact_phone,status,created_at_ms) VALUES (?,?,?,?,?,?,?)',
            [('school_001', '示范学校', 'SCH001', '系统管理员', '13800000000', 'enabled', ts)],
        )
        _seed_if_empty(
            cur,
            'grades',
            'INSERT INTO grades (id,school_id,name,sort_order,status,created_at_ms) VALUES (?,?,?,?,?,?)',
            [
                ('grade_001', 'school_001', '初一', 1, 'enabled', ts),
                ('grade_002', 'school_001', '初二', 2, 'enabled', ts),
                ('grade_003', 'school_001', '初三', 3, 'enabled', ts),
            ],
        )
        _seed_if_empty(
            cur,
            'classes',
            'INSERT INTO classes (id,grade_id,name,teacher_name,student_count,status,created_at_ms) VALUES (?,?,?,?,?,?,?)',
            [
                ('class_001', 'grade_003', '初三(2)班', '王老师', 0, 'enabled', ts),
                ('class_002', 'grade_002', '初二(5)班', '李老师', 0, 'enabled', ts),
                ('class_003', 'grade_001', '初一(3)班', '赵老师', 0, 'enabled', ts),
                ('class_004', 'grade_003', '初三(1)班', '陈老师', 0, 'enabled', ts),
            ],
        )
        _seed_if_empty(
            cur,
            'students',
            'INSERT INTO students (id,student_no,name,gender,birth_date,grade_name,class_id,class_name,status,face_status,last_test_at_ms,created_at_ms) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
            [
                ('stu_001', 'S20260605001', '张同学', '男', '2011-03-02', '初三', 'class_001', '初三(2)班', 'active', 'ready', 0, ts),
                ('stu_002', 'S20260605002', '李同学', '女', '2011-08-16', '初三', 'class_001', '初三(2)班', 'active', 'ready', 0, ts),
                ('stu_003', 'S20260605003', '王同学', '男', '2012-06-22', '初二', 'class_002', '初二(5)班', 'active', 'ready', 0, ts),
                ('stu_004', 'S20260605004', '赵同学', '女', '2013-01-12', '初一', 'class_003', '初一(3)班', 'active', 'ready', 0, ts),
                ('stu_005', 'S20260605005', '陈同学', '男', '2011-11-03', '初三', 'class_004', '初三(1)班', 'active', 'ready', 0, ts),
                ('stu_006', 'S20260605006', '周同学', '女', '2012-09-13', '初二', 'class_002', '初二(5)班', 'active', 'pending', 0, ts),
            ],
        )
        _seed_if_empty(
            cur,
            'face_samples',
            'INSERT INTO face_samples (id,student_id,image_url,quality_score,is_primary,status,created_at_ms,updated_at_ms) VALUES (?,?,?,?,?,?,?,?)',
            [
                ('face_001', 'stu_001', '/static/faces/stu_001.jpg', 95.0, 1, 'ready', ts, ts),
                ('face_002', 'stu_002', '/static/faces/stu_002.jpg', 93.0, 1, 'ready', ts, ts),
                ('face_003', 'stu_003', '/static/faces/stu_003.jpg', 91.0, 1, 'ready', ts, ts),
                ('face_004', 'stu_004', '/static/faces/stu_004.jpg', 94.0, 1, 'ready', ts, ts),
                ('face_005', 'stu_005', '/static/faces/stu_005.jpg', 90.0, 1, 'ready', ts, ts),
                ('face_006', 'stu_006', '/static/faces/stu_006.jpg', 76.0, 1, 'low_quality', ts, ts),
            ],
        )
        _seed_if_empty(
            cur,
            'venues',
            'INSERT INTO venues (id,school_id,name,code,status,last_test_at_ms,created_at_ms) VALUES (?,?,?,?,?,?,?)',
            [('venue_001', 'school_001', '一号跳绳考场', 'VENUE001', 'online', 0, ts)],
        )
        _seed_if_empty(
            cur,
            'devices',
            'INSERT INTO devices (id,venue_id,device_no,name,type,ip_address,version,status,last_heartbeat_at_ms,created_at_ms) VALUES (?,?,?,?,?,?,?,?,?,?)',
            [
                ('device_001', 'venue_001', 'CAM001', '主摄像头', 'camera', '192.168.1.30', '1.0.0', 'online', ts, ts),
                ('device_002', 'venue_001', 'SCREEN001', '考场大屏', 'screen', '192.168.1.31', '1.0.0', 'online', ts, ts),
                ('device_003', 'venue_001', 'HOST001', '识别主机', 'host', '192.168.1.32', '1.0.0', 'online', ts, ts),
            ],
        )
        _seed_if_empty(
            cur,
            'tasks',
            'INSERT INTO tasks (id,name,test_item,test_date,time_range,target_type,target_ref,venue_id,device_ids_json,duration_sec,countdown_sec,binding_action,status,created_at_ms) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            [(
                'task_001',
                '初三体测跳绳示范任务',
                'jump_rope',
                '2026-06-10',
                '08:00-10:00',
                'class',
                'class_001',
                'venue_001',
                json.dumps(['device_001', 'device_002', 'device_003'], ensure_ascii=False),
                60,
                5,
                'wave',
                'published',
                ts,
            )],
        )

        for key, value in {
            'exam_params': {'durationSec': 60, 'countdownSec': 5, 'bindingAction': 'wave', 'resultStaySec': 15},
            'display_config': {'showSchoolName': True, 'showVenueName': True, 'resultStaySec': 15},
            'business_rules': {'groupSize': 5, 'autoMarkExceptionScore': True, 'autoAddRetest': True, 'faceQualityMin': 80, 'deviceOfflineThresholdSec': 20},
        }.items():
            cur.execute('INSERT OR IGNORE INTO settings (key,value_json,updated_at_ms) VALUES (?,?,?)', (key, json.dumps(value, ensure_ascii=False), ts))

        cur.execute('SELECT COUNT(*) AS c FROM operation_logs')
        if int(cur.fetchone()['c']) == 0:
            logs = [
                ('log_001', 'system', 'bootstrap', 'database', {'message': '初始化系统数据'}, ts - 3600_000),
                ('log_002', 'task', 'publish', 'task_001', {'message': '发布示范任务'}, ts - 1800_000),
            ]
            cur.executemany(
                'INSERT INTO operation_logs (id,module,action,target,detail_json,created_at_ms) VALUES (?,?,?,?,?,?)',
                [(a, b, c, d, json.dumps(e, ensure_ascii=False), f) for a, b, c, d, e, f in logs],
            )

        cur.execute('SELECT COUNT(*) AS c FROM login_logs')
        if int(cur.fetchone()['c']) == 0:
            cur.execute(
                'INSERT INTO login_logs (id,account,result,login_ip,created_at_ms) VALUES (?,?,?,?,?)',
                ('login_001', 'admin', 'success', '127.0.0.1', ts - 600_000),
            )

        _recount_class_sizes(cur)
        conn.commit()
    finally:
        conn.close()


def list_rows(sql: str, params: tuple = ()) -> list[dict]:
    conn = db_connect()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def fetch_row(sql: str, params: tuple = ()) -> dict | None:
    conn = db_connect()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def execute(sql: str, params: tuple = ()) -> None:
    conn = db_connect()
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def execute_many(sql: str, rows: list[tuple]) -> None:
    conn = db_connect()
    try:
        conn.executemany(sql, rows)
        conn.commit()
    finally:
        conn.close()


def upsert_setting(key: str, value: dict) -> None:
    ts = now_ms()
    execute(
        'INSERT INTO settings (key,value_json,updated_at_ms) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at_ms=excluded.updated_at_ms',
        (key, json.dumps(value, ensure_ascii=False), ts),
    )


def log_operation(module: str, action: str, target: str, detail: dict | None = None) -> None:
    execute(
        'INSERT INTO operation_logs (id,module,action,target,detail_json,created_at_ms) VALUES (?,?,?,?,?,?)',
        (f'log_{uuid.uuid4().hex[:12]}', module, action, target, json.dumps(detail or {}, ensure_ascii=False), now_ms()),
    )


def log_flow(run_id: str, venue_id: str, phase: str, event_type: str, description: str) -> None:
    execute(
        'INSERT INTO flow_logs (id,run_id,venue_id,phase,event_type,description,created_at_ms) VALUES (?,?,?,?,?,?,?)',
        (f'flow_{uuid.uuid4().hex[:12]}', run_id, venue_id, phase, event_type, description, now_ms()),
    )
