@echo off
title AegisRegistry 1-Click Launcher
echo ========================================================
echo   Starting AegisRegistry Platform (Backend + UI)
echo ========================================================
cd /d "%~dp0"
python launch_all.py
pause
