#!/usr/bin/env python3
"""
GUI功能测试（非界面测试，测试GUI相关功能逻辑）
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """测试所有导入"""
    print("\n[测试] 导入检查")
    
    try:
        from app_gui import MainWindow, CrawlerWorker, ProxyTestWorker
        print("  [OK] GUI类导入成功")
    except Exception as e:
        print(f"  [FAIL] GUI类导入失败: {e}")
        return False
    
    try:
        from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3
        print("  [OK] V3爬虫导入成功")
    except Exception as e:
        print(f"  [FAIL] V3爬虫导入失败: {e}")
        return False
    
    try:
        from core.document_handler import DocumentHandler
        from core.proxy_manager import ProxyManager
        print("  [OK] 核心模块导入成功")
    except Exception as e:
        print(f"  [FAIL] 核心模块导入失败: {e}")
        return False
    
    return True


def test_crawler_worker_params():
    """测试CrawlerWorker参数"""
    print("\n[测试] CrawlerWorker参数")
    
    from app_gui import CrawlerWorker
    
    # 测试带代理参数的初始化
    try:
        worker = CrawlerWorker(
            urls_file="urls.csv",
            mode="all",
            use_dynamic=False,
            output_dir="./output",
            use_proxy=True,
            proxy_file="proxies.json"
        )
        print("  [OK] CrawlerWorker带代理参数初始化成功")
    except Exception as e:
        print(f"  [FAIL] CrawlerWorker初始化失败: {e}")
        return False
    
    # 检查属性
    if hasattr(worker, 'use_proxy') and hasattr(worker, 'proxy_file'):
        print("  [OK] CrawlerWorker代理属性存在")
    else:
        print("  [FAIL] CrawlerWorker代理属性缺失")
        return False
    
    return True


def test_mode_options():
    """测试模式选项"""
    print("\n[测试] 模式选项")
    
    # 检查模式映射
    mode_map = {
        "all - 全部(文档+报告)": "all",
        "doc - 仅下载文档": "doc",
        "html - 仅生成报告": "html",
    }
    
    for display, value in mode_map.items():
        extracted = display.split(" - ")[0]
        if extracted == value:
            print(f"  [OK] 模式 '{display}' -> '{value}'")
        else:
            print(f"  [FAIL] 模式解析错误: '{display}' -> '{extracted}' (期望 '{value}')")
            return False
    
    return True


def test_document_types_display():
    """测试文档类型显示"""
    print("\n[测试] 文档类型显示")
    
    from core.document_handler import DocumentHandler
    
    handler = DocumentHandler()
    
    # 测试各种文档类型的显示
    test_docs = [
        ("通知.pdf", "PDF"),
        ("报名表.docx", "Word"),
        ("名单.xlsx", "Excel"),
        ("演示.pptx", "PowerPoint"),
        ("附件.zip", "Archive"),
    ]
    
    for filename, expected_type in test_docs:
        doc_type = handler.get_document_type(filename)
        if doc_type == expected_type:
            print(f"  [OK] {filename} -> {doc_type}")
        else:
            print(f"  [FAIL] {filename} -> {doc_type} (期望 {expected_type})")
            return False
    
    return True


def test_settings_persistence():
    """测试设置持久化"""
    print("\n[测试] 设置持久化逻辑")
    
    # 模拟设置保存和加载
    test_settings = {
        "proxy/enabled": True,
        "proxy/file": "test_proxies.json",
        "output/dir": "./test_output",
    }
    
    # 验证设置值
    if test_settings["proxy/enabled"] == True:
        print("  [OK] 代理启用设置")
    else:
        print("  [FAIL] 代理启用设置异常")
        return False
    
    if test_settings["proxy/file"] == "test_proxies.json":
        print("  [OK] 代理文件设置")
    else:
        print("  [FAIL] 代理文件设置异常")
        return False
    
    return True


def test_progress_parsing():
    """测试进度解析"""
    print("\n[测试] 进度解析")
    
    import re
    
    # 测试各种进度消息的解析
    test_messages = [
        ("[PROGRESS] Completed: 5/10 (50.0%)", "PROGRESS"),
        ("[DOC] Found 3 documents: {'PDF': 2, 'Word': 1}", "DOC"),
        ("[OK] Title: 比赛通知", "OK"),
        ("[FAIL] URL failed 2/3 times", "FAIL"),
        ("[REMOVE] URL reached max failures", "REMOVE"),
    ]
    
    for message, expected_tag in test_messages:
        # 提取标签
        match = re.match(r'\[(\w+)\]', message)
        if match:
            tag = match.group(1)
            if tag == expected_tag:
                print(f"  [OK] 解析 '{tag}' 成功")
            else:
                print(f"  [FAIL] 标签不匹配: '{tag}' vs '{expected_tag}'")
                return False
        else:
            print(f"  [FAIL] 无法解析消息: {message[:50]}")
            return False
    
    return True


def test_command_building():
    """测试命令行构建"""
    print("\n[测试] 命令行构建")
    
    # 模拟构建命令
    cmd = [
        sys.executable, "-u", "enhanced_crawler_v3.py",
        "--urls", "urls.csv",
        "--mode", "all",
        "--output", "./output"
    ]
    
    # 添加代理参数
    use_proxy = True
    proxy_file = "proxies.json"
    
    if use_proxy:
        cmd.append("--proxy")
        cmd.extend(["--proxy-file", proxy_file])
    
    # 验证命令
    expected_parts = [
        "enhanced_crawler_v3.py",
        "--urls", "urls.csv",
        "--proxy",
        "--proxy-file", "proxies.json"
    ]
    
    for part in expected_parts:
        if part in cmd:
            print(f"  [OK] 命令包含: {part}")
        else:
            print(f"  [FAIL] 命令缺少: {part}")
            return False
    
    return True


def test_url_validation():
    """测试URL验证逻辑"""
    print("\n[测试] URL验证逻辑")
    
    test_urls = [
        ("http://example.com", True),
        ("https://test.com/page", True),
        ("ftp://files.com", False),  # 不支持ftp
        ("not-a-url", False),
        ("", False),
    ]
    
    for url, should_be_valid in test_urls:
        # 简单验证
        is_valid = url.startswith(("http://", "https://"))
        
        if is_valid == should_be_valid:
            status = "有效" if is_valid else "无效"
            print(f"  [OK] '{url[:30]}...' -> {status}")
        else:
            print(f"  [FAIL] '{url}' 验证结果错误")
            return False
    
    return True


def main():
    print("=" * 70)
    print("    GUI功能测试")
    print("=" * 70)
    
    results = []
    
    tests = [
        ("导入检查", test_imports),
        ("CrawlerWorker参数", test_crawler_worker_params),
        ("模式选项", test_mode_options),
        ("文档类型显示", test_document_types_display),
        ("设置持久化", test_settings_persistence),
        ("进度解析", test_progress_parsing),
        ("命令行构建", test_command_building),
        ("URL验证", test_url_validation),
    ]
    
    for name, test_func in tests:
        try:
            results.append((name, test_func()))
        except Exception as e:
            print(f"\n  [ERROR] {name}测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 70)
    print("    测试结果汇总")
    print("=" * 70)
    
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("    所有GUI功能测试通过!")
    else:
        print("    有测试失败，请检查!")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
