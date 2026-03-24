#!/usr/bin/env python3
"""
反检测模块 - 防止网站屏蔽
集成：User-Agent轮换、请求间隔、代理IP、请求头伪装
"""
import random
import time
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import aiohttp

# 导入代理管理器
try:
    from core.proxy_manager import ProxyManager, Proxy
    PROXY_AVAILABLE = True
except ImportError:
    PROXY_AVAILABLE = False


# 50个真实的User-Agent
USER_AGENTS = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    # Windows Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.0.0",
    # Windows Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
    # macOS Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    # macOS Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    # macOS Firefox
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Linux Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Linux Firefox
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Mobile - iOS
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    # Mobile - Android
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Redmi Note 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]


class UserAgentRotator:
    """User-Agent轮换器"""
    
    def __init__(self, user_agents: Optional[List[str]] = None):
        self.user_agents = user_agents or USER_AGENTS
        self.used_indices = set()
    
    def get_random(self) -> str:
        """随机获取一个User-Agent"""
        return random.choice(self.user_agents)
    
    def get_unique(self) -> str:
        """获取不重复的User-Agent"""
        available = set(range(len(self.user_agents))) - self.used_indices
        if not available:
            self.used_indices.clear()
            available = set(range(len(self.user_agents)))
        
        index = random.choice(list(available))
        self.used_indices.add(index)
        return self.user_agents[index]


@dataclass
class AntiDetectionConfig:
    """反检测配置"""
    # User-Agent
    rotate_user_agent: bool = True
    user_agent_rotator: UserAgentRotator = None
    
    # 请求间隔
    request_delay: tuple = (1.0, 3.0)  # 随机延迟范围(秒)
    add_random_delay: bool = True
    
    # 代理设置
    use_proxy: bool = False
    proxy_manager: Optional['ProxyManager'] = None  # type: ignore
    proxy_rotation: str = "random"  # random, round_robin
    
    # 请求头
    use_full_headers: bool = True
    referer_policy: str = "strict"  # strict, lax, none
    
    # 重试设置
    max_retries: int = 3
    retry_delay: tuple = (2.0, 5.0)
    
    def __post_init__(self):
        if self.user_agent_rotator is None:
            self.user_agent_rotator = UserAgentRotator()
        
        # 初始化代理管理器
        if self.use_proxy and PROXY_AVAILABLE and self.proxy_manager is None:
            self.proxy_manager = ProxyManager()


class RequestBehaviors:
    """请求行为控制器"""
    
    def __init__(self, config: Optional[AntiDetectionConfig] = None):
        self.config = config or AntiDetectionConfig()
        self._last_request_time = 0
        self._request_count = 0
        self._current_proxy: Optional[Proxy] = None
    
    def _get_headers(self) -> Dict[str, str]:
        """生成请求头"""
        headers = {}
        
        # User-Agent
        if self.config.rotate_user_agent:
            headers['User-Agent'] = self.config.user_agent_rotator.get_random()
        
        if self.config.use_full_headers:
            # 完整的浏览器请求头
            headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'DNT': '1',
            })
        
        return headers
    
    async def _apply_delay(self):
        """应用请求间隔"""
        if self.config.add_random_delay:
            delay = random.uniform(*self.config.request_delay)
            
            # 确保两次请求之间有足够的间隔
            elapsed = time.time() - self._last_request_time
            if elapsed < delay:
                await asyncio.sleep(delay - elapsed)
            else:
                await asyncio.sleep(delay)
        
        self._last_request_time = time.time()
    
    def _get_proxy(self) -> Optional[str]:
        """获取代理"""
        if not self.config.use_proxy or not PROXY_AVAILABLE:
            return None
        
        if self.config.proxy_manager is None:
            return None
        
        if self.config.proxy_rotation == "random":
            proxy = self.config.proxy_manager.get_random()
        else:
            proxy = self.config.proxy_manager.get_next()
        
        if proxy:
            self._current_proxy = proxy
            return str(proxy)
        return None
    
    def _handle_proxy_failure(self):
        """处理代理失败"""
        if self._current_proxy and PROXY_AVAILABLE:
            self.config.proxy_manager.mark_failed(self._current_proxy)
            print(f"[Proxy] 代理失败: {self._current_proxy}")
    
    def _handle_proxy_success(self):
        """处理代理成功"""
        if self._current_proxy and PROXY_AVAILABLE:
            self.config.proxy_manager.mark_success(self._current_proxy)
    
    async def fetch_with_anti_detection(
        self, 
        session: aiohttp.ClientSession, 
        url: str, 
        attempt: int = 0
    ) -> aiohttp.ClientResponse:
        """
        使用反检测策略获取页面
        
        Args:
            session: aiohttp会话
            url: 目标URL
            attempt: 当前重试次数
            
        Returns:
            HTTP响应对象
        """
        # 应用请求间隔
        await self._apply_delay()
        
        # 获取请求头
        headers = self._get_headers()
        
        # 获取代理
        proxy = self._get_proxy()
        
        try:
            # 发起请求
            kwargs = {
                'headers': headers,
                'ssl': False,
            }
            if proxy:
                kwargs['proxy'] = proxy
            
            async with session.get(url, **kwargs) as response:
                # 处理特定状态码
                if response.status == 403:
                    # 尝试更换代理重试
                    if attempt < self.config.max_retries:
                        self._handle_proxy_failure()
                        await asyncio.sleep(random.uniform(*self.config.retry_delay))
                        return await self.fetch_with_anti_detection(session, url, attempt + 1)
                
                elif response.status == 429:  # Too Many Requests
                    if attempt < self.config.max_retries:
                        wait_time = random.uniform(*self.config.retry_delay) * (attempt + 1)
                        print(f"  [Rate Limit] 遇到429错误，等待 {wait_time:.1f}s 后重试...")
                        await asyncio.sleep(wait_time)
                        return await self.fetch_with_anti_detection(session, url, attempt + 1)
                
                elif response.status == 503:  # Service Unavailable
                    if attempt < self.config.max_retries:
                        await asyncio.sleep(random.uniform(*self.config.retry_delay))
                        return await self.fetch_with_anti_detection(session, url, attempt + 1)
                
                # 请求成功
                if response.status == 200:
                    self._handle_proxy_success()
                
                return response
                
        except aiohttp.ClientProxyConnectionError as e:
            # 代理连接失败
            print(f"  [Proxy Error] 代理连接失败: {e}")
            self._handle_proxy_failure()
            if attempt < self.config.max_retries:
                return await self.fetch_with_anti_detection(session, url, attempt + 1)
            raise
            
        except aiohttp.ClientHttpProxyError as e:
            # HTTP代理错误
            print(f"  [Proxy Error] HTTP代理错误: {e}")
            self._handle_proxy_failure()
            if attempt < self.config.max_retries:
                return await self.fetch_with_anti_detection(session, url, attempt + 1)
            raise
            
        except asyncio.TimeoutError:
            # 处理超时
            if attempt < self.config.max_retries:
                wait_time = random.uniform(*self.config.retry_delay)
                print(f"  [Timeout] 请求超时，{wait_time:.1f}s 后重试...")
                await asyncio.sleep(wait_time)
                return await self.fetch_with_anti_detection(session, url, attempt + 1)
            raise
            
        except Exception as e:
            # 其他错误
            if attempt < self.config.max_retries:
                wait_time = random.uniform(*self.config.retry_delay)
                print(f"  [Error] {e}，{wait_time:.1f}s 后重试...")
                await asyncio.sleep(wait_time)
                return await self.fetch_with_anti_detection(session, url, attempt + 1)
            raise
    
    def create_session(self) -> aiohttp.ClientSession:
        """创建配置了反检测的会话"""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=10,
            enable_cleanup_closed=True,
            force_close=True,
            ssl=False
        )
        
        timeout = aiohttp.ClientTimeout(
            total=30,
            connect=10,
            sock_read=10
        )
        
        return aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            trust_env=True
        )


# 便捷函数
def create_anti_detection_config(
    use_proxy: bool = False,
    proxy_file: Optional[str] = None,
    request_delay: tuple = (1.0, 3.0),
    max_retries: int = 3
) -> AntiDetectionConfig:
    """创建反检测配置"""
    config = AntiDetectionConfig(
        use_proxy=use_proxy,
        request_delay=request_delay,
        max_retries=max_retries
    )
    
    if use_proxy and PROXY_AVAILABLE and proxy_file:
        from core.proxy_manager import ProxyManager
        config.proxy_manager = ProxyManager(proxy_file)
    
    return config


def create_balanced_fetcher(**kwargs) -> RequestBehaviors:
    """创建平衡的请求行为（推荐）"""
    config = AntiDetectionConfig(
        rotate_user_agent=True,
        request_delay=(1.0, 2.5),
        add_random_delay=True,
        use_full_headers=True,
        max_retries=3,
        **kwargs
    )
    return RequestBehaviors(config)


def create_stealth_fetcher(**kwargs) -> RequestBehaviors:
    """创建高隐蔽性的请求行为（慢但稳定）"""
    config = AntiDetectionConfig(
        rotate_user_agent=True,
        request_delay=(2.0, 5.0),
        add_random_delay=True,
        use_full_headers=True,
        max_retries=5,
        **kwargs
    )
    return RequestBehaviors(config)


def create_fast_fetcher(**kwargs) -> RequestBehaviors:
    """创建快速请求行为（可能被屏蔽）"""
    config = AntiDetectionConfig(
        rotate_user_agent=True,
        request_delay=(0.5, 1.0),
        add_random_delay=False,
        use_full_headers=True,
        max_retries=2,
        **kwargs
    )
    return RequestBehaviors(config)
