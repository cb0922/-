#!/usr/bin/env python3
"""
路径修复测试脚本
验证所有路径处理是否正确
"""
import os
import sys

def test_paths():
    print("=" * 60)
    print("路径修复测试")
    print("=" * 60)
    
    # 测试1: 程序目录
    print("\n[测试1] 程序目录")
    app_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"  app_dir = {app_dir}")
    assert os.path.exists(app_dir), "程序目录不存在！"
    print("  ✓ 通过")
    
    # 测试2: urls.csv 路径
    print("\n[测试2] urls.csv 路径")
    urls_file = os.path.join(app_dir, "urls.csv")
    print(f"  urls_file = {urls_file}")
    if os.path.exists(urls_file):
        print("  ✓ 文件存在")
    else:
        print("  ⚠ 文件不存在（将在添加网址时创建）")
    
    # 测试3: 输出目录路径
    print("\n[测试3] 输出目录路径")
    output_dir = os.path.normpath(os.path.join(app_dir, "./output"))
    print(f"  output_dir = {output_dir}")
    print(f"  是否为绝对路径: {os.path.isabs(output_dir)}")
    print("  ✓ 通过")
    
    # 测试4: 爬虫脚本路径
    print("\n[测试4] 爬虫脚本路径")
    crawler_script = os.path.join(app_dir, "enhanced_crawler_v3.py")
    print(f"  crawler_script = {crawler_script}")
    if os.path.exists(crawler_script):
        print("  ✓ 文件存在")
    else:
        print("  ✗ 文件不存在！")
        return False
    
    # 测试5: 核心模块路径
    print("\n[测试5] 核心模块路径")
    core_dir = os.path.join(app_dir, "core")
    print(f"  core_dir = {core_dir}")
    if os.path.exists(core_dir):
        print("  ✓ 目录存在")
    else:
        print("  [ERROR] 目录不存在！")
        return False
    
    # 测试6: 导入测试
    print("\n[测试6] 模块导入测试")
    try:
        sys.path.insert(0, app_dir)
        from app_gui import MainWindow, CrawlerWorker
        print("  ✓ app_gui 导入成功")
        
        # 测试 MainWindow.app_dir
        from PyQt6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = MainWindow()
        print(f"  MainWindow.app_dir = {window.app_dir}")
        assert window.app_dir == app_dir, "app_dir 不匹配！"
        print("  ✓ MainWindow.app_dir 正确")
        
    except Exception as e:
        print(f"  [ERROR] 导入失败: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("所有测试通过！")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_paths()
    input("\n按回车键退出...")
    sys.exit(0 if success else 1)
