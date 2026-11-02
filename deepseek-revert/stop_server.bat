@echo off
title Stop DeepSeek Gateway
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3002 ^| findstr LISTENING') do (
    echo Terminating PID %%a listening on port 3002...
    taskkill /f /pid %%a
)
echo DeepSeek Gateway stopped.
timeout /t 2 >nul
