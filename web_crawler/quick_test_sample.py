#!/usr/bin/env python3
"""
快速测试样本 - 测试不同类型网址
"""
import sys
import os
import asyncio
import csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3


def get_sample_urls():
    """获取代表性样本URL（各种类型）"""
    return [
        # 类型1: 中央教育网站
        {"index": 1, "url": "https://www.moe.gov.cn/", "name": "教育部", "type": "中央"},
        {"index": 2, "url": "https://www.ncet.edu.cn/", "name": "中央电教馆", "type": "中央"},
        
        # 类型2: 省级教育网站
        {"index": 3, "url": "http://jyt.beijing.gov.cn/", "name": "北京教育厅", "type": "省级"},
        {"index": 4, "url": "http://edu.sh.gov.cn/", "name": "上海教育", "type": "省级"},
        
        # 类型3: 市级教育网站
        {"index": 5, "url": "http://www.bjdjt.gov.cn/", "name": "北京电教馆", "type": "市级"},
        
        # 类型4: 可能慢速的（新疆等）
        {"index": 6, "url": "http://jyt.xinjiang.gov.cn/", "name": "新疆教育厅", "type": "慢速"},
        {"index": 7, "url": "http://www.qhjyks.com/", "name": "青海考试院", "type": "慢速"},
        
        # 类型5: 学校/机构网站
        {"index": 8, "url": "https://www.naea.edu.cn/", "name": "教育装备协会", "type": "机构"},
    ]


async def test_url(url_info, timeout=15):
    """测试单个URL"""
    idx = url_info['index']
    url = url_info['url']
    name = url_info['name']
    url_type = url_info['type']
    
    print(f"\n[{idx}] {name} ({url_type})")
    print(f"    {url}")
    
    crawler = EnhancedCompetitionCrawlerV3(
        urls_file="urls.csv",
        timeout=timeout,
        auto_remove_failed=False,
        max_retries=1
    )
    
    import time
    start = time.time()
    
    try:
        result = await asyncio.wait_for(
            crawler.crawl_single({'url': url}),
            timeout=30
        )
        
        elapsed = time.time() - start
        
        if result and result.get('success'):
            print(f"    [OK] 成功 ({elapsed:.1f}s)")
            print(f"    标题: {result.get('title', 'N/A')[:40]}...")
            return {
                'url': url,
                'name': name,
                'type': url_type,
                'status': 'OK',
                'time': elapsed,
                'title': result.get('title', 'N/A')[:50]
            }
        else:
            error = result.get('error', 'Unknown') if result else 'No result'
            print(f"    [FAIL] 失败 ({elapsed:.1f}s) - {error[:50]}")
            return {
                'url': url,
                'name': name,
                'type': url_type,
                'status': 'FAIL',
                'time': elapsed,
                'error': error[:50]
            }
            
    except asyncio.TimeoutError:
        print(f"    [TIMEOUT] 超时 (30s)")
        return {
            'url': url,
            'name': name,
            'type': url_type,
            'status': 'TIMEOUT',
            'time': 30,
            'error': 'Timeout'
        }
    except Exception as e:
        print(f"    [ERROR] 异常: {e}")
        return {
            'url': url,
            'name': name,
            'type': url_type,
            'status': 'ERROR',
            'time': 0,
            'error': str(e)[:50]
        }


async def main():
    """主函数"""
    print("=" * 70)
    print("URL样本测试 (8个代表性网址)")
    print("=" * 70)
    print("\n测试类型:")
    print("  - 中央教育网站 (moe.gov.cn, ncet.edu.cn)")
    print("  - 省级教育网站 (北京、上海)")
    print("  - 市级教育网站 (北京电教馆)")
    print("  - 慢速网站 (新疆、青海)")
    print("  - 机构网站 (教育装备协会)")
    print()
    
    urls = get_sample_urls()
    results = []
    
    for url_info in urls:
        result = await test_url(url_info)
        results.append(result)
    
    # 汇总
    print("\n" + "=" * 70)
    print("测试汇总")
    print("=" * 70)
    
    ok = sum(1 for r in results if r['status'] == 'OK')
    fail = sum(1 for r in results if r['status'] == 'FAIL')
    timeout = sum(1 for r in results if r['status'] == 'TIMEOUT')
    error = sum(1 for r in results if r['status'] == 'ERROR')
    
    print(f"总计: {len(results)} 个URL")
    print(f"成功: {ok} 个")
    print(f"失败: {fail} 个")
    print(f"超时: {timeout} 个")
    print(f"异常: {error} 个")
    
    print("\n按类型统计:")
    type_stats = {}
    for r in results:
        t = r['type']
        if t not in type_stats:
            type_stats[t] = {'total': 0, 'ok': 0}
        type_stats[t]['total'] += 1
        if r['status'] == 'OK':
            type_stats[t]['ok'] += 1
    
    for t, stats in type_stats.items():
        rate = stats['ok'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"  {t}: {stats['ok']}/{stats['total']} ({rate:.0f}%)")
    
    print("\n" + "=" * 70)
    print("结论:")
    if timeout > 0 or error > 0:
        print("  发现超时/异常问题，建议使用 --no-auto-remove 和更短超时")
    elif fail > 3:
        print("  多个网站访问失败，建议检查网络或使用代理")
    else:
        print("  大部分网站正常，可以开始爬取")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
