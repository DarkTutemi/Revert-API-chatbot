@echo off
chcp 65001 >nul
title Gemini Gateway Server (Port 3000)

cd /d "%~dp0"

netstat -ano | findstr ":3000.*LISTENING" >nul
if %errorlevel% equ 0 (
    echo [!] Port 3000 đang bận. Đang tắt tiến trình cũ...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING"') do (
        taskkill /f /pid %%a >nul 2>&1
    )
    timeout /t 1 /nobreak >nul
)

echo [*] Khởi động Gemini Gateway...
python main.py
pause
