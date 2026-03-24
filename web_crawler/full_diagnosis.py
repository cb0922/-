#!/usr/bin/env python3
"""
全面诊断脚本 - 检查抓取流程的每个环节
"""
import sys
import os
import asyncio
import csv
import json
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_environment():
    """测试环境"""
    print("=" * 80)
    print("步骤1: 环境检查")
    print("=" * 80)
    
    issues = []
    
    # Python版本
    print(f"\nPython版本: {sys.version}")
    if sys.version_info < (3, 8):
        issues.append("Python版本过低，需要3.8+")
    
    # 检查关键依赖
    print("\n依赖检查:")
    deps = {
        'aiohttp': 'aiohttp',
        'beautifulsoup4': 'bs4',
        'PyQt6': 'PyQt6',
        'python-docx': 'docx',
        'lxml': 'lxml',
    }
    
    for pkg, import_name in deps.items():
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"  ✓ {pkg}: {version}")
        except ImportError as e:
            print(f"  ✗ {pkg}: 未安装 - {e}")
            issues.append(f"缺少依赖: {pkg}")
    
    return issues


def test_file_access():
    """测试文件访问"""
    print("\n" + "=" * 80)
    print("步骤2: 文件访问检查")
    print("=" * 80)
    
    issues = []
    
    # 检查关键文件
    files = [
        'urls.csv',
        'enhanced_crawler_v3.py',
        'core/fetcher.py',
        'core/parser.py',
        'core/document_handler.py',
    ]
    
    print("\n关键文件:")
    for f in files:
        exists = os.path.exists(f)
        status = "✓" if exists else "✗"
        print(f"  {status} {f}")
        if not exists:
            issues.append(f"缺少文件: {f}")
    
    # 检查urls.csv
    print("\nurls.csv 内容检查:")
    if os.path.exists('urls.csv'):
        try:
            with open('urls.csv', 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                print(f"  标题行: {header}")
                
                rows = list(reader)
                print(f"  数据行数: {len(rows)}")
                
                if rows:
                    print(f"  第一行: {rows[0]}")
                    
                    # 检查URL格式
                    for i, row in enumerate(rows[:3], 1):
                        if row:
                            url = row[0]
                            if not url.startswith(('http://', 'https://')):
                                issues.append(f"第{i}行URL格式错误: {url}")
                                print(f"  ✗ 第{i}行URL格式错误")
                            else:
                                print(f"  ✓ 第{i}行URL格式正确")
        except Exception as e:
            print(f"  ✗ 读取失败: {e}")
            issues.append(f"urls.csv读取失败: {e}")
    else:
        issues.append("urls.csv不存在")
    
    return issues


def test_network():
    """测试网络"""
    print("\n" + "=" * 80)
    print("步骤3: 网络连接测试")
    print("=" * 80)
    
    issues = []
    
    try:
        import aiohttp
        import asyncio
        
        async def test_connection():
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 测试百度
                try:
                    async with session.get('https://www.baidu.com', ssl=False) as resp:
                        print(f"  ✓ 百度连接: HTTP {resp.status}")
                except Exception as e:
                    print(f"  ✗ 百度连接失败: {e}")
                    issues.append("无法连接百度")
                
                # 测试教育部
                try:
                    async with session.get('https://www.moe.gov.cn/', ssl=False) as resp:
                        print(f"  ✓ 教育部连接: HTTP {resp.status}")
                except Exception as e:
                    print(f"  ✗ 教育部连接失败: {e}")
                    issues.append("无法连接教育部")
        
        asyncio.run(test_connection())
        
    except Exception as e:
        print(f"  ✗ 网络测试失败: {e}")
        issues.append(f"网络测试失败: {e}")
    
    return issues


def test_fetcher():
    """测试Fetcher模块"""
    print("\n" + "=" * 80)
    print("步骤4: Fetcher模块测试")
    print("=" * 80)
    
    issues = []
    
    try:
        from core.fetcher import AsyncFetcher, get_random_headers
        
        print("\nFetcher导入: ✓")
        
        # 测试获取headers
        headers = get_random_headers()
        print(f"  ✓ User-Agent: {headers.get('User-Agent', 'N/A')[:50]}...")
        
        # 测试Fetcher初始化
        fetcher = AsyncFetcher(timeout=10)
        print(f"  ✓ Fetcher初始化成功")
        
        # 测试单个URL获取
        print("\n测试单个URL获取:")
        
        async def test_fetch():
            try:
                results = await fetcher.fetch_all([{"url": "https://www.baidu.com"}])
                if results and len(results) > 0:
                    result = results[0]
                    print(f"  ✓ 请求成功: HTTP {result.get('status', 'N/A')}")
                    if result.get('success'):
                        print(f"  ✓ 内容获取成功: {len(result.get('content', ''))} 字符")
                    else:
                        print(f"  ✗ 内容获取失败: {result.get('error', 'Unknown')}")
                        issues.append(f"百度抓取失败: {result.get('error')}")
                else:
                    print(f"  ✗ 无结果返回")
                    issues.append("Fetcher无结果返回")
            except Exception as e:
                print(f"  ✗ 请求异常: {e}")
                issues.append(f"Fetcher异常: {e}")
        
        asyncio.run(test_fetch())
        
    except Exception as e:
        print(f"  ✗ Fetcher测试失败: {e}")
        traceback.print_exc()
        issues.append(f"Fetcher模块错误: {e}")
    
    return issues


def test_parser():
    """测试Parser模块"""
    print("\n" + "=" * 80)
    print("步骤5: Parser模块测试")
    print("=" * 80)
    
    issues = []
    
    try:
        from core.parser import ContentParser
        
        print("\nParser导入: ✓")
        
        # 测试HTML解析
        test_html = """
        <html>
        <head><title>测试页面 - 比赛通知</title></head>
        <body>
            <h1>2024年全国教学大赛</h1>
            <p>欢迎参加比赛，<a href="/file.pdf">下载通知</a></p>
        </body>
        </html>
        """
        
        parser = ContentParser(test_html)
        title = parser.get_title()
        print(f"  ✓ 标题提取: {title}")
        
        if "测试页面" in title:
            print(f"  ✓ 标题解析正确")
        else:
            print(f"  ✗ 标题解析异常")
            issues.append("标题解析异常")
        
        text = parser.get_text()
        print(f"  ✓ 文本提取: {len(text)} 字符")
        
        # 测试文档提取
        from core.document_handler import DocumentHandler
        handler = DocumentHandler()
        docs = handler.extract_document_links(test_html, "http://example.com", "比赛通知")
        print(f"  ✓ 文档提取: {len(docs)} 个文档")
        
        if len(docs) == 1:
            print(f"  ✓ 文档提取正确")
        else:
            print(f"  ✗ 文档提取异常，期望1个，实际{len(docs)}个")
            issues.append("文档提取异常")
        
    except Exception as e:
        print(f"  ✗ Parser测试失败: {e}")
        traceback.print_exc()
        issues.append(f"Parser模块错误: {e}")
    
    return issues


def test_crawler_core():
    """测试爬虫核心"""
    print("\n" + "=" * 80)
    print("步骤6: 爬虫核心测试")
    print("=" * 80)
    
    issues = []
    
    try:
        from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3
        
        print("\n爬虫核心导入: ✓")
        
        # 创建爬虫实例
        crawler = EnhancedCompetitionCrawlerV3(
            timeout=10,
            auto_remove_failed=False,
            urls_file="urls.csv"
        )
        print(f"  ✓ 爬虫实例创建成功")
        
        # 测试比赛关键词检测
        is_comp = crawler.is_competition_related("全国教学大赛通知", "")
        print(f"  ✓ 比赛检测: {is_comp}")
        
        if is_comp:
            print(f"  ✓ 比赛检测正常")
        else:
            print(f"  ✗ 比赛检测异常")
            issues.append("比赛检测异常")
        
        # 测试单个URL爬取（如果前面的测试都通过了）
        if not issues:
            print("\n测试单个URL爬取:")
            
            async def test_crawl():
                try:
                    result = await crawler.crawl_single({"url": "https://www.baidu.com"})
                    if result:
                        if result.get('success'):
                            print(f"  ✓ 爬取成功: {result.get('title', 'N/A')[:40]}...")
                        else:
                            print(f"  ✗ 爬取失败: {result.get('error', 'Unknown')}")
                            issues.append(f"百度爬取失败: {result.get('error')}")
                    else:
                        print(f"  ✗ 无结果")
                        issues.append("爬虫无结果返回")
                except Exception as e:
                    print(f"  ✗ 爬取异常: {e}")
                    traceback.print_exc()
                    issues.append(f"爬虫异常: {e}")
            
            asyncio.run(test_crawl())
        
    except Exception as e:
        print(f"  ✗ 爬虫核心测试失败: {e}")
        traceback.print_exc()
        issues.append(f"爬虫核心错误: {e}")
    
    return issues


def test_word_generator():
    """测试Word生成器"""
    print("\n" + "=" * 80)
    print("步骤7: Word生成器测试")
    print("=" * 80)
    
    issues = []
    
    try:
        from word_generator import NoticeWordGenerator
        
        print("\nWord生成器导入: ✓")
        
        # 创建生成器
        generator = NoticeWordGenerator(output_dir="test_output")
        print(f"  ✓ Word生成器初始化成功")
        
        # 测试生成（使用模拟数据）
        test_data = [
            {
                "url": "http://example.com/1",
                "title": "测试通知",
                "text": "这是测试内容",
                "is_competition_related": True,
                "competition_documents": [],
                "crawled_at": "2024-01-01T00:00:00"
            }
        ]
        
        print(f"\n测试Word生成（使用模拟数据）:")
        try:
            filepath = generator.generate(test_data, "测试报告")
            if filepath and os.path.exists(filepath):
                print(f"  ✓ Word生成成功: {filepath}")
                # 清理
                import shutil
                shutil.rmtree("test_output", ignore_errors=True)
            else:
                print(f"  ✗ Word生成失败或文件不存在")
                issues.append("Word生成失败")
        except Exception as e:
            print(f"  ✗ Word生成异常: {e}")
            traceback.print_exc()
            issues.append(f"Word生成错误: {e}")
        
    except Exception as e:
        print(f"  ✗ Word生成器测试失败: {e}")
        traceback.print_exc()
        issues.append(f"Word生成器错误: {e}")
    
    return issues


def main():
    print("=" * 80)
    print("全面诊断工具 - 检查抓取流程的每个环节")
    print("=" * 80)
    
    all_issues = []
    
    # 运行所有测试
    all_issues.extend(test_environment())
    all_issues.extend(test_file_access())
    all_issues.extend(test_network())
    all_issues.extend(test_fetcher())
    all_issues.extend(test_parser())
    all_issues.extend(test_crawler_core())
    all_issues.extend(test_word_generator())
    
    # 汇总
    print("\n" + "=" * 80)
    print("诊断汇总")
    print("=" * 80)
    
    if all_issues:
        print(f"\n发现 {len(all_issues)} 个问题:")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        
        print("\n" + "=" * 80)
        print("建议解决方案:")
        print("=" * 80)
        
        if any("缺少依赖" in i for i in all_issues):
            print("\n1. 安装缺失依赖:")
            print("   pip install -r requirements_gui.txt")
        
        if any("urls.csv" in i for i in all_issues):
            print("\n2. 修复urls.csv:")
            print("   - 检查文件编码（应为UTF-8）")
            print("   - 检查URL格式（应以http://或https://开头）")
            print("   - 检查CSV格式（应为：url,name,category）")
        
        if any("网络" in i for i in all_issues):
            print("\n3. 检查网络连接:")
            print("   - 确认可以访问百度和教育部网站")
            print("   - 检查防火墙设置")
            print("   - 检查代理设置")
        
        if any("Fetcher" in i or "Parser" in i or "爬虫" in i for i in all_issues):
            print("\n4. 检查核心模块:")
            print("   - 确认core目录存在且文件完整")
            print("   - 重新下载完整代码包")
        
    else:
        print("\n✓ 所有测试通过！没有发现明显问题。")
        print("\n如果GUI仍然崩溃，可能是:")
        print("  1. 特定网址导致的问题")
        print("  2. 内存不足")
        print("  3. PyQt6与系统兼容性问题")
        print("\n建议: 使用命令行模式运行")
        print("  python enhanced_crawler_v3.py --urls urls.csv --no-auto-remove")
    
    print("\n" + "=" * 80)
    
    return len(all_issues) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
