#!/usr/bin/env python3
"""
自定义解析规则示例
根据特定网站的结构定制解析规则
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from core.fetcher import AsyncFetcher
from storage.database import StorageManager


class CustomSiteParser:
    """
    自定义站点解析器示例
    针对特定网站结构编写解析规则
    """
    
    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, 'lxml')
    
    def parse_news_site(self) -> dict:
        """
        新闻站点解析示例
        根据实际网站结构调整选择器
        """
        return {
            "title": self._safe_get_text('.article-title, h1'),
            "author": self._safe_get_text('.author-name, .byline'),
            "publish_time": self._safe_get_attr('time', 'datetime') or self._safe_get_text('.publish-time'),
            "content": self._safe_get_text('.article-content, .post-content'),
            "summary": self._safe_get_text('.summary, .excerpt'),
            "tags": self._safe_get_list('.tag, .article-tag'),
            "images": self._safe_get_images('.article-content img'),
        }
    
    def parse_product_site(self) -> dict:
        """
        电商产品页解析示例
        """
        return {
            "title": self._safe_get_text('.product-title, h1'),
            "price": self._safe_get_text('.price, .product-price'),
            "original_price": self._safe_get_text('.original-price'),
            "description": self._safe_get_text('.product-description'),
            "images": self._safe_get_images('.product-gallery img'),
            "specs": self._safe_get_table('.product-specs'),
            "stock": self._safe_get_text('.stock-status'),
        }
    
    def _safe_get_text(self, selector: str) -> str:
        """安全获取文本"""
        try:
            elem = self.soup.select_one(selector)
            return elem.get_text(strip=True) if elem else ""
        except:
            return ""
    
    def _safe_get_attr(self, selector: str, attr: str) -> str:
        """安全获取属性"""
        try:
            elem = self.soup.select_one(selector)
            return elem.get(attr, "") if elem else ""
        except:
            return ""
    
    def _safe_get_list(self, selector: str) -> list:
        """安全获取列表"""
        try:
            return [elem.get_text(strip=True) for elem in self.soup.select(selector)]
        except:
            return []
    
    def _safe_get_images(self, selector: str) -> list:
        """安全获取图片"""
        try:
            images = []
            for img in self.soup.select(selector):
                src = img.get('data-src') or img.get('src', '')
                alt = img.get('alt', '')
                if src:
                    images.append({"src": src, "alt": alt})
            return images
        except:
            return []
    
    def _safe_get_table(self, selector: str) -> dict:
        """安全获取表格数据"""
        try:
            table = self.soup.select_one(selector)
            if not table:
                return {}
            
            result = {}
            for row in table.find_all('tr'):
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    result[key] = value
            return result
        except:
            return {}


def demo_custom_parser():
    """
    使用自定义解析器的示例
    """
    # 这里应该替换为实际的URL列表
    urls = [
        {"url": "https://example-news.com/article/1", "type": "news"},
        {"url": "https://example-shop.com/product/1", "type": "product"},
    ]
    
    fetcher = AsyncFetcher(concurrency=3, delay=1)
    results = fetcher.run(urls)
    
    parsed_data = []
    for result in results:
        if not result.get("success"):
            continue
        
        url = result["url"]
        content = result["content"]
        page_type = result.get("type", "news")
        
        parser = CustomSiteParser(content)
        
        if page_type == "news":
            data = parser.parse_news_site()
        elif page_type == "product":
            data = parser.parse_product_site()
        else:
            data = {"title": "未知类型"}
        
        data["url"] = url
        data["type"] = page_type
        parsed_data.append(data)
    
    # 保存
    storage = StorageManager("./data")
    storage.save(parsed_data, name="custom_parsed", formats=["json"])
    
    print(f"解析完成，保存 {len(parsed_data)} 条数据")


if __name__ == "__main__":
    print("自定义解析器示例")
    print("请根据目标网站的实际HTML结构修改解析规则")
    # demo_custom_parser()  # 取消注释以运行
