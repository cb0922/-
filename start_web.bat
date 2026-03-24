@echo off
chcp 65001 >nul

:: 比赛通知爬虫 Web 服务启动脚本 (Windows)

echo ======================================
echo    Web Crawler Web Server
echo ======================================

:: 检查是否在项目根目录
if not exist "web_crawler" (
    echo 错误：请在项目根目录运行此脚本
    pause
    exit /b 1
)

:: 检查虚拟环境
if not exist ".venv" (
    echo 创建虚拟环境...
    python -m venv .venv
)

:: 激活虚拟环境
echo 激活虚拟环境...
call .venv\Scripts\activate.bat

:: 安装依赖
echo 安装依赖...
pip install -q -r web_server\requirements.txt

:: 创建必要的目录
echo 创建目录...
if not exist "web_server\uploads" mkdir web_server\uploads
if not exist "web_server\output\documents" mkdir web_server\output\documents
if not exist "web_server\output\reports" mkdir web_server\output\reports
if not exist "web_server\output\word_reports" mkdir web_server\output\word_reports
if not exist "web_server\output\data" mkdir web_server\output\data

:: 启动服务
echo.
echo ======================================
echo   服务启动中...
echo   访问地址: http://localhost:8000
echo   API 文档: http://localhost:8000/docs
echo ======================================
echo.

cd web_server
set PYTHONPATH=..
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
