#!/usr/bin/env python3
"""
打包脚本 - 将爬虫打包成exe可执行文件
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path


def clean_build():
    """清理之前的构建文件"""
    dirs_to_remove = ['build', 'dist', '__pycache__', '*.spec']
    for pattern in dirs_to_remove:
        for path in Path('.').glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"Removed directory: {path}")
            elif path.is_file():
                path.unlink()
                print(f"Removed file: {path}")


def build_exe():
    """使用PyInstaller打包"""
    
    # PyInstaller命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=比赛通知爬虫",
        "--windowed",  # 不显示控制台窗口
        "--onefile",   # 打包成单个文件
        "--icon=NONE", # 可以指定图标文件
        "--add-data=urls.csv;.",  # 包含数据文件
        "--add-data=core;core",
        "--add-data=enhanced_crawler.py;.",
        "--add-data=report_generator.py;.",
        "--add-data=report_generator_v2.py;.",
        "--add-data=download_pdfs_enhanced.py;.",
        "--add-data=manual_download_helper.py;.",
        # 隐藏导入
        "--hidden-import=aiohttp",
        "--hidden-import=bs4",
        "--hidden-import=lxml",
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "app_gui.py"
    ]
    
    print("Building executable...")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\n✅ Build successful!")
        print("Output: dist/比赛通知爬虫.exe")
        return True
    else:
        print("\n❌ Build failed!")
        print("Error:", result.stderr)
        return False


def create_portable_version():
    """创建便携版（包含所有依赖文件）"""
    print("\nCreating portable version...")
    
    portable_dir = "dist/比赛通知爬虫_便携版"
    os.makedirs(portable_dir, exist_ok=True)
    
    # 复制exe
    shutil.copy("dist/比赛通知爬虫.exe", portable_dir)
    
    # 创建数据目录
    dirs_to_create = [
        "pdfs",
        "reports", 
        "data",
        "output"
    ]
    
    for dir_name in dirs_to_create:
        os.makedirs(os.path.join(portable_dir, dir_name), exist_ok=True)
    
    # 复制默认urls.csv
    if os.path.exists("urls.csv"):
        shutil.copy("urls.csv", portable_dir)
    
    # 创建启动脚本
    launcher = os.path.join(portable_dir, "启动程序.bat")
    with open(launcher, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("chcp 65001 >nul\n")
        f.write("echo 正在启动比赛通知爬虫...\n")
        f.write('start "" "比赛通知爬虫.exe"\n')
        f.write("exit\n")
    
    # 创建说明文件
    readme = os.path.join(portable_dir, "使用说明.txt")
    with open(readme, "w", encoding="utf-8") as f:
        f.write("=" * 50 + "\n")
        f.write("比赛通知爬虫 - 使用说明\n")
        f.write("=" * 50 + "\n\n")
        f.write("【启动方式】\n")
        f.write("1. 双击 启动程序.bat\n")
        f.write("2. 或直接双击 比赛通知爬虫.exe\n\n")
        f.write("【功能说明】\n")
        f.write("- 控制台：开始/停止爬取任务\n")
        f.write("- 网址管理：添加/删除监控网址\n")
        f.write("- 定时任务：设置自动爬取周期\n")
        f.write("- 结果查看：查看报告和PDF\n\n")
        f.write("【输出目录】\n")
        f.write("- pdfs/ - 下载的PDF文件\n")
        f.write("- reports/ - HTML可视化报告\n")
        f.write("- data/ - JSON数据文件\n\n")
        f.write("【注意事项】\n")
        f.write("- 首次运行可能需要允许防火墙访问\n")
        f.write("- 请勿删除urls.csv文件\n")
        f.write("- 建议定期清理pdfs文件夹以节省空间\n\n")
    
    print(f"✅ Portable version created: {portable_dir}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build EXE for Crawler App")
    parser.add_argument("--clean", action="store_true", help="Clean build files first")
    parser.add_argument("--portable", action="store_true", help="Create portable version")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("比赛通知爬虫 - 打包工具")
    print("=" * 60)
    
    # 清理
    if args.clean:
        print("\nCleaning build files...")
        clean_build()
    
    # 打包
    print("\nBuilding executable...")
    if build_exe():
        # 创建便携版
        if args.portable:
            create_portable_version()
        
        print("\n" + "=" * 60)
        print("Build completed successfully!")
        print("=" * 60)
        print("\n输出文件:")
        print("  dist/比赛通知爬虫.exe - 独立可执行文件")
        if args.portable:
            print("  dist/比赛通知爬虫_便携版/ - 便携版文件夹")
        print("\n使用方法:")
        print("  直接双击 exe 文件运行")
    else:
        print("\nBuild failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
