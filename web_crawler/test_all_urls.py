#!/usr/bin/env python3
"""
全面测试所有URL
测试全部127个网址，记录每个的状态
"""
import sys
import os
import asyncio
import csv
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3


class URLTester:
    """URL全面测试器"""
    
    def __init__(self, urls_file="urls.csv", timeout=20):
        self.urls_file = urls_file
        self.timeout = timeout
        self.results = []
        
    def load_urls(self):
        """加载所有URL"""
        if not os.path.exists(self.urls_file):
            print(f"[ERROR] 文件不存在: {self.urls_file}")
            return []
        
        urls = []
        with open(self.urls_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for i, row in enumerate(reader, 1):
                if row and row[0].strip():
                    urls.append({
                        'index': i,
                        'url': row[0].strip(),
                        'name': row[1] if len(row) > 1 else '',
                        'category': row[2] if len(row) > 2 else ''
                    })
        return urls
    
    async def test_single_url(self, url_info):
        """测试单个URL"""
        idx = url_info['index']
        url = url_info['url']
        name = url_info['name']
        
        print(f"\n[{idx}] 测试: {name[:20] if name else 'N/A'}")
        print(f"    URL: {url[:70]}...")
        
        crawler = EnhancedCompetitionCrawlerV3(
            urls_file=self.urls_file,
            timeout=self.timeout,
            auto_remove_failed=False,
            max_retries=1  # 只试1次，加快测试
        )
        
        start_time = datetime.now()
        
        try:
            result = await asyncio.wait_for(
                crawler.crawl_single({'url': url}),
                timeout=35  # 最大35秒
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if result and result.get('success'):
                return {
                    'index': idx,
                    'url': url,
                    'name': name,
                    'status': 'SUCCESS',
                    'title': result.get('title', 'N/A')[:50],
                    'documents': len(result.get('all_documents', [])),
                    'is_competition': result.get('is_competition_related', False),
                    'time': elapsed,
                    'error': None
                }
            elif result:
                return {
                    'index': idx,
                    'url': url,
                    'name': name,
                    'status': 'FAILED',
                    'title': None,
                    'documents': 0,
                    'is_competition': False,
                    'time': elapsed,
                    'error': result.get('error', 'Unknown error')
                }
            else:
                return {
                    'index': idx,
                    'url': url,
                    'name': name,
                    'status': 'NO_RESPONSE',
                    'title': None,
                    'documents': 0,
                    'is_competition': False,
                    'time': elapsed,
                    'error': 'No response'
                }
                
        except asyncio.TimeoutError:
            return {
                'index': idx,
                'url': url,
                'name': name,
                'status': 'TIMEOUT',
                'title': None,
                'documents': 0,
                'is_competition': False,
                'time': 35,
                'error': f'Timeout after 35s'
            }
        except Exception as e:
            return {
                'index': idx,
                'url': url,
                'name': name,
                'status': 'EXCEPTION',
                'title': None,
                'documents': 0,
                'is_competition': False,
                'time': 0,
                'error': f'{type(e).__name__}: {str(e)[:100]}'
            }
    
    async def test_all(self):
        """测试所有URL"""
        urls = self.load_urls()
        total = len(urls)
        
        print("=" * 80)
        print(f"全面URL测试")
        print(f"总计: {total} 个URL")
        print(f"超时: {self.timeout}s (单个请求)")
        print(f"最大等待: 35s (每个URL)")
        print("=" * 80)
        
        # 逐个测试，避免并发问题
        for i, url_info in enumerate(urls, 1):
            result = await self.test_single_url(url_info)
            self.results.append(result)
            
            # 实时显示状态
            status_icon = {
                'SUCCESS': '[OK]',
                'FAILED': '[FAIL]',
                'TIMEOUT': '[TIMEOUT]',
                'NO_RESPONSE': '[NO RES]',
                'EXCEPTION': '[ERROR]'
            }.get(result['status'], '[?]')
            
            print(f"    结果: {status_icon} {result['status']} ({result['time']:.1f}s)")
            
            # 每10个显示进度
            if i % 10 == 0 or i == total:
                success = sum(1 for r in self.results if r['status'] == 'SUCCESS')
                print(f"\n{'='*80}")
                print(f"进度: {i}/{total} | 成功: {success} | 失败: {i-success}")
                print(f"{'='*80}\n")
        
        return self.results
    
    def generate_report(self):
        """生成测试报告"""
        if not self.results:
            print("无结果可报告")
            return
        
        total = len(self.results)
        success = sum(1 for r in self.results if r['status'] == 'SUCCESS')
        failed = sum(1 for r in self.results if r['status'] == 'FAILED')
        timeout = sum(1 for r in self.results if r['status'] == 'TIMEOUT')
        exception = sum(1 for r in self.results if r['status'] == 'EXCEPTION')
        no_response = sum(1 for r in self.results if r['status'] == 'NO_RESPONSE')
        
        print("\n" + "=" * 80)
        print("测试报告汇总")
        print("=" * 80)
        print(f"总计测试: {total} 个URL")
        print(f"成功: {success} ({success/total*100:.1f}%)")
        print(f"失败: {failed} ({failed/total*100:.1f}%)")
        print(f"超时: {timeout} ({timeout/total*100:.1f}%)")
        print(f"异常: {exception} ({exception/total*100:.1f}%)")
        print(f"无响应: {no_response} ({no_response/total*100:.1f}%)")
        
        # 保存详细报告
        report_file = f"url_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total': total,
                    'success': success,
                    'failed': failed,
                    'timeout': timeout,
                    'exception': exception,
                    'no_response': no_response
                },
                'results': self.results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存: {report_file}")
        
        # 显示失败的URL
        if failed + timeout + exception > 0:
            print("\n" + "=" * 80)
            print("失败的URL列表 (前20个)")
            print("=" * 80)
            
            failed_results = [r for r in self.results if r['status'] != 'SUCCESS']
            for r in failed_results[:20]:
                print(f"\n[{r['index']}] {r['status']}")
                print(f"    {r['url'][:70]}...")
                print(f"    错误: {r['error'][:80]}..." if r['error'] else "    错误: 无")
        
        return {
            'total': total,
            'success': success,
            'failed': failed,
            'timeout': timeout,
            'exception': exception
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="全面URL测试")
    parser.add_argument("--urls", default="urls.csv", help="URL文件")
    parser.add_argument("--timeout", type=int, default=20, help="超时时间")
    
    args = parser.parse_args()
    
    tester = URLTester(urls_file=args.urls, timeout=args.timeout)
    
    try:
        asyncio.run(tester.test_all())
        tester.generate_report()
    except KeyboardInterrupt:
        print("\n\n用户中断")
        if tester.results:
            tester.generate_report()
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
