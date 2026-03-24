#!/usr/bin/env python3
"""
文档处理器全面测试 - 包括边界情况
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.document_handler import DocumentHandler


def test_competition_detection():
    """测试比赛相关性判断"""
    print("\n[测试] 比赛相关性判断")
    
    handler = DocumentHandler()
    
    test_cases = [
        ("关于举办大赛的通知.pdf", True),
        ("教学计划.docx", False),
        ("获奖名单公布.xlsx", True),
        ("2024年比赛报名表.doc", True),
        ("学校简介.pptx", False),
        ("评审结果公示.pdf", True),
        ("普通文档.txt", False),
        ("竞赛方案最终版.docx", True),
    ]
    
    passed = 0
    for filename, expected in test_cases:
        result = handler.is_competition_related(filename)
        status = "OK" if result == expected else "FAIL"
        if result == expected:
            passed += 1
        print(f"  [{status}] {filename} -> {result} (expected: {expected})")
    
    print(f"  通过率: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_edge_cases():
    """测试边界情况"""
    print("\n[测试] 边界情况处理")
    
    handler = DocumentHandler()
    
    # 测试空内容
    docs = handler.extract_document_links("", "http://example.com", "")
    print(f"  [OK] 空HTML返回 {len(docs)} 个文档")
    
    # 测试无扩展名URL
    is_doc = handler.is_document_link("http://example.com/file")
    print(f"  [OK] 无扩展名URL识别为文档: {is_doc}")
    
    # 测试超长文件名
    long_name = "关于" + "A" * 200 + "大赛的通知.pdf"
    cleaned = handler.clean_filename(long_name)
    print(f"  [OK] 超长文件名清理后长度: {len(cleaned)} (max 80)")
    assert len(cleaned) <= 80, "文件名过长"
    
    # 测试特殊字符
    special = "通知<重要>|?:*\\/\".pdf"
    cleaned = handler.clean_filename(special)
    print(f"  [OK] 特殊字符清理: {cleaned}")
    assert "<" not in cleaned and ">" not in cleaned, "特殊字符未清理"
    
    # 测试URL编码文件名
    encoded = "%E9%80%9A%E7%9F%A5.pdf"  # "通知.pdf" 的URL编码
    cleaned = handler.clean_filename(encoded)
    print(f"  [OK] URL编码解码: {cleaned}")
    
    # 测试无扩展名
    no_ext = handler.get_document_type("readme")
    print(f"  [OK] 无扩展名类型: {no_ext}")
    
    return True


def test_html_extraction_edge_cases():
    """测试HTML提取边界情况"""
    print("\n[测试] HTML提取边界情况")
    
    handler = DocumentHandler()
    
    # HTML中有重复链接
    html_dup = '''
    <a href="/file.pdf">下载1</a>
    <a href="/file.pdf">下载2</a>
    <a href="http://example.com/file.pdf">下载3</a>
    '''
    docs = handler.extract_document_links(html_dup, "http://example.com", "标题")
    print(f"  [OK] 重复链接去重: 找到 {len(docs)} 个 (应为1个)")
    assert len(docs) == 1, "重复链接未去重"
    
    # HTML中无文档链接
    html_no_doc = '''
    <a href="/page.html">页面</a>
    <a href="/image.jpg">图片</a>
    '''
    docs = handler.extract_document_links(html_no_doc, "http://example.com", "标题")
    print(f"  [OK] 无文档链接: 找到 {len(docs)} 个 (应为0个)")
    
    # HTML中有相对路径和绝对路径
    html_mixed = '''
    <a href="/absolute/path/file.pdf">绝对</a>
    <a href="relative/file.docx">相对</a>
    <a href="../parent/file.xlsx">上级</a>
    '''
    docs = handler.extract_document_links(html_mixed, "http://example.com/dir/page.html", "标题")
    print(f"  [OK] 混合路径: 找到 {len(docs)} 个文档")
    for d in docs:
        print(f"      - {d['url']}")
    
    # HTML中有javascript链接
    html_js = '''
    <a href="javascript:download('file.pdf')">JS下载</a>
    <a href="#" onclick="location.href='real.pdf'">点击下载</a>
    '''
    docs = handler.extract_document_links(html_js, "http://example.com", "标题")
    print(f"  [OK] JavaScript链接: 找到 {len(docs)} 个 (应识别onclick)")
    
    return True


def test_all_supported_formats():
    """测试所有支持的格式"""
    print("\n[测试] 所有支持格式")
    
    handler = DocumentHandler()
    
    all_formats = [
        # PDF
        ("file.pdf", "PDF"),
        # Word
        ("file.doc", "Word"), ("file.docx", "Word"), ("file.dot", "Word"),
        ("file.dotx", "Word"), ("file.rtf", "Word"),
        # Excel
        ("file.xls", "Excel"), ("file.xlsx", "Excel"), ("file.xlsm", "Excel"),
        ("file.xlsb", "Excel"), ("file.csv", "Excel"),
        # PowerPoint
        ("file.ppt", "PowerPoint"), ("file.pptx", "PowerPoint"),
        ("file.pps", "PowerPoint"), ("file.ppsx", "PowerPoint"),
        # Archive
        ("file.zip", "Archive"), ("file.rar", "Archive"), ("file.7z", "Archive"),
        ("file.tar", "Archive"), ("file.gz", "Archive"), ("file.bz2", "Archive"),
        # Text
        ("file.txt", "Text"),
        # WPS
        ("file.wps", "WPS"), ("file.et", "WPS"), ("file.dps", "WPS"),
    ]
    
    passed = 0
    for filename, expected in all_formats:
        doc_type = handler.get_document_type(filename)
        if doc_type == expected:
            passed += 1
        else:
            print(f"  [FAIL] {filename} -> {doc_type} (expected: {expected})")
    
    print(f"  [OK] 格式识别: {passed}/{len(all_formats)} 通过")
    return passed == len(all_formats)


def main():
    print("=" * 70)
    print("    文档处理器 - 全面测试")
    print("=" * 70)
    
    results = []
    
    try:
        results.append(("比赛相关性", test_competition_detection()))
    except Exception as e:
        print(f"  [ERROR] 比赛相关性测试失败: {e}")
        results.append(("比赛相关性", False))
    
    try:
        results.append(("边界情况", test_edge_cases()))
    except Exception as e:
        print(f"  [ERROR] 边界情况测试失败: {e}")
        results.append(("边界情况", False))
    
    try:
        results.append(("HTML提取边界", test_html_extraction_edge_cases()))
    except Exception as e:
        print(f"  [ERROR] HTML提取边界测试失败: {e}")
        results.append(("HTML提取边界", False))
    
    try:
        results.append(("所有格式", test_all_supported_formats()))
    except Exception as e:
        print(f"  [ERROR] 所有格式测试失败: {e}")
        results.append(("所有格式", False))
    
    print("\n" + "=" * 70)
    print("    测试结果汇总")
    print("=" * 70)
    
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + "=" * 70)
    if all_passed:
        print("    所有测试通过!")
    else:
        print("    有测试失败，请检查!")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
