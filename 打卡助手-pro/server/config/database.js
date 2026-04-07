const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// 数据库文件路径
const DB_PATH = path.join(__dirname, '..', 'database.sqlite');

// 创建数据库连接
const db = new sqlite3.Database(DB_PATH, (err) => {
    if (err) {
        console.error('数据库连接失败:', err.message);
    } else {
        console.log('✓ 数据库连接成功');
    }
});

// 启用外键约束
db.run('PRAGMA foreign_keys = ON');

// 数据库查询封装
const dbQuery = (sql, params = []) => {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) reject(err);
            else resolve(rows);
        });
    });
};

// 数据库执行封装
const dbRun = (sql, params = []) => {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function(err) {
            if (err) reject(err);
            else resolve({ id: this.lastID, changes: this.changes });
        });
    });
};

// 数据库获取单条记录
const dbGet = (sql, params = []) => {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) reject(err);
            else resolve(row);
        });
    });
};

module.exports = {
    db,
    dbQuery,
    dbRun,
    dbGet,
    DB_PATH
};
