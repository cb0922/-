// 统一响应格式
const response = {
    // 成功响应
    success: (res, data = null, message = '操作成功', code = 200) => {
        return res.status(code).json({
            success: true,
            code,
            message,
            data,
            timestamp: new Date().toISOString()
        });
    },

    // 错误响应
    error: (res, message = '操作失败', code = 500, data = null) => {
        return res.status(code).json({
            success: false,
            code,
            message,
            data,
            timestamp: new Date().toISOString()
        });
    },

    // 分页响应
    paginate: (res, list, pagination, message = '获取成功') => {
        return res.status(200).json({
            success: true,
            code: 200,
            message,
            data: {
                list,
                pagination: {
                    page: pagination.page,
                    pageSize: pagination.pageSize,
                    total: pagination.total,
                    totalPages: Math.ceil(pagination.total / pagination.pageSize)
                }
            },
            timestamp: new Date().toISOString()
        });
    },

    // 参数错误
    badRequest: (res, message = '请求参数错误', data = null) => {
        return response.error(res, message, 400, data);
    },

    // 未授权
    unauthorized: (res, message = '未授权访问') => {
        return response.error(res, message, 401);
    },

    // 禁止访问
    forbidden: (res, message = '禁止访问') => {
        return response.error(res, message, 403);
    },

    // 资源不存在
    notFound: (res, message = '资源不存在') => {
        return response.error(res, message, 404);
    },

    // 服务器错误
    serverError: (res, message = '服务器内部错误', error = null) => {
        return response.error(res, message, 500, error ? { error: error.message } : null);
    }
};

module.exports = response;
