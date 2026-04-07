const winston = require('winston');
const DailyRotateFile = require('winston-daily-rotate-file');
const path = require('path');

// 日志目录
const logDir = path.join(__dirname, '..', '..', 'logs');

// 定义日志格式
const logFormat = winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.errors({ stack: true }),
    winston.format.splat(),
    winston.format.json()
);

// 控制台输出格式
const consoleFormat = winston.format.combine(
    winston.format.colorize(),
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.printf(({ level, message, timestamp, ...metadata }) => {
        let msg = `${timestamp} [${level}]: ${message}`;
        if (Object.keys(metadata).length > 0) {
            msg += ` ${JSON.stringify(metadata)}`;
        }
        return msg;
    })
);

// 创建日志记录器
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: logFormat,
    defaultMeta: { service: '打卡助手-pro' },
    transports: [
        // 错误日志
        new DailyRotateFile({
            filename: path.join(logDir, 'error-%DATE%.log'),
            datePattern: 'YYYY-MM-DD',
            level: 'error',
            maxSize: '20m',
            maxFiles: '30d'
        }),
        // 综合日志
        new DailyRotateFile({
            filename: path.join(logDir, 'combined-%DATE%.log'),
            datePattern: 'YYYY-MM-DD',
            maxSize: '20m',
            maxFiles: '30d'
        }),
        // 访问日志
        new DailyRotateFile({
            filename: path.join(logDir, 'access-%DATE%.log'),
            datePattern: 'YYYY-MM-DD',
            maxSize: '20m',
            maxFiles: '30d'
        }),
        // API调用日志
        new DailyRotateFile({
            filename: path.join(logDir, 'api-%DATE%.log'),
            datePattern: 'YYYY-MM-DD',
            maxSize: '20m',
            maxFiles: '30d'
        })
    ]
});

// 开发环境添加控制台输出
if (process.env.NODE_ENV !== 'production') {
    logger.add(new winston.transports.Console({
        format: consoleFormat
    }));
}

// 日志分类方法
const systemLogger = {
    info: (message, meta = {}) => logger.info(message, { ...meta, type: 'system' }),
    error: (message, meta = {}) => logger.error(message, { ...meta, type: 'system' }),
    warn: (message, meta = {}) => logger.warn(message, { ...meta, type: 'system' }),
    debug: (message, meta = {}) => logger.debug(message, { ...meta, type: 'system' })
};

const apiLogger = {
    info: (message, meta = {}) => logger.info(message, { ...meta, type: 'api' }),
    error: (message, meta = {}) => logger.error(message, { ...meta, type: 'api' }),
    debug: (message, meta = {}) => logger.debug(message, { ...meta, type: 'api' })
};

const dbLogger = {
    info: (message, meta = {}) => logger.info(message, { ...meta, type: 'database' }),
    error: (message, meta = {}) => logger.error(message, { ...meta, type: 'database' }),
    debug: (message, meta = {}) => logger.debug(message, { ...meta, type: 'database' })
};

module.exports = {
    logger,
    systemLogger,
    apiLogger,
    dbLogger
};
