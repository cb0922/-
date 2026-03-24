@echo off
chcp 65001 >nul
title 一键打包 - 比赛通知爬虫
echo.
echo ========================================
echo    比赛通知爬虫 - 一键打包
echo ========================================
echo.
echo 本脚本将创建两种分发版本：
echo   1. 精简版 (dist/比赛通知爬虫.exe)
echo   2. 完整便携版 (dist/比赛通知爬虫_完整便携版/)
echo.
pause

REM 检查 Python
echo.
echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到 Python，请确保 Python 已安装并添加到 PATH
    pause
    exit /b 1
)
python --version
echo.

REM 安装打包工具
echo [2/3] 安装打包工具...
pip install pyinstaller -q
if errorlevel 1 (
    echo 安装失败，尝试使用镜像...
    pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple -q
)

REM 运行打包
echo.
echo [3/3] 开始打包...
echo.

REM 方法1：PyInstaller 单文件版
echo 正在打包单文件版本...
python build_exe.py --portable

REM 方法2：创建完整便携版
echo.
echo 正在创建完整便携版...
python create_portable.py

echo.
echo ========================================
echo    打包完成！
echo ========================================
echo.
echo 输出文件：
echo   1. dist/比赛通知爬虫.exe (单文件版，需要系统已安装依赖)
echo   2. dist/比赛通知爬虫_完整便携版/ (文件夹版，带依赖安装脚本)
echo.
echo 推荐使用：
echo   - 发给技术人员：单文件版
echo   - 发给普通用户：完整便携版 + 附带安装说明
echo.
pause
