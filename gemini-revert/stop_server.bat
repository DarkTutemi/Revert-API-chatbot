@echo off
chcp 65001 >nul
title Dừng Gemini Gateway Server

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING"') do (
    echo [*] Đang tắt Server (PID: %%a)...
    taskkill /f /pid %%a >nul 2>&1
)
echo [OK] Đã hoàn tất.
timeout /t 2 >nul
