@echo off
chcp 65001 >nul
title Dừng ChatGPT Proxy Server

echo ============================================================
echo   Dừng ChatGPT Proxy Server (Port 3000)
echo ============================================================
echo.

setlocal enabledelayedexpansion
set "FOUND=0"

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING"') do (
    set "FOUND=1"
    echo [*] Tìm thấy Server (PID: %%a), đang tắt...
    taskkill /f /pid %%a >nul 2>&1
    if !errorlevel! equ 0 (
        echo [OK] Đã tắt Server thành công.
    ) else (
        echo [!] Không thể tắt PID %%a.
    )
)

if "!FOUND!"=="0" (
    echo [i] Server không chạy (Port 3000 đang trống).
)

echo.
timeout /t 3
