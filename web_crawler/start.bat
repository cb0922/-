@echo off
chcp 65001 >nul
echo ===========================================
echo       网页信息采集爬虫工具
echo ===========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖
echo [1/3] 检查依赖...
python -c "import aiohttp" 2>nul
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
)
echo 依赖检查完成
echo.

REM 检查URL文件
if not exist "urls.csv" (
    echo [2/3] 创建URL模板文件...
    python run.py
    echo.
    echo 请编辑 urls.csv 添加要爬取的URL
    echo 然后重新运行此脚本
    pause
    exit /b 0
)

echo [2/3] 发现URL文件: urls.csv
echo.

REM 运行爬虫
echo [3/3] 开始爬取...
echo.
python main.py --urls urls.csv --format json,csv
echo.

echo ===========================================
echo 任务完成！数据保存在 data/ 目录
echo ===========================================
pause
