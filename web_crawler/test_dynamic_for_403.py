#!/usr/bin/env python3
"""
测试使用动态渲染(Playwright)处理403错误
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_crawler_v2 import EnhancedCompetitionCrawlerV2
from core.parser import ContentParser

# 403错误的网站
FORBIDDEN_SITES = [
    {"url": "https://www.youjiaobei.com/about/", "name": "优教杯"},
    {"url": "https://www.zhongchuangbei.com/about/", "name": "众创杯"},
]


async def test_dynamic_crawl():
    """测试动态渲染模式"""
    print("=" * 70)
    print("测试动态渲染(Playwright)处理403错误")
    print("=" * 70)
    print("\n原理：使用真实浏览器访问，模拟人类行为")
    print("预期：可以绕过基于HTTP头的反爬机制")
    print()
    
    # 创建爬虫（开启动态渲染）
    crawler = EnhancedCompetitionCrawlerV2(
        use_dynamic=True,  # 开启动态渲染
        timeout=60
    )
    
    results = []
    for site in FORBIDDEN_SITES:
        print(f"\n[TEST] {site['name']} - {site['url']}")
        print(f"       之前错误: HTTP 403 (静态模式)")
        print(f"       当前模式: 动态渲染(Playwright)")
        
        try:
            # 使用动态渲染爬取
            result = await crawler.crawl_dynamic(site['url'])
            
            if result and result.get('success'):
                title = result.get('title', '无标题')
                content = result.get('content', '')
                
                print(f"[SUCCESS] 动态渲染成功!")
                print(f"          标题: {title[:50]}...")
                print(f"          内容长度: {len(content)} 字符")
                results.append({"site": site, "success": True, "title": title})
            else:
                error = result.get('error', 'Unknown') if result else 'No response'
                print(f"[FAILED] 动态渲染也失败: {error}")
                results.append({"site": site, "success": False, "error": error})
                
        except Exception as e:
            print(f"[ERROR] 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append({"site": site, "success": False, "error": str(e)})
    
    return results


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("动态渲染测试需要安装Playwright:")
    print("  pip install playwright")
    print("  playwright install chromium")
    print("=" * 70)
    
    try:
        results = asyncio.run(test_dynamic_crawl())
        
        # 总结
        print("\n" + "=" * 70)
        print("测试结果总结")
        print("=" * 70)
        
        for r in results:
            status = "成功" if r['success'] else "失败"
            print(f"  {r['site']['name']}: {status}")
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n成功率: {success_count}/{len(results)}")
        
    except ImportError as e:
        print(f"\n[ERROR] 缺少依赖: {e}")
        print("请安装Playwright:")
        print("  pip install playwright")
        print("  playwright install chromium")
    except Exception as e:
        print(f"\n[ERROR] 测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
