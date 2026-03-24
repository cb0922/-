#!/usr/bin/env python3
"""
报告查看器 - 命令行友好的可视化工具
"""
import json
import os
import sys
from datetime import datetime
from urllib.parse import urlparse


def print_header(text, width=60):
    """打印标题"""
    print("\n" + "=" * width)
    print(text.center(width))
    print("=" * width)


def print_card(title, content):
    """打印卡片"""
    print(f"\n[{title}]")
    print("-" * 60)
    print(content)


def generate_summary(item):
    """生成自然语言摘要"""
    title = item.get("title", "未知")
    text = item.get("text", "")
    url = item.get("url", "")
    status = item.get("status", 0)
    links = item.get("links_count", 0)
    images = item.get("images_count", 0)
    
    domain = urlparse(url).netloc
    
    if status != 200:
        return f"爬取失败 (HTTP {status})，该网站可能有反爬虫机制或需要特殊权限访问。"
    
    parts = []
    
    # 网站类型
    if "wkds" in domain or "zhyww" in domain:
        site_type = "教育赛事平台"
    elif "ncet" in domain or "edu" in domain:
        site_type = "教育部官方网站"
    elif "qq" in domain or "aiteach" in domain:
        site_type = "腾讯教育平台"
    else:
        site_type = "网站"
    
    parts.append(f"【{site_type}】《{title}》")
    parts.append(f"域名: {domain}")
    
    # 内容统计
    text_len = len(text)
    if text_len > 1000:
        parts.append(f"内容丰富，共 {text_len} 字符")
    elif text_len > 100:
        parts.append(f"内容长度: {text_len} 字符")
    else:
        parts.append("内容较少(可能是动态加载页面)")
    
    # 资源
    if links > 0 or images > 0:
        resources = []
        if links > 0:
            resources.append(f"{links}个链接")
        if images > 0:
            resources.append(f"{images}张图片")
        parts.append(f"包含资源: {', '.join(resources)}")
    
    return "\n".join(parts)


def view_data(data):
    """查看数据详情"""
    while True:
        print("\n" + "-" * 60)
        print("选择一个网页查看详情 (0 返回, q 退出):")
        for i, item in enumerate(data, 1):
            title = item.get("title", "无标题")[:30]
            status = "OK" if item.get("status") == 200 else "FAIL"
            print(f"  {i}. [{status}] {title}")
        
        choice = input("\n输入编号: ").strip().lower()
        
        if choice == 'q':
            sys.exit(0)
        if choice == '0':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(data):
                show_detail(data[idx])
            else:
                print("无效编号")
        except ValueError:
            print("请输入数字")


def show_detail(item):
    """显示单个网站详情"""
    print_header("网页详情")
    
    # 基本信息
    print(f"\n标题: {item.get('title', '无标题')}")
    print(f"URL: {item.get('url', '')}")
    print(f"状态: {'成功 (200)' if item.get('status') == 200 else '失败 (' + str(item.get('status')) + ')'}")
    
    # 智能摘要
    print("\n" + "-" * 60)
    print("【智能摘要】")
    print("-" * 60)
    print(generate_summary(item))
    
    # 元数据
    print("\n" + "-" * 60)
    print("【元数据】")
    print("-" * 60)
    print(f"链接数量: {item.get('links_count', 0)}")
    print(f"图片数量: {item.get('images_count', 0)}")
    print(f"内容长度: {len(item.get('text', ''))} 字符")
    
    # 描述和关键词
    desc = item.get('description', '')
    keywords = item.get('keywords', '')
    if desc:
        print(f"描述: {desc[:100]}...")
    if keywords:
        print(f"关键词: {keywords}")
    
    # 内容预览
    print("\n" + "-" * 60)
    print("【内容预览】(前800字符)")
    print("-" * 60)
    text = item.get('text', '')
    preview = text[:800] if text else "(无内容)"
    print(preview)
    if len(text) > 800:
        print(f"\n... (共 {len(text)} 字符)")
    
    input("\n按 Enter 键继续...")


def show_list(data):
    """显示列表视图"""
    print_header("爬取结果列表")
    
    print(f"\n总计: {len(data)} 个网页\n")
    
    for i, item in enumerate(data, 1):
        title = item.get("title", "无标题")[:40]
        url = item.get("url", "")
        status = item.get("status", 0)
        text_len = len(item.get("text", ""))
        
        status_str = "OK" if status == 200 else "FAIL"
        domain = urlparse(url).netloc[:30]
        
        print(f"{i}. [{status_str}] {title}")
        print(f"   域名: {domain}")
        print(f"   状态: {status} | 内容: {text_len} 字符")
        print()


def show_statistics(data):
    """显示统计信息"""
    print_header("统计信息")
    
    total = len(data)
    success = sum(1 for item in data if item.get("status") == 200)
    failed = total - success
    total_links = sum(item.get("links_count", 0) for item in data)
    total_images = sum(item.get("images_count", 0) for item in data)
    total_text = sum(len(item.get("text", "")) for item in data)
    
    print(f"\n总网页数: {total}")
    print(f"成功: {success}")
    print(f"失败: {failed}")
    print(f"成功率: {success/total*100:.1f}%" if total > 0 else "0%")
    print(f"\n链接总数: {total_links}")
    print(f"图片总数: {total_images}")
    print(f"文本总长度: {total_text} 字符")


def find_reports():
    """查找所有报告文件"""
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    if not os.path.exists(reports_dir):
        return []
    
    reports = []
    for f in os.listdir(reports_dir):
        if f.endswith('.html'):
            path = os.path.join(reports_dir, f)
            mtime = os.path.getmtime(path)
            reports.append({
                "name": f,
                "path": path,
                "time": datetime.fromtimestamp(mtime)
            })
    
    return sorted(reports, key=lambda x: x["time"], reverse=True)


def main():
    """主函数"""
    print_header("Web Crawler Report Viewer")
    
    # 加载数据
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    
    if not json_files:
        print("\n错误: 未找到数据文件")
        return
    
    latest = max(json_files, key=lambda f: os.path.getmtime(os.path.join(data_dir, f)))
    
    with open(os.path.join(data_dir, latest), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n已加载数据: {latest}")
    print(f"包含 {len(data)} 个网页")
    
    # 检查是否有 HTML 报告
    reports = find_reports()
    
    while True:
        print("\n" + "-" * 60)
        print("选择操作:")
        print("  1. 查看统计信息")
        print("  2. 查看列表")
        print("  3. 查看详情")
        
        if reports:
            print(f"  4. 打开可视化报告 ({len(reports)}个)")
        
        print("  q. 退出")
        
        choice = input("\n输入选项: ").strip().lower()
        
        if choice == 'q':
            print("\n再见!")
            break
        elif choice == '1':
            show_statistics(data)
        elif choice == '2':
            show_list(data)
        elif choice == '3':
            view_data(data)
        elif choice == '4' and reports:
            import webbrowser
            webbrowser.open(f'file://{os.path.abspath(reports[0]["path"])}')
            print(f"\n已打开: {reports[0]['name']}")
        else:
            print("\n无效选项")


if __name__ == "__main__":
    main()
