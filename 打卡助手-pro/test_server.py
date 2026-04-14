#!/usr/bin/env python3
"""
松鼠打卡 - 测试服务器
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
import urllib.request
import ssl

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
MOCK_USER_POINTS = 150

MOCK_USER = {
    "id": 1,
    "username": "testuser",
    "nickname": "测试用户",
    "email": "test@example.com",
    "phone": "13800138000",
    "avatar": None,
    "role": "user",
    "total_points": MOCK_USER_POINTS,
    "continuous_days": 7,
    "total_checkins": 45,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": get_beijing_iso_str()
}

MOCK_HABITS = [
    # 学习习惯 (1-12)
    {"id": 1, "name": "认真完成各科作业", "icon": "book", "color": "#22C55E", "habit_type": "daily_once", "points": 2, "description": "按时认真完成各科作业", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 2, "name": "复习今日所学内容", "icon": "book", "color": "#3B82F6", "habit_type": "daily_once", "points": 2, "description": "当天复习学习的内容", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 3, "name": "预习明日要学课程", "icon": "calendar", "color": "#8B5CF6", "habit_type": "daily_once", "points": 3, "description": "提前预习第二天的课程", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 4, "name": "每日练字15分钟", "icon": "edit", "color": "#F97316", "habit_type": "daily_once", "points": 2, "description": "练习书法15分钟", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 5, "name": "坐姿、握笔姿势标准", "icon": "user", "color": "#22C55E", "habit_type": "daily_once", "points": 2, "description": "保持正确的坐姿和握笔姿势", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 6, "name": "课外书阅读30分钟", "icon": "book", "color": "#A855F7", "habit_type": "daily_once", "points": 5, "description": "每天阅读课外书30分钟", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 7, "name": "学习不无故离开座位", "icon": "target", "color": "#3B82F6", "habit_type": "daily_once", "points": 5, "description": "学习时专注不走动", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 8, "name": "阅读理解1篇", "icon": "file", "color": "#3B82F6", "habit_type": "daily_once", "points": 3, "description": "完成阅读理解练习1篇", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 9, "name": "看图写话1篇", "icon": "edit", "color": "#A855F7", "habit_type": "daily_once", "points": 5, "description": "完成看图写话练习1篇", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 10, "name": "摘抄好词好句30个", "icon": "edit", "color": "#F97316", "habit_type": "daily_once", "points": 3, "description": "摘抄好词好句30个", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 11, "name": "口算题50道", "icon": "activity", "color": "#22C55E", "habit_type": "daily_multi", "points": 2, "description": "完成口算题50道", "status": "active", "created_at": "2024-01-01T00:00:00", "max_checkins": 3},
    {"id": 12, "name": "听力1篇", "icon": "headphones", "color": "#3B82F6", "habit_type": "daily_once", "points": 5, "description": "完成听力练习1篇", "status": "active", "created_at": "2024-01-01T00:00:00"},
    
    # 生活习惯 (13-24)
    {"id": 13, "name": "主动洗澡", "icon": "droplet", "color": "#3B82F6", "habit_type": "daily_once", "points": 2, "description": "主动洗澡保持卫生", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 14, "name": "整理书包、课桌", "icon": "box", "color": "#F97316", "habit_type": "daily_multi", "points": 1, "description": "保持书包和课桌整洁", "status": "active", "created_at": "2024-01-01T00:00:00", "max_checkins": 2},
    {"id": 15, "name": "吃饭认真、不挑食", "icon": "heart", "color": "#22C55E", "habit_type": "daily_once", "points": 1, "description": "好好吃饭，不挑食", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 16, "name": "吃饭不超过20分钟", "icon": "clock", "color": "#3B82F6", "habit_type": "daily_once", "points": 1, "description": "在20分钟内吃完饭", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 17, "name": "按时睡觉、起床", "icon": "moon", "color": "#A855F7", "habit_type": "daily_once", "points": 2, "description": "按时作息不拖延", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 18, "name": "主动做家务", "icon": "home", "color": "#EC4899", "habit_type": "daily_multi", "points": 2, "description": "主动帮忙做家务", "status": "active", "created_at": "2024-01-01T00:00:00", "max_checkins": 3},
    {"id": 19, "name": "照顾弟弟妹妹", "icon": "heart", "color": "#EC4899", "habit_type": "daily_once", "points": 2, "description": "照顾和陪伴弟弟妹妹", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 20, "name": "每日运动30分钟", "icon": "activity", "color": "#22C55E", "habit_type": "daily_once", "points": 3, "description": "每天运动锻炼30分钟", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 21, "name": "作业本整齐", "icon": "check", "color": "#22C55E", "habit_type": "daily_once", "points": 2, "description": "作业本书写整齐", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 22, "name": "默写满分", "icon": "star", "color": "#F97316", "habit_type": "daily_once", "points": 5, "description": "默写测试得满分", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 23, "name": "考试95分以上", "icon": "trophy", "color": "#F97316", "habit_type": "daily_once", "points": 5, "description": "考试成绩95分以上", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 24, "name": "获得学校的奖状", "icon": "star", "color": "#F59E0B", "habit_type": "daily_once", "points": 10, "description": "获得学校颁发的奖状", "status": "active", "created_at": "2024-01-01T00:00:00"},
    
    # 品德习惯 (25-30)
    {"id": 25, "name": "一天不发脾气", "icon": "smile", "color": "#EC4899", "habit_type": "daily_once", "points": 3, "description": "全天保持好情绪", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 26, "name": "尊敬长辈、不顶嘴", "icon": "heart", "color": "#EC4899", "habit_type": "daily_once", "points": 3, "description": "尊敬长辈，听话不顶嘴", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 27, "name": "主动和认识的人打招呼", "icon": "user", "color": "#3B82F6", "habit_type": "daily_multi", "points": 2, "description": "见到认识的人主动打招呼", "status": "active", "created_at": "2024-01-01T00:00:00", "max_checkins": 5},
    {"id": 28, "name": "公共场合不大声喧哗", "icon": "volume", "color": "#A855F7", "habit_type": "daily_once", "points": 2, "description": "在公共场合保持安静", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 29, "name": "遇到难题想办法解决", "icon": "lightbulb", "color": "#F97316", "habit_type": "daily_once", "points": 5, "description": "遇到困难主动思考解决", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 30, "name": "遇到问题不哭", "icon": "shield", "color": "#3B82F6", "habit_type": "daily_once", "points": 5, "description": "遇到问题不哭不闹", "status": "active", "created_at": "2024-01-01T00:00:00"},
    
    # ========== 加分习惯 (31-60) ==========
    # 健康习惯
    {"id": 31, "name": "喝水8杯", "icon": "droplet", "color": "#3B82F6", "habit_type": "daily_multi", "points": 1, "description": "每天喝8杯水，保持水分充足", "status": "active", "created_at": "2024-01-01T00:00:00", "max_checkins": 8},
    {"id": 32, "name": "冥想10分钟", "icon": "moon", "color": "#8B5CF6", "habit_type": "daily_once", "points": 3, "description": "每天冥想10分钟，放松身心", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 33, "name": "吃水果", "icon": "heart", "color": "#EF4444", "habit_type": "daily_once", "points": 1, "description": "每天吃一份新鲜水果", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 34, "name": "眼保健操", "icon": "activity", "color": "#10B981", "habit_type": "daily_multi", "points": 1, "description": "每天做眼保健操保护视力", "status": "active", "created_at": "2024-01-01T00:00:00", "max_checkins": 3},
    {"id": 35, "name": "深呼吸练习", "icon": "activity", "color": "#06B6D4", "habit_type": "daily_once", "points": 2, "description": "深呼吸放松练习5分钟", "status": "active", "created_at": "2024-01-01T00:00:00"},
    
    # 学习与成长
    {"id": 36, "name": "背单词20个", "icon": "book", "color": "#6366F1", "habit_type": "daily_once", "points": 3, "description": "每天背诵20个新单词", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 37, "name": "英语听力", "icon": "volume", "color": "#F59E0B", "habit_type": "daily_once", "points": 5, "description": "每天练习英语听力15分钟", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 38, "name": "写代码练习", "icon": "box", "color": "#14B8A6", "habit_type": "daily_once", "points": 5, "description": "每天编程练习1小时", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 39, "name": "听知识播客", "icon": "headphones", "color": "#EC4899", "habit_type": "daily_once", "points": 2, "description": "每天听一期知识类播客", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 40, "name": "写日记100字", "icon": "edit", "color": "#64748B", "habit_type": "daily_once", "points": 2, "description": "每天写100字日记", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 41, "name": "学新技能", "icon": "lightbulb", "color": "#F97316", "habit_type": "daily_once", "points": 5, "description": "每天学习一项新技能", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 42, "name": "看TED演讲", "icon": "volume", "color": "#EF4444", "habit_type": "daily_once", "points": 3, "description": "每天看一个TED演讲", "status": "active", "created_at": "2024-01-01T00:00:00"},
    
    # 工作效率
    {"id": 43, "name": "整理桌面", "icon": "home", "color": "#06B6D4", "habit_type": "daily_once", "points": 1, "description": "每天整理工作桌面", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 44, "name": "番茄工作法", "icon": "clock", "color": "#EF4444", "habit_type": "daily_multi", "points": 2, "description": "完成番茄工作周期", "status": "active", "created_at": "2024-01-01T00:00:00", "max_checkins": 4},
    {"id": 45, "name": "复盘总结", "icon": "target", "color": "#8B5CF6", "habit_type": "daily_once", "points": 3, "description": "每天复盘当日工作与学习", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 46, "name": "制定明日计划", "icon": "calendar", "color": "#3B82F6", "habit_type": "daily_once", "points": 2, "description": "每天制定明日计划", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 47, "name": "阅读技术文章", "icon": "file", "color": "#14B8A6", "habit_type": "daily_once", "points": 2, "description": "每天阅读一篇技术文章", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 48, "name": "记录灵感", "icon": "bookmark", "color": "#F59E0B", "habit_type": "daily_multi", "points": 1, "description": "随时记录灵感和想法", "status": "active", "created_at": "2024-01-01T00:00:00", "max_checkins": 5},
    
    # 社交与沟通
    {"id": 49, "name": "联系朋友", "icon": "user", "color": "#EC4899", "habit_type": "daily_once", "points": 2, "description": "主动联系一位朋友", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 50, "name": "赞美他人", "icon": "heart", "color": "#F472B6", "habit_type": "daily_multi", "points": 1, "description": "真诚地赞美身边的人", "status": "active", "created_at": "2024-01-01T00:00:00", "max_checkins": 3},
    {"id": 51, "name": "分享知识", "icon": "lightbulb", "color": "#FBBF24", "habit_type": "daily_once", "points": 3, "description": "向他人分享一个知识点", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 52, "name": "保持微笑", "icon": "smile", "color": "#F59E0B", "habit_type": "daily_once", "points": 1, "description": "全天保持微笑，积极面对", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 53, "name": "倾听他人", "icon": "headphones", "color": "#6366F1", "habit_type": "daily_once", "points": 2, "description": "认真倾听他人说话", "status": "active", "created_at": "2024-01-01T00:00:00"},
    
    # 生活习惯
    {"id": 54, "name": "整理衣物", "icon": "home", "color": "#10B981", "habit_type": "daily_once", "points": 1, "description": "每天整理衣物和床铺", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 55, "name": "垃圾分类", "icon": "box", "color": "#22C55E", "habit_type": "daily_once", "points": 1, "description": "认真做好垃圾分类", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 56, "name": "节约用水", "icon": "droplet", "color": "#3B82F6", "habit_type": "daily_once", "points": 1, "description": "注意节约用水", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 57, "name": "断舍离", "icon": "shield", "color": "#64748B", "habit_type": "daily_once", "points": 2, "description": "每天丢弃一件不需要的物品", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 58, "name": "记账", "icon": "edit", "color": "#F97316", "habit_type": "daily_once", "points": 2, "description": "记录每日收支情况", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 59, "name": "不刷短视频", "icon": "shield", "color": "#EF4444", "habit_type": "daily_once", "points": 5, "description": "今天不刷短视频，专注生活", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 60, "name": "不抱怨", "icon": "smile", "color": "#10B981", "habit_type": "daily_once", "points": 3, "description": "一整天不抱怨，保持积极", "status": "active", "created_at": "2024-01-01T00:00:00"},
    
    # ========== 减分习惯 (61-90) ==========
    # 学习不良习惯
    {"id": 61, "name": "不认真完成各科作业", "icon": "alert-circle", "color": "#EF4444", "habit_type": "daily_once", "points": -5, "description": "作业马虎、不认真", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 62, "name": "没有复习今日所学", "icon": "x-circle", "color": "#DC2626", "habit_type": "daily_once", "points": -1, "description": "没有复习当天学习内容", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 63, "name": "没有预习明日课程", "icon": "x-circle", "color": "#DC2626", "habit_type": "daily_once", "points": -2, "description": "没有预习第二天课程", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 64, "name": "没有进行每日练字", "icon": "x-circle", "color": "#DC2626", "habit_type": "daily_once", "points": -1, "description": "没有完成每日练字任务", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 65, "name": "坐姿、握笔不标准", "icon": "alert-triangle", "color": "#F97316", "habit_type": "daily_once", "points": -1, "description": "坐姿或握笔姿势不正确", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 66, "name": "没有进行课外书阅读", "icon": "x-circle", "color": "#DC2626", "habit_type": "daily_once", "points": -2, "description": "没有完成课外阅读", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 67, "name": "做作业好动、不认真", "icon": "alert-circle", "color": "#EF4444", "habit_type": "daily_once", "points": -5, "description": "做作业时好动、分心", "status": "active", "created_at": "2024-01-01T00:00:00"},
    
    # 生活不良习惯
    {"id": 68, "name": "不主动洗澡", "icon": "x-circle", "color": "#DC2626", "habit_type": "daily_once", "points": -2, "description": "不主动洗澡，需要催促", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 69, "name": "不主动整理书包、课桌", "icon": "x-square", "color": "#DC2626", "habit_type": "daily_multi", "points": -1, "description": "书包课桌凌乱不整理", "status": "active", "created_at": "2024-01-01T00:00:00", "max_checkins": 2},
    {"id": 70, "name": "吃饭不认真、挑食", "icon": "alert-circle", "color": "#F97316", "habit_type": "daily_once", "points": -2, "description": "吃饭挑食、不认真", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 71, "name": "吃饭超过30分钟", "icon": "clock", "color": "#F97316", "habit_type": "daily_once", "points": -1, "description": "吃饭时间超过30分钟", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 72, "name": "睡觉、起床拖拉磨蹭", "icon": "alert-triangle", "color": "#F59E0B", "habit_type": "daily_once", "points": -1, "description": "睡觉起床拖延磨蹭", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 73, "name": "乱扔东西、垃圾", "icon": "trash-2", "color": "#EF4444", "habit_type": "daily_multi", "points": -3, "description": "随意乱扔东西和垃圾", "status": "active", "created_at": "2024-01-01T00:00:00", "max_checkins": 5},
    {"id": 74, "name": "不尊老爱幼", "icon": "alert-circle", "color": "#EF4444", "habit_type": "daily_once", "points": -3, "description": "不尊敬老人、不爱护幼小", "status": "active", "created_at": "2024-01-01T00:00:00"},
    
    # 成绩与表现
    {"id": 75, "name": "没完成运动任务", "icon": "x-circle", "color": "#DC2626", "habit_type": "daily_once", "points": -3, "description": "没有完成每日运动任务", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 76, "name": "单元测试85分以下", "icon": "alert-triangle", "color": "#F97316", "habit_type": "daily_once", "points": -3, "description": "单元测试成绩85分以下", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 77, "name": "单元测试70分以下", "icon": "alert-circle", "color": "#EF4444", "habit_type": "daily_once", "points": -5, "description": "单元测试成绩70分以下", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 78, "name": "单元测试不及格", "icon": "x-octagon", "color": "#B91C1C", "habit_type": "daily_once", "points": -10, "description": "单元测试成绩不及格", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 79, "name": "被老师批评", "icon": "alert-circle", "color": "#B91C1C", "habit_type": "daily_once", "points": -10, "description": "在学校被老师批评", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 80, "name": "老师找家长", "icon": "phone-missed", "color": "#7F1D1D", "habit_type": "daily_once", "points": -15, "description": "老师联系家长沟通问题", "status": "active", "created_at": "2024-01-01T00:00:00"},
    
    # 品德与行为问题
    {"id": 81, "name": "乱发脾气", "icon": "frown", "color": "#EF4444", "habit_type": "daily_multi", "points": -3, "description": "无缘无故发脾气", "status": "active", "created_at": "2024-01-01T00:00:00", "max_checkins": 3},
    {"id": 82, "name": "和长辈顶嘴", "icon": "alert-circle", "color": "#EF4444", "habit_type": "daily_multi", "points": -5, "description": "和长辈顶嘴不听话", "status": "active", "created_at": "2024-01-01T00:00:00", "max_checkins": 3},
    {"id": 83, "name": "说脏话", "icon": "alert-triangle", "color": "#DC2626", "habit_type": "daily_multi", "points": -2, "description": "说脏话、骂人", "status": "active", "created_at": "2024-01-01T00:00:00", "max_checkins": 3},
    {"id": 84, "name": "无故哭闹", "icon": "alert-triangle", "color": "#F97316", "habit_type": "daily_multi", "points": -3, "description": "无缘无故哭闹", "status": "active", "created_at": "2024-01-01T00:00:00", "max_checkins": 3},
    {"id": 85, "name": "撒谎、屡教不改", "icon": "x-octagon", "color": "#B91C1C", "habit_type": "daily_once", "points": -10, "description": "撒谎并且屡教不改", "status": "active", "created_at": "2024-01-01T00:00:00"},
    
    # 其他不良行为
    {"id": 86, "name": "与同学发生冲突", "icon": "users", "color": "#EF4444", "habit_type": "daily_once", "points": -5, "description": "与同学打架或吵架", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 87, "name": "沉迷于电子游戏", "icon": "monitor", "color": "#DC2626", "habit_type": "daily_once", "points": -5, "description": "过度玩游戏影响学习", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 88, "name": "不按时完成作业", "icon": "clock", "color": "#F97316", "habit_type": "daily_once", "points": -3, "description": "作业拖延不按时完成", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 89, "name": "课堂纪律问题", "icon": "volume-x", "color": "#DC2626", "habit_type": "daily_once", "points": -2, "description": "上课说话、走神等", "status": "active", "created_at": "2024-01-01T00:00:00"},
    {"id": 90, "name": "损坏公共物品", "icon": "tool", "color": "#B91C1C", "habit_type": "daily_once", "points": -5, "description": "故意损坏公物或他人物品", "status": "active", "created_at": "2024-01-01T00:00:00"}
]

MOCK_CHECKINS = []
MOCK_LOGS = []
MOCK_LOGIN_LOGS = []

# 生成模拟打卡记录（只生成历史数据，不包含今天）
for i in range(1, 8):  # 过去7天
    date = (get_beijing_time() - timedelta(days=i)).strftime('%Y-%m-%d')
    for habit_id in [1, 2]:
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
                    "name": "松鼠打卡 API (测试模式)",
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
            user = MOCK_USER.copy()
            user['total_points'] = MOCK_USER_POINTS
            self.send_json_response({"success": True, "data": user})
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
            today_checkins_list = [c for c in MOCK_CHECKINS if c['checkin_date'] == today]
            today_checkins = len(today_checkins_list)
            today_points = sum(c.get('points_earned', 0) for c in today_checkins_list)
            
            self.send_json_response({
                "success": True,
                "data": {
                    "today": {"habits_completed": today_checkins, "points": today_points},
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
            
            global MOCK_USER_POINTS
            MOCK_USER_POINTS += points
            
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
            
            global MOCK_USER_POINTS
            MOCK_USER_POINTS += habit['points']
            
            self.send_json_response({
                "success": True,
                "data": new_checkin,
                "message": "补打卡成功"
            }, 201)
            return
        
        # ========== AI学习计划生成 ==========
        if path == '/api/ai/generate-study-plans':
            prompt = data.get('prompt', '')
            hours = data.get('hours', 2)
            style = data.get('style', 'balanced')
            
            if not prompt:
                self.send_json_response({"success": False, "message": "请输入学习目标"}, 400)
                return
            
            try:
                # 调用KIM API生成学习计划
                generated_plans = self.call_kim_api(prompt, hours, style)
                
                self.send_json_response({
                    "success": True,
                    "data": generated_plans,
                    "message": "学习计划生成成功"
                })
            except Exception as e:
                print(f"AI生成失败: {e}")
                # 如果API调用失败，使用模拟数据
                fallback_plans = self.generate_mock_study_plans(prompt, hours, style)
                self.send_json_response({
                    "success": True,
                    "data": fallback_plans,
                    "message": "学习计划生成成功（模拟模式）"
                })
            return
        
        # 404
        self.send_json_response({"success": False, "message": "API not found"}, 404)
    
    def call_kim_api(self, prompt, hours, style):
        """调用KIM大模型API生成学习计划"""
        # KIM API配置 - 使用Moonshot API
        KIM_API_KEY = os.environ.get('KIMI_API_KEY', '')
        KIM_API_URL = 'https://api.moonshot.cn/v1/chat/completions'
        
        # 构建系统提示词
        system_prompt = '''你是一个专业的学习规划助手。请根据用户的需求，生成合理的学习计划。
要求：
1. 每个计划包含：name（任务名称）、time（预计时间，分钟）、subject（学科/类别）
2. 总时间应控制在用户可用时间范围内
3. 任务要具体、可执行
4. 返回JSON数组格式，如：[{"name": "数学公式复习", "time": 30, "subject": "数学"}]
5. 不要添加任何解释，只返回JSON数组'''
        
        # 构建用户提示词
        style_desc = {
            'intensive': '紧凑高效',
            'relaxed': '轻松舒适',
            'balanced': '均衡适中'
        }.get(style, '均衡适中')
        
        user_prompt = f'''请为我生成学习计划。
学习目标：{prompt}
可用时间：{hours}小时
学习风格：{style_desc}

请返回JSON数组格式，每个元素包含name、time、subject字段。'''
        
        # 如果没有配置API Key，使用模拟数据
        if not KIM_API_KEY:
            print("未配置KIMI_API_KEY环境变量，使用模拟数据")
            return self.generate_mock_study_plans(prompt, hours, style)
        
        # 构建请求
        request_body = {
            'model': 'moonshot-v1-8k',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.7,
            'response_format': {'type': 'json_object'}
        }
        
        # 发送请求
        req = urllib.request.Request(
            KIM_API_URL,
            data=json.dumps(request_body).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {KIM_API_KEY}'
            },
            method='POST'
        )
        
        # 创建SSL上下文（忽略证书验证）
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            content = result['choices'][0]['message']['content']
            # 解析JSON响应
            plans = json.loads(content)
            if isinstance(plans, dict) and 'plans' in plans:
                plans = plans['plans']
            return plans
    
    def generate_mock_study_plans(self, prompt, hours, style):
        """生成模拟学习计划（API失败时备用）"""
        total_minutes = hours * 60
        plans = []
        
        # 根据关键词生成相关计划
        if '数学' in prompt or 'math' in prompt.lower():
            plans = [
                {'name': '数学公式复习', 'time': round(total_minutes * 0.25), 'subject': '数学'},
                {'name': '数学例题练习', 'time': round(total_minutes * 0.35), 'subject': '数学'},
                {'name': '数学错题整理', 'time': round(total_minutes * 0.25), 'subject': '数学'},
                {'name': '数学模拟测试', 'time': round(total_minutes * 0.15), 'subject': '数学'}
            ]
        elif '英语' in prompt or 'english' in prompt.lower():
            plans = [
                {'name': '英语单词背诵', 'time': round(total_minutes * 0.3), 'subject': '英语'},
                {'name': '英语听力练习', 'time': round(total_minutes * 0.25), 'subject': '英语'},
                {'name': '英语阅读理解', 'time': round(total_minutes * 0.25), 'subject': '英语'},
                {'name': '英语写作练习', 'time': round(total_minutes * 0.2), 'subject': '英语'}
            ]
        elif '语文' in prompt or 'chinese' in prompt.lower():
            plans = [
                {'name': '语文课文朗读', 'time': round(total_minutes * 0.2), 'subject': '语文'},
                {'name': '语文古诗词背诵', 'time': round(total_minutes * 0.25), 'subject': '语文'},
                {'name': '语文阅读理解', 'time': round(total_minutes * 0.3), 'subject': '语文'},
                {'name': '语文作文练习', 'time': round(total_minutes * 0.25), 'subject': '语文'}
            ]
        elif '物理' in prompt or '化学' in prompt or '生物' in prompt:
            subject = '物理' if '物理' in prompt else '化学' if '化学' in prompt else '生物'
            plans = [
                {'name': f'{subject}概念梳理', 'time': round(total_minutes * 0.3), 'subject': subject},
                {'name': f'{subject}公式推导', 'time': round(total_minutes * 0.25), 'subject': subject},
                {'name': f'{subject}实验题练习', 'time': round(total_minutes * 0.25), 'subject': subject},
                {'name': f'{subject}综合测试', 'time': round(total_minutes * 0.2), 'subject': subject}
            ]
        else:
            # 通用计划
            count = 4 if style == 'intensive' else 3 if style == 'relaxed' else 4
            time_per_plan = round(total_minutes / count)
            plans = [
                {'name': '知识点复习', 'time': time_per_plan, 'subject': '综合'},
                {'name': '练习题完成', 'time': time_per_plan, 'subject': '综合'},
                {'name': '错题整理', 'time': time_per_plan, 'subject': '综合'}
            ]
            if count == 4:
                plans.append({'name': '模拟测试', 'time': time_per_plan, 'subject': '综合'})
        
        # 根据风格调整时间
        if style == 'intensive':
            for p in plans:
                p['time'] = round(p['time'] * 0.9)
        elif style == 'relaxed':
            for p in plans:
                p['time'] = round(p['time'] * 1.1)
        
        return plans
    
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
            checkin = next((c for c in MOCK_CHECKINS if c['id'] == checkin_id), None)
            global MOCK_CHECKINS
            MOCK_CHECKINS = [c for c in MOCK_CHECKINS if c['id'] != checkin_id]
            if checkin:
                global MOCK_USER_POINTS
                MOCK_USER_POINTS -= checkin.get('points_earned', 0)
            self.send_json_response({"success": True, "message": "打卡已取消"})
            return
        
        # 清理日志
        if path == '/api/logs/cleanup':
            self.send_json_response({"success": True, "data": {"deleted": 10}, "message": "日志清理成功"})
            return
        
        self.send_json_response({"success": False, "message": "API not found"}, 404)

def main():
    import sys
    import io
    # 设置输出编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 60)
    print("   松鼠打卡 - 测试服务器")
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
    print("  - AI学习计划生成 (NEW)")
    print("  - 日志查询 (系统日志/登录日志)")
    print("  - 用户管理 (资料修改/密码修改)")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60 + "\n")
    
    with socketserver.TCPServer(("", PORT), MockAPIHandler) as httpd:
        httpd.serve_forever()

if __name__ == '__main__':
    main()
