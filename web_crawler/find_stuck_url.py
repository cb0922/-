#!/usr/bin/env python3
"""
找出卡住的URL
"""
import sys
import os
import csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def analyze_fail_records():
    """分析失败记录，找出可能卡住的URL"""
    
    print("=" * 70)
    print("分析可能卡住的URL")
    print("=" * 70)
    
    # 检查失败记录
    fail_file = "urls_fail_records.json"
    if os.path.exists(fail_file):
        import json
        with open(fail_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        
        print(f"\n失败记录文件: {len(records)} 个URL")
        
        # 找出失败次数最多的
        sorted_records = sorted(records.items(), key=lambda x: x[1], reverse=True)
        
        print("\n失败次数最多的URL (Top 10):")
        for i, (url, count) in enumerate(sorted_records[:10], 1):
            print(f"  {i}. {url[:60]}... (失败{count}次)")
        
        return [url for url, _ in sorted_records[:10]]
    else:
        print("无失败记录文件")
        return []


def find_slow_urls():
    """找出可能需要很长时间的URL"""
    
    print("\n" + "=" * 70)
    print("分析可能慢速的URL")
    print("=" * 70)
    
    if not os.path.exists("urls.csv"):
        print("urls.csv 不存在")
        return []
    
    with open("urls.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # 跳过标题
        urls = [row[0] if row else "" for row in reader if row and row[0].strip()]
    
    # 根据URL特征判断可能慢速的网站
    slow_patterns = [
        (".gov.cn", "政府网站（通常较慢）"),
        ("edu.cn", "教育网站（可能较慢）"),
        ("xjjks", "新疆考试院（已知问题）"),
        ("qhjyks", "青海考试院（已知问题）"),
        ("nxjky", "宁夏考试院（已知问题）"),
        ("xjdjg", "新疆电教馆（已知问题）"),
        ("jyt.xinjiang", "新疆教育厅（已知问题）"),
    ]
    
    slow_urls = []
    
    print("\n可能慢速的URL:")
    for url in urls:
        for pattern, desc in slow_patterns:
            if pattern in url:
                print(f"  - {url[:60]}... [{desc}]")
                slow_urls.append((url, desc))
                break
    
    if not slow_urls:
        print("  未发现明显慢速URL")
    
    return slow_urls


def create_url_batches():
    """创建URL批次，方便分批处理"""
    
    print("\n" + "=" * 70)
    print("创建分批处理文件")
    print("=" * 70)
    
    if not os.path.exists("urls.csv"):
        print("urls.csv 不存在")
        return
    
    # 读取所有URL
    with open("urls.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        all_rows = list(reader)
    
    # 分离可能慢的URL（新疆、青海等）
    slow_keywords = ["xinjiang", "xjjks", "qhjyks", "nxjky", "xjdjg"]
    
    normal_urls = []
    slow_urls = []
    
    for row in all_rows:
        if not row or not row[0].strip():
            continue
        url = row[0]
        
        is_slow = any(kw in url.lower() for kw in slow_keywords)
        if is_slow:
            slow_urls.append(row)
        else:
            normal_urls.append(row)
    
    print(f"\nURL分类:")
    print(f"  正常URL: {len(normal_urls)} 个")
    print(f"  可能慢速URL: {len(slow_urls)} 个")
    
    # 保存分类文件
    # 1. 正常URL - 优先处理
    with open("urls_normal.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(normal_urls)
    print(f"\n[OK] 保存正常URL: urls_normal.csv ({len(normal_urls)} 个)")
    
    # 2. 慢速URL - 最后处理，单独超时设置
    with open("urls_slow.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(slow_urls)
    print(f"[OK] 保存慢速URL: urls_slow.csv ({len(slow_urls)} 个)")
    
    # 3. 创建测试文件（前5个正常URL）
    with open("urls_test.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(normal_urls[:5])
    print(f"[OK] 保存测试URL: urls_test.csv (5 个)")
    
    return len(normal_urls), len(slow_urls)


def generate_skip_script():
    """生成跳过特定URL的脚本"""
    
    script_content = '''#!/usr/bin/env python3
"""
跳过特定URL的爬取脚本
使用方式: python crawl_skip.py [要跳过的URL关键词]
"""
import sys
import os
import csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def skip_urls(skip_keywords):
    """跳过包含特定关键词的URL"""
    
    if not os.path.exists("urls.csv"):
        print("urls.csv 不存在")
        return
    
    # 读取
    with open("urls.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        all_rows = list(reader)
    
    # 过滤
    skipped = []
    kept = []
    
    for row in all_rows:
        if not row or not row[0].strip():
            continue
        url = row[0]
        
        should_skip = any(kw in url for kw in skip_keywords)
        if should_skip:
            skipped.append(row)
        else:
            kept.append(row)
    
    # 保存
    with open("urls_filtered.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(kept)
    
    print(f"原始URL: {len(all_rows)} 个")
    print(f"跳过URL: {len(skipped)} 个")
    print(f"保留URL: {len(kept)} 个")
    print(f"已保存到: urls_filtered.csv")
    
    if skipped:
        print("\n跳过的URL:")
        for row in skipped[:10]:
            print(f"  - {row[0][:60]}...")

if __name__ == "__main__":
    # 默认跳过新疆、青海等已知慢速网站
    default_keywords = ["xinjiang", "xjjks", "qhjyks", "nxjky"]
    
    if len(sys.argv) > 1:
        keywords = sys.argv[1:]
    else:
        keywords = default_keywords
    
    print(f"跳过关键词: {keywords}")
    skip_urls(keywords)
'''
    
    with open("crawl_skip.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("\n[OK] 生成跳过脚本: crawl_skip.py")
    print("  使用: python crawl_skip.py [关键词1] [关键词2]")


def main():
    print("=" * 70)
    print("找出卡住的URL - 分析工具")
    print("=" * 70)
    
    # 1. 分析失败记录
    problem_urls = analyze_fail_records()
    
    # 2. 找出可能慢速的URL
    slow_urls = find_slow_urls()
    
    # 3. 创建分批文件
    create_url_batches()
    
    # 4. 生成跳过脚本
    generate_skip_script()
    
    print("\n" + "=" * 70)
    print("建议解决方案")
    print("=" * 70)
    
    print("\n1. 先测试正常URL:")
    print("   python crawl_safe.py --urls urls_normal.csv")
    
    print("\n2. 如果正常URL没问题，单独处理慢速URL:")
    print("   python crawl_safe.py --urls urls_slow.csv --timeout 5")
    
    print("\n3. 或者跳过特定URL:")
    print("   python crawl_skip.py")
    print("   python crawl_safe.py --urls urls_filtered.csv")
    
    print("\n4. 只测试前5个:")
    print("   python crawl_safe.py --urls urls_test.csv")


if __name__ == "__main__":
    main()
