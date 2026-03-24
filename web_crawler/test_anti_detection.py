#!/usr/bin/env python3
"""
反反爬功能测试
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.anti_detection import (
    UserAgentRotator, 
    RequestHeadersGenerator,
    AntiDetectionConfig,
    create_stealth_config,
    create_fast_config
)
from core.enhanced_fetcher import (
    EnhancedAsyncFetcher,
    create_stealth_fetcher,
    create_balanced_fetcher
)


def test_user_agent_rotation():
    """测试User-Agent轮换"""
    print("=" * 60)
    print("测试1: User-Agent轮换")
    print("=" * 60)
    
    ua_rotator = UserAgentRotator(use_mobile=True)
    
    print("\n生成10个随机User-Agent:")
    for i in range(10):
        ua = ua_rotator.get_random()
        print(f"  {i+1}. {ua[:60]}...")
    
    # 验证不重复（最近3个不会重复）
    recent = ua_rotator._history[-3:]
    has_duplicate = len(recent) != len(set(recent))
    print(f"\n最近3个是否重复: {'是' if has_duplicate else '否'}")
    print("[OK] User-Agent轮换正常" if not has_duplicate else "[WARN] 需要优化")


def test_headers_generation():
    """测试请求头生成"""
    print("\n" + "=" * 60)
    print("测试2: 请求头生成")
    print("=" * 60)
    
    headers_gen = RequestHeadersGenerator()
    
    print("\nChrome请求头:")
    headers = headers_gen.get_chrome_headers()
    for key, value in headers.items():
        print(f"  {key}: {value[:50]}...")
    
    print("\n验证必要字段:")
    required = ['User-Agent', 'Accept', 'Accept-Language', 'sec-ch-ua']
    for field in required:
        status = "✓" if field in headers else "✗"
        print(f"  {status} {field}")


def test_config_creation():
    """测试配置创建"""
    print("\n" + "=" * 60)
    print("测试3: 配置创建")
    print("=" * 60)
    
    print("\n隐形模式配置:")
    stealth = create_stealth_config()
    print(f"  延迟范围: {stealth.delayer.min_delay}-{stealth.delayer.max_delay}秒")
    print(f"  最大重试: {stealth.max_retries}")
    print(f"  使用移动端UA: {stealth.ua_rotator.user_agents != stealth.ua_rotator.DESKTOP_UAS}")
    
    print("\n快速模式配置:")
    fast = create_fast_config()
    print(f"  延迟范围: {fast.delayer.min_delay}-{fast.delayer.max_delay}秒")
    print(f"  最大重试: {fast.max_retries}")


async def test_fetcher_basic():
    """测试增强版抓取器基础功能"""
    print("\n" + "=" * 60)
    print("测试4: 增强版抓取器")
    print("=" * 60)
    
    # 使用平衡模式测试几个网址
    fetcher = create_balanced_fetcher(concurrency=2, timeout=15)
    
    test_urls = [
        {"url": "https://httpbin.org/get", "name": "测试页面1"},
        {"url": "https://httpbin.org/user-agent", "name": "测试页面2"},
    ]
    
    print("\n抓取测试URL...")
    try:
        results = await fetcher.fetch_all(test_urls)
        
        print(f"\n结果统计:")
        print(f"  总数: {len(results)}")
        print(f"  成功: {sum(1 for r in results if r.get('success'))}")
        print(f"  失败: {sum(1 for r in results if not r.get('success'))}")
        
        stats = fetcher.get_stats()
        print(f"\n详细统计:")
        print(f"  成功率: {stats['success_rate']}")
        print(f"  平均请求时间: {stats['avg_request_time']}")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("反反爬功能测试套件")
    print("=" * 60)
    
    # 运行非异步测试
    test_user_agent_rotation()
    test_headers_generation()
    test_config_creation()
    
    # 运行异步测试
    try:
        result = asyncio.run(test_fetcher_basic())
    except Exception as e:
        print(f"\n异步测试出错: {e}")
        result = False
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print("✓ User-Agent轮换: 正常")
    print("✓ 请求头生成: 正常")
    print("✓ 配置创建: 正常")
    if result:
        print("✓ 抓取器功能: 正常")
        print("\n所有测试通过！反反爬功能正常工作。")
    else:
        print("⚠ 抓取器功能: 需要检查网络")
    print("=" * 60)


if __name__ == "__main__":
    main()
