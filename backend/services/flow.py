import json
import threading
import time
import uuid
from typing import Any

from fastapi import HTTPException

from backend.db import db_connect, log_flow, now_ms

FLOW_LOCK = threading.Lock()
FLOW_STATE: dict[str, Any] = {}
CAMERA_CONFIG = {'mode': 'SIM', 'index': 0}
WORKER_STARTED = False


def empty_slots() -> list[dict[str, Any]]:
    return [
        {'slot': i + 1, 'user': None, 'confirmedInfo': False, 'confirmedPosition': False}
        for i in range(5)
    ]


def flow_reset() -> dict[str, Any]:
    global FLOW_STATE
    FLOW_STATE = {
        'phase': 'idle',
        'slots': empty_slots(),
        'prompt_slot': 0,
        'run_id': '',
        'task_id': 'task_001',
        'venue_id': 'venue_001',
        'duration_sec': 60,
        'started_at_ms': 0,
        'ended_at_ms': 0,
        'counts': [0, 0, 0, 0, 0],
        'points': [[], [], [], [], []],
        'cadences_ms': [470, 390, 520, 430, 610],
        '_last_inc_ms': [0, 0, 0, 0, 0],
        '_persisted_run_id': '',
        '_pending_students': [],
    }
    return FLOW_STATE


def public_state(ts_ms: int | None = None) -> dict[str, Any]:
    with FLOW_LOCK:
        phase = FLOW_STATE.get('phase', 'idle')
        run_id = str(FLOW_STATE.get('run_id') or '')
        duration_sec = int(FLOW_STATE.get('duration_sec') or 0)
        prompt_slot = int(FLOW_STATE.get('prompt_slot') or 0)
        slots = json.loads(json.dumps(FLOW_STATE.get('slots') or []))
        counts = list(FLOW_STATE.get('counts') or [0, 0, 0, 0, 0])
        started_at_ms = int(FLOW_STATE.get('started_at_ms') or 0)

    t = ts_ms if ts_ms is not None else now_ms()
    remaining = 0
    if phase == 'running' and started_at_ms > 0:
        elapsed_ms = max(0, t - started_at_ms)
        remaining = max(0, int(duration_sec - (elapsed_ms / 1000.0)))

    ranking = [{'slot': i + 1, 'count': counts[i]} for i in range(5)]
    ranking.sort(key=lambda item: (-item['count'], item['slot']))

    slot_status = ['OK'] * 5
    if phase == 'running':
        sec = int(t / 1000)
        for i in range(5):
            marker = (sec + i * 3) % 20
            if 6 <= marker <= 7:
                slot_status[i] = 'OUT_OF_ROI'
            elif 10 <= marker <= 11:
                slot_status[i] = 'OCCLUDED'
            elif 15 <= marker <= 16:
                slot_status[i] = 'TRACK_LOST'

    return {
        'phase': phase,
        'runId': run_id,
        'durationSec': duration_sec,
        'remainingSec': remaining,
        'counts': counts,
        'ranking': ranking,
        'promptSlot': prompt_slot,
        'slots': slots,
        'slotStatus': slot_status,
        'ts': t,
    }


def db_fetch_students(limit: int = 5) -> list[dict[str, Any]]:
    conn = db_connect()
    try:
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT id, student_no, name, class_name, gender, face_status
            FROM students
            WHERE status = 'active'
            ORDER BY id
            LIMIT ?
            ''',
            (limit,),
        )
        rows = []
        for row in cur.fetchall():
            rows.append(
                {
                    'id': row['id'],
                    'name': row['name'],
                    'className': row['class_name'],
                    'gender': row['gender'],
                    'studentId': row['student_no'],
                    'hasFace': row['face_status'] == 'ready',
                }
            )
        return rows
    finally:
        conn.close()


def persist_run_if_needed() -> None:
    with FLOW_LOCK:
        run_id = str(FLOW_STATE.get('run_id') or '')
        if not run_id or FLOW_STATE.get('_persisted_run_id') == run_id or FLOW_STATE.get('phase') != 'result':
            return
        started_at_ms = int(FLOW_STATE.get('started_at_ms') or 0)
        ended_at_ms = int(FLOW_STATE.get('ended_at_ms') or 0) or now_ms()
        duration_sec = int(FLOW_STATE.get('duration_sec') or 60)
        task_id = str(FLOW_STATE.get('task_id') or '')
        venue_id = str(FLOW_STATE.get('venue_id') or '')
        slots = json.loads(json.dumps(FLOW_STATE.get('slots') or []))
        counts = list(FLOW_STATE.get('counts') or [0, 0, 0, 0, 0])
        points = json.loads(json.dumps(FLOW_STATE.get('points') or [[], [], [], [], []]))

    conn = db_connect()
    try:
        cur = conn.cursor()
        cur.execute(
            'INSERT OR REPLACE INTO test_runs (run_id,task_id,venue_id,started_at_ms,ended_at_ms,duration_sec) VALUES (?,?,?,?,?,?)',
            (run_id, task_id, venue_id, started_at_ms, ended_at_ms, duration_sec),
        )
        cur.execute('DELETE FROM test_run_slots WHERE run_id = ?', (run_id,))
        cur.execute('DELETE FROM scores WHERE run_id = ?', (run_id,))
        for i in range(5):
            user = slots[i].get('user') if i < len(slots) else None
            user_id = user.get('id') if isinstance(user, dict) else ''
            cur.execute(
                'INSERT INTO test_run_slots (run_id,slot,user_id,count,points_json) VALUES (?,?,?,?,?)',
                (run_id, i + 1, user_id, int(counts[i]), json.dumps(points[i], ensure_ascii=False)),
            )
            cur.execute(
                'INSERT INTO scores (id,run_id,task_id,venue_id,student_id,slot,final_count,status,review_status,tested_at_ms) VALUES (?,?,?,?,?,?,?,?,?,?)',
                (
                    f'score_{uuid.uuid4().hex[:12]}',
                    run_id,
                    task_id,
                    venue_id,
                    user_id,
                    i + 1,
                    int(counts[i]),
                    'normal',
                    'none',
                    ended_at_ms,
                ),
            )
            if user_id:
                cur.execute('UPDATE students SET last_test_at_ms = ? WHERE id = ?', (ended_at_ms, user_id))
        conn.commit()
    finally:
        conn.close()

    with FLOW_LOCK:
        FLOW_STATE['_persisted_run_id'] = run_id

    log_flow(run_id, venue_id, 'result', 'persist', '测试结果已写入数据库')


def flow_worker() -> None:
    while True:
        time.sleep(0.05)
        t = now_ms()
        to_persist = False
        with FLOW_LOCK:
            if FLOW_STATE.get('phase') != 'running':
                continue
            started_at_ms = int(FLOW_STATE.get('started_at_ms') or 0)
            duration_ms = int(FLOW_STATE.get('duration_sec') or 0) * 1000
            if started_at_ms <= 0:
                continue

            last_inc = FLOW_STATE.get('_last_inc_ms') or [0, 0, 0, 0, 0]
            cadences = FLOW_STATE.get('cadences_ms') or [470, 390, 520, 430, 610]
            counts = FLOW_STATE.get('counts') or [0, 0, 0, 0, 0]
            points = FLOW_STATE.get('points') or [[], [], [], [], []]

            for i in range(5):
                if last_inc[i] <= 0:
                    last_inc[i] = started_at_ms
                while t - last_inc[i] >= int(cadences[i]):
                    last_inc[i] += int(cadences[i])
                    counts[i] = int(counts[i]) + 1
                    points[i].append({'t': int(last_inc[i] - started_at_ms), 'c': int(counts[i])})

            FLOW_STATE['_last_inc_ms'] = last_inc
            FLOW_STATE['counts'] = counts
            FLOW_STATE['points'] = points

            if t - started_at_ms >= duration_ms:
                FLOW_STATE['phase'] = 'result'
                FLOW_STATE['ended_at_ms'] = t
                to_persist = True

        if to_persist:
            persist_run_if_needed()


def ensure_worker_started() -> None:
    global WORKER_STARTED
    if WORKER_STARTED:
        return
    with FLOW_LOCK:
        if not FLOW_STATE:
            flow_reset()
    thread = threading.Thread(target=flow_worker, daemon=True, name='jump-rope-flow-worker')
    thread.start()
    WORKER_STARTED = True


def get_camera_config() -> dict[str, Any]:
    return dict(CAMERA_CONFIG)


def set_camera_config(mode: str, index: int) -> dict[str, Any]:
    CAMERA_CONFIG['mode'] = mode if mode in {'SIM', 'USB'} else 'SIM'
    CAMERA_CONFIG['index'] = int(index)
    return get_camera_config()


def start_recognition() -> dict[str, Any]:
    students = db_fetch_students(5)
    with FLOW_LOCK:
        FLOW_STATE['phase'] = 'confirming_info'
        FLOW_STATE['prompt_slot'] = 0
        FLOW_STATE['run_id'] = ''
        FLOW_STATE['ended_at_ms'] = 0
        FLOW_STATE['counts'] = [0, 0, 0, 0, 0]
        FLOW_STATE['points'] = [[], [], [], [], []]
        FLOW_STATE['_last_inc_ms'] = [0, 0, 0, 0, 0]
        FLOW_STATE['_persisted_run_id'] = ''
        slots = empty_slots()
        # 逐个识别：只分配第1个站位的学生，其余排队等待
        if len(students) > 0:
            slots[0]['user'] = students[0]
        FLOW_STATE['slots'] = slots
        FLOW_STATE['_pending_students'] = students[1:]
    log_flow('', str(FLOW_STATE.get('venue_id') or ''), 'confirming_info', 'recognition_start', '开始逐个识别站位')
    return {'ok': True, 'slots': json.loads(json.dumps(FLOW_STATE['slots']))}


def confirm_info(slot: int, confirmed: bool) -> dict[str, Any]:
    with FLOW_LOCK:
        if slot < 1 or slot > 5:
            raise HTTPException(status_code=400, detail='BAD_SLOT')
        if FLOW_STATE.get('phase') != 'confirming_info':
            raise HTTPException(status_code=409, detail='NOT_IN_CONFIRMING')
        FLOW_STATE['slots'][slot - 1]['confirmedInfo'] = bool(confirmed)
        # 当前站位确认后，分配下一个站位的学生（逐个识别）
        pending = FLOW_STATE.get('_pending_students', [])
        if pending:
            next_slot_idx = slot  # 0-based: slot 1→index 0, next is slot 2→index 1
            if next_slot_idx < 5:
                FLOW_STATE['slots'][next_slot_idx]['user'] = pending[0]
                FLOW_STATE['_pending_students'] = pending[1:]
        if all(item.get('confirmedInfo') for item in FLOW_STATE['slots']):
            FLOW_STATE['phase'] = 'binding'
            FLOW_STATE['prompt_slot'] = 1
            FLOW_STATE['_pending_students'] = []
    log_flow('', str(FLOW_STATE.get('venue_id') or ''), str(FLOW_STATE.get('phase') or ''), 'confirm_info', f'站位 {slot} 身份确认完成')
    return {'ok': True, 'state': public_state()}


def confirm_gesture(slot: int) -> dict[str, Any]:
    with FLOW_LOCK:
        if FLOW_STATE.get('phase') != 'binding':
            raise HTTPException(status_code=409, detail={'error': 'NOT_BINDING', 'promptSlot': int(FLOW_STATE.get('prompt_slot') or 0)})
        prompt = int(FLOW_STATE.get('prompt_slot') or 0)
        if slot != prompt:
            raise HTTPException(status_code=409, detail={'error': 'NOT_PROMPTED', 'promptSlot': prompt})
        FLOW_STATE['slots'][slot - 1]['confirmedPosition'] = True
        nxt = prompt + 1
        if nxt <= 5:
            FLOW_STATE['prompt_slot'] = nxt
        else:
            FLOW_STATE['prompt_slot'] = 0
            FLOW_STATE['phase'] = 'ready'
    log_flow('', str(FLOW_STATE.get('venue_id') or ''), str(FLOW_STATE.get('phase') or ''), 'binding', f'站位 {slot} 完成动作绑定')
    return {'ok': True, 'state': public_state()}


def start_test(duration_sec: int) -> dict[str, Any]:
    duration_sec = max(5, min(600, int(duration_sec)))
    with FLOW_LOCK:
        if FLOW_STATE.get('phase') != 'ready':
            raise HTTPException(status_code=409, detail='NOT_READY')
        run_id = f'r_{uuid.uuid4().hex[:12]}'
        started = now_ms()
        FLOW_STATE['phase'] = 'running'
        FLOW_STATE['run_id'] = run_id
        FLOW_STATE['duration_sec'] = duration_sec
        FLOW_STATE['started_at_ms'] = started
        FLOW_STATE['ended_at_ms'] = 0
        FLOW_STATE['counts'] = [0, 0, 0, 0, 0]
        FLOW_STATE['points'] = [[], [], [], [], []]
        FLOW_STATE['_last_inc_ms'] = [started, started, started, started, started]
        FLOW_STATE['_persisted_run_id'] = ''
        venue_id = str(FLOW_STATE.get('venue_id') or '')
    log_flow(run_id, venue_id, 'running', 'start', '开始正式计数')
    return {'ok': True, 'state': public_state()}


def stop_test() -> dict[str, Any]:
    with FLOW_LOCK:
        if FLOW_STATE.get('phase') != 'running':
            raise HTTPException(status_code=409, detail='NOT_RUNNING')
        FLOW_STATE['phase'] = 'result'
        FLOW_STATE['ended_at_ms'] = now_ms()
        run_id = str(FLOW_STATE.get('run_id') or '')
        venue_id = str(FLOW_STATE.get('venue_id') or '')
    persist_run_if_needed()
    log_flow(run_id, venue_id, 'result', 'stop', '测试手动结束')
    return {'ok': True, 'state': public_state()}


def reset_system() -> dict[str, Any]:
    with FLOW_LOCK:
        flow_reset()
    return {'ok': True, 'state': public_state()}


def svg_frame(ts_ms: int) -> str:
    with FLOW_LOCK:
        phase = FLOW_STATE.get('phase') or 'idle'
        counts = list(FLOW_STATE.get('counts') or [0, 0, 0, 0, 0])
        prompt = int(FLOW_STATE.get('prompt_slot') or 0)

    w, h = 900, 520
    pad = 22
    gap = 14
    box_w = int((w - pad * 2 - gap * 4) / 5)
    box_h = 240
    top = 90

    def rect(i: int) -> str:
        x = pad + i * (box_w + gap)
        y = top
        highlighted = (phase == 'binding') and (prompt == i + 1)
        stroke = '#1db46c' if highlighted else 'rgba(20,40,60,0.26)'
        fill = 'rgba(255,255,255,0.10)' if highlighted else 'rgba(255,255,255,0.06)'
        return f'<rect x="{x}" y="{y}" rx="18" ry="18" width="{box_w}" height="{box_h}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>'

    def text(i: int) -> str:
        x = pad + i * (box_w + gap) + 18
        y = top + 34
        count = counts[i]
        return (
            f'<text x="{x}" y="{y}" font-size="20" font-family="ui-sans-serif,system-ui" fill="rgba(0,0,0,0.72)">站位 {i + 1}</text>'
            f'<text x="{x}" y="{y + 44}" font-size="44" font-weight="800" font-family="ui-sans-serif,system-ui" fill="rgba(0,0,0,0.78)">{count}</text>'
        )

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">']
    parts.append('<defs><linearGradient id="g1" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d7fff9"/><stop offset="1" stop-color="#dbe9ff"/></linearGradient></defs>')
    parts.append(f'<rect x="0" y="0" width="{w}" height="{h}" fill="url(#g1)"/>')
    parts.append('<text x="22" y="46" font-size="22" font-weight="900" font-family="ui-sans-serif,system-ui" fill="rgba(0,0,0,0.76)">单摄像头画面（FastAPI 模拟）</text>')
    parts.append(f'<text x="22" y="72" font-size="14" font-family="ui-sans-serif,system-ui" fill="rgba(0,0,0,0.55)">phase: {phase} · ts: {ts_ms}</text>')
    for i in range(5):
        parts.append(rect(i))
        parts.append(text(i))
    parts.append('</svg>')
    return ''.join(parts)
