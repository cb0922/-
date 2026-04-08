#!/usr/bin/env python3
"""
打卡助手 Pro - 测试服务器
用于前端功能测试的简单HTTP服务器，模拟后端API
"""

import http.server
import socketserver
import json
import os
import re
from datetime import datetime, timedelta
import time
from urllib.parse import urlparse, parse_qs

PORT = 3000
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), 'public')

# 北京时间偏移量（UTC+8）
BEIJING_TZ_OFFSET = 8 * 3600  # 8小时 = 28800秒

def get_beijing_time():
    """获取当前北京时间"""
    # 获取UTC时间戳
    utc_timestamp = time.time()
    # 转换为北京时间（UTC+8）
    beijing_timestamp = utc_timestamp + BEIJING_TZ_OFFSET
    return datetime.fromtimestamp(beijing_timestamp)

def get_beijing_date_str():
    """获取北京日期字符串 YYYY-MM-DD"""
    return get_beijing_time().strftime('%Y-%m-%d')

def get_beijing_time_str():
    """获取北京时间字符串 HH:MM:SS"""
    return get_beijing_time().strftime('%H:%M:%S')

def get_beijing_iso_str():
    """获取北京ISO时间字符串"""
    return get_beijing_time().isoformat()

# 模拟数据
MOCK_USER = {
    "id": 1,
    "username": "testuser",
    "nickname": "测试用户",
    "email": "test@example.com",
    "phone": "13800138000",
    "avatar": None,
    "role": "user",
    "total_points": 150,
    "continuous_days": 7,
    "total_checkins": 45,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": get_beijing_iso_str()
}

MOCK_HABITS = [
    {"id": 1, "name": "早起", "icon": "sun", "color": "#F59E0B", "habit_type": "daily_once", "points": 2, "description": "早睡早起身体好", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 2, "name": "晨读", "icon": "book", "color": "#4A7BF7", "habit_type": "daily_once", "points": 3, "description": "每天阅读30分钟", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 3, "name": "运动", "icon": "activity", "color": "#22C55E", "habit_type": "daily_once", "points": 2, "description": "坚持锻炼", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 4, "name": "背单词", "icon": "pen-tool", "color": "#8B5CF6", "habit_type": "daily_once", "points": 1, "description": "记忆新单词", "status": "active", "created_at": "2024-01-01T00:00:00"}
]

MOCK_CHECKINS = []
MOCK_LOGS = []
MOCK_LOGIN_LOGS = []

# 生成模拟打卡记录
for i in range(30):
    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
    for habit_id in [1, 2, 3]:
        MOCK_CHECKINS.append({
            "id": len(MOCK_CHECKINS) + 1,
            "habit_id": habit_id,
            "user_id": 1,
            "checkin_date": date,
            "checkin_time": f"{8+i%3:02d}:00:00",
            "status": "completed",
            "points_earned": 2,
            "note": "",
            "created_at": f"{date}T08:00:00"
        })

# 生成模拟日志
for i in range(50):
    MOCK_LOGS.append({
        "id": i + 1,
        "user_id": 1,
        "username": "testuser",
        "action": ["login", "create_habit", "checkin", "update_habit"][i % 4],
        "target_type": ["user", "habit", "checkin", "habit"][i % 4],
        "target_id": i % 4 + 1,
        "old_value": None,
        "new_value": f"操作记录 #{i+1}",
        "ip_address": "127.0.0.1",
        "user_agent": "Mozilla/5.0",
        "created_at": (datetime.now() - timedelta(hours=i)).isoformat()
    })

# 生成登录日志
for i in range(20):
    MOCK_LOGIN_LOGS.append({
        "id": i + 1,
        "user_id": 1,
        "username": "testuser",
        "action": "login",
        "ip_address": "127.0.0.1",
        "user_agent": "Mozilla/5.0",
        "status": "success",
        "fail_reason": None,
        "created_at": (datetime.now() - timedelta(hours=i*2)).isoformat()
    })

class MockAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}] {args[0]}")
    
    def send_json_response(self, data, status=200):
        """发送JSON响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def read_body(self):
        """读取请求体"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        try:
            return json.loads(body)
        except:
            return {}
    
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
        
        # API根
        if path == '/api':
            self.send_json_response({
                "success": True,
                "data": {
                    "name": "打卡助手 Pro API (测试模式)",
                    "version": "1.0.0-test",
                    "endpoints": ["/api/auth", "/api/habits", "/api/checkins", "/api/analytics", "/api/logs"]
                }
            })
            return
        
        # 健康检查
        if path == '/api/health':
            self.send_json_response({"success": True, "data": {"status": "healthy", "time": get_beijing_iso_str()}})
            return
        
        # ========== 认证模块 ==========
        if path == '/api/auth/profile':
            self.send_json_response({"success": True, "data": MOCK_USER})
            return
        
        # ========== 习惯模块 ==========
        if path == '/api/habits':
            status = query.get('status', ['active'])[0]
            habits = [h for h in MOCK_HABITS if h['status'] == status]
            self.send_json_response({
                "success": True,
                "data": {
                    "list": habits,
                    "pagination": {"page": 1, "pageSize": 20, "total": len(habits), "totalPages": 1}
                }
            })
            return
        
        # 习惯详情 /api/habits/:id
        match = re.match(r'^/api/habits/(\d+)$', path)
        if match:
            habit_id = int(match.group(1))
            habit = next((h for h in MOCK_HABITS if h['id'] == habit_id), None)
            if habit:
                # 添加统计数据
                habit_stats = habit.copy()
                habit_stats['total_checkins'] = len([c for c in MOCK_CHECKINS if c['habit_id'] == habit_id])
                habit_stats['last_checkin'] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                habit_stats['recent_checkins'] = [
                    {"checkin_date": (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), "status": "completed"}
                    for i in range(7)
                ]
                self.send_json_response({"success": True, "data": habit_stats})
            else:
                self.send_json_response({"success": False, "message": "习惯不存在"}, 404)
            return
        
        # 习惯统计 /api/habits/:id/stats
        match = re.match(r'^/api/habits/(\d+)/stats$', path)
        if match:
            habit_id = int(match.group(1))
            total = len([c for c in MOCK_CHECKINS if c['habit_id'] == habit_id])
            month = len([c for c in MOCK_CHECKINS if c['habit_id'] == habit_id and c['checkin_date'] >= (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')])
            self.send_json_response({
                "success": True,
                "data": {
                    "total_checkins": total,
                    "month_checkins": month,
                    "continuous_days": 7,
                    "last_30_days": [
                        {"checkin_date": (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), "status": "completed"}
                        for i in range(30)
                    ]
                }
            })
            return
        
        # ========== 打卡模块 ==========
        if path == '/api/checkins':
            habit_id = query.get('habit_id', [None])[0]
            checkins = MOCK_CHECKINS
            if habit_id:
                checkins = [c for c in checkins if c['habit_id'] == int(habit_id)]
            
            # 添加习惯名称
            for checkin in checkins:
                habit = next((h for h in MOCK_HABITS if h['id'] == checkin['habit_id']), None)
                if habit:
                    checkin['habit_name'] = habit['name']
                    checkin['habit_icon'] = habit['icon']
                    checkin['habit_color'] = habit['color']
            
            page = int(query.get('page', [1])[0])
            page_size = int(query.get('pageSize', [20])[0])
            start = (page - 1) * page_size
            end = start + page_size
            
            self.send_json_response({
                "success": True,
                "data": {
                    "list": checkins[start:end],
                    "pagination": {"page": page, "pageSize": page_size, "total": len(checkins), "totalPages": (len(checkins) + page_size - 1) // page_size}
                }
            })
            return
        
        if path == '/api/checkins/stats/overview':
            today = get_beijing_date_str()
            today_checkins = len([c for c in MOCK_CHECKINS if c['checkin_date'] == today])
            
            self.send_json_response({
                "success": True,
                "data": {
                    "today": {"habits_completed": today_checkins, "points": today_checkins * 2},
                    "this_week": {"checkins": 21, "points": 45},
                    "this_month": {"checkins": 85, "points": 180},
                    "total": len(MOCK_CHECKINS),
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
        
        if path == '/api/checkins/calendar':
            year = query.get('year', [get_beijing_time().year])[0]
            month = query.get('month', [get_beijing_time().month])[0]
            
            calendar_data = []
            for i in range(30):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                day_checkins = [c for c in MOCK_CHECKINS if c['checkin_date'] == date]
                if day_checkins:
                    habits = [next((h['name'] for h in MOCK_HABITS if h['id'] == c['habit_id']), '') for c in day_checkins]
                    calendar_data.append({
                        "checkin_date": date,
                        "count": len(day_checkins),
                        "habits": ",".join(habits),
                        "points": sum(c['points_earned'] for c in day_checkins)
                    })
            
            self.send_json_response({"success": True, "data": calendar_data})
            return
        
        # ========== 数据分析模块 ==========
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
                        {"id": 1, "name": "早起", "color": "#F59E0B", "completed_days": 15, "total_checkins": 20, "icon": "sun"},
                        {"id": 2, "name": "晨读", "color": "#4A7BF7", "completed_days": 12, "total_checkins": 18, "icon": "book"},
                        {"id": 3, "name": "运动", "color": "#22C55E", "completed_days": 18, "total_checkins": 25, "icon": "activity"},
                        {"id": 4, "name": "背单词", "color": "#8B5CF6", "completed_days": 10, "total_checkins": 15, "icon": "pen-tool"}
                    ]
                }
            })
            return
        
        if path == '/api/analytics/habits':
            habits_data = []
            for habit in MOCK_HABITS:
                h = habit.copy()
                h['total_checkins'] = len([c for c in MOCK_CHECKINS if c['habit_id'] == habit['id']])
                h['month_checkins'] = len([c for c in MOCK_CHECKINS if c['habit_id'] == habit['id'] and c['checkin_date'] >= (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')])
                h['last_checkin'] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                h['continuous_days'] = 7
                habits_data.append(h)
            
            self.send_json_response({"success": True, "data": habits_data})
            return
        
        if path == '/api/analytics/trends':
            trend_type = query.get('type', ['daily'])[0]
            range_days = int(query.get('range', ['30'])[0])
            
            trends = []
            for i in range(range_days):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                day_checkins = [c for c in MOCK_CHECKINS if c['checkin_date'] == date]
                trends.append({
                    "date": date,
                    "checkins": len(day_checkins),
                    "points": sum(c['points_earned'] for c in day_checkins)
                })
            
            self.send_json_response({
                "success": True,
                "data": {
                    "trends": list(reversed(trends)),
                    "completion_rate": [
                        {"checkin_date": (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), "completed_habits": 3, "total_habits": 4}
                        for i in range(30)
                    ]
                }
            })
            return
        
        if path == '/api/analytics/points':
            self.send_json_response({
                "success": True,
                "data": {
                    "summary": {
                        "total_earned": 150,
                        "total_spent": 0,
                        "current_balance": 150
                    },
                    "trend": [
                        {"date": (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), "earned": 7, "spent": 0}
                        for i in range(30)
                    ],
                    "source_distribution": [
                        {"source": "checkin", "total_points": 120, "count": 45},
                        {"source": "makeup", "total_points": 30, "count": 10}
                    ],
                    "recent_records": [
                        {"id": i+1, "points": 2, "type": "earn", "source": "checkin", "description": f"打卡奖励 #{i+1}", "created_at": (datetime.now() - timedelta(hours=i)).isoformat()}
                        for i in range(10)
                    ]
                }
            })
            return
        
        # ========== 日志模块 ==========
        if path == '/api/logs/system':
            page = int(query.get('page', [1])[0])
            page_size = int(query.get('pageSize', [20])[0])
            action = query.get('action', [None])[0]
            
            logs = MOCK_LOGS
            if action:
                logs = [l for l in logs if l['action'] == action]
            
            start = (page - 1) * page_size
            end = start + page_size
            
            self.send_json_response({
                "success": True,
                "data": {
                    "list": logs[start:end],
                    "pagination": {"page": page, "pageSize": page_size, "total": len(logs), "totalPages": (len(logs) + page_size - 1) // page_size}
                }
            })
            return
        
        if path == '/api/logs/login':
            page = int(query.get('page', [1])[0])
            page_size = int(query.get('pageSize', [20])[0])
            status = query.get('status', [None])[0]
            
            logs = MOCK_LOGIN_LOGS
            if status:
                logs = [l for l in logs if l['status'] == status]
            
            start = (page - 1) * page_size
            end = start + page_size
            
            self.send_json_response({
                "success": True,
                "data": {
                    "list": logs[start:end],
                    "pagination": {"page": page, "pageSize": page_size, "total": len(logs), "totalPages": (len(logs) + page_size - 1) // page_size}
                }
            })
            return
        
        if path == '/api/logs/stats':
            self.send_json_response({
                "success": True,
                "data": {
                    "action_stats": [
                        {"action": "login", "count": 20, "users": 1},
                        {"action": "create_habit", "count": 10, "users": 1},
                        {"action": "checkin", "count": 45, "users": 1}
                    ],
                    "user_stats": [
                        {"username": "testuser", "total_actions": 50, "active_days": 30}
                    ],
                    "login_stats": {
                        "total_attempts": 20,
                        "success_count": 20,
                        "fail_count": 0
                    },
                    "daily_stats": [
                        {"date": (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), "active_users": 1, "total_actions": 5}
                        for i in range(30)
                    ]
                }
            })
            return
        
        # ========== 页面路由 ==========
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
        data = self.read_body()
        
        # ========== 认证模块 ==========
        if path == '/api/auth/login':
            username = data.get('username', '')
            password = data.get('password', '')
            
            if username in ['testuser', 'admin'] and password in ['user123', 'admin123']:
                self.send_json_response({
                    "success": True,
                    "data": {
                        "token": f"mock_jwt_token_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "user": MOCK_USER
                    },
                    "message": "登录成功"
                })
            else:
                self.send_json_response({"success": False, "message": "用户名或密码错误"}, 401)
            return
        
        if path == '/api/auth/register':
            username = data.get('username', '')
            if not username or len(username) < 3:
                self.send_json_response({"success": False, "message": "用户名至少3位"}, 400)
                return
            
            self.send_json_response({
                "success": True,
                "data": {"id": 999, "username": username, "nickname": data.get('nickname', username)},
                "message": "注册成功"
            }, 201)
            return
        
        if path == '/api/auth/logout':
            self.send_json_response({"success": True, "message": "登出成功"})
            return
        
        # ========== 习惯模块 ==========
        if path == '/api/habits':
            name = data.get('name', '')
            if not name:
                self.send_json_response({"success": False, "message": "习惯名称为必填项"}, 400)
                return
            
            new_habit = {
                "id": len(MOCK_HABITS) + 1,
                "name": name,
                "description": data.get('description', ''),
                "icon": data.get('icon', 'star'),
                "color": data.get('color', '#4A7BF7'),
                "habit_type": data.get('habit_type', 'daily_once'),
                "points": data.get('points', 1),
                "status": "active",
                "created_at": get_beijing_iso_str()
            }
            MOCK_HABITS.append(new_habit)
            
            self.send_json_response({
                "success": True,
                "data": new_habit,
                "message": "习惯创建成功"
            }, 201)
            return
        
        # ========== 打卡模块 ==========
        if path == '/api/checkins':
            habit_id = data.get('habit_id')
            if not habit_id:
                self.send_json_response({"success": False, "message": "习惯ID为必填项"}, 400)
                return
            
            habit = next((h for h in MOCK_HABITS if h['id'] == habit_id), None)
            if not habit:
                self.send_json_response({"success": False, "message": "习惯不存在"}, 404)
                return
            
            today = get_beijing_date_str()
            # 检查是否已打卡
            existing = next((c for c in MOCK_CHECKINS if c['habit_id'] == habit_id and c['checkin_date'] == today), None)
            if existing:
                self.send_json_response({"success": False, "message": "今天已经打过卡了"}, 400)
                return
            
            points = habit['points']
            new_checkin = {
                "id": len(MOCK_CHECKINS) + 1,
                "habit_id": habit_id,
                "user_id": 1,
                "checkin_date": today,
                "checkin_time": get_beijing_time_str(),
                "status": "completed",
                "points_earned": points,
                "note": data.get('note', ''),
                "created_at": get_beijing_iso_str()
            }
            MOCK_CHECKINS.insert(0, new_checkin)
            
            self.send_json_response({
                "success": True,
                "data": {
                    **new_checkin,
                    "habit_name": habit['name'],
                    "message": "打卡成功"
                },
                "message": "打卡成功"
            }, 201)
            return
        
        if path == '/api/checkins/makeup':
            habit_id = data.get('habit_id')
            checkin_date = data.get('checkin_date')
            
            if not habit_id or not checkin_date:
                self.send_json_response({"success": False, "message": "习惯ID和日期为必填项"}, 400)
                return
            
            habit = next((h for h in MOCK_HABITS if h['id'] == habit_id), None)
            if not habit:
                self.send_json_response({"success": False, "message": "习惯不存在"}, 404)
                return
            
            new_checkin = {
                "id": len(MOCK_CHECKINS) + 1,
                "habit_id": habit_id,
                "user_id": 1,
                "checkin_date": checkin_date,
                "checkin_time": "12:00:00",
                "status": "completed",
                "points_earned": habit['points'],
                "note": data.get('note', ''),
                "created_at": get_beijing_iso_str()
            }
            MOCK_CHECKINS.insert(0, new_checkin)
            
            self.send_json_response({
                "success": True,
                "data": new_checkin,
                "message": "补打卡成功"
            }, 201)
            return
        
        # 404
        self.send_json_response({"success": False, "message": "API not found"}, 404)
    
    def do_PUT(self):
        """处理PUT请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        data = self.read_body()
        
        # 更新用户信息
        if path == '/api/auth/profile':
            global MOCK_USER
            MOCK_USER['nickname'] = data.get('nickname', MOCK_USER['nickname'])
            MOCK_USER['email'] = data.get('email', MOCK_USER['email'])
            MOCK_USER['phone'] = data.get('phone', MOCK_USER['phone'])
            MOCK_USER['avatar'] = data.get('avatar', MOCK_USER['avatar'])
            MOCK_USER['updated_at'] = get_beijing_iso_str()
            
            self.send_json_response({"success": True, "data": MOCK_USER, "message": "个人信息更新成功"})
            return
        
        # 修改密码
        if path == '/api/auth/password':
            old_password = data.get('oldPassword', '')
            new_password = data.get('newPassword', '')
            
            if not old_password or not new_password:
                self.send_json_response({"success": False, "message": "原密码和新密码为必填项"}, 400)
                return
            
            if len(new_password) < 6:
                self.send_json_response({"success": False, "message": "新密码至少6位"}, 400)
                return
            
            self.send_json_response({"success": True, "message": "密码修改成功"})
            return
        
        # 更新习惯 /api/habits/:id
        match = re.match(r'^/api/habits/(\d+)$', path)
        if match:
            habit_id = int(match.group(1))
            habit = next((h for h in MOCK_HABITS if h['id'] == habit_id), None)
            
            if not habit:
                self.send_json_response({"success": False, "message": "习惯不存在"}, 404)
                return
            
            habit['name'] = data.get('name', habit['name'])
            habit['description'] = data.get('description', habit['description'])
            habit['icon'] = data.get('icon', habit['icon'])
            habit['color'] = data.get('color', habit['color'])
            habit['habit_type'] = data.get('habit_type', habit['habit_type'])
            habit['points'] = data.get('points', habit['points'])
            habit['status'] = data.get('status', habit['status'])
            habit['updated_at'] = get_beijing_iso_str()
            
            self.send_json_response({"success": True, "data": habit, "message": "习惯更新成功"})
            return
        
        self.send_json_response({"success": False, "message": "API not found"}, 404)
    
    def do_DELETE(self):
        """处理DELETE请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 删除习惯 /api/habits/:id
        match = re.match(r'^/api/habits/(\d+)$', path)
        if match:
            habit_id = int(match.group(1))
            habit = next((h for h in MOCK_HABITS if h['id'] == habit_id), None)
            
            if not habit:
                self.send_json_response({"success": False, "message": "习惯不存在"}, 404)
                return
            
            habit['status'] = 'deleted'
            self.send_json_response({"success": True, "message": "习惯删除成功"})
            return
        
        # 取消打卡 /api/checkins/:id
        match = re.match(r'^/api/checkins/(\d+)$', path)
        if match:
            checkin_id = int(match.group(1))
            global MOCK_CHECKINS
            MOCK_CHECKINS = [c for c in MOCK_CHECKINS if c['id'] != checkin_id]
            self.send_json_response({"success": True, "message": "打卡已取消"})
            return
        
        # 清理日志
        if path == '/api/logs/cleanup':
            self.send_json_response({"success": True, "data": {"deleted": 10}, "message": "日志清理成功"})
            return
        
        self.send_json_response({"success": False, "message": "API not found"}, 404)

def main():
    print("=" * 60)
    print("   打卡助手 Pro - 测试服务器")
    print("=" * 60)
    print(f"\n启动测试服务器...")
    print(f"访问地址: http://localhost:{PORT}")
    print(f"\n测试账号:")
    print("  - testuser / user123")
    print("  - admin / admin123")
    print("\n功能测试:")
    print("  - 登录/注册页面")
    print("  - 习惯管理 (增删改查)")
    print("  - 打卡功能 (打卡/补打卡/取消)")
    print("  - 数据分析仪表盘")
    print("  - 日志查询 (系统日志/登录日志)")
    print("  - 用户管理 (资料修改/密码修改)")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60 + "\n")
    
    with socketserver.TCPServer(("", PORT), MockAPIHandler) as httpd:
        httpd.serve_forever()

if __name__ == '__main__':
    main()
