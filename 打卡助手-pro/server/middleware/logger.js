const { dbRun } = require('../config/database');
const { apiLogger } = require('../utils/logger');

// 请求日志中间件
const requestLogger = (req, res, next) => {
    const start = Date.now();
    
    res.on('finish', () => {
        const duration = Date.now() - start;
        const logData = {
            method: req.method,
            url: req.originalUrl,
            status: res.statusCode,
            duration: `${duration}ms`,
            ip: req.ip || req.connection.remoteAddress,
            userAgent: req.headers['user-agent'],
            userId: req.user?.id,
            username: req.user?.username
        };

        // 记录API日志
        apiLogger.info(`${req.method} ${req.originalUrl} ${res.statusCode} ${duration}ms`, logData);
    });

    next();
};

// 操作日志记录器
const operationLogger = (action, targetType = null) => {
    return async (req, res, next) => {
        // 保存原始send方法
        const originalSend = res.send.bind(res);
        
        res.send = async (data) => {
            // 记录操作日志
            if (req.user && (res.statusCode === 200 || res.statusCode === 201)) {
                try {
                    let targetId = null;
                    let oldValue = null;
                    let newValue = null;
                    
                    // 从请求参数或响应数据中提取目标ID
                    if (req.params.id) {
                        targetId = req.params.id;
                    }
                    
                    // 记录新旧值（用于更新操作）
                    if (req.method === 'PUT' || req.method === 'PATCH') {
                        oldValue = JSON.stringify(req.body.oldValue || {});
                        newValue = JSON.stringify(req.body.newValue || req.body);
                    }
                    
                    await dbRun(
                        `INSERT INTO system_logs 
                        (user_id, username, action, target_type, target_id, old_value, new_value, ip_address, user_agent) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                        [
                            req.user.id,
                            req.user.username,
                            action,
                            targetType,
                            targetId,
                            oldValue,
                            newValue,
                            req.ip || req.connection.remoteAddress,
                            req.headers['user-agent']
                        ]
                    );
                } catch (error) {
                    console.error('操作日志记录失败:', error.message);
                }
            }
            
            return originalSend(data);
        };
        
        next();
    };
};

// 登录日志记录
const logLogin = async (userId, username, action, status, ip, userAgent, failReason = null) => {
    try {
        await dbRun(
            `INSERT INTO login_logs (user_id, username, action, ip_address, user_agent, status, fail_reason) 
             VALUES (?, ?, ?, ?, ?, ?, ?)`,
            [userId, username, action, ip, userAgent, status, failReason]
        );
    } catch (error) {
        console.error('登录日志记录失败:', error.message);
    }
};

module.exports = {
    requestLogger,
    operationLogger,
    logLogin
};
