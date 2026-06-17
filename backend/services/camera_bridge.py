"""
摄像头人脸识别 & 跳绳计数桥接层
================================
后期接入真实摄像头 SDK / 算法时，只需修改本文件的三个函数：
    1. detect_faces()          -> 返回镜头拍到的人脸列表
    2. track_slot_status()     -> 返回每个站位的实时跟踪状态
    3. count_jump_events()     -> 返回当前帧各站位的跳绳增量

当前为 MOCK 模拟实现。
切换方式：修改 CAMERA_CONFIG['engine'] 为 'REAL'
"""

CAMERA_CONFIG = {
    'mode': 'SIM',
    'index': 0,
    'engine': 'MOCK',  # MOCK | REAL — 后期切换到 REAL 接入真实 SDK
}


def get_camera_config() -> dict:
    return CAMERA_CONFIG


from backend.db import db_connect


def _fetch_students(count: int) -> list[dict]:
    """供 _mock_detect_faces 内部使用"""
    db = db_connect()
    cur = db.execute('SELECT id, name, student_no FROM students ORDER BY id ASC LIMIT ?', (count,))
    rows = cur.fetchall()
    return [dict(r) for r in rows] if rows else []


def detect_faces() -> list[dict]:
    """
    返回镜头当前拍到的人脸列表（包含学生信息与站位编号）。
    [
        {"student_id": "2024001", "name": "张三", "id": 1, "slot": 1},
        ...
    ]
    后期替换为真实模型推理结果。
    """
    cfg = get_camera_config()
    if cfg.get('engine') == 'REAL':
        return _real_detect_faces()
    return _mock_detect_faces()


def track_slot_status() -> list[str]:
    """
    返回 5 个站位的实时跟踪状态。
    ["OK", "OUT_OF_ROI", "OK", "OCCLUDED", "TRACK_LOST"]
    后期替换为摄像头实时跟踪结果。
    """
    cfg = get_camera_config()
    if cfg.get('engine') == 'REAL':
        return _real_track_slot_status()
    return _mock_track_slot_status()


def count_jump_events() -> list[int]:
    """
    返回各站位的跳绳增量（每次调用返回本次检测到的新跳绳次数）。
    [0, 1, 0, 0, 2] 表示站位 2 跳了 1 次，站位 5 跳了 2 次。
    后期替换为人体姿态检测 + 过绳判定。
    """
    cfg = get_camera_config()
    if cfg.get('engine') == 'REAL':
        return _real_count_jump_events()
    return _mock_count_jump_events()


# ============================================================
#  MOCK 模拟实现（后期替换为真实实现）
# ============================================================

def _mock_detect_faces() -> list[dict]:
    students = _fetch_students(5)
    results = []
    for i, s in enumerate(students):
        results.append({
            'student_id': s.get('student_no', ''),
            'name': s.get('name', ''),
            'id': s.get('id', ''),
            'slot': i + 1,
        })
    return results


def _mock_track_slot_status() -> list[str]:
    return ['OK', 'OK', 'OK', 'OK', 'OK']


def _mock_count_jump_events() -> list[int]:
    return [0, 0, 0, 0, 0]


# ============================================================
#  REAL 实现（后期填写真实 SDK / 算法逻辑）
# ============================================================

def _real_detect_faces() -> list[dict]:
    """TODO: 接入真实人脸识别 SDK（OpenCV / MediaPipe / 自研模型）"""
    return []


def _real_track_slot_status() -> list[str]:
    """TODO: 接入摄像头实时跟踪结果"""
    return ['OK', 'OK', 'OK', 'OK', 'OK']


def _real_count_jump_events() -> list[int]:
    """TODO: 接入人体姿态检测 + 过绳计数算法"""
    return [0, 0, 0, 0, 0]
