const express = require('express');
const { dbQuery, dbGet, dbRun } = require('../config/database');
const { authMiddleware } = require('../middleware/auth');
const { operationLogger } = require('../middleware/logger');
const response = require('../utils/response');
const { asyncHandler } = require('../middleware/error');

const router = express.Router();

// 获取习惯列表
router.get('/', authMiddleware, asyncHandler(async (req, res) => {
    const { status = 'active', page = 1, pageSize = 20 } = req.query;
    const offset = (page - 1) * pageSize;

    // 获取习惯列表
    const habits = await dbQuery(
        `SELECT h.*, 
                (SELECT COUNT(*) FROM checkins WHERE habit_id = h.id AND status = 'completed') as total_checkins,
                (SELECT MAX(checkin_date) FROM checkins WHERE habit_id = h.id AND status = 'completed') as last_checkin
         FROM habits h 
         WHERE h.user_id = ? AND h.status = ?
         ORDER BY h.created_at DESC 
         LIMIT ? OFFSET ?`,
        [req.user.id, status, parseInt(pageSize), parseInt(offset)]
    );

    // 获取总数
    const countResult = await dbGet(
        'SELECT COUNT(*) as total FROM habits WHERE user_id = ? AND status = ?',
        [req.user.id, status]
    );

    response.paginate(res, habits, {
        page: parseInt(page),
        pageSize: parseInt(pageSize),
        total: countResult.total
    });
}));

// 获取习惯详情
router.get('/:id', authMiddleware, asyncHandler(async (req, res) => {
    const { id } = req.params;

    const habit = await dbGet(
        `SELECT h.*, 
                (SELECT COUNT(*) FROM checkins WHERE habit_id = h.id AND status = 'completed') as total_checkins,
                (SELECT MAX(checkin_date) FROM checkins WHERE habit_id = h.id AND status = 'completed') as last_checkin
         FROM habits h 
         WHERE h.id = ? AND h.user_id = ?`,
        [id, req.user.id]
    );

    if (!habit) {
        return response.notFound(res, '习惯不存在');
    }

    // 获取最近7天的打卡记录
    const recentCheckins = await dbQuery(
        `SELECT checkin_date, status, points_earned 
         FROM checkins 
         WHERE habit_id = ? AND checkin_date >= date('now', '-7 days')
         ORDER BY checkin_date DESC`,
        [id]
    );

    response.success(res, { ...habit, recent_checkins: recentCheckins });
}));

// 创建习惯
router.post('/', authMiddleware, operationLogger('create_habit', 'habit'), asyncHandler(async (req, res) => {
    const { name, description, icon, color, habit_type, points, parent_approval, reminder_time } = req.body;

    // 验证必填字段
    if (!name) {
        return response.badRequest(res, '习惯名称为必填项');
    }

    const result = await dbRun(
        `INSERT INTO habits (user_id, name, description, icon, color, habit_type, points, parent_approval, reminder_time) 
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [req.user.id, name, description, icon || 'star', color || '#4A7BF7', 
         habit_type || 'daily_once', points || 1, parent_approval || 0, reminder_time]
    );

    const habit = await dbGet('SELECT * FROM habits WHERE id = ?', [result.id]);

    response.success(res, habit, '习惯创建成功', 201);
}));

// 更新习惯
router.put('/:id', authMiddleware, operationLogger('update_habit', 'habit'), asyncHandler(async (req, res) => {
    const { id } = req.params;
    const { name, description, icon, color, habit_type, points, parent_approval, reminder_time, status } = req.body;

    // 检查习惯是否存在
    const habit = await dbGet(
        'SELECT id FROM habits WHERE id = ? AND user_id = ?',
        [id, req.user.id]
    );

    if (!habit) {
        return response.notFound(res, '习惯不存在');
    }

    await dbRun(
        `UPDATE habits 
         SET name = ?, description = ?, icon = ?, color = ?, habit_type = ?, 
             points = ?, parent_approval = ?, reminder_time = ?, status = ?, updated_at = CURRENT_TIMESTAMP 
         WHERE id = ? AND user_id = ?`,
        [name, description, icon, color, habit_type, points, parent_approval, reminder_time, status, id, req.user.id]
    );

    const updatedHabit = await dbGet('SELECT * FROM habits WHERE id = ?', [id]);

    response.success(res, updatedHabit, '习惯更新成功');
}));

// 删除习惯
router.delete('/:id', authMiddleware, operationLogger('delete_habit', 'habit'), asyncHandler(async (req, res) => {
    const { id } = req.params;

    // 检查习惯是否存在
    const habit = await dbGet(
        'SELECT id FROM habits WHERE id = ? AND user_id = ?',
        [id, req.user.id]
    );

    if (!habit) {
        return response.notFound(res, '习惯不存在');
    }

    // 软删除：将状态改为deleted
    await dbRun(
        'UPDATE habits SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?',
        ['deleted', id, req.user.id]
    );

    response.success(res, null, '习惯删除成功');
}));

// 获取习惯统计
router.get('/:id/stats', authMiddleware, asyncHandler(async (req, res) => {
    const { id } = req.params;

    // 检查习惯是否存在
    const habit = await dbGet(
        'SELECT id FROM habits WHERE id = ? AND user_id = ?',
        [id, req.user.id]
    );

    if (!habit) {
        return response.notFound(res, '习惯不存在');
    }

    // 总打卡次数
    const totalCheckins = await dbGet(
        "SELECT COUNT(*) as count FROM checkins WHERE habit_id = ? AND status = 'completed'",
        [id]
    );

    // 本月打卡次数
    const monthCheckins = await dbGet(
        "SELECT COUNT(*) as count FROM checkins WHERE habit_id = ? AND status = 'completed' AND strftime('%Y-%m', checkin_date) = strftime('%Y-%m', 'now')",
        [id]
    );

    // 连续打卡天数
    const continuousDays = await calculateContinuousDays(id);

    // 最近30天打卡数据
    const last30Days = await dbQuery(
        `SELECT checkin_date, status 
         FROM checkins 
         WHERE habit_id = ? AND checkin_date >= date('now', '-30 days')
         ORDER BY checkin_date DESC`,
        [id]
    );

    response.success(res, {
        total_checkins: totalCheckins.count,
        month_checkins: monthCheckins.count,
        continuous_days: continuousDays,
        last_30_days: last30Days
    });
}));

// 计算连续打卡天数
async function calculateContinuousDays(habitId) {
    const checkins = await dbQuery(
        "SELECT checkin_date FROM checkins WHERE habit_id = ? AND status = 'completed' ORDER BY checkin_date DESC",
        [habitId]
    );

    if (checkins.length === 0) return 0;

    let continuousDays = 1;
    let lastDate = new Date(checkins[0].checkin_date);

    for (let i = 1; i < checkins.length; i++) {
        const currentDate = new Date(checkins[i].checkin_date);
        const diffDays = (lastDate - currentDate) / (1000 * 60 * 60 * 24);

        if (diffDays === 1) {
            continuousDays++;
            lastDate = currentDate;
        } else {
            break;
        }
    }

    // 检查今天是否打卡
    const today = new Date().toISOString().split('T')[0];
    if (checkins[0].checkin_date !== today) {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = yesterday.toISOString().split('T')[0];
        
        if (checkins[0].checkin_date !== yesterdayStr) {
            continuousDays = 0;
        }
    }

    return continuousDays;
}

module.exports = router;
