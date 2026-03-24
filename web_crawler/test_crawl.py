#!/usr/bin/env python3
"""
直接测试爬虫功能，不通过GUI
"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_crawler import EnhancedCompetitionCrawler

def test_crawl():
    """测试爬取和PDF下载"""
    print("=" * 70)
    print("测试爬虫和PDF下载功能")
    print("=" * 70)
    
    # 创建爬虫实例
    crawler = EnhancedCompetitionCrawler(use_dynamic=False, timeout=30)
    
    # 测试URL - 一个已知有PDF的比赛通知页面
    test_urls = [
        {"url": "http://www.moe.gov.cn/jyb_xwfb/s5147/202501/t20250110_1174827.html"},
    ]
    
    print(f"\n[1/3] 开始爬取 {len(test_urls)} 个测试页面...")
    results = crawler.crawl_all(test_urls)
    
    if not results:
        print("  [ERROR] 没有成功爬取的页面")
        return
    
    print(f"  [OK] 成功爬取 {len(results)} 个页面")
    
    # 统计PDF
    all_pdfs = []
    competition_pdfs = []
    for r in results:
        print(f"\n  页面: {r.get('title', 'N/A')}")
        print(f"    所有PDF: {len(r.get('all_pdfs', []))}")
        print(f"    相关PDF: {len(r.get('competition_pdfs', []))}")
        
        all_pdfs.extend(r.get('all_pdfs', []))
        competition_pdfs.extend(r.get('competition_pdfs', []))
    
    print(f"\n[2/3] PDF统计:")
    print(f"    总共发现: {len(all_pdfs)} 个PDF")
    print(f"    相关PDF: {len(competition_pdfs)} 个")
    
    # 下载PDF
    if competition_pdfs:
        print(f"\n[3/3] 开始下载PDF...")
        download_results = crawler.download_pdfs(competition_pdfs, output_dir="test_pdfs")
        
        print(f"\n下载结果:")
        for r in download_results:
            status = r.get('status', 'unknown')
            filename = r.get('filename', 'N/A')
            if status == 'downloaded':
                size = r.get('size', 0)
                print(f"  [OK] {filename} ({size} bytes)")
            elif status == 'exists':
                print(f"  [EXISTS] {filename}")
            else:
                error = r.get('error', 'Unknown error')
                print(f"  [ERROR] {filename}: {error}")
    else:
        print("\n[3/3] 没有相关PDF需要下载")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)

if __name__ == "__main__":
    test_crawl()
