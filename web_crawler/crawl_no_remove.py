#!/usr/bin/env python3
"""
禁用自动删除的安全爬取模式
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3
from core.url_manager import URLManager


def crawl_without_removal(urls_file="urls.csv", max_urls=None):
    """
    爬取网址，但禁用自动删除功能（避免删除导致的崩溃）
    """
    
    # 加载URL
    url_manager = URLManager()
    url_manager.load_from_file(urls_file)
    all_urls = url_manager.urls
    
    if max_urls:
        all_urls = all_urls[:max_urls]
    
    total = len(all_urls)
    print("=" * 70)
    print(f"安全爬取模式（禁用自动删除）")
    print(f"总计: {total} 个URL")
    print("=" * 70)
    
    # 创建爬虫 - 关键：禁用自动删除
    crawler = EnhancedCompetitionCrawlerV3(
        urls_file=urls_file,
        timeout=20,
        auto_remove_failed=False,  # 禁用自动删除！
        max_retries=2
    )
    
    # 分批处理，避免内存问题
    batch_size = 10
    all_results = []
    
    for i in range(0, total, batch_size):
        batch = all_urls[i:i+batch_size]
        batch_num = i // batch_size + 1
        num_batches = (total + batch_size - 1) // batch_size
        
        print(f"\n{'='*70}")
        print(f"批次 {batch_num}/{num_batches} (URL {i+1}-{min(i+batch_size, total)})")
        print(f"{'='*70}")
        
        try:
            # 处理本批
            import asyncio
            
            async def process_batch():
                results = []
                for j, url_item in enumerate(batch, 1):
                    actual_idx = i + j
                    print(f"\n[{actual_idx}/{total}] ", end="")
                    
                    try:
                        result = await asyncio.wait_for(
                            crawler.crawl_single(url_item),
                            timeout=40  # 单个URL最多40秒
                        )
                        
                        if result and result.get("success"):
                            print(f"✓ 成功")
                            results.append(result)
                        elif result and result.get("removed"):
                            print(f"✗ 将被删除（但禁用删除）")
                            results.append(result)
                        else:
                            print(f"✗ 失败")
                            
                    except asyncio.TimeoutError:
                        print(f"✗ 超时")
                    except Exception as e:
                        print(f"✗ 异常: {e}")
                
                return results
            
            batch_results = asyncio.run(process_batch())
            all_results.extend(batch_results)
            
            print(f"\n本批完成: {len(batch_results)}/{len(batch)} 成功")
            
        except Exception as e:
            print(f"\n[ERROR] 批次 {batch_num} 出错: {e}")
            import traceback
            traceback.print_exc()
    
    # 最终结果
    print("\n" + "=" * 70)
    print(f"全部完成！总计成功: {len(all_results)}/{total}")
    print("=" * 70)
    
    # 生成报告
    if all_results:
        try:
            crawler.results = all_results
            word_path = crawler.generate_word_report(output_dir="output/word_reports")
            if word_path:
                print(f"[OK] Word报告: {word_path}")
        except Exception as e:
            print(f"[WARN] 报告生成失败: {e}")
    
    return all_results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="禁用自动删除的安全爬取")
    parser.add_argument("--urls", default="urls.csv", help="URL文件")
    parser.add_argument("--max-urls", type=int, help="最多处理N个URL")
    
    args = parser.parse_args()
    
    crawl_without_removal(
        urls_file=args.urls,
        max_urls=args.max_urls
    )


if __name__ == "__main__":
    main()
