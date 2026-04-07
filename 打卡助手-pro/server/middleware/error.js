const response = require('../utils/response');
const { systemLogger } = require('../utils/logger');

// 404处理
const notFoundHandler = (req, res) => {
    response.notFound(res, `未找到资源: ${req.originalUrl}`);
};

// 全局错误处理
const errorHandler = (err, req, res, next) => {
    // 记录错误日志
    systemLogger.error('服务器错误', {
        error: err.message,
        stack: err.stack,
        url: req.originalUrl,
        method: req.method,
        userId: req.user?.id,
        body: req.body,
        params: req.params,
        query: req.query
    });

    // 处理特定类型的错误
    if (err.name === 'ValidationError') {
        return response.badRequest(res, '数据验证失败', err.errors);
    }

    if (err.code === 'SQLITE_CONSTRAINT_UNIQUE') {
        return response.badRequest(res, '数据已存在，请勿重复创建');
    }

    if (err.code === 'SQLITE_CONSTRAINT_FOREIGNKEY') {
        return response.badRequest(res, '关联数据不存在');
    }

    if (err.code === 'SQLITE_CONSTRAINT_NOTNULL') {
        return response.badRequest(res, '必填字段不能为空');
    }

    // 默认服务器错误
    response.serverError(res, process.env.NODE_ENV === 'production' ? '服务器内部错误' : err.message, err);
};

// 异步错误包装器
const asyncHandler = (fn) => (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
};

module.exports = {
    notFoundHandler,
    errorHandler,
    asyncHandler
};
