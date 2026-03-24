#!/usr/bin/env python3
"""
PDF提取测试脚本
用于诊断PDF链接提取问题
"""
import sys
sys.path.insert(0, __file__.rsplit('\\', 1)[0] if '\\' in __file__ else '.')

from core.pdf_handler import PDFHandler

def test_pdf_extraction():
    """测试PDF提取功能"""
    print("=" * 70)
    print("PDF提取功能诊断测试")
    print("=" * 70)
    
    handler = PDFHandler()
    
    # 测试HTML样本
    test_cases = [
        {
            "name": "大赛通知页面",
            "html": """
            <html>
            <head><title>第九届全国语文微课大赛通知</title></head>
            <body>
                <h1>第九届全国语文微课大赛</h1>
                <p>欢迎参加比赛，请下载附件：</p>
                <a href="/uploads/2024/01/notice.pdf">比赛通知.pdf</a>
                <a href="/files/rules.pdf">参赛规则</a>
                <a href="/download/form.docx">报名表.docx</a>
            </body>
            </html>
            """,
            "url": "http://example.com/contest/2024/"
        },
        {
            "name": "评职通知页面",
            "html": """
            <html>
            <head><title>2024年教师职称评审通知</title></head>
            <body>
                <h1>职称评审文件</h1>
                <a href="http://example.com/docs/pingzhi.pdf">下载评审标准</a>
            </body>
            </html>
            """,
            "url": "http://example.com/notice/2024/"
        },
        {
            "name": "普通页面（无PDF）",
            "html": """
            <html>
            <head><title>学校新闻</title></head>
            <body>
                <h1>校园新闻</h1>
                <a href="/news/1.html">查看详情</a>
            </body>
            </html>
            """,
            "url": "http://example.com/news/"
        }
    ]
    
    print(f"\n关键词列表: {handler.COMPETITION_KEYWORDS}")
    print("\n" + "-" * 70)
    
    for case in test_cases:
        print(f"\n测试: {case['name']}")
        print(f"URL: {case['url']}")
        
        # 从HTML中提取标题
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(case['html'], 'lxml')
        title = soup.title.string if soup.title else ""
        print(f"标题: {title}")
        
        # 提取PDF
        pdfs = handler.extract_pdf_links(case['html'], case['url'], title)
        
        print(f"发现 {len(pdfs)} 个PDF链接:")
        for pdf in pdfs:
            status = "相关" if pdf['is_competition_related'] else "非相关"
            print(f"  - {pdf['filename']}")
            print(f"    URL: {pdf['url'][:50]}...")
            print(f"    链接文本: '{pdf['link_text']}'")
            print(f"    状态: {status}")
        
        print("-" * 70)
    
    print("\n测试完成！")
    print("如果测试显示PDF被标记为'非相关'，检查：")
    print("1. 页面标题是否包含关键词")
    print("2. PDF链接文本是否包含关键词")
    print("3. 关键词列表是否覆盖该类型活动")

if __name__ == "__main__":
    test_pdf_extraction()
