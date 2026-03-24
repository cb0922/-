"""
网页内容解析模块
使用 BeautifulSoup 提取结构化数据
"""
from bs4 import BeautifulSoup, Tag, NavigableString
from typing import List, Dict, Optional, Callable, Union
import re
import json


class ContentParser:
    """通用内容解析器"""
    
    # 需要移除的标签（广告、导航等无关内容）
    NOISE_TAGS = [
        'script', 'style', 'nav', 'footer', 'header', 'aside',
        '.advertisement', '.ad', '.ads', '.banner', '.sidebar',
        '#sidebar', '.widget', '.comments', '.comment',
        '.share', '.social', '.related', '.recommend',
        'iframe', 'noscript'
    ]
    
    def __init__(self, html_content: str):
        # 处理编码问题
        if isinstance(html_content, bytes):
            # 尝试自动检测编码
            html_content = self._decode_bytes(html_content)
        
        self.soup = BeautifulSoup(html_content, 'lxml')
        self.html_content = html_content
    
    def _decode_bytes(self, content: bytes) -> str:
        """尝试多种编码解码字节内容"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin-1']
        for encoding in encodings:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        # 如果都失败，使用utf-8并忽略错误
        return content.decode('utf-8', errors='ignore')
    
    def get_title(self) -> str:
        """获取页面标题"""
        # 尝试多种方式获取标题
        title_tag = self.soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            # 清理标题中常见的网站后缀
            title = re.sub(r'[\|\-\–\—].*$', '', title).strip()
            return title
        
        # 尝试 h1 标签
        h1 = self.soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        # 尝试 og:title
        og_title = self.get_meta('og:title')
        if og_title:
            return og_title
        
        return ""
    
    def get_meta(self, name: str) -> str:
        """获取 meta 标签内容"""
        # 尝试 name 属性
        meta = self.soup.find('meta', attrs={'name': name})
        if meta:
            return meta.get('content', '')
        
        # 尝试 property 属性 (Open Graph)
        meta = self.soup.find('meta', attrs={'property': name})
        if meta:
            return meta.get('content', '')
        
        # 尝试 http-equiv
        meta = self.soup.find('meta', attrs={'http-equiv': name})
        if meta:
            return meta.get('content', '')
        
        return ""
    
    def get_all_meta(self) -> Dict[str, str]:
        """获取所有 meta 标签"""
        meta_dict = {}
        for meta in self.soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content', '')
            if name and content:
                meta_dict[name] = content
        return meta_dict
    
    def get_text(self, selector: Optional[str] = None, 
                 clean: bool = True,
                 remove_noise: bool = True) -> str:
        """
        获取文本内容
        :param selector: CSS选择器，None则获取整个页面
        :param clean: 是否清理空白字符
        :param remove_noise: 是否移除噪声标签
        """
        # 创建工作副本
        if selector:
            element = self.soup.select_one(selector)
            if not element:
                return ""
            soup_copy = BeautifulSoup(str(element), 'lxml')
        else:
            soup_copy = BeautifulSoup(self.html_content, 'lxml')
        
        # 移除噪声标签
        if remove_noise:
            for tag_name in self.NOISE_TAGS:
                if tag_name.startswith('.') or tag_name.startswith('#'):
                    # 类名或ID选择器
                    for elem in soup_copy.select(tag_name):
                        elem.decompose()
                else:
                    # 标签名
                    for elem in soup_copy.find_all(tag_name):
                        elem.decompose()
        
        # 获取文本
        text = soup_copy.get_text(separator='\n', strip=True)
        
        if clean:
            # 清理多余空白
            text = re.sub(r'\n\s*\n+', '\n\n', text)  # 多个空行合并为两个
            text = re.sub(r'[ \t]+', ' ', text)  # 多个空格合并为一个
            text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)  # 行首尾空格
        
        return text.strip()
    
    def get_main_content(self) -> str:
        """
        智能提取主要内容
        使用简单的文本密度算法
        """
        # 常见的主要内容区域选择器
        content_selectors = [
            'article', 'main', '.content', '#content',
            '.article-content', '.post-content', '.entry-content',
            '.detail-content', '.text-content', '.news-content'
        ]
        
        for selector in content_selectors:
            element = self.soup.select_one(selector)
            if element:
                return self.get_text(selector, remove_noise=True)
        
        # 如果没有找到，返回整个页面的文本
        return self.get_text(remove_noise=True)
    
    def get_links(self, pattern: Optional[str] = None) -> List[Dict]:
        """获取所有链接"""
        links = []
        for a in self.soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)
            
            # 跳过无意义链接
            if not text or text in ['#', 'javascript:void(0)']:
                continue
            
            if pattern and pattern not in href:
                continue
            
            links.append({
                "url": href,
                "text": text[:100],  # 限制长度
                "title": a.get('title', '')
            })
        return links
    
    def get_images(self) -> List[Dict]:
        """获取所有图片"""
        images = []
        for img in self.soup.find_all('img'):
            src = img.get('src', '')
            # 如果没有src，尝试 data-src (懒加载)
            if not src:
                src = img.get('data-src', '')
            if not src:
                src = img.get('data-original', '')
            
            if src and not src.startswith('data:'):  # 跳过 base64 图片
                images.append({
                    "src": src,
                    "alt": img.get('alt', ''),
                    "title": img.get('title', ''),
                    "width": img.get('width', ''),
                    "height": img.get('height', '')
                })
        return images
    
    def extract_table(self, selector: str) -> List[Dict]:
        """提取表格数据"""
        table = self.soup.select_one(selector)
        if not table:
            return []
        
        headers = []
        rows = []
        
        # 获取表头
        header_row = table.find('thead')
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        
        # 获取数据行
        tbody = table.find('tbody') or table
        for tr in tbody.find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
            if cells:
                rows.append(cells)
        
        # 如果没有表头，使用第一行作为表头
        if not headers and rows:
            headers = rows[0]
            rows = rows[1:]
        
        # 转换为字典列表
        result = []
        for row in rows:
            row_dict = {}
            for i, header in enumerate(headers):
                row_dict[header] = row[i] if i < len(row) else ""
            result.append(row_dict)
        
        return result
    
    def extract_list(self, selector: str) -> List[str]:
        """提取列表项"""
        elements = self.soup.select(selector)
        return [elem.get_text(strip=True) for elem in elements]
    
    def extract_by_rules(self, rules: Dict[str, str]) -> Dict:
        """
        根据规则提取数据
        :param rules: 字段名 -> CSS选择器 的映射
        :return: 提取的数据字典
        """
        result = {}
        for field, selector in rules.items():
            element = self.soup.select_one(selector)
            if element:
                result[field] = element.get_text(strip=True)
            else:
                result[field] = ""
        return result
    
    def to_dict(self) -> Dict:
        """将页面转换为结构化字典"""
        return {
            "title": self.get_title(),
            "description": self.get_meta("description"),
            "keywords": self.get_meta("keywords"),
            "text": self.get_main_content()[:3000],  # 使用智能提取，限制长度
            "links_count": len(self.soup.find_all('a', href=True)),
            "images_count": len(self.soup.find_all('img'))
        }


class ArticleParser(ContentParser):
    """文章页面专用解析器"""
    
    def get_article(self) -> Dict:
        """提取文章信息"""
        return {
            "title": self.get_title(),
            "author": self._get_author(),
            "publish_time": self._get_publish_time(),
            "source": self._get_source(),
            "content": self._get_article_content(),
            "images": self.get_images()
        }
    
    def _get_author(self) -> str:
        """提取作者信息"""
        selectors = [
            '.author', '.writer', '.byline', '[rel="author"]',
            '.post-author', '.article-author', '.meta-author',
            '.author-name', '.user-name', '.nickname'
        ]
        for selector in selectors:
            elem = self.soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return ""
    
    def _get_publish_time(self) -> str:
        """提取发布时间"""
        # 先尝试 time 标签
        time_elem = self.soup.find('time')
        if time_elem and time_elem.get('datetime'):
            return time_elem['datetime']
        
        selectors = [
            '.time', '.date', '.publish-time', '.post-date',
            '.article-date', '.meta-date', '.publish_date'
        ]
        for selector in selectors:
            elem = self.soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return ""
    
    def _get_source(self) -> str:
        """提取文章来源"""
        selectors = [
            '.source', '.source-name', '.article-source',
            '.publisher', '.site-name'
        ]
        for selector in selectors:
            elem = self.soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return ""
    
    def _get_article_content(self) -> str:
        """提取文章内容"""
        # 常见内容选择器
        selectors = [
            'article', '.article-content', '.post-content',
            '.entry-content', '.content', '#content',
            '.article-body', '.post-body', '.detail-content'
        ]
        
        for selector in selectors:
            elem = self.soup.select_one(selector)
            if elem:
                return elem.get_text(separator='\n', strip=True)
        
        # 如果没找到，返回所有长段落文本
        paragraphs = self.soup.find_all('p')
        long_paragraphs = [
            p.get_text(strip=True) 
            for p in paragraphs 
            if len(p.get_text(strip=True)) > 50
        ]
        return '\n'.join(long_paragraphs)


class JSONParser:
    """JSON 数据解析器"""
    
    @staticmethod
    def parse(json_content: str) -> Union[Dict, List]:
        """解析JSON字符串"""
        try:
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            return {"error": f"JSON解析失败: {str(e)}"}
    
    @staticmethod
    def extract_from_html(html_content: str) -> Optional[Union[Dict, List]]:
        """从HTML中提取JSON数据（如 script type="application/ld+json"）"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 查找 JSON-LD
        json_scripts = soup.find_all('script', type='application/ld+json')
        results = []
        
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                results.append(data)
            except:
                continue
        
        return results if results else None


class PDFLinkExtractor:
    """PDF链接提取器"""
    
    def __init__(self, html_content: str, base_url: str):
        self.soup = BeautifulSoup(html_content, 'lxml')
        self.base_url = base_url
    
    def extract_pdf_links(self) -> List[Dict]:
        """提取所有PDF链接"""
        from urllib.parse import urljoin
        
        pdf_links = []
        
        for a_tag in self.soup.find_all('a', href=True):
            href = a_tag['href']
            link_text = a_tag.get_text(strip=True)
            
            # 检查是否是PDF
            if href.lower().endswith('.pdf') or '.pdf?' in href.lower():
                full_url = urljoin(self.base_url, href)
                
                # 获取上下文
                context = self._get_context(a_tag)
                
                pdf_links.append({
                    "url": full_url,
                    "link_text": link_text,
                    "context": context[:200]
                })
        
        return pdf_links
    
    def _get_context(self, element, max_length: int = 300) -> str:
        """获取元素的上下文"""
        # 尝试获取父元素
        for parent_name in ['p', 'div', 'li', 'td', 'article']:
            parent = element.find_parent(parent_name)
            if parent:
                return parent.get_text(strip=True)[:max_length]
        
        # 返回链接文本
        return element.get_text(strip=True)[:max_length]


class PageAnalyzer:
    """页面分析器 - 分析网页结构和内容质量"""
    
    def __init__(self, html_content: str):
        self.parser = ContentParser(html_content)
    
    def analyze(self) -> Dict:
        """分析页面"""
        soup = self.parser.soup
        
        # 基础统计
        stats = {
            "title": self.parser.get_title(),
            "has_h1": bool(soup.find('h1')),
            "h1_count": len(soup.find_all('h1')),
            "h2_count": len(soup.find_all('h2')),
            "h3_count": len(soup.find_all('h3')),
            "paragraph_count": len(soup.find_all('p')),
            "link_count": len(soup.find_all('a', href=True)),
            "image_count": len(soup.find_all('img')),
            "table_count": len(soup.find_all('table')),
            "has_video": bool(soup.find(['video', 'iframe[src*="youtube"]', 'iframe[src*="vimeo"]'])),
            "text_length": len(self.parser.get_text()),
            "meta_description": self.parser.get_meta('description'),
            "meta_keywords": self.parser.get_meta('keywords'),
        }
        
        # 内容质量评分
        quality_score = 0
        if stats['title']:
            quality_score += 20
        if stats['has_h1']:
            quality_score += 15
        if stats['meta_description']:
            quality_score += 15
        if stats['paragraph_count'] > 3:
            quality_score += 20
        if stats['text_length'] > 500:
            quality_score += 30
        
        stats['quality_score'] = min(100, quality_score)
        
        return stats
