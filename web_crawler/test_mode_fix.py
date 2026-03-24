#!/usr/bin/env python3
"""
测试模式修复 - 验证 all/doc/html 模式
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3


def test_modes():
    """测试不同模式"""
    print("=" * 80)
    print("测试模式修复")
    print("=" * 80)
    
    # 模拟爬取结果
    test_results = [
        {
            "url": "http://example.com/1",
            "title": "比赛通知1",
            "text": "全国教学大赛通知",
            "is_competition_related": True,
            "all_documents": [
                {
                    "url": "http://example.com/1.pdf",
                    "filename": "通知.pdf",
                    "doc_type": "PDF",
                    "is_competition_related": True
                }
            ],
            "competition_documents": [
                {
                    "url": "http://example.com/1.pdf",
                    "filename": "通知.pdf",
                    "doc_type": "PDF",
                    "is_competition_related": True
                }
            ],
            "crawled_at": "2024-01-01T00:00:00"
        },
        {
            "url": "http://example.com/2",
            "title": "普通通知",
            "text": "普通公告",
            "is_competition_related": False,
            "all_documents": [],
            "competition_documents": [],
            "crawled_at": "2024-01-01T00:00:00"
        }
    ]
    
    crawler = EnhancedCompetitionCrawlerV3(
        urls_file="test.csv",
        auto_remove_failed=False
    )
    crawler.results = test_results
    
    output_dir = "./test_output_mode"
    
    # 测试1: HTML报告生成
    print("\n[测试1] HTML报告生成")
    try:
        report_path = crawler.generate_html_report()
        if report_path:
            print(f"  [OK] HTML报告: {report_path}")
            if os.path.exists(report_path):
                print(f"  [OK] 文件存在")
            else:
                print(f"  [FAIL] 文件不存在")
        else:
            print(f"  [FAIL] 生成失败")
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试2: Word报告生成
    print("\n[测试2] Word报告生成")
    try:
        word_path = crawler.generate_word_report(output_dir=os.path.join(output_dir, "word_reports"))
        if word_path:
            print(f"  [OK] Word报告: {word_path}")
            if os.path.exists(word_path):
                print(f"  [OK] 文件存在")
            else:
                print(f"  [FAIL] 文件不存在")
        else:
            print(f"  [FAIL] 生成失败（无比赛相关结果）")
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试3: 文档下载
    print("\n[测试3] 文档下载")
    competition_docs = [d for r in test_results for d in r.get("competition_documents", [])]
    print(f"  找到 {len(competition_docs)} 个比赛相关文档")
    
    if competition_docs:
        try:
            # 注意：这里不会真的下载，因为URL是假的
            doc_results = crawler.download_documents(
                competition_docs, 
                output_dir=os.path.join(output_dir, "documents")
            )
            print(f"  [OK] 下载完成: {len(doc_results)} 个")
        except Exception as e:
            print(f"  [FAIL] 异常: {e}")
    else:
        print("  - 无文档需要下载")
    
    # 测试4: JSON保存
    print("\n[测试4] JSON数据保存")
    try:
        json_path = crawler.save_json_data(output_dir=os.path.join(output_dir, "data"))
        if json_path:
            print(f"  [OK] JSON数据: {json_path}")
            if os.path.exists(json_path):
                print(f"  [OK] 文件存在")
            else:
                print(f"  [FAIL] 文件不存在")
        else:
            print(f"  [FAIL] 保存失败")
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 汇总
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
    print(f"\n输出目录: {os.path.abspath(output_dir)}")
    
    if os.path.exists(output_dir):
        print("\n目录结构:")
        for root, dirs, files in os.walk(output_dir):
            level = root.replace(output_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 2 * (level + 1)
            for file in files[:5]:  # 只显示前5个文件
                print(f"{sub_indent}{file}")
            if len(files) > 5:
                print(f"{sub_indent}... 和 {len(files)-5} 个其他文件")
    
    # 清理
    import shutil
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir, ignore_errors=True)
        print(f"\n[清理] 已删除测试目录")


if __name__ == "__main__":
    test_modes()
