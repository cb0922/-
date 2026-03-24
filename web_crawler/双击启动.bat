@echo off
chcp 65001 >nul
title 比赛通知爬虫启动器
echo.
echo ========================================
echo    比赛通知爬虫 - 启动器
echo ========================================
echo.
echo 正在检查环境并启动...
echo.

python "启动器.py"

if errorlevel 1 (
    echo.
    echo 启动失败，请检查上方错误信息
    pause
)
