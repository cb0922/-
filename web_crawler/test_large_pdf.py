#!/usr/bin/env python3
"""
大PDF文件下载测试
"""
import asyncio
import sys
import os
import aiohttp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.pdf_handler import PDFHandler


async def test_large_pdf_download():
    """测试大PDF下载"""
    print("=" * 70)
    print("大PDF文件下载测试")
    print("=" * 70)
    
    # 测试用的大PDF链接（示例）
    # 注意：这里使用一个小文件来测试，实际使用时可替换为大文件
    test_pdfs = [
        {
            "url": "https://wkds.zhyww.cn/wkds6/images/game9/wkds9new.pdf",
            "filename": "测试_大文件下载.pdf",
            "link_text": "测试大文件下载",
            "context": "测试"
        }
    ]
    
    print("\n测试PDF信息:")
    for pdf in test_pdfs:
        print(f"  文件名: {pdf['filename']}")
        print(f"  URL: {pdf['url'][:60]}...")
    
    handler = PDFHandler(timeout=300)  # 5分钟超时
    
    print("\n开始下载测试...")
    print("观察点：")
    print("  1. 是否显示文件大小")
    print("  2. 是否显示下载进度（每5MB）")
    print("  3. 是否成功完成\n")
    
    results = await handler.download_all_pdfs(
        test_pdfs, 
        subdir="test_large",
        concurrency=1
    )
    
    print("\n" + "=" * 70)
    print("测试结果:")
    for r in results:
        print(f"  状态: {r['status']}")
        if r['status'] == 'downloaded':
            size_mb = r.get('size', 0) / (1024 * 1024)
            print(f"  大小: {size_mb:.2f} MB")
            print(f"  路径: {r.get('filepath', 'N/A')}")
        elif r['status'] == 'error':
            print(f"  错误: {r.get('error', 'Unknown')}")
    print("=" * 70)


def main():
    """主函数"""
    try:
        asyncio.run(test_large_pdf_download())
    except RuntimeError:
        # 如果已经在事件循环中
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.run(test_large_pdf_download())


if __name__ == "__main__":
    main()
