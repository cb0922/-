#!/usr/bin/env python3
"""
诊断爬虫错误脚本
"""
import sys
import os
import subprocess
import json

def check_environment():
    """检查环境"""
    print("=" * 60)
    print("环境检查")
    print("=" * 60)
    
    # Python版本
    print(f"Python版本: {sys.version}")
    
    # 检查关键文件
    files_to_check = [
        "enhanced_crawler_v3.py",
        "app_gui.py",
        "core/document_handler.py",
        "core/proxy_manager.py",
        "urls.csv",
    ]
    
    print("\n文件检查:")
    for f in files_to_check:
        exists = "[OK]" if os.path.exists(f) else "[MISSING]"
        print(f"  {exists} {f}")
    
    # 检查依赖
    print("\n依赖检查:")
    required_modules = [
        "PyQt6",
        "aiohttp",
        "beautifulsoup4",
        "docx",
    ]
    
    for module in required_modules:
        try:
            __import__(module.lower())
            print(f"  [OK] {module}")
        except ImportError:
            print(f"  [MISSING] {module} (未安装)")
    
    # 检查urls.csv
    print("\n网址文件检查:")
    if os.path.exists("urls.csv"):
        with open("urls.csv", "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"  总行数: {len(lines)}")
        print(f"  标题行: {lines[0].strip() if lines else '无'}")
        
        # 检查格式
        if lines:
            first_data = lines[1] if len(lines) > 1 else ""
            cols = first_data.strip().split(",")
            print(f"  列数: {len(cols)}")
            print(f"  第一行数据: {first_data[:80]}...")
    
    return True


def test_single_url():
    """测试单个URL爬取"""
    print("\n" + "=" * 60)
    print("单URL测试")
    print("=" * 60)
    
    # 获取第一个URL
    if not os.path.exists("urls.csv"):
        print("错误: urls.csv不存在")
        return False
    
    with open("urls.csv", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    if len(lines) < 2:
        print("错误: urls.csv中没有数据")
        return False
    
    # 获取第一个有效URL
    test_url = None
    for line in lines[1:]:
        cols = line.strip().split(",")
        if cols and cols[0].strip():
            test_url = cols[0].strip()
            break
    
    if not test_url:
        print("错误: 没有找到有效的URL")
        return False
    
    print(f"测试URL: {test_url}")
    
    # 创建测试脚本
    test_script = f'''
import sys
import asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3

async def test():
    crawler = EnhancedCompetitionCrawlerV3(
        urls_file="urls.csv",
        auto_remove_failed=False,
        timeout=10
    )
    result = await crawler.crawl_single({{"url": "{test_url}"}})
    if result:
        print(f"成功: {{result.get('title', 'N/A')}}")
    else:
        print("Failed: No result")

asyncio.run(test())
'''
    
    with open("_test_single.py", "w", encoding="utf-8") as f:
        f.write(test_script)
    
    print("运行单URL测试...")
    try:
        result = subprocess.run(
            [sys.executable, "_test_single.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        print("STDOUT:", result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        print("STDERR:", result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
        print("返回码:", result.returncode)
    except Exception as e:
        print(f"测试出错: {e}")
    finally:
        if os.path.exists("_test_single.py"):
            os.remove("_test_single.py")
    
    return True


def check_error_logs():
    """检查错误日志"""
    print("\n" + "=" * 60)
    print("错误日志检查")
    print("=" * 60)
    
    # 检查失败记录
    if os.path.exists("urls_fail_records.json"):
        with open("urls_fail_records.json", "r", encoding="utf-8") as f:
            records = json.load(f)
        print(f"失败记录数: {len(records)}")
        print("最近5条失败记录:")
        for i, (url, count) in enumerate(list(records.items())[:5]):
            print(f"  {i+1}. {url[:50]}... (失败{count}次)")
    else:
        print("无失败记录文件")
    
    # 检查是否有Python错误文件
    for f in os.listdir("."):
        if f.endswith(".log") or "error" in f.lower():
            print(f"\n发现日志文件: {f}")


def fix_common_issues():
    """修复常见问题"""
    print("\n" + "=" * 60)
    print("常见问题修复")
    print("=" * 60)
    
    # 1. 清理失败记录
    if os.path.exists("urls_fail_records.json"):
        response = input("是否清理失败记录? (y/n): ")
        if response.lower() == 'y':
            os.remove("urls_fail_records.json")
            print("[OK] 已清理失败记录")
    
    # 2. 重置urls.csv编码
    if os.path.exists("urls.csv"):
        response = input("是否检查并修复urls.csv编码? (y/n): ")
        if response.lower() == 'y':
            try:
                with open("urls.csv", "r", encoding="utf-8") as f:
                    content = f.read()
                # 重新保存确保编码正确
                with open("urls.csv", "w", encoding="utf-8") as f:
                    f.write(content)
                print("✓ 已修复urls.csv编码")
            except Exception as e:
                print(f"[ERROR] 修复失败: {e}")


def main():
    print("=" * 60)
    print("爬虫错误诊断工具")
    print("=" * 60)
    
    check_environment()
    check_error_logs()
    
    response = input("\n是否运行单URL测试? (y/n): ")
    if response.lower() == 'y':
        test_single_url()
    
    fix_common_issues()
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
    print("\n建议:")
    print("1. 如果单URL测试成功，但批量失败，可能是内存问题，尝试减少并发数")
    print("2. 如果显示编码错误，确保所有文件都是UTF-8编码")
    print("3. 如果依赖缺失，运行: pip install -r requirements_gui.txt")
    print("4. 查看详细日志运行命令行模式:")
    print("   python enhanced_crawler_v3.py --urls urls.csv --output ./output 2>&1 | tee crawl.log")


if __name__ == "__main__":
    main()
