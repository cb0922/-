const express = require('express');
const path = require('path');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const { requestLogger } = require('./middleware/logger');
const { notFoundHandler, errorHandler } = require('./middleware/error');
const response = require('./utils/response');

// 导入路由
const authRoutes = require('./routes/auth');
const habitRoutes = require('./routes/habits');
const checkinRoutes = require('./routes/checkins');
const analyticsRoutes = require('./routes/analytics');
const logRoutes = require('./routes/logs');
const pointsRoutes = require('./routes/points');

// 创建应用实例
const app = express();
const PORT = process.env.PORT || 3000;

// 中间件配置
app.use(helmet({
    contentSecurityPolicy: false // 允许加载前端资源
}));

app.use(cors({
    origin: process.env.CORS_ORIGIN || '*',
    credentials: true
}));

// 速率限制
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15分钟
    max: 1000, // 每个IP最多1000次请求
    message: '请求过于频繁，请稍后再试'
});
app.use(limiter);

// 请求体解析
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 日志记录
app.use(morgan('combined'));
app.use(requestLogger);

// 静态文件服务
app.use(express.static(path.join(__dirname, '..', 'public')));

// API路由
app.use('/api/auth', authRoutes);
app.use('/api/habits', habitRoutes);
app.use('/api/checkins', checkinRoutes);
app.use('/api/analytics', analyticsRoutes);
app.use('/api/logs', logRoutes);
app.use('/api/points', pointsRoutes);

// API根路径
app.get('/api', (req, res) => {
    response.success(res, {
        name: '松鼠打卡 API',
        version: '1.0.0',
        description: '本地化Web测试版本API',
        endpoints: {
            auth: '/api/auth',
            habits: '/api/habits',
            checkins: '/api/checkins',
            analytics: '/api/analytics',
            logs: '/api/logs'
        }
    });
});

// 健康检查
app.get('/api/health', (req, res) => {
    response.success(res, {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
    });
});

// 前端页面路由 - 所有非API请求都返回前端页面
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'public', 'index.html'));
});

app.get('/login', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'public', 'pages', 'login.html'));
});

app.get('/register', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'public', 'pages', 'register.html'));
});

app.get('/dashboard', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'public', 'pages', 'dashboard.html'));
});

app.get('/logs', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'public', 'pages', 'logs.html'));
});

app.get('/points', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'public', 'index.html'));
});

// 404处理
app.use(notFoundHandler);

// 错误处理
app.use(errorHandler);

// 启动服务器
app.listen(PORT, () => {
    console.log('========================================');
    console.log('    松鼠打卡 - 本地化Web测试版本');
    console.log('========================================');
    console.log(`\n✓ 服务启动成功！`);
    console.log(`\n访问地址：`);
    console.log(`  - 前端页面: http://localhost:${PORT}`);
    console.log(`  - API接口: http://localhost:${PORT}/api`);
    console.log(`  - 登录页面: http://localhost:${PORT}/login`);
    console.log(`  - 数据面板: http://localhost:${PORT}/dashboard`);
    console.log(`\n快捷操作：`);
    console.log(`  - 初始化数据库: npm run init-db`);
    console.log(`  - 导入测试数据: npm run seed`);
    console.log(`\n========================================`);
});

module.exports = app;
