#!/usr/bin/env python3
"""
测试流式下载功能
"""
import aiohttp
import asyncio
import os
import time

async def test_streaming_download():
    """测试流式下载"""
    print("=" * 60)
    print("流式下载功能测试")
    print("=" * 60)
    
    # 测试URL（使用一个中等大小的PDF）
    url = "https://wkds.zhyww.cn/wkds6/images/game9/wkds9new.pdf"
    output_file = "test_streaming.pdf"
    
    print(f"\n测试URL: {url}")
    print("开始下载...")
    
    start_time = time.time()
    
    timeout = aiohttp.ClientTimeout(
        total=None,
        connect=30,
        sock_read=60
    )
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, ssl=False) as response:
            if response.status == 200:
                # 获取文件大小
                total_size = response.headers.get('Content-Length')
                if total_size:
                    total_size = int(total_size)
                    print(f"文件大小: {total_size / 1024:.1f} KB")
                
                # 流式下载
                chunk_size = 64 * 1024  # 64KB
                downloaded = 0
                last_print = 0
                
                with open(output_file, 'wb') as f:
                    while True:
                        chunk = await response.content.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 每100KB打印一次
                        if downloaded - last_print >= 100 * 1024:
                            print(f"已下载: {downloaded / 1024:.1f} KB")
                            last_print = downloaded
                
                elapsed = time.time() - start_time
                print(f"\n下载完成!")
                print(f"总大小: {downloaded / 1024:.1f} KB")
                print(f"用时: {elapsed:.2f} 秒")
                print(f"速度: {downloaded / 1024 / elapsed:.1f} KB/s")
                
                # 清理
                os.remove(output_file)
                print(f"已清理测试文件")
                return True
            else:
                print(f"下载失败: HTTP {response.status}")
                return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_streaming_download())
        if result:
            print("\n流式下载功能正常!")
        else:
            print("\n流式下载功能异常!")
    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()
