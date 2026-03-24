@echo off
chcp 65001 >nul
title 测试路径修复
color 0A

echo.
echo  ========================================
echo    测试路径修复
echo  ========================================
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"

echo [测试1] 检查工作目录
echo   当前工作目录: %cd%
echo   脚本目录: %~dp0
echo.

if "%cd%" == "%~dp0" (
    echo   [OK] 工作目录正确
) else (
    echo   [错误] 工作目录不匹配！
)
echo.

echo [测试2] 检查关键文件是否存在
echo   检查 urls.csv...
if exist "urls.csv" (
    echo   [OK] urls.csv 存在
) else (
    echo   [警告] urls.csv 不存在（将在首次添加网址时创建）
)
echo.

echo   检查 app_gui.py...
if exist "app_gui.py" (
    echo   [OK] app_gui.py 存在
) else (
    echo   [错误] app_gui.py 不存在！
)
echo.

echo [测试3] 检查Python和依赖
echo   检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [错误] Python 未安装
    pause
    exit /b 1
)
python --version
echo.

echo   检查 PyQt6...
python -c "import PyQt6; print('  [OK] PyQt6 已安装')" 2>nul
if errorlevel 1 (
    echo   [警告] PyQt6 未安装，请运行 一键安装.bat
)
echo.

echo [测试4] 启动程序
echo   正在启动程序进行实际测试...
echo   注意：请检查程序是否能正常读取网址列表
echo.
timeout /t 2 /nobreak >nul

python "启动器.py"

echo.
echo  ========================================
echo    测试完成
echo  ========================================
pause
