#!/usr/bin/env python3
"""
增强型比赛通知爬虫 - V3多格式版
新增功能：
1. 支持多种文档格式（PDF, Word, Excel, PPT, 压缩包）
2. 自动删除无效网址（3次失败后自动删除）
3. 失败记录和统计
"""
import argparse
import sys
import os
import json
import asyncio
import csv
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.url_manager import URLManager
from core.fetcher import AsyncFetcher, get_random_headers
from core.parser import ContentParser
from core.document_handler import DocumentHandler
from report_generator import ReportGenerator
from word_generator import NoticeWordGenerator


class EnhancedCompetitionCrawlerV3:
    """增强型比赛通知爬虫 V3 - 多格式支持"""
    
    # 比赛相关关键词
    COMPETITION_KEYWORDS = [
        "大赛", "比赛", "竞赛", "征集", "评选", "征稿", "评职", "评奖", "评优", "评先",
        "微课", "公开课", "优质课", "精品课", "说课", "征文", "论文", "通知", "公告",
        "公示", "简章", "方案", "指南", "报名", "参赛", "作品", "提交", "评审", "获奖"
    ]
    
    def __init__(self, use_dynamic: bool = False, timeout: int = 30, 
                 use_proxy: bool = False, proxy_file: str = "proxies.json",
                 max_retries: int = 3, auto_remove_failed: bool = False,  # 默认禁用自动删除
                 urls_file: str = "urls.csv"):
        self.use_dynamic = use_dynamic
        self.timeout = timeout
        self.use_proxy = use_proxy
        self.proxy_file = proxy_file
        self.max_retries = max_retries
        self.auto_remove_failed = auto_remove_failed
        self.urls_file = urls_file
        
        self.results = []
        self.document_handler = DocumentHandler(timeout=timeout)
        
        # 失败记录 {url: fail_count}
        self.fail_records = {}
        
        # 加载失败记录
        self._load_fail_records()
        
    def _get_fail_record_file(self) -> str:
        """获取失败记录文件路径"""
        return self.urls_file.replace('.csv', '_fail_records.json')
    
    def _load_fail_records(self):
        """加载失败记录"""
        record_file = self._get_fail_record_file()
        if os.path.exists(record_file):
            try:
                with open(record_file, 'r', encoding='utf-8') as f:
                    self.fail_records = json.load(f)
                print(f"  [INFO] Loaded fail records: {len(self.fail_records)} URLs")
            except Exception as e:
                print(f"  [WARN] Failed to load fail records: {e}")
                self.fail_records = {}
    
    def _save_fail_records(self):
        """保存失败记录"""
        record_file = self._get_fail_record_file()
        try:
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(self.fail_records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  [WARN] Failed to save fail records: {e}")
    
    def _record_failure(self, url: str) -> bool:
        """
        记录失败，返回是否应该删除
        注意：只有 auto_remove_failed=True 时才会返回True
        """
        self.fail_records[url] = self.fail_records.get(url, 0) + 1
        fail_count = self.fail_records[url]
        
        # 如果禁用了自动删除，只记录但不标记删除
        if not self.auto_remove_failed:
            print(f"  [FAIL] URL failed {fail_count} times (auto-remove disabled): {url[:50]}...")
            self._save_fail_records()
            return False
        
        print(f"  [FAIL] URL failed {fail_count}/{self.max_retries} times: {url[:50]}...")
        
        # 保存记录
        self._save_fail_records()
        
        # 检查是否达到删除阈值
        if fail_count >= self.max_retries:
            print(f"  [REMOVE] URL reached max failures ({self.max_retries}), marking for removal")
            return True
        return False
    
    def _record_success(self, url: str):
        """记录成功，重置失败计数"""
        if url in self.fail_records:
            del self.fail_records[url]
            self._save_fail_records()
    
    def remove_failed_urls(self, urls_to_remove: List[str]):
        """从CSV中删除失败的网址"""
        if not urls_to_remove or not self.auto_remove_failed:
            return
        
        if not os.path.exists(self.urls_file):
            return
        
        print(f"\n[AUTO_REMOVE] Removing {len(urls_to_remove)} failed URLs from {self.urls_file}")
        
        # 备份原文件
        backup_file = self.urls_file + ".backup"
        try:
            import shutil
            shutil.copy2(self.urls_file, backup_file)
        except Exception as e:
            print(f"  [WARN] Failed to create backup: {e}")
        
        try:
            # 读取所有URL
            all_urls = []
            header = ['url', 'name', 'category']
            
            with open(self.urls_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                try:
                    first_row = next(reader, None)
                    if first_row and ('url' in first_row[0].lower() or 'http' not in first_row[0]):
                        header = first_row
                    else:
                        # 第一行是数据不是标题
                        if first_row:
                            all_urls.append(first_row)
                except StopIteration:
                    pass
                
                for row in reader:
                    if row and len(row) > 0 and row[0].strip():
                        all_urls.append(row)
            
            if not all_urls:
                print(f"  [WARN] No URLs found in file")
                return
            
            # 过滤掉失败的URL
            urls_to_remove_set = set(urls_to_remove)
            remaining_urls = []
            skipped_count = 0
            
            for row in all_urls:
                if len(row) > 0 and row[0].strip():
                    if row[0].strip() not in urls_to_remove_set:
                        remaining_urls.append(row)
                    else:
                        skipped_count += 1
            
            print(f"  [INFO] Original: {len(all_urls)}, Remove: {skipped_count}, Remaining: {len(remaining_urls)}")
            
            # 写回文件（使用临时文件避免数据丢失）
            temp_file = self.urls_file + ".tmp"
            with open(temp_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(remaining_urls)
            
            # 原子替换
            os.replace(temp_file, self.urls_file)
            
            # 删除备份
            if os.path.exists(backup_file):
                os.remove(backup_file)
            
            print(f"  [OK] Removed {skipped_count} URLs successfully")
            
            # 同时从失败记录中删除
            for url in urls_to_remove:
                if url in self.fail_records:
                    del self.fail_records[url]
            self._save_fail_records()
            
        except Exception as e:
            print(f"  [ERROR] Failed to remove URLs: {e}")
            import traceback
            traceback.print_exc()
            
            # 恢复备份
            if os.path.exists(backup_file):
                try:
                    shutil.copy2(backup_file, self.urls_file)
                    print(f"  [OK] Restored from backup")
                except Exception as restore_error:
                    print(f"  [CRITICAL] Failed to restore backup: {restore_error}")
    
    def is_competition_related(self, title: str, text: str = "") -> bool:
        """判断内容是否与比赛相关"""
        combined = f"{title} {text}".lower()
        return any(keyword in combined for keyword in self.COMPETITION_KEYWORDS)
    
    async def crawl_single(self, url_item: Dict) -> Optional[Dict]:
        """异步爬取单个URL"""
        url = url_item.get("url") if isinstance(url_item, dict) else url_item
        
        print(f"\n  [FETCH] {url[:70]}...")
        
        # 使用fetcher实例
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
                if self._record_failure(url):
                    return {"url": url, "removed": True, "error": "No response"}
                return None
            
            if not fetch_result.get("success"):
                error = fetch_result.get('error', 'Unknown error')
                print(f"  [FAIL] {error}")
                if self._record_failure(url):
                    return {"url": url, "removed": True, "error": error}
                return None
            
            # 解析内容
            html_content = fetch_result.get("content", "")
            parser = ContentParser(html_content)
            title = parser.get_title() or fetch_result.get("title", "Unknown")
            
            print(f"  [OK] Title: {title[:60]}...")
            
            # 记录成功
            self._record_success(url)
            
            # 提取比赛相关信息
            text_preview = parser.get_text()[:500]
            is_competition = self.is_competition_related(title, text_preview)
            
            if is_competition:
                print(f"  [INFO] Competition-related content detected")
            
            # 提取所有文档链接（多格式支持）
            documents = self.document_handler.extract_document_links(
                html_content, url, title
            )
            competition_docs = [d for d in documents if d.get("is_competition_related", False)]
            
            if documents:
                doc_types = {}
                for d in documents:
                    t = d.get('doc_type', 'Other')
                    doc_types[t] = doc_types.get(t, 0) + 1
                print(f"  [DOC] Found {len(documents)} documents: {doc_types}")
                if competition_docs:
                    print(f"  [DOC] Competition-related: {len(competition_docs)}")
            
            return {
                "url": url,
                "title": title,
                "content": html_content,
                "text": parser.get_main_content(),
                "is_competition_related": is_competition,
                "all_documents": documents,
                "competition_documents": competition_docs,
                "success": True,
                "crawled_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")
            if self._record_failure(url):
                return {"url": url, "removed": True, "error": str(e)}
            return None
    
    async def crawl_all_async(self, urls: List[Dict]) -> List[Dict]:
        """批量爬取（纯异步）"""
        total = len(urls)
        print(f"\n[PROGRESS] Starting to crawl {total} URLs...")
        print(f"[INFO] Auto-remove failed URLs: {self.auto_remove_failed} (max {self.max_retries} retries)")
        
        results = []
        urls_to_remove = []
        semaphore = asyncio.Semaphore(3)
        
        async def crawl_with_limit(url_item, index):
            async with semaphore:
                url = url_item.get("url") if isinstance(url_item, dict) else url_item
                progress = index + 1
                
                try:
                    result = await self.crawl_single(url_item)
                    
                    if result:
                        if result.get("removed"):
                            urls_to_remove.append(url)
                            print(f"  [PROGRESS] Marked for removal: {progress}/{total} ({progress/total*100:.1f}%)")
                        else:
                            print(f"  [PROGRESS] Completed: {progress}/{total} ({progress/total*100:.1f}%)")
                    else:
                        print(f"  [PROGRESS] Failed: {progress}/{total} ({progress/total*100:.1f}%)")
                    
                    return result
                except Exception as e:
                    print(f"  [ERROR] Exception crawling {url[:50]}...: {type(e).__name__}: {e}")
                    # 记录失败
                    if self._record_failure(url):
                        urls_to_remove.append(url)
                        print(f"  [PROGRESS] Exception - Marked for removal: {progress}/{total}")
                    else:
                        print(f"  [PROGRESS] Exception - Failed: {progress}/{total}")
                    return None
        
        # 创建所有任务
        tasks = [crawl_with_limit(url, i) for i, url in enumerate(urls)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤结果
        valid_results = []
        for r in results:
            if isinstance(r, Exception):
                print(f"  [ERROR] Task failed: {r}")
            elif r is not None:
                valid_results.append(r)
        
        print(f"\n[PROGRESS] Crawl completed: {len(valid_results)}/{total} succeeded")
        
        # 自动删除失败的URL
        if urls_to_remove:
            self.remove_failed_urls(urls_to_remove)
        
        self.results = valid_results
        return valid_results
    
    def crawl_all(self, urls: List[Dict]) -> List[Dict]:
        """批量爬取（同步入口）"""
        try:
            # 检查是否已有事件循环
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
            except RuntimeError:
                pass
            
            return asyncio.run(self.crawl_all_async(urls))
        except RuntimeError as e:
            print(f"  [WARNING] Event loop issue: {e}")
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                print("  [ERROR] nest_asyncio not installed. Run: pip install nest-asyncio")
                raise
            return asyncio.run(self.crawl_all_async(urls))
    
    async def download_documents_async(self, documents: List[Dict], output_dir: str) -> List[Dict]:
        """异步下载文档"""
        handler = DocumentHandler(timeout=self.timeout, output_dir=output_dir)
        return await handler.download_documents(documents)
    
    def download_documents(self, documents: List[Dict], output_dir: str) -> List[Dict]:
        """同步下载文档"""
        try:
            # 检查是否已有事件循环
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
            except RuntimeError:
                pass
            
            return asyncio.run(self.download_documents_async(documents, output_dir))
        except RuntimeError as e:
            print(f"  [WARNING] Event loop issue in download: {e}")
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                print("  [ERROR] nest_asyncio not installed")
                raise
            return asyncio.run(self.download_documents_async(documents, output_dir))
    
    def generate_html_report(self) -> str:
        """生成HTML报告"""
        generator = ReportGenerator()
        report_path = generator.generate(self.results)
        return report_path
    
    def generate_word_report(self, output_dir: str = "./word_reports") -> str:
        """生成Word报告"""
        os.makedirs(output_dir, exist_ok=True)
        
        competition_results = [r for r in self.results if r.get("is_competition_related")]
        
        if not competition_results:
            print("  [WARN] No competition results for Word report")
            return None
        
        generator = NoticeWordGenerator(output_dir=output_dir)
        filepath = generator.generate(competition_results)
        
        if filepath:
            print(f"  [OK] Word report: {filepath}")
        
        return filepath
    
    def save_json_data(self, output_dir: str = "./output/data") -> str:
        """保存JSON数据"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(output_dir, f"crawl_result_{timestamp}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"  [OK] JSON data: {filepath}")
        return filepath


def main():
    """主函数"""
    print("=" * 70)
    print("              ENHANCED COMPETITION NOTIFICATION CRAWLER")
    print("                         V3 多格式文档版")
    print("=" * 70)
    print("\n支持格式: PDF, Word(doc/docx), Excel(xls/xlsx), PPT(ppt/pptx), 压缩包")
    print("自动删除: 3次失败后自动从urls.csv移除无效网址")
    print("=" * 70)
    
    parser = argparse.ArgumentParser(
        description="Enhanced crawler with multi-format document support",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--urls", "-u", required=True, help="URL source file (CSV)")
    parser.add_argument("--mode", "-m", choices=["all", "doc", "html"], default="all",
                       help="Crawl mode: all=documents+report, doc=documents only, html=report only")
    parser.add_argument("--dynamic", "-d", action="store_true", help="Use dynamic rendering")
    parser.add_argument("--timeout", "-t", type=int, default=30, help="Request timeout")
    parser.add_argument("--output", "-o", default="./output", help="Output directory")
    parser.add_argument("--proxy", "-p", action="store_true", help="Use proxy")
    parser.add_argument("--proxy-file", default="proxies.json", help="Proxy file")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retries before removal")
    parser.add_argument("--no-auto-remove", action="store_true", 
                       help="Disable auto-removal of failed URLs")
    
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
    crawler = EnhancedCompetitionCrawlerV3(
        use_dynamic=args.dynamic,
        timeout=args.timeout,
        use_proxy=args.proxy,
        proxy_file=args.proxy_file,
        max_retries=args.max_retries,
        auto_remove_failed=not args.no_auto_remove,
        urls_file=args.urls
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
    all_docs = []
    competition_docs = []
    for r in results:
        all_docs.extend(r.get("all_documents", []))
        competition_docs.extend(r.get("competition_documents", []))
    
    # 按类型统计文档
    doc_types = {}
    for d in all_docs:
        t = d.get('doc_type', 'Other')
        doc_types[t] = doc_types.get(t, 0) + 1
    
    print(f"\n  [STATS]")
    print(f"    Competition-related pages: {len(competition_pages)}")
    print(f"    Total documents found: {len(all_docs)}")
    print(f"    By type: {doc_types}")
    print(f"    Competition-related documents: {len(competition_docs)}")
    
    # 根据模式执行不同操作
    doc_results = []
    if args.mode in ["all", "doc"] and competition_docs:
        print(f"\n[3/4] Downloading documents...")
        doc_output = os.path.join(args.output, "documents")
        try:
            doc_results = crawler.download_documents(competition_docs, output_dir=doc_output)
            print(f"  [OK] Downloaded {len([d for d in doc_results if d.get('downloaded')])} documents")
        except Exception as e:
            print(f"  [ERROR] Document download failed: {e}")
            import traceback
            traceback.print_exc()
    
    if args.mode in ["all", "html"]:
        print(f"\n[3/4] Generating HTML report...")
        try:
            report_path = crawler.generate_html_report()
        except Exception as e:
            print(f"  [ERROR] HTML report generation failed: {e}")
            report_path = None
    
    # 生成Word文档
    print(f"\n[3.5/4] Generating Word document...")
    try:
        word_path = crawler.generate_word_report(output_dir=os.path.join(args.output, "word_reports"))
    except Exception as e:
        print(f"  [ERROR] Word report generation failed: {e}")
        word_path = None
    
    # 保存JSON数据
    print(f"\n[4/4] Saving data...")
    json_path = crawler.save_json_data(output_dir=os.path.join(args.output, "data"))
    
    # 完成
    print("\n" + "=" * 70)
    print("                         CRAWL COMPLETED!")
    print("=" * 70)
    print(f"\nOutput files:")
    if args.mode in ["all", "doc"]:
        print(f"  - Documents: {args.output}/documents/")
    if args.mode in ["all", "html"]:
        print(f"  - HTML Report: {report_path if 'report_path' in locals() else 'N/A'}")
    print(f"  - Word Report: {word_path if word_path else 'N/A'}")
    print(f"  - JSON Data: {json_path if 'json_path' in locals() else 'N/A'}")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
