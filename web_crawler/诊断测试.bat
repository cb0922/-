@echo off
chcp 65001 >nul
title 爬虫诊断测试
echo.
echo ========================================
echo    爬虫诊断测试
echo ========================================
echo.
echo 本测试将直接运行爬虫（不通过GUI），查看完整日志
echo.

cd /d "%~dp0"

echo [1/2] 测试单个URL爬取和PDF下载...
echo.
python test_crawl.py
echo.

echo [2/2] 测试完整爬虫流程...
echo.
python enhanced_crawler.py --urls urls.csv --mode all --output ./output 2>&1
echo.

echo ========================================
echo 诊断完成
echo ========================================
echo.
echo 请检查上方日志：
echo - 是否有 "[PDF_DEBUG]" 日志？
echo - 是否有 "[DOWNLOAD]" 日志？
echo - 是否有 "[PDF_DOWNLOAD]" 日志？
echo.
echo 如果都没有，说明PDF提取或下载流程被跳过
echo.
pause
