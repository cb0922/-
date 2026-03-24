#!/usr/bin/env python3
"""
按省份筛选网址
"""
import os
import csv

def show_menu():
    """显示菜单"""
    print("\n" + "=" * 70)
    print("按省份筛选网址")
    print("=" * 70)
    
    if not os.path.exists("urls.csv"):
        print("\n未找到 urls.csv 文件")
        return
    
    # 读取所有网址
    with open("urls.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_urls = list(reader)
    
    # 按分类统计
    categories = {}
    for item in all_urls:
        cat = item.get('category', '未分类') or '未分类'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    print(f"\n当前共有 {len(all_urls)} 个网址\n")
    print("省份/分类列表:")
    
    # 排序：国家级在前，然后按拼音排序
    sorted_cats = sorted(categories.keys(), 
                         key=lambda x: ('0' if x == '国家级' else '1') + x)
    
    for i, cat in enumerate(sorted_cats, 1):
        count = len(categories[cat])
        print(f"  {i}. {cat} ({count}个)")
    
    print(f"  0. 显示所有")
    print(f"  q. 退出")
    
    choice = input("\n请选择 (输入序号或q): ").strip()
    
    if choice == 'q':
        return
    
    if choice == '0':
        display_urls(all_urls, "所有网址")
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(sorted_cats):
                cat = sorted_cats[idx]
                display_urls(categories[cat], f"{cat}的网址")
        except:
            print("无效选择")


def display_urls(urls, title):
    """显示网址列表"""
    print(f"\n{'='*70}")
    print(f"{title} (共{len(urls)}个)")
    print(f"{'='*70}\n")
    
    for i, item in enumerate(urls, 1):
        name = item.get('name', '未命名') or '未命名'
        url = item.get('url', '')
        cat = item.get('category', '')
        
        print(f"{i}. {name}")
        print(f"   网址: {url}")
        if cat:
            print(f"   分类: {cat}")
        print()


if __name__ == "__main__":
    while True:
        show_menu()
        again = input("\n继续查询? (y/n): ").strip().lower()
        if again != 'y':
            break
    
    print("\n已退出")
