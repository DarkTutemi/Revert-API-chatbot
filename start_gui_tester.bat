@echo off
title AI Reverse Proxy Gateway - PySide6 GUI Tester
cd /d "%~dp0"
python gui_tester.py
if errorlevel 1 pause
