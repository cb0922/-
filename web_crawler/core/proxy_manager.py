#!/usr/bin/env python3
"""
代理IP管理模块
支持HTTP/HTTPS/SOCKS代理，自动轮换和验证
"""
import os
import json
import random
import asyncio
import aiohttp
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Proxy:
    """代理IP数据类"""
    host: str
    port: int
    protocol: str = "http"  # http, https, socks5
    username: Optional[str] = None
    password: Optional[str] = None
    
    # 元数据
    name: Optional[str] = None  # 代理名称/地区
    latency: Optional[float] = None  # 延迟(秒)
    last_check: Optional[str] = None  # 最后检查时间
    is_working: bool = True  # 是否可用
    fail_count: int = 0  # 失败次数
    
    def __hash__(self):
        """使Proxy可以作为set元素"""
        return hash((self.host, self.port, self.protocol))
    
    def __eq__(self, other):
        """相等性比较"""
        if not isinstance(other, Proxy):
            return False
        return (self.host == other.host and 
                self.port == other.port and 
                self.protocol == other.protocol)
    
    def __str__(self) -> str:
        """返回代理URL字符串"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Proxy':
        """从字典创建"""
        return cls(**data)
    
    @classmethod
    def from_string(cls, proxy_str: str) -> Optional['Proxy']:
        """从字符串解析代理
        支持的格式:
        - http://host:port
        - http://user:pass@host:port
        - host:port (默认http)
        """
        try:
            proxy_str = proxy_str.strip()
            
            # 解析协议
            protocol = "http"
            if "://" in proxy_str:
                protocol, rest = proxy_str.split("://", 1)
            else:
                rest = proxy_str
            
            # 解析认证信息
            username = None
            password = None
            if "@" in rest:
                auth, rest = rest.rsplit("@", 1)
                if ":" in auth:
                    username, password = auth.split(":", 1)
                else:
                    username = auth
            
            # 解析主机和端口
            if ":" in rest:
                host, port_str = rest.rsplit(":", 1)
                port = int(port_str)
            else:
                host = rest
                port = 8080 if protocol == "http" else 1080
            
            return cls(
                host=host,
                port=port,
                protocol=protocol,
                username=username,
                password=password
            )
        except Exception as e:
            print(f"[Proxy Parse Error] {e}")
            return None


class ProxyManager:
    """代理IP管理器"""
    
    def __init__(self, proxy_file: str = "proxies.json"):
        self.proxy_file = proxy_file
        self.proxies: List[Proxy] = []
        self.current_index = 0
        self.failed_proxies: set = set()
        
        # 加载代理
        self.load_proxies()
    
    def load_proxies(self):
        """从文件加载代理列表"""
        if not os.path.exists(self.proxy_file):
            print(f"[Proxy Manager] 代理文件不存在: {self.proxy_file}")
            return
        
        try:
            with open(self.proxy_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.proxies = [Proxy.from_dict(p) for p in data]
            print(f"[Proxy Manager] 已加载 {len(self.proxies)} 个代理")
        except Exception as e:
            print(f"[Proxy Manager] 加载代理失败: {e}")
    
    def save_proxies(self):
        """保存代理列表到文件"""
        try:
            with open(self.proxy_file, 'w', encoding='utf-8') as f:
                json.dump([p.to_dict() for p in self.proxies], f, ensure_ascii=False, indent=2)
            print(f"[Proxy Manager] 已保存 {len(self.proxies)} 个代理")
        except Exception as e:
            print(f"[Proxy Manager] 保存代理失败: {e}")
    
    def add_proxy(self, proxy: Proxy) -> bool:
        """添加代理"""
        # 检查是否已存在
        for p in self.proxies:
            if p.host == proxy.host and p.port == proxy.port:
                print(f"[Proxy Manager] 代理已存在: {proxy}")
                return False
        
        self.proxies.append(proxy)
        self.save_proxies()
        return True
    
    def add_proxy_from_string(self, proxy_str: str, name: Optional[str] = None) -> bool:
        """从字符串添加代理"""
        proxy = Proxy.from_string(proxy_str)
        if proxy:
            if name:
                proxy.name = name
            return self.add_proxy(proxy)
        return False
    
    def remove_proxy(self, host: str, port: int) -> bool:
        """移除代理"""
        for i, p in enumerate(self.proxies):
            if p.host == host and p.port == port:
                del self.proxies[i]
                self.save_proxies()
                return True
        return False
    
    def get_next(self) -> Optional[Proxy]:
        """获取下一个可用代理（轮询）"""
        if not self.proxies:
            return None
        
        # 轮询获取
        attempts = 0
        while attempts < len(self.proxies):
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            
            # 跳过失败的代理
            if proxy not in self.failed_proxies and proxy.is_working:
                return proxy
            
            attempts += 1
        
        # 所有代理都失败了
        return None
    
    def get_random(self) -> Optional[Proxy]:
        """随机获取一个可用代理"""
        available = [p for p in self.proxies 
                     if p not in self.failed_proxies and p.is_working]
        if available:
            return random.choice(available)
        return None
    
    def mark_failed(self, proxy: Proxy):
        """标记代理为失败"""
        proxy.fail_count += 1
        if proxy.fail_count >= 3:
            proxy.is_working = False
            self.failed_proxies.add(proxy)
            print(f"[Proxy Manager] 代理已标记为失败: {proxy}")
        self.save_proxies()
    
    def mark_success(self, proxy: Proxy):
        """标记代理为成功"""
        proxy.fail_count = max(0, proxy.fail_count - 1)
        if proxy in self.failed_proxies:
            self.failed_proxies.remove(proxy)
        proxy.is_working = True
        self.save_proxies()
    
    async def test_proxy(self, proxy: Proxy, test_url: str = "http://httpbin.org/ip", 
                         timeout: int = 10) -> Tuple[bool, float]:
        """测试代理是否可用"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    test_url, 
                    proxy=str(proxy),
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    
                    if response.status == 200:
                        proxy.latency = elapsed
                        proxy.last_check = datetime.now().isoformat()
                        return True, elapsed
                    else:
                        return False, 0
        except Exception as e:
            print(f"[Proxy Test] {proxy} 测试失败: {e}")
            return False, 0
    
    async def test_all_proxies(self, test_url: str = "http://httpbin.org/ip"):
        """测试所有代理"""
        print(f"[Proxy Manager] 开始测试 {len(self.proxies)} 个代理...")
        
        tasks = []
        for proxy in self.proxies:
            task = self.test_proxy(proxy, test_url)
            tasks.append((proxy, task))
        
        results = []
        for proxy, task in tasks:
            try:
                is_working, latency = await task
                proxy.is_working = is_working
                proxy.latency = latency
                results.append((proxy, is_working, latency))
            except Exception as e:
                proxy.is_working = False
                results.append((proxy, False, 0))
        
        # 保存结果
        self.save_proxies()
        
        # 打印统计
        working = sum(1 for _, is_working, _ in results if is_working)
        print(f"[Proxy Manager] 测试完成: {working}/{len(results)} 个代理可用")
        
        return results
    
    def get_stats(self) -> Dict:
        """获取代理统计信息"""
        total = len(self.proxies)
        working = sum(1 for p in self.proxies if p.is_working)
        failed = total - working
        
        avg_latency = 0
        working_proxies = [p for p in self.proxies if p.is_working and p.latency]
        if working_proxies:
            avg_latency = sum(p.latency for p in working_proxies) / len(working_proxies)
        
        return {
            "total": total,
            "working": working,
            "failed": failed,
            "working_rate": f"{working/total*100:.1f}%" if total > 0 else "0%",
            "avg_latency": f"{avg_latency:.2f}s" if avg_latency > 0 else "N/A"
        }
    
    def clear_failed(self):
        """清理失败的代理"""
        self.proxies = [p for p in self.proxies if p.is_working]
        self.failed_proxies.clear()
        self.save_proxies()
        print(f"[Proxy Manager] 已清理失败代理，剩余 {len(self.proxies)} 个")
    
    def import_from_file(self, filepath: str, format: str = "auto") -> int:
        """从文件导入代理
        
        Args:
            filepath: 文件路径
            format: 文件格式 (auto, json, txt)
        """
        imported = 0
        
        try:
            # 自动检测格式
            if format == "auto":
                if filepath.endswith('.json'):
                    format = "json"
                else:
                    format = "txt"
            
            if format == "json":
                # JSON格式
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        if isinstance(item, str):
                            proxy = Proxy.from_string(item)
                        else:
                            proxy = Proxy.from_dict(item)
                        if proxy and self.add_proxy(proxy):
                            imported += 1
            
            else:
                # 文本格式 (每行一个)
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            proxy = Proxy.from_string(line)
                            if proxy and self.add_proxy(proxy):
                                imported += 1
            
            print(f"[Proxy Manager] 从 {filepath} 导入 {imported} 个代理")
            return imported
            
        except Exception as e:
            print(f"[Proxy Manager] 导入失败: {e}")
            return 0


# 便捷函数
def create_proxy_manager(proxy_file: str = "proxies.json") -> ProxyManager:
    """创建代理管理器"""
    return ProxyManager(proxy_file)


def get_free_proxies() -> List[str]:
    """获取一些免费代理源（示例）
    注意：免费代理通常不稳定，建议购买付费代理
    """
    # 这里可以添加免费代理API
    # 例如：
    # - 站大爷
    # - 快代理
    # - 芝麻代理
    return []
