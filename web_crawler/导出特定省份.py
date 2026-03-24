#!/usr/bin/env python3
"""
导出特定省份的网址到单独文件
"""
import os
import csv

def export_by_province():
    """按省份导出"""
    print("=" * 70)
    print("导出特定省份的网址")
    print("=" * 70)
    
    if not os.path.exists("urls.csv"):
        print("\n未找到 urls.csv 文件")
        return
    
    # 读取所有网址
    with open("urls.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_urls = list(reader)
    
    # 按分类分组
    categories = {}
    for item in all_urls:
        cat = item.get('category', '未分类') or '未分类'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    print(f"\n当前共有 {len(all_urls)} 个网址")
    print("\n可导出的省份/分类:")
    
    sorted_cats = sorted(categories.keys())
    for i, cat in enumerate(sorted_cats, 1):
        print(f"  {i}. {cat} ({len(categories[cat])}个)")
    
    choice = input("\n请选择要导出的省份 (输入序号，多个用逗号分隔，0导出全部): ").strip()
    
    if choice == '0':
        export_urls(all_urls, "全部网址")
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected_urls = []
            selected_names = []
            
            for idx in indices:
                if 0 <= idx < len(sorted_cats):
                    cat = sorted_cats[idx]
                    selected_urls.extend(categories[cat])
                    selected_names.append(cat)
            
            if selected_urls:
                name = "_".join(selected_names)
                export_urls(selected_urls, name)
        except:
            print("无效选择")


def export_urls(urls, name):
    """导出网址到文件"""
    filename = f"urls_{name}.csv"
    
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['url', 'name', 'category'])
        for item in urls:
            writer.writerow([item.get('url', ''), item.get('name', ''), item.get('category', '')])
    
    print(f"\n✅ 导出成功！")
    print(f"   文件: {filename}")
    print(f"   数量: {len(urls)} 个网址")


if __name__ == "__main__":
    export_by_province()
    input("\n按回车键退出...")
