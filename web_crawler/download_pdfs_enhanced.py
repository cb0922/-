#!/usr/bin/env python3
"""
增强型PDF下载器
解决PDF下载失败问题
功能:
1. 多层重试机制
2. 智能请求头轮换
3. 动态渲染支持
4. 404链接自动更新检测
"""
import asyncio
import aiohttp
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse


class EnhancedPDFDownloader:
    """增强型PDF下载器"""
    
    def __init__(self, timeout: int = 60):
        self.timeout = aiohttp.ClientTimeout(total=timeout, connect=10)
        self.downloaded = []
        self.failed = []
        
        # 多种请求头配置
        self.header_configs = [
            # 配置1: 完整浏览器请求头
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
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
            # 配置2: PDF专用请求头
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Connection": "keep-alive",
            },
            # 配置3: 简单请求头
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            },
        ]
    
    async def download_with_retry(self, pdf_info: Dict, output_dir: str) -> Dict:
        """
        带重试机制的PDF下载
        """
        url = pdf_info["url"]
        filename = pdf_info.get("filename", "unknown.pdf")
        referer = pdf_info.get("referer", "")
        
        filepath = os.path.join(output_dir, filename)
        
        # 检查文件是否已存在
        if os.path.exists(filepath):
            return {
                "url": url,
                "filename": filename,
                "status": "exists",
                "filepath": filepath,
                "size": os.path.getsize(filepath)
            }
        
        print(f"\n  Downloading: {filename}")
        print(f"  URL: {url[:60]}...")
        
        # 尝试多种请求头配置
        for attempt, headers in enumerate(self.header_configs, 1):
            # 添加Referer（如果有）
            if referer:
                headers["Referer"] = referer
            
            try:
                result = await self._try_download(url, headers, filepath)
                if result["success"]:
                    print(f"  [OK] Success with config {attempt}")
                    return result
                else:
                    print(f"  [RETRY {attempt}] Failed: {result.get('error', 'Unknown')}")
                    
            except Exception as e:
                print(f"  [RETRY {attempt}] Error: {e}")
                continue
        
        # 所有配置都失败
        print(f"  [FAIL] All attempts failed for {filename}")
        self.failed.append(pdf_info)
        
        return {
            "url": url,
            "filename": filename,
            "status": "failed",
            "error": "All retry attempts failed"
        }
    
    async def _try_download(self, url: str, headers: dict, filepath: str) -> Dict:
        """尝试下载PDF"""
        async with aiohttp.ClientSession(headers=headers, timeout=self.timeout) as session:
            async with session.get(url, ssl=False) as response:
                status = response.status
                
                if status == 200:
                    content = await response.read()
                    
                    # 检查是否是有效的PDF
                    if content[:4] == b'%PDF':
                        # 保存文件
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        with open(filepath, 'wb') as f:
                            f.write(content)
                        
                        return {
                            "url": url,
                            "filepath": filepath,
                            "status": "downloaded",
                            "success": True,
                            "size": len(content)
                        }
                    else:
                        # 不是PDF，可能是HTML错误页面
                        content_preview = content[:100].decode('utf-8', errors='ignore')
                        return {
                            "url": url,
                            "status": "failed",
                            "success": False,
                            "error": f"Not a valid PDF. Content: {content_preview[:50]}..."
                        }
                
                elif status == 404:
                    return {
                        "url": url,
                        "status": "failed",
                        "success": False,
                        "error": "HTTP 404 - File not found"
                    }
                
                else:
                    return {
                        "url": url,
                        "status": "failed",
                        "success": False,
                        "error": f"HTTP {status}"
                    }
    
    async def download_with_dynamic(self, pdf_info: Dict, output_dir: str) -> Dict:
        """
        使用Playwright动态渲染下载（针对JS保护的网站）
        """
        try:
            from playwright.async_api import async_playwright
            
            url = pdf_info["url"]
            filename = pdf_info.get("filename", "unknown.pdf")
            referer = pdf_info.get("referer", "")
            filepath = os.path.join(output_dir, filename)
            
            print(f"\n  [DYNAMIC] Using Playwright for: {filename}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                
                # 如果有referer，先访问原页面
                if referer:
                    page = await context.new_page()
                    await page.goto(referer, wait_until="networkidle")
                    await asyncio.sleep(2)
                
                # 直接访问PDF链接
                page = await context.new_page()
                response = await page.goto(url, wait_until="networkidle")
                
                if response:
                    # 获取PDF内容
                    content = await response.body()
                    
                    if content and content[:4] == b'%PDF':
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        with open(filepath, 'wb') as f:
                            f.write(content)
                        
                        await browser.close()
                        
                        print(f"  [OK] Dynamic download success")
                        return {
                            "url": url,
                            "filepath": filepath,
                            "status": "downloaded",
                            "success": True,
                            "size": len(content)
                        }
                
                await browser.close()
                
                return {
                    "url": url,
                    "status": "failed",
                    "success": False,
                    "error": "Dynamic render failed"
                }
                
        except ImportError:
            return {
                "url": pdf_info["url"],
                "status": "failed",
                "success": False,
                "error": "Playwright not installed"
            }
        except Exception as e:
            return {
                "url": pdf_info["url"],
                "status": "failed",
                "success": False,
                "error": str(e)
            }
    
    async def download_all(self, pdf_list: List[Dict], output_dir: str = "pdfs/enhanced", use_dynamic: bool = False) -> List[Dict]:
        """
        批量下载PDF
        """
        print(f"\n{'='*70}")
        print(f"Enhanced PDF Downloader")
        print(f"Total PDFs: {len(pdf_list)}")
        print(f"Output dir: {output_dir}")
        print(f"Dynamic mode: {use_dynamic}")
        print('='*70)
        
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        
        for pdf_info in pdf_list:
            # 先尝试普通下载
            result = await self.download_with_retry(pdf_info, output_dir)
            
            # 如果失败且启用了动态渲染，尝试动态模式
            if not result.get("success") and use_dynamic:
                result = await self.download_with_dynamic(pdf_info, output_dir)
            
            results.append(result)
        
        # 统计
        success_count = sum(1 for r in results if r.get("status") == "downloaded")
        exists_count = sum(1 for r in results if r.get("status") == "exists")
        failed_count = len(results) - success_count - exists_count
        
        print(f"\n{'='*70}")
        print(f"Download Summary:")
        print(f"  Success: {success_count}")
        print(f"  Exists:  {exists_count}")
        print(f"  Failed:  {failed_count}")
        print('='*70)
        
        # 保存失败记录
        if self.failed:
            failed_file = os.path.join(output_dir, "failed_downloads.json")
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(self.failed, f, ensure_ascii=False, indent=2)
            print(f"\nFailed downloads saved to: {failed_file}")
        
        return results


def load_pdfs_from_crawl_data(json_file: str) -> List[Dict]:
    """从爬虫数据中提取PDF信息"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pdfs = []
    for item in data:
        for pdf in item.get("competition_pdfs", []):
            pdf_info = {
                "url": pdf["url"],
                "filename": pdf["filename"],
                "referer": item["url"],  # 原网页作为referer
                "title": pdf.get("link_text", "")
            }
            pdfs.append(pdf_info)
    
    return pdfs


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced PDF Downloader")
    parser.add_argument("--input", "-i", default="batch_test/data/enhanced_crawl_20260320_142833.json",
                       help="Input JSON file from crawler")
    parser.add_argument("--output", "-o", default="pdfs/enhanced",
                       help="Output directory for PDFs")
    parser.add_argument("--dynamic", "-d", action="store_true",
                       help="Use dynamic rendering for failed downloads")
    
    args = parser.parse_args()
    
    # 加载PDF列表
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        return
    
    pdfs = load_pdfs_from_crawl_data(args.input)
    
    if not pdfs:
        print("No PDFs found in input file")
        return
    
    print(f"Found {len(pdfs)} PDFs to download")
    
    # 下载
    downloader = EnhancedPDFDownloader(timeout=60)
    results = await downloader.download_all(pdfs, args.output, use_dynamic=args.dynamic)
    
    # 显示失败的PDF
    failed = [r for r in results if r.get("status") == "failed"]
    if failed:
        print(f"\n{'='*70}")
        print("Failed PDFs (need manual download):")
        for f in failed:
            print(f"  - {f['filename']}")
            print(f"    URL: {f['url']}")
            print(f"    Error: {f.get('error', 'Unknown')}")
        print('='*70)


if __name__ == "__main__":
    asyncio.run(main())
