const { db } = require('./config/database');

console.log('========================================');
console.log('      打卡助手 - 数据库初始化');
console.log('========================================\n');

// 用户表
const createUsersTable = `
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    nickname VARCHAR(50),
    avatar TEXT,
    email VARCHAR(100),
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'user',
    status VARCHAR(20) DEFAULT 'active',
    total_points INTEGER DEFAULT 0,
    continuous_days INTEGER DEFAULT 0,
    total_checkins INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)`;

// 习惯表
const createHabitsTable = `
CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50) DEFAULT 'star',
    color VARCHAR(20) DEFAULT '#4A7BF7',
    habit_type VARCHAR(50) DEFAULT 'daily_once',
    points INTEGER DEFAULT 1,
    parent_approval BOOLEAN DEFAULT 0,
    reminder_time TIME,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)`;

// 打卡记录表
const createCheckinsTable = `
CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    checkin_date DATE NOT NULL,
    checkin_time TIME,
    status VARCHAR(20) DEFAULT 'completed',
    points_earned INTEGER DEFAULT 0,
    note TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(habit_id, checkin_date)
)`;

// 学习计划表
const createStudyPlansTable = `
CREATE TABLE IF NOT EXISTS study_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    category VARCHAR(50),
    repeat_type VARCHAR(50) DEFAULT 'once',
    start_date DATE,
    end_date DATE,
    duration INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)`;

// 学习计划任务表（每日任务实例）
const createPlanTasksTable = `
CREATE TABLE IF NOT EXISTS plan_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    task_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES study_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)`;

// 系统日志表
const createSystemLogsTable = `
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id INTEGER,
    old_value TEXT,
    new_value TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
)`;

// 用户积分记录表
const createUserPointsTable = `
CREATE TABLE IF NOT EXISTS user_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    points INTEGER NOT NULL,
    type VARCHAR(20) NOT NULL,
    source VARCHAR(100),
    source_id INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)`;

// 登录日志表
const createLoginLogsTable = `
CREATE TABLE IF NOT EXISTS login_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username VARCHAR(50),
    action VARCHAR(20) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    status VARCHAR(20) DEFAULT 'success',
    fail_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
)`;

// 系统配置表
const createSettingsTable = `
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)`;

// 创建索引
const createIndexes = [
    'CREATE INDEX IF NOT EXISTS idx_checkins_user ON checkins(user_id)',
    'CREATE INDEX IF NOT EXISTS idx_checkins_date ON checkins(checkin_date)',
    'CREATE INDEX IF NOT EXISTS idx_checkins_habit ON checkins(habit_id)',
    'CREATE INDEX IF NOT EXISTS idx_habits_user ON habits(user_id)',
    'CREATE INDEX IF NOT EXISTS idx_plans_user ON study_plans(user_id)',
    'CREATE INDEX IF NOT EXISTS idx_logs_user ON system_logs(user_id)',
    'CREATE INDEX IF NOT EXISTS idx_logs_time ON system_logs(created_at)',
    'CREATE INDEX IF NOT EXISTS idx_points_user ON user_points(user_id)',
    'CREATE INDEX IF NOT EXISTS idx_login_logs_user ON login_logs(user_id)',
    'CREATE INDEX IF NOT EXISTS idx_login_logs_time ON login_logs(created_at)'
];

// 初始化默认配置
const initSettings = [
    { key: 'app_name', value: '小打卡 - 学习打卡助手', description: '应用名称' },
    { key: 'app_version', value: '1.0.0', description: '应用版本' },
    { key: 'points_per_checkin', value: '1', description: '每次打卡基础积分' },
    { key: 'max_continuous_bonus', value: '7', description: '连续打卡最大奖励天数' },
    { key: 'allow_registration', value: 'true', description: '是否允许注册' }
];

// 执行创建表的函数
const createTables = async () => {
    const tables = [
        { name: '用户表', sql: createUsersTable },
        { name: '习惯表', sql: createHabitsTable },
        { name: '打卡记录表', sql: createCheckinsTable },
        { name: '学习计划表', sql: createStudyPlansTable },
        { name: '计划任务表', sql: createPlanTasksTable },
        { name: '系统日志表', sql: createSystemLogsTable },
        { name: '用户积分表', sql: createUserPointsTable },
        { name: '登录日志表', sql: createLoginLogsTable },
        { name: '系统配置表', sql: createSettingsTable }
    ];

    for (const table of tables) {
        await new Promise((resolve, reject) => {
            db.run(table.sql, (err) => {
                if (err) {
                    console.error(`✗ ${table.name}创建失败:`, err.message);
                    reject(err);
                } else {
                    console.log(`✓ ${table.name}创建成功`);
                    resolve();
                }
            });
        });
    }
};

// 创建索引
const createIdx = async () => {
    console.log('\n创建索引...');
    for (const sql of createIndexes) {
        await new Promise((resolve, reject) => {
            db.run(sql, (err) => {
                if (err) reject(err);
                else resolve();
            });
        });
    }
    console.log('✓ 索引创建成功');
};

// 初始化设置
const initDefaultSettings = async () => {
    console.log('\n初始化系统配置...');
    const stmt = db.prepare(`INSERT OR IGNORE INTO settings (key, value, description) VALUES (?, ?, ?)`);
    
    for (const setting of initSettings) {
        await new Promise((resolve, reject) => {
            stmt.run([setting.key, setting.value, setting.description], (err) => {
                if (err) reject(err);
                else resolve();
            });
        });
    }
    
    stmt.finalize();
    console.log('✓ 系统配置初始化完成');
};

// 主函数
const initDatabase = async () => {
    try {
        console.log('开始初始化数据库...\n');
        
        await createTables();
        await createIdx();
        await initDefaultSettings();
        
        console.log('\n========================================');
        console.log('     数据库初始化完成！');
        console.log('========================================');
        console.log('\n您可以运行以下命令：');
        console.log('  npm run seed    - 导入测试数据');
        console.log('  npm start       - 启动服务');
        console.log('  npm run dev     - 开发模式启动');
        
    } catch (error) {
        console.error('\n✗ 数据库初始化失败:', error.message);
    } finally {
        db.close((err) => {
            if (err) console.error('数据库关闭失败:', err.message);
            else console.log('\n✓ 数据库连接已关闭');
        });
    }
};

// 执行初始化
initDatabase();
