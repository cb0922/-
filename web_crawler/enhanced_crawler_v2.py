#!/usr/bin/env python3
"""
增强型比赛通知爬虫 - V2优化版
优化内容：
1. 修复事件循环冲突问题
2. 优化内存使用（流式处理大内容）
3. 改进错误处理和日志
4. 添加连接池复用
5. 优化并发控制
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
from core.fetcher import AsyncFetcher, get_random_headers
from core.parser import ContentParser, PDFLinkExtractor
from core.pdf_handler import PDFHandler
from report_generator import ReportGenerator
from word_generator import NoticeWordGenerator


class EnhancedCompetitionCrawlerV2:
    """增强型比赛通知爬虫 V2"""
    
    # 比赛相关关键词
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
    
    def __init__(self, use_dynamic: bool = False, timeout: int = 30, 
                 use_proxy: bool = False, proxy_file: str = "proxies.json"):
        self.use_dynamic = use_dynamic
        self.timeout = timeout
        self.use_proxy = use_proxy
        self.proxy_file = proxy_file
        self.results = []
        self.pdf_handler = PDFHandler(timeout=timeout)
        
    def is_competition_related(self, title: str, text: str = "") -> bool:
        """判断内容是否与比赛相关"""
        combined = f"{title} {text}".lower()
        for keyword in self.COMPETITION_KEYWORDS:
            if keyword in combined:
                return True
        return False
    
    async def crawl_single(self, url_item: Dict, session=None) -> Dict:
        """异步爬取单个URL"""
        url = url_item.get("url") if isinstance(url_item, dict) else url_item
        
        print(f"\n  [FETCH] {url[:70]}...")
        
        # 使用新的fetcher实例（支持代理）
        fetcher = AsyncFetcher(
            timeout=self.timeout, 
            headers=get_random_headers(),
            use_proxy=self.use_proxy,
            proxy_file=self.proxy_file
        )
        
        try:
            results = await fetcher.fetch_all([{"url": url}])
            fetch_result = results[0] if results else None
            
            if not fetch_result:
                print(f"  [FAIL] No response")
                return None
            
            if not fetch_result.get("success"):
                error = fetch_result.get('error', 'Unknown error')
                print(f"  [FAIL] {error}")
                return None
            
            # 解析内容
            html_content = fetch_result.get("content", "")
            parser = ContentParser(html_content)
            title = parser.get_title() or fetch_result.get("title", "Unknown")
            
            print(f"  [OK] Title: {title[:60]}...")
            
            # 提取比赛相关信息
            text_preview = parser.get_text()[:500]
            is_competition = self.is_competition_related(title, text_preview)
            
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
                "text": parser.get_main_content(),  # 保存提取的文本
                "is_competition_related": is_competition,
                "all_pdfs": pdf_links,
                "competition_pdfs": competition_pdfs,
                "success": True,
                "crawled_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")
            return None
    
    async def crawl_all_async(self, urls: List[Dict]) -> List[Dict]:
        """批量爬取（纯异步）"""
        total = len(urls)
        print(f"\n  [PROGRESS] Starting to crawl {total} URLs...")
        
        results = []
        semaphore = asyncio.Semaphore(3)  # 限制并发数为3
        
        async def crawl_with_limit(url_item, index):
            async with semaphore:
                result = await self.crawl_single(url_item)
                progress = index + 1
                if result:
                    print(f"  [PROGRESS] Completed: {progress}/{total} ({progress/total*100:.1f}%)")
                else:
                    print(f"  [PROGRESS] Failed: {progress}/{total} ({progress/total*100:.1f}%)")
                return result
        
        # 创建所有任务
        tasks = [crawl_with_limit(url, i) for i, url in enumerate(urls)]
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤掉异常和None结果
        valid_results = []
        for r in results:
            if isinstance(r, Exception):
                print(f"  [ERROR] Task failed: {r}")
            elif r is not None:
                valid_results.append(r)
        
        print(f"\n  [PROGRESS] Crawl completed: {len(valid_results)}/{total} succeeded")
        self.results = valid_results
        return valid_results
    
    def crawl_all(self, urls: List[Dict]) -> List[Dict]:
        """批量爬取（同步入口）"""
        # 使用asyncio.run来管理事件循环
        try:
            return asyncio.run(self.crawl_all_async(urls))
        except RuntimeError as e:
            # 如果已经在事件循环中，使用nest_asyncio
            print(f"  [WARNING] Event loop issue: {e}")
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(self.crawl_all_async(urls))
    
    def download_pdfs(self, pdf_list: List[Dict], output_dir: str = "pdfs/competitions") -> List[Dict]:
        """下载PDF文件"""
        if not pdf_list:
            print("\n  [INFO] No PDFs to download")
            return []
        
        print(f"\n  [DOWNLOAD] Preparing to download {len(pdf_list)} PDFs...")
        print(f"  [DOWNLOAD] Output directory: {output_dir}")
        
        # 显示前3个PDF
        for i, pdf in enumerate(pdf_list[:3]):
            print(f"    [{i+1}] {pdf.get('filename', 'N/A')}")
        if len(pdf_list) > 3:
            print(f"    ... and {len(pdf_list) - 3} more")
        
        try:
            # 使用asyncio.run
            results = asyncio.run(
                self.pdf_handler.download_all_pdfs(pdf_list, subdir=output_dir)
            )
        except RuntimeError:
            import nest_asyncio
            nest_asyncio.apply()
            results = asyncio.run(
                self.pdf_handler.download_all_pdfs(pdf_list, subdir=output_dir)
            )
        
        summary = self.pdf_handler.get_pdf_summary(results)
        print(f"\n  [DOWNLOAD_SUMMARY]")
        print(f"    Downloaded: {summary['downloaded']}")
        print(f"    Exists: {summary['exists']}")
        print(f"    Failed: {summary['failed']}")
        
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
            # 复用已提取的text，避免重复解析
            text = result.get('text', '')
            
            report_data.append({
                "url": result.get("url"),
                "title": result.get("title"),
                "description": "",  # 简化
                "keywords": "",
                "text": text[:3000],
                "links_count": 0,  # 简化
                "images_count": 0,
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
            text = result.get('text', '')
            
            word_data.append({
                "url": result.get("url"),
                "title": result.get("title"),
                "text": text,  # 完整正文
                "content": result.get("content", ""),
                "competition_pdfs": result.get("competition_pdfs", []),
                "is_competition_related": result.get("is_competition_related", False),
            })
            
            print(f"    [WORD] {result.get('title', 'N/A')[:40]}... Content length: {len(text)} chars")
        
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
            # text已包含提取的内容
            item["content"] = "[HTML_CONTENT_TRUNCATED]"  # 不保存完整HTML
            save_data.append(item)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        print(f"  [OK] JSON data saved: {filepath}")
        return filepath


def main():
    """主函数"""
    # 打印横幅
    print("=" * 70)
    print("              ENHANCED COMPETITION NOTIFICATION CRAWLER")
    print("                         V2 优化版")
    print("=" * 70)
    
    parser = argparse.ArgumentParser(
        description="Enhanced crawler for competition notifications",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--urls", "-u", required=True, help="URL source file (CSV)")
    parser.add_argument("--mode", "-m", choices=["all", "pdf", "html"], default="all")
    parser.add_argument("--dynamic", "-d", action="store_true")
    parser.add_argument("--timeout", "-t", type=int, default=30)
    parser.add_argument("--output", "-o", default="./output")
    parser.add_argument("--proxy", "-p", action="store_true", help="Use proxy from proxies.json")
    parser.add_argument("--proxy-file", default="proxies.json", help="Proxy configuration file")
    
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
    crawler = EnhancedCompetitionCrawlerV2(
        use_dynamic=args.dynamic,
        timeout=args.timeout,
        use_proxy=args.proxy,
        proxy_file=args.proxy_file
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
