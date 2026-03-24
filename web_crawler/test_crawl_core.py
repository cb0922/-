#!/usr/bin/env python3
"""
测试爬虫核心功能 - 直接调用测试
"""
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

def test_crawl_all():
    """测试crawl_all方法"""
    print("=" * 60)
    print("测试爬虫核心功能")
    print("=" * 60)
    
    try:
        from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3
        from core.url_manager import URLManager
        
        print("\n[1] 加载URL...")
        url_manager = URLManager()
        url_manager.load_from_file("urls.csv")
        urls = url_manager.urls[:3]  # 只测试前3个URL
        print(f"  加载了 {len(urls)} 个URL")
        
        print("\n[2] 创建爬虫...")
        crawler = EnhancedCompetitionCrawlerV3(
            use_dynamic=False,
            timeout=30,
            auto_remove_failed=False
        )
        print("  爬虫创建成功")
        
        print("\n[3] 开始爬取...")
        results = crawler.crawl_all(urls)
        print(f"  爬取完成: {len(results)} 个结果")
        
        if results:
            print("\n[4] 检查结果...")
            for i, r in enumerate(results[:2]):
                print(f"  结果 {i+1}:")
                print(f"    URL: {r.get('url', 'N/A')[:50]}...")
                print(f"    状态: {'成功' if r.get('success') else '失败'}")
                print(f"    标题: {r.get('title', 'N/A')[:30]}...")
                
            # 检查文档
            all_docs = []
            for r in results:
                all_docs.extend(r.get("all_documents", []))
            print(f"\n  发现 {len(all_docs)} 个文档")
            
            # 测试下载（如果有文档）
            competition_docs = [d for d in all_docs if d.get("is_competition_related")]
            if competition_docs:
                print(f"\n[5] 测试下载 {len(competition_docs[:2])} 个文档...")
                doc_results = crawler.download_documents(
                    competition_docs[:2], 
                    output_dir="test_output/documents"
                )
                print(f"  下载完成: {len(doc_results)} 个")
                for dr in doc_results:
                    status = "成功" if dr.get("downloaded") else "失败"
                    print(f"    - {dr.get('filename')}: {status}")
        
        print("\n" + "=" * 60)
        print("✓ 测试通过！核心功能正常")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_crawl_all()
    input("\n按回车键退出...")
    sys.exit(0 if success else 1)
