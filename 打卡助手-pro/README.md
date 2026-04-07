# 打卡助手 Pro - 本地化Web测试版本

基于本地化运营的学习打卡助手Web测试版本，拥有完整的用户数据库、前端表单编辑功能、历史日志查询和用户数据分析面板。

## 功能特性

### 核心功能
- ✅ **用户认证系统** - JWT Token认证，支持注册/登录/密码修改
- ✅ **习惯管理** - 完整的CRUD操作，支持图标/颜色自定义
- ✅ **打卡系统** - 每日打卡/补打卡，连续天数计算
- ✅ **学习计划** - 创建/管理学习计划，支持多种重复类型
- ✅ **积分系统** - 打卡积分，积分记录和统计

### 数据分析
- ✅ **仪表盘** - 可视化展示打卡数据
- ✅ **趋势分析** - 日/周/月打卡趋势
- ✅ **习惯分析** - 各习惯完成情况统计
- ✅ **积分统计** - 积分来源和趋势分析

### 日志系统
- ✅ **操作日志** - 记录所有用户操作
- ✅ **登录日志** - 记录登录/登出行为
- ✅ **日志查询** - 支持多条件筛选查询
- ✅ **日志导出** - 支持导出日志数据

## 技术栈

- **后端**: Node.js + Express + SQLite
- **前端**: HTML5 + CSS3 + JavaScript
- **认证**: JWT + bcryptjs
- **日志**: Winston
- **数据可视化**: Chart.js

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 初始化数据库

```bash
npm run init-db
```

### 3. 导入测试数据（可选）

```bash
npm run seed
```

### 4. 启动服务

```bash
# 生产模式
npm start

# 开发模式（热重载）
npm run dev
```

### 5. 访问应用

- 首页: http://localhost:3000
- 登录: http://localhost:3000/login
- 数据面板: http://localhost:3000/dashboard

## 测试账号

导入测试数据后，可使用以下账号登录：

- **管理员**: admin / admin123
- **测试用户**: testuser / user123

## 项目结构

```
打卡助手-pro/
├── server/                 # 后端服务
│   ├── config/            # 配置文件
│   ├── middleware/        # 中间件
│   ├── routes/            # API路由
│   ├── utils/             # 工具函数
│   ├── app.js             # 服务入口
│   ├── init-db.js         # 数据库初始化
│   └── seed-data.js       # 测试数据
├── public/                # 前端文件
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── pages/
├── logs/                  # 日志文件
├── package.json
└── README.md
```

## API接口

### 认证模块
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/profile` - 获取用户信息
- `PUT /api/auth/profile` - 更新用户信息
- `PUT /api/auth/password` - 修改密码

### 习惯管理
- `GET /api/habits` - 获取习惯列表
- `POST /api/habits` - 创建习惯
- `GET /api/habits/:id` - 获取习惯详情
- `PUT /api/habits/:id` - 更新习惯
- `DELETE /api/habits/:id` - 删除习惯

### 打卡功能
- `GET /api/checkins` - 获取打卡记录
- `POST /api/checkins` - 打卡
- `POST /api/checkins/makeup` - 补打卡
- `DELETE /api/checkins/:id` - 取消打卡
- `GET /api/checkins/stats/overview` - 打卡统计

### 数据分析
- `GET /api/analytics/dashboard` - 仪表盘数据
- `GET /api/analytics/habits` - 习惯分析
- `GET /api/analytics/trends` - 趋势分析
- `GET /api/analytics/points` - 积分统计

### 日志查询
- `GET /api/logs/system` - 系统日志
- `GET /api/logs/login` - 登录日志
- `GET /api/logs/stats` - 日志统计

## 数据库表结构

### users - 用户表
存储用户基本信息和统计

### habits - 习惯表
存储用户创建的习惯

### checkins - 打卡记录表
存储每日打卡记录

### study_plans - 学习计划表
存储学习计划

### system_logs - 系统日志表
存储用户操作日志

### login_logs - 登录日志表
存储登录/登出记录

### user_points - 用户积分表
存储积分变动记录

## 开发计划

- [x] Phase 1: 基础架构搭建
- [x] Phase 2: 认证与核心功能
- [ ] Phase 3: 前端改造
- [ ] Phase 4: 数据分析面板
- [ ] Phase 5: 日志系统完善

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License
