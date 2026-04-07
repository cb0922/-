const express = require('express');
const { dbQuery, dbGet } = require('../config/database');
const { authMiddleware } = require('../middleware/auth');
const response = require('../utils/response');
const { asyncHandler } = require('../middleware/error');

const router = express.Router();

// 仪表盘数据
router.get('/dashboard', authMiddleware, asyncHandler(async (req, res) => {
    const userId = req.user.id;

    // 获取用户基本信息
    const user = await dbGet(
        `SELECT total_points, continuous_days, total_checkins 
         FROM users WHERE id = ?`,
        [userId]
    );

    // 今日统计
    const todayStats = await dbGet(
        `SELECT 
            COUNT(DISTINCT habit_id) as habits_count,
            SUM(points_earned) as points
         FROM checkins 
         WHERE user_id = ? AND checkin_date = date('now')`,
        [userId]
    );

    // 活跃习惯数
    const activeHabits = await dbGet(
        `SELECT COUNT(*) as count FROM habits WHERE user_id = ? AND status = 'active'`,
        [userId]
    );

    // 本周统计
    const weekStats = await dbGet(
        `SELECT 
            COUNT(*) as checkins,
            SUM(points_earned) as points
         FROM checkins 
         WHERE user_id = ? AND checkin_date >= date('now', '-7 days')`,
        [userId]
    );

    // 最近7天趋势
    const weeklyTrend = await dbQuery(
        `SELECT 
            checkin_date,
            COUNT(*) as checkins,
            SUM(points_earned) as points
         FROM checkins 
         WHERE user_id = ? AND checkin_date >= date('now', '-7 days')
         GROUP BY checkin_date
         ORDER BY checkin_date`,
        [userId]
    );

    // 习惯完成率
    const habitCompletion = await dbQuery(
        `SELECT 
            h.id,
            h.name,
            h.color,
            COUNT(c.id) as completed_days,
            (SELECT COUNT(*) FROM checkins WHERE habit_id = h.id) as total_checkins
         FROM habits h
         LEFT JOIN checkins c ON h.id = c.habit_id 
            AND c.checkin_date >= date('now', '-30 days')
            AND c.status = 'completed'
         WHERE h.user_id = ? AND h.status = 'active'
         GROUP BY h.id
         ORDER BY completed_days DESC`,
        [userId]
    );

    response.success(res, {
        user: {
            total_points: user.total_points,
            continuous_days: user.continuous_days,
            total_checkins: user.total_checkins
        },
        today: {
            habits_completed: todayStats.habits_count || 0,
            points_earned: todayStats.points || 0
        },
        active_habits: activeHabits.count,
        this_week: {
            checkins: weekStats.checkins || 0,
            points: weekStats.points || 0
        },
        weekly_trend: weeklyTrend,
        habit_completion: habitCompletion
    });
}));

// 习惯分析
router.get('/habits', authMiddleware, asyncHandler(async (req, res) => {
    const userId = req.user.id;
    const { period = '30' } = req.query;

    // 习惯统计
    const habitStats = await dbQuery(
        `SELECT 
            h.id,
            h.name,
            h.icon,
            h.color,
            h.habit_type,
            h.created_at,
            COUNT(c.id) as total_checkins,
            COUNT(CASE WHEN c.checkin_date >= date('now', '-30 days') THEN 1 END) as month_checkins,
            MAX(c.checkin_date) as last_checkin
         FROM habits h
         LEFT JOIN checkins c ON h.id = c.habit_id AND c.status = 'completed'
         WHERE h.user_id = ? AND h.status = 'active'
         GROUP BY h.id
         ORDER BY total_checkins DESC`,
        [userId]
    );

    // 计算每个习惯的连续打卡天数
    for (const habit of habitStats) {
        habit.continuous_days = await calculateHabitContinuousDays(habit.id);
    }

    response.success(res, habitStats);
}));

// 趋势分析
router.get('/trends', authMiddleware, asyncHandler(async (req, res) => {
    const userId = req.user.id;
    const { type = 'daily', range = '30' } = req.query;

    let sql;
    let groupBy;

    if (type === 'daily') {
        // 日趋势
        sql = `
            SELECT 
                checkin_date as date,
                COUNT(*) as checkins,
                SUM(points_earned) as points,
                COUNT(DISTINCT habit_id) as habits
            FROM checkins 
            WHERE user_id = ? AND checkin_date >= date('now', '-${range} days')
            GROUP BY checkin_date
            ORDER BY checkin_date
        `;
    } else if (type === 'weekly') {
        // 周趋势
        sql = `
            SELECT 
                strftime('%Y-W%W', checkin_date) as date,
                COUNT(*) as checkins,
                SUM(points_earned) as points
            FROM checkins 
            WHERE user_id = ? AND checkin_date >= date('now', '-${range * 7} days')
            GROUP BY strftime('%Y-W%W', checkin_date)
            ORDER BY date
        `;
    } else if (type === 'monthly') {
        // 月趋势
        sql = `
            SELECT 
                strftime('%Y-%m', checkin_date) as date,
                COUNT(*) as checkins,
                SUM(points_earned) as points
            FROM checkins 
            WHERE user_id = ? AND checkin_date >= date('now', '-${range} months')
            GROUP BY strftime('%Y-%m', checkin_date)
            ORDER BY date
        `;
    }

    const trends = await dbQuery(sql, [userId]);

    // 计算完成率趋势
    const completionRate = await dbQuery(
        `SELECT 
            checkin_date,
            COUNT(DISTINCT habit_id) as completed_habits,
            (SELECT COUNT(*) FROM habits WHERE user_id = ? AND status = 'active') as total_habits
         FROM checkins 
         WHERE user_id = ? AND checkin_date >= date('now', '-30 days')
         GROUP BY checkin_date
         ORDER BY checkin_date`,
        [userId, userId]
    );

    response.success(res, {
        trends,
        completion_rate: completionRate
    });
}));

// 积分统计
router.get('/points', authMiddleware, asyncHandler(async (req, res) => {
    const userId = req.user.id;
    const { start_date, end_date } = req.query;

    let dateFilter = '';
    const params = [userId];

    if (start_date) {
        dateFilter += ' AND created_at >= ?';
        params.push(start_date);
    }
    if (end_date) {
        dateFilter += ' AND created_at <= ?';
        params.push(end_date);
    }

    // 积分汇总
    const summary = await dbGet(
        `SELECT 
            SUM(CASE WHEN type = 'earn' THEN points ELSE 0 END) as total_earned,
            SUM(CASE WHEN type = 'spend' THEN ABS(points) ELSE 0 END) as total_spent,
            SUM(points) as current_balance
         FROM user_points WHERE user_id = ?`,
        [userId]
    );

    // 积分趋势
    const pointsTrend = await dbQuery(
        `SELECT 
            date(created_at) as date,
            SUM(CASE WHEN type = 'earn' THEN points ELSE 0 END) as earned,
            SUM(CASE WHEN type = 'spend' THEN points ELSE 0 END) as spent
         FROM user_points 
         WHERE user_id = ? ${dateFilter}
         GROUP BY date(created_at)
         ORDER BY date`,
        params
    );

    // 积分来源分布
    const sourceDistribution = await dbQuery(
        `SELECT 
            source,
            SUM(points) as total_points,
            COUNT(*) as count
         FROM user_points 
         WHERE user_id = ? AND type = 'earn' ${dateFilter}
         GROUP BY source
         ORDER BY total_points DESC`,
        params
    );

    // 最近积分记录
    const recentRecords = await dbQuery(
        `SELECT 
            p.*,
            h.name as habit_name
         FROM user_points p
         LEFT JOIN habits h ON p.source_id = h.id
         WHERE p.user_id = ?
         ORDER BY p.created_at DESC
         LIMIT 20`,
        [userId]
    );

    response.success(res, {
        summary,
        trend: pointsTrend,
        source_distribution: sourceDistribution,
        recent_records: recentRecords
    }));
}));

// 计算习惯连续打卡天数
async function calculateHabitContinuousDays(habitId) {
    const checkins = await dbQuery(
        `SELECT checkin_date FROM checkins 
         WHERE habit_id = ? AND status = 'completed'
         ORDER BY checkin_date DESC`,
        [habitId]
    );

    if (checkins.length === 0) return 0;

    const today = new Date().toISOString().split('T')[0];
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toISOString().split('T')[0];

    let continuousDays = 1;
    let lastDate = new Date(checkins[0].checkin_date);

    // 如果最新记录不是今天或昨天，连续天数为0
    if (checkins[0].checkin_date !== today && checkins[0].checkin_date !== yesterdayStr) {
        return 0;
    }

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
