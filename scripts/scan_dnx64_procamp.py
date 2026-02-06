import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from DNX64 import DNX64
except Exception as e:
    raise SystemExit(f"Failed to import DNX64: {e}")

DLL_PATH = os.getenv(
    "DNX64_DLL_PATH",
    r"C:\\Program Files\\DNX64\\DNX64.dll",
)
DEVICE_INDEX = int(os.getenv("DNX64_DEVICE_INDEX", "0"))
MAX_INDEX = int(os.getenv("DNX64_PROCAMP_MAX", "32"))


def main():
    print(f"Using DLL: {DLL_PATH}")
    microscope = DNX64(DLL_PATH)
    microscope.SetVideoDeviceIndex(DEVICE_INDEX)
    time.sleep(0.1)

    candidates = []
    for idx in range(MAX_INDEX + 1):
        try:
            _, min_val, max_val, step, default = microscope.GetVideoProcAmpValueRange(idx)
            candidates.append((idx, min_val, max_val, step, default))
            print(f"index={idx} min={min_val} max={max_val} step={step} default={default}")
        except Exception:
            continue

    if not candidates:
        print("No valid VideoProcAmp ranges found.")
        return

    print("\nSet environment variables:")
    print("DNX64_EXPOSURE_INDEX=<index>")
    print("DNX64_GAIN_INDEX=<index>")
    print("\nChoose the index whose range matches Exposure/Gain per your device manual.")


if __name__ == "__main__":
    main()
