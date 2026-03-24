#!/usr/bin/env python3
"""
诊断简化版问题
"""
import sys
import os
import subprocess

def check_imports():
    """检查关键导入"""
    print("="*70)
    print("检查模块导入")
    print("="*70)
    
    checks = [
        ("enhanced_crawler_v3", "EnhancedCompetitionCrawlerV3"),
        ("report_generator_v3", "ReportGenerator"),
        ("word_generator", "NoticeWordGenerator"),
        ("core.document_handler", "DocumentHandler"),
        ("core.fetcher", "AsyncFetcher"),
        ("core.parser", "ContentParser"),
        ("core.proxy_manager", "ProxyManager"),
        ("core.url_manager", "URLManager"),
    ]
    
    for module_name, class_name in checks:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✓ {module_name}.{class_name}")
        except Exception as e:
            print(f"✗ {module_name}.{class_name}: {e}")

def check_files():
    """检查关键文件"""
    print("\n" + "="*70)
    print("检查关键文件")
    print("="*70)
    
    files = [
        "enhanced_crawler_v3.py",
        "report_generator_v3.py",
        "word_generator.py",
        "core/__init__.py",
        "core/document_handler.py",
        "core/fetcher.py",
        "core/parser.py",
        "core/proxy_manager.py",
        "core/url_manager.py",
    ]
    
    for f in files:
        if os.path.exists(f):
            size = os.path.getsize(f)
            print(f"✓ {f} ({size} bytes)")
        else:
            print(f"✗ {f} MISSING!")

def test_crawler_init():
    """测试爬虫初始化"""
    print("\n" + "="*70)
    print("测试爬虫初始化")
    print("="*70)
    
    try:
        from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3
        crawler = EnhancedCompetitionCrawlerV3()
        print("✓ 爬虫初始化成功")
    except Exception as e:
        print(f"✗ 爬虫初始化失败: {e}")
        import traceback
        traceback.print_exc()

def test_gui_import():
    """测试GUI导入"""
    print("\n" + "="*70)
    print("测试GUI导入")
    print("="*70)
    
    try:
        from app_gui import MainWindow
        print("✓ GUI导入成功")
    except Exception as e:
        print(f"✗ GUI导入失败: {e}")
        import traceback
        traceback.print_exc()

def check_encoding():
    """检查编码问题"""
    print("\n" + "="*70)
    print("检查文件编码")
    print("="*70)
    
    files_to_check = [
        "enhanced_crawler_v3.py",
        "report_generator_v3.py",
    ]
    
    for f in files_to_check:
        if os.path.exists(f):
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    content = file.read()
                    # 检查是否有BOM
                    if content.startswith('\ufeff'):
                        print(f"! {f} 有UTF-8 BOM")
                    else:
                        print(f"✓ {f} UTF-8 (无BOM)")
            except Exception as e:
                print(f"✗ {f} 编码错误: {e}")

if __name__ == "__main__":
    check_imports()
    check_files()
    test_crawler_init()
    test_gui_import()
    check_encoding()
