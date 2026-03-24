#!/usr/bin/env python3
"""
优化版爬虫测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_crawler_v2 import EnhancedCompetitionCrawlerV2

def test_optimized_crawler():
    """测试优化后的爬虫"""
    print("=" * 70)
    print("测试优化版爬虫 (enhanced_crawler_v2.py)")
    print("=" * 70)
    
    # 测试数据（5个网址）
    test_urls = [
        {"url": "https://wkds.zhyww.cn/", "name": "语文报杯"},
        {"url": "https://www.ncet.edu.cn/zhuzhan/sytztg/20250430/6449.html", "name": "中央电教馆"},
        {"url": "http://chengguodasai.com/", "name": "成果大赛"},
        {"url": "https://www.cdec.org.cn/articleDetail/2109", "name": "中国教育装备"},
        {"url": "https://cat.jzmu.edu.cn/info/1223/2366.htm", "name": "锦州医科大学"},
    ]
    
    print(f"\n测试网址数: {len(test_urls)}")
    print("开始爬取...\n")
    
    # 创建爬虫实例
    crawler = EnhancedCompetitionCrawlerV2(use_dynamic=False, timeout=30)
    
    # 开始爬取
    import time
    start_time = time.time()
    
    results = crawler.crawl_all(test_urls)
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 70)
    print(f"爬取完成! 用时: {elapsed:.1f}秒")
    print(f"成功: {len(results)}/{len(test_urls)}")
    
    if results:
        # 生成报告
        print("\n生成报告中...")
        crawler.generate_html_report()
        crawler.generate_word_report(output_dir="./test_optimized_output/word_reports")
        crawler.save_json_data(output_dir="./test_optimized_output/data")
        
        # PDF下载
        pdfs = []
        for r in results:
            pdfs.extend(r.get("competition_pdfs", []))
        
        if pdfs:
            print(f"\n下载PDF: {len(pdfs)}个")
            crawler.download_pdfs(pdfs, output_dir="./test_optimized_output/pdfs")
    
    print("\n测试完成!")
    return len(results) > 0

if __name__ == "__main__":
    success = test_optimized_crawler()
    sys.exit(0 if success else 1)
