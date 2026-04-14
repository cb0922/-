const express = require('express');
const { dbQuery, dbGet, dbRun } = require('../config/database');
const { authMiddleware } = require('../middleware/auth');
const { operationLogger } = require('../middleware/logger');
const response = require('../utils/response');
const { asyncHandler } = require('../middleware/error');

const router = express.Router();

// ============================================
// 积分概览
// ============================================
router.get('/overview', authMiddleware, asyncHandler(async (req, res) => {
    const userId = req.user.id;

    // 当前余额
    const user = await dbGet('SELECT total_points FROM users WHERE id = ?', [userId]);
    const balance = user ? user.total_points : 0;

    // 本周获得（周一到周日）
    const weekEarned = await dbGet(
        `SELECT COALESCE(SUM(points), 0) as total FROM user_points 
         WHERE user_id = ? AND type = 'earn' 
         AND created_at >= date('now', 'weekday 0', '-7 days')`,
        [userId]
    );

    // 本月获得
    const monthEarned = await dbGet(
        `SELECT COALESCE(SUM(points), 0) as total FROM user_points 
         WHERE user_id = ? AND type = 'earn' 
         AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')`,
        [userId]
    );

    // 累计获得
    const totalEarned = await dbGet(
        `SELECT COALESCE(SUM(points), 0) as total FROM user_points 
         WHERE user_id = ? AND type = 'earn'`,
        [userId]
    );

    // 累计消耗
    const totalSpent = await dbGet(
        `SELECT COALESCE(SUM(ABS(points)), 0) as total FROM user_points 
         WHERE user_id = ? AND type = 'spend'`,
        [userId]
    );

    response.success(res, {
        balance,
        week_earned: weekEarned.total || 0,
        month_earned: monthEarned.total || 0,
        total_earned: totalEarned.total || 0,
        total_spent: totalSpent.total || 0
    });
}));

// ============================================
// 积分历史
// ============================================
router.get('/history', authMiddleware, asyncHandler(async (req, res) => {
    const userId = req.user.id;
    const { page = 1, pageSize = 20 } = req.query;
    const offset = (page - 1) * pageSize;

    const list = await dbQuery(
        `SELECT * FROM user_points 
         WHERE user_id = ? 
         ORDER BY created_at DESC 
         LIMIT ? OFFSET ?`,
        [userId, parseInt(pageSize), parseInt(offset)]
    );

    const countResult = await dbGet(
        `SELECT COUNT(*) as total FROM user_points WHERE user_id = ?`,
        [userId]
    );

    response.paginate(res, list, {
        page: parseInt(page),
        pageSize: parseInt(pageSize),
        total: countResult.total
    });
}));

// ============================================
// 愿望清单
// ============================================

// 获取愿望列表
router.get('/wishes', authMiddleware, asyncHandler(async (req, res) => {
    const userId = req.user.id;
    const { status } = req.query;

    let whereClause = 'WHERE user_id = ?';
    const params = [userId];

    if (status) {
        whereClause += ' AND status = ?';
        params.push(status);
    }

    const wishes = await dbQuery(
        `SELECT * FROM wishes ${whereClause} ORDER BY created_at DESC`,
        params
    );

    response.success(res, wishes);
}));

// 添加愿望
router.post('/wishes', authMiddleware, operationLogger('create_wish', 'wish'), asyncHandler(async (req, res) => {
    const userId = req.user.id;
    const { title, description, cost } = req.body;

    if (!title) {
        return response.badRequest(res, '愿望标题不能为空');
    }

    const result = await dbRun(
        `INSERT INTO wishes (user_id, title, description, cost) VALUES (?, ?, ?, ?)`,
        [userId, title, description || '', cost || 1]
    );

    const wish = await dbGet('SELECT * FROM wishes WHERE id = ?', [result.id]);
    response.success(res, wish, '愿望添加成功', 201);
}));

// 更新愿望
router.put('/wishes/:id', authMiddleware, operationLogger('update_wish', 'wish'), asyncHandler(async (req, res) => {
    const userId = req.user.id;
    const { id } = req.params;
    const { title, description, cost } = req.body;

    const wish = await dbGet('SELECT * FROM wishes WHERE id = ? AND user_id = ?', [id, userId]);
    if (!wish) {
        return response.notFound(res, '愿望不存在');
    }

    if (wish.status === 'redeemed') {
        return response.badRequest(res, '已兑换的愿望不能修改');
    }

    await dbRun(
        `UPDATE wishes SET title = ?, description = ?, cost = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?`,
        [title || wish.title, description !== undefined ? description : wish.description, cost !== undefined ? cost : wish.cost, id]
    );

    const updated = await dbGet('SELECT * FROM wishes WHERE id = ?', [id]);
    response.success(res, updated, '愿望更新成功');
}));

// 删除愿望
router.delete('/wishes/:id', authMiddleware, operationLogger('delete_wish', 'wish'), asyncHandler(async (req, res) => {
    const userId = req.user.id;
    const { id } = req.params;

    const wish = await dbGet('SELECT * FROM wishes WHERE id = ? AND user_id = ?', [id, userId]);
    if (!wish) {
        return response.notFound(res, '愿望不存在');
    }

    await dbRun('DELETE FROM wishes WHERE id = ?', [id]);
    response.success(res, null, '愿望删除成功');
}));

// 兑换愿望
router.post('/wishes/:id/redeem', authMiddleware, operationLogger('redeem_wish', 'wish'), asyncHandler(async (req, res) => {
    const userId = req.user.id;
    const { id } = req.params;

    const wish = await dbGet('SELECT * FROM wishes WHERE id = ? AND user_id = ?', [id, userId]);
    if (!wish) {
        return response.notFound(res, '愿望不存在');
    }

    if (wish.status === 'redeemed') {
        return response.badRequest(res, '该愿望已经兑换过了');
    }

    const user = await dbGet('SELECT total_points FROM users WHERE id = ?', [userId]);
    if (!user || user.total_points < wish.cost) {
        return response.badRequest(res, '星星余额不足，快去打卡赚积分吧！');
    }

    // 扣除积分
    await dbRun(
        'UPDATE users SET total_points = total_points - ? WHERE id = ?',
        [wish.cost, userId]
    );

    // 记录积分变动
    await dbRun(
        `INSERT INTO user_points (user_id, points, type, source, source_id, description) VALUES (?, ?, 'spend', 'wish', ?, ?)`,
        [userId, -wish.cost, wish.id, `兑换愿望：${wish.title}`]
    );

    // 更新愿望状态
    await dbRun(
        `UPDATE wishes SET status = 'redeemed', redeemed_at = CURRENT_TIMESTAMP WHERE id = ?`,
        [id]
    );

    // 检查成就
    await checkAndUnlockAchievement(userId, 'wish_redeemed');

    const updated = await dbGet('SELECT * FROM wishes WHERE id = ?', [id]);
    response.success(res, updated, `兑换成功！消耗 ${wish.cost}⭐`);
}));

// ============================================
// 成就系统
// ============================================

// 获取成就列表（含用户解锁状态）
router.get('/achievements', authMiddleware, asyncHandler(async (req, res) => {
    const userId = req.user.id;

    const achievements = await dbQuery(
        `SELECT a.*, 
                CASE WHEN ua.id IS NOT NULL THEN 1 ELSE 0 END as unlocked,
                ua.claimed,
                ua.unlocked_at
         FROM achievements a
         LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = ?
         ORDER BY a.id ASC`,
        [userId]
    );

    response.success(res, achievements);
}));

// 领取成就奖励
router.post('/achievements/:id/claim', authMiddleware, operationLogger('claim_achievement', 'achievement'), asyncHandler(async (req, res) => {
    const userId = req.user.id;
    const { id } = req.params;

    const ua = await dbGet(
        `SELECT ua.*, a.reward_points, a.name FROM user_achievements ua
         JOIN achievements a ON ua.achievement_id = a.id
         WHERE ua.id = ? AND ua.user_id = ?`,
        [id, userId]
    );

    if (!ua) {
        return response.notFound(res, '成就未解锁');
    }

    if (ua.claimed) {
        return response.badRequest(res, '奖励已经领取过了');
    }

    // 发放奖励
    await dbRun(
        'UPDATE users SET total_points = total_points + ? WHERE id = ?',
        [ua.reward_points, userId]
    );

    // 记录积分变动
    await dbRun(
        `INSERT INTO user_points (user_id, points, type, source, source_id, description) VALUES (?, ?, 'earn', 'achievement', ?, ?)`,
        [userId, ua.reward_points, ua.achievement_id, `解锁成就：${ua.name}`]
    );

    // 标记已领取
    await dbRun(
        `UPDATE user_achievements SET claimed = 1 WHERE id = ?`,
        [ua.id]
    );

    response.success(res, { claimed: true, reward_points: ua.reward_points }, `领取成功！+${ua.reward_points}⭐`);
}));

// ============================================
// 宠物系统
// ============================================

// 获取宠物
router.get('/pet', authMiddleware, asyncHandler(async (req, res) => {
    const userId = req.user.id;
    const pet = await dbGet('SELECT * FROM pets WHERE user_id = ?', [userId]);
    response.success(res, pet || null);
}));

// 领养宠物
router.post('/pet/adopt', authMiddleware, operationLogger('adopt_pet', 'pet'), asyncHandler(async (req, res) => {
    const userId = req.user.id;
    const { name, type } = req.body;

    if (!name) {
        return response.badRequest(res, '请给宠物取个名字');
    }

    const existingPet = await dbGet('SELECT id FROM pets WHERE user_id = ?', [userId]);
    if (existingPet) {
        return response.badRequest(res, '你已经有一只宠物了');
    }

    const validTypes = ['cat', 'dog', 'rabbit', 'bird'];
    const petType = validTypes.includes(type) ? type : 'cat';

    const result = await dbRun(
        `INSERT INTO pets (user_id, name, type, level, exp, max_exp, hunger, happiness, energy, cleanliness) 
         VALUES (?, ?, ?, 1, 0, 100, 80, 80, 80, 80)`,
        [userId, name, petType]
    );

    // 检查成就
    await checkAndUnlockAchievement(userId, 'pet_adopted');

    const pet = await dbGet('SELECT * FROM pets WHERE id = ?', [result.id]);
    response.success(res, pet, '领养成功！', 201);
}));

// 喂食
router.post('/pet/feed', authMiddleware, operationLogger('feed_pet', 'pet'), asyncHandler(async (req, res) => {
    const userId = req.user.id;
    const feedCost = 1;

    const pet = await dbGet('SELECT * FROM pets WHERE user_id = ?', [userId]);
    if (!pet) {
        return response.notFound(res, '还没有领养宠物');
    }

    const user = await dbGet('SELECT total_points FROM users WHERE id = ?', [userId]);
    if (!user || user.total_points < feedCost) {
        return response.badRequest(res, '星星余额不足，快去打卡赚积分吧！');
    }

    if (pet.hunger >= 100) {
        return response.badRequest(res, '宠物已经很饱了');
    }

    // 扣除积分
    await dbRun(
        'UPDATE users SET total_points = total_points - ? WHERE id = ?',
        [feedCost, userId]
    );

    // 记录积分变动
    await dbRun(
        `INSERT INTO user_points (user_id, points, type, source, source_id, description) VALUES (?, ?, 'spend', 'pet_feed', ?, '喂食宠物')`,
        [userId, -feedCost, pet.id]
    );

    // 更新宠物状态
    const newHunger = Math.min(100, pet.hunger + 20);
    const newExp = pet.exp + 10;
    const levelUpResult = calculateLevelUp(pet.level, newExp, pet.max_exp);

    await dbRun(
        `UPDATE pets SET hunger = ?, exp = ?, max_exp = ?, level = ?, last_interact_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?`,
        [newHunger, levelUpResult.exp, levelUpResult.maxExp, levelUpResult.level, pet.id]
    );

    // 发放升级奖励
    if (levelUpResult.level > pet.level) {
        const bonus = 50 * (levelUpResult.level - pet.level);
        await dbRun(
            'UPDATE users SET total_points = total_points + ? WHERE id = ?',
            [bonus, userId]
        );
        await dbRun(
            `INSERT INTO user_points (user_id, points, type, source, source_id, description) VALUES (?, ?, 'earn', 'pet_levelup', ?, ?)`,
            [userId, bonus, pet.id, `宠物升级到 Lv.${levelUpResult.level}`]
        );
    }

    const updatedPet = await dbGet('SELECT * FROM pets WHERE id = ?', [pet.id]);
    response.success(res, {
        pet: updatedPet,
        level_up: levelUpResult.level > pet.level,
        new_level: levelUpResult.level > pet.level ? levelUpResult.level : null,
        bonus: levelUpResult.level > pet.level ? 50 * (levelUpResult.level - pet.level) : 0
    }, '喂食成功！饱食度+20，经验+10');
}));

// 玩耍
router.post('/pet/play', authMiddleware, operationLogger('play_pet', 'pet'), asyncHandler(async (req, res) => {
    const userId = req.user.id;

    const pet = await dbGet('SELECT * FROM pets WHERE user_id = ?', [userId]);
    if (!pet) {
        return response.notFound(res, '还没有领养宠物');
    }

    if (pet.energy < 20) {
        return response.badRequest(res, '宠物精力不足，需要休息或睡觉');
    }

    if (pet.is_sleeping) {
        return response.badRequest(res, '宠物正在睡觉，请稍后再玩');
    }

    const newHappiness = Math.min(100, pet.happiness + 15);
    const newEnergy = Math.max(0, pet.energy - 20);
    const newExp = pet.exp + 15;
    const levelUpResult = calculateLevelUp(pet.level, newExp, pet.max_exp);

    await dbRun(
        `UPDATE pets SET happiness = ?, energy = ?, exp = ?, max_exp = ?, level = ?, last_interact_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?`,
        [newHappiness, newEnergy, levelUpResult.exp, levelUpResult.maxExp, levelUpResult.level, pet.id]
    );

    if (levelUpResult.level > pet.level) {
        const bonus = 50 * (levelUpResult.level - pet.level);
        await dbRun('UPDATE users SET total_points = total_points + ? WHERE id = ?', [bonus, userId]);
        await dbRun(
            `INSERT INTO user_points (user_id, points, type, source, source_id, description) VALUES (?, ?, 'earn', 'pet_levelup', ?, ?)`,
            [userId, bonus, pet.id, `宠物升级到 Lv.${levelUpResult.level}`]
        );
    }

    const updatedPet = await dbGet('SELECT * FROM pets WHERE id = ?', [pet.id]);
    response.success(res, {
        pet: updatedPet,
        level_up: levelUpResult.level > pet.level,
        new_level: levelUpResult.level > pet.level ? levelUpResult.level : null,
        bonus: levelUpResult.level > pet.level ? 50 * (levelUpResult.level - pet.level) : 0
    }, '玩耍成功！心情+15，经验+15');
}));

// 清洁
router.post('/pet/clean', authMiddleware, operationLogger('clean_pet', 'pet'), asyncHandler(async (req, res) => {
    const userId = req.user.id;

    const pet = await dbGet('SELECT * FROM pets WHERE user_id = ?', [userId]);
    if (!pet) {
        return response.notFound(res, '还没有领养宠物');
    }

    const newCleanliness = Math.min(100, pet.cleanliness + 30);
    const newExp = pet.exp + 5;
    const levelUpResult = calculateLevelUp(pet.level, newExp, pet.max_exp);

    await dbRun(
        `UPDATE pets SET cleanliness = ?, exp = ?, max_exp = ?, level = ?, last_interact_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?`,
        [newCleanliness, levelUpResult.exp, levelUpResult.maxExp, levelUpResult.level, pet.id]
    );

    if (levelUpResult.level > pet.level) {
        const bonus = 50 * (levelUpResult.level - pet.level);
        await dbRun('UPDATE users SET total_points = total_points + ? WHERE id = ?', [bonus, userId]);
        await dbRun(
            `INSERT INTO user_points (user_id, points, type, source, source_id, description) VALUES (?, ?, 'earn', 'pet_levelup', ?, ?)`,
            [userId, bonus, pet.id, `宠物升级到 Lv.${levelUpResult.level}`]
        );
    }

    const updatedPet = await dbGet('SELECT * FROM pets WHERE id = ?', [pet.id]);
    response.success(res, {
        pet: updatedPet,
        level_up: levelUpResult.level > pet.level,
        new_level: levelUpResult.level > pet.level ? levelUpResult.level : null,
        bonus: levelUpResult.level > pet.level ? 50 * (levelUpResult.level - pet.level) : 0
    }, '清洁成功！清洁度+30，经验+5');
}));

// 切换睡觉状态
router.post('/pet/sleep', authMiddleware, operationLogger('sleep_pet', 'pet'), asyncHandler(async (req, res) => {
    const userId = req.user.id;

    const pet = await dbGet('SELECT * FROM pets WHERE user_id = ?', [userId]);
    if (!pet) {
        return response.notFound(res, '还没有领养宠物');
    }

    const newSleeping = pet.is_sleeping ? 0 : 1;
    const newEnergy = newSleeping ? pet.energy : Math.min(100, pet.energy + 10);

    await dbRun(
        `UPDATE pets SET is_sleeping = ?, energy = ?, last_interact_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?`,
        [newSleeping, newEnergy, pet.id]
    );

    const updatedPet = await dbGet('SELECT * FROM pets WHERE id = ?', [pet.id]);
    response.success(res, updatedPet, newSleeping ? '宠物开始睡觉了 💤' : '宠物醒来了！☀️');
}));

// ============================================
// 成就检测辅助函数（供其他模块调用）
// ============================================
async function checkAndUnlockAchievement(userId, conditionType) {
    const achievements = await dbQuery(
        'SELECT * FROM achievements WHERE condition_type = ?',
        [conditionType]
    );

    for (const ach of achievements) {
        // 检查是否已解锁
        const existing = await dbGet(
            'SELECT id FROM user_achievements WHERE user_id = ? AND achievement_id = ?',
            [userId, ach.id]
        );

        if (existing) continue;

        let shouldUnlock = false;

        if (ach.condition_type === 'checkin_count') {
            const result = await dbGet(
                'SELECT COUNT(*) as count FROM checkins WHERE user_id = ? AND status = ?',
                [userId, 'completed']
            );
            shouldUnlock = result.count >= ach.threshold;
        } else if (ach.condition_type === 'study_count') {
            const result = await dbGet(
                'SELECT COUNT(*) as count FROM plan_tasks WHERE user_id = ? AND status = ?',
                [userId, 'completed']
            );
            shouldUnlock = result.count >= ach.threshold;
        } else if (ach.condition_type === 'total_earned_points') {
            const result = await dbGet(
                `SELECT COALESCE(SUM(points), 0) as total FROM user_points WHERE user_id = ? AND type = 'earn'`,
                [userId]
            );
            shouldUnlock = result.total >= ach.threshold;
        } else if (ach.condition_type === 'wish_redeemed') {
            const result = await dbGet(
                `SELECT COUNT(*) as count FROM wishes WHERE user_id = ? AND status = 'redeemed'`,
                [userId]
            );
            shouldUnlock = result.count >= ach.threshold;
        } else if (ach.condition_type === 'pet_adopted') {
            const result = await dbGet(
                'SELECT COUNT(*) as count FROM pets WHERE user_id = ?',
                [userId]
            );
            shouldUnlock = result.count >= ach.threshold;
        } else if (ach.condition_type === 'continuous_days') {
            const result = await dbGet(
                'SELECT continuous_days FROM users WHERE id = ?',
                [userId]
            );
            shouldUnlock = result && result.continuous_days >= ach.threshold;
        } else if (ach.condition_type === 'all_round') {
            const today = new Date().toISOString().split('T')[0];
            const checkin = await dbGet(
                `SELECT COUNT(*) as count FROM checkins WHERE user_id = ? AND checkin_date = ? AND status = 'completed'`,
                [userId, today]
            );
            const study = await dbGet(
                `SELECT COUNT(*) as count FROM plan_tasks WHERE user_id = ? AND task_date = ? AND status = 'completed'`,
                [userId, today]
            );
            shouldUnlock = checkin.count > 0 && study.count > 0;
        }

        if (shouldUnlock) {
            await dbRun(
                `INSERT INTO user_achievements (user_id, achievement_id) VALUES (?, ?)`,
                [userId, ach.id]
            );
        }
    }
}

// 升级计算
function calculateLevelUp(level, exp, maxExp) {
    let newLevel = level;
    let newExp = exp;
    let newMaxExp = maxExp;

    while (newExp >= newMaxExp) {
        newLevel++;
        newExp -= newMaxExp;
        newMaxExp = Math.floor(newMaxExp * 1.5);
    }

    return { level: newLevel, exp: newExp, maxExp: newMaxExp };
}

module.exports = router;
module.exports.checkAndUnlockAchievement = checkAndUnlockAchievement;
