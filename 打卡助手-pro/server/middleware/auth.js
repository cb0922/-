const jwt = require('jsonwebtoken');
const { dbGet } = require('../config/database');
const response = require('../utils/response');

// JWT密钥
const JWT_SECRET = process.env.JWT_SECRET || 'daka-helper-secret-key-2024';
const JWT_EXPIRES = process.env.JWT_EXPIRES || '7d';

// 生成Token
const generateToken = (userId, username, role) => {
    return jwt.sign(
        { userId, username, role },
        JWT_SECRET,
        { expiresIn: JWT_EXPIRES }
    );
};

// 验证Token中间件
const authMiddleware = async (req, res, next) => {
    try {
        const authHeader = req.headers.authorization;
        
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return response.unauthorized(res, '请提供有效的访问令牌');
        }

        const token = authHeader.substring(7);
        
        // 验证Token
        const decoded = jwt.verify(token, JWT_SECRET);
        
        // 检查用户是否仍然存在且有效
        const user = await dbGet(
            'SELECT id, username, nickname, role, status FROM users WHERE id = ?',
            [decoded.userId]
        );

        if (!user) {
            return response.unauthorized(res, '用户不存在');
        }

        if (user.status !== 'active') {
            return response.forbidden(res, '账号已被禁用');
        }

        // 将用户信息附加到请求对象
        req.user = {
            id: user.id,
            username: user.username,
            nickname: user.nickname,
            role: user.role
        };

        next();
    } catch (error) {
        if (error.name === 'TokenExpiredError') {
            return response.unauthorized(res, '登录已过期，请重新登录');
        }
        if (error.name === 'JsonWebTokenError') {
            return response.unauthorized(res, '无效的访问令牌');
        }
        return response.serverError(res, '认证失败', error);
    }
};

// 可选认证（不强制要求登录，但会解析token）
const optionalAuth = async (req, res, next) => {
    try {
        const authHeader = req.headers.authorization;
        
        if (authHeader && authHeader.startsWith('Bearer ')) {
            const token = authHeader.substring(7);
            const decoded = jwt.verify(token, JWT_SECRET);
            
            const user = await dbGet(
                'SELECT id, username, nickname, role FROM users WHERE id = ? AND status = ?',
                [decoded.userId, 'active']
            );

            if (user) {
                req.user = {
                    id: user.id,
                    username: user.username,
                    nickname: user.nickname,
                    role: user.role
                };
            }
        }
        
        next();
    } catch (error) {
        next();
    }
};

// 管理员权限检查
const adminOnly = (req, res, next) => {
    if (!req.user || req.user.role !== 'admin') {
        return response.forbidden(res, '需要管理员权限');
    }
    next();
};

module.exports = {
    generateToken,
    authMiddleware,
    optionalAuth,
    adminOnly,
    JWT_SECRET
};
