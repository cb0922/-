#!/usr/bin/env python3
"""
测试多格式文档处理器
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.document_handler import DocumentHandler


def test_document_detection():
    """测试文档类型检测"""
    print("\n[测试1] 文档类型检测")
    
    handler = DocumentHandler()
    
    test_cases = [
        ("通知.pdf", "PDF"),
        ("比赛方案.docx", "Word"),
        ("报名表.xls", "Excel"),
        ("获奖名单.xlsx", "Excel"),
        ("演示.pptx", "PowerPoint"),
        ("附件.zip", "Archive"),
        ("资料.rar", "Archive"),
        ("readme.txt", "Text"),
        ("unknown.xyz", "Other"),
    ]
    
    for filename, expected in test_cases:
        doc_type = handler.get_document_type(filename)
        status = "OK" if doc_type == expected else "FAIL"
        print(f"  [{status}] {filename} -> {doc_type} (expected: {expected})")


def test_link_detection():
    """测试链接检测"""
    print("\n[测试2] 文档链接检测")
    
    handler = DocumentHandler()
    
    test_urls = [
        "https://example.com/file.pdf",
        "https://example.com/doc.docx",
        "https://example.com/data.xlsx",
        "https://example.com/slide.ppt",
        "https://example.com/archive.zip",
        "https://example.com/page.html",
        "https://example.com/image.jpg",
    ]
    
    for url in test_urls:
        is_doc = handler.is_document_link(url)
        status = "DOC" if is_doc else "NOT DOC"
        print(f"  [{status}] {url}")


def test_filename_cleaning():
    """测试文件名清理"""
    print("\n[测试3] 文件名清理")
    
    handler = DocumentHandler()
    
    test_cases = [
        "关于举办2024年全国师生信息素养提升实践活动（第二十八届教师活动）的通知.pdf",
        "very/long/path/比赛通知<重要>.docx",
        "获奖名单：一等奖.xlsx",
    ]
    
    for filename in test_cases:
        cleaned = handler.clean_filename(filename)
        print(f"  [原始] {filename[:60]}...")
        print(f"  [清理] {cleaned}")
        print()


def test_extraction():
    """测试从HTML中提取文档链接"""
    print("\n[测试4] HTML文档链接提取")
    
    html = '''
    <html>
    <body>
        <h1>比赛通知</h1>
        <a href="/files/比赛通知.pdf">下载PDF通知</a>
        <a href="/files/报名表.docx">下载Word报名表</a>
        <a href="/files/获奖名单.xlsx">下载Excel名单</a>
        <a href="/files/演示PPT.pptx">下载PPT</a>
        <a href="/files/附件.zip">下载附件</a>
        <a href="/page.html">普通页面</a>
    </body>
    </html>
    '''
    
    handler = DocumentHandler()
    documents = handler.extract_document_links(html, "https://example.com", "比赛通知")
    
    print(f"  找到 {len(documents)} 个文档:")
    for doc in documents:
        print(f"    - {doc['filename']} ({doc['doc_type']}) "
              f"[比赛相关: {doc['is_competition_related']}]")


def main():
    print("=" * 60)
    print("    多格式文档处理器测试")
    print("=" * 60)
    
    test_document_detection()
    test_link_detection()
    test_filename_cleaning()
    test_extraction()
    
    print("\n" + "=" * 60)
    print("    所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
