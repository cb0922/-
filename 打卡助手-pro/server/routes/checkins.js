const express = require('express');
const { dbQuery, dbGet, dbRun } = require('../config/database');
const { authMiddleware } = require('../middleware/auth');
const { operationLogger } = require('../middleware/logger');
const response = require('../utils/response');
const { asyncHandler } = require('../middleware/error');

const router = express.Router();

// 获取打卡记录列表
router.get('/', authMiddleware, asyncHandler(async (req, res) => {
    const { habit_id, start_date, end_date, page = 1, pageSize = 20 } = req.query;
    const offset = (page - 1) * pageSize;

    let whereClause = 'WHERE c.user_id = ?';
    const params = [req.user.id];

    if (habit_id) {
        whereClause += ' AND c.habit_id = ?';
        params.push(habit_id);
    }

    if (start_date) {
        whereClause += ' AND c.checkin_date >= ?';
        params.push(start_date);
    }

    if (end_date) {
        whereClause += ' AND c.checkin_date <= ?';
        params.push(end_date);
    }

    // 获取打卡记录
    const checkins = await dbQuery(
        `SELECT c.*, h.name as habit_name, h.icon as habit_icon, h.color as habit_color
         FROM checkins c
         JOIN habits h ON c.habit_id = h.id
         ${whereClause}
         ORDER BY c.checkin_date DESC, c.checkin_time DESC
         LIMIT ? OFFSET ?`,
        [...params, parseInt(pageSize), parseInt(offset)]
    );

    // 获取总数
    const countResult = await dbGet(
        `SELECT COUNT(*) as total FROM checkins c ${whereClause}`,
        params
    );

    response.paginate(res, checkins, {
        page: parseInt(page),
        pageSize: parseInt(pageSize),
        total: countResult.total
    });
}));

// 打卡
router.post('/', authMiddleware, operationLogger('checkin', 'checkin'), asyncHandler(async (req, res) => {
    const { habit_id, checkin_date, note } = req.body;
    const ip = req.ip || req.connection.remoteAddress;
    const userAgent = req.headers['user-agent'];

    // 验证必填字段
    if (!habit_id) {
        return response.badRequest(res, '习惯ID为必填项');
    }

    // 检查习惯是否存在且属于当前用户
    const habit = await dbGet(
        'SELECT id, name, points, parent_approval FROM habits WHERE id = ? AND user_id = ? AND status = ?',
        [habit_id, req.user.id, 'active']
    );

    if (!habit) {
        return response.notFound(res, '习惯不存在或已被删除');
    }

    const date = checkin_date || new Date().toISOString().split('T')[0];
    const time = new Date().toTimeString().split(' ')[0];

    // 检查是否已打卡
    const existingCheckin = await dbGet(
        'SELECT id FROM checkins WHERE habit_id = ? AND checkin_date = ?',
        [habit_id, date]
    );

    if (existingCheckin) {
        return response.badRequest(res, '今天已经打过卡了');
    }

    // 确定打卡状态
    const status = habit.parent_approval ? 'pending' : 'completed';
    const pointsEarned = habit.parent_approval ? 0 : habit.points;

    // 创建打卡记录
    const result = await dbRun(
        `INSERT INTO checkins (habit_id, user_id, checkin_date, checkin_time, status, points_earned, note, ip_address, user_agent) 
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [habit_id, req.user.id, date, time, status, pointsEarned, note, ip, userAgent]
    );

    // 更新用户积分和打卡统计
    if (pointsEarned > 0) {
        await dbRun(
            `UPDATE users SET total_points = total_points + ?, total_checkins = total_checkins + 1 WHERE id = ?`,
            [pointsEarned, req.user.id]
        );

        // 记录积分变动
        await dbRun(
            `INSERT INTO user_points (user_id, points, type, source, source_id, description) 
             VALUES (?, ?, 'earn', 'checkin', ?, ?)`,
            [req.user.id, pointsEarned, result.id, `打卡：${habit.name}`]
        );
    }

    // 更新连续打卡天数
    await updateContinuousDays(req.user.id);

    const checkin = await dbGet('SELECT * FROM checkins WHERE id = ?', [result.id]);

    response.success(res, {
        ...checkin,
        habit_name: habit.name,
        message: habit.parent_approval ? '打卡成功，等待家长审核' : '打卡成功'
    }, '打卡成功', 201);
}));

// 补打卡（允许补最近7天）
router.post('/makeup', authMiddleware, operationLogger('makeup_checkin', 'checkin'), asyncHandler(async (req, res) => {
    const { habit_id, checkin_date, note } = req.body;

    if (!habit_id || !checkin_date) {
        return response.badRequest(res, '习惯ID和打卡日期为必填项');
    }

    // 检查日期是否在允许范围内（最近7天）
    const date = new Date(checkin_date);
    const today = new Date();
    const diffDays = (today - date) / (1000 * 60 * 60 * 24);

    if (diffDays > 7 || diffDays < 0) {
        return response.badRequest(res, '只能补最近7天的打卡');
    }

    // 检查习惯
    const habit = await dbGet(
        'SELECT id, name, points FROM habits WHERE id = ? AND user_id = ? AND status = ?',
        [habit_id, req.user.id, 'active']
    );

    if (!habit) {
        return response.notFound(res, '习惯不存在');
    }

    // 检查是否已打卡
    const existingCheckin = await dbGet(
        'SELECT id FROM checkins WHERE habit_id = ? AND checkin_date = ?',
        [habit_id, checkin_date]
    );

    if (existingCheckin) {
        return response.badRequest(res, '该日期已经打过卡了');
    }

    const result = await dbRun(
        `INSERT INTO checkins (habit_id, user_id, checkin_date, checkin_time, status, points_earned, note) 
         VALUES (?, ?, ?, ?, 'completed', ?, ?)`,
        [habit_id, req.user.id, checkin_date, '12:00:00', habit.points, note]
    );

    // 更新用户积分
    await dbRun(
        `UPDATE users SET total_points = total_points + ?, total_checkins = total_checkins + 1 WHERE id = ?`,
        [habit.points, req.user.id]
    );

    // 记录积分变动
    await dbRun(
        `INSERT INTO user_points (user_id, points, type, source, source_id, description) 
         VALUES (?, ?, 'earn', 'makeup', ?, ?)`,
        [req.user.id, habit.points, result.id, `补打卡：${habit.name}`]
    );

    const checkin = await dbGet('SELECT * FROM checkins WHERE id = ?', [result.id]);

    response.success(res, checkin, '补打卡成功', 201);
}));

// 取消打卡
router.delete('/:id', authMiddleware, operationLogger('cancel_checkin', 'checkin'), asyncHandler(async (req, res) => {
    const { id } = req.params;

    const checkin = await dbGet(
        'SELECT * FROM checkins WHERE id = ? AND user_id = ?',
        [id, req.user.id]
    );

    if (!checkin) {
        return response.notFound(res, '打卡记录不存在');
    }

    // 如果已赚取积分，需要扣除
    if (checkin.points_earned > 0) {
        await dbRun(
            'UPDATE users SET total_points = total_points - ? WHERE id = ?',
            [checkin.points_earned, req.user.id]
        );

        // 记录积分扣除
        await dbRun(
            `INSERT INTO user_points (user_id, points, type, source, source_id, description) 
             VALUES (?, ?, 'spend', 'cancel_checkin', ?, ?)`,
            [req.user.id, -checkin.points_earned, id, '取消打卡']
        );
    }

    await dbRun('DELETE FROM checkins WHERE id = ?', [id]);

    response.success(res, null, '打卡已取消');
}));

// 获取打卡统计
router.get('/stats/overview', authMiddleware, asyncHandler(async (req, res) => {
    const userId = req.user.id;

    // 今日打卡数
    const todayCheckins = await dbGet(
        `SELECT COUNT(*) as count FROM checkins 
         WHERE user_id = ? AND checkin_date = date('now')`,
        [userId]
    );

    // 本周打卡数
    const weekCheckins = await dbGet(
        `SELECT COUNT(*) as count FROM checkins 
         WHERE user_id = ? AND checkin_date >= date('now', 'weekday 0', '-7 days')`,
        [userId]
    );

    // 本月打卡数
    const monthCheckins = await dbGet(
        `SELECT COUNT(*) as count FROM checkins 
         WHERE user_id = ? AND strftime('%Y-%m', checkin_date) = strftime('%Y-%m', 'now')`,
        [userId]
    );

    // 总打卡数
    const totalCheckins = await dbGet(
        `SELECT COUNT(*) as count FROM checkins WHERE user_id = ?`,
        [userId]
    );

    // 连续打卡天数
    const continuousDays = await calculateUserContinuousDays(userId);

    // 习惯打卡分布
    const habitDistribution = await dbQuery(
        `SELECT h.name, COUNT(c.id) as count 
         FROM habits h 
         LEFT JOIN checkins c ON h.id = c.habit_id AND c.status = 'completed'
         WHERE h.user_id = ? AND h.status = 'active'
         GROUP BY h.id
         ORDER BY count DESC`,
        [userId]
    );

    // 最近7天打卡趋势
    const weeklyTrend = await dbQuery(
        `SELECT checkin_date, COUNT(*) as count 
         FROM checkins 
         WHERE user_id = ? AND checkin_date >= date('now', '-7 days')
         GROUP BY checkin_date
         ORDER BY checkin_date`,
        [userId]
    );

    response.success(res, {
        today: todayCheckins.count,
        this_week: weekCheckins.count,
        this_month: monthCheckins.count,
        total: totalCheckins.count,
        continuous_days: continuousDays,
        habit_distribution: habitDistribution,
        weekly_trend: weeklyTrend
    });
}));

// 获取日历数据
router.get('/calendar', authMiddleware, asyncHandler(async (req, res) => {
    const { year, month } = req.query;
    const userId = req.user.id;

    let dateFilter = '';
    const params = [userId];

    if (year && month) {
        dateFilter = "AND strftime('%Y-%m', c.checkin_date) = ?";
        params.push(`${year}-${month.padStart(2, '0')}`);
    }

    const calendarData = await dbQuery(
        `SELECT c.checkin_date, COUNT(*) as count, 
                GROUP_CONCAT(h.name) as habits,
                SUM(c.points_earned) as points
         FROM checkins c
         JOIN habits h ON c.habit_id = h.id
         WHERE c.user_id = ? ${dateFilter}
         GROUP BY c.checkin_date
         ORDER BY c.checkin_date`,
        params
    );

    response.success(res, calendarData);
}));

// 更新用户连续打卡天数
async function updateContinuousDays(userId) {
    const continuousDays = await calculateUserContinuousDays(userId);
    await dbRun(
        'UPDATE users SET continuous_days = ? WHERE id = ?',
        [continuousDays, userId]
    );
}

// 计算用户连续打卡天数
async function calculateUserContinuousDays(userId) {
    const checkins = await dbQuery(
        `SELECT DISTINCT checkin_date 
         FROM checkins 
         WHERE user_id = ? AND status = 'completed'
         ORDER BY checkin_date DESC`,
        [userId]
    );

    if (checkins.length === 0) return 0;

    const today = new Date().toISOString().split('T')[0];
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toISOString().split('T')[0];

    // 检查今天或昨天是否打卡
    const latestDate = checkins[0].checkin_date;
    if (latestDate !== today && latestDate !== yesterdayStr) {
        return 0;
    }

    let continuousDays = 1;
    let lastDate = new Date(latestDate);

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

    return continuousDays;
}

module.exports = router;
