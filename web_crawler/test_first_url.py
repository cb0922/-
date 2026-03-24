#!/usr/bin/env python3
"""测试第一个URL"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_first_url():
    # 读取第一个URL
    if not os.path.exists("urls.csv"):
        print("Error: urls.csv not found")
        return
    
    with open("urls.csv", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    if len(lines) < 2:
        print("Error: No URLs in file")
        return
    
    # 获取第一个URL
    first_line = lines[1].strip()
    url = first_line.split(",")[0]
    
    print(f"Testing first URL: {url}")
    print("-" * 60)
    
    # 导入并测试
    try:
        from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3
        
        crawler = EnhancedCompetitionCrawlerV3(
            urls_file="urls.csv",
            auto_remove_failed=False,
            timeout=15
        )
        
        async def run_test():
            result = await crawler.crawl_single({"url": url})
            return result
        
        result = asyncio.run(run_test())
        
        if result:
            if result.get("removed"):
                print(f"Result: URL marked for removal")
            elif result.get("success"):
                print(f"Success! Title: {result.get('title', 'N/A')[:50]}")
                docs = result.get("all_documents", [])
                print(f"Documents found: {len(docs)}")
            else:
                print(f"Failed: {result.get('error', 'Unknown error')}")
        else:
            print("Result: None (failed but not removed)")
            
    except Exception as e:
        print(f"CRASH: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_first_url()
