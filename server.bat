@echo off
chcp 65001 >nul
title Quản lý Unified AI Gateway (Port 3000)
setlocal enabledelayedexpansion

cd /d "H:\reqble-mcp\unified-ai-gateway"

:MENU
cls
echo ================================================================
echo           UNIFIED AI GATEWAY - TRÌNH ĐIỀU KHIỂN (PORT 3000)
echo ================================================================

set "RUNNING_PID="
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do (
    set "RUNNING_PID=%%a"
)

if defined RUNNING_PID (
    echo  Trạng thái: [ĐANG BẬT] - PID: !RUNNING_PID! (http://localhost:3000)
) else (
    echo  Trạng thái: [ĐÃ TẮT] - Cổng 3000 đang sẵn sàng
)
echo ================================================================
echo.
echo   [1] Tự động Chuyển Đổi (Toggle: Đang tắt thì Bật, Đang bật thì Tắt)
echo   [2] BẬT Server (Start)
echo   [3] TẮT Server (Stop)
echo   [4] KHỞI ĐỘNG LẠI (Restart)
echo   [5] Mở Giao Diện Kiểm Thử (PySide6 GUI Tester)
echo   [0] Thoát
echo.
echo ================================================================
set /p opt=" Nhập lựa chọn của bạn [Mặc định 1]: "
if "%opt%"=="" set opt=1

if "%opt%"=="1" goto TOGGLE
if "%opt%"=="2" goto START_SERVER
if "%opt%"=="3" goto STOP_SERVER
if "%opt%"=="4" goto RESTART_SERVER
if "%opt%"=="5" goto OPEN_TESTER
if "%opt%"=="0" exit /b
goto MENU

:TOGGLE
if defined RUNNING_PID (
    goto STOP_SERVER
) else (
    goto START_SERVER
)

:START_SERVER
if defined RUNNING_PID (
    echo.
    echo [!] Server đã đang chạy với PID: !RUNNING_PID!.
    timeout /t 2 >nul
    goto MENU
)
echo.
echo [*] Đang khởi động Unified AI Gateway trên cổng 3000...
start "Unified AI Gateway (Port 3000)" cmd /k "cd /d H:\reqble-mcp\unified-ai-gateway && python main.py"
timeout /t 3 >nul
goto MENU

:STOP_SERVER
if not defined RUNNING_PID (
    echo.
    echo [!] Server hiện không chạy trên cổng 3000.
    timeout /t 2 >nul
    goto MENU
)
echo.
echo [*] Đang tắt tiến trình PID: !RUNNING_PID!...
taskkill /f /pid !RUNNING_PID! >nul 2>&1
echo [OK] Đã tắt Server thành công.
timeout /t 2 >nul
goto MENU

:RESTART_SERVER
echo.
echo [*] Đang dừng server cũ...
if defined RUNNING_PID (
    taskkill /f /pid !RUNNING_PID! >nul 2>&1
    timeout /t 2 >nul
)
echo [*] Đang khởi động lại server mới...
start "Unified AI Gateway (Port 3000)" cmd /k "cd /d H:\reqble-mcp\unified-ai-gateway && python main.py"
timeout /t 3 >nul
goto MENU

:OPEN_TESTER
echo.
echo [*] Đang mở PySide6 GUI Tester...
start "AI WebEngine Tester" cmd /c "cd /d H:\reqble-mcp && python gui_tester.py"
goto MENU
