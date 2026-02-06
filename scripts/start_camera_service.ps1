param(
  [int]$CameraIndex = 1,
  [int]$Port = 12002,
  [string]$DllPath = "C:\\Program Files\\DNX64\\DNX64.dll,
  [int]$DeviceIndex = 0
)

$env:CAMERA_INDEX = "$CameraIndex"
$env:CAMERA_SERVICE_PORT = "$Port"
$env:DNX64_DEVICE_INDEX = "$DeviceIndex"

if ($DllPath -ne "") {
  $env:DNX64_DLL_PATH = $DllPath
}

python -m uvicorn camera_service:app --host 0.0.0.0 --port $Port
