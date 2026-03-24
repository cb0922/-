#!/usr/bin/env python3
"""
修复版启动器 - 使用绝对路径避免工作目录问题
"""
import sys
import os

# 确保我们在正确的目录
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

# 导入并运行GUI
from app_gui import main

if __name__ == "__main__":
    main()
