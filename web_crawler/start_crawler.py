#!/usr/bin/env python3
"""
比赛通知爬虫 - 统一启动入口
简化版，只保留核心功能
"""
import sys
import os
import argparse

# 确保可以导入core模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3
from core.url_manager import URLManager


def main():
    """主函数 - 简化版启动入口"""
    parser = argparse.ArgumentParser(
        description="比赛通知爬虫 - 自动抓取比赛通知和文档",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --urls urls.csv --mode all
  %(prog)s --urls urls.csv --mode doc --output ./output
  %(prog)s --urls urls.csv --mode html --timeout 60

模式说明:
  all  - 下载文档 + 生成HTML/Word报告
  doc  - 仅下载文档（PDF/Word/Excel等）
  html - 仅生成HTML/Word报告

更多帮助: https://github.com/your-repo
        """
    )
    
    parser.add_argument("--urls", "-u", default="urls.csv",
                       help="URL列表文件 (CSV格式，默认: urls.csv)")
    parser.add_argument("--mode", "-m", choices=["all", "doc", "html"], default="all",
                       help="爬取模式: all=全部, doc=仅文档, html=仅报告 (默认: all)")
    parser.add_argument("--output", "-o", default="./output",
                       help="输出目录 (默认: ./output)")
    parser.add_argument("--timeout", "-t", type=int, default=30,
                       help="请求超时时间/秒 (默认: 30)")
    parser.add_argument("--max-retries", type=int, default=2,
                       help="失败重试次数 (默认: 2)")
    parser.add_argument("--no-auto-remove", action="store_true",
                       help="禁用自动删除失败网址（推荐）")
    parser.add_argument("--proxy", action="store_true",
                       help="启用代理IP")
    parser.add_argument("--proxy-file", default="proxies.json",
                       help="代理配置文件 (默认: proxies.json)")
    parser.add_argument("--version", action="version", version="%(prog)s 3.0")
    
    args = parser.parse_args()
    
    # 打印启动信息
    print("=" * 70)
    print("              比赛通知爬虫 V3.0")
    print("              Competition Notice Crawler")
    print("=" * 70)
    print(f"模式: {args.mode}")
    print(f"URL文件: {args.urls}")
    print(f"输出目录: {args.output}")
    print(f"超时: {args.timeout}s")
    print(f"自动删除: {'禁用' if args.no_auto_remove else '启用'}")
    print("=" * 70)
    
    # 检查URL文件
    if not os.path.exists(args.urls):
        print(f"\n[错误] URL文件不存在: {args.urls}")
        print("请创建urls.csv文件，格式: url,name,category")
        return 1
    
    # 加载URL
    print(f"\n[1/4] 加载URL列表...")
    url_manager = URLManager()
    try:
        url_manager.load_from_file(args.urls)
    except Exception as e:
        print(f"[错误] 加载URL失败: {e}")
        return 1
    
    urls = url_manager.urls
    print(f"  [OK] 已加载 {len(urls)} 个URL")
    
    if len(urls) == 0:
        print("[错误] 没有有效的URL")
        return 1
    
    # 创建爬虫
    print(f"\n[2/4] 启动爬虫...")
    crawler = EnhancedCompetitionCrawlerV3(
        use_dynamic=False,
        timeout=args.timeout,
        use_proxy=args.proxy,
        proxy_file=args.proxy_file,
        max_retries=args.max_retries,
        auto_remove_failed=not args.no_auto_remove,  # 默认禁用自动删除
        urls_file=args.urls
    )
    
    # 开始爬取
    try:
        results = crawler.crawl_all(urls)
    except Exception as e:
        print(f"\n[错误] 爬取过程异常: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    if not results:
        print("\n[警告] 没有成功爬取的页面")
        return 0
    
    print(f"\n  [OK] 成功爬取 {len(results)} 个页面")
    
    # 统计
    competition_pages = [r for r in results if r.get("is_competition_related")]
    all_docs = []
    competition_docs = []
    for r in results:
        all_docs.extend(r.get("all_documents", []))
        competition_docs.extend(r.get("competition_documents", []))
    
    print(f"\n  [统计]")
    print(f"    比赛相关页面: {len(competition_pages)}")
    print(f"    总文档数: {len(all_docs)}")
    print(f"    比赛相关文档: {len(competition_docs)}")
    
    # 根据模式执行不同操作
    if args.mode in ["all", "doc"] and competition_docs:
        print(f"\n[3/4] 下载文档...")
        doc_output = os.path.join(args.output, "documents")
        try:
            doc_results = crawler.download_documents(competition_docs, output_dir=doc_output)
            print(f"  [OK] 下载完成: {len(doc_results)} 个文档")
        except Exception as e:
            print(f"  [警告] 文档下载出错: {e}")
    
    if args.mode in ["all", "html"]:
        print(f"\n[3/4] 生成HTML报告...")
        try:
            report_path = crawler.generate_html_report()
            if report_path:
                print(f"  [OK] HTML报告: {report_path}")
        except Exception as e:
            print(f"  [警告] HTML报告生成出错: {e}")
    
    # 生成Word文档
    print(f"\n[3.5/4] 生成Word报告...")
    try:
        word_path = crawler.generate_word_report(output_dir=os.path.join(args.output, "word_reports"))
        if word_path:
            print(f"  [OK] Word报告: {word_path}")
    except Exception as e:
        print(f"  [警告] Word报告生成出错: {e}")
    
    # 保存JSON数据
    print(f"\n[4/4] 保存数据...")
    try:
        json_path = crawler.save_json_data(output_dir=os.path.join(args.output, "data"))
        if json_path:
            print(f"  [OK] JSON数据: {json_path}")
    except Exception as e:
        print(f"  [警告] JSON保存出错: {e}")
    
    # 完成
    print("\n" + "=" * 70)
    print("                         爬取完成!")
    print("=" * 70)
    print(f"\n输出文件:")
    if args.mode in ["all", "doc"]:
        print(f"  - 文档: {args.output}/documents/")
    if args.mode in ["all", "html"]:
        print(f"  - HTML报告: ./reports/")
    print(f"  - Word报告: {args.output}/word_reports/")
    print(f"  - JSON数据: {args.output}/data/")
    print("\n" + "=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
