@echo off
chcp 65001 >nul
title 比赛通知爬虫 - 一键修复工具
color 0B

echo.
echo =============================================
echo      比赛通知爬虫 - 一键修复工具
echo =============================================
echo.
echo  正在启动修复程序...
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  错误: 未找到 Python，请确保 Python 已安装并添加到 PATH
    pause
    exit /b 1
)

REM 运行修复脚本
python "%~dp0一键修复.py"

if errorlevel 1 (
    echo.
    echo 修复过程出现问题，请查看上方错误信息
    pause
    exit /b 1
)

exit /b 0
