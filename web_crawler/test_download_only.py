#!/usr/bin/env python3
"""
文档下载功能单独测试
"""
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

import asyncio
from core.document_handler import DocumentHandler

# 测试文档列表（使用一些公共PDF文件进行测试）
test_docs = [
    {
        "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "filename": "test_pdf.pdf",
        "link_text": "Test PDF",
        "page_title": "Test Page",
        "doc_type": "PDF",
        "is_competition_related": True,
        "source_url": "https://example.com"
    }
]

async def test_download():
    """测试下载功能"""
    print("=" * 60)
    print("文档下载功能测试")
    print("=" * 60)
    
    output_dir = "test_download_output"
    print(f"\n输出目录: {output_dir}")
    
    try:
        handler = DocumentHandler(timeout=30, output_dir=output_dir)
        print("✓ DocumentHandler初始化成功")
        
        print("\n开始下载测试文档...")
        results = await handler.download_documents(test_docs, concurrency=1)
        
        print(f"\n结果:")
        for r in results:
            print(f"  - {r['filename']}: {'成功' if r.get('downloaded') else '失败'}")
            if r.get('error'):
                print(f"    错误: {r['error']}")
            if r.get('filepath'):
                print(f"    路径: {r['filepath']}")
                
        # 统计
        success = sum(1 for r in results if r.get('downloaded'))
        print(f"\n总计: {success}/{len(results)} 成功")
        
        if success > 0:
            print("\n✓ 下载功能正常")
        else:
            print("\n✗ 下载功能异常")
            
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        print("\n详细错误:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_download())
    input("\n按回车键退出...")
