@echo off
chcp 65001 >nul
title 比赛通知爬虫
color 0A

:: 切换到脚本所在目录（关键！确保工作目录正确）
cd /d "%~dp0"

echo.
echo  ========================================
echo    比赛通知爬虫 - 启动中...
echo  ========================================
echo.
echo  当前工作目录: %cd%
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [错误] 未检测到 Python！
    echo  请先运行 "一键安装.bat" 进行安装
    pause
    exit /b 1
)

:: 检查关键依赖
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo  [错误] 依赖未安装！
    echo  请先运行 "一键安装.bat" 进行安装
    pause
    exit /b 1
)

:: 启动程序
python 启动器.py

if errorlevel 1 (
    echo.
    echo  [错误] 程序异常退出
    pause
)

exit /b 0
