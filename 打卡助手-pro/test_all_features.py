#!/usr/bin/env python3
"""
全面功能测试脚本 - 测试所有API和交互功能
"""

import http.client
import json
import sys

def make_request(method, path, body=None, headers=None):
    """发送HTTP请求"""
    try:
        conn = http.client.HTTPConnection("localhost", 3000)
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)
        
        if body and isinstance(body, dict):
            body = json.dumps(body)
        
        conn.request(method, path, body, default_headers)
        response = conn.getresponse()
        data = response.read().decode('utf-8')
        conn.close()
        
        return response.status, json.loads(data) if data else {}
    except Exception as e:
        print(f"  ERROR: {e}")
        return None, {}

class TestRunner:
    def __init__(self):
        self.token = None
        self.passed = 0
        self.failed = 0
        
    def test(self, name, func):
        """运行单个测试"""
        print(f"\n[TEST] {name}")
        try:
            func()
            self.passed += 1
            print(f"  [PASS] ✓")
        except AssertionError as e:
            self.failed += 1
            print(f"  [FAIL] ✗ {e}")
        except Exception as e:
            self.failed += 1
            print(f"  [ERROR] ✗ {e}")
    
    def assert_true(self, condition, message=""):
        if not condition:
            raise AssertionError(message)
    
    def assert_equal(self, a, b, message=""):
        if a != b:
            raise AssertionError(f"{message} Expected {b}, got {a}")

# ============ 测试用例 ============

def test_health(runner):
    """测试健康检查"""
    status, data = make_request("GET", "/api/health")
    runner.assert_equal(status, 200)
    runner.assert_true(data.get("success"), "Health check should return success")

def test_login(runner):
    """测试登录"""
    status, data = make_request("POST", "/api/auth/login", {
        "username": "testuser",
        "password": "user123"
    })
    runner.assert_equal(status, 200)
    runner.assert_true(data.get("success"), "Login should succeed")
    runner.assert_true("token" in data.get("data", {}), "Should return token")
    runner.token = data["data"]["token"]

def test_get_profile(runner):
    """测试获取用户信息"""
    status, data = make_request("GET", "/api/auth/profile")
    runner.assert_equal(status, 200)
    runner.assert_true(data.get("success"), "Get profile should succeed")

def test_get_habits(runner):
    """测试获取习惯列表"""
    status, data = make_request("GET", "/api/habits")
    runner.assert_equal(status, 200)
    runner.assert_true(data.get("success"), "Get habits should succeed")
    runner.assert_true("data" in data, "Should return data")

def test_create_habit(runner):
    """测试创建习惯"""
    status, data = make_request("POST", "/api/habits", {
        "name": "测试习惯-跑步",
        "description": "每天早上跑步30分钟",
        "icon": "activity",
        "color": "#22C55E",
        "habit_type": "daily_once",
        "points": 2
    })
    runner.assert_equal(status, 201)
    runner.assert_true(data.get("success"), "Create habit should succeed")
    runner.created_habit_id = data.get("data", {}).get("id")

def test_update_habit(runner):
    """测试更新习惯"""
    # 先创建一个习惯
    status, data = make_request("POST", "/api/habits", {
        "name": "测试更新习惯",
        "description": "原始描述",
        "icon": "star",
        "color": "#4A7BF7",
        "habit_type": "daily_once",
        "points": 1
    })
    habit_id = data.get("data", {}).get("id")
    
    # 更新习惯
    status, data = make_request("PUT", f"/api/habits/{habit_id}", {
        "name": "已更新的习惯",
        "description": "更新后的描述",
        "points": 3
    })
    runner.assert_equal(status, 200)
    runner.assert_true(data.get("success"), "Update habit should succeed")

def test_delete_habit(runner):
    """测试删除习惯"""
    # 先创建一个习惯
    status, data = make_request("POST", "/api/habits", {
        "name": "待删除习惯",
        "icon": "star",
        "color": "#4A7BF7",
        "habit_type": "daily_once",
        "points": 1
    })
    habit_id = data.get("data", {}).get("id")
    
    # 删除习惯
    status, data = make_request("DELETE", f"/api/habits/{habit_id}")
    runner.assert_equal(status, 200)
    runner.assert_true(data.get("success"), "Delete habit should succeed")

def test_checkin(runner):
    """测试打卡"""
    # 获取第一个习惯
    status, data = make_request("GET", "/api/habits")
    habits = data.get("data", {}).get("list", [])
    if not habits:
        print("  SKIP: No habits available")
        return
    
    habit_id = habits[0]["id"]
    
    # 打卡
    status, data = make_request("POST", "/api/checkins", {
        "habit_id": habit_id,
        "note": "测试打卡"
    })
    runner.assert_equal(status, 201)
    runner.assert_true(data.get("success"), "Checkin should succeed")

def test_makeup_checkin(runner):
    """测试补打卡"""
    from datetime import datetime, timedelta
    
    # 获取第一个习惯
    status, data = make_request("GET", "/api/habits")
    habits = data.get("data", {}).get("list", [])
    if not habits:
        print("  SKIP: No habits available")
        return
    
    habit_id = habits[0]["id"]
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 补打卡
    status, data = make_request("POST", "/api/checkins/makeup", {
        "habit_id": habit_id,
        "checkin_date": yesterday,
        "note": "补打卡测试"
    })
    runner.assert_equal(status, 201)
    runner.assert_true(data.get("success"), "Makeup checkin should succeed")

def test_get_checkin_stats(runner):
    """测试获取打卡统计"""
    status, data = make_request("GET", "/api/checkins/stats/overview")
    runner.assert_equal(status, 200)
    runner.assert_true(data.get("success"), "Get stats should succeed")

def test_get_calendar(runner):
    """测试获取日历数据"""
    from datetime import datetime
    now = datetime.now()
    status, data = make_request("GET", f"/api/checkins/calendar?year={now.year}&month={now.month}")
    runner.assert_equal(status, 200)
    runner.assert_true(data.get("success"), "Get calendar should succeed")

def test_get_analytics_dashboard(runner):
    """测试仪表盘数据"""
    status, data = make_request("GET", "/api/analytics/dashboard")
    runner.assert_equal(status, 200)
    runner.assert_true(data.get("success"), "Get dashboard should succeed")

def test_get_logs(runner):
    """测试获取日志"""
    status, data = make_request("GET", "/api/logs/system")
    runner.assert_equal(status, 200)
    runner.assert_true(data.get("success"), "Get logs should succeed")

# ============ 运行测试 ============

def main():
    print("=" * 60)
    print("  松鼠打卡 Pro - 全面功能测试")
    print("=" * 60)
    
    runner = TestRunner()
    
    # 基础API测试
    runner.test("Health Check", lambda: test_health(runner))
    runner.test("Login", lambda: test_login(runner))
    runner.test("Get Profile", lambda: test_get_profile(runner))
    
    # 习惯管理测试
    runner.test("Get Habits", lambda: test_get_habits(runner))
    runner.test("Create Habit", lambda: test_create_habit(runner))
    runner.test("Update Habit", lambda: test_update_habit(runner))
    runner.test("Delete Habit", lambda: test_delete_habit(runner))
    
    # 打卡功能测试
    runner.test("Checkin", lambda: test_checkin(runner))
    runner.test("Makeup Checkin", lambda: test_makeup_checkin(runner))
    runner.test("Get Checkin Stats", lambda: test_get_checkin_stats(runner))
    runner.test("Get Calendar", lambda: test_get_calendar(runner))
    
    # 数据分析测试
    runner.test("Analytics Dashboard", lambda: test_analytics_dashboard(runner))
    
    # 日志测试
    runner.test("Get Logs", lambda: test_get_logs(runner))
    
    # 打印结果
    print("\n" + "=" * 60)
    print(f"  测试完成: {runner.passed} 通过, {runner.failed} 失败")
    print("=" * 60)
    
    return runner.failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
