import time

import cv2

INDEXES = list(range(0, 6))
BACKENDS = [
    ("DSHOW", cv2.CAP_DSHOW),
    ("MSMF", cv2.CAP_MSMF),
]
FOURCCS = ["MJPG", "YUY2"]
RESOLUTIONS = [(640, 480), (1280, 720)]


def try_open(index: int, backend_name: str, backend: int, fourcc: str, size):
    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        cap.release()
        return None

    width, height = size
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, 15)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*fourcc))
    try:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
    except Exception:
        pass

    # Warm up
    for _ in range(8):
        cap.read()

    ret, frame = cap.read()
    if not ret or frame is None or frame.size == 0:
        cap.release()
        return None

    mean_luma = float(frame.mean())
    cap.release()
    return {
        "index": index,
        "backend": backend_name,
        "fourcc": fourcc,
        "width": width,
        "height": height,
        "mean_luma": mean_luma,
    }


def main():
    candidates = []
    print("Scanning cameras...")
    for index in INDEXES:
        for backend_name, backend in BACKENDS:
            for fourcc in FOURCCS:
                for size in RESOLUTIONS:
                    result = try_open(index, backend_name, backend, fourcc, size)
                    if result:
                        candidates.append(result)
                        print(
                            f"OK  index={index} backend={backend_name} fmt={fourcc} size={size[0]}x{size[1]} mean={result['mean_luma']:.1f}"
                        )
                    else:
                        print(
                            f"FAIL index={index} backend={backend_name} fmt={fourcc} size={size[0]}x{size[1]}"
                        )

    if not candidates:
        print("\nNo working camera configuration found.")
        print("Check: device power, USB cable, driver, and other apps using the camera.")
        return

    # Prefer brighter frames (not black) and higher resolution
    candidates.sort(key=lambda x: (x["mean_luma"], x["width"] * x["height"]), reverse=True)
    best = candidates[0]
    print("\nRecommended settings:")
    print(
        f"index={best['index']} backend={best['backend']} fmt={best['fourcc']} size={best['width']}x{best['height']} mean={best['mean_luma']:.1f}"
    )


if __name__ == "__main__":
    main()
