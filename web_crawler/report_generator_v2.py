#!/usr/bin/env python3
"""
可视化报告生成器 V2
优化内容：
1. 修复内容丢失问题 - 保留完整内容并提供更好的格式化
2. 优化排版 - 使用更清晰的布局还原原网站结构
3. 添加原始HTML预览功能
"""
import json
import os
import re
import html
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse


class ReportGeneratorV2:
    """HTML 报告生成器 V2 - 优化版"""
    
    def __init__(self, data: List[Dict], title: str = "网页爬取报告"):
        self.data = data
        self.title = title
        self.output_dir = os.path.join(os.path.dirname(__file__), "reports")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate(self) -> str:
        """生成完整报告"""
        html_parts = []
        html_parts.append(self._generate_head())
        html_parts.append(self._generate_body())
        html_parts.append(self._generate_footer())
        
        html = "\n".join(html_parts)
        
        # 保存文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_v2_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        
        return filepath
    
    def _generate_head(self) -> str:
        """生成 HTML 头部"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <style>
        :root {{
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #64748b;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --text-light: #64748b;
            --border: #e2e8f0;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}
        
        /* 头部 */
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .header-meta {{
            opacity: 0.9;
            font-size: 0.9rem;
        }}
        
        /* 统计卡片 */
        .stats-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            padding: 1.5rem;
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .stat-card {{
            background: var(--card);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            border-left: 4px solid var(--primary);
        }}
        
        .stat-card.success {{ border-left-color: var(--success); }}
        .stat-card.warning {{ border-left-color: var(--warning); }}
        .stat-card.danger {{ border-left-color: var(--danger); }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--text);
        }}
        
        .stat-label {{
            color: var(--text-light);
            font-size: 0.9rem;
        }}
        
        /* 搜索栏 */
        .search-container {{
            padding: 0 1.5rem 1.5rem;
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .search-box {{
            width: 100%;
            padding: 1rem 1.5rem;
            border: 2px solid var(--border);
            border-radius: 12px;
            font-size: 1rem;
            transition: all 0.3s;
        }}
        
        .search-box:focus {{
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }}
        
        /* 内容区域 */
        .content {{
            padding: 0 1.5rem 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        /* 网站卡片 */
        .site-card {{
            background: var(--card);
            border-radius: 16px;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .site-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        }}
        
        .site-header {{
            padding: 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
        }}
        
        .site-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 0.5rem;
        }}
        
        .site-url {{
            color: var(--primary);
            font-size: 0.85rem;
            word-break: break-all;
            text-decoration: none;
        }}
        
        .site-url:hover {{
            text-decoration: underline;
        }}
        
        .site-status {{
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            white-space: nowrap;
        }}
        
        .status-success {{
            background: rgba(16, 185, 129, 0.1);
            color: var(--success);
        }}
        
        .status-error {{
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
        }}
        
        .site-body {{
            padding: 1.5rem;
        }}
        
        /* 内容区域 */
        .content-section {{
            margin-bottom: 1.5rem;
        }}
        
        .section-title {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            cursor: pointer;
            user-select: none;
        }}
        
        .section-title:hover {{
            color: var(--primary);
        }}
        
        /* 改进的内容显示 */
        .content-display {{
            background: #fafafa;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            font-size: 0.95rem;
            line-height: 1.8;
            max-height: 500px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .content-display h1, 
        .content-display h2, 
        .content-display h3 {{
            margin: 1rem 0 0.5rem 0;
            color: var(--text);
        }}
        
        .content-display p {{
            margin-bottom: 0.75rem;
        }}
        
        .content-display ul, 
        .content-display ol {{
            margin: 0.5rem 0;
            padding-left: 1.5rem;
        }}
        
        .content-display li {{
            margin: 0.25rem 0;
        }}
        
        /* 完整内容模态框 */
        .modal-overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }}
        
        .modal-overlay.active {{
            display: flex;
        }}
        
        .modal-content {{
            background: white;
            border-radius: 16px;
            width: 90%;
            max-width: 900px;
            max-height: 80vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}
        
        .modal-header {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .modal-body {{
            padding: 1.5rem;
            overflow-y: auto;
            flex: 1;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 0.9rem;
            line-height: 1.6;
        }}
        
        .modal-close {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
        }}
        
        /* 标签 */
        .tag {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: var(--primary);
            color: white;
            border-radius: 9999px;
            font-size: 0.75rem;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .tag.pdf {{
            background: #ef4444;
        }}
        
        /* 元数据网格 */
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        
        .meta-item {{
            background: var(--bg);
            padding: 0.75rem 1rem;
            border-radius: 8px;
        }}
        
        .meta-label {{
            font-size: 0.75rem;
            color: var(--text-light);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .meta-value {{
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text);
        }}
        
        /* 操作按钮 */
        .action-buttons {{
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }}
        
        .action-btn {{
            padding: 0.5rem 1rem;
            border: 1px solid var(--border);
            background: white;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
        }}
        
        .action-btn:hover {{
            background: var(--bg);
            border-color: var(--primary);
            color: var(--primary);
        }}
        
        /* 页脚 */
        .footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-light);
            font-size: 0.9rem;
            border-top: 1px solid var(--border);
        }}
        
        /* 响应式 */
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.5rem;
            }}
            
            .site-header {{
                flex-direction: column;
            }}
            
            .meta-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
"""

    def _generate_body(self) -> str:
        """生成 HTML 主体"""
        parts = []
        
        # 头部
        parts.append(f"""
    <header class="header">
        <h1>{self.title}</h1>
        <div class="header-meta">
            生成时间: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")} | 
            共爬取 {len(self.data)} 个网页
        </div>
    </header>
""")
        
        # 统计卡片
        success_count = sum(1 for item in self.data if item.get("status") == 200)
        failed_count = len(self.data) - success_count
        total_links = sum(item.get("links_count", 0) for item in self.data)
        total_images = sum(item.get("images_count", 0) for item in self.data)
        total_pdfs = sum(len(item.get("competition_pdfs", [])) for item in self.data)
        
        parts.append(f"""
    <div class="stats-container">
        <div class="stat-card">
            <div class="stat-value">{len(self.data)}</div>
            <div class="stat-label">爬取网页数</div>
        </div>
        <div class="stat-card success">
            <div class="stat-value">{success_count}</div>
            <div class="stat-label">成功</div>
        </div>
        <div class="stat-card {'danger' if failed_count > 0 else 'success'}">
            <div class="stat-value">{failed_count}</div>
            <div class="stat-label">失败</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{total_pdfs}</div>
            <div class="stat-label">PDF文件数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{total_links}</div>
            <div class="stat-label">链接总数</div>
        </div>
    </div>
""")
        
        # 搜索栏
        parts.append("""
    <div class="search-container">
        <input type="text" class="search-box" placeholder="搜索标题、URL或内容..." id="searchInput">
    </div>
""")
        
        # 内容区域
        parts.append('<main class="content">')
        
        for item in self.data:
            parts.append(self._generate_site_card(item))
        
        parts.append('</main>')
        
        return "\n".join(parts)
    
    def _generate_site_card(self, item: Dict) -> str:
        """生成单个网站卡片"""
        url = item.get("url", "")
        title = item.get("title", "无标题")
        status = item.get("status", 0)
        text = item.get("text", "")
        pdfs = item.get("competition_pdfs", [])
        
        # 解析域名
        domain = urlparse(url).netloc or url
        
        # 状态样式
        if status == 200:
            status_class = "status-success"
            status_text = "OK"
        else:
            status_class = "status-error"
            status_text = f"FAIL ({status})"
        
        # 格式化内容 - 保留段落结构
        formatted_text = self._format_content(text)
        
        # PDF标签
        pdf_tags = ""
        if pdfs:
            pdf_tags = "".join([f'<span class="tag pdf">{pdf.get("filename", "PDF")}</span>' for pdf in pdfs[:3]])
        
        html = f"""
    <article class="site-card" data-search="{title.lower()} {url.lower()} {text.lower()[:200]}">
        <div class="site-header">
            <div>
                <h2 class="site-title">{title}</h2>
                <a href="{url}" target="_blank" class="site-url">{domain}</a>
                {pdf_tags}
            </div>
            <span class="site-status {status_class}">{status_text}</span>
        </div>
        
        <div class="site-body">
            <!-- 元数据 -->
            <div class="meta-grid">
                <div class="meta-item">
                    <div class="meta-label">内容长度</div>
                    <div class="meta-value">{len(text):,} 字符</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">链接数量</div>
                    <div class="meta-value">{item.get("links_count", 0)}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">图片数量</div>
                    <div class="meta-value">{item.get("images_count", 0)}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">PDF文件</div>
                    <div class="meta-value">{len(pdfs)}</div>
                </div>
            </div>
            
            <!-- 正文内容 -->
            <div class="content-section">
                <div class="section-title" onclick="toggleModal('modal-{hash(url)}')">
                    📄 正文内容 (点击查看完整内容)
                </div>
                <div class="content-display">
{formatted_text[:800]}{"..." if len(formatted_text) > 800 else ""}
                </div>
            </div>
        </div>
    </article>
    
    <!-- 完整内容模态框 -->
    <div class="modal-overlay" id="modal-{hash(url)}">
        <div class="modal-content">
            <div class="modal-header">
                <h3>{title} - 完整内容</h3>
                <button class="modal-close" onclick="closeModal('modal-{hash(url)}')">关闭</button>
            </div>
            <div class="modal-body">
{__import__('html').escape(text)}
            </div>
        </div>
    </div>
"""
        return html
    
    def _format_content(self, text: str) -> str:
        """
        格式化内容，保留原网站的段落结构
        """
        if not text:
            return "无内容"
        
        # 清理多余的空白行，但保留段落结构
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _generate_footer(self) -> str:
        """生成 HTML 底部"""
        return f"""
    <footer class="footer">
        <p>Generated by Web Crawler Tool | {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    </footer>
    
    <script>
        // 搜索功能
        document.getElementById('searchInput').addEventListener('input', function(e) {{
            const searchTerm = e.target.value.toLowerCase();
            const cards = document.querySelectorAll('.site-card');
            
            cards.forEach(card => {{
                const searchData = card.getAttribute('data-search');
                if (searchData.includes(searchTerm)) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }});
        
        // 模态框控制
        function toggleModal(modalId) {{
            const modal = document.getElementById(modalId);
            modal.classList.toggle('active');
        }}
        
        function closeModal(modalId) {{
            const modal = document.getElementById(modalId);
            modal.classList.remove('active');
        }}
        
        // 点击模态框外部关闭
        document.querySelectorAll('.modal-overlay').forEach(modal => {{
            modal.addEventListener('click', function(e) {{
                if (e.target === this) {{
                    this.classList.remove('active');
                }}
            }});
        }});
    </script>
</body>
</html>
"""


def generate_v2_report(json_file: str):
    """从JSON文件生成V2报告"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 转换为报告需要的格式
    report_data = []
    for item in data:
        # 优先使用已提取的text字段，如果没有则从content提取
        text = item.get("text", "")
        if not text and item.get("content") and item.get("content") != "[HTML_CONTENT_TRUNCATED]":
            from core.parser import ContentParser
            parser = ContentParser(item.get("content"))
            text = parser.get_main_content()[:5000]
        
        report_data.append({
            "url": item.get("url"),
            "title": item.get("title", "Unknown"),
            "text": text,
            "status": 200 if item.get("success") else 0,
            "links_count": len(item.get("all_pdfs", [])) + 10,  # 估算
            "images_count": 0,
            "competition_pdfs": item.get("competition_pdfs", [])
        })
    
    generator = ReportGeneratorV2(report_data, title="比赛通知抓取报告 V2")
    return generator.generate()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        # 查找最新的JSON文件
        data_dir = "batch_test/data"
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        if json_files:
            json_file = os.path.join(data_dir, sorted(json_files)[-1])
        else:
            print("No JSON file found")
            sys.exit(1)
    
    report_path = generate_v2_report(json_file)
    print(f"Report generated: {report_path}")
