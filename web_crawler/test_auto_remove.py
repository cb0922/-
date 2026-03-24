#!/usr/bin/env python3
"""
测试自动删除无效网址功能
"""
import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3


def setup_test_data():
    """设置测试数据"""
    # 创建测试CSV文件
    with open("test_urls_auto_remove.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "name", "category"])
        # 使用几个确保失败的URL
        writer.writerow(["http://invalid.domain.that.does.not.exist.com/page", "无效网站1", "测试"])
        writer.writerow(["http://127.0.0.1:99999/invalid", "无效网站2", "测试"])
        writer.writerow(["https://www.example.com/nonexistent-page-404", "无效网站3", "测试"])
        writer.writerow(["https://httpstat.us/403", "403网站", "测试"])
        writer.writerow(["https://httpstat.us/500", "500网站", "测试"])
    
    print("[OK] 创建测试文件: test_urls_auto_remove.csv")
    
    # 清理可能存在的失败记录
    fail_record_file = "test_urls_auto_remove_fail_records.json"
    if os.path.exists(fail_record_file):
        os.remove(fail_record_file)
        print("[OK] 清理旧的失败记录")


def test_fail_record_management():
    """测试失败记录管理"""
    print("\n[测试] 失败记录管理")
    
    crawler = EnhancedCompetitionCrawlerV3(
        urls_file="test_urls_auto_remove.csv",
        max_retries=3,
        auto_remove_failed=True
    )
    
    # 测试记录失败
    url1 = "http://example.com/test1"
    url2 = "http://example.com/test2"
    
    # 第一次失败
    should_remove = crawler._record_failure(url1)
    print(f"  [OK] 第一次失败 should_remove={should_remove} (应为False)")
    assert not should_remove, "第一次失败不应触发删除"
    
    # 第二次失败
    should_remove = crawler._record_failure(url1)
    print(f"  [OK] 第二次失败 should_remove={should_remove} (应为False)")
    assert not should_remove, "第二次失败不应触发删除"
    
    # 第三次失败
    should_remove = crawler._record_failure(url1)
    print(f"  [OK] 第三次失败 should_remove={should_remove} (应为True)")
    assert should_remove, "第三次失败应触发删除"
    
    # 检查记录
    assert crawler.fail_records[url1] == 3, f"失败次数应为3，实际是{crawler.fail_records[url1]}"
    print(f"  [OK] 失败次数记录正确: {crawler.fail_records[url1]}")
    
    # 测试记录成功
    crawler._record_success(url1)
    assert url1 not in crawler.fail_records, "成功后应清除记录"
    print(f"  [OK] 成功记录后清除失败记录")
    
    # 测试记录保存
    fail_file = "test_urls_auto_remove_fail_records.json"
    assert os.path.exists(fail_file), "失败记录文件应被创建"
    with open(fail_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  [OK] 失败记录已保存到文件: {len(data)} 条记录")
    
    return True


def test_url_removal():
    """测试网址删除功能"""
    print("\n[测试] 网址删除功能")
    
    # 准备测试数据
    with open("test_removal.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "name", "category"])
        writer.writerow(["http://keep1.com", "保留1", "测试"])
        writer.writerow(["http://remove1.com", "删除1", "测试"])
        writer.writerow(["http://keep2.com", "保留2", "测试"])
        writer.writerow(["http://remove2.com", "删除2", "测试"])
    
    crawler = EnhancedCompetitionCrawlerV3(
        urls_file="test_removal.csv",
        max_retries=3,
        auto_remove_failed=True
    )
    
    # 删除指定URL
    urls_to_remove = ["http://remove1.com", "http://remove2.com"]
    crawler.remove_failed_urls(urls_to_remove)
    
    # 验证结果
    with open("test_removal.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    remaining_urls = [r[0] for r in rows[1:]]
    print(f"  [OK] 剩余网址: {remaining_urls}")
    
    assert "http://keep1.com" in remaining_urls, "保留的网址不应被删除"
    assert "http://keep2.com" in remaining_urls, "保留的网址不应被删除"
    assert "http://remove1.com" not in remaining_urls, "要删除的网址应被删除"
    assert "http://remove2.com" not in remaining_urls, "要删除的网址应被删除"
    
    print(f"  [OK] 删除功能工作正常")
    
    # 清理
    os.remove("test_removal.csv")
    
    return True


def test_disabled_auto_remove():
    """测试禁用自动删除"""
    print("\n[测试] 禁用自动删除")
    
    crawler = EnhancedCompetitionCrawlerV3(
        urls_file="test_urls_auto_remove.csv",
        max_retries=3,
        auto_remove_failed=False  # 禁用
    )
    
    url = "http://example.com/test"
    
    # 失败10次
    for i in range(10):
        should_remove = crawler._record_failure(url)
        assert not should_remove, "禁用时不应触发删除"
    
    print(f"  [OK] 禁用自动删除后，即使失败10次也不会标记删除")
    print(f"  [OK] 当前失败记录: {crawler.fail_records}")
    
    return True


def test_empty_csv():
    """测试空CSV处理"""
    print("\n[测试] 空CSV处理")
    
    # 创建空CSV
    with open("test_empty.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "name", "category"])
    
    crawler = EnhancedCompetitionCrawlerV3(
        urls_file="test_empty.csv",
        auto_remove_failed=True
    )
    
    # 尝试删除（应无错误）
    crawler.remove_failed_urls(["http://test.com"])
    
    print(f"  [OK] 空CSV处理无错误")
    
    os.remove("test_empty.csv")
    return True


def test_custom_max_retries():
    """测试自定义最大重试次数"""
    print("\n[测试] 自定义最大重试次数")
    
    # 测试5次
    crawler = EnhancedCompetitionCrawlerV3(
        urls_file="test_urls_auto_remove.csv",
        max_retries=5,
        auto_remove_failed=True
    )
    
    url = "http://example.com/custom"
    
    # 失败4次
    for i in range(4):
        should_remove = crawler._record_failure(url)
        assert not should_remove, f"第{i+1}次失败不应触发删除"
    
    # 第5次
    should_remove = crawler._record_failure(url)
    assert should_remove, "第5次失败应触发删除"
    
    print(f"  [OK] 自定义max_retries=5工作正常")
    
    return True


def cleanup():
    """清理测试文件"""
    files_to_remove = [
        "test_urls_auto_remove.csv",
        "test_urls_auto_remove_fail_records.json",
        "test_empty.csv",
        "test_removal.csv"
    ]
    
    for f in files_to_remove:
        if os.path.exists(f):
            os.remove(f)
            print(f"[清理] {f}")


def main():
    print("=" * 70)
    print("    自动删除无效网址 - 全面测试")
    print("=" * 70)
    
    setup_test_data()
    
    results = []
    
    try:
        results.append(("失败记录管理", test_fail_record_management()))
    except Exception as e:
        print(f"  [ERROR] 失败记录管理测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("失败记录管理", False))
    
    try:
        results.append(("网址删除功能", test_url_removal()))
    except Exception as e:
        print(f"  [ERROR] 网址删除功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("网址删除功能", False))
    
    try:
        results.append(("禁用自动删除", test_disabled_auto_remove()))
    except Exception as e:
        print(f"  [ERROR] 禁用自动删除测试失败: {e}")
        results.append(("禁用自动删除", False))
    
    try:
        results.append(("空CSV处理", test_empty_csv()))
    except Exception as e:
        print(f"  [ERROR] 空CSV处理测试失败: {e}")
        results.append(("空CSV处理", False))
    
    try:
        results.append(("自定义重试次数", test_custom_max_retries()))
    except Exception as e:
        print(f"  [ERROR] 自定义重试次数测试失败: {e}")
        results.append(("自定义重试次数", False))
    
    print("\n" + "=" * 70)
    print("    测试结果汇总")
    print("=" * 70)
    
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("    所有测试通过!")
    else:
        print("    有测试失败，请检查!")
    print("=" * 70)
    
    cleanup()
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
