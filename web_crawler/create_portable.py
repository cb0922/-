#!/usr/bin/env python3
"""
创建便携版 - 包含Python环境，无需用户安装
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def find_python_embed():
    """查找 Python embeddable 版本"""
    # 检查当前 Python 是否为 embeddable
    python_exe = sys.executable
    python_dir = os.path.dirname(python_exe)
    
    # 检查是否存在 python3x.zip（embeddable 版本的特征）
    version = f"python{sys.version_info.major}{sys.version_info.minor}"
    zip_file = os.path.join(python_dir, f"{version}.zip")
    
    if os.path.exists(zip_file):
        return python_dir
    return None

def create_portable_package():
    """创建完整便携包"""
    
    print("=" * 60)
    print("    创建比赛通知爬虫便携版")
    print("=" * 60)
    
    output_dir = "dist/比赛通知爬虫_完整便携版"
    
    # 清理旧文件
    if os.path.exists(output_dir):
        print(f"\n[清理] 删除旧目录: {output_dir}")
        shutil.rmtree(output_dir)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 复制当前 Python 环境（如果可能）
    print("\n[1/5] 准备 Python 环境...")
    embed_python = find_python_embed()
    
    if embed_python:
        print(f"  找到 Embeddable Python: {embed_python}")
        # 复制 Python 目录
        for item in os.listdir(embed_python):
            src = os.path.join(embed_python, item)
            dst = os.path.join(output_dir, item)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.isdir(src) and item not in ['__pycache__', 'site-packages']:
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__'))
    else:
        print("  未找到 Embeddable Python，将创建依赖安装脚本")
    
    # 2. 复制项目文件
    print("\n[2/5] 复制项目文件...")
    files_to_copy = [
        "app_gui.py",
        "enhanced_crawler.py",
        "enhanced_crawler_v2.py",
        "enhanced_crawler_v3.py",
        "enhanced_crawler_v3_safe.py",
        "report_generator.py",
        "report_generator_v2.py",
        "report_generator_v3.py",
        "word_generator.py",
        "download_pdfs_enhanced.py",
        "manual_download_helper.py",
        "启动器.py",
        "urls.csv",
        "全国电教馆_教科委网址库.csv",
        "requirements_gui.txt",
        "安装说明.txt",
        "proxies_example.json",
        "代理配置说明.md",
        "README_V3.md",
        "最终修复说明.md",
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, output_dir)
            print(f"  复制: {file}")
    
    # 复制目录
    dirs_to_copy = ["core"]
    for dir_name in dirs_to_copy:
        if os.path.exists(dir_name):
            dst = os.path.join(output_dir, dir_name)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(dir_name, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            print(f"  复制目录: {dir_name}/")
    
    # 3. 创建启动脚本
    print("\n[3/5] 创建启动脚本...")
    
    # 创建 .bat 启动脚本
    bat_content = '''@echo off
chcp 65001 >nul
title 比赛通知爬虫
echo.
echo ========================================
echo    比赛通知爬虫
echo ========================================
echo.

REM 检查 Python
if exist "python.exe" (
    set PYTHON=python.exe
) else if exist "pythonw.exe" (
    set PYTHON=pythonw.exe
) else (
    echo 错误：未找到 Python 环境
    echo 请确保程序完整解压
    pause
    exit /b 1
)

echo 正在启动程序...
"%PYTHON%" "启动器.py"

if errorlevel 1 (
    echo.
    echo 程序异常退出，错误码: %errorlevel%
    pause
)
'''
    
    with open(os.path.join(output_dir, "启动.bat"), "w", encoding="utf-8") as f:
        f.write(bat_content)
    print("  创建: 启动.bat")
    
    # 创建安装依赖脚本
    install_bat = '''@echo off
chcp 65001 >nul
title 安装依赖
echo.
echo ========================================
echo    安装比赛通知爬虫依赖
echo ========================================
echo.

if not exist "python.exe" (
    echo 错误：未找到 python.exe
    echo 请确保在正确的目录下运行此脚本
    pause
    exit /b 1
)

echo 正在安装依赖，请耐心等待...
echo 如果下载慢，可以关闭窗口后手动编辑 requirements_gui.txt 换镜像源
echo.

python -m pip install --upgrade pip
python -m pip install -r requirements_gui.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if errorlevel 1 (
    echo.
    echo 安装失败，尝试阿里云镜像...
    python -m pip install -r requirements_gui.txt -i https://mirrors.aliyun.com/pypi/simple
)

echo.
echo 安装完成！
pause
'''
    
    with open(os.path.join(output_dir, "安装依赖.bat"), "w", encoding="utf-8") as f:
        f.write(install_bat)
    print("  创建: 安装依赖.bat")
    
    # 4. 创建数据目录
    print("\n[4/5] 创建数据目录...")
    for dir_name in ["pdfs", "reports", "output", "data"]:
        os.makedirs(os.path.join(output_dir, dir_name), exist_ok=True)
        print(f"  创建: {dir_name}/")
    
    # 5. 创建 README
    print("\n[5/5] 创建说明文档...")
    readme = '''比赛通知爬虫 - 便携版使用说明
========================================

【目录结构】
- 启动.bat          : 启动程序（推荐）
- 安装依赖.bat      : 如果启动失败，先运行这个安装依赖
- 启动器.py         : Python 启动脚本
- app_gui.py        : 主程序
- core/             : 核心模块
- urls.csv          : 默认网址列表
- pdfs/             : 下载的 PDF 保存位置
- reports/          : 生成的报告
- output/           : 爬取结果数据

【使用步骤】
1. 双击 "启动.bat" 运行程序
2. 首次运行可能需要安装依赖（自动完成）
3. 如果自动安装失败，双击 "安装依赖.bat" 手动安装
4. 安装完成后再次运行 "启动.bat"

【常见问题】
Q: 双击启动.bat 后闪退
A: 先运行 "安装依赖.bat" 安装所需包

Q: 提示缺少某个模块
A: 运行 "安装依赖.bat" 或查看 安装说明.txt

Q: 如何更新程序
A: 直接替换 .py 文件即可，数据保存在 pdfs/ 和 reports/ 中

【技术支持】
如有问题，请查看 安装说明.txt 或联系开发者
'''
    
    with open(os.path.join(output_dir, "README.txt"), "w", encoding="utf-8") as f:
        f.write(readme)
    print("  创建: README.txt")
    
    # 完成
    print("\n" + "=" * 60)
    print(f"便携版创建完成！")
    print(f"位置: {os.path.abspath(output_dir)}")
    print("\n使用方式：")
    print(f"  1. 将整个文件夹复制到目标电脑")
    print(f"  2. 双击 启动.bat 运行")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    create_portable_package()
