"""
PDF 处理器
专门用于处理比赛通知和公告PDF文件的下载和解析
"""
import aiohttp
import asyncio
import os
import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse, unquote
from datetime import datetime
import hashlib


class PDFHandler:
    """PDF文件处理器"""
    
    # PDF文件保存目录
    PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pdfs")
    
    # 比赛相关的关键词（用于识别相关PDF - 扩展教育类）
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
        "通知", "公告", "公示", "简章", "方案", "指南"
    ]
    
    def __init__(self, timeout: int = 60):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.downloaded_pdfs = []
        os.makedirs(self.PDF_DIR, exist_ok=True)
    
    def is_pdf_url(self, url: str) -> bool:
        """检查URL是否指向PDF文件"""
        if not url:
            return False
        
        url_lower = url.lower()
        
        # 检查URL后缀
        if url_lower.endswith('.pdf'):
            return True
        
        # 检查URL中是否包含PDF相关参数
        if '.pdf?' in url_lower or '.pdf#' in url_lower:
            return True
        
        # 检查是否包含PDF相关的路径
        if '/pdf/' in url_lower or '/download/' in url_lower:
            # 进一步检查内容类型提示
            pdf_indicators = ['file', 'download', 'pdf', 'document', 'attachment']
            return any(ind in url_lower for ind in pdf_indicators)
        
        # 新增：检查常见的PDF下载链接模式
        # 例如：/uploads/xxx.pdf 或 /files/xxx.pdf
        import re
        pdf_patterns = [
            r'/uploads?/.*\.pdf',
            r'/files?/.*\.pdf',
            r'/attachments?/.*\.pdf',
            r'/docs?/.*\.pdf',
            r'/resources?/.*\.pdf',
            r'\.pdf(?:\?[^\s]*)?$',  # .pdf 结尾，可能有查询参数
        ]
        for pattern in pdf_patterns:
            if re.search(pattern, url_lower):
                return True
        
        return False
    
    def is_competition_related(self, text: str, link_text: str = "", page_title: str = "") -> bool:
        """
        判断是否与比赛/通知相关
        :param text: 周围文本内容
        :param link_text: 链接文本
        :param page_title: 页面标题（新增）
        """
        combined_text = f"{page_title} {text} {link_text}".lower()
        
        # 检查是否包含比赛相关关键词
        for keyword in self.COMPETITION_KEYWORDS:
            if keyword in combined_text:
                return True
        
        return False
    
    def extract_pdf_links(self, html_content: str, base_url: str, page_title: str = "") -> List[Dict]:
        """
        从HTML中提取所有PDF链接
        :param html_content: HTML内容
        :param base_url: 基础URL
        :param page_title: 页面标题（用于智能命名）
        :return: 包含PDF信息的字典列表
        """
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'lxml')
        pdf_links = []
        all_links_count = 0
        
        # 查找所有<a>标签
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            link_text = a_tag.get_text(strip=True)
            
            # 转换为绝对URL
            full_url = urljoin(base_url, href)
            
            # 检查是否是PDF
            if self.is_pdf_url(full_url):
                all_links_count += 1
                # 获取上下文信息
                context = self._get_context(a_tag)
                
                # 判断是否相关
                is_related = self.is_competition_related(context, link_text, page_title)
                
                pdf_info = {
                    "url": full_url,
                    "link_text": link_text,
                    "context": context,
                    "filename": self._generate_filename(full_url, link_text, page_title),
                    "is_competition_related": is_related
                }
                pdf_links.append(pdf_info)
        
        # 调试输出
        related_count = sum(1 for p in pdf_links if p["is_competition_related"])
        if pdf_links:
            print(f"    [PDF_DEBUG] 页面 '{page_title[:30]}...' 发现 {len(pdf_links)} 个PDF")
            print(f"    [PDF_DEBUG]   - 相关PDF: {related_count}, 非相关: {len(pdf_links) - related_count}")
            if len(pdf_links) > 0 and related_count == 0:
                print(f"    [PDF_DEBUG]   - 警告：发现PDF但无相关匹配，检查关键词是否覆盖")
        
        # 去重
        seen_urls = set()
        unique_links = []
        for pdf in pdf_links:
            if pdf["url"] not in seen_urls:
                seen_urls.add(pdf["url"])
                unique_links.append(pdf)
        
        return unique_links
    
    def _get_context(self, element, context_length: int = 200) -> str:
        """获取元素的上下文文本"""
        # 获取父元素的文本
        parent = element.find_parent(['p', 'div', 'li', 'td'])
        if parent:
            text = parent.get_text(strip=True)
            return text[:context_length]
        
        # 如果没有父元素，获取相邻文本
        prev_sibling = element.find_previous_sibling(string=True)
        next_sibling = element.find_next_sibling(string=True)
        
        context = ""
        if prev_sibling:
            context += str(prev_sibling)[-context_length//2:]
        if next_sibling:
            context += str(next_sibling)[:context_length//2]
        
        return context.strip()
    
    def _generate_filename(self, url: str, link_text: str = "", page_title: str = "") -> str:
        """
        智能生成PDF文件名 - 基于赛事名称
        :param url: PDF链接
        :param link_text: 链接文本
        :param page_title: 网页标题
        """
        # 优先使用智能识别的赛事名称
        smart_name = self._extract_competition_name(url, link_text, page_title)
        if smart_name:
            return f"{smart_name}.pdf"
        
        # 回退：尝试从URL中提取文件名
        parsed = urlparse(url)
        path = unquote(parsed.path)
        original_name = os.path.basename(path)
        
        if original_name and original_name.endswith('.pdf'):
            # 如果是通用名称（如 notice.pdf, file.pdf），尝试改进
            generic_names = ['notice', 'file', 'document', 'download', 'pdf', 'attachment']
            name_without_ext = original_name[:-4].lower()
            
            if name_without_ext in generic_names or len(name_without_ext) <= 5:
                # 使用链接文本或标题
                alt_name = link_text or page_title
                if alt_name:
                    clean_name = self._clean_filename(alt_name)
                    return f"{clean_name[:80]}.pdf"
            
            # 使用原始文件名（清理后）
            return self._clean_filename(original_name)
        
        # 最后回退：使用链接文本
        if link_text:
            return f"{self._clean_filename(link_text)}.pdf"
        
        # 最坏情况：使用时间戳
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"赛事通知_{timestamp}_{url_hash}.pdf"
    
    def _extract_competition_name(self, url: str, link_text: str, page_title: str) -> str:
        """
        智能提取赛事名称
        """
        combined_text = f"{page_title} {link_text}"
        
        # 模式1: 第X届XXX大赛/比赛/竞赛
        # 匹配"第九届"、"第9届"等格式
        # 使用贪婪匹配确保完整捕获到"大赛"/"比赛"/"竞赛"
        pattern1 = r'(第[一二三四五六七八九十0-9]+届[^""\']{2,50}(?:大赛|比赛|竞赛))'
        match = re.search(pattern1, combined_text)
        if match:
            return self._clean_filename(match.group(1))
        
        # 模式2: 备用模式 - 更宽松的正则
        pattern1b = r'(第[一二三四五六七八九十0-9]+届.+?大赛)'
        match = re.search(pattern1b, combined_text)
        if match:
            return self._clean_filename(match.group(1))
        
        # 模式3: XXX大赛/比赛/竞赛
        pattern2 = r'([^\s""\']{3,30}(?:大赛|比赛|竞赛))'
        match = re.search(pattern2, combined_text)
        if match:
            competition = match.group(1)
            return self._clean_filename(competition)
        
        # 模式4: XXX征集/评选/活动
        pattern3 = r'([^\s""\']{3,30}(?:征集|评选|活动|方案))'
        match = re.search(pattern3, combined_text)
        if match:
            competition = match.group(1)
            return self._clean_filename(competition)
        
        # 模式5: 从URL路径中提取届数+标题
        url_lower = url.lower()
        if 'game' in url_lower or 'match' in url_lower or 'competition' in url_lower:
            # 提取届数 (game9, game_9, game-9 等格式)
            edition_match = re.search(r'game[\-_]?(\d+)', url_lower)
            if edition_match:
                edition_num = edition_match.group(1)
                # 尝试从标题提取名称
                name_match = re.search(r'[""]?([^""]+?)[大赛比赛竞赛]', page_title)
                if name_match:
                    competition_name = name_match.group(1).strip()
                    return self._clean_filename(f"第{edition_num}届{competition_name}大赛通知")
        
        return ""
    
    def _number_to_chinese(self, num_str: str) -> str:
        """数字转中文（简版）"""
        num_map = {
            '1': '一', '2': '二', '3': '三', '4': '四', '5': '五',
            '6': '六', '7': '七', '8': '八', '9': '九', '0': '〇'
        }
        return ''.join(num_map.get(c, c) for c in num_str)
    
    def _clean_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除文件扩展名（如果有）
        if filename.lower().endswith('.pdf'):
            filename = filename[:-4]
        
        # 移除前后空格
        filename = filename.strip()
        
        # 替换非法字符为下划线
        filename = re.sub(r'[\\/*?:""<>|]', '_', filename)
        
        # 移除或替换其他特殊字符
        filename = re.sub(r'[\s]+', '_', filename)  # 空格转下划线
        filename = re.sub(r'[_]+', '_', filename)  # 多个下划线合并
        filename = re.sub(r'[^\w\-\u4e00-\u9fa5]', '', filename)  # 只保留中文、英文、数字、下划线、横线
        
        # 限制长度（保留更多字符）
        return filename[:100]
    
    async def download_pdf(self, session: aiohttp.ClientSession, 
                          pdf_info: Dict,
                          subdir: str = "") -> Dict:
        """
        下载单个PDF文件（支持大文件流式下载）
        """
        url = pdf_info["url"]
        filename = pdf_info["filename"]
        
        print(f"    [PDF_DOWNLOAD] 开始下载: {filename}")
        print(f"    [PDF_DOWNLOAD] URL: {url[:80]}...")
        
        # 创建子目录
        if subdir:
            save_dir = os.path.join(self.PDF_DIR, subdir)
        else:
            save_dir = self.PDF_DIR
        
        os.makedirs(save_dir, exist_ok=True)
        
        filepath = os.path.join(save_dir, filename)
        
        # 检查文件是否已存在
        if os.path.exists(filepath):
            print(f"    [PDF_DOWNLOAD] 文件已存在，跳过: {filename}")
            return {
                "url": url,
                "filename": filename,
                "filepath": filepath,
                "status": "exists",
                "size": os.path.getsize(filepath)
            }
        
        try:
            print(f"    [PDF_DOWNLOAD] 正在请求: {url[:60]}...")
            
            # 使用更大的超时时间（针对大文件）
            # total=None 表示不限制总时间，只限制连接和读取时间
            download_timeout = aiohttp.ClientTimeout(
                total=None,  # 不限制总时间
                connect=30,  # 连接超时30秒
                sock_read=60  # 读取超时60秒（每次读取）
            )
            
            async with session.get(url, timeout=download_timeout, ssl=False) as response:
                print(f"    [PDF_DOWNLOAD] 响应状态: {response.status}")
                
                if response.status == 200:
                    # 获取文件大小
                    total_size = response.headers.get('Content-Length')
                    if total_size:
                        total_size = int(total_size)
                        print(f"    [PDF_DOWNLOAD] 文件大小: {self._format_size(total_size)}")
                    
                    # 流式下载，分块读取
                    chunk_size = 64 * 1024  # 64KB 块
                    downloaded = 0
                    last_print = 0
                    
                    # 先读取第一块验证PDF格式
                    first_chunk = await response.content.read(chunk_size)
                    if not self._is_valid_pdf(first_chunk):
                        print(f"    [PDF_DOWNLOAD] 错误: 不是有效的PDF文件")
                        return {
                            "url": url,
                            "filename": filename,
                            "status": "error",
                            "error": "下载的内容不是有效的PDF文件"
                        }
                    
                    # 保存文件
                    with open(filepath, 'wb') as f:
                        f.write(first_chunk)
                        downloaded += len(first_chunk)
                        
                        # 继续读取剩余内容
                        while True:
                            chunk = await response.content.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # 每5MB打印一次进度
                            if downloaded - last_print >= 5 * 1024 * 1024:
                                print(f"    [PDF_DOWNLOAD] 已下载: {self._format_size(downloaded)}")
                                last_print = downloaded
                    
                    print(f"    [PDF_DOWNLOAD] 下载完成: {self._format_size(downloaded)}")
                    print(f"    [PDF_DOWNLOAD] 保存成功: {filepath}")
                    
                    return {
                        "url": url,
                        "filename": filename,
                        "filepath": filepath,
                        "status": "downloaded",
                        "size": downloaded,
                        "link_text": pdf_info.get("link_text", ""),
                        "context": pdf_info.get("context", "")
                    }
                else:
                    print(f"    [PDF_DOWNLOAD] 错误: HTTP {response.status}")
                    return {
                        "url": url,
                        "filename": filename,
                        "status": "error",
                        "error": f"HTTP {response.status}"
                    }
        except asyncio.TimeoutError:
            print(f"    [PDF_DOWNLOAD] 错误: 下载超时")
            # 清理未完成的文件
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"    [PDF_DOWNLOAD] 已清理未完成文件")
                except:
                    pass
            return {
                "url": url,
                "filename": filename,
                "status": "error",
                "error": "下载超时（文件可能太大或网络太慢）"
            }
        except Exception as e:
            print(f"    [PDF_DOWNLOAD] 异常: {e}")
            # 清理未完成的文件
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            return {
                "url": url,
                "filename": filename,
                "status": "error",
                "error": str(e)
            }
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小显示"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def _is_valid_pdf(self, content: bytes) -> bool:
        """验证文件是否为有效的PDF"""
        # PDF文件的魔数: %PDF
        return content[:4] == b'%PDF'
    
    async def download_all_pdfs(self, pdf_infos: List[Dict], 
                                 subdir: str = "",
                                 concurrency: int = 3) -> List[Dict]:
        """
        批量下载PDF文件
        """
        print(f"\n  [PDF_BATCH] 开始批量下载，共 {len(pdf_infos)} 个PDF")
        print(f"  [PDF_BATCH] 保存目录: {os.path.join(self.PDF_DIR, subdir)}")
        print(f"  [PDF_BATCH] 并发数: {concurrency}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        connector = aiohttp.TCPConnector(limit=concurrency, ssl=False)
        
        async with aiohttp.ClientSession(
            connector=connector,
            headers=headers
        ) as session:
            # 创建信号量限制并发
            semaphore = asyncio.Semaphore(concurrency)
            
            async def download_with_limit(pdf_info):
                async with semaphore:
                    return await self.download_pdf(session, pdf_info, subdir)
            
            # 执行下载
            tasks = [download_with_limit(pdf) for pdf in pdf_infos]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            download_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"    [PDF_BATCH] 第 {i+1} 个下载异常: {result}")
                    download_results.append({
                        "status": "error",
                        "error": str(result)
                    })
                else:
                    download_results.append(result)
            
            print(f"  [PDF_BATCH] 批量下载完成，成功 {len([r for r in download_results if r.get('status') == 'downloaded'])}")
            return download_results
    
    def get_pdf_summary(self, results: List[Dict]) -> Dict:
        """获取PDF下载汇总信息"""
        total = len(results)
        downloaded = sum(1 for r in results if r.get("status") == "downloaded")
        exists = sum(1 for r in results if r.get("status") == "exists")
        failed = total - downloaded - exists
        
        total_size = sum(r.get("size", 0) for r in results if r.get("status") in ["downloaded", "exists"])
        
        return {
            "total": total,
            "downloaded": downloaded,
            "exists": exists,
            "failed": failed,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }


class PDFTextExtractor:
    """PDF文本提取器（可选功能）"""
    
    @staticmethod
    def extract_text(pdf_path: str) -> str:
        """
        提取PDF文本内容
        需要安装 PyPDF2 或 pdfplumber
        """
        try:
            # 尝试使用 pdfplumber（效果更好）
            import pdfplumber
            
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            return "\n".join(text_parts)
        except ImportError:
            # 回退到 PyPDF2
            try:
                import PyPDF2
                
                text_parts = []
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                
                return "\n".join(text_parts)
            except ImportError:
                return "错误: 未安装PDF解析库。请安装 pdfplumber 或 PyPDF2"
        except Exception as e:
            return f"PDF解析错误: {str(e)}"
