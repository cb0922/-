"""
异步网页抓取模块
使用 aiohttp 实现高并发爬取
"""
import aiohttp
import asyncio
import aiofiles
from typing import List, Dict, Optional, Callable
from urllib.parse import urljoin, urlparse
import time
import random
from tqdm import tqdm


# 真实浏览器 User-Agent 列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]


def get_random_headers():
    """获取随机请求头"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }


class AsyncFetcher:
    """异步网页抓取器"""
    
    def __init__(self, 
                 concurrency: int = 5,
                 timeout: int = 30,
                 max_retries: int = 3,
                 delay: float = 1.0,
                 headers: Optional[Dict] = None,
                 follow_redirects: bool = True,
                 use_proxy: bool = False,
                 proxy_file: Optional[str] = None):
        self.concurrency = concurrency
        self.timeout = aiohttp.ClientTimeout(total=timeout, connect=10)
        self.max_retries = max_retries
        self.delay = delay
        self.headers = headers or get_random_headers()
        self.follow_redirects = follow_redirects
        self.semaphore = asyncio.Semaphore(concurrency)
        self.results = []
        self.failed_urls = []
        
        # 代理设置
        self.use_proxy = use_proxy
        self.proxy_manager = None
        if use_proxy and proxy_file:
            try:
                from core.proxy_manager import ProxyManager
                self.proxy_manager = ProxyManager(proxy_file)
                print(f"  [PROXY] Loaded {len(self.proxy_manager.proxies)} proxies from {proxy_file}")
            except Exception as e:
                print(f"  [PROXY] Failed to load proxy manager: {e}")
    
    def _get_proxy(self) -> Optional[str]:
        """获取代理"""
        if self.proxy_manager:
            proxy = self.proxy_manager.get_random() or self.proxy_manager.get_next()
            if proxy:
                return str(proxy)
        return None
    
    async def fetch(self, session: aiohttp.ClientSession, 
                    url_item: Dict) -> Optional[Dict]:
        """
        抓取单个URL
        """
        url = url_item.get("url") if isinstance(url_item, dict) else url_item
        metadata = url_item if isinstance(url_item, dict) else {"url": url}
        
        async with self.semaphore:
            for attempt in range(self.max_retries):
                try:
                    # 随机延迟，避免请求过快
                    if attempt > 0:
                        await asyncio.sleep(random.uniform(1, 3))
                    
                    # 准备请求参数
                    request_kwargs = {
                        "headers": self.headers,
                        "timeout": self.timeout,
                        "ssl": False,  # 禁用SSL验证，避免证书问题
                        "allow_redirects": self.follow_redirects,
                    }
                    
                    # 添加代理
                    if self.use_proxy and self.proxy_manager:
                        proxy_url = self._get_proxy()
                        if proxy_url:
                            request_kwargs["proxy"] = proxy_url
                    
                    async with session.get(url, **request_kwargs) as response:
                        # 记录请求信息
                        result = {
                            "url": url,
                            "status": response.status,
                            "headers": dict(response.headers),
                            **metadata
                        }
                        
                        if response.status == 200:
                            # 尝试获取文本内容
                            try:
                                # 自动检测编码
                                content = await response.text()
                                result["content"] = content
                                result["content_type"] = response.headers.get("Content-Type", "")
                                result["final_url"] = str(response.url)  # 记录最终URL（重定向后）
                                result["success"] = True
                            except Exception as e:
                                result["success"] = False
                                result["error"] = f"内容读取失败: {str(e)}"
                        elif response.status in [301, 302, 307, 308]:
                            # 重定向
                            result["success"] = False
                            result["error"] = f"重定向: HTTP {response.status} -> {response.headers.get('Location', 'unknown')}"
                        elif response.status == 403:
                            result["success"] = False
                            result["error"] = f"访问被拒绝(403): 可能需要登录或有反爬机制"
                        elif response.status == 404:
                            result["success"] = False
                            result["error"] = f"页面不存在(404)"
                        elif response.status >= 500:
                            result["success"] = False
                            result["error"] = f"服务器错误: HTTP {response.status}"
                        else:
                            result["success"] = False
                            result["error"] = f"HTTP {response.status}"
                        
                        # 添加延迟避免请求过快
                        if self.delay > 0:
                            await asyncio.sleep(random.uniform(self.delay * 0.5, self.delay * 1.5))
                        
                        return result
                        
                except asyncio.TimeoutError:
                    if attempt == self.max_retries - 1:
                        return {
                            "url": url,
                            "success": False,
                            "error": f"请求超时(重试{self.max_retries}次)",
                            **metadata
                        }
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                    
                except aiohttp.ClientConnectorError as e:
                    if attempt == self.max_retries - 1:
                        return {
                            "url": url,
                            "success": False,
                            "error": f"连接错误: {str(e)}",
                            **metadata
                        }
                    await asyncio.sleep(2 ** attempt)
                    
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        return {
                            "url": url,
                            "success": False,
                            "error": f"{type(e).__name__}: {str(e)}",
                            **metadata
                        }
                    await asyncio.sleep(2 ** attempt)
    
    async def fetch_all(self, 
                        url_items: List[Dict],
                        progress_callback: Optional[Callable] = None) -> List[Dict]:
        """
        批量抓取URL
        """
        self.results = []
        self.failed_urls = []
        
        connector = aiohttp.TCPConnector(
            limit=self.concurrency * 2,
            limit_per_host=self.concurrency,
            enable_cleanup_closed=True,
            force_close=True,
            ttl_dns_cache=300,  # DNS缓存5分钟
            use_dns_cache=True,
        )
        
        # 创建会话时使用随机headers
        headers = get_random_headers()
        
        async with aiohttp.ClientSession(
            connector=connector,
            headers=headers,
            trust_env=True  # 使用系统代理设置
        ) as session:
            tasks = []
            for url_item in url_items:
                task = asyncio.create_task(
                    self._fetch_with_progress(session, url_item, progress_callback)
                )
                tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for result in results:
                if isinstance(result, Exception):
                    continue
                if result:
                    self.results.append(result)
                    if not result.get("success"):
                        self.failed_urls.append(result.get("url"))
        
        return self.results
    
    async def _fetch_with_progress(self, 
                                    session: aiohttp.ClientSession,
                                    url_item: Dict,
                                    progress_callback: Optional[Callable]) -> Optional[Dict]:
        """带进度回调的抓取"""
        result = await self.fetch(session, url_item)
        if progress_callback:
            progress_callback()
        return result
    
    def run(self, url_items: List[Dict], 
            show_progress: bool = True) -> List[Dict]:
        """
        同步接口：运行抓取任务
        """
        if show_progress:
            pbar = tqdm(total=len(url_items), desc="抓取进度")
            
            def update():
                pbar.update(1)
            
            results = asyncio.run(self.fetch_all(url_items, update))
            pbar.close()
        else:
            results = asyncio.run(self.fetch_all(url_items))
        
        return results
    
    def get_stats(self) -> Dict:
        """获取抓取统计信息"""
        total = len(self.results)
        success = sum(1 for r in self.results if r.get("success"))
        failed = total - success
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": f"{success/total*100:.1f}%" if total > 0 else "0%",
            "failed_urls": self.failed_urls[:10]  # 只显示前10个失败URL
        }


class ContentFetcher:
    """内容抓取器（用于抓取特定类型的内容）"""
    
    def __init__(self, fetcher: Optional[AsyncFetcher] = None):
        self.fetcher = fetcher or AsyncFetcher()
    
    async def fetch_article(self, session: aiohttp.ClientSession, 
                           url: str) -> Dict:
        """抓取文章类型页面"""
        result = await self.fetcher.fetch(session, {"url": url})
        return result
    
    async def fetch_with_pagination(self, 
                                    base_url: str,
                                    page_param: str = "page",
                                    start_page: int = 1,
                                    end_page: int = 1,
                                    step: int = 1) -> List[Dict]:
        """
        抓取分页内容
        """
        urls = []
        for page in range(start_page, end_page + 1, step):
            if "?" in base_url:
                url = f"{base_url}&{page_param}={page}"
            else:
                url = f"{base_url}?{page_param}={page}"
            urls.append({"url": url, "page": page})
        
        return await self.fetcher.fetch_all(urls)
    
    def extract_links(self, html_content: str, 
                     base_url: str,
                     pattern: Optional[str] = None) -> List[str]:
        """
        从HTML中提取链接
        """
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'lxml')
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            
            # 过滤条件
            if pattern and pattern not in full_url:
                continue
            
            # 确保是同域名
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                links.append(full_url)
        
        return list(set(links))  # 去重
