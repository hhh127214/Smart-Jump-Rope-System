from fastapi import APIRouter, Body
from fastapi.responses import Response

from backend.services.flow import (
    confirm_gesture,
    confirm_info,
    get_camera_config,
    public_state,
    reset_system,
    set_camera_config,
    start_recognition,
    start_test,
    stop_test,
    svg_frame,
)
from backend.db import now_ms

router = APIRouter(prefix='/api', tags=['screen'])


@router.get('/health')
def health() -> dict:
    return {'ok': True, 'backend': 'fastapi'}


@router.get('/camera/config')
def get_camera() -> dict:
    return {'config': get_camera_config()}


@router.post('/camera/config')
def update_camera(payload: dict = Body(default_factory=dict)) -> dict:
    mode = str(payload.get('mode') or 'SIM')
    index = int(payload.get('index') or 0)
    return {'ok': True, 'config': set_camera_config(mode, index)}


@router.post('/system/reset')
def system_reset() -> dict:
    return reset_system()


@router.post('/recognition/start')
def recognition_start() -> dict:
    return start_recognition()


@router.post('/slots/confirm_info')
def slot_confirm(payload: dict = Body(default_factory=dict)) -> dict:
    return confirm_info(int(payload.get('slot') or 0), bool(payload.get('confirmed', True)))


@router.post('/binding/gesture')
def binding_gesture(payload: dict = Body(default_factory=dict)) -> dict:
    return confirm_gesture(int(payload.get('slot') or 0))


@router.post('/test/start')
def test_start(payload: dict = Body(default_factory=dict)) -> dict:
    return start_test(int(payload.get('durationSec') or 60))


@router.post('/test/stop')
def test_stop() -> dict:
    return stop_test()


@router.get('/test/metrics')
def test_metrics() -> dict:
    return public_state()


@router.get('/camera/frame.svg')
def camera_frame(ts: int | None = None, t: int | None = None) -> Response:
    current = ts or t or now_ms()
    return Response(content=svg_frame(int(current)), media_type='image/svg+xml; charset=utf-8')


# === 后期摄像头算法接入预留端点 ===

@router.post('/camera/faces')
def push_faces(payload: dict = Body(default_factory=dict)) -> dict:
    """摄像头人脸识别回调（后期接入真实 SDK 时使用）"""
    faces = payload.get('faces', [])
    return {'ok': True, 'received': len(faces)}


@router.post('/camera/counts')
def push_counts(payload: dict = Body(default_factory=dict)) -> dict:
    """跳绳计数回调（后期接入姿态检测算法时使用）"""
    counts = payload.get('counts', [])
    return {'ok': True, 'received': len(counts)}
