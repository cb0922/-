#!/usr/bin/env python3
"""
网页爬虫工具主控脚本

功能：
1. 从CSV/Excel文件导入URL列表
2. 异步并发爬取网页内容
3. 解析并提取结构化数据
4. 支持JSON/CSV/SQLite多种格式存储

使用方法：
    python main.py --urls urls.csv --output data.json
    python main.py --urls urls.xlsx --format json,csv
"""
import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.url_manager import URLManager, create_url_template
from core.fetcher import AsyncFetcher
from core.parser import ContentParser, ArticleParser
from storage.database import StorageManager, DataStorage
from config.settings import CRAWLER_CONFIG, DATA_DIR


def print_banner():
    """打印程序横幅"""
    banner = """
============================================
          Web Crawler Tool v1.0           
       网页信息采集与本地化存储工具        
============================================
    """
    print(banner)


def crawl_urls(url_manager: URLManager, 
               concurrency: int = 5,
               timeout: int = 30,
               delay: float = 1.0) -> list:
    """
    爬取URL列表
    """
    urls = url_manager.urls
    if not urls:
        print("错误: 没有要爬取的URL")
        return []
    
    print(f"\n开始爬取 {len(urls)} 个网页...")
    print(f"并发数: {concurrency}, 超时: {timeout}s, 延迟: {delay}s\n")
    
    # 创建抓取器
    fetcher = AsyncFetcher(
        concurrency=concurrency,
        timeout=timeout,
        delay=delay
    )
    
    # 执行爬取
    results = fetcher.run(urls, show_progress=True)
    
    # 打印统计
    stats = fetcher.get_stats()
    print(f"\n爬取完成!")
    print(f"  总计: {stats['total']}")
    print(f"  成功: {stats['success']}")
    print(f"  失败: {stats['failed']}")
    print(f"  成功率: {stats['success_rate']}")
    
    if stats['failed_urls']:
        print(f"\n失败的URL (前10个):")
        for url in stats['failed_urls']:
            print(f"  - {url}")
    
    return results


def parse_content(results: list, parser_type: str = "auto") -> list:
    """
    解析网页内容
    """
    print(f"\n开始解析网页内容...")
    
    parsed_data = []
    
    for result in results:
        if not result.get("success"):
            continue
        
        url = result.get("url")
        content = result.get("content", "")
        content_type = result.get("content_type", "")
        
        # 只解析HTML内容
        if "text/html" not in content_type and content_type:
            # 非HTML内容，保存原始信息
            parsed_data.append({
                "url": url,
                "type": "raw",
                "content_type": content_type,
                "status": result.get("status"),
                "crawled_at": result.get("crawled_at")
            })
            continue
        
        try:
            # 根据解析器类型选择解析方式
            if parser_type == "article":
                parser = ArticleParser(content)
                data = parser.get_article()
            else:
                parser = ContentParser(content)
                data = parser.to_dict()
            
            # 添加元数据
            data.update({
                "url": url,
                "status": result.get("status"),
                "crawled_at": result.get("crawled_at")
            })
            
            parsed_data.append(data)
            
        except Exception as e:
            print(f"解析失败 {url}: {str(e)}")
            # 保存原始内容
            parsed_data.append({
                "url": url,
                "type": "parse_error",
                "error": str(e),
                "status": result.get("status"),
                "crawled_at": result.get("crawled_at")
            })
    
    print(f"解析完成，共 {len(parsed_data)} 条数据")
    return parsed_data


def save_data(data: list, output_formats: list, output_name: str = None):
    """
    保存数据
    """
    print(f"\n开始保存数据...")
    
    storage_manager = StorageManager(DATA_DIR)
    saved_paths = storage_manager.save(data, name=output_name, formats=output_formats)
    
    print(f"数据已保存到:")
    for fmt, path in saved_paths.items():
        print(f"  [{fmt.upper()}] {path}")
    
    return saved_paths


def main():
    """主函数"""
    print_banner()
    
    # 命令行参数解析
    parser = argparse.ArgumentParser(
        description="网页信息采集与本地化存储工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 从CSV文件导入URL并爬取
  python main.py --urls urls.csv
  
  # 指定输出格式为JSON和CSV
  python main.py --urls urls.xlsx --format json,csv
  
  # 创建URL导入模板
  python main.py --template template.csv
  
  # 使用文章解析器
  python main.py --urls urls.csv --parser article
  
  # 调整并发数和延迟
  python main.py --urls urls.csv --concurrency 10 --delay 0.5
        """
    )
    
    parser.add_argument(
        "--urls", "-u",
        help="URL源文件路径 (CSV或Excel格式)"
    )
    parser.add_argument(
        "--format", "-f",
        default="json",
        help="输出格式，支持: json, csv, sqlite (多个用逗号分隔，默认: json)"
    )
    parser.add_argument(
        "--output", "-o",
        help="输出文件名（不含扩展名）"
    )
    parser.add_argument(
        "--parser", "-p",
        choices=["auto", "article"],
        default="auto",
        help="内容解析器类型 (默认: auto)"
    )
    parser.add_argument(
        "--concurrency", "-c",
        type=int,
        default=CRAWLER_CONFIG["concurrency"],
        help=f"并发请求数 (默认: {CRAWLER_CONFIG['concurrency']})"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=CRAWLER_CONFIG["timeout"],
        help=f"请求超时时间，秒 (默认: {CRAWLER_CONFIG['timeout']})"
    )
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=CRAWLER_CONFIG["delay"],
        help=f"请求间隔时间，秒 (默认: {CRAWLER_CONFIG['delay']})"
    )
    parser.add_argument(
        "--template",
        metavar="PATH",
        help="创建URL导入模板文件"
    )
    
    args = parser.parse_args()
    
    # 创建模板
    if args.template:
        create_url_template(args.template)
        return
    
    # 检查URL文件
    if not args.urls:
        print("错误: 请提供URL源文件路径 (--urls)")
        print("使用 --help 查看帮助信息")
        return
    
    if not os.path.exists(args.urls):
        print(f"错误: 文件不存在: {args.urls}")
        return
    
    # 1. 加载URL
    print(f"\n正在加载URL列表: {args.urls}")
    url_manager = URLManager()
    try:
        url_manager.load_from_file(args.urls)
    except Exception as e:
        print(f"加载URL失败: {str(e)}")
        return
    
    stats = url_manager.get_stats()
    print(f"\nURL统计:")
    print(f"  总计: {stats['total']}")
    if stats['by_category']:
        print(f"  按分类: {stats['by_category']}")
    
    # 2. 爬取网页
    results = crawl_urls(
        url_manager,
        concurrency=args.concurrency,
        timeout=args.timeout,
        delay=args.delay
    )
    
    if not results:
        print("没有获取到任何数据")
        return
    
    # 3. 解析内容
    parsed_data = parse_content(results, parser_type=args.parser)
    
    # 4. 保存数据
    output_formats = [f.strip() for f in args.format.split(",")]
    save_data(parsed_data, output_formats, output_name=args.output)
    
    print("\n[OK] 全部任务完成!")


if __name__ == "__main__":
    main()
