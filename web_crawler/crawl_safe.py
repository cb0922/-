#!/usr/bin/env python3
"""
防卡住爬取脚本 - 带超时控制和强制终止
"""
import sys
import os
import asyncio
import signal
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3
from core.url_manager import URLManager


class TimeoutCrawler:
    """带超时的爬虫"""
    
    def __init__(self, urls_file="urls.csv", timeout=15, max_urls=None):
        self.urls_file = urls_file
        self.timeout = timeout
        self.max_urls = max_urls  # 最多处理多少个URL
        self.results = []
        self.current_url = None
        
    async def crawl_with_timeout(self, url_item, max_time=30):
        """单个URL爬取，带超时"""
        url = url_item.get("url") if isinstance(url_item, dict) else url_item
        self.current_url = url
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 开始: {url[:60]}...")
        
        crawler = EnhancedCompetitionCrawlerV3(
            urls_file=self.urls_file,
            timeout=self.timeout,
            auto_remove_failed=False,
            max_retries=1  # 只重试1次，避免卡住
        )
        
        try:
            # 使用wait_for强制超时
            result = await asyncio.wait_for(
                crawler.crawl_single(url_item),
                timeout=max_time
            )
            
            if result and result.get("success"):
                print(f"  [OK] 成功: {result.get('title', 'N/A')[:50]}...")
                return result
            else:
                error = result.get('error', 'Unknown') if result else 'No result'
                print(f"  [FAIL] 失败: {error}")
                return result
                
        except asyncio.TimeoutError:
            print(f"  [TIMEOUT] 超时({max_time}秒): {url[:50]}...")
            return {
                "url": url,
                "success": False,
                "error": f"Timeout after {max_time}s",
                "timeout": True
            }
        except Exception as e:
            print(f"  [ERROR] 异常: {type(e).__name__}: {e}")
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }
    
    async def crawl_all_safe(self):
        """安全批量爬取"""
        # 加载URL
        url_manager = URLManager()
        url_manager.load_from_file(self.urls_file)
        all_urls = url_manager.urls
        
        if self.max_urls:
            all_urls = all_urls[:self.max_urls]
        
        total = len(all_urls)
        print("=" * 70)
        print(f"安全爬取工具")
        print(f"总计URL: {total}")
        print(f"超时设置: {self.timeout}s (单个请求)")
        print(f"最大等待: 30s (每个URL)")
        print("=" * 70)
        
        success_count = 0
        fail_count = 0
        timeout_count = 0
        
        # 逐个处理，避免并发导致卡住
        for i, url_item in enumerate(all_urls, 1):
            print(f"\n{'='*70}")
            print(f"进度: {i}/{total} ({i/total*100:.1f}%)")
            print(f"成功: {success_count} | 失败: {fail_count} | 超时: {timeout_count}")
            print(f"{'='*70}")
            
            result = await self.crawl_with_timeout(url_item, max_time=30)
            
            if result:
                if result.get("success"):
                    success_count += 1
                    self.results.append(result)
                elif result.get("timeout"):
                    timeout_count += 1
                else:
                    fail_count += 1
            else:
                fail_count += 1
            
            # 每5个保存一次中间结果
            if i % 5 == 0 and self.results:
                self._save_progress()
        
        # 最终结果
        print("\n" + "=" * 70)
        print(f"爬取完成!")
        print(f"总计: {total}")
        print(f"成功: {success_count}")
        print(f"失败: {fail_count}")
        print(f"超时: {timeout_count}")
        print("=" * 70)
        
        return self.results
    
    def _save_progress(self):
        """保存进度"""
        import json
        output_dir = "output/safe_crawl"
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, f"progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"  [SAVE] 进度已保存: {filepath}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="防卡住爬取工具")
    parser.add_argument("--urls", default="urls.csv", help="URL文件")
    parser.add_argument("--timeout", type=int, default=15, help="请求超时(秒)")
    parser.add_argument("--max-urls", type=int, help="最多处理N个URL")
    
    args = parser.parse_args()
    
    # 运行
    crawler = TimeoutCrawler(
        urls_file=args.urls,
        timeout=args.timeout,
        max_urls=args.max_urls
    )
    
    try:
        asyncio.run(crawler.crawl_all_safe())
    except KeyboardInterrupt:
        print("\n\n用户中断 (Ctrl+C)")
        if crawler.results:
            crawler._save_progress()
            print(f"已保存 {len(crawler.results)} 个结果")
    except Exception as e:
        print(f"\n[ERROR] 程序异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
