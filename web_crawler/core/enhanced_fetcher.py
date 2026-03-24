#!/usr/bin/env python3
"""
增强版异步网页抓取模块
集成反反爬功能
"""
import aiohttp
import asyncio
from typing import List, Dict, Optional, Callable
from urllib.parse import urljoin, urlparse
import time
import random

from .anti_detection import (
    AntiDetectionConfig, 
    create_stealth_config,
    create_fast_config,
    SmartRetryManager
)


class EnhancedAsyncFetcher:
    """增强版异步网页抓取器 - 集成反反爬"""
    
    def __init__(self, 
                 anti_detection_config: Optional[AntiDetectionConfig] = None,
                 concurrency: int = 3,  # 降低默认并发，减少被封概率
                 timeout: int = 30,
                 follow_redirects: bool = True,
                 stealth_mode: bool = False):
        """
        初始化增强版抓取器
        
        Args:
            anti_detection_config: 反检测配置
            concurrency: 并发数（建议3-5，太高容易被封）
            timeout: 超时时间
            follow_redirects: 是否跟随重定向
            stealth_mode: 是否启用隐形模式（更慢但更隐蔽）
        """
        if stealth_mode:
            self.config = create_stealth_config()
        else:
            self.config = anti_detection_config or create_fast_config()
        
        self.concurrency = concurrency
        self.timeout = aiohttp.ClientTimeout(
            total=timeout,
            connect=10,
            sock_read=timeout
        )
        self.follow_redirects = follow_redirects
        self.semaphore = asyncio.Semaphore(concurrency)
        self.results = []
        self.failed_urls = []
        
        # 跟踪请求时间，用于自适应延迟
        self.request_times = []
        
    async def fetch_single(self, url_item: Dict, session: aiohttp.ClientSession) -> Optional[Dict]:
        """
        抓取单个URL（带反反爬策略）
        """
        url = url_item.get("url") if isinstance(url_item, dict) else url_item
        metadata = url_item if isinstance(url_item, dict) else {"url": url}
        
        # 获取反检测配置
        headers = self.config.get_headers()
        proxy = self.config.get_proxy()
        
        # 自适应延迟
        delay = await self.config.delayer.sleep()
        
        retry_count = 0
        max_retries = self.config.max_retries
        
        while retry_count < max_retries:
            try:
                async with self.semaphore:
                    start_time = time.time()
                    
                    # 准备请求参数
                    request_kwargs = {
                        "headers": headers,
                        "timeout": self.timeout,
                        "ssl": False,  # 禁用SSL验证，避免证书问题
                        "allow_redirects": self.follow_redirects,
                    }
                    
                    # 添加代理（如果配置了）
                    if proxy and proxy.http:
                        request_kwargs["proxy"] = proxy.http
                    
                    async with session.get(url, **request_kwargs) as response:
                        request_time = time.time() - start_time
                        self.request_times.append(request_time)
                        
                        # 记录请求信息
                        result = {
                            "url": url,
                            "status": response.status,
                            "headers": dict(response.headers),
                            "request_time": request_time,
                            **metadata
                        }
                        
                        # 根据状态码处理
                        if response.status == 200:
                            # 成功
                            content = await response.text()
                            result["content"] = content
                            result["content_type"] = response.headers.get("Content-Type", "")
                            result["final_url"] = str(response.url)
                            result["success"] = True
                            
                            # 记录成功，减少延迟
                            self.config.delayer.record_success()
                            
                            return result
                            
                        elif response.status in [301, 302, 307, 308]:
                            # 重定向
                            result["success"] = False
                            result["error"] = f"Redirect: {response.headers.get('Location', 'unknown')}"
                            return result
                            
                        elif response.status == 429:
                            # 请求过于频繁 - 需要重试并增加延迟
                            result["success"] = False
                            result["error"] = "Rate limited (429)"
                            
                            # 指数退避
                            wait_time = (2 ** retry_count) + random.uniform(1, 3)
                            print(f"    [RATE LIMIT] 429 detected, waiting {wait_time:.1f}s before retry {retry_count + 1}")
                            await asyncio.sleep(wait_time)
                            
                            # 更换User-Agent
                            headers = self.config.get_headers()
                            
                            retry_count += 1
                            self.config.delayer.record_error()
                            continue
                            
                        elif response.status == 403:
                            # 访问被拒绝 - 尝试更换代理和UA
                            result["success"] = False
                            result["error"] = f"Forbidden (403)"
                            
                            if retry_count < max_retries - 1:
                                print(f"    [FORBIDDEN] 403 detected, rotating headers and retrying...")
                                headers = self.config.get_headers()
                                if proxy:
                                    proxy = self.config.get_proxy()
                                await asyncio.sleep(random.uniform(2, 5))
                                retry_count += 1
                                continue
                            return result
                            
                        elif response.status == 503:
                            # 服务不可用 - 等待后重试
                            result["success"] = False
                            result["error"] = f"Service unavailable (503)"
                            
                            if retry_count < max_retries - 1:
                                wait_time = 5 + random.uniform(1, 5)
                                print(f"    [SERVICE UNAVAILABLE] Waiting {wait_time:.1f}s before retry...")
                                await asyncio.sleep(wait_time)
                                retry_count += 1
                                continue
                            return result
                            
                        else:
                            # 其他错误
                            result["success"] = False
                            result["error"] = f"HTTP {response.status}"
                            
                            # 服务器错误(5xx)尝试重试
                            if response.status >= 500 and retry_count < max_retries - 1:
                                await asyncio.sleep(2 ** retry_count)
                                retry_count += 1
                                continue
                            return result
                            
            except asyncio.TimeoutError:
                error_msg = f"Timeout after {self.timeout.total}s"
                print(f"    [TIMEOUT] {url[:60]}... - Retry {retry_count + 1}/{max_retries}")
                
                if retry_count < max_retries - 1:
                    await asyncio.sleep(2 ** retry_count)
                    retry_count += 1
                    continue
                    
                return {
                    "url": url,
                    "success": False,
                    "error": error_msg,
                    **metadata
                }
                
            except aiohttp.ClientConnectorError as e:
                error_msg = f"Connection error: {str(e)}"
                print(f"    [CONNECTION ERROR] {url[:60]}... - {error_msg}")
                
                if retry_count < max_retries - 1:
                    await asyncio.sleep(2 ** retry_count)
                    retry_count += 1
                    continue
                    
                return {
                    "url": url,
                    "success": False,
                    "error": error_msg,
                    **metadata
                }
                
            except aiohttp.ClientOSError as e:
                error_msg = f"OS error: {str(e)}"
                print(f"    [OS ERROR] {url[:60]}...")
                
                if retry_count < max_retries - 1:
                    await asyncio.sleep(1)
                    retry_count += 1
                    continue
                    
                return {
                    "url": url,
                    "success": False,
                    "error": error_msg,
                    **metadata
                }
                
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                print(f"    [ERROR] {url[:60]}... - {error_msg}")
                
                return {
                    "url": url,
                    "success": False,
                    "error": error_msg,
                    **metadata
                }
        
        # 所有重试都失败了
        return {
            "url": url,
            "success": False,
            "error": f"Failed after {max_retries} retries",
            **metadata
        }
    
    async def fetch_all(self, 
                        url_items: List[Dict],
                        progress_callback: Optional[Callable] = None) -> List[Dict]:
        """
        批量抓取URL（带反反爬策略）
        """
        self.results = []
        self.failed_urls = []
        
        # 创建连接池配置
        connector = aiohttp.TCPConnector(
            limit=self.concurrency * 2,
            limit_per_host=self.concurrency,
            enable_cleanup_closed=True,
            force_close=True,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        # 创建会话
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout
        ) as session:
            
            # 创建任务
            tasks = []
            for i, url_item in enumerate(url_items):
                task = self.fetch_single(url_item, session)
                tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for result in results:
                if isinstance(result, Exception):
                    print(f"    [TASK ERROR] {result}")
                elif result:
                    self.results.append(result)
                    if not result.get("success"):
                        self.failed_urls.append(result.get("url"))
            
            return self.results
    
    def get_stats(self) -> Dict:
        """获取抓取统计信息"""
        total = len(self.results)
        success = sum(1 for r in self.results if r.get("success"))
        failed = total - success
        
        avg_time = 0
        if self.request_times:
            avg_time = sum(self.request_times) / len(self.request_times)
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": f"{success/total*100:.1f}%" if total > 0 else "0%",
            "avg_request_time": f"{avg_time:.2f}s",
            "failed_urls": self.failed_urls
        }


# 便捷函数
def create_stealth_fetcher(concurrency: int = 2, timeout: int = 45) -> EnhancedAsyncFetcher:
    """
    创建隐形模式抓取器（最高反检测，但较慢）
    
    适用场景：
    - 目标网站有严格的反爬机制
    - 需要高成功率
    - 可以接受较慢的速度
    """
    return EnhancedAsyncFetcher(
        anti_detection_config=create_stealth_config(),
        concurrency=concurrency,  # 低并发，减少被封概率
        timeout=timeout,
        stealth_mode=True
    )


def create_balanced_fetcher(concurrency: int = 3, timeout: int = 30) -> EnhancedAsyncFetcher:
    """
    创建平衡模式抓取器（速度和隐蔽性平衡）
    
    适用场景：
    - 一般反爬机制的网站
    - 需要平衡速度和成功率
    """
    return EnhancedAsyncFetcher(
        anti_detection_config=create_fast_config(),
        concurrency=concurrency,
        timeout=timeout,
        stealth_mode=False
    )
