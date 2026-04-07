const express = require('express');
const bcrypt = require('bcryptjs');
const { dbGet, dbRun } = require('../config/database');
const { generateToken, authMiddleware } = require('../middleware/auth');
const { logLogin } = require('../middleware/logger');
const response = require('../utils/response');
const { asyncHandler } = require('../middleware/error');

const router = express.Router();

// 用户注册
router.post('/register', asyncHandler(async (req, res) => {
    const { username, password, nickname, email, phone } = req.body;

    // 验证必填字段
    if (!username || !password) {
        return response.badRequest(res, '用户名和密码为必填项');
    }

    // 验证用户名格式（字母数字下划线，3-50字符）
    if (!/^[a-zA-Z0-9_]{3,50}$/.test(username)) {
        return response.badRequest(res, '用户名只能包含字母、数字和下划线，长度3-50位');
    }

    // 验证密码强度
    if (password.length < 6) {
        return response.badRequest(res, '密码长度至少6位');
    }

    // 检查用户名是否已存在
    const existingUser = await dbGet('SELECT id FROM users WHERE username = ?', [username]);
    if (existingUser) {
        return response.badRequest(res, '用户名已被注册');
    }

    // 加密密码
    const hashedPassword = await bcrypt.hash(password, 10);

    // 创建用户
    const result = await dbRun(
        `INSERT INTO users (username, password, nickname, email, phone) 
         VALUES (?, ?, ?, ?, ?)`,
        [username, hashedPassword, nickname || username, email, phone]
    );

    // 记录注册日志
    const ip = req.ip || req.connection.remoteAddress;
    const userAgent = req.headers['user-agent'];
    await logLogin(result.id, username, 'register', 'success', ip, userAgent);

    response.success(res, {
        userId: result.id,
        username,
        nickname: nickname || username
    }, '注册成功', 201);
}));

// 用户登录
router.post('/login', asyncHandler(async (req, res) => {
    const { username, password } = req.body;
    const ip = req.ip || req.connection.remoteAddress;
    const userAgent = req.headers['user-agent'];

    // 验证必填字段
    if (!username || !password) {
        await logLogin(null, username, 'login', 'failed', ip, userAgent, '缺少用户名或密码');
        return response.badRequest(res, '用户名和密码为必填项');
    }

    // 查询用户
    const user = await dbGet(
        'SELECT id, username, password, nickname, role, status, avatar FROM users WHERE username = ?',
        [username]
    );

    if (!user) {
        await logLogin(null, username, 'login', 'failed', ip, userAgent, '用户不存在');
        return response.unauthorized(res, '用户名或密码错误');
    }

    // 检查账号状态
    if (user.status !== 'active') {
        await logLogin(user.id, username, 'login', 'failed', ip, userAgent, '账号已被禁用');
        return response.forbidden(res, '账号已被禁用，请联系管理员');
    }

    // 验证密码
    const isPasswordValid = await bcrypt.compare(password, user.password);
    if (!isPasswordValid) {
        await logLogin(user.id, username, 'login', 'failed', ip, userAgent, '密码错误');
        return response.unauthorized(res, '用户名或密码错误');
    }

    // 生成Token
    const token = generateToken(user.id, user.username, user.role);

    // 记录登录成功日志
    await logLogin(user.id, username, 'login', 'success', ip, userAgent);

    response.success(res, {
        token,
        user: {
            id: user.id,
            username: user.username,
            nickname: user.nickname,
            role: user.role,
            avatar: user.avatar
        }
    }, '登录成功');
}));

// 获取当前用户信息
router.get('/profile', authMiddleware, asyncHandler(async (req, res) => {
    const user = await dbGet(
        `SELECT id, username, nickname, email, phone, avatar, role, 
                total_points, continuous_days, total_checkins,
                created_at, updated_at 
         FROM users WHERE id = ?`,
        [req.user.id]
    );

    if (!user) {
        return response.notFound(res, '用户不存在');
    }

    response.success(res, user);
}));

// 更新用户信息
router.put('/profile', authMiddleware, asyncHandler(async (req, res) => {
    const { nickname, email, phone, avatar } = req.body;

    await dbRun(
        `UPDATE users 
         SET nickname = ?, email = ?, phone = ?, avatar = ?, updated_at = CURRENT_TIMESTAMP 
         WHERE id = ?`,
        [nickname, email, phone, avatar, req.user.id]
    );

    response.success(res, null, '个人信息更新成功');
}));

// 修改密码
router.put('/password', authMiddleware, asyncHandler(async (req, res) => {
    const { oldPassword, newPassword } = req.body;

    if (!oldPassword || !newPassword) {
        return response.badRequest(res, '原密码和新密码为必填项');
    }

    if (newPassword.length < 6) {
        return response.badRequest(res, '新密码长度至少6位');
    }

    // 获取用户密码
    const user = await dbGet('SELECT password FROM users WHERE id = ?', [req.user.id]);
    if (!user) {
        return response.notFound(res, '用户不存在');
    }

    // 验证原密码
    const isPasswordValid = await bcrypt.compare(oldPassword, user.password);
    if (!isPasswordValid) {
        return response.badRequest(res, '原密码错误');
    }

    // 加密新密码
    const hashedPassword = await bcrypt.hash(newPassword, 10);

    await dbRun(
        'UPDATE users SET password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        [hashedPassword, req.user.id]
    );

    response.success(res, null, '密码修改成功');
}));

// 登出（可选：可以在这里处理token黑名单）
router.post('/logout', authMiddleware, asyncHandler(async (req, res) => {
    const ip = req.ip || req.connection.remoteAddress;
    const userAgent = req.headers['user-agent'];
    
    await logLogin(req.user.id, req.user.username, 'logout', 'success', ip, userAgent);
    
    response.success(res, null, '登出成功');
}));

module.exports = router;
