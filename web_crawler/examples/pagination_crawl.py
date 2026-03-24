#!/usr/bin/env python3
"""
分页爬取示例
用于爬取有分页的列表页面
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.fetcher import AsyncFetcher
from core.parser import ContentParser
from storage.database import StorageManager
import asyncio


def crawl_pagination():
    """
    分页爬取示例
    """
    # 配置
    BASE_URL = "https://example.com/list"  # 基础URL
    START_PAGE = 1
    END_PAGE = 5
    PAGE_PARAM = "page"  # 分页参数名
    
    # 生成分页URL
    urls = []
    for page in range(START_PAGE, END_PAGE + 1):
        url = f"{BASE_URL}?{PAGE_PARAM}={page}"
        urls.append({"url": url, "page": page})
    
    print(f"将爬取 {len(urls)} 个分页")
    
    # 爬取
    fetcher = AsyncFetcher(concurrency=3, delay=2)
    results = fetcher.run(urls)
    
    # 解析每页的链接
    all_links = []
    for result in results:
        if result.get("success"):
            parser = ContentParser(result["content"])
            links = parser.get_links()
            all_links.extend(links)
            print(f"第 {result.get('page')} 页找到 {len(links)} 个链接")
    
    # 保存结果
    storage = StorageManager("./data")
    storage.save(all_links, name="pagination_links", formats=["json", "csv"])
    
    print(f"\n总共收集 {len(all_links)} 个链接")


if __name__ == "__main__":
    crawl_pagination()
