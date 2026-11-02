@echo off
chcp 65001 >nul
title Quản lý ChatGPT Proxy Server

cd /d "%~dp0"

netstat -ano | findstr ":3000.*LISTENING" >nul
if %errorlevel% equ 0 (
    echo ============================================================
    echo   Server đang BẬT. Tiến hành TẮT...
    echo ============================================================
    call stop_server.bat
) else (
    echo ============================================================
    echo   Server đang TẮT. Tiến hành BẬT...
    echo ============================================================
    start "" cmd /k "start_server.bat"
)
