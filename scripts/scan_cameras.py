import time

import cv2

MAX_INDEX = 10


def scan():
    results = []
    for idx in range(MAX_INDEX + 1):
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            continue

        # Give camera a moment to initialize
        time.sleep(0.1)
        ok, frame = cap.read()
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        if ok and frame is not None:
            results.append((idx, width, height, fps))

    if not results:
        print("No cameras detected.")
        return

    print("Detected cameras:")
    for idx, w, h, fps in results:
        fps_str = f"{fps:.1f}" if fps and fps > 0 else "--"
        print(f"- index {idx}: {w}x{h} @ {fps_str} fps")

    print("\nRecommendation:")
    print("Pick the index that matches your USB camera resolution/behavior.")
    print("Then start service with CAMERA_INDEX set to that index.")


if __name__ == "__main__":
    scan()
