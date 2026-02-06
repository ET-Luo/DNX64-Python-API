if __name__ == "__main__":
    import os
    import time
    import cv2

    # Camera index, please change it if you have more than one camera,
    # i.e. webcam, connected to your PC until CAM_INDEX is been set to first Dino-Lite product.
    CAM_INDEX = int(os.getenv("CAM_INDEX", "1"))

    # Change CAM_INDEX to Dino-Lite camera index, which is based on the order of the camera connected to your PC.
    # Read the full doc of `cv2.VideoCapture()` at
    # https://docs.opencv.org/4.5.2/d8/dfe/classcv_1_1VideoCapture.html#aabce0d83aa0da9af802455e8cf5fd181 &
    # https://docs.opencv.org/3.4/dd/d43/tutorial_py_video_display.html

    def open_camera(backend: int):
        cap = cv2.VideoCapture(CAM_INDEX, backend)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 15)
        # Try common pixel formats (some USB microscopes require MJPG)
        for fourcc in ("MJPG", "YUY2"):
            try:
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*fourcc))
            except Exception:
                pass
        # Enable auto exposure where supported (DSHOW uses 0.75 for auto)
        try:
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
        except Exception:
            pass
        # Boost gain slightly to avoid near-black frames
        try:
            cap.set(cv2.CAP_PROP_GAIN, 8)
        except Exception:
            pass
        return cap

    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF]
    cap = None
    for backend in backends:
        candidate = open_camera(backend)
        if candidate.isOpened():
            cap = candidate
            break
        candidate.release()

    if cap is None or not cap.isOpened():
        print("Failed to open camera. Check index and permissions.")
        raise SystemExit(1)

    # Warm up a few frames
    for _ in range(10):
        cap.read()

    # Press ESC to exit preview window
    last_warn = 0.0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or frame is None or frame.size == 0:
            now = time.time()
            if now - last_warn > 1.5:
                print("Warning: empty frame (try different backend, format, or index)")
                last_warn = now
            key = cv2.waitKey(1)
            if key == 27:
                break
            continue
        # Detect near-black frames and suggest fixes
        mean_luma = frame.mean()
        if mean_luma < 5:
            now = time.time()
            if now - last_warn > 1.5:
                print("Warning: black frame (try different backend or increase exposure/gain)")
                last_warn = now
        cv2.imshow("frame", frame)
        key = cv2.waitKey(1)
        # ESC
        if key == 27:
            break
    cap.release()
    cv2.destroyAllWindows()
