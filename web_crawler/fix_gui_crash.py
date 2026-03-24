#!/usr/bin/env python3
"""
修复GUI崩溃问题
一键修复所有可能导致崩溃的问题
"""
import os
import sys
import shutil

def main():
    print("=" * 70)
    print("GUI崩溃修复工具")
    print("=" * 70)
    
    # 1. 清理失败记录
    print("\n[1/5] 清理失败记录...")
    if os.path.exists("urls_fail_records.json"):
        os.remove("urls_fail_records.json")
        print("  ✓ 已删除 urls_fail_records.json")
    else:
        print("  - 无失败记录文件")
    
    # 2. 备份urls.csv
    print("\n[2/5] 备份网址文件...")
    if os.path.exists("urls.csv"):
        backup = "urls.csv.backup." + datetime_now()
        shutil.copy2("urls.csv", backup)
        print(f"  ✓ 已备份到 {backup}")
    
    # 3. 检查必要文件
    print("\n[3/5] 检查必要文件...")
    required_files = [
        "app_gui.py",
        "enhanced_crawler_v3_safe.py",
        "core/document_handler.py",
        "core/proxy_manager.py"
    ]
    
    for f in required_files:
        if os.path.exists(f):
            print(f"  ✓ {f}")
        else:
            print(f"  ✗ {f} 缺失！")
    
    # 4. 清理临时文件
    print("\n[4/5] 清理临时文件...")
    temp_patterns = ['.tmp', '.backup', '_fail_records.json']
    cleaned = 0
    for f in os.listdir('.'):
        if any(p in f for p in temp_patterns):
            try:
                if os.path.isfile(f):
                    os.remove(f)
                    cleaned += 1
            except:
                pass
    print(f"  ✓ 清理了 {cleaned} 个临时文件")
    
    # 5. 验证修复
    print("\n[5/5] 验证修复...")
    try:
        # 测试导入
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from enhanced_crawler_v3_safe import EnhancedCompetitionCrawlerV3
        
        # 创建实例测试
        crawler = EnhancedCompetitionCrawlerV3(
            urls_file="urls.csv",
            auto_remove_failed=False  # 确保安全模式
        )
        print("  ✓ 安全版本加载成功")
        print("  ✓ 自动删除功能已禁用")
    except Exception as e:
        print(f"  ✗ 验证失败: {e}")
    
    print("\n" + "=" * 70)
    print("修复完成！")
    print("=" * 70)
    print("\n现在可以重新启动GUI:")
    print("  python app_gui.py")
    print("\n或者使用命令行（更安全）：")
    print("  python enhanced_crawler_v3_safe.py --urls urls.csv --no-auto-remove")


def datetime_now():
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")


if __name__ == "__main__":
    main()
