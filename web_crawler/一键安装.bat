@echo off
chcp 65001 >nul
title 比赛通知爬虫 - 一键安装
color 0A

:: ========================================
:: 比赛通知爬虫 - 一键安装脚本
:: 功能：自动检测环境、安装依赖、启动程序
:: ========================================

:: 切换到脚本所在目录（关键！确保工作目录正确）
cd /d "%~dp0"

echo.
echo  ========================================
echo    比赛通知爬虫 - 一键安装
echo  ========================================
echo.
echo  当前工作目录: %cd%
echo.

:: 检查 Python
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [错误] 未检测到 Python！
    echo.
    echo  请按以下步骤安装 Python：
    echo  1. 访问 https://www.python.org/downloads/
    echo  2. 下载 Python 3.8 或更高版本
    echo  3. 安装时务必勾选 "Add Python to PATH"
    echo.
    echo  安装完成后重新运行此脚本。
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
echo  [OK] 检测到 %PYTHON_VERSION%

:: 检查 pip
echo.
echo [2/4] 检查 pip 包管理器...
pip --version >nul 2>&1
if errorlevel 1 (
    echo  [错误] pip 未安装！
    echo  请重新安装 Python 并勾选 "Add Python to PATH"
    pause
    exit /b 1
)
echo  [OK] pip 正常

:: 安装依赖
echo.
echo [3/4] 安装依赖包 (使用清华镜像加速)...
echo  这可能需要 5-10 分钟，请耐心等待...
echo.

:: 尝试使用清华镜像安装
pip install -r requirements_gui.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade

if errorlevel 1 (
    echo.
    echo  [警告] 清华镜像安装失败，尝试阿里云镜像...
    pip install -r requirements_gui.txt -i https://mirrors.aliyun.com/pypi/simple --upgrade
    
    if errorlevel 1 (
        echo.
        echo  [错误] 依赖安装失败！
        echo  可能原因：
        echo  1. 网络连接问题
        echo  2. pip 版本过旧，尝试运行：python -m pip install --upgrade pip
        echo.
        echo  请截图错误信息寻求帮助。
        pause
        exit /b 1
    )
)

echo.
echo  [OK] 依赖安装完成！

:: 验证关键依赖
echo.
echo [4/4] 验证安装结果...
python -c "import PyQt6; from PyQt6.QtWidgets import QApplication; print('  [OK] PyQt6 正常')" 2>nul
if errorlevel 1 (
    echo  [警告] PyQt6 安装可能不完整，尝试重新安装...
    pip install PyQt6 -i https://pypi.tuna.tsinghua.edu.cn/simple --force-reinstall
)

python -c "import aiohttp; print('  [OK] aiohttp 正常')" 2>nul
python -c "import pandas; print('  [OK] pandas 正常')" 2>nul
python -c "import beautifulsoup4; print('  [OK] beautifulsoup4 正常')" 2>nul || python -c "from bs4 import BeautifulSoup; print('  [OK] beautifulsoup4 正常')" 2>nul
python -c "import docx; print('  [OK] python-docx 正常')" 2>nul

echo.
echo  ========================================
echo    安装完成！正在启动程序...
echo  ========================================
echo.
timeout /t 2 /nobreak >nul

:: 启动程序
echo  正在启动程序...
echo  工作目录: %cd%
echo.

python "启动器.py"

if errorlevel 1 (
    echo.
    echo  [错误] 程序启动失败！
    echo  请截图错误信息寻求帮助。
    pause
)

exit /b 0
