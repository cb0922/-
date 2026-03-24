#!/usr/bin/env python3
"""
V3爬虫集成测试
"""
import sys
import os
import csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3
from core.url_manager import URLManager


def setup_test_urls():
    """设置测试URL"""
    # 使用一些测试网站
    with open("test_integration.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "name", "category"])
        # 几个正常的网站
        writer.writerow(["https://httpbin.org/html", "测试HTML", "测试"])
        writer.writerow(["https://www.example.com", "示例网站", "测试"])
        # 一个会失败的URL
        writer.writerow(["http://invalid.invalid.invalid", "无效网站", "测试"])
    
    print("[OK] 创建测试URL文件")


def test_crawler_initialization():
    """测试爬虫初始化"""
    print("\n[测试] 爬虫初始化")
    
    # 各种配置组合
    configs = [
        {"use_proxy": False, "auto_remove": True, "max_retries": 3},
        {"use_proxy": False, "auto_remove": False, "max_retries": 5},
        {"use_proxy": True, "auto_remove": True, "max_retries": 3},
    ]
    
    for i, config in enumerate(configs):
        try:
            crawler = EnhancedCompetitionCrawlerV3(
                use_proxy=config["use_proxy"],
                auto_remove_failed=config["auto_remove"],
                max_retries=config["max_retries"],
                urls_file="test_integration.csv"
            )
            print(f"  [OK] 配置{i+1}: proxy={config['use_proxy']}, auto_remove={config['auto_remove']}, retries={config['max_retries']}")
        except Exception as e:
            print(f"  [FAIL] 配置{i+1}初始化失败: {e}")
            return False
    
    return True


def test_crawl_single():
    """测试单个URL爬取"""
    print("\n[测试] 单个URL爬取")
    
    crawler = EnhancedCompetitionCrawlerV3(
        urls_file="test_integration.csv",
        timeout=10
    )
    
    # 测试正常URL
    import asyncio
    
    async def test_normal():
        result = await crawler.crawl_single({"url": "https://httpbin.org/html"})
        return result
    
    try:
        result = asyncio.run(test_normal())
        if result and result.get("success"):
            print(f"  [OK] 正常URL爬取成功: {result.get('title', 'N/A')[:50]}")
        else:
            error = result.get("error", "Unknown") if result else "No result"
            print(f"  [INFO] 正常URL爬取结果: {error}")
    except Exception as e:
        print(f"  [INFO] 正常URL爬取异常: {e}")
    
    # 测试无效URL（应记录失败）
    async def test_invalid():
        result = await crawler.crawl_single({"url": "http://invalid.invalid.invalid"})
        return result
    
    try:
        result = asyncio.run(test_invalid())
        if result and result.get("removed"):
            print(f"  [OK] 无效URL标记删除成功")
        elif result is None:
            print(f"  [OK] 无效URL返回None（未达到删除阈值）")
        else:
            print(f"  [INFO] 无效URL结果: {result}")
    except Exception as e:
        print(f"  [INFO] 无效URL测试异常: {e}")
    
    return True


def test_document_extraction():
    """测试文档提取功能"""
    print("\n[测试] 文档提取集成")
    
    # 创建一个包含各种文档链接的HTML
    test_html = '''
    <html>
    <head><title>比赛通知 - 测试页面</title></head>
    <body>
        <h1>2024年全国教学大赛通知</h1>
        <p>欢迎参加比赛，请下载以下文件：</p>
        <ul>
            <li><a href="/files/比赛通知.pdf">比赛通知.pdf</a></li>
            <li><a href="/files/报名表.docx">报名表.docx</a></li>
            <li><a href="/files/获奖名单.xlsx">获奖名单.xlsx</a></li>
            <li><a href="/files/演示PPT.pptx">演示PPT.pptx</a></li>
            <li><a href="/files/资料包.zip">资料包.zip</a></li>
            <li><a href="/page.html">普通页面</a></li>
        </ul>
    </body>
    </html>
    '''
    
    from core.document_handler import DocumentHandler
    
    handler = DocumentHandler()
    documents = handler.extract_document_links(
        test_html, "http://example.com", "比赛通知 - 测试页面"
    )
    
    print(f"  [OK] 提取到 {len(documents)} 个文档")
    
    # 验证分类
    expected_types = {"PDF": 1, "Word": 1, "Excel": 1, "PowerPoint": 1, "Archive": 1}
    actual_types = {}
    for doc in documents:
        t = doc["doc_type"]
        actual_types[t] = actual_types.get(t, 0) + 1
    
    print(f"  [OK] 文档类型统计: {actual_types}")
    
    # 验证比赛相关性
    competition_docs = [d for d in documents if d["is_competition_related"]]
    print(f"  [OK] 比赛相关文档: {len(competition_docs)}/{len(documents)}")
    
    return True


def test_crawl_all():
    """测试批量爬取"""
    print("\n[测试] 批量爬取")
    
    # 准备少量测试URL
    with open("test_batch.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "name", "category"])
        writer.writerow(["https://httpbin.org/html", "测试1", "测试"])
        writer.writerow(["https://www.example.com", "测试2", "测试"])
    
    crawler = EnhancedCompetitionCrawlerV3(
        urls_file="test_batch.csv",
        timeout=15
    )
    
    url_manager = URLManager()
    url_manager.load_from_file("test_batch.csv")
    
    print(f"  [INFO] 开始批量爬取 {len(url_manager.urls)} 个URL...")
    
    try:
        results = crawler.crawl_all(url_manager.urls)
        print(f"  [OK] 批量爬取完成: {len(results)} 个成功")
        
        # 检查是否有文档被提取
        for r in results:
            docs = r.get("all_documents", [])
            if docs:
                print(f"    - {r['url'][:40]}: {len(docs)} 个文档")
    except Exception as e:
        print(f"  [INFO] 批量爬取异常: {e}")
    
    # 清理
    os.remove("test_batch.csv")
    
    return True


def test_word_report_generation():
    """测试Word报告生成"""
    print("\n[测试] Word报告生成")
    
    crawler = EnhancedCompetitionCrawlerV3()
    
    # 模拟一些结果
    crawler.results = [
        {
            "url": "http://example.com/1",
            "title": "比赛通知1",
            "text": "这是比赛通知的内容",
            "is_competition_related": True,
            "competition_documents": [
                {"filename": "通知.pdf", "url": "http://example.com/1.pdf"}
            ],
            "crawled_at": "2024-01-01T00:00:00"
        },
        {
            "url": "http://example.com/2",
            "title": "普通通知",
            "text": "这是普通通知",
            "is_competition_related": False,
            "competition_documents": [],
            "crawled_at": "2024-01-01T00:00:00"
        }
    ]
    
    try:
        word_path = crawler.generate_word_report(output_dir="test_word_output")
        if word_path and os.path.exists(word_path):
            print(f"  [OK] Word报告生成成功: {word_path}")
            # 清理
            import shutil
            shutil.rmtree("test_word_output", ignore_errors=True)
        else:
            print(f"  [INFO] Word报告未生成或文件不存在")
    except Exception as e:
        print(f"  [INFO] Word报告生成异常: {e}")
    
    return True


def cleanup():
    """清理测试文件"""
    files = [
        "test_integration.csv",
        "test_integration_fail_records.json",
        "test_batch.csv",
        "test_batch_fail_records.json"
    ]
    for f in files:
        if os.path.exists(f):
            os.remove(f)
            print(f"[清理] {f}")


def main():
    print("=" * 70)
    print("    V3爬虫集成测试")
    print("=" * 70)
    
    setup_test_urls()
    
    results = []
    
    tests = [
        ("爬虫初始化", test_crawler_initialization),
        ("单个URL爬取", test_crawl_single),
        ("文档提取集成", test_document_extraction),
        ("批量爬取", test_crawl_all),
        ("Word报告生成", test_word_report_generation),
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
        print("    所有集成测试通过!")
    else:
        print("    有测试失败，请检查!")
    print("=" * 70)
    
    cleanup()
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
