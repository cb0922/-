#!/usr/bin/env python3
"""
清理重复的网址
"""
import os
import csv

def clean_duplicates():
    """清理重复网址"""
    print("=" * 70)
    print("清理重复网址")
    print("=" * 70)
    
    if not os.path.exists("urls.csv"):
        print("\n未找到 urls.csv 文件")
        return
    
    # 读取所有网址
    with open("urls.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_urls = list(reader)
    
    print(f"\n当前共有 {len(all_urls)} 个网址")
    
    # 去重（保留第一个）
    seen = set()
    unique_urls = []
    duplicates = []
    
    for item in all_urls:
        url = item.get('url', '').strip()
        if url and url not in seen:
            seen.add(url)
            unique_urls.append(item)
        else:
            duplicates.append(item)
    
    if len(duplicates) == 0:
        print("没有发现重复网址")
        return
    
    print(f"\n发现 {len(duplicates)} 个重复网址:")
    for item in duplicates:
        print(f"  - {item.get('name', '未命名')}: {item.get('url', '')}")
    
    confirm = input(f"\n删除重复网址，保留 {len(unique_urls)} 个唯一网址? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("已取消")
        return
    
    # 保存去重后的数据
    with open("urls.csv", 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['url', 'name', 'category'])
        for item in unique_urls:
            writer.writerow([item.get('url', ''), item.get('name', ''), item.get('category', '')])
    
    print(f"\n✅ 清理完成！")
    print(f"   已删除 {len(duplicates)} 个重复网址")
    print(f"   保留 {len(unique_urls)} 个唯一网址")


if __name__ == "__main__":
    clean_duplicates()
    input("\n按回车键退出...")
