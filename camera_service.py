import os
import time
from pathlib import Path
from typing import Optional

import cv2
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

try:
    from DNX64 import DNX64
except Exception:
    DNX64 = None  # type: ignore

APP_PORT = int(os.getenv("CAMERA_SERVICE_PORT", "12002"))
CAPTURE_DIR = Path(os.getenv("CAMERA_CAPTURE_DIR", str(Path(__file__).parent / "captures")))
CAM_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
FRAME_WIDTH = int(os.getenv("CAMERA_WIDTH", "1280"))
FRAME_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "960"))
FRAME_FPS = int(os.getenv("CAMERA_FPS", "30"))
DNX64_DLL_PATH = os.getenv("DNX64_DLL_PATH", "")
DNX64_DEVICE_INDEX = int(os.getenv("DNX64_DEVICE_INDEX", "0"))

CAPTURE_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="DNX64 Camera Service", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)

app.mount("/captures", StaticFiles(directory=str(CAPTURE_DIR)), name="captures")

_camera: Optional[cv2.VideoCapture] = None
_dnx64: Optional[object] = None


def _init_dnx64() -> Optional[object]:
    global _dnx64
    if _dnx64 is not None:
        return _dnx64
    if not DNX64 or not DNX64_DLL_PATH:
        return None
    try:
        _dnx64 = DNX64(DNX64_DLL_PATH)
        _dnx64.SetVideoDeviceIndex(DNX64_DEVICE_INDEX)
        time.sleep(0.1)
        return _dnx64
    except Exception:
        _dnx64 = None
        return None


def _init_camera() -> cv2.VideoCapture:
    global _camera
    if _camera is not None and _camera.isOpened():
        return _camera

    cam = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)
    cam.set(cv2.CAP_PROP_FPS, FRAME_FPS)
    cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc("M", "J", "P", "G"))
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cam.isOpened():
        raise HTTPException(status_code=503, detail="Camera not available")

    _camera = cam
    return cam


def _encode_frame(frame) -> bytes:
    ok, encoded = cv2.imencode(".jpg", frame)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to encode frame")
    return encoded.tobytes()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/stream")
async def stream(request: Request):
    base = str(request.base_url).rstrip("/")
    return {"stream_url": f"{base}/mjpeg"}


@app.get("/mjpeg")
async def mjpeg():
    cam = _init_camera()

    def generate():
        while True:
            ok, frame = cam.read()
            if not ok:
                time.sleep(0.2)
                continue
            payload = _encode_frame(frame)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + payload + b"\r\n"
            )
            time.sleep(max(0.0, 1.0 / max(FRAME_FPS, 1)))

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.post("/capture")
async def capture(payload: dict):
    cam = _init_camera()
    ok, frame = cam.read()
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to capture image")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    tool_id = payload.get("tool_id", 0)
    waypoint_index = payload.get("waypoint_index", 0)
    filename = f"capture_t{tool_id}_w{waypoint_index}_{timestamp}.jpg"
    path = CAPTURE_DIR / filename
    cv2.imwrite(str(path), frame)

    return {
        "image_id": filename,
        "image_url": f"/captures/{filename}",
        "captured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@app.post("/params")
async def set_params(payload: dict):
    cam = _init_camera()
    dnx64 = _init_dnx64()

    exposure = payload.get("exposure")
    gain = payload.get("gain")
    focus = payload.get("focus")
    auto_exposure = payload.get("autoExposure")
    auto_focus = payload.get("autoFocus")

    if auto_exposure is not None:
        try:
            cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1 if auto_exposure else 0)
        except Exception:
            pass
        if dnx64 is not None:
            try:
                dnx64.SetAutoExposure(DNX64_DEVICE_INDEX, 1 if auto_exposure else 0)
            except Exception:
                pass

    if exposure is not None:
        try:
            cam.set(cv2.CAP_PROP_EXPOSURE, float(exposure))
        except Exception:
            pass
        if dnx64 is not None:
            try:
                dnx64.SetExposureValue(DNX64_DEVICE_INDEX, int(exposure))
            except Exception:
                pass

    if gain is not None:
        try:
            cam.set(cv2.CAP_PROP_GAIN, float(gain))
        except Exception:
            pass

    if auto_focus is not None:
        try:
            cam.set(cv2.CAP_PROP_AUTOFOCUS, 1 if auto_focus else 0)
        except Exception:
            pass

    if focus is not None:
        try:
            cam.set(cv2.CAP_PROP_FOCUS, float(focus))
        except Exception:
            pass
        if dnx64 is not None:
            try:
                dnx64.SetLensPos(DNX64_DEVICE_INDEX, int(focus))
            except Exception:
                pass

    return JSONResponse({"status": "ok"})
