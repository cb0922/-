#!/usr/bin/env python3
"""
手动下载辅助工具
为下载失败的PDF提供手动下载指导
"""
import json
import webbrowser
import os


def show_manual_download_guide():
    """显示手动下载指南"""
    
    failed_pdfs = [
        {
            "name": "全国教育创新科研成果大赛通知",
            "status": "404 - 文件不存在",
            "website": "http://chengguodasai.com/",
            "guide": """
【下载步骤】
1. 访问官网: http://chengguodasai.com/
2. 在首页或"通知公告"栏目查找最新的大赛通知
3. 点击PDF下载链接（注意：原链接已失效，可能有新的文件链接）
4. 建议文件名: 全国教育创新科研成果大赛通知.pdf
            """,
            "alternative": "联系网站管理员获取最新通知文件"
        },
        {
            "name": "学科网-全国中小学优秀教学课例大赛",
            "status": "JavaScript保护",
            "website": "https://yx.xkw.com/hd/2026jxklds/",
            "guide": """
【下载步骤】
1. 访问页面: https://yx.xkw.com/hd/2026jxklds/
2. 在页面上找到"下载"或"参赛规则"按钮
3. 点击下载PDF文件
4. 建议文件名: 全国中小学优秀教学课例大赛通知.pdf
            """,
            "alternative": "使用浏览器开发者工具(F12) -> Network -> 找到PDF请求 -> 复制URL"
        }
    ]
    
    print("=" * 70)
    print("          PDF手动下载辅助工具")
    print("=" * 70)
    print("\n有2个PDF需要手动下载：\n")
    
    for i, pdf in enumerate(failed_pdfs, 1):
        print(f"{i}. {pdf['name']}")
        print(f"   状态: {pdf['status']}")
        print(f"   官网: {pdf['website']}")
        print(pdf['guide'])
        print(f"   备选方案: {pdf['alternative']}")
        print()
    
    print("=" * 70)
    print("是否自动打开下载页面？(y/n): ")
    response = input().strip().lower()
    
    if response == 'y':
        print("\n正在打开浏览器...")
        for pdf in failed_pdfs:
            webbrowser.open(pdf['website'])
        print("已打开所有页面，请按上述步骤手动下载PDF")
    
    # 保存指南到文件
    guide_file = "pdfs/enhanced/download_guide.txt"
    os.makedirs(os.path.dirname(guide_file), exist_ok=True)
    
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write("PDF手动下载指南\n")
        f.write("=" * 70 + "\n\n")
        for pdf in failed_pdfs:
            f.write(f"【{pdf['name']}】\n")
            f.write(f"状态: {pdf['status']}\n")
            f.write(f"官网: {pdf['website']}\n")
            f.write(pdf['guide'] + "\n")
            f.write("-" * 70 + "\n\n")
    
    print(f"\n下载指南已保存到: {guide_file}")


if __name__ == "__main__":
    show_manual_download_guide()
