"""
Web Crawler Tool
网页信息采集与本地化存储工具
"""

__version__ = "1.0.0"
__author__ = "Web Crawler"

from core.url_manager import URLManager
from core.fetcher import AsyncFetcher
from core.parser import ContentParser, ArticleParser
from storage.database import DataStorage, StorageManager

__all__ = [
    "URLManager",
    "AsyncFetcher", 
    "ContentParser",
    "ArticleParser",
    "DataStorage",
    "StorageManager",
]
