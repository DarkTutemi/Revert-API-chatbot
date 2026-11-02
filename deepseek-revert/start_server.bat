@echo off
title DeepSeek Web Proxy Gateway (Port 3002)
cd /d "%~dp0"
python main.py
if errorlevel 1 pause
