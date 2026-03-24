#!/usr/bin/env python3
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
        print("
跳过的URL:")
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
