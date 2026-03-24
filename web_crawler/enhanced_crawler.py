#!/usr/bin/env python3
"""
增强型比赛通知爬虫
功能：
1. 抓取PDF格式的比赛通知/公告并下载
2. 抓取网页形式的比赛通知/公告并生成可视化HTML报告
3. 支持JavaScript动态加载的内容（使用Playwright/Selenium）

使用方法:
    python enhanced_crawler.py --urls urls.csv --mode all
    python enhanced_crawler.py --urls urls.csv --mode pdf
    python enhanced_crawler.py --urls urls.csv --mode html --dynamic
"""
import argparse
import sys
import os
import json
import asyncio
import re
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.url_manager import URLManager
from core.fetcher import AsyncFetcher
from core.parser import ContentParser, PDFLinkExtractor
from core.pdf_handler import PDFHandler
from report_generator import ReportGenerator
from word_generator import NoticeWordGenerator


class EnhancedCompetitionCrawler:
    """增强型比赛通知爬虫"""
    
    # 比赛相关关键词（扩展教育类关键词）
    COMPETITION_KEYWORDS = [
        # 核心赛事
        "大赛", "比赛", "竞赛",
        # 评选评优
        "征集", "评选", "征稿", "评职", "评奖", "评优", "评先",
        # 教学活动
        "微课", "公开课", "优质课", "精品课", "说课",
        # 学术成果
        "征文", "论文",
        # 通知公告
        "通知", "公告", "公示", "简章", "方案", "指南",
        # 参与相关
        "报名", "参赛", "作品", "提交", "评审", "获奖"
    ]
    
    def __init__(self, use_dynamic: bool = False, timeout: int = 30):
        self.use_dynamic = use_dynamic
        self.timeout = timeout
        self.results = []
        self.pdf_handler = PDFHandler(timeout=timeout)
        
    def is_competition_related(self, title: str, text: str = "") -> bool:
        """判断内容是否与比赛相关"""
        combined = f"{title} {text}".lower()
        for keyword in self.COMPETITION_KEYWORDS:
            if keyword in combined:
                return True
        return False
    
    async def crawl_static(self, url: str) -> Dict:
        """静态页面爬取"""
        fetcher = AsyncFetcher(timeout=self.timeout)
        
        result = fetcher.run([{"url": url}], show_progress=False)
        if result and result[0].get("success"):
            return result[0]
        return None
    
    async def crawl_dynamic(self, url: str) -> Dict:
        """动态页面爬取（使用Playwright）"""
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # 设置超时
                page.set_default_timeout(self.timeout * 1000)
                
                # 访问页面
                await page.goto(url, wait_until="networkidle")
                
                # 等待内容加载
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)  # 额外等待JS执行
                
                # 获取内容
                content = await page.content()
                title = await page.title()
                
                await browser.close()
                
                return {
                    "url": url,
                    "success": True,
                    "content": content,
                    "title": title,
                    "status": 200,
                    "is_dynamic": True
                }
        except ImportError:
            print("  [Warning] Playwright not installed, falling back to static crawl")
            return await self.crawl_static(url)
        except Exception as e:
            print(f"  [Error] Dynamic crawl failed: {e}")
            return None
    
    def crawl_single_sync(self, url_item: Dict) -> Dict:
        """同步方式爬取单个URL"""
        url = url_item.get("url") if isinstance(url_item, dict) else url_item
        return self._crawl_with_new_loop(url)
    
    def _crawl_with_new_loop(self, url: str) -> Dict:
        """使用新的事件循环进行爬取，带重试机制"""
        from concurrent.futures import ThreadPoolExecutor
        
        # 不同的请求头配置（用于重试）
        header_configs = [
            # 配置1: 完整请求头
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            },
            # 配置2: Mac Safari
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
            },
            # 配置3: 简单请求头
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            },
        ]
        
        fetch_result = None
        
        for attempt, headers in enumerate(header_configs, 1):
            try:
                def run_async():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    fetcher = AsyncFetcher(timeout=self.timeout, headers=headers)
                    result = fetcher.run([{"url": url}], show_progress=False)
                    loop.close()
                    return result[0] if result else None
                
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async)
                    fetch_result = future.result(timeout=self.timeout + 5)
                
                if fetch_result and fetch_result.get("success"):
                    break  # 成功，跳出重试循环
                    
            except Exception as e:
                print(f"  [RETRY {attempt}] Failed with error: {e}")
                continue
        
        if not fetch_result:
            print("  [FAIL] Failed to fetch page")
            return None
        
        if not fetch_result.get("success"):
            print(f"  [FAIL] HTTP {fetch_result.get('status', 'unknown')}")
            return None
        
        # 解析内容
        html_content = fetch_result.get("content", "")
        parser = ContentParser(html_content)
        title = parser.get_title() or fetch_result.get("title", "Unknown")
        
        print(f"  [OK] Title: {title[:60]}...")
        
        # 提取比赛相关信息
        is_competition = self.is_competition_related(title, parser.get_text()[:500])
        
        if is_competition:
            print(f"  [INFO] Competition-related content detected")
        
        # 提取PDF链接
        pdf_links = self.pdf_handler.extract_pdf_links(html_content, url, title)
        competition_pdfs = [pdf for pdf in pdf_links if pdf.get("is_competition_related", False)]
        
        if pdf_links:
            print(f"  [PDF] Found {len(pdf_links)} PDFs ({len(competition_pdfs)} competition-related)")
        
        return {
            "url": url,
            "title": title,
            "content": html_content,
            "is_competition_related": is_competition,
            "all_pdfs": pdf_links,
            "competition_pdfs": competition_pdfs,
            "success": True,
            "crawled_at": datetime.now().isoformat()
        }
    
    def crawl_all(self, urls: List[Dict]) -> List[Dict]:
        """批量爬取（同步方式）"""
        results = []
        total = len(urls)
        
        print(f"\n  [PROGRESS] Starting to crawl {total} URLs...")
        
        for i, url in enumerate(urls, 1):
            url_str = url.get('url', url) if isinstance(url, dict) else url
            print(f"\n  [{i}/{total}] Crawling: {url_str[:60]}...")
            
            try:
                result = self.crawl_single_sync(url)
                if result:
                    results.append(result)
                    print(f"  [PROGRESS] Completed: {i}/{total} ({i/total*100:.1f}%)")
                else:
                    print(f"  [PROGRESS] Failed: {i}/{total} ({i/total*100:.1f}%)")
            except Exception as e:
                print(f"  [Error] {e}")
                print(f"  [PROGRESS] Error: {i}/{total} ({i/total*100:.1f}%)")
        
        print(f"\n  [PROGRESS] Crawl completed: {len(results)}/{total} succeeded")
        self.results = results
        return results
    
    def download_pdfs(self, pdf_list: List[Dict], output_dir: str = "pdfs/competitions") -> List[Dict]:
        """下载PDF文件"""
        if not pdf_list:
            print("\n  [INFO] No PDFs to download")
            return []
        
        print(f"\n  [DOWNLOAD] 准备下载 {len(pdf_list)} 个PDF文件")
        print(f"  [DOWNLOAD] 输出目录: {output_dir}")
        
        # 打印前3个PDF的信息用于调试
        for i, pdf in enumerate(pdf_list[:3]):
            print(f"    [{i+1}] {pdf.get('filename', 'N/A')} - {pdf.get('url', 'N/A')[:50]}...")
        if len(pdf_list) > 3:
            print(f"    ... 还有 {len(pdf_list) - 3} 个PDF")
        
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                self.pdf_handler.download_all_pdfs(pdf_list, subdir=output_dir)
            )
        except Exception as e:
            print(f"  [ERROR] 下载过程异常: {e}")
            import traceback
            traceback.print_exc()
            results = []
        finally:
            loop.close()
        
        summary = self.pdf_handler.get_pdf_summary(results)
        print(f"\n  [DOWNLOAD_SUMMARY]")
        print(f"    成功下载: {summary['downloaded']}")
        print(f"    已存在: {summary['exists']}")
        print(f"    失败: {summary['failed']}")
        print(f"    总大小: {summary.get('total_size', 0) / 1024 / 1024:.2f} MB")
        
        return results
    
    def generate_html_report(self, output_name: str = None) -> str:
        """生成可视化HTML报告"""
        if not self.results:
            print("\n  [WARNING] No data to generate report")
            return None
        
        print("\n  [REPORT] Generating HTML visualization report...")
        
        # 转换为ReportGenerator需要的格式
        report_data = []
        for result in self.results:
            parser = ContentParser(result.get("content", ""))
            
            report_data.append({
                "url": result.get("url"),
                "title": result.get("title"),
                "description": parser.get_meta("description"),
                "keywords": parser.get_meta("keywords"),
                "text": parser.get_main_content()[:3000],
                "links_count": len(parser.get_links()),
                "images_count": len(parser.get_images()),
                "status": 200 if result.get("success") else 0,
                "is_competition": result.get("is_competition_related", False),
                "pdfs_found": len(result.get("competition_pdfs", []))
            })
        
        # 生成报告
        generator = ReportGenerator(report_data, title="比赛通知综合抓取报告")
        report_path = generator.generate()
        
        print(f"  [OK] Report saved: {report_path}")
        return report_path
    
    def generate_word_report(self, output_dir: str = "./word_reports") -> str:
        """生成Word文档报告（包含完整正文）"""
        if not self.results:
            print("\n  [WARNING] No data to generate Word report")
            return None
        
        print("\n  [WORD] Generating Word document with full content...")
        
        # 准备数据（保留完整内容）
        word_data = []
        for result in self.results:
            # 提取完整正文内容
            content = result.get("content", "")
            if content and content != "[HTML_CONTENT_TRUNCATED]":
                parser = ContentParser(content)
                full_text = parser.get_main_content()
            else:
                full_text = result.get("text", "")
            
            word_data.append({
                "url": result.get("url"),
                "title": result.get("title"),
                "text": full_text,  # 完整正文
                "content": content,
                "competition_pdfs": result.get("competition_pdfs", []),
                "is_competition_related": result.get("is_competition_related", False),
            })
            
            print(f"    [WORD] {result.get('title', 'N/A')[:40]}... 内容长度: {len(full_text)} 字符")
        
        # 生成Word文档
        generator = NoticeWordGenerator(output_dir)
        word_path = generator.generate(word_data, title="通知公告汇总报告")
        
        print(f"  [OK] Word document saved: {word_path}")
        return word_path
    
    def save_json_data(self, output_dir: str = "./data") -> str:
        """保存JSON格式的详细数据"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(output_dir, f"enhanced_crawl_{timestamp}.json")
        
        # 准备数据（移除HTML内容以减小文件大小，但保留提取的文本）
        save_data = []
        for result in self.results:
            item = result.copy()
            
            # 提取正文内容（在截断HTML之前）
            from core.parser import ContentParser
            parser = ContentParser(result.get("content", ""))
            item["text"] = parser.get_main_content()[:5000]  # 保留提取的正文
            
            item["content"] = "[HTML_CONTENT_TRUNCATED]"  # 不保存完整HTML
            save_data.append(item)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        print(f"  [OK] JSON data saved: {filepath}")
        return filepath


def print_banner():
    """打印横幅"""
    print("=" * 70)
    print("              ENHANCED COMPETITION NOTIFICATION CRAWLER")
    print("                    增强型比赛通知综合爬虫")
    print("=" * 70)
    print("  Features:")
    print("    - PDF notification download")
    print("    - Webpage notification extraction with HTML visualization")
    print("    - JavaScript dynamic content support (Playwright)")
    print("=" * 70)


def main():
    """主函数"""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="Enhanced crawler for competition notifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage Examples:
  # Crawl both PDF and webpage content (default)
  python enhanced_crawler.py --urls urls.csv
  
  # Crawl only PDF files
  python enhanced_crawler.py --urls urls.csv --mode pdf
  
  # Crawl only webpage content with HTML report
  python enhanced_crawler.py --urls urls.csv --mode html
  
  # Use dynamic rendering for JavaScript-heavy sites
  python enhanced_crawler.py --urls urls.csv --dynamic
  
  # Full features: dynamic rendering + all content types
  python enhanced_crawler.py --urls urls.csv --mode all --dynamic
        """
    )
    
    parser.add_argument(
        "--urls", "-u",
        required=True,
        help="URL source file (CSV or Excel)"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["all", "pdf", "html"],
        default="all",
        help="Crawl mode: all (default), pdf only, or html only"
    )
    parser.add_argument(
        "--dynamic", "-d",
        action="store_true",
        help="Enable dynamic rendering for JavaScript-heavy websites"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--output", "-o",
        default="./output",
        help="Output directory (default: ./output)"
    )
    
    args = parser.parse_args()
    
    # 检查URL文件
    if not os.path.exists(args.urls):
        print(f"\n  [ERROR] File not found: {args.urls}")
        return
    
    # 加载URL
    print(f"\n[1/4] Loading URL list from: {args.urls}")
    url_manager = URLManager()
    try:
        url_manager.load_from_file(args.urls)
    except Exception as e:
        print(f"  [ERROR] Failed to load URLs: {e}")
        return
    
    urls = url_manager.urls
    print(f"  [OK] Loaded {len(urls)} URLs")
    
    # 创建爬虫
    crawler = EnhancedCompetitionCrawler(
        use_dynamic=args.dynamic,
        timeout=args.timeout
    )
    
    # 开始爬取
    print(f"\n[2/4] Starting crawl (mode: {args.mode}, dynamic: {args.dynamic})...")
    results = crawler.crawl_all(urls)
    
    if not results:
        print("\n  [ERROR] No pages successfully crawled")
        return
    
    print(f"\n  [OK] Successfully crawled {len(results)} pages")
    
    # 统计
    competition_pages = [r for r in results if r.get("is_competition_related")]
    all_pdfs = []
    competition_pdfs = []
    for r in results:
        all_pdfs.extend(r.get("all_pdfs", []))
        competition_pdfs.extend(r.get("competition_pdfs", []))
    
    print(f"\n  [STATS]")
    print(f"    Competition-related pages: {len(competition_pages)}")
    print(f"    Total PDFs found: {len(all_pdfs)}")
    print(f"    Competition-related PDFs: {len(competition_pdfs)}")
    
    # 根据模式执行不同操作
    if args.mode in ["all", "pdf"] and competition_pdfs:
        print(f"\n[3/4] Processing PDF downloads...")
        pdf_results = crawler.download_pdfs(competition_pdfs, output_dir=f"{args.output}/pdfs")
    
    if args.mode in ["all", "html"]:
        print(f"\n[3/4] Generating HTML visualization report...")
        report_path = crawler.generate_html_report()
        
        if report_path:
            # 尝试打开浏览器
            try:
                import webbrowser
                webbrowser.open(f'file://{os.path.abspath(report_path)}')
                print(f"  [OK] Opened report in browser")
            except:
                pass
    
    # 生成Word文档
    print(f"\n[3.5/4] Generating Word document...")
    word_path = crawler.generate_word_report(output_dir=f"{args.output}/word_reports")
    
    # 保存JSON数据
    print(f"\n[4/4] Saving data...")
    json_path = crawler.save_json_data(output_dir=f"{args.output}/data")
    
    # 完成
    print("\n" + "=" * 70)
    print("                         CRAWL COMPLETED!")
    print("=" * 70)
    print(f"\nOutput files:")
    if args.mode in ["all", "pdf"]:
        print(f"  - PDF files: {args.output}/pdfs/")
    if args.mode in ["all", "html"]:
        print(f"  - HTML Report: {report_path if 'report_path' in locals() else 'N/A'}")
    print(f"  - Word Report: {word_path if word_path else 'N/A'}")
    print(f"  - JSON Data: {json_path if 'json_path' in locals() else 'N/A'}")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
