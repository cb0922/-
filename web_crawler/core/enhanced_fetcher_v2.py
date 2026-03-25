#!/usr/bin/env python3
"""
增强版异步抓取器 V2
优化点：
1. 支持 Brotli 压缩
2. 智能重试机制（指数退避）
3. User-Agent 轮换
4. 更好的错误处理和分类
5. 代理支持
"""
import asyncio
import aiohttp
import random
import ssl
import certifi
from typing import List, Dict, Optional
from urllib.parse import urlparse
from datetime import datetime


# 轮换的 User-Agent 列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


def get_random_headers():
    """获取随机请求头"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",  # 支持 Brotli
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


class EnhancedFetcherV2:
    """增强版异步抓取器"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3, 
                 use_proxy: bool = False, proxy_file: str = None,
                 headers: dict = None):  # 添加 headers 参数保持兼容
        self.timeout = aiohttp.ClientTimeout(total=timeout, connect=10, sock_read=timeout)
        self.max_retries = max_retries
        self.use_proxy = use_proxy
        self.proxies = []
        self.headers = headers or get_random_headers()  # 保存 headers
        
        # SSL 上下文
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # 加载代理
        if use_proxy and proxy_file:
            self._load_proxies(proxy_file)
    
    def _load_proxies(self, proxy_file: str):
        """加载代理列表"""
        try:
            import json
            with open(proxy_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.proxies = data.get('proxies', [])
        except Exception as e:
            print(f"[WARN] 加载代理失败: {e}")
    
    def _get_proxy(self) -> Optional[str]:
        """获取随机代理"""
        if not self.proxies:
            return None
        proxy = random.choice(self.proxies)
        return f"http://{proxy}"
    
    def _classify_error(self, error: Exception, url: str) -> Dict:
        """分类错误类型"""
        error_str = str(error).lower()
        error_type = "unknown"
        suggestion = ""
        
        # DNS 错误
        if any(x in error_str for x in ['name or service not known', 'no address associated', 
                                        'getaddrinfo failed', 'nodename nor servname']):
            error_type = "dns_error"
            suggestion = "域名解析失败，可能是网址已失效或网络问题"
        
        # 连接错误
        elif any(x in error_str for x in ['cannot connect to host', 'connection refused',
                                          'connect call failed']):
            error_type = "connection_error"
            suggestion = "无法连接服务器，可能是网站关闭或防火墙拦截"
        
        # 超时错误
        elif 'timeout' in error_str:
            error_type = "timeout"
            suggestion = "请求超时，网站响应过慢"
        
        # SSL 错误
        elif 'ssl' in error_str:
            error_type = "ssl_error"
            suggestion = "SSL 证书错误"
        
        # HTTP 错误
        elif '400' in error_str:
            error_type = "http_400"
            suggestion = "请求格式错误，可能需要特殊请求头"
        
        elif '403' in error_str:
            error_type = "http_403"
            suggestion = "访问被拒绝，可能有反爬机制，建议开启代理"
        
        elif '404' in error_str:
            error_type = "http_404"
            suggestion = "页面不存在"
        
        elif '500' in error_str:
            error_type = "http_500"
            suggestion = "服务器内部错误，网站暂时不可用"
        
        elif '502' in error_str or '503' in error_str or '504' in error_str:
            error_type = "http_5xx"
            suggestion = "服务器过载或维护中"
        
        return {
            "error_type": error_type,
            "error_message": str(error),
            "suggestion": suggestion
        }
    
    async def fetch_single(self, session: aiohttp.ClientSession, url: str, 
                          retry_count: int = 0) -> Dict:
        """抓取单个 URL，带重试机制"""
        result = {
            "url": url,
            "success": False,
            "content": "",
            "status": None,
            "error": None,
            "error_type": None,
            "retry_count": retry_count
        }
        
        try:
            # 获取代理
            proxy = self._get_proxy() if self.use_proxy else None
            
            # 随机延迟，避免请求过快
            if retry_count > 0:
                delay = min(2 ** retry_count, 30)  # 指数退避，最多30秒
                await asyncio.sleep(delay)
            
            async with session.get(url, proxy=proxy, ssl=self.ssl_context) as response:
                result["status"] = response.status
                
                if response.status == 200:
                    # 根据内容类型处理
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'text/html' in content_type:
                        result["content"] = await response.text()
                        result["content_type"] = "text/html"
                    elif 'application/json' in content_type:
                        result["content"] = await response.json()
                        result["content_type"] = "application/json"
                    else:
                        # 其他类型，获取二进制
                        result["content"] = await response.read()
                        result["content_type"] = content_type
                    
                    result["success"] = True
                    
                elif response.status == 403:
                    error_info = self._classify_error(
                        Exception(f"HTTP {response.status}"), url
                    )
                    result["error"] = f"访问被拒绝(403)：可能需要登录或有反爬机制"
                    result["error_type"] = error_info["error_type"]
                    
                elif response.status == 500:
                    error_info = self._classify_error(
                        Exception(f"HTTP {response.status}"), url
                    )
                    result["error"] = f"服务器错误：HTTP 500"
                    result["error_type"] = error_info["error_type"]
                    
                else:
                    result["error"] = f"HTTP {response.status}"
                    result["error_type"] = f"http_{response.status}"
                    
        except aiohttp.ClientConnectorError as e:
            error_info = self._classify_error(e, url)
            result["error"] = f"连接错误：{error_info['error_message'][:100]}"
            result["error_type"] = error_info["error_type"]
            result["suggestion"] = error_info["suggestion"]
            
        except asyncio.TimeoutError:
            result["error"] = f"请求超时(重试{retry_count}次)"
            result["error_type"] = "timeout"
            result["suggestion"] = "网站响应过慢，建议增加超时时间或稍后重试"
            
        except Exception as e:
            error_info = self._classify_error(e, url)
            result["error"] = f"{error_info['error_type']}：{str(e)[:100]}"
            result["error_type"] = error_info["error_type"]
            result["suggestion"] = error_info["suggestion"]
        
        return result
    
    async def fetch_with_retry(self, session: aiohttp.ClientSession, 
                               url: str) -> Dict:
        """带重试的抓取"""
        last_result = None
        
        for retry in range(self.max_retries + 1):
            result = await self.fetch_single(session, url, retry)
            
            if result["success"]:
                return result
            
            last_result = result
            
            # 某些错误不需要重试
            if result["error_type"] in ["dns_error", "http_404"]:
                break
            
            if retry < self.max_retries:
                print(f"  [RETRY] {url[:50]}... 第{retry+1}次重试...")
        
        return last_result
    
    async def fetch_all(self, urls: List[Dict]) -> List[Dict]:
        """批量抓取 URL"""
        if not urls:
            return []
        
        results = []
        
        # 创建会话
        connector = aiohttp.TCPConnector(
            limit=10,  # 连接池限制
            limit_per_host=3,  # 每个主机最多3个连接
            ttl_dns_cache=300,  # DNS 缓存5分钟
            use_dns_cache=True,
        )
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers=get_random_headers()
        ) as session:
            # 限制并发数
            semaphore = asyncio.Semaphore(5)
            
            async def fetch_with_limit(url_item):
                async with semaphore:
                    url = url_item.get("url") if isinstance(url_item, dict) else url_item
                    return await self.fetch_with_retry(session, url)
            
            # 创建所有任务
            tasks = [fetch_with_limit(u) for u in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    url = urls[i].get("url") if isinstance(urls[i], dict) else urls[i]
                    processed_results.append({
                        "url": url,
                        "success": False,
                        "error": f"任务异常: {str(result)[:100]}",
                        "error_type": "task_exception"
                    })
                else:
                    processed_results.append(result)
            
            return processed_results
    
    def run(self, urls: List[Dict]) -> List[Dict]:
        """同步入口"""
        return asyncio.run(self.fetch_all(urls))


# 保持与旧版兼容的函数
def get_random_headers():
    """获取随机请求头"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


class AsyncFetcher(EnhancedFetcherV2):
    """兼容旧版名称"""
    pass


if __name__ == "__main__":
    # 测试
    fetcher = EnhancedFetcherV2(timeout=30, max_retries=3)
    
    test_urls = [
        {"url": "https://www.example.com"},
        {"url": "https://www.invalid-domain-12345.com"},  # DNS 错误
    ]
    
    results = fetcher.run(test_urls)
    for r in results:
        print(f"URL: {r['url'][:50]}")
        print(f"Success: {r['success']}")
        if r['error']:
            print(f"Error: {r['error']}")
            print(f"Type: {r.get('error_type')}")
        print("-" * 50)
