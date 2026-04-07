// API封装 - 统一管理后端接口调用
const API_BASE_URL = '';

// 获取Token
const getToken = () => localStorage.getItem('token');

// 设置Token
const setToken = (token) => {
    if (token) {
        localStorage.setItem('token', token);
    } else {
        localStorage.removeItem('token');
    }
};

// 获取当前用户
const getCurrentUser = () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
};

// 设置当前用户
const setCurrentUser = (user) => {
    if (user) {
        localStorage.setItem('user', JSON.stringify(user));
    } else {
        localStorage.removeItem('user');
    }
};

// 检查是否已登录
const isLoggedIn = () => !!getToken();

// ==================== 时间工具函数 ====================
// 北京时间偏移量（UTC+8）
const BEIJING_TZ_OFFSET = 8 * 60; // 8小时 = 480分钟

/**
 * 获取当前北京时间
 * @returns {Date} 北京时间
 */
const getBeijingTime = () => {
    const now = new Date();
    const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
    return new Date(utc + (BEIJING_TZ_OFFSET * 60000));
};

/**
 * 获取北京日期字符串 YYYY-MM-DD
 * @returns {string}
 */
const getBeijingDateStr = () => {
    const beijing = getBeijingTime();
    const year = beijing.getFullYear();
    const month = String(beijing.getMonth() + 1).padStart(2, '0');
    const day = String(beijing.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
};

/**
 * 获取北京时间字符串 HH:MM:SS
 * @returns {string}
 */
const getBeijingTimeStr = () => {
    const beijing = getBeijingTime();
    const hours = String(beijing.getHours()).padStart(2, '0');
    const minutes = String(beijing.getMinutes()).padStart(2, '0');
    const seconds = String(beijing.getSeconds()).padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
};

/**
 * 获取北京ISO时间字符串
 * @returns {string}
 */
const getBeijingISOString = () => {
    const beijing = getBeijingTime();
    return beijing.toISOString();
};

/**
 * 判断两个日期是否是同一天（按北京时间）
 * @param {string} date1 - 日期1 YYYY-MM-DD
 * @param {string} date2 - 日期2 YYYY-MM-DD
 * @returns {boolean}
 */
const isSameBeijingDay = (date1, date2) => {
    return date1 === date2;
};

/**
 * 检查日期是否是今天（按北京时间）
 * @param {string} dateStr - 日期 YYYY-MM-DD
 * @returns {boolean}
 */
const isTodayInBeijing = (dateStr) => {
    return dateStr === getBeijingDateStr();
};

// 通用请求函数
const request = async (url, options = {}) => {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${url}`, {
            ...options,
            headers
        });
        
        const data = await response.json();
        
        // 处理未授权
        if (response.status === 401) {
            setToken(null);
            setCurrentUser(null);
            window.location.href = '/login';
            return Promise.reject(new Error('登录已过期'));
        }
        
        if (!data.success) {
            throw new Error(data.message || '请求失败');
        }
        
        return data;
    } catch (error) {
        console.error('API请求错误:', error);
        throw error;
    }
};

// GET请求
const get = (url, params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    const fullUrl = queryString ? `${url}?${queryString}` : url;
    return request(fullUrl, { method: 'GET' });
};

// POST请求
const post = (url, data = {}) => {
    return request(url, {
        method: 'POST',
        body: JSON.stringify(data)
    });
};

// PUT请求
const put = (url, data = {}) => {
    return request(url, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
};

// DELETE请求
const del = (url) => {
    return request(url, { method: 'DELETE' });
};

// ==================== 认证API ====================
const authAPI = {
    // 登录
    login: (username, password) => post('/api/auth/login', { username, password }),
    
    // 注册
    register: (data) => post('/api/auth/register', data),
    
    // 登出
    logout: () => post('/api/auth/logout'),
    
    // 获取用户信息
    getProfile: () => get('/api/auth/profile'),
    
    // 更新用户信息
    updateProfile: (data) => put('/api/auth/profile', data),
    
    // 修改密码
    changePassword: (oldPassword, newPassword) => put('/api/auth/password', { oldPassword, newPassword })
};

// ==================== 习惯API ====================
const habitsAPI = {
    // 获取习惯列表
    getList: (params = {}) => get('/api/habits', params),
    
    // 获取习惯详情
    getDetail: (id) => get(`/api/habits/${id}`),
    
    // 创建习惯
    create: (data) => post('/api/habits', data),
    
    // 更新习惯
    update: (id, data) => put(`/api/habits/${id}`, data),
    
    // 删除习惯
    delete: (id) => del(`/api/habits/${id}`),
    
    // 获取习惯统计
    getStats: (id) => get(`/api/habits/${id}/stats`)
};

// ==================== 打卡API ====================
const checkinsAPI = {
    // 获取打卡记录
    getList: (params = {}) => get('/api/checkins', params),
    
    // 打卡
    checkin: (habitId, data = {}) => post('/api/checkins', { habit_id: habitId, ...data }),
    
    // 补打卡
    makeup: (habitId, checkinDate, note) => post('/api/checkins/makeup', { 
        habit_id: habitId, 
        checkin_date: checkinDate, 
        note 
    }),
    
    // 取消打卡
    cancel: (id) => del(`/api/checkins/${id}`),
    
    // 获取打卡统计
    getStats: () => get('/api/checkins/stats/overview'),
    
    // 获取日历数据
    getCalendar: (year, month) => get('/api/checkins/calendar', { year, month })
};

// ==================== 数据分析API ====================
const analyticsAPI = {
    // 仪表盘数据
    getDashboard: () => get('/api/analytics/dashboard'),
    
    // 习惯分析
    getHabits: (period = '30') => get('/api/analytics/habits', { period }),
    
    // 趋势分析
    getTrends: (type = 'daily', range = '30') => get('/api/analytics/trends', { type, range }),
    
    // 积分统计
    getPoints: (params = {}) => get('/api/analytics/points', params)
};

// ==================== 日志API ====================
const logsAPI = {
    // 获取系统日志
    getSystemLogs: (params = {}) => get('/api/logs/system', params),
    
    // 获取登录日志
    getLoginLogs: (params = {}) => get('/api/logs/login', params),
    
    // 获取日志统计
    getStats: (params = {}) => get('/api/logs/stats', params),
    
    // 清理日志
    cleanup: (days, type) => post('/api/logs/cleanup', { days, type })
};

// 导出API
window.API = {
    auth: authAPI,
    habits: habitsAPI,
    checkins: checkinsAPI,
    analytics: analyticsAPI,
    logs: logsAPI,
    utils: {
        getToken,
        setToken,
        getCurrentUser,
        setCurrentUser,
        isLoggedIn,
        // 时间工具
        getBeijingTime,
        getBeijingDateStr,
        getBeijingTimeStr,
        getBeijingISOString,
        isSameBeijingDay,
        isTodayInBeijing
    }
};
