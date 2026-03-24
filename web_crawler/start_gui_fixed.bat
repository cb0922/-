@echo off
chcp 65001 >nul
title Competition Notice Crawler - Fixed

cd /d "%~dp0"
echo Current directory: %cd%
echo.

REM Check Python
where python >nul 2>nul
if errorlevel 1 (
    echo [Error] Python not found
    pause
    exit /b 1
)

python start_fixed.py
pause
