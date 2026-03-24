#!/usr/bin/env python3
"""
批量导入全国各省市电教馆和教科委官网网址
"""
import os
import csv
import sys

def import_national_urls():
    """导入全国网址"""
    print("=" * 70)
    print("批量导入全国各省市电教馆和教科委官网网址")
    print("=" * 70)
    
    # 源文件
    source_file = "全国电教馆_教科委网址库.csv"
    target_file = "urls.csv"
    
    if not os.path.exists(source_file):
        print(f"\n错误：未找到源文件 {source_file}")
        return False
    
    # 读取源文件
    urls_to_add = []
    with open(source_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            urls_to_add.append({
                'url': row.get('url', '').strip(),
                'name': row.get('name', '').strip(),
                'category': row.get('category', '').strip()
            })
    
    print(f"\n源文件包含 {len(urls_to_add)} 个网址")
    
    # 统计分类
    categories = {}
    for item in urls_to_add:
        cat = item['category'] or '未分类'
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n分类统计:")
    for cat, count in sorted(categories.items()):
        print(f"  - {cat}: {count} 个")
    
    # 检查目标文件
    existing_urls = set()
    if os.path.exists(target_file):
        with open(target_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # 跳过标题
            for row in reader:
                if row:
                    existing_urls.add(row[0].strip())
        print(f"\n目标文件已有 {len(existing_urls)} 个网址")
    
    # 过滤已存在的
    new_urls = [u for u in urls_to_add if u['url'] not in existing_urls]
    duplicates = len(urls_to_add) - len(new_urls)
    
    if duplicates > 0:
        print(f"  跳过重复: {duplicates} 个")
    
    if not new_urls:
        print("\n所有网址都已存在，无需导入")
        return True
    
    print(f"\n准备导入: {len(new_urls)} 个新网址")
    
    # 确认导入
    confirm = input("\n确认导入? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消导入")
        return False
    
    # 执行导入
    try:
        # 如果目标文件不存在，创建并写入标题
        if not os.path.exists(target_file):
            with open(target_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['url', 'name', 'category'])
        
        # 追加新网址
        with open(target_file, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            for item in new_urls:
                writer.writerow([item['url'], item['name'], item['category']])
        
        print(f"\n✅ 导入成功！")
        print(f"   已添加 {len(new_urls)} 个网址到 {target_file}")
        
        # 显示导入的网址
        print("\n导入的网址列表:")
        for i, item in enumerate(new_urls[:10], 1):
            print(f"  {i}. {item['name']} ({item['category']})")
        
        if len(new_urls) > 10:
            print(f"  ... 还有 {len(new_urls) - 10} 个")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_urls():
    """显示当前所有网址"""
    target_file = "urls.csv"
    
    if not os.path.exists(target_file):
        print(f"\n未找到文件: {target_file}")
        return
    
    with open(target_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        urls = list(reader)
    
    print(f"\n当前共有 {len(urls)} 个网址:\n")
    
    # 按分类分组
    by_category = {}
    for item in urls:
        cat = item.get('category', '未分类') or '未分类'
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    # 显示
    for cat in sorted(by_category.keys()):
        items = by_category[cat]
        print(f"\n【{cat}】({len(items)}个)")
        for i, item in enumerate(items[:5], 1):
            name = item.get('name', '未命名') or '未命名'
            url = item.get('url', '')
            print(f"  {i}. {name}")
            print(f"     {url[:60]}...")
        if len(items) > 5:
            print(f"  ... 还有 {len(items) - 5} 个")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'show':
            show_urls()
            return
    
    print("\n选项:")
    print("  1. 导入全国电教馆和教科委网址")
    print("  2. 查看当前所有网址")
    print("  3. 退出")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == '1':
        import_national_urls()
    elif choice == '2':
        show_urls()
    else:
        print("已退出")


if __name__ == "__main__":
    main()
