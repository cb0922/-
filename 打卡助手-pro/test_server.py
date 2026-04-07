#!/usr/bin/env python3
"""
打卡助手 Pro - 测试服务器
用于前端功能测试的简单HTTP服务器，模拟后端API
"""

import http.server
import socketserver
import json
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

PORT = 3000
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), 'public')

# 模拟数据
MOCK_USER = {
    "id": 1,
    "username": "testuser",
    "nickname": "测试用户",
    "email": "test@example.com",
    "role": "user",
    "total_points": 150,
    "continuous_days": 7,
    "total_checkins": 45
}

MOCK_HABITS = [
    {"id": 1, "name": "早起", "icon": "sun", "color": "#F59E0B", "habit_type": "daily_once", "points": 2, "description": "早睡早起身体好"},
    {"id": 2, "name": "晨读", "icon": "book", "color": "#4A7BF7", "habit_type": "daily_once", "points": 3, "description": "每天阅读30分钟"},
    {"id": 3, "name": "运动", "icon": "activity", "color": "#22C55E", "habit_type": "daily_once", "points": 2, "description": "坚持锻炼"},
    {"id": 4, "name": "背单词", "icon": "pen-tool", "color": "#8B5CF6", "habit_type": "daily_once", "points": 1, "description": "记忆新单词"}
]

MOCK_CHECKINS = []

# 生成模拟打卡记录
for i in range(7):
    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
    for habit_id in [1, 2, 3]:
        MOCK_CHECKINS.append({
            "id": len(MOCK_CHECKINS) + 1,
            "habit_id": habit_id,
            "checkin_date": date,
            "checkin_time": "08:00:00",
            "status": "completed",
            "points_earned": 2
        })

class MockAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args[0]}")
    
    def send_json_response(self, data, status=200):
        """发送JSON响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        
        # API路由
        if path == '/api':
            self.send_json_response({
                "success": True,
                "data": {
                    "name": "打卡助手 Pro API (测试模式)",
                    "version": "1.0.0-test"
                }
            })
            return
        
        if path == '/api/auth/profile':
            self.send_json_response({"success": True, "data": MOCK_USER})
            return
        
        if path == '/api/habits':
            self.send_json_response({
                "success": True,
                "data": {
                    "list": MOCK_HABITS,
                    "pagination": {"page": 1, "pageSize": 20, "total": len(MOCK_HABITS)}
                }
            })
            return
        
        if path == '/api/checkins/stats/overview':
            self.send_json_response({
                "success": True,
                "data": {
                    "today": {"habits_completed": 3, "points": 7},
                    "this_week": {"checkins": 21, "points": 45},
                    "total": 45,
                    "continuous_days": 7,
                    "habit_distribution": [
                        {"name": "早起", "count": 15},
                        {"name": "晨读", "count": 12},
                        {"name": "运动", "count": 18}
                    ],
                    "weekly_trend": [
                        {"checkin_date": (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), "checkins": 3}
                        for i in range(6, -1, -1)
                    ]
                }
            })
            return
        
        if path == '/api/analytics/dashboard':
            self.send_json_response({
                "success": True,
                "data": {
                    "user": MOCK_USER,
                    "today": {"habits_completed": 3, "points_earned": 7},
                    "active_habits": 4,
                    "this_week": {"checkins": 21, "points": 45},
                    "weekly_trend": [
                        {"checkin_date": (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), "checkins": 3, "points": 7}
                        for i in range(6, -1, -1)
                    ],
                    "habit_completion": [
                        {"id": 1, "name": "早起", "color": "#F59E0B", "completed_days": 15, "total_checkins": 20},
                        {"id": 2, "name": "晨读", "color": "#4A7BF7", "completed_days": 12, "total_checkins": 18},
                        {"id": 3, "name": "运动", "color": "#22C55E", "completed_days": 18, "total_checkins": 25},
                        {"id": 4, "name": "背单词", "color": "#8B5CF6", "completed_days": 10, "total_checkins": 15}
                    ]
                }
            })
            return
        
        if path == '/api/logs/system':
            self.send_json_response({
                "success": True,
                "data": {
                    "list": [
                        {"id": 1, "created_at": datetime.now().isoformat(), "action": "login", "username": "testuser", "ip_address": "127.0.0.1", "new_value": "用户登录"},
                        {"id": 2, "created_at": datetime.now().isoformat(), "action": "create_habit", "username": "testuser", "ip_address": "127.0.0.1", "new_value": "创建习惯：早起"},
                        {"id": 3, "created_at": datetime.now().isoformat(), "action": "checkin", "username": "testuser", "ip_address": "127.0.0.1", "new_value": "打卡：早起 +2⭐"}
                    ],
                    "pagination": {"page": 1, "pageSize": 20, "total": 3, "totalPages": 1}
                }
            })
            return
        
        if path == '/api/logs/login':
            self.send_json_response({
                "success": True,
                "data": {
                    "list": [
                        {"id": 1, "created_at": datetime.now().isoformat(), "action": "login", "username": "testuser", "ip_address": "127.0.0.1", "status": "success"},
                        {"id": 2, "created_at": (datetime.now() - timedelta(hours=1)).isoformat(), "action": "login", "username": "testuser", "ip_address": "127.0.0.1", "status": "success"}
                    ],
                    "pagination": {"page": 1, "pageSize": 20, "total": 2, "totalPages": 1}
                }
            })
            return
        
        # 页面路由
        page_routes = {
            '/': '/index.html',
            '/login': '/pages/login.html',
            '/register': '/pages/register.html',
            '/dashboard': '/pages/dashboard.html',
            '/logs': '/pages/logs.html'
        }
        
        if path in page_routes:
            self.path = page_routes[path]
            return super().do_GET()
        
        # 静态文件服务
        if path.startswith('/api/'):
            self.send_json_response({"success": False, "message": "API not found"}, 404)
            return
        
        return super().do_GET()
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 读取请求体
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            data = json.loads(body)
        except:
            data = {}
        
        # 登录
        if path == '/api/auth/login':
            username = data.get('username', '')
            password = data.get('password', '')
            
            if username == 'testuser' and password == 'user123':
                self.send_json_response({
                    "success": True,
                    "data": {
                        "token": "mock_jwt_token_" + datetime.now().strftime('%Y%m%d%H%M%S'),
                        "user": MOCK_USER
                    },
                    "message": "登录成功"
                })
            else:
                self.send_json_response({"success": False, "message": "用户名或密码错误"}, 401)
            return
        
        # 注册
        if path == '/api/auth/register':
            self.send_json_response({
                "success": True,
                "data": {"id": 999, "username": data.get('username')},
                "message": "注册成功"
            }, 201)
            return
        
        # 打卡
        if path == '/api/checkins':
            habit_id = data.get('habit_id')
            habit = next((h for h in MOCK_HABITS if h['id'] == habit_id), None)
            points = habit['points'] if habit else 1
            
            self.send_json_response({
                "success": True,
                "data": {
                    "id": 999,
                    "habit_id": habit_id,
                    "checkin_date": datetime.now().strftime('%Y-%m-%d'),
                    "points_earned": points,
                    "message": "打卡成功"
                },
                "message": "打卡成功"
            }, 201)
            return
        
        # 创建习惯
        if path == '/api/habits':
            self.send_json_response({
                "success": True,
                "data": {
                    "id": len(MOCK_HABITS) + 1,
                    "name": data.get('name'),
                    "icon": data.get('icon', 'star'),
                    "color": data.get('color', '#4A7BF7')
                },
                "message": "习惯创建成功"
            }, 201)
            return
        
        self.send_json_response({"success": False, "message": "API not found"}, 404)

def main():
    print("=" * 60)
    print("   打卡助手 Pro - 测试服务器")
    print("=" * 60)
    print(f"\n启动测试服务器...")
    print(f"访问地址: http://localhost:{PORT}")
    print(f"\n测试账号: testuser / user123")
    print("\n功能测试:")
    print("  - 登录/注册页面")
    print("  - 习惯管理")
    print("  - 打卡功能")
    print("  - 数据分析仪表盘")
    print("  - 日志查询")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60 + "\n")
    
    with socketserver.TCPServer(("", PORT), MockAPIHandler) as httpd:
        httpd.serve_forever()

if __name__ == '__main__':
    main()
