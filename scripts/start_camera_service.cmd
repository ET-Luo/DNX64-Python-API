@echo off
set CAMERA_INDEX=%1
if "%CAMERA_INDEX%"=="" set CAMERA_INDEX=1

set PORT=%2
if "%PORT%"=="" set PORT=12002

set DNX64_DLL_PATH=%3
if "%DNX64_DLL_PATH%"=="" set DNX64_DLL_PATH=C:\\Program Files\\DNX64\\DNX64.dll
set DEVICE_INDEX=%4
if "%DEVICE_INDEX%"=="" set DEVICE_INDEX=0

set CAMERA_SERVICE_PORT=%PORT%
set DNX64_DEVICE_INDEX=%DEVICE_INDEX%
set DNX64_GAIN_INDEX=9
set CAMERA_EXPOSURE_MIN=1
set CAMERA_EXPOSURE_MAX=30000

python -m uvicorn camera_service:app --host 0.0.0.0 --port %PORT%
