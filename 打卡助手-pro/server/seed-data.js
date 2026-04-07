const bcrypt = require('bcryptjs');
const { db, dbRun, dbGet } = require('./config/database');

console.log('========================================');
console.log('      导入测试数据');
console.log('========================================\n');

// 测试数据
const seedData = async () => {
    try {
        // 检查是否已有数据
        const existingUsers = await dbGet('SELECT COUNT(*) as count FROM users');
        if (existingUsers.count > 0) {
            console.log('✓ 数据库中已有数据，跳过测试数据导入');
            console.log('  如需重新导入，请先清空数据库：npm run init-db');
            return;
        }

        console.log('开始导入测试数据...\n');

        // 1. 创建测试用户
        console.log('1. 创建测试用户...');
        const adminPassword = await bcrypt.hash('admin123', 10);
        const userPassword = await bcrypt.hash('user123', 10);

        const adminUser = await dbRun(
            `INSERT INTO users (username, password, nickname, email, role, total_points, continuous_days) 
             VALUES (?, ?, ?, ?, ?, ?, ?)`,
            ['admin', adminPassword, '管理员', 'admin@example.com', 'admin', 100, 7]
        );

        const testUser = await dbRun(
            `INSERT INTO users (username, password, nickname, email, role, total_points, continuous_days) 
             VALUES (?, ?, ?, ?, ?, ?, ?)`,
            ['testuser', userPassword, '测试用户', 'test@example.com', 'user', 50, 5]
        );

        console.log(`   ✓ 管理员账号: admin / admin123 (ID: ${adminUser.id})`);
        console.log(`   ✓ 测试账号: testuser / user123 (ID: ${testUser.id})`);

        // 2. 创建习惯数据
        console.log('\n2. 创建习惯数据...');
        const habits = [
            { name: '早起', icon: 'sun', color: '#F59E0B', type: 'daily_once', points: 2 },
            { name: '晨读', icon: 'book', color: '#4A7BF7', type: 'daily_once', points: 3 },
            { name: '运动', icon: 'activity', color: '#22C55E', type: 'daily_once', points: 2 },
            { name: '背单词', icon: 'pen-tool', color: '#8B5CF6', type: 'daily_once', points: 1 },
            { name: '早睡', icon: 'moon', color: '#6B7280', type: 'daily_once', points: 2 }
        ];

        const habitIds = [];
        for (const habit of habits) {
            const result = await dbRun(
                `INSERT INTO habits (user_id, name, icon, color, habit_type, points, description) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)`,
                [testUser.id, habit.name, habit.icon, habit.color, habit.type, habit.points, `每日${habit.name}打卡`]
            );
            habitIds.push(result.id);
        }
        console.log(`   ✓ 创建了 ${habits.length} 个习惯`);

        // 3. 创建打卡记录（最近30天）
        console.log('\n3. 创建打卡记录...');
        const today = new Date();
        let checkinCount = 0;
        let pointsTotal = 0;

        for (let i = 0; i < 30; i++) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];

            // 随机选择2-4个习惯打卡
            const numCheckins = Math.floor(Math.random() * 3) + 2;
            const selectedHabits = habitIds.sort(() => 0.5 - Math.random()).slice(0, numCheckins);

            for (const habitId of selectedHabits) {
                const habit = habits[habitIds.indexOf(habitId)];
                const hour = 6 + Math.floor(Math.random() * 12); // 6点到18点
                const minute = Math.floor(Math.random() * 60);
                const timeStr = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}:00`;

                await dbRun(
                    `INSERT INTO checkins (habit_id, user_id, checkin_date, checkin_time, status, points_earned) 
                     VALUES (?, ?, ?, ?, 'completed', ?)`,
                    [habitId, testUser.id, dateStr, timeStr, habit.points]
                );

                checkinCount++;
                pointsTotal += habit.points;
            }
        }
        console.log(`   ✓ 创建了 ${checkinCount} 条打卡记录`);
        console.log(`   ✓ 累计积分: ${pointsTotal}`);

        // 4. 创建积分记录
        console.log('\n4. 创建积分记录...');
        const pointsRecords = [
            { points: 10, type: 'earn', source: 'checkin', desc: '完成早起打卡' },
            { points: 15, type: 'earn', source: 'checkin', desc: '完成晨读打卡' },
            { points: 10, type: 'earn', source: 'checkin', desc: '完成运动打卡' },
            { points: 5, type: 'earn', source: 'checkin', desc: '完成背单词打卡' },
            { points: 10, type: 'earn', source: 'checkin', desc: '完成早睡打卡' }
        ];

        for (const record of pointsRecords) {
            await dbRun(
                `INSERT INTO user_points (user_id, points, type, source, description) 
                 VALUES (?, ?, ?, ?, ?)`,
                [testUser.id, record.points, record.type, record.source, record.desc]
            );
        }
        console.log(`   ✓ 创建了 ${pointsRecords.length} 条积分记录`);

        // 5. 创建学习计划
        console.log('\n5. 创建学习计划...');
        const studyPlans = [
            { title: '数学练习', category: '数学', repeat: 'daily' },
            { title: '英语阅读', category: '英语', repeat: 'daily' },
            { title: '物理实验', category: '物理', repeat: 'weekly' }
        ];

        for (const plan of studyPlans) {
            await dbRun(
                `INSERT INTO study_plans (user_id, title, category, repeat_type, start_date, content) 
                 VALUES (?, ?, ?, ?, date('now'), ?)`,
                [testUser.id, plan.title, plan.category, plan.repeat, `${plan.title}每日练习`]
            );
        }
        console.log(`   ✓ 创建了 ${studyPlans.length} 个学习计划`);

        // 6. 更新用户统计
        console.log('\n6. 更新用户统计...');
        await dbRun(
            'UPDATE users SET total_points = ?, total_checkins = ? WHERE id = ?',
            [pointsTotal, checkinCount, testUser.id]
        );
        console.log(`   ✓ 用户统计已更新`);

        // 7. 创建系统日志
        console.log('\n7. 创建系统日志...');
        const systemLogs = [
            { action: 'user_login', target: 'user', desc: '用户登录' },
            { action: 'create_habit', target: 'habit', desc: '创建习惯' },
            { action: 'checkin', target: 'checkin', desc: '打卡' },
            { action: 'update_profile', target: 'user', desc: '更新个人资料' }
        ];

        for (const log of systemLogs) {
            await dbRun(
                `INSERT INTO system_logs (user_id, username, action, target_type, new_value) 
                 VALUES (?, ?, ?, ?, ?)`,
                [testUser.id, 'testuser', log.action, log.target, log.desc]
            );
        }
        console.log(`   ✓ 创建了 ${systemLogs.length} 条系统日志`);

        console.log('\n========================================');
        console.log('     测试数据导入完成！');
        console.log('========================================');
        console.log('\n测试账号：');
        console.log('  管理员: admin / admin123');
        console.log('  用户:   testuser / user123');
        console.log('\n现在您可以启动服务进行测试：');
        console.log('  npm start');
        console.log('========================================');

    } catch (error) {
        console.error('\n✗ 导入测试数据失败:', error.message);
        console.error(error.stack);
    } finally {
        db.close((err) => {
            if (err) console.error('数据库关闭失败:', err.message);
            else console.log('\n✓ 数据库连接已关闭');
        });
    }
};

seedData();
