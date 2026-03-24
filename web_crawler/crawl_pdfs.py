#!/usr/bin/env python3
"""
比赛通知PDF专用爬虫
专门用于爬取网页上的比赛信息通知和公告PDF文件

使用方法:
    python crawl_pdfs.py --urls urls.csv
    python crawl_pdfs.py --urls urls.csv --download-only
"""
import argparse
import sys
import os
import json
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.url_manager import URLManager
from core.fetcher import AsyncFetcher
from core.parser import ContentParser, PDFLinkExtractor
from core.pdf_handler import PDFHandler


def print_banner():
    """打印程序横幅"""
    print("=" * 60)
    print("COMPETITION PDF CRAWLER")
    print("比赛通知PDF专用爬虫")
    print("=" * 60)


def crawl_and_extract_pdfs(url_manager: URLManager, 
                            timeout: int = 30) -> Dict:
    """
    爬取网页并提取PDF链接
    """
    urls = url_manager.urls
    if not urls:
        print("错误: 没有要爬取的URL")
        return {"results": [], "all_pdfs": []}
    
    print(f"\n[1/3] 爬取 {len(urls)} 个网页...")
    
    # 爬取网页
    fetcher = AsyncFetcher(
        concurrency=3,
        timeout=timeout,
        delay=1.5
    )
    
    results = fetcher.run(urls, show_progress=True)
    
    # 统计
    stats = fetcher.get_stats()
    print(f"\n爬取完成: {stats['success']}/{stats['total']} 成功")
    
    # 提取PDF链接
    print("\n[2/3] 提取PDF链接...")
    
    all_pdf_links = []
    page_results = []
    
    for result in results:
        if not result.get("success"):
            continue
        
        url = result.get("url")
        content = result.get("content", "")
        
        # 解析页面
        parser = ContentParser(content)
        title = parser.get_title()
        
        # 提取PDF链接（传递页面标题用于智能命名）
        pdf_handler = PDFHandler()
        detailed_pdfs = pdf_handler.extract_pdf_links(content, url, title)
        
        page_info = {
            "url": url,
            "title": title,
            "pdf_count": len(detailed_pdfs),
            "pdfs": detailed_pdfs
        }
        
        page_results.append(page_info)
        all_pdf_links.extend(detailed_pdfs)
        
        print(f"  [{len(detailed_pdfs)}个PDF] {title[:50]}...")
    
    print(f"\n共发现 {len(all_pdf_links)} 个PDF链接")
    
    # 筛选与比赛相关的PDF
    competition_pdfs = [pdf for pdf in all_pdf_links if pdf.get("is_competition_related", False)]
    print(f"其中与比赛/通知相关的PDF: {len(competition_pdfs)} 个")
    
    return {
        "page_results": page_results,
        "all_pdfs": all_pdf_links,
        "competition_pdfs": competition_pdfs,
        "stats": {
            "total_pages": len(results),
            "successful_pages": stats['success'],
            "total_pdfs": len(all_pdf_links),
            "competition_pdfs": len(competition_pdfs)
        }
    }


def download_pdfs(pdf_list: List[Dict], 
                  output_subdir: str = "competitions") -> List[Dict]:
    """
    下载PDF文件
    """
    if not pdf_list:
        print("没有需要下载的PDF")
        return []
    
    print(f"\n[3/3] 下载PDF文件 (共{len(pdf_list)}个)...")
    
    pdf_handler = PDFHandler()
    results = asyncio.run(pdf_handler.download_all_pdfs(
        pdf_list, 
        subdir=output_subdir,
        concurrency=3
    ))
    
    # 汇总
    summary = pdf_handler.get_pdf_summary(results)
    print(f"\n下载完成!")
    print(f"  新下载: {summary['downloaded']} 个")
    print(f"  已存在: {summary['exists']} 个")
    print(f"  失败: {summary['failed']} 个")
    print(f"  总大小: {summary['total_size_mb']} MB")
    
    return results


def save_results(data: Dict, output_dir: str = "./data"):
    """保存结果到文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存JSON结果
    json_path = os.path.join(output_dir, f"pdf_scan_{timestamp}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n扫描结果已保存: {json_path}")
    
    # 生成文本报告
    report_path = os.path.join(output_dir, f"pdf_report_{timestamp}.txt")
    generate_text_report(data, report_path)
    
    return json_path, report_path


def generate_text_report(data: Dict, filepath: str):
    """生成文本报告"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("比赛通知PDF扫描报告\n")
        f.write("=" * 60 + "\n\n")
        
        # 统计
        stats = data.get("stats", {})
        f.write(f"扫描网页数: {stats.get('total_pages', 0)}\n")
        f.write(f"成功爬取: {stats.get('successful_pages', 0)}\n")
        f.write(f"发现PDF总数: {stats.get('total_pdfs', 0)}\n")
        f.write(f"比赛相关PDF: {stats.get('competition_pdfs', 0)}\n\n")
        
        # 每个页面的PDF
        f.write("-" * 60 + "\n")
        f.write("详细PDF列表\n")
        f.write("-" * 60 + "\n\n")
        
        for page in data.get("page_results", []):
            f.write(f"\n网页: {page.get('title', 'Unknown')}\n")
            f.write(f"URL: {page.get('url')}\n")
            f.write(f"PDF数量: {page.get('pdf_count', 0)}\n\n")
            
            for i, pdf in enumerate(page.get("pdfs", []), 1):
                f.write(f"  {i}. {pdf.get('link_text', 'Unknown')}\n")
                f.write(f"     URL: {pdf.get('url')}\n")
                f.write(f"     文件名: {pdf.get('filename')}\n")
                if pdf.get('is_competition_related'):
                    f.write(f"     [比赛相关]\n")
                f.write(f"     上下文: {pdf.get('context', '')[:100]}...\n\n")
    
    print(f"文本报告已保存: {filepath}")


def main():
    """主函数"""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="比赛通知PDF专用爬虫",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 扫描并下载所有PDF
  python crawl_pdfs.py --urls urls.csv
  
  # 只扫描，不下载PDF
  python crawl_pdfs.py --urls urls.csv --scan-only
  
  # 只下载与比赛相关的PDF
  python crawl_pdfs.py --urls urls.csv --competition-only
  
  # 指定输出目录
  python crawl_pdfs.py --urls urls.csv --output ./my_pdfs
        """
    )
    
    parser.add_argument(
        "--urls", "-u",
        required=True,
        help="URL源文件路径 (CSV或Excel格式)"
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="只扫描，不下载PDF"
    )
    parser.add_argument(
        "--competition-only",
        action="store_true",
        help="只下载与比赛/通知相关的PDF"
    )
    parser.add_argument(
        "--output", "-o",
        default="./pdfs",
        help="PDF输出目录 (默认: ./pdfs)"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=30,
        help="请求超时时间(秒) (默认: 30)"
    )
    
    args = parser.parse_args()
    
    # 检查URL文件
    if not os.path.exists(args.urls):
        print(f"错误: 文件不存在: {args.urls}")
        return
    
    # 加载URL
    print(f"\n加载URL列表: {args.urls}")
    url_manager = URLManager()
    try:
        url_manager.load_from_file(args.urls)
    except Exception as e:
        print(f"加载URL失败: {str(e)}")
        return
    
    print(f"共加载 {len(url_manager.urls)} 个URL")
    
    # 爬取并提取PDF
    results = crawl_and_extract_pdfs(url_manager, timeout=args.timeout)
    
    if not results["all_pdfs"]:
        print("\n未找到任何PDF文件")
        # 仍然保存扫描结果
        save_results(results)
        return
    
    # 决定要下载哪些PDF
    if args.competition_only:
        pdfs_to_download = results["competition_pdfs"]
        print(f"\n将下载与比赛相关的 {len(pdfs_to_download)} 个PDF")
    else:
        pdfs_to_download = results["all_pdfs"]
        print(f"\n将下载所有 {len(pdfs_to_download)} 个PDF")
    
    # 下载PDF
    if not args.scan_only and pdfs_to_download:
        download_results = download_pdfs(pdfs_to_download, output_subdir=args.output)
        results["download_results"] = download_results
    elif args.scan_only:
        print("\n[扫描模式] 跳过下载")
    
    # 保存结果
    print("\n" + "=" * 60)
    print("保存扫描结果...")
    save_results(results)
    
    print("\n" + "=" * 60)
    print("任务完成!")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    main()
