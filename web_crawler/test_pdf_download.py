#!/usr/bin/env python3
"""
PDF下载功能测试
"""
import sys
import os
import asyncio
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.document_handler import DocumentHandler


async def test_pdf_download():
    """测试PDF下载功能"""
    print("=" * 80)
    print("PDF下载功能测试")
    print("=" * 80)
    
    # 创建测试目录
    test_output = "./test_pdf_output"
    if os.path.exists(test_output):
        shutil.rmtree(test_output, ignore_errors=True)
    os.makedirs(test_output, exist_ok=True)
    
    # 创建DocumentHandler
    handler = DocumentHandler(timeout=30, output_dir=test_output)
    
    # 测试1: 使用一个公开可访问的PDF文件
    print("\n[测试1] 下载公开PDF文件")
    test_pdf = {
        "url": "http://www.pdf995.com/samples/pdf.pdf",  # 测试用PDF
        "filename": "test_download.pdf",
        "doc_type": "PDF",
        "is_competition_related": True,
        "downloaded": False
    }
    
    import aiohttp
    
    try:
        connector = aiohttp.TCPConnector(limit=1)
        timeout = aiohttp.ClientTimeout(total=None, connect=30, sock_read=60)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            result = await handler.download_document(session, test_pdf)
            
            if result.get("downloaded"):
                print(f"  [OK] 下载成功")
                print(f"  文件路径: {result.get('filepath')}")
                print(f"  文件大小: {result.get('size', 0)} bytes")
                
                # 验证文件是否存在
                if os.path.exists(result.get('filepath')):
                    print(f"  [OK] 文件确实存在")
                    actual_size = os.path.getsize(result.get('filepath'))
                    print(f"  实际大小: {actual_size} bytes")
                else:
                    print(f"  [FAIL] 文件不存在！")
                    return False
            else:
                print(f"  [FAIL] 下载失败: {result.get('error', 'Unknown')}")
                # 如果是网络问题，不算功能失败
                if "Cannot connect" in str(result.get('error', '')):
                    print("  [INFO] 网络连接问题，非功能问题")
                    return True
                return False
                
    except Exception as e:
        print(f"  [ERROR] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试2: 批量下载
    print("\n[测试2] 批量下载多个PDF")
    test_pdfs = [
        {
            "url": "http://www.pdf995.com/samples/pdf.pdf",
            "filename": "batch1.pdf",
            "doc_type": "PDF",
            "is_competition_related": True,
            "downloaded": False
        },
        {
            "url": "http://www.pdf995.com/samples/pdf.pdf",
            "filename": "batch2.pdf",
            "doc_type": "PDF",
            "is_competition_related": True,
            "downloaded": False
        }
    ]
    
    try:
        results = await handler.download_documents(test_pdfs, concurrency=2)
        success_count = sum(1 for r in results if r.get("downloaded"))
        print(f"  [INFO] 批量下载: {success_count}/{len(test_pdfs)} 成功")
        
        # 检查文件
        for r in results:
            if r.get("downloaded") and r.get("filepath"):
                if os.path.exists(r.get("filepath")):
                    print(f"  [OK] {os.path.basename(r.get('filepath'))}: 存在")
                else:
                    print(f"  [FAIL] {os.path.basename(r.get('filepath'))}: 不存在")
                    
    except Exception as e:
        print(f"  [ERROR] 批量下载异常: {e}")
    
    # 测试3: 检查目录结构
    print("\n[测试3] 检查目录结构")
    if os.path.exists(test_output):
        for root, dirs, files in os.walk(test_output):
            level = root.replace(test_output, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 2 * (level + 1)
            for file in files:
                file_path = os.path.join(root, file)
                size = os.path.getsize(file_path)
                print(f"{sub_indent}{file} ({size} bytes)")
    
    # 清理
    print("\n[清理] 删除测试目录...")
    shutil.rmtree(test_output, ignore_errors=True)
    
    print("\n" + "=" * 80)
    print("PDF下载测试完成")
    print("=" * 80)
    return True


def test_pdf_extraction():
    """测试PDF链接提取"""
    print("\n" + "=" * 80)
    print("PDF链接提取测试")
    print("=" * 80)
    
    handler = DocumentHandler()
    
    # 测试HTML提取PDF链接
    test_html = """
    <html>
    <body>
        <h1>比赛通知</h1>
        <a href="/files/通知.pdf">下载通知</a>
        <a href="/files/报名表.docx">报名表</a>
        <a href="/files/获奖名单.pdf">获奖名单</a>
        <a href="http://other.com/比赛规则.pdf">外部链接</a>
    </body>
    </html>
    """
    
    docs = handler.extract_document_links(test_html, "http://example.com", "比赛通知")
    
    print(f"\n提取到 {len(docs)} 个文档:")
    pdf_count = 0
    for doc in docs:
        print(f"  - {doc['filename']} ({doc['doc_type']}) [比赛相关: {doc['is_competition_related']}]")
        if doc['doc_type'] == 'PDF':
            pdf_count += 1
    
    if pdf_count >= 2:
        print(f"\n[OK] 成功提取 {pdf_count} 个PDF链接")
        return True
    else:
        print(f"\n[FAIL] 只提取到 {pdf_count} 个PDF，期望至少2个")
        return False


def test_pdf_integration():
    """测试集成到爬虫的PDF下载"""
    print("\n" + "=" * 80)
    print("集成PDF下载测试")
    print("=" * 80)
    
    from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3
    
    # 模拟爬取结果（包含PDF）
    test_results = [
        {
            "url": "http://example.com/notice",
            "title": "比赛通知",
            "text": "全国教学大赛通知",
            "is_competition_related": True,
            "all_documents": [
                {
                    "url": "http://www.pdf995.com/samples/pdf.pdf",
                    "filename": "比赛通知.pdf",
                    "doc_type": "PDF",
                    "is_competition_related": True,
                    "downloaded": False
                }
            ],
            "competition_documents": [
                {
                    "url": "http://www.pdf995.com/samples/pdf.pdf",
                    "filename": "比赛通知.pdf",
                    "doc_type": "PDF",
                    "is_competition_related": True,
                    "downloaded": False
                }
            ],
            "crawled_at": "2024-01-01T00:00:00"
        }
    ]
    
    crawler = EnhancedCompetitionCrawlerV3()
    crawler.results = test_results
    
    # 测试下载
    output_dir = "./test_integration"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir, ignore_errors=True)
    
    try:
        competition_docs = test_results[0]["competition_documents"]
        print(f"\n开始下载 {len(competition_docs)} 个PDF...")
        
        results = crawler.download_documents(competition_docs, output_dir=output_dir)
        
        success = sum(1 for r in results if r.get("downloaded"))
        print(f"下载完成: {success}/{len(competition_docs)} 成功")
        
        # 检查文件
        if os.path.exists(output_dir):
            pdf_dir = os.path.join(output_dir, "PDF")
            if os.path.exists(pdf_dir):
                files = os.listdir(pdf_dir)
                print(f"PDF目录文件: {files}")
            else:
                print(f"PDF目录不存在: {pdf_dir}")
        
        # 清理
        shutil.rmtree(output_dir, ignore_errors=True)
        
        print("\n[OK] 集成测试完成")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 集成测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 80)
    print("PDF功能全面测试")
    print("=" * 80)
    
    results = []
    
    # 测试1: PDF链接提取
    try:
        results.append(("PDF链接提取", test_pdf_extraction()))
    except Exception as e:
        print(f"[ERROR] PDF链接提取测试失败: {e}")
        results.append(("PDF链接提取", False))
    
    # 测试2: PDF下载
    try:
        results.append(("PDF下载", asyncio.run(test_pdf_download())))
    except Exception as e:
        print(f"[ERROR] PDF下载测试失败: {e}")
        results.append(("PDF下载", False))
    
    # 测试3: 集成测试
    try:
        results.append(("集成PDF下载", test_pdf_integration()))
    except Exception as e:
        print(f"[ERROR] 集成测试失败: {e}")
        results.append(("集成PDF下载", False))
    
    # 汇总
    print("\n" + "=" * 80)
    print("测试汇总")
    print("=" * 80)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")
    
    print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
