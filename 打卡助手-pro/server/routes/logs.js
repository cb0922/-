const express = require('express');
const { dbQuery, dbGet } = require('../config/database');
const { authMiddleware, adminOnly } = require('../middleware/auth');
const response = require('../utils/response');
const { asyncHandler } = require('../middleware/error');

const router = express.Router();

// 获取系统日志（管理员可查看所有，普通用户只能查看自己的）
router.get('/system', authMiddleware, asyncHandler(async (req, res) => {
    const { action, target_type, start_date, end_date, page = 1, pageSize = 20 } = req.query;
    const offset = (page - 1) * pageSize;

    let whereClause = 'WHERE 1=1';
    const params = [];

    // 非管理员只能查看自己的日志
    if (req.user.role !== 'admin') {
        whereClause += ' AND user_id = ?';
        params.push(req.user.id);
    }

    if (action) {
        whereClause += ' AND action = ?';
        params.push(action);
    }

    if (target_type) {
        whereClause += ' AND target_type = ?';
        params.push(target_type);
    }

    if (start_date) {
        whereClause += ' AND created_at >= ?';
        params.push(start_date);
    }

    if (end_date) {
        whereClause += ' AND created_at <= ?';
        params.push(end_date);
    }

    const logs = await dbQuery(
        `SELECT * FROM system_logs 
         ${whereClause}
         ORDER BY created_at DESC
         LIMIT ? OFFSET ?`,
        [...params, parseInt(pageSize), parseInt(offset)]
    );

    const countResult = await dbGet(
        `SELECT COUNT(*) as total FROM system_logs ${whereClause}`,
        params
    );

    response.paginate(res, logs, {
        page: parseInt(page),
        pageSize: parseInt(pageSize),
        total: countResult.total
    });
}));

// 获取登录日志
router.get('/login', authMiddleware, asyncHandler(async (req, res) => {
    const { action, status, start_date, end_date, page = 1, pageSize = 20 } = req.query;
    const offset = (page - 1) * pageSize;

    let whereClause = 'WHERE 1=1';
    const params = [];

    // 非管理员只能查看自己的登录日志
    if (req.user.role !== 'admin') {
        whereClause += ' AND user_id = ?';
        params.push(req.user.id);
    }

    if (action) {
        whereClause += ' AND action = ?';
        params.push(action);
    }

    if (status) {
        whereClause += ' AND status = ?';
        params.push(status);
    }

    if (start_date) {
        whereClause += ' AND created_at >= ?';
        params.push(start_date);
    }

    if (end_date) {
        whereClause += ' AND created_at <= ?';
        params.push(end_date);
    }

    const logs = await dbQuery(
        `SELECT * FROM login_logs 
         ${whereClause}
         ORDER BY created_at DESC
         LIMIT ? OFFSET ?`,
        [...params, parseInt(pageSize), parseInt(offset)]
    );

    const countResult = await dbGet(
        `SELECT COUNT(*) as total FROM login_logs ${whereClause}`,
        params
    );

    response.paginate(res, logs, {
        page: parseInt(page),
        pageSize: parseInt(pageSize),
        total: countResult.total
    });
}));

// 获取用户操作统计（仅管理员）
router.get('/stats', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const { start_date, end_date } = req.query;

    let dateFilter = '';
    const params = [];

    if (start_date) {
        dateFilter += ' AND created_at >= ?';
        params.push(start_date);
    }
    if (end_date) {
        dateFilter += ' AND created_at <= ?';
        params.push(end_date);
    }

    // 操作类型统计
    const actionStats = await dbQuery(
        `SELECT 
            action,
            COUNT(*) as count,
            COUNT(DISTINCT user_id) as users
         FROM system_logs 
         WHERE 1=1 ${dateFilter}
         GROUP BY action
         ORDER BY count DESC`,
        params
    );

    // 用户活跃度统计
    const userStats = await dbQuery(
        `SELECT 
            username,
            COUNT(*) as total_actions,
            COUNT(DISTINCT DATE(created_at)) as active_days
         FROM system_logs 
         WHERE user_id IS NOT NULL ${dateFilter}
         GROUP BY user_id
         ORDER BY total_actions DESC
         LIMIT 20`,
        params
    );

    // 登录统计
    const loginStats = await dbGet(
        `SELECT 
            COUNT(*) as total_attempts,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as fail_count
         FROM login_logs 
         WHERE 1=1 ${dateFilter}`,
        params
    );

    // 每日活跃度
    const dailyStats = await dbQuery(
        `SELECT 
            DATE(created_at) as date,
            COUNT(DISTINCT user_id) as active_users,
            COUNT(*) as total_actions
         FROM system_logs 
         WHERE user_id IS NOT NULL ${dateFilter}
         GROUP BY DATE(created_at)
         ORDER BY date DESC
         LIMIT 30`,
        params
    );

    response.success(res, {
        action_stats: actionStats,
        user_stats: userStats,
        login_stats: loginStats,
        daily_stats: dailyStats
    });
}));

// 清理日志（仅管理员）
router.delete('/cleanup', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const { days = 30, type = 'system' } = req.body;

    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);
    const cutoffStr = cutoffDate.toISOString().split('T')[0];

    let result;
    if (type === 'system' || type === 'all') {
        result = await dbGet(
            `DELETE FROM system_logs WHERE created_at < ?`,
            [cutoffStr]
        );
    }
    if (type === 'login' || type === 'all') {
        result = await dbGet(
            `DELETE FROM login_logs WHERE created_at < ?`,
            [cutoffStr]
        );
    }

    response.success(res, { deleted: result?.changes || 0 }, '日志清理成功');
}));

module.exports = router;
