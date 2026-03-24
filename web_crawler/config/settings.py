"""
爬虫工具配置文件
"""
import os

# 基础路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据存储路径
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# 爬虫配置
CRAWLER_CONFIG = {
    # 并发请求数
    "concurrency": 5,
    
    # 请求超时（秒）
    "timeout": 30,
    
    # 重试次数
    "max_retries": 3,
    
    # 请求间隔（秒）
    "delay": 1,
    
    # 是否遵守 robots.txt
    "respect_robots": True,
    
    # User-Agent
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0"
}

# 存储配置
STORAGE_CONFIG = {
    # 存储格式: json, csv, sqlite
    "format": "json",
    
    # 数据文件路径
    "data_file": os.path.join(DATA_DIR, "crawled_data.json"),
    "csv_file": os.path.join(DATA_DIR, "crawled_data.csv"),
    "db_file": os.path.join(DATA_DIR, "crawled_data.db"),
    
    # 是否按日期分文件存储
    "split_by_date": True,
}

# URL源文件配置
URL_SOURCE_CONFIG = {
    # 支持的文件格式
    "supported_formats": [".csv", ".xlsx", ".xls"],
    
    # 默认列名映射
    "column_mapping": {
        "url": ["url", "网址", "链接", "link", "href"],
        "name": ["name", "名称", "标题", "title"],
        "category": ["category", "分类", "类别", "type"],
        "priority": ["priority", "优先级", "priority"],
    }
}
