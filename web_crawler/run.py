#!/usr/bin/env python3
"""
简化版运行脚本 - 适合快速使用

直接修改下面的配置即可运行
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.url_manager import URLManager, create_url_template
from core.fetcher import AsyncFetcher
from core.parser import ContentParser
from storage.database import StorageManager
from config.settings import DATA_DIR


def quick_crawl():
    """
    快速爬取示例
    修改以下配置后运行: python run.py
    """
    
    # ==================== 配置区域 ====================
    
    # 1. URL来源（CSV或Excel文件路径）
    # 如果不存在，可以先用 create_url_template("urls.csv") 创建模板
    URL_FILE = "urls.csv"
    
    # 2. 输出格式: "json", "csv", "sqlite" 或多个 "json,csv,sqlite"
    OUTPUT_FORMAT = "json,csv"
    
    # 3. 输出文件名（可选，留空则自动生成时间戳文件名）
    OUTPUT_NAME = ""
    
    # 4. 爬虫配置
    CONCURRENCY = 5      # 并发数
    TIMEOUT = 30         # 超时时间（秒）
    DELAY = 1.0          # 请求间隔（秒）
    
    # =================================================
    
    # 如果URL文件不存在，创建模板
    if not os.path.exists(URL_FILE):
        print(f"URL文件不存在，创建模板: {URL_FILE}")
        create_url_template(URL_FILE)
        print(f"\n请编辑 {URL_FILE} 文件添加要爬取的URL，然后重新运行")
        return
    
    print(f"=" * 50)
    print(f"开始爬取任务")
    print(f"=" * 50)
    
    # 1. 加载URL
    print(f"\n[1/4] 加载URL列表...")
    url_manager = URLManager()
    url_manager.load_from_file(URL_FILE)
    print(f"✓ 加载了 {len(url_manager.urls)} 个URL")
    
    # 2. 爬取
    print(f"\n[2/4] 开始爬取网页...")
    fetcher = AsyncFetcher(
        concurrency=CONCURRENCY,
        timeout=TIMEOUT,
        delay=DELAY
    )
    results = fetcher.run(url_manager.urls)
    print(f"✓ 爬取完成: {len(results)} 个结果")
    
    # 3. 解析
    print(f"\n[3/4] 解析网页内容...")
    parsed_data = []
    for result in results:
        if result.get("success"):
            try:
                parser = ContentParser(result["content"])
                data = parser.to_dict()
                data["url"] = result["url"]
                data["crawled_at"] = result.get("crawled_at")
                parsed_data.append(data)
            except Exception as e:
                print(f"  解析失败: {result['url']} - {e}")
    print(f"✓ 解析完成: {len(parsed_data)} 条数据")
    
    # 4. 保存
    print(f"\n[4/4] 保存数据...")
    storage_manager = StorageManager(DATA_DIR)
    formats = [f.strip() for f in OUTPUT_FORMAT.split(",")]
    saved = storage_manager.save(parsed_data, name=OUTPUT_NAME or None, formats=formats)
    for fmt, path in saved.items():
        print(f"  ✓ [{fmt.upper()}] {path}")
    
    print(f"\n" + "=" * 50)
    print(f"任务完成!")
    print(f"=" * 50)


if __name__ == "__main__":
    quick_crawl()
