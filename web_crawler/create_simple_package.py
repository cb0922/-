#!/usr/bin/env python3
"""
创建简化版爬虫包 - 只保留核心文件
"""
import os
import sys
import shutil


def create_simple_package():
    """创建简化版包"""
    
    print("=" * 70)
    print("创建简化版爬虫包")
    print("=" * 70)
    
    output_dir = "dist/比赛通知爬虫_简化版"
    
    # 清理旧目录
    if os.path.exists(output_dir):
        print(f"\n[清理] 删除旧目录: {output_dir}")
        shutil.rmtree(output_dir)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 核心文件列表（只保留必要的）
    core_files = [
        # 主程序
        ("start_crawler.py", True),
        ("app_gui.py", True),
        
        # 爬虫核心（保留V3，删除V1/V2）
        ("enhanced_crawler_v3.py", True),
        
        # 报告生成器（保留V3兼容版）
        ("report_generator_v3.py", True),
        ("report_generator.py", True),  # 作为备用
        
        # 其他必要文件
        ("word_generator.py", True),
        ("manual_download_helper.py", True),
        
        # 配置文件
        ("urls.csv", True),
        ("全国电教馆_教科委网址库.csv", True),
        ("requirements_gui.txt", True),
        ("安装说明.txt", True),
        ("proxies_example.json", False),  # 可选
        
        # 使用说明
        ("README_V3.md", True),
        ("代理配置说明.md", False),  # 可选
    ]
    
    print("\n[1/3] 复制核心文件...")
    for filename, required in core_files:
        if os.path.exists(filename):
            shutil.copy2(filename, output_dir)
            status = "[OK]" if required else "[OPT]"
            print(f"  {status} {filename}")
        else:
            if required:
                print(f"  [MISS] {filename} (missing!)")
            else:
                print(f"  [SKIP] {filename} (optional)")
    
    # 复制core目录
    print("\n[2/3] 复制核心模块...")
    if os.path.exists("core"):
        dst = os.path.join(output_dir, "core")
        shutil.copytree("core", dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        print(f"  [OK] core/")
        
        # 列出core中的文件
        core_files_list = os.listdir(dst)
        for f in sorted(core_files_list):
            if not f.startswith('__'):
                print(f"      - {f}")
    else:
        print("  [MISS] core/ missing!")
    
    # 创建启动脚本
    print("\n[3/3] 创建启动脚本...")
    
    # Windows启动脚本（使用英文文件名避免编码问题）
    bat_content = '''@echo off
chcp 65001 >nul
title Competition Notice Crawler
echo.
echo ========================================
echo    Competition Notice Crawler V3.0
echo ========================================
echo.

REM Check Python
where python >nul 2>nul
if errorlevel 1 (
    echo [Error] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo [1/2] Checking dependencies...
python -c "import aiohttp, bs4, docx, PyQt6" >nul 2>nul
if errorlevel 1 (
    echo [Info] Installing dependencies...
    python -m pip install -r requirements_gui.txt -q
)

echo [2/2] Starting program...
echo.
echo Select mode:
echo   1. GUI (recommended)
echo   2. CLI - All features
echo   3. CLI - Documents only
echo   4. CLI - Reports only
echo.
set /p choice="Enter number (1-4): "

if "%choice%"=="1" goto gui
if "%choice%"=="2" goto all
if "%choice%"=="3" goto doc
if "%choice%"=="4" goto html
goto gui

:gui
echo.
echo Starting GUI...
python app_gui.py
goto end

:all
echo.
echo Starting all features mode...
python start_crawler.py --urls urls.csv --mode all --output ./output
goto end

:doc
echo.
echo Starting documents only mode...
python start_crawler.py --urls urls.csv --mode doc --output ./output
goto end

:html
echo.
echo Starting reports only mode...
python start_crawler.py --urls urls.csv --mode html --output ./output
goto end

:end
echo.
echo Program exited.
pause
'''
    
    with open(os.path.join(output_dir, "start.bat"), "w", encoding="utf-8") as f:
        f.write(bat_content)
    print(f"  [OK] start.bat")
    
    # 创建README
    readme_content = '''============================================================
    比赛通知爬虫 V3.0 - 简化版
============================================================

版本说明
--------
- 版本: V3.0 简化版
- 日期: 2026-03-23
- 状态: 稳定运行版

文件结构
--------
├── 启动.bat              # Windows启动脚本
├── 启动爬虫.py           # 命令行入口（推荐）
├── app_gui.py            # GUI界面
├── enhanced_crawler_v3.py # 爬虫核心（V3稳定版）
├── report_generator_v3.py # 报告生成器（V3兼容版）
├── word_generator.py     # Word报告生成
├── core/                 # 核心模块目录
│   ├── document_handler.py   # 文档处理器
│   ├── fetcher.py           # 网络请求
│   ├── parser.py            # HTML解析
│   ├── proxy_manager.py     # 代理管理
│   └── url_manager.py       # URL管理
├── urls.csv              # URL列表文件
├── requirements_gui.txt  # 依赖列表
└── README_V3.md          # 详细说明文档

快速开始
--------

方式1: 双击启动（最简单）
    双击 "启动.bat" → 选择模式 → 开始爬取

方式2: GUI界面（推荐）
    python app_gui.py

方式3: 命令行 - 全部功能
    python 启动爬虫.py --urls urls.csv --mode all

方式4: 命令行 - 仅下载文档
    python 启动爬虫.py --urls urls.csv --mode doc

方式5: 命令行 - 仅生成报告
    python 启动爬虫.py --urls urls.csv --mode html

输出位置
--------
./output/
├── documents/          # 下载的文档（PDF/Word/Excel等）
│   ├── PDF/
│   ├── Word/
│   ├── Excel/
│   └── ...
├── word_reports/      # Word报告
└── data/              # JSON数据

./reports/             # HTML报告

参数说明
--------
--urls URL文件          指定URL列表文件（默认: urls.csv）
--mode 模式            选择模式: all/doc/html（默认: all）
--output 输出目录      指定输出目录（默认: ./output）
--timeout 超时         请求超时时间（默认: 30秒）
--no-auto-remove       禁用自动删除（推荐，更稳定）
--proxy               启用代理IP
--proxy-file 文件     代理配置文件

示例命令
--------
# 基础使用
python 启动爬虫.py

# 指定URL文件
python 启动爬虫.py --urls my_urls.csv

# 仅下载文档
python 启动爬虫.py --mode doc

# 启用代理
python 启动爬虫.py --proxy --proxy-file proxies.json

# 禁用自动删除（更稳定）
python 启动爬虫.py --no-auto-remove

技术支持
--------
- 详细说明: README_V3.md
- 代理配置: 代理配置说明.md
- 依赖安装: requirements_gui.txt

============================================================
'''
    
    with open(os.path.join(output_dir, "使用说明.txt"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"  [OK] README.txt")
    
    # 创建数据目录
    for subdir in ["data", "reports", "output", "pdfs"]:
        os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)
    print(f"  [OK] data dirs")
    
    # 完成
    print("\n" + "=" * 70)
    print("简化版包创建完成!")
    print("=" * 70)
    print(f"\n位置: {os.path.abspath(output_dir)}")
    print(f"\n使用方法:")
    print(f"  1. 复制到目标目录")
    print(f"  2. 双击 启动.bat")
    print(f"  3. 选择运行模式")
    print(f"\n或命令行:")
    print(f"  cd {output_dir}")
    print(f"  python 启动爬虫.py")
    print("=" * 70)


if __name__ == "__main__":
    create_simple_package()
