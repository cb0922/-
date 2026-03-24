#!/usr/bin/env python3
"""
分批爬取脚本 - 避免一次性爬取过多网址导致崩溃
"""
import sys
import os
import csv
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3
from core.url_manager import URLManager


def crawl_in_batches(urls_file="urls.csv", batch_size=20, start_batch=0):
    """
    分批爬取网址
    
    Args:
        urls_file: URL文件
        batch_size: 每批爬取数量
        start_batch: 从第几批开始（0表示从头开始）
    """
    
    # 加载所有URL
    url_manager = URLManager()
    url_manager.load_from_file(urls_file)
    all_urls = url_manager.urls
    
    total = len(all_urls)
    print("=" * 70)
    print(f"分批爬取工具")
    print(f"总计: {total} 个URL")
    print(f"每批: {batch_size} 个")
    print(f"开始批次: {start_batch}")
    print("=" * 70)
    
    # 计算批次
    num_batches = (total + batch_size - 1) // batch_size
    print(f"共分 {num_batches} 批")
    print()
    
    all_results = []
    
    for batch_num in range(start_batch, num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total)
        batch_urls = all_urls[start_idx:end_idx]
        
        print(f"\n{'='*70}")
        print(f"批次 {batch_num + 1}/{num_batches} (URL {start_idx+1}-{end_idx})")
        print(f"{'='*70}")
        
        # 创建爬虫
        crawler = EnhancedCompetitionCrawlerV3(
            urls_file=urls_file,
            timeout=30,
            auto_remove_failed=True,
            max_retries=2  # 减少重试次数，加快失败处理
        )
        
        # 爬取本批
        try:
            results = crawler.crawl_all(batch_urls)
            all_results.extend(results)
            
            print(f"\n本批完成: {len(results)}/{len(batch_urls)} 成功")
            
            # 保存中间结果
            save_intermediate_results(all_results, batch_num + 1)
            
        except Exception as e:
            print(f"\n[ERROR] 批次 {batch_num + 1} 出错: {e}")
            import traceback
            traceback.print_exc()
            
            # 询问是否继续
            response = input(f"\n批次 {batch_num + 1} 出错，是否继续下一批? (y/n): ")
            if response.lower() != 'y':
                print("用户取消")
                break
    
    # 最终结果
    print("\n" + "=" * 70)
    print(f"全部完成！总计成功: {len(all_results)}")
    print("=" * 70)
    
    # 生成最终报告
    generate_final_report(all_results)
    
    return all_results


def save_intermediate_results(results, batch_num):
    """保存中间结果"""
    output_dir = "output/batch_results"
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = os.path.join(output_dir, f"batch_{batch_num:03d}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"[SAVE] 中间结果已保存: {filepath}")


def generate_final_report(all_results):
    """生成最终报告"""
    if not all_results:
        print("没有结果可生成报告")
        return
    
    print("\n生成最终报告...")
    
    # 创建临时爬虫对象来生成报告
    crawler = EnhancedCompetitionCrawlerV3()
    crawler.results = all_results
    
    # Word报告
    try:
        word_path = crawler.generate_word_report(output_dir="output/word_reports")
        if word_path:
            print(f"[OK] Word报告: {word_path}")
    except Exception as e:
        print(f"[WARN] Word报告生成失败: {e}")
    
    # JSON数据
    try:
        json_path = crawler.save_json_data(output_dir="output/data")
        if json_path:
            print(f"[OK] JSON数据: {json_path}")
    except Exception as e:
        print(f"[WARN] JSON保存失败: {e}")
    
    # 统计
    competition = [r for r in all_results if r.get("is_competition_related")]
    docs = sum(len(r.get("all_documents", [])) for r in all_results)
    
    print(f"\n统计:")
    print(f"  成功爬取: {len(all_results)} 个页面")
    print(f"  比赛相关: {len(competition)} 个")
    print(f"  文档总数: {docs} 个")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="分批爬取工具")
    parser.add_argument("--urls", default="urls.csv", help="URL文件")
    parser.add_argument("--batch-size", type=int, default=20, help="每批数量（默认20）")
    parser.add_argument("--start-batch", type=int, default=0, help="开始批次（默认0）")
    
    args = parser.parse_args()
    
    crawl_in_batches(
        urls_file=args.urls,
        batch_size=args.batch_size,
        start_batch=args.start_batch
    )


if __name__ == "__main__":
    main()
