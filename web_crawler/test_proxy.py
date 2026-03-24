#!/usr/bin/env python3
"""
代理功能测试脚本
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.proxy_manager import ProxyManager, Proxy


def test_proxy_parsing():
    """测试代理解析"""
    print("\n[测试1] 代理字符串解析")
    
    test_cases = [
        "http://192.168.1.1:8080",
        "http://user:pass@proxy.com:8080",
        "https://secure.proxy.com:8443",
        "socks5://127.0.0.1:1080",
        "192.168.1.1:3128",
    ]
    
    for case in test_cases:
        proxy = Proxy.from_string(case)
        if proxy:
            print(f"  [OK] {case} -> {proxy}")
        else:
            print(f"  [FAIL] {case} -> 解析失败")


def test_proxy_manager():
    """测试代理管理器"""
    print("\n[测试2] 代理管理器")
    
    # 创建临时代理文件
    test_file = "test_proxies.json"
    
    manager = ProxyManager(test_file)
    
    # 添加测试代理
    proxy1 = Proxy.from_string("http://192.168.1.1:8080")
    proxy1.name = "测试代理1"
    
    proxy2 = Proxy.from_string("http://192.168.1.2:8080")
    proxy2.name = "测试代理2"
    
    manager.add_proxy(proxy1)
    manager.add_proxy(proxy2)
    
    print(f"  已添加 {len(manager.proxies)} 个代理")
    
    # 测试获取代理
    p = manager.get_random()
    print(f"  随机获取: {p}")
    
    p = manager.get_next()
    print(f"  轮询获取: {p}")
    
    # 统计信息
    stats = manager.get_stats()
    print(f"  统计: {stats}")
    
    # 清理
    if os.path.exists(test_file):
        os.remove(test_file)
    print(f"  [OK] 测试完成，已清理")


async def test_proxy_async():
    """测试异步代理功能"""
    print("\n[测试3] 异步代理测试")
    print("  注意: 此测试需要实际代理服务器")
    
    # 注意：这里使用一个假设的代理进行测试
    # 实际使用时需要替换为真实代理
    print("  跳过（无实际代理服务器）")


def main():
    print("=" * 50)
    print("    代理功能测试")
    print("=" * 50)
    
    test_proxy_parsing()
    test_proxy_manager()
    
    # 运行异步测试
    asyncio.run(test_proxy_async())
    
    print("\n" + "=" * 50)
    print("    所有测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
