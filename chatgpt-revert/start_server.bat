@echo off
chcp 65001 >nul
title ChatGPT Proxy Server (Port 3000)

echo ============================================================
echo   Khởi động ChatGPT Proxy Server (http://localhost:3000)
echo ============================================================
echo.

cd /d "%~dp0"

:: Kiểm tra port 3000 có đang bị chiếm không
netstat -ano | findstr ":3000.*LISTENING" >nul
if %errorlevel% equ 0 (
    echo [!] Cảnh báo: Port 3000 đã có tiến trình đang chạy.
    echo Đang tắt tiến trình cũ...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING"') do (
        taskkill /f /pid %%a >nul 2>&1
    )
    timeout /t 1 /nobreak >nul
)

echo [*] Đang khởi động Server FastAPI...
python main.py

pause
