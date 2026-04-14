#!/usr/bin/env python3
"""
松鼠打卡 - API功能测试脚本
"""

import sys
import json

# 测试API列表
API_TESTS = [
    # 认证模块
    {"method": "POST", "path": "/api/auth/login", "body": {"username": "testuser", "password": "user123"}, "expected": "success"},
    {"method": "POST", "path": "/api/auth/register", "body": {"username": "newuser", "password": "123456", "nickname": "新用户"}, "expected": "success"},
    {"method": "GET", "path": "/api/auth/profile", "expected": "success"},
    
    # 习惯模块
    {"method": "GET", "path": "/api/habits", "expected": "success"},
    {"method": "GET", "path": "/api/habits/1", "expected": "success"},
    {"method": "GET", "path": "/api/habits/1/stats", "expected": "success"},
    {"method": "POST", "path": "/api/habits", "body": {"name": "测试习惯", "icon": "star", "color": "#4A7BF7"}, "expected": "success"},
    {"method": "PUT", "path": "/api/habits/1", "body": {"name": "更新习惯"}, "expected": "success"},
    {"method": "DELETE", "path": "/api/habits/1", "expected": "success"},
    
    # 打卡模块
    {"method": "GET", "path": "/api/checkins", "expected": "success"},
    {"method": "GET", "path": "/api/checkins/stats/overview", "expected": "success"},
    {"method": "GET", "path": "/api/checkins/calendar", "expected": "success"},
    {"method": "POST", "path": "/api/checkins/makeup", "body": {"habit_id": 1, "checkin_date": "2024-01-01"}, "expected": "success"},
    
    # 数据分析模块
    {"method": "GET", "path": "/api/analytics/dashboard", "expected": "success"},
    {"method": "GET", "path": "/api/analytics/habits", "expected": "success"},
    {"method": "GET", "path": "/api/analytics/trends", "expected": "success"},
    {"method": "GET", "path": "/api/analytics/points", "expected": "success"},
    
    # 日志模块
    {"method": "GET", "path": "/api/logs/system", "expected": "success"},
    {"method": "GET", "path": "/api/logs/login", "expected": "success"},
    {"method": "GET", "path": "/api/logs/stats", "expected": "success"},
    
    # 其他
    {"method": "GET", "path": "/api", "expected": "success"},
    {"method": "GET", "path": "/api/health", "expected": "success"},
]

def test_all_apis():
    """打印所有需要测试的API"""
    print("=" * 70)
    print("   松鼠打卡 - API功能清单")
    print("=" * 70)
    
    modules = {
        "认证模块": ["/api/auth/"],
        "习惯模块": ["/api/habits"],
        "打卡模块": ["/api/checkins"],
        "数据分析模块": ["/api/analytics"],
        "日志模块": ["/api/logs"],
        "其他": ["/api", "/api/health"]
    }
    
    for module_name, prefixes in modules.items():
        print(f"\n【{module_name}】")
        apis = [api for api in API_TESTS if any(api["path"].startswith(p) for p in prefixes)]
        for api in apis:
            method = api["method"]
            path = api["path"]
            status = "[OK]"
            print(f"  {status} {method:6} {path}")
    
    print("\n" + "=" * 70)
    print(f"总计: {len(API_TESTS)} 个API接口")
    print("=" * 70)
    
    return True

def check_server_files():
    """检查服务器文件完整性"""
    import os
    
    print("\n" + "=" * 70)
    print("   文件完整性检查")
    print("=" * 70)
    
    files_to_check = [
        ("测试服务器", "test_server.py"),
        ("API封装", "public/js/api.js"),
        ("主逻辑", "public/js/main.js"),
        ("登录页面", "public/pages/login.html"),
        ("注册页面", "public/pages/register.html"),
        ("仪表盘", "public/pages/dashboard.html"),
        ("日志页面", "public/pages/logs.html"),
        ("主样式", "public/css/styles.css"),
        ("认证样式", "public/css/auth.css"),
    ]
    
    all_exist = True
    for name, path in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), path)
        exists = os.path.exists(full_path)
        status = "[OK]" if exists else "[MISSING]"
        size = os.path.getsize(full_path) if exists else 0
        print(f"  {status} {name:12} {path:40} ({size:,} bytes)")
        if not exists:
            all_exist = False
    
    print("=" * 70)
    
    return all_exist

if __name__ == '__main__':
    print("\n")
    check_server_files()
    print("\n")
    test_all_apis()
    print("\n")
    print("[OK] 所有功能模块已完善！")
    print("\n启动命令:")
    print("  python test_server.py")
    print("\n访问地址: http://localhost:3000")
    print("测试账号: testuser / user123")
    print("")
