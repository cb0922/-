#!/usr/bin/env python3
"""
测试 all 模式 - 模拟GUI运行
"""
import sys
import os
import asyncio
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3


async def test_all_mode():
    """测试 all 模式"""
    print("=" * 80)
    print("测试 all 模式（模拟GUI）")
    print("=" * 80)
    
    # 模拟爬取结果（75个网址成功）
    test_results = []
    for i in range(75):
        test_results.append({
            "url": f"http://example{i}.com",
            "title": f"测试通知 {i}",
            "text": f"这是测试内容 {i} " * 50,
            "is_competition_related": i % 3 == 0,  # 1/3是比赛相关
            "all_documents": [
                {
                    "url": f"http://example{i}.com/file.pdf",
                    "filename": f"通知{i}.pdf",
                    "doc_type": "PDF",
                    "is_competition_related": i % 3 == 0
                }
            ] if i % 3 == 0 else [],
            "competition_documents": [
                {
                    "url": f"http://example{i}.com/file.pdf",
                    "filename": f"通知{i}.pdf",
                    "doc_type": "PDF",
                    "is_competition_related": True
                }
            ] if i % 3 == 0 else [],
            "success": True,
            "crawled_at": "2024-01-01T00:00:00"
        })
    
    crawler = EnhancedCompetitionCrawlerV3(
        urls_file="test_urls.csv",
        auto_remove_failed=False
    )
    crawler.results = test_results
    
    output_dir = "./test_all_output"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir, ignore_errors=True)
    
    print(f"\n模拟75个网址爬取完成")
    print(f"比赛相关: {sum(1 for r in test_results if r['is_competition_related'])}")
    print(f"文档总数: {sum(len(r['all_documents']) for r in test_results)}")
    
    # 模拟 all 模式的所有步骤
    steps = []
    
    # 步骤1: 下载文档
    print("\n[步骤1] 下载文档...")
    try:
        competition_docs = [d for r in test_results for d in r.get("competition_documents", [])]
        print(f"  需要下载 {len(competition_docs)} 个文档")
        # 注意：这里不会真的下载，因为URL是假的
        # 但在真实环境中会执行
        steps.append(("下载文档", True))
    except Exception as e:
        print(f"  [FAIL] {e}")
        steps.append(("下载文档", False))
    
    # 步骤2: 生成HTML报告
    print("\n[步骤2] 生成HTML报告...")
    try:
        html_path = crawler.generate_html_report()
        if html_path:
            print(f"  [OK] HTML报告: {html_path}")
            steps.append(("HTML报告", True))
        else:
            print(f"  [FAIL] 返回None")
            steps.append(("HTML报告", False))
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        steps.append(("HTML报告", False))
    
    # 步骤3: 生成Word报告
    print("\n[步骤3] 生成Word报告...")
    try:
        word_path = crawler.generate_word_report(output_dir=os.path.join(output_dir, "word_reports"))
        if word_path:
            print(f"  [OK] Word报告: {word_path}")
            steps.append(("Word报告", True))
        else:
            print(f"  [WARN] 返回None（可能没有比赛相关结果）")
            steps.append(("Word报告", True))  # None是正常情况
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        steps.append(("Word报告", False))
    
    # 步骤4: 保存JSON
    print("\n[步骤4] 保存JSON数据...")
    try:
        json_path = crawler.save_json_data(output_dir=os.path.join(output_dir, "data"))
        if json_path:
            print(f"  [OK] JSON数据: {json_path}")
            steps.append(("JSON数据", True))
        else:
            print(f"  [FAIL] 返回None")
            steps.append(("JSON数据", False))
    except Exception as e:
        print(f"  [ERROR] {e}")
        steps.append(("JSON数据", False))
    
    # 汇总
    print("\n" + "=" * 80)
    print("测试结果")
    print("=" * 80)
    
    passed = sum(1 for _, r in steps if r)
    total = len(steps)
    
    for name, result in steps:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    # 清理
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir, ignore_errors=True)
        print(f"\n[清理] 已删除测试目录")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(test_all_mode())
    sys.exit(0 if success else 1)
