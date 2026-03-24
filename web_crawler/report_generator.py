#!/usr/bin/env python3
"""
可视化报告生成器
将爬取的机器数据转换为美观、易读的交互式 HTML 报告
"""
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse


class ReportGenerator:
    """HTML 报告生成器"""
    
    def __init__(self, data: List[Dict], title: str = "网页爬取报告", output_dir: str = None):
        self.data = data
        self.title = title
        if output_dir:
            self.output_dir = output_dir
        else:
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
        filename = f"report_{timestamp}.html"
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
        
        /* 摘要区域 */
        .summary {{
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-left: 4px solid var(--primary);
            padding: 1rem 1.25rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
        }}
        
        .summary-title {{
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .summary-text {{
            color: var(--text);
            line-height: 1.8;
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
        }}
        
        .section-content {{
            background: var(--bg);
            padding: 1rem;
            border-radius: 8px;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 0.9rem;
            line-height: 1.8;
        }}
        
        .section-content::-webkit-scrollbar {{
            width: 8px;
        }}
        
        .section-content::-webkit-scrollbar-track {{
            background: var(--border);
            border-radius: 4px;
        }}
        
        .section-content::-webkit-scrollbar-thumb {{
            background: var(--secondary);
            border-radius: 4px;
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
        
        .tag.secondary {{
            background: var(--secondary);
        }}
        
        /* 图片网格 */
        .image-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 0.75rem;
        }}
        
        .image-item {{
            aspect-ratio: 16/9;
            background: var(--bg);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-light);
            font-size: 0.8rem;
        }}
        
        /* 空状态 */
        .empty-state {{
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-light);
        }}
        
        .empty-icon {{
            font-size: 4rem;
            margin-bottom: 1rem;
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
        
        /* 折叠/展开 */
        .collapsible {{
            cursor: pointer;
            user-select: none;
        }}
        
        .collapsible::after {{
            content: '▼';
            margin-left: 0.5rem;
            transition: transform 0.2s;
        }}
        
        .collapsible.collapsed::after {{
            transform: rotate(-90deg);
        }}
        
        .collapsible-content {{
            transition: max-height 0.3s ease-out;
        }}
        
        .collapsible-content.hidden {{
            display: none;
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
            <div class="stat-value">{total_links}</div>
            <div class="stat-label">链接总数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{total_images}</div>
            <div class="stat-label">图片总数</div>
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
        
        # 解析域名
        domain = urlparse(url).netloc or url
        
        # 生成自然语言摘要
        summary = self._generate_summary(item)
        
        # 状态样式
        if status == 200:
            status_class = "status-success"
            status_text = "✓ 成功"
        else:
            status_class = "status-error"
            status_text = f"✗ 失败 ({status})"
        
        # 截断文本
        text_preview = text[:500] + "..." if len(text) > 500 else text
        
        # 关键词提取（简单的）
        keywords = self._extract_keywords(text)
        
        html = f"""
    <article class="site-card" data-search="{title.lower()} {url.lower()} {text.lower()[:200]}">
        <div class="site-header">
            <div>
                <h2 class="site-title">{title}</h2>
                <a href="{url}" target="_blank" class="site-url">{domain}</a>
            </div>
            <span class="site-status {status_class}">{status_text}</span>
        </div>
        
        <div class="site-body">
            <!-- 智能摘要 -->
            <div class="summary">
                <div class="summary-title">📝 内容摘要</div>
                <div class="summary-text">{summary}</div>
            </div>
            
            <!-- 元数据 -->
            <div class="meta-grid">
                <div class="meta-item">
                    <div class="meta-label">链接数量</div>
                    <div class="meta-value">{item.get("links_count", 0)}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">图片数量</div>
                    <div class="meta-value">{item.get("images_count", 0)}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">内容长度</div>
                    <div class="meta-value">{len(text)} 字符</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">HTTP状态</div>
                    <div class="meta-value">{status}</div>
                </div>
            </div>
            
            <!-- 关键词 -->
            <div class="content-section">
                <h3 class="section-title">🏷️ 关键词</h3>
                <div>
                    {''.join(f'<span class="tag">{kw}</span>' for kw in keywords[:8]) if keywords else '<span style="color: var(--text-light);">未识别到关键词</span>'}
                </div>
            </div>
            
            <!-- 正文内容 -->
            <div class="content-section">
                <h3 class="section-title collapsible" onclick="toggleContent(this)">📄 正文内容</h3>
                <div class="section-content">{text_preview or '无内容'}</div>
            </div>
        </div>
    </article>
"""
        return html
    
    def _generate_summary(self, item: Dict) -> str:
        """生成自然语言摘要"""
        title = item.get("title", "")
        text = item.get("text", "")
        url = item.get("url", "")
        links_count = item.get("links_count", 0)
        images_count = item.get("images_count", 0)
        status = item.get("status", 0)
        
        if status != 200:
            return f"该网页爬取失败（HTTP {status}），可能由于网站反爬虫机制、访问权限限制或网络问题导致无法获取内容。"
        
        # 根据内容类型生成不同摘要
        domain = urlparse(url).netloc
        
        summary_parts = []
        
        # 网站类型识别
        if "wkds" in domain or "zhyww" in domain:
            site_type = "教育赛事平台"
        elif "ncet" in domain or "edu" in domain:
            site_type = "教育部官方网站"
        elif "qq" in domain or "aiteach" in domain:
            site_type = "腾讯教育平台"
        else:
            site_type = "网站"
        
        summary_parts.append(f"这是一个{site_type}，标题为《{title}》。")
        
        # 内容长度
        text_len = len(text)
        if text_len > 1000:
            summary_parts.append(f"页面内容较为丰富，约 {text_len} 字符。")
        elif text_len > 100:
            summary_parts.append(f"页面包含 {text_len} 字符的内容。")
        else:
            summary_parts.append("页面内容较少，可能是动态加载的单页应用。")
        
        # 资源统计
        resources = []
        if links_count > 0:
            resources.append(f"{links_count} 个链接")
        if images_count > 0:
            resources.append(f"{images_count} 张图片")
        
        if resources:
            summary_parts.append(f"页面包含 {', '.join(resources)}。")
        
        # 内容主题推断
        themes = self._detect_themes(text)
        if themes:
            summary_parts.append(f"主要内容涉及：{'、'.join(themes)}。")
        
        return "".join(summary_parts)
    
    def _detect_themes(self, text: str) -> List[str]:
        """检测内容主题"""
        themes = []
        
        theme_keywords = {
            "教育赛事": ["大赛", "比赛", "评选", "征集", "获奖", "报名", "参赛作品"],
            "教学资源": ["教案", "课件", "微课", "视频", "教材", "课程"],
            "教师培训": ["教师", "培训", "研修", "进修", "学习", "提升"],
            "通知公告": ["通知", "公告", "公示", "说明"],
            "数字化教育": ["智慧教育", "数字化", "在线", "平台", "AI", "智能"],
        }
        
        for theme, keywords in theme_keywords.items():
            if any(kw in text for kw in keywords):
                themes.append(theme)
        
        return themes[:3]
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取：找出现频率较高的名词性词汇
        if not text:
            return []
        
        # 常见停用词
        stopwords = set(["的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这", "那"])
        
        # 统计词频
        words = re.findall(r'[\u4e00-\u9fa5]{2,6}', text)
        word_freq = {}
        
        for word in words:
            if word not in stopwords and len(word) >= 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 返回高频词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_n] if freq > 1]
    
    def _generate_footer(self) -> str:
        """生成 HTML 底部"""
        return f"""
    <footer class="footer">
        <p>由 Web Crawler Tool 自动生成 | {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
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
        
        // 折叠/展开功能
        function toggleContent(element) {{
            element.classList.toggle('collapsed');
            const content = element.nextElementSibling;
            content.classList.toggle('hidden');
        }}
    </script>
</body>
</html>
"""


def load_latest_data() -> List[Dict]:
    """加载最新的爬取数据"""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    
    # 找最新的 JSON 文件
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    if not json_files:
        raise FileNotFoundError("未找到数据文件")
    
    latest_file = max(json_files, key=lambda f: os.path.getmtime(os.path.join(data_dir, f)))
    
    with open(os.path.join(data_dir, latest_file), 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """主函数"""
    print("="*50)
    print("Web Crawler Report Generator")
    print("="*50)
    
    try:
        # 加载数据
        print("\n正在加载爬取数据...")
        data = load_latest_data()
        print(f"[OK] Loaded {len(data)} records")
        
        # 生成报告
        print("\n正在生成可视化报告...")
        generator = ReportGenerator(data, title="网页爬取可视化报告")
        report_path = generator.generate()
        
        print(f"\n✓ 报告生成成功!")
        print(f"  文件路径: {report_path}")
        
        # 尝试在浏览器中打开
        import webbrowser
        webbrowser.open(f'file://{os.path.abspath(report_path)}')
        print("\nTrying to open report in browser...")
        
    except Exception as e:
        print(f"\n[ERROR] Generation failed: {str(e)}")


if __name__ == "__main__":
    main()
