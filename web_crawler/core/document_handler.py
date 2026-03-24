#!/usr/bin/env python3
"""
多格式文档处理器
支持: PDF, Word(doc/docx), Excel(xls/xlsx), PPT(ppt/pptx), 压缩包(zip/rar/7z)
"""
import os
import re
import json
import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse, unquote
from typing import List, Dict, Optional
from pathlib import Path


class DocumentHandler:
    """多格式文档处理器"""
    
    # 支持的文档格式
    DOCUMENT_EXTENSIONS = {
        # PDF
        '.pdf': 'PDF',
        # Word
        '.doc': 'Word',
        '.docx': 'Word',
        '.dot': 'Word',
        '.dotx': 'Word',
        '.rtf': 'Word',
        # Excel
        '.xls': 'Excel',
        '.xlsx': 'Excel',
        '.xlsm': 'Excel',
        '.xlsb': 'Excel',
        '.csv': 'Excel',
        # PowerPoint
        '.ppt': 'PowerPoint',
        '.pptx': 'PowerPoint',
        '.pps': 'PowerPoint',
        '.ppsx': 'PowerPoint',
        # 压缩包
        '.zip': 'Archive',
        '.rar': 'Archive',
        '.7z': 'Archive',
        '.tar': 'Archive',
        '.gz': 'Archive',
        '.bz2': 'Archive',
        # 其他文档
        '.txt': 'Text',
        '.wps': 'WPS',
        '.et': 'WPS',
        '.dps': 'WPS',
    }
    
    # 比赛相关关键词（用于判断文档相关性）
    COMPETITION_KEYWORDS = [
        "大赛", "比赛", "竞赛", "征集", "评选", "征稿",
        "评职", "评奖", "评优", "评先", "微课", "公开课",
        "优质课", "精品课", "说课", "征文", "论文", "通知",
        "公告", "公示", "简章", "方案", "指南", "报名",
        "参赛", "作品", "提交", "评审", "获奖", "结果",
        "名单", "荣誉", "证书", "活动", "赛事", "选拔"
    ]
    
    def __init__(self, timeout: int = 60, output_dir: str = "./output/documents"):
        self.timeout = timeout
        self.output_dir = output_dir
        self.downloaded_files = []
        
        # 创建输出目录
        for doc_type in set(self.DOCUMENT_EXTENSIONS.values()):
            os.makedirs(os.path.join(output_dir, doc_type), exist_ok=True)
    
    def get_document_type(self, filename: str) -> str:
        """获取文档类型"""
        ext = Path(filename).suffix.lower()
        return self.DOCUMENT_EXTENSIONS.get(ext, 'Other')
    
    def is_document_link(self, url: str) -> bool:
        """检查URL是否是文档链接"""
        url_lower = url.lower()
        # 检查是否是文档扩展名结尾
        for ext in self.DOCUMENT_EXTENSIONS.keys():
            if url_lower.endswith(ext):
                return True
        # 检查URL中是否包含文档标识
        if any(ext in url_lower for ext in ['.pdf', '.doc', '.xls', '.ppt', '.zip', '.rar']):
            return True
        return False
    
    def _clean_notice_title(self, title: str) -> str:
        """清理通知标题，移除非法字符
        
        Args:
            title: 通知标题
            
        Returns:
            清理后的标题，最多50字符
        """
        if not title:
            return ""
        
        # 移除Windows文件名非法字符: < > : " / \ | ? *
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            title = title.replace(char, '_')
        
        # 移除换行符、回车符等
        title = title.replace('\n', '').replace('\r', '').replace('\t', ' ')
        
        # 移除多余空白
        title = re.sub(r'\s+', ' ', title).strip()
        
        # 限制长度，最多50字符
        return title[:50]
    
    def _limit_filename_length(self, filename: str, max_length: int = 200) -> str:
        """限制文件名总长度
        
        Args:
            filename: 原始文件名
            max_length: 最大长度
            
        Returns:
            截断后的文件名（保留扩展名）
        """
        if len(filename) <= max_length:
            return filename
        
        name, ext = os.path.splitext(filename)
        # 保留扩展名，截断中间部分
        keep_len = (max_length - len(ext) - 3) // 2
        if keep_len < 1:
            # 如果名字部分太短，直接截断
            return filename[:max_length]
        
        return name[:keep_len] + "..." + name[-keep_len:] + ext
    
    def _find_existing_file(self, save_dir: str, url: str, filename: str) -> Optional[str]:
        """查找是否已有相同URL的文件下载过
        
        通过检查下载记录文件来判断
        
        Args:
            save_dir: 保存目录
            url: 文档URL
            filename: 期望的文件名
            
        Returns:
            已存在文件的路径，如果不存在则返回None
        """
        # 下载记录文件路径
        record_file = os.path.join(save_dir, ".download_records.json")
        
        # 加载下载记录
        records = {}
        if os.path.exists(record_file):
            try:
                with open(record_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            except Exception:
                records = {}
        
        # 检查URL是否已下载过
        if url in records:
            existing_path = records[url]
            if os.path.exists(existing_path):
                return existing_path
            else:
                # 文件被删除，从记录中移除
                del records[url]
                try:
                    with open(record_file, 'w', encoding='utf-8') as f:
                        json.dump(records, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
        
        # 也检查目标文件名是否已存在（兼容旧文件）
        filepath = os.path.join(save_dir, filename)
        if os.path.exists(filepath):
            # 记录这个新文件
            records[url] = filepath
            try:
                with open(record_file, 'w', encoding='utf-8') as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            return filepath
        
        return None
    
    def _record_download(self, save_dir: str, url: str, filepath: str):
        """记录下载的文件
        
        Args:
            save_dir: 保存目录
            url: 文档URL
            filepath: 文件路径
        """
        record_file = os.path.join(save_dir, ".download_records.json")
        
        records = {}
        if os.path.exists(record_file):
            try:
                with open(record_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            except Exception:
                records = {}
        
        records[url] = filepath
        
        try:
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def clean_filename(self, filename: str, page_title: str = "", max_length: int = 80) -> str:
        """清理文件名，格式为"通知标题_原始文件名"
        
        Args:
            filename: 原始文件名
            page_title: 比赛通知页面标题
            max_length: 文件名最大长度（不含扩展名）
        
        Returns:
            格式为: {清理后的通知标题}_{原始文件名}
        """
        # 解码URL编码
        filename = unquote(filename)
        
        # 移除路径中的目录部分
        filename = os.path.basename(filename)
        
        # 如果文件名中没有扩展名，默认使用.pdf
        if '.' not in filename:
            ext = '.pdf'
        else:
            # 提取原始扩展名
            ext = os.path.splitext(filename)[1].lower()
        
        # 清理扩展名中的非法字符
        ext = re.sub(r'[<>"/\\|?*]', '_', ext)
        
        # 提取原始文件名（不含扩展名）
        original_name = os.path.splitext(filename)[0]
        original_name = re.sub(r'[<>"/\\|?*]', '_', original_name)
        original_name = re.sub(r'\s+', ' ', original_name).strip()
        
        # 如果page_title不为空，使用"标题_文件名"格式
        if page_title and page_title.strip():
            clean_title = self._clean_notice_title(page_title)
            # 格式: {通知标题}_{原始文件名}
            name = f"{clean_title}_{original_name}"
        else:
            name = original_name
        
        # 限制文件名长度（不含扩展名）
        if len(name) > max_length:
            name = name[:max_length].strip()
        
        # 组合最终文件名
        final_filename = name + ext
        
        return final_filename.strip()
    
    def is_competition_related(self, text: str) -> bool:
        """判断是否与比赛相关"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.COMPETITION_KEYWORDS)
    
    def extract_document_links(self, html_content: str, base_url: str, page_title: str = "") -> List[Dict]:
        """从HTML中提取所有文档链接"""
        documents = []
        
        # 1. 提取<a>标签中的文档链接
        import re
        
        # 匹配href属性
        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
        links = re.findall(link_pattern, html_content, re.IGNORECASE | re.DOTALL)
        
        for href, link_text in links:
            href = href.strip()
            link_text = re.sub(r'<[^>]+>', '', link_text).strip()  # 移除HTML标签
            
            # 转换为绝对URL
            full_url = urljoin(base_url, href)
            
            # 检查是否是文档链接
            if self.is_document_link(full_url):
                # 获取文件名
                parsed = urlparse(full_url)
                filename = os.path.basename(parsed.path) or "unnamed"
                filename = self.clean_filename(filename, page_title)
                
                # 判断是否与比赛相关
                combined_text = f"{page_title} {link_text} {filename}"
                is_competition = self.is_competition_related(combined_text)
                
                doc_info = {
                    "url": full_url,
                    "filename": filename,
                    "link_text": link_text,
                    "page_title": page_title,
                    "doc_type": self.get_document_type(filename),
                    "is_competition_related": is_competition,
                    "source_url": base_url,
                    "size": None,  # 将在下载时获取
                    "downloaded": False
                }
                
                # 去重
                if not any(d["url"] == full_url for d in documents):
                    documents.append(doc_info)
        
        # 2. 提取onclick中的文档链接
        onclick_pattern = r'onclick=["\'][^"\']*location\.href=["\']([^"\']+)["\']'
        onclick_links = re.findall(onclick_pattern, html_content, re.IGNORECASE)
        
        for href in onclick_links:
            full_url = urljoin(base_url, href)
            if self.is_document_link(full_url):
                parsed = urlparse(full_url)
                filename = os.path.basename(parsed.path) or "unnamed"
                filename = self.clean_filename(filename, page_title)
                
                combined_text = f"{page_title} {filename}"
                is_competition = self.is_competition_related(combined_text)
                
                doc_info = {
                    "url": full_url,
                    "filename": filename,
                    "link_text": "",
                    "page_title": page_title,
                    "doc_type": self.get_document_type(filename),
                    "is_competition_related": is_competition,
                    "source_url": base_url,
                    "size": None,
                    "downloaded": False
                }
                
                if not any(d["url"] == full_url for d in documents):
                    documents.append(doc_info)
        
        # 3. 提取data-url或其他常见属性
        data_url_pattern = r'data-url=["\']([^"\']+)["\']'
        data_urls = re.findall(data_url_pattern, html_content, re.IGNORECASE)
        
        for href in data_urls:
            full_url = urljoin(base_url, href)
            if self.is_document_link(full_url):
                parsed = urlparse(full_url)
                filename = os.path.basename(parsed.path) or "unnamed"
                filename = self.clean_filename(filename, page_title)
                
                combined_text = f"{page_title} {filename}"
                is_competition = self.is_competition_related(combined_text)
                
                doc_info = {
                    "url": full_url,
                    "filename": filename,
                    "link_text": "",
                    "page_title": page_title,
                    "doc_type": self.get_document_type(filename),
                    "is_competition_related": is_competition,
                    "source_url": base_url,
                    "size": None,
                    "downloaded": False
                }
                
                if not any(d["url"] == full_url for d in documents):
                    documents.append(doc_info)
        
        return documents
    
    async def download_document(self, session: aiohttp.ClientSession, doc_info: Dict, 
                                progress_callback=None, notice_title: str = "") -> Dict:
        """下载单个文档
        
        Args:
            session: aiohttp会话
            doc_info: 文档信息字典
            progress_callback: 进度回调函数
            notice_title: 通知标题，用于生成文件名
        """
        url = doc_info["url"]
        filename = doc_info.get("filename", "")
        doc_type = doc_info.get("doc_type", "Other")
        
        # 优先使用传入的notice_title，否则使用doc_info中的page_title
        title_to_use = notice_title or doc_info.get("page_title", "")
        
        # 从原始URL提取原始文件名
        parsed = urlparse(url)
        original_name = os.path.basename(parsed.path) or "unnamed"
        
        # 使用"通知标题_原始文件名"格式生成文件名
        filename = self.clean_filename(original_name, title_to_use)
        
        # 限制总文件名长度（Windows限制260字符）
        filename = self._limit_filename_length(filename, max_length=200)
        
        # 确定保存路径
        save_dir = os.path.join(self.output_dir, doc_type)
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)
        
        # 检查文件是否已存在（基于URL的MD5来判断是否是同一文件）
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        
        # 查找是否已有相同URL的文件下载过
        existing_file = self._find_existing_file(save_dir, url, filename)
        if existing_file:
            print(f"    [SKIP] 文件已存在: {os.path.basename(existing_file)}")
            doc_info["downloaded"] = True
            doc_info["filepath"] = existing_file
            doc_info["size"] = os.path.getsize(existing_file)
            doc_info["local_filename"] = os.path.basename(existing_file)
            return doc_info
        
        # 避免文件名冲突（同一页面多个附件时添加序号）
        counter = 1
        name, ext = os.path.splitext(filename)
        base_filepath = filepath
        while os.path.exists(filepath):
            filepath = os.path.join(save_dir, f"{name}_{counter}{ext}")
            counter += 1
        
        try:
            timeout = aiohttp.ClientTimeout(total=None, connect=30, sock_read=60)
            
            async with session.get(url, timeout=timeout, ssl=False) as response:
                if response.status == 200:
                    # 获取文件大小
                    total_size = response.headers.get('Content-Length')
                    if total_size:
                        total_size = int(total_size)
                    
                    # 流式下载
                    downloaded = 0
                    chunk_size = 65536  # 64KB
                    
                    with open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if progress_callback and total_size:
                                progress_callback(downloaded, total_size)
                    
                    # 验证文件
                    file_size = os.path.getsize(filepath)
                    
                    # 记录下载
                    self._record_download(save_dir, url, filepath)
                    
                    doc_info["downloaded"] = True
                    doc_info["filepath"] = filepath
                    doc_info["size"] = file_size
                    doc_info["local_filename"] = os.path.basename(filepath)
                    
                    print(f"    [DOWNLOAD] {os.path.basename(filepath)} ({self._format_size(file_size)})")
                    
                    return doc_info
                else:
                    doc_info["error"] = f"HTTP {response.status}"
                    return doc_info
                    
        except asyncio.TimeoutError:
            doc_info["error"] = "Download timeout"
            return doc_info
        except Exception as e:
            doc_info["error"] = str(e)
            return doc_info
    
    async def download_documents(self, documents: List[Dict], concurrency: int = 3,
                                  notice_title: str = "") -> List[Dict]:
        """批量下载文档
        
        Args:
            documents: 文档列表
            concurrency: 并发数
            notice_title: 通知标题，用于生成文件名（可选，优先使用doc_info中的page_title）
        """
        if not documents:
            return []
        
        print(f"\n[DOCUMENT] Preparing to download {len(documents)} documents...")
        
        # 统计
        type_count = {}
        for doc in documents:
            doc_type = doc.get("doc_type", "Other")
            type_count[doc_type] = type_count.get(doc_type, 0) + 1
        
        print(f"  [STATS] By type: {type_count}")
        
        # 只下载比赛相关的文档
        competition_docs = [d for d in documents if d.get("is_competition_related", False)]
        print(f"  [STATS] Competition-related: {len(competition_docs)}/{len(documents)}")
        
        if not competition_docs:
            print("  [INFO] No competition-related documents to download")
            return []
        
        # 预处理：为同一页面的多个文档预先分配序号，避免文件名冲突
        # 按page_title分组，为每组的文档添加序号
        from collections import defaultdict
        title_groups = defaultdict(list)
        for i, doc in enumerate(competition_docs):
            # 优先使用传入的notice_title，否则使用doc中的page_title
            title = notice_title or doc.get("page_title", "") or "unnamed"
            # 生成基础文件名（不含序号）
            parsed = urlparse(doc["url"])
            original_name = os.path.basename(parsed.path) or "unnamed"
            base_name = self.clean_filename(original_name, title)
            # 限制长度
            base_name = self._limit_filename_length(base_name, max_length=200)
            # 使用基础文件名（不含扩展名）作为分组键
            name_without_ext = os.path.splitext(base_name)[0]
            title_groups[name_without_ext].append(i)
        
        # 为需要序号的文档预先分配带序号的filename
        for title_key, indices in title_groups.items():
            if len(indices) > 1:
                # 同一页面有多个附件，预先添加序号
                for seq, idx in enumerate(indices, start=1):
                    doc = competition_docs[idx]
                    parsed = urlparse(doc["url"])
                    original_name = os.path.basename(parsed.path) or "unnamed"
                    # 优先使用传入的notice_title，否则使用doc中的page_title
                    page_title = notice_title or doc.get("page_title", "")
                    # 获取原始扩展名
                    ext = os.path.splitext(original_name)[1].lower() or ".pdf"
                    # 清理标题作为文件名主体
                    clean_title = self._clean_notice_title(page_title)
                    # 提取原始文件名（不含扩展名）
                    orig_name_no_ext = os.path.splitext(original_name)[0]
                    orig_name_no_ext = re.sub(r'[<>"/\\|?*]', '_', orig_name_no_ext)
                    # 格式: {通知标题}_{原始文件名}_{序号}
                    new_filename = f"{clean_title}_{orig_name_no_ext}_{seq}{ext}"
                    # 限制总长度
                    new_filename = self._limit_filename_length(new_filename, max_length=200)
                    competition_docs[idx]["filename"] = new_filename
        
        # 并发下载
        connector = aiohttp.TCPConnector(limit=concurrency)
        timeout = aiohttp.ClientTimeout(total=None, connect=30, sock_read=60)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            semaphore = asyncio.Semaphore(concurrency)
            
            async def download_with_limit(doc):
                async with semaphore:
                    # 传递notice_title参数
                    return await self.download_document(session, doc, notice_title=notice_title)
            
            tasks = [download_with_limit(doc) for doc in competition_docs]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        successful = []
        failed = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                competition_docs[i]["error"] = str(result)
                failed.append(competition_docs[i])
            elif result.get("downloaded"):
                successful.append(result)
            else:
                failed.append(result)
        
        print(f"\n  [DOWNLOAD] Completed: {len(successful)} succeeded, {len(failed)} failed")
        
        if failed:
            print(f"  [FAILED] {[d.get('filename', 'unknown') for d in failed[:3]]}")
        
        return successful
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f}KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes/(1024*1024):.1f}MB"
        else:
            return f"{size_bytes/(1024*1024*1024):.1f}GB"


# 便捷函数
def extract_documents(html_content: str, base_url: str, page_title: str = "") -> List[Dict]:
    """提取文档链接的便捷函数"""
    handler = DocumentHandler()
    return handler.extract_document_links(html_content, base_url, page_title)


async def download_documents(documents: List[Dict], output_dir: str = "./output/documents",
                              notice_title: str = "") -> List[Dict]:
    """下载文档的便捷函数
    
    Args:
        documents: 文档列表
        output_dir: 输出目录
        notice_title: 通知标题，用于生成文件名
    """
    handler = DocumentHandler(output_dir=output_dir)
    return await handler.download_documents(documents, notice_title=notice_title)
