#!/usr/bin/env python3
"""
测试反反爬功能 - 针对之前爬取失败的网站
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.enhanced_fetcher import create_stealth_fetcher, create_balanced_fetcher
from core.parser import ContentParser

# 之前爬取失败的网站
FAILED_SITES = [
    {"url": "https://www.youjiaobei.com/about/", "name": "优教杯", "error": "HTTP 403"},
    {"url": "https://www.zhongchuangbei.com/about/", "name": "众创杯", "error": "HTTP 403"},
    {"url": "http://chengguodasai.com/", "name": "成果大赛", "error": "部分PDF 404"},
]

# 之前爬取成功的网站（作为对比）
SUCCESS_SITES = [
    {"url": "https://wkds.zhyww.cn/", "name": "语文报杯", "note": "之前成功"},
    {"url": "https://www.ncet.edu.cn/zhuzhan/sytztg/20250430/6449.html", "name": "中央电教馆", "note": "之前成功"},
]


async def test_with_balanced_mode(sites, label="平衡模式"):
    """使用平衡模式测试"""
    print(f"\n{'='*70}")
    print(f"使用 {label} 测试")
    print(f"{'='*70}")
    
    fetcher = create_balanced_fetcher(concurrency=2, timeout=30)
    
    results = []
    for site in sites:
        print(f"\n[TEST] {site['name']} - {site['url']}")
        print(f"       之前错误: {site.get('error', '无')}")
        
        try:
            fetch_results = await fetcher.fetch_all([{"url": site['url']}], progress_callback=None)
            result = fetch_results[0] if fetch_results else None
            
            if result and result.get('success'):
                # 解析内容
                content = result.get('content', '')
                parser = ContentParser(content)
                title = parser.get_title() or "无标题"
                
                print(f"[SUCCESS] 抓取成功!")
                print(f"          标题: {title[:50]}...")
                print(f"          内容长度: {len(content)} 字符")
                results.append({"site": site, "success": True, "title": title})
            else:
                error = result.get('error', 'Unknown') if result else 'No response'
                print(f"[FAILED] 仍然失败: {error}")
                results.append({"site": site, "success": False, "error": error})
                
        except Exception as e:
            print(f"[ERROR] 异常: {e}")
            results.append({"site": site, "success": False, "error": str(e)})
    
    return results


async def test_with_stealth_mode(sites, label="隐形模式"):
    """使用隐形模式测试"""
    print(f"\n{'='*70}")
    print(f"使用 {label} 测试")
    print(f"{'='*70}")
    
    fetcher = create_stealth_fetcher(concurrency=1, timeout=45)
    
    results = []
    for site in sites:
        print(f"\n[TEST] {site['name']} - {site['url']}")
        print(f"       之前错误: {site.get('error', '无')}")
        
        try:
            fetch_results = await fetcher.fetch_all([{"url": site['url']}], progress_callback=None)
            result = fetch_results[0] if fetch_results else None
            
            if result and result.get('success'):
                content = result.get('content', '')
                parser = ContentParser(content)
                title = parser.get_title() or "无标题"
                
                print(f"[SUCCESS] 抓取成功!")
                print(f"          标题: {title[:50]}...")
                print(f"          内容长度: {len(content)} 字符")
                results.append({"site": site, "success": True, "title": title})
            else:
                error = result.get('error', 'Unknown') if result else 'No response'
                print(f"[FAILED] 仍然失败: {error}")
                results.append({"site": site, "success": False, "error": error})
                
        except Exception as e:
            print(f"[ERROR] 异常: {e}")
            results.append({"site": site, "success": False, "error": str(e)})
    
    return results


def print_summary(results_balanced, results_stealth, label):
    """打印对比总结"""
    print(f"\n{'='*70}")
    print(f"{label} 测试结果对比")
    print(f"{'='*70}")
    
    print("\n网站\t\t\t之前状态\t平衡模式\t隐形模式")
    print("-" * 70)
    
    for i, site in enumerate(FAILED_SITES + SUCCESS_SITES):
        name = site['name']
        before = site.get('error', '成功')
        
        # 平衡模式结果
        if i < len(results_balanced):
            balanced = "成功" if results_balanced[i]['success'] else "失败"
        else:
            balanced = "-"
        
        # 隐形模式结果
        if i < len(results_stealth):
            stealth = "成功" if results_stealth[i]['success'] else "失败"
        else:
            stealth = "-"
        
        print(f"{name}\t\t{before}\t\t{balanced}\t\t{stealth}")
    
    # 统计
    total = len(FAILED_SITES) + len(SUCCESS_SITES)
    balanced_success = sum(1 for r in results_balanced if r['success'])
    stealth_success = sum(1 for r in results_stealth if r['success'])
    
    print(f"\n成功率统计:")
    print(f"  平衡模式: {balanced_success}/{total} ({balanced_success/total*100:.1f}%)")
    print(f"  隐形模式: {stealth_success}/{total} ({stealth_success/total*100:.1f}%)")


async def main():
    """主函数"""
    print("=" * 70)
    print("反反爬功能测试 - 针对之前爬取失败的网站")
    print("=" * 70)
    print("\n测试目标:")
    print("  1. 验证反反爬功能对403错误的处理能力")
    print("  2. 对比平衡模式和隐形模式的效果")
    print("  3. 测试之前成功的网站是否仍然正常")
    
    all_sites = FAILED_SITES + SUCCESS_SITES
    
    # 测试平衡模式
    results_balanced = await test_with_balanced_mode(all_sites, "平衡模式")
    
    # 测试隐形模式
    results_stealth = await test_with_stealth_mode(all_sites, "隐形模式")
    
    # 打印对比总结
    print_summary(results_balanced, results_stealth, "反反爬功能")
    
    print("\n" + "=" * 70)
    print("测试完成!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.run(main())
