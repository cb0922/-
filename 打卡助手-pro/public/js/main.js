// ============================================
// 松鼠打卡 - 主JavaScript文件
// ============================================

// 全局状态
let currentUser = null;
let habits = [];
let currentDate = new Date(); // 临时值，DOMContentLoaded中会更新
let checkins = []; // 打卡记录
let currentEditingHabitId = null; // 当前编辑的习惯ID
let selectedIcon = 'star';
let selectedColor = '#4A7BF7';

// 学习计划和打卡时间记录
let studyPlans = []; // 学习计划列表
let todayStudyTime = 0; // 今日学习时间（分钟）
let todaySportTime = 0; // 今日运动时间（分钟）

// ============================================
// 积分本地缓存引擎（后端为主要数据源）
// ============================================
const POINTS_KEY = 'starBalance';
const HISTORY_KEY = 'pointsHistory';

function getStarBalance() {
    const val = localStorage.getItem(POINTS_KEY);
    return val === null ? (currentUser?.total_points || 0) : parseInt(val, 10);
}
function setStarBalance(val) {
    localStorage.setItem(POINTS_KEY, Math.max(0, val));
}
function getPointsHistory() {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); } catch(e) { return []; }
}
function addPointsRecord(type, amount, source, description) {
    const history = getPointsHistory();
    const balance = getStarBalance() + (type === 'earn' ? amount : -amount);
    setStarBalance(balance);
    history.unshift({
        id: Date.now() + Math.random(),
        type,
        amount,
        source,
        description,
        date: API.utils.getBeijingISOString(),
        balanceAfter: balance
    });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 200)));
    return balance;
}
function calculateStudyPlanStars(minutes) {
    return Math.max(1, Math.ceil(minutes / 30));
}

// 习惯分类映射（用于统计学习时间/运动时间）
const HABIT_CATEGORIES = {
    '学习': ['book', 'edit', 'file', 'calendar', 'clock', 'star'],
    '运动': ['activity', 'sun', 'heart'],
    '其他': ['moon', 'check', 'target', 'award', 'trophy', 'bookmark', 'default']
};

// ============================================
// 图标SVG映射
// ============================================
const ICONS_SVG = {
    star: '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>',
    book: '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>',
    sun: '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>',
    activity: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>',
    moon: '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>',
    heart: '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>',
    check: '<polyline points="20 6 9 17 4 12"></polyline>',
    target: '<circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle>',
    award: '<circle cx="12" cy="8" r="7"></circle><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"></polyline>',
    trophy: '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path><path d="M4 22h16"></path><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"></path>',
    bookmark: '<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>',
    edit: '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>',
    file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline>',
    calendar: '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line>',
    clock: '<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>',
    // 新增图标
    user: '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle>',
    headphones: '<path d="M3 18v-6a9 9 0 0 1 18 0v6"></path><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"></path>',
    droplet: '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>',
    box: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line>',
    home: '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline>',
    smile: '<circle cx="12" cy="12" r="10"></circle><path d="M8 14s1.5 2 4 2 4-2 4-2"></path><line x1="9" y1="9" x2="9.01" y2="9"></line><line x1="15" y1="9" x2="15.01" y2="9"></line>',
    volume: '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>',
    lightbulb: '<path d="M9 18h6"></path><path d="M10 22h4"></path><path d="M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7z"></path>',
    shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>',
    // 减分习惯图标
    'alert-circle': '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line>',
    'x-circle': '<circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line>',
    'alert-triangle': '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line>',
    'x-square': '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="9" x2="15" y2="15"></line><line x1="15" y1="9" x2="9" y2="15"></line>',
    'trash-2': '<polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line>',
    'x-octagon': '<polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line>',
    'phone-missed': '<line x1="23" y1="1" x2="17" y2="7"></line><line x1="17" y1="1" x2="23" y2="7"></line><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>',
    frown: '<circle cx="12" cy="12" r="10"></circle><path d="M16 16s-1.5-2-4-2-4 2-4 2"></path><line x1="9" y1="9" x2="9.01" y2="9"></line><line x1="15" y1="9" x2="15.01" y2="9"></line>',
    users: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path>',
    monitor: '<rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line>',
    'volume-x': '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line>',
    tool: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>',
    default: '<circle cx="12" cy="12" r="10"></circle><path d="M12 8v4l3 3"></path>'
};

// ============================================
// 初始化
// ============================================
document.addEventListener('DOMContentLoaded', async function() {
    // 初始化北京时间
    currentDate = API.utils.getBeijingTime();
    
    // 启动时间更新
    updateTimeDisplay();
    setInterval(updateTimeDisplay, 1000);
    
    // 检查登录状态
    if (!API.utils.isLoggedIn()) {
        window.location.href = '/login';
        return;
    }
    
    try {
        // 加载用户信息
        await loadUserInfo();
        
        // 加载习惯列表
        await loadHabits();
        
        // 加载打卡记录
        await loadCheckins();
        
        // 加载统计数据
        await loadStats();
        
        // 初始化页面
        initPage();
        
    } catch (error) {
        console.error('初始化失败:', error);
        if (error.message && error.message.includes('登录')) {
            logout();
        }
    }
});

// ============================================
// 用户相关
// ============================================
async function loadUserInfo() {
    try {
        const response = await API.auth.getProfile();
        currentUser = response.data;
        
        // 更新UI
        document.getElementById('userName').textContent = currentUser.nickname || currentUser.username;
        document.getElementById('userAvatar').textContent = (currentUser.nickname || currentUser.username).charAt(0);
        
        // 更新统计卡片
        updateStatCard('连续打卡', currentUser.continuous_days + '天');
        updateStatCard('累计完成', currentUser.total_checkins + '个');
        
    } catch (error) {
        console.error('加载用户信息失败:', error);
        throw error;
    }
}

function updateStatCard(label, value) {
    const cards = document.querySelectorAll('.stat-card');
    cards.forEach(card => {
        const cardLabel = card.querySelector('.stat-label');
        if (cardLabel && cardLabel.textContent.includes(label)) {
            const valueEl = card.querySelector('.stat-value, .highlight');
            if (valueEl) {
                valueEl.textContent = value;
            }
        }
    });
}

function logout() {
    API.utils.setToken(null);
    API.utils.setCurrentUser(null);
    window.location.href = '/login';
}

function goToDashboard() {
    window.location.href = '/pages/dashboard.html';
}

function goToLogs() {
    window.location.href = '/pages/logs.html';
}

// ============================================
// 习惯管理
// ============================================
async function loadHabits() {

    try {
        const response = await API.habits.getList({ status: 'active' });

        habits = response.data.list || [];

        
        // 更新习惯列表UI
        renderHabitList();
        
        // 更新统计数据（今日任务数量依赖习惯数）
        await loadStats();
        
    } catch (error) {
        console.error('加载习惯列表失败:', error);
    }
}

function renderHabitList() {

    const container = document.querySelector('.habit-cards');
    if (!container) {

        return;
    }
    
    if (habits.length === 0) {
        container.innerHTML = `
            <div class="habit-empty-state">
                <div class="habit-empty-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#4A90E2" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M12 8v4l3 3"></path>
                    </svg>
                </div>
                <h3 class="habit-empty-title">还没有行为习惯</h3>
                <p class="habit-empty-desc">创建你的第一个行为习惯，开始培养好习惯！</p>
                <button class="btn btn-primary btn-create-first" onclick="openHabitModal()">
                    创建第一个习惯
                </button>
            </div>
        `;
        return;
    }
    
    try {
        container.innerHTML = habits.map(habit => {
            try {
                return `
        <div class="habit-card" data-id="${habit.id}">
            <div class="habit-card-header">
                <div class="habit-icon" style="background: ${habit.color};">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        ${getIconSvg(habit.icon)}
                    </svg>
                </div>
                <div class="habit-info">
                    <h4 class="habit-name">${habit.name}</h4>
                    <p class="habit-desc">${habit.description || '暂无描述'}</p>
                </div>
            </div>
            <div class="habit-card-footer">
                <div class="habit-meta">
                    <span class="habit-type">${getHabitTypeText(habit.habit_type)}</span>
                    <span class="habit-points" style="color: ${habit.points < 0 ? '#EF4444' : '#22C55E'}">${habit.points > 0 ? '+' : ''}${habit.points}⭐</span>
                </div>
                <button class="btn-checkin" onclick="checkinHabit(${habit.id})" ${isCheckedInToday(habit.id) ? 'disabled' : ''} style="${habit.points < 0 ? 'background: linear-gradient(135deg, #F87171, #EF4444);' : ''}">
                    ${isCheckedInToday(habit.id) ? '已打卡' : (habit.points < 0 ? '记录' : '打卡')}
                </button>
            </div>
        </div>`;
            } catch (e) {

                return '';
            }
        }).join('');
    } catch (e) {

    }
    

    if (habits.length > 0) {

    }
    
    // 添加事件委托
    container.onclick = function(e) {
        const btn = e.target.closest('.btn-checkin');
        if (btn && !btn.disabled) {
            const card = btn.closest('.habit-card');
            if (card) {
                const habitId = parseInt(card.dataset.id);

                checkinHabit(habitId);
            }
        }
    };
}

function getIconSvg(icon) {
    if (!icon || !ICONS_SVG[icon]) {

        return ICONS_SVG.default;
    }
    return ICONS_SVG[icon];
}

function getHabitTypeText(type) {
    const types = {
        daily_once: '每日一次',
        daily_multi: '每日多次',
        weekly_once: '每周一次',
        weekly_multi: '每周多次'
    };
    return types[type] || '每日一次';
}

// ============================================
// 打卡功能 - 完整实现
// ============================================

// 加载打卡记录
async function loadCheckins() {
    try {
        const response = await API.checkins.getList({ page: 1, pageSize: 100 });
        checkins = response.data.list || [];
    } catch (error) {
        console.error('加载打卡记录失败:', error);
    }
}

function isCheckedInToday(habitId) {
    const today = API.utils.getBeijingDateStr();
    return checkins.some(c => 
        c.habit_id === habitId && 
        c.checkin_date === today &&
        c.status === 'completed'
    );
}

function isCheckedInOnDate(habitId, date) {
    return checkins.some(c => 
        c.habit_id === habitId && 
        c.checkin_date === date &&
        c.status === 'completed'
    );
}

async function checkinHabit(habitId) {
    try {
        const response = await API.checkins.checkin(habitId);
        const points = response.data.points_earned || 0;
        
        // 积分记录
        const habit = habits.find(h => h.id === habitId);
        addPointsRecord('earn', points, 'habit', `习惯打卡：${habit ? habit.name : ''}`);
        showToast(`打卡成功！+${points}⭐`);
        
        // 立即更新本地打卡记录（用于实时统计）
        if (habit) {
            checkins.push({
                id: Date.now(),
                habit_id: habitId,
                checkin_date: API.utils.getBeijingDateStr(),
                status: 'completed',
                points_earned: points
            });
        }
        
        // 刷新数据
        await loadCheckins();
        await loadUserInfo();
        await loadHabits();
        
        // 关键：刷新统计数据
        await loadStats();
        
        // 更新日历显示
        updateHabitCalendar();
        
    } catch (error) {
        showToast(error.message || '打卡失败', 'error');
    }
}

// 补打卡功能
async function makeupCheckin(habitId, date) {
    try {
        const response = await API.checkins.makeup(habitId, date);
        const points = response.data.points_earned || 0;
        const habit = habits.find(h => h.id === habitId);
        addPointsRecord('earn', points, 'habit', `补打卡：${habit ? habit.name : ''}`);
        showToast(`补打卡成功！+${points}⭐`);
        
        // 刷新数据
        await loadCheckins();
        await loadUserInfo();
        await loadStats();
        await loadHabits();
        updateHabitCalendar();
        
    } catch (error) {
        showToast(error.message || '补打卡失败', 'error');
    }
}

// 取消打卡
async function cancelCheckin(checkinId) {
    if (!confirm('确定要取消这次打卡吗？')) {
        return;
    }
    
    try {
        const checkin = checkins.find(c => c.id === checkinId);
        const points = checkin ? (checkin.points_earned || 0) : 0;
        await API.checkins.cancel(checkinId);
        if (points > 0) {
            addPointsRecord('spend', points, 'habit', '取消打卡扣除');
        }
        showToast('打卡已取消');
        
        // 刷新数据
        await loadCheckins();
        await loadUserInfo();
        await loadStats();
        await loadHabits();
        updateHabitCalendar();
        
    } catch (error) {
        showToast(error.message || '取消失败', 'error');
    }
}

// 显示可补打卡日期
function showMakeupDialog() {
    const today = new Date(API.utils.getBeijingDateStr());
    const makeupDates = [];
    
    // 获取最近7天的日期
    for (let i = 1; i <= 7; i++) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        makeupDates.push(dateStr);
    }
    
    // 创建补打卡对话框
    let dialog = document.getElementById('makeupDialog');
    if (!dialog) {
        dialog = document.createElement('div');
        dialog.id = 'makeupDialog';
        dialog.className = 'modal-overlay';
        document.body.appendChild(dialog);
    }
    
    dialog.innerHTML = `
        <div class="modal-container" style="max-width: 400px;">
            <div class="modal-header">
                <h3 class="modal-title">选择补打卡日期</h3>
                <button class="modal-close" onclick="closeMakeupDialog()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="modal-body">
                <div class="makeup-dates">
                    ${makeupDates.map(date => {
                        const dateObj = new Date(date);
                        const dayStr = `${dateObj.getMonth() + 1}月${dateObj.getDate()}日`;
                        const weekDay = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][dateObj.getDay()];
                        return `
                            <div class="makeup-date-item" onclick="showHabitSelectForMakeup('${date}')">
                                <span class="date-text">${dayStr} ${weekDay}</span>
                                <span class="arrow">›</span>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        </div>
    `;
    
    dialog.classList.add('active');
}

function closeMakeupDialog() {
    const dialog = document.getElementById('makeupDialog');
    if (dialog) {
        dialog.classList.remove('active');
    }
}

// 选择习惯进行补打卡
function showHabitSelectForMakeup(date) {
    const uncheckinHabits = habits.filter(h => !isCheckedInOnDate(h.id, date));
    
    if (uncheckinHabits.length === 0) {
        showToast('该日期所有习惯都已打卡', 'info');
        return;
    }
    
    let dialog = document.getElementById('makeupHabitDialog');
    if (!dialog) {
        dialog = document.createElement('div');
        dialog.id = 'makeupHabitDialog';
        dialog.className = 'modal-overlay';
        document.body.appendChild(dialog);
    }
    
    const dateObj = new Date(date);
    const dayStr = `${dateObj.getMonth() + 1}月${dateObj.getDate()}日`;
    
    dialog.innerHTML = `
        <div class="modal-container" style="max-width: 400px;">
            <div class="modal-header">
                <h3 class="modal-title">${dayStr} - 选择要补打卡的习惯</h3>
                <button class="modal-close" onclick="closeMakeupHabitDialog()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="modal-body">
                <div class="makeup-habits">
                    ${uncheckinHabits.map(habit => `
                        <div class="makeup-habit-item" onclick="makeupCheckin(${habit.id}, '${date}'); closeMakeupHabitDialog(); closeMakeupDialog();">
                            <div class="habit-icon-small" style="background: ${habit.color};">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    ${getIconSvg(habit.icon)}
                                </svg>
                            </div>
                            <span class="habit-name">${habit.name}</span>
                            <span class="points">+${habit.points}⭐</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
    
    dialog.classList.add('active');
}

function closeMakeupHabitDialog() {
    const dialog = document.getElementById('makeupHabitDialog');
    if (dialog) {
        dialog.classList.remove('active');
    }
}

// ============================================
// 统计数据 - 实时计算
// ============================================
async function loadStats() {
    try {
        const today = API.utils.getBeijingDateStr();
        
        // 1. 计算习惯相关数据
        const totalHabits = habits.length;
        const completedHabits = checkins.filter(c => 
            c.checkin_date === today && c.status === 'completed'
        ).length;
        
        // 2. 计算学习计划相关数据
        const todayPlans = studyPlans.filter(p => p.createdAt === today);
        const totalPlans = todayPlans.length;
        const completedPlans = todayPlans.filter(p => p.completed).length;
        
        // 3. 总任务数 = 习惯数 + 学习计划数
        const totalTasks = totalHabits + totalPlans;
        const completedTasks = completedHabits + completedPlans;
        
        // 4. 计算完成率
        const completionRate = totalTasks > 0 
            ? Math.round((completedTasks / totalTasks) * 100) 
            : 0;
        
        // 5. 计算今日学习时间和运动时间
        calculateTodayStats();
        
        // 6. 更新统计卡片
        document.querySelectorAll('.stat-value.blue').forEach((el, index) => {
            if (index === 0) {
                // 今日学习时间
                el.textContent = formatTime(todayStudyTime);
            }
            if (index === 1) {
                // 今日运动时间
                el.textContent = formatTime(todaySportTime);
            }
            if (index === 2) {
                // 今日任务数量 = 习惯数 + 计划数
                el.textContent = totalTasks;
            }
            if (index === 3) {
                // 今日完成率
                el.textContent = completionRate + '%';
            }
        });
        
        // 7. 更新副标题统计
        updateHeaderStats(completedTasks, totalPlans);
        
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}

// 更新头部统计信息
function updateHeaderStats(completedHabits, completedPlans) {
    const statsText = document.querySelector('.user-stats');
    if (statsText) {
        const continuousDays = currentUser?.continuous_days || 0;
        statsText.innerHTML = `你已连续打卡 <span class="highlight">${continuousDays}</span> 天，已累计完成 <span class="highlight">${completedHabits}</span> 个习惯、<span class="highlight">${completedPlans}</span> 个学习计划`;
    }
}

// 计算今日学习和运动时间
function calculateTodayStats() {
    const today = API.utils.getBeijingDateStr();
    todayStudyTime = 0;
    todaySportTime = 0;
    
    // 遍历今日打卡记录，根据习惯类型统计时间
    const todayCheckins = checkins.filter(c => c.checkin_date === today && c.status === 'completed');
    
    todayCheckins.forEach(checkin => {
        const habit = habits.find(h => h.id === checkin.habit_id);
        if (!habit) return;
        
        // 估算每次打卡的时间（默认30分钟，可根据习惯名称智能判断）
        const estimatedMinutes = estimateHabitTime(habit);
        
        // 根据习惯图标或名称判断是学习时间还是运动时间
        if (isStudyHabit(habit)) {
            todayStudyTime += estimatedMinutes;
        } else if (isSportHabit(habit)) {
            todaySportTime += estimatedMinutes;
        }
    });
}

// 判断是否为学习习惯
function isStudyHabit(habit) {
    const studyKeywords = ['学习', '阅读', '作业', '复习', '预习', '背诵', '写字', '练习', 'book', 'edit', 'file'];
    const name = habit.name || '';
    const icon = habit.icon || '';
    
    return studyKeywords.some(kw => name.includes(kw) || icon.includes(kw));
}

// 判断是否为运动习惯
function isSportHabit(habit) {
    const sportKeywords = ['运动', '跑步', '锻炼', '健身', '户外', '体育', 'activity', 'sun'];
    const name = habit.name || '';
    const icon = habit.icon || '';
    
    return sportKeywords.some(kw => name.includes(kw) || icon.includes(kw));
}

// 估算习惯所需时间（分钟）
function estimateHabitTime(habit) {
    const name = habit.name || '';
    
    // 根据习惯名称智能判断时间
    if (name.includes('30分钟')) return 30;
    if (name.includes('1小时') || name.includes('60分钟')) return 60;
    if (name.includes('45分钟')) return 45;
    if (name.includes('15分钟')) return 15;
    if (name.includes('跑步') || name.includes('运动')) return 30;
    if (name.includes('阅读') || name.includes('晨读')) return 30;
    if (name.includes('作业')) return 45;
    
    // 默认30分钟
    return 30;
}

// 格式化时间显示（分钟转为 Xm 或 XhXm）
function formatTime(minutes) {
    if (minutes === 0) return '0m';
    if (minutes < 60) return `${minutes}m`;
    
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (mins === 0) return `${hours}h`;
    return `${hours}h${mins}m`;
}

// ============================================
// 习惯模态框 - 完整功能
// ============================================
function openHabitModal(habitId = null) {
    const modal = document.getElementById('habitModal');
    if (!modal) return;
    
    // 重置表单
    resetHabitForm();
    
    if (habitId) {
        // 编辑模式
        currentEditingHabitId = habitId;
        const habit = habits.find(h => h.id === habitId);
        if (habit) {
            fillHabitForm(habit);
            document.querySelector('.modal-title').textContent = '编辑习惯';
            document.querySelector('.btn-create').textContent = '保存';
        }
    } else {
        // 创建模式
        currentEditingHabitId = null;
        document.querySelector('.modal-title').textContent = '新建习惯';
        document.querySelector('.btn-create').textContent = '创建';
    }
    
    modal.classList.add('active');
    initHabitModalEvents();
}

function closeHabitModal() {
    const modal = document.getElementById('habitModal');
    if (modal) {
        modal.classList.remove('active');
    }
    currentEditingHabitId = null;
}

function resetHabitForm() {
    // 重置输入
    const nameInput = document.querySelector('#habitModal .form-input');
    const descInput = document.querySelector('#habitModal .form-textarea');
    const pointsInput = document.querySelector('#habitModal input[type="number"]');
    const typeSelect = document.querySelector('#habitModal .form-select');
    const approvalCheckbox = document.querySelector('#habitModal .checkbox-input');
    
    if (nameInput) nameInput.value = '';
    if (descInput) descInput.value = '';
    if (pointsInput) pointsInput.value = '1';
    if (typeSelect) typeSelect.selectedIndex = 0;
    if (approvalCheckbox) approvalCheckbox.checked = false;
    
    // 重置图标和颜色选择
    selectedIcon = 'star';
    selectedColor = '#4A7BF7';
    updateIconSelection();
    updateColorSelection();
    updatePreview();
}

function fillHabitForm(habit) {
    const nameInput = document.querySelector('#habitModal .form-input');
    const descInput = document.querySelector('#habitModal .form-textarea');
    const pointsInput = document.querySelector('#habitModal input[type="number"]');
    const typeSelect = document.querySelector('#habitModal .form-select');
    
    if (nameInput) nameInput.value = habit.name || '';
    if (descInput) descInput.value = habit.description || '';
    if (pointsInput) pointsInput.value = habit.points || 1;
    if (typeSelect) {
        const typeMap = {
            'daily_once': 0,
            'daily_multi': 1,
            'weekly_once': 2,
            'weekly_multi': 3
        };
        typeSelect.selectedIndex = typeMap[habit.habit_type] || 0;
    }
    
    selectedIcon = habit.icon || 'star';
    selectedColor = habit.color || '#4A7BF7';
    updateIconSelection();
    updateColorSelection();
    updatePreview();
}

function initHabitModalEvents() {
    // 图标选择
    document.querySelectorAll('.icon-item').forEach(item => {
        item.onclick = () => {
            selectedIcon = item.dataset.icon;
            updateIconSelection();
            updatePreview();
        };
    });
    
    // 颜色选择
    document.querySelectorAll('.color-item').forEach(item => {
        item.onclick = () => {
            selectedColor = item.dataset.color;
            updateColorSelection();
            updatePreview();
        };
    });
}

function updateIconSelection() {
    document.querySelectorAll('.icon-item').forEach(item => {
        item.classList.toggle('active', item.dataset.icon === selectedIcon);
    });
}

function updateColorSelection() {
    document.querySelectorAll('.color-item').forEach(item => {
        item.classList.toggle('active', item.dataset.color === selectedColor);
    });
}

function updatePreview() {
    const previewIcon = document.getElementById('previewIcon');
    if (previewIcon) {
        previewIcon.style.background = selectedColor;
        previewIcon.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${getIconSvg(selectedIcon)}</svg>`;
    }
}

async function createHabit() {
    const nameInput = document.querySelector('#habitModal .form-input');
    const descInput = document.querySelector('#habitModal .form-textarea');
    const pointsInput = document.querySelector('#habitModal input[type="number"]');
    const typeSelect = document.querySelector('#habitModal .form-select');
    const approvalCheckbox = document.querySelector('#habitModal .checkbox-input');
    
    const name = nameInput ? nameInput.value.trim() : '';
    
    if (!name) {
        showToast('请输入习惯名称', 'error');
        return;
    }
    
    const habitData = {
        name: name,
        description: descInput ? descInput.value.trim() : '',
        icon: selectedIcon,
        color: selectedColor,
        habit_type: typeSelect ? typeSelect.value : 'daily_once',
        points: parseInt(pointsInput ? pointsInput.value : 1) || 1,
        parent_approval: approvalCheckbox ? approvalCheckbox.checked : false
    };
    
    try {
        if (currentEditingHabitId) {
            // 编辑模式
            await API.habits.update(currentEditingHabitId, habitData);
            showToast('习惯更新成功');
        } else {
            // 创建模式
            await API.habits.create(habitData);
            showToast('习惯创建成功');
        }
        
        closeHabitModal();
        await loadHabits();
        
    } catch (error) {
        showToast(error.message || '操作失败', 'error');
    }
}

// 编辑习惯
function editHabit(habitId) {
    openHabitModal(habitId);
}

// 删除习惯
async function deleteHabit(habitId) {
    if (!confirm('确定要删除这个习惯吗？删除后无法恢复。')) {
        return;
    }
    
    try {
        await API.habits.delete(habitId);
        showToast('习惯已删除');
        await loadHabits();
    } catch (error) {
        showToast(error.message || '删除失败', 'error');
    }
}

function renderHabitListWithManage() {
    const container = document.querySelector('.habit-cards');
    if (!container) return;
    
    if (habits.length === 0) {
        container.innerHTML = `
            <div class="habit-empty-state">
                <div class="habit-empty-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#4A90E2" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M12 8v4l3 3"></path>
                    </svg>
                </div>
                <h3 class="habit-empty-title">还没有行为习惯</h3>
                <p class="habit-empty-desc">创建你的第一个行为习惯，开始培养好习惯！</p>
                <button class="btn btn-primary btn-create-first" onclick="openHabitModal()">
                    创建第一个习惯
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = habits.map(habit => `
        <div class="habit-card" data-id="${habit.id}">
            <div class="habit-card-header">
                <div class="habit-icon" style="background: ${habit.color};">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        ${getIconSvg(habit.icon)}
                    </svg>
                </div>
                <div class="habit-info">
                    <h4 class="habit-name">${habit.name}</h4>
                    <p class="habit-desc">${habit.description || '暂无描述'}</p>
                </div>
            </div>
            <div class="habit-card-footer">
                <div class="habit-meta">
                    <span class="habit-type">${getHabitTypeText(habit.habit_type)}</span>
                    <span class="habit-points">${habit.points > 0 ? '+' : ''}${habit.points}⭐</span>
                </div>
                <div class="habit-actions">
                    <button class="btn-checkin" onclick="checkinHabit(${habit.id})" ${isCheckedInToday(habit.id) ? 'disabled' : ''}>
                        ${isCheckedInToday(habit.id) ? '已打卡' : '打卡'}
                    </button>
                    <button class="btn-edit" onclick="editHabit(${habit.id})">编辑</button>
                    <button class="btn-delete" onclick="deleteHabit(${habit.id})">删除</button>
                </div>
            </div>
        </div>
    `).join('');
}

// ============================================
// 时间显示
// ============================================
function updateTimeDisplay() {
    const now = API.utils.getBeijingTime();
    const timeStr = now.toLocaleString('zh-CN', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit', 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: false 
    });
    
    // 更新页面上的时间显示
    const timeElements = document.querySelectorAll('.beijing-time');
    timeElements.forEach(el => el.textContent = timeStr);
}

// ============================================
// 页面初始化
// ============================================
function initPage() {
    // 用户菜单下拉
    const userMenu = document.getElementById('userMenu');
    const userDropdown = document.getElementById('userDropdown');
    
    if (userMenu && userDropdown) {
        userMenu.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });
        
        document.addEventListener('click', () => {
            userDropdown.classList.remove('show');
        });
    }
    
    // 初始化日历
    updateCalendar();
    updateHabitCalendar();
    
    // 初始化筛选标签
    initFilterTags();
    
    // 初始化搜索
    initSearch();
    
    // 初始化学习计划
    loadStudyPlans();
    
    // 初始化电子宠物
    initPetSystem();
    
    // 动画效果
    initAnimations();
}

// 初始化筛选标签
function initFilterTags() {
    const filterTags = document.querySelectorAll('.filter-tag');
    filterTags.forEach(tag => {
        tag.addEventListener('click', function() {
            filterTags.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            const filter = this.textContent.trim();
            filterHabits(filter);
        });
    });
}

// 筛选习惯
function filterHabits(filter) {
    const cards = document.querySelectorAll('.habit-card');
    
    cards.forEach(card => {
        const habitId = parseInt(card.dataset.id);
        const habit = habits.find(h => h.id === habitId);
        if (!habit) return;
        
        let shouldShow = true;
        
        switch(filter) {
            case '加分':
                shouldShow = habit.points > 0;
                break;
            case '扣分':
                shouldShow = habit.points < 0;
                break;
            case '已完成':
                shouldShow = isCheckedInToday(habit.id);
                break;
            case '待完成':
                shouldShow = !isCheckedInToday(habit.id);
                break;
            case '每日一次':
                shouldShow = habit.habit_type === 'daily_once';
                break;
            case '每日多次':
                shouldShow = habit.habit_type === 'daily_multi';
                break;
            case '每周多次':
                shouldShow = habit.habit_type === 'weekly_multi';
                break;
            case '全部':
            default:
                shouldShow = true;
        }
        
        card.style.display = shouldShow ? 'block' : 'none';
    });
}

// 初始化搜索
function initSearch() {
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const keyword = this.value.trim().toLowerCase();
            searchHabits(keyword);
        });
    }
}

// 搜索习惯
function searchHabits(keyword) {
    const cards = document.querySelectorAll('.habit-card');
    
    cards.forEach(card => {
        const habitId = parseInt(card.dataset.id);
        const habit = habits.find(h => h.id === habitId);
        if (!habit) return;
        
        const match = habit.name.toLowerCase().includes(keyword) ||
                     (habit.description && habit.description.toLowerCase().includes(keyword));
        
        card.style.display = match ? 'block' : 'none';
    });
}

function initAnimations() {
    // 卡片入场动画
    const cards = document.querySelectorAll('.stat-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.3s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 50);
    });
}

// ============================================
// 工具函数
// ============================================
function showToast(message, type = 'success') {
    // 创建toast元素
    let toast = document.getElementById('globalToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'globalToast';
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            z-index: 10000;
            transition: all 0.3s;
        `;
        document.body.appendChild(toast);
    }
    
    toast.textContent = message;
    toast.style.background = type === 'success' ? '#10b981' : '#ef4444';
    toast.style.color = 'white';
    toast.style.opacity = '1';
    
    setTimeout(() => {
        toast.style.opacity = '0';
    }, 3000);
}

// ============================================
// 保持原有功能
// ============================================
// Tab切换
function switchTab(tabName) {
    // 隐藏积分成就页面
    const pointsPage = document.getElementById('pointsPage');
    if (pointsPage) {
        pointsPage.classList.remove('active');
    }
    
    // 隐藏宠物页面
    const petPage = document.getElementById('petPage');
    if (petPage) {
        petPage.style.display = 'none';
        petPage.classList.remove('active');
    }
    
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    document.querySelector(`.tab-btn[data-tab="${tabName}"]`)?.classList.add('active');
    document.getElementById(`${tabName}Tab`)?.classList.add('active');
    
    // 滚动到内容区域顶部
    setTimeout(() => {
        const tabHeader = document.querySelector('.tab-header');
        if (tabHeader) {
            const rect = tabHeader.getBoundingClientRect();
            const scrollTop = window.pageYOffset + rect.top - 80;
            window.scrollTo({ top: scrollTop, behavior: 'smooth' });
        }
    }, 100);
}

// ============================================
// 学习计划管理
// ============================================

// 添加学习计划
function addStudyPlan() {
    const planName = prompt('请输入学习计划名称：', '例如：数学作业、英语阅读');
    if (!planName || !planName.trim()) return;
    
    const planTime = prompt('预计学习时间（分钟）：', '30');
    const minutes = parseInt(planTime) || 30;
    
    const plan = {
        id: Date.now(),
        name: planName.trim(),
        estimatedTime: minutes,
        completed: false,
        completedTime: 0,
        createdAt: API.utils.getBeijingDateStr()
    };
    
    studyPlans.push(plan);
    saveStudyPlans();
    renderStudyPlans();
    
    showToast('学习计划添加成功');
}

// 渲染学习计划列表
function renderStudyPlans() {
    const container = document.querySelector('.plan-empty-state')?.parentElement;
    if (!container) return;
    
    const today = API.utils.getBeijingDateStr();
    const todayPlans = studyPlans.filter(p => p.createdAt === today);
    
    if (todayPlans.length === 0) {
        container.innerHTML = `
            <div class="plan-header">
                <div class="plan-title-wrapper">
                    <div class="title-indicator"></div>
                    <h3 class="plan-title">我的计划</h3>
                </div>
                <button class="btn-share" onclick="addStudyPlan()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="12" y1="5" x2="12" y2="19"></line>
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                    </svg>
                    添加计划
                </button>
            </div>
            <div class="plan-empty-state">
                <div class="book-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#C5C9D0" stroke-width="1.5">
                        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
                    </svg>
                </div>
                <p style="color: #9CA3AF; margin-top: 12px;">还没有学习计划，点击"添加计划"开始</p>
            </div>
        `;
        return;
    }
    
    // 计算今日学习进度
    const totalTime = todayPlans.reduce((sum, p) => sum + p.estimatedTime, 0);
    const completedTime = todayPlans.reduce((sum, p) => sum + (p.completed ? p.estimatedTime : 0), 0);
    const progress = totalTime > 0 ? Math.round((completedTime / totalTime) * 100) : 0;
    
    let html = `
        <div class="plan-header">
            <div class="plan-title-wrapper">
                <div class="title-indicator"></div>
                <h3 class="plan-title">我的计划</h3>
            </div>
            <div style="display: flex; gap: 12px; align-items: center;">
                <span style="font-size: 13px; color: #6B7280;">今日进度: ${progress}%</span>
                <button class="btn-share" onclick="addStudyPlan()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="12" y1="5" x2="12" y2="19"></line>
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                    </svg>
                    添加计划
                </button>
            </div>
        </div>
        <div style="background: white; border-radius: 12px; padding: 16px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 13px; color: #6B7280;">已完成: ${formatTime(completedTime)}</span>
                <span style="font-size: 13px; color: #6B7280;">总计: ${formatTime(totalTime)}</span>
            </div>
            <div style="background: #E5E7EB; height: 8px; border-radius: 4px; overflow: hidden;">
                <div style="background: #4A7BF7; height: 100%; width: ${progress}%; transition: width 0.3s;"></div>
            </div>
        </div>
        <div class="study-plan-list">
    `;
    
    todayPlans.forEach(plan => {
        html += `
            <div class="study-plan-item" data-id="${plan.id}" style="
                background: white;
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                gap: 12px;
                border: 2px solid ${plan.completed ? '#22C55E' : '#E5E7EB'};
            ">
                <input type="checkbox" 
                    ${plan.completed ? 'checked' : ''} 
                    onchange="toggleStudyPlan(${plan.id})"
                    style="width: 20px; height: 20px; cursor: pointer;">
                <div style="flex: 1;">
                    <div style="font-weight: 500; color: ${plan.completed ? '#9CA3AF' : '#1F2937'}; 
                                text-decoration: ${plan.completed ? 'line-through' : 'none'};">
                        ${plan.name}
                    </div>
                    <div style="font-size: 13px; color: #6B7280; margin-top: 4px;">
                        预计 ${plan.estimatedTime} 分钟
                    </div>
                </div>
                <button onclick="deleteStudyPlan(${plan.id})" style="
                    background: none;
                    border: none;
                    color: #EF4444;
                    cursor: pointer;
                    padding: 4px;
                ">删除</button>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// 切换学习计划完成状态
function toggleStudyPlan(planId) {
    const plan = studyPlans.find(p => p.id === planId);
    if (!plan) return;
    
    plan.completed = !plan.completed;
    const stars = calculateStudyPlanStars(plan.estimatedTime);
    
    if (plan.completed) {
        // 完成计划，增加学习时间和星星
        todayStudyTime += plan.estimatedTime;
        addPointsRecord('earn', stars, 'study', `完成学习计划：${plan.name}`);
        showToast(`完成计划！学习时间 +${plan.estimatedTime}分钟，+${stars}⭐`);
    } else {
        // 取消完成，减少学习时间和星星
        todayStudyTime = Math.max(0, todayStudyTime - plan.estimatedTime);
        addPointsRecord('spend', stars, 'study', `取消完成学习计划：${plan.name}`);
    }
    
    saveStudyPlans();
    renderStudyPlans();
    updateStudyTimeDisplay();
    
    // 关键：刷新统计数据（任务数量和完成率）
    loadStats();
}

// 删除学习计划
function deleteStudyPlan(planId) {
    if (!confirm('确定要删除这个学习计划吗？')) return;
    
    const plan = studyPlans.find(p => p.id === planId);
    if (plan && plan.completed) {
        // 如果已完成，减少学习时间和星星
        todayStudyTime = Math.max(0, todayStudyTime - plan.estimatedTime);
        const stars = calculateStudyPlanStars(plan.estimatedTime);
        addPointsRecord('spend', stars, 'study', `删除已完成学习计划：${plan.name}`);
    }
    
    studyPlans = studyPlans.filter(p => p.id !== planId);
    saveStudyPlans();
    renderStudyPlans();
    updateStudyTimeDisplay();
    
    // 关键：刷新统计数据
    loadStats();
    
    showToast('计划已删除');
}

// 保存学习计划到本地存储
function saveStudyPlans() {
    localStorage.setItem('studyPlans', JSON.stringify(studyPlans));
}

// 加载学习计划
function loadStudyPlans() {
    const saved = localStorage.getItem('studyPlans');
    if (saved) {
        studyPlans = JSON.parse(saved);
        // 只保留今天的计划
        const today = API.utils.getBeijingDateStr();
        studyPlans = studyPlans.filter(p => p.createdAt === today);
    }
    renderStudyPlans();
}

// 更新学习时间显示
function updateStudyTimeDisplay() {
    document.querySelectorAll('.stat-value.blue').forEach((el, index) => {
        if (index === 0) {
            el.textContent = formatTime(todayStudyTime);
        }
    });
}

// 日历相关
function updateCalendar() {
    // 使用北京时间更新日历
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const date = currentDate.getDate();
    const day = currentDate.getDay();
    
    // 计算当前周的起始日期（周一）
    const weekStart = new Date(currentDate);
    const dayOfWeek = day === 0 ? 6 : day - 1; // 转换为周一开始(0=周一, 6=周日)
    weekStart.setDate(date - dayOfWeek);
    
    // 计算周数
    const weekNum = getWeekNumber(currentDate);
    const weekTitle = document.getElementById('weekTitle');
    if (weekTitle) {
        weekTitle.textContent = `${year}年${month + 1}月第${weekNum}周`;
    }
    
    // 更新日期格子
    const dayCells = document.querySelectorAll('.day-cell');
    const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    
    dayCells.forEach((cell, index) => {
        const cellDate = new Date(weekStart);
        cellDate.setDate(weekStart.getDate() + index);
        
        const cellMonth = cellDate.getMonth() + 1;
        const cellDay = cellDate.getDate();
        
        const dayNameEl = cell.querySelector('.day-name');
        const dayDateEl = cell.querySelector('.day-date');
        
        if (dayNameEl) dayNameEl.textContent = weekDays[index];
        if (dayDateEl) dayDateEl.textContent = `${cellMonth}/${cellDay}`;
        cell.setAttribute('data-date', cellDate.toISOString().split('T')[0]);
        
        // 检查是否是当前选中日期
        cell.classList.remove('active');
        if (cellDate.toDateString() === currentDate.toDateString()) {
            cell.classList.add('active');
        }
        
        // 点击事件
        cell.onclick = () => {
            currentDate = new Date(cellDate);
            updateCalendar();
        };
    });
}

// 计算周数
function getWeekNumber(date) {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const dayNum = d.getUTCDay() || 7;
    d.setUTCDate(d.getUTCDate() + 4 - dayNum);
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
}

function changeWeek(direction) {
    currentDate.setDate(currentDate.getDate() + (direction * 7));
    updateCalendar();
}

function goToToday() {
    currentDate = API.utils.getBeijingTime();
    updateCalendar();
}

// 关闭横幅
function closeBanner() {
    const banner = document.getElementById('notificationBanner');
    if (banner) {
        banner.style.display = 'none';
    }
}

// ============================================
// 更多功能页面
// ============================================
function showMorePage() {
    const morePage = document.getElementById('morePage');
    if (morePage) {
        morePage.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function hideMorePage() {
    const morePage = document.getElementById('morePage');
    if (morePage) {
        morePage.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// ============================================
// 帮助页面
// ============================================
function showHelpPage() {
    const helpPage = document.getElementById('helpPage');
    if (helpPage) {
        helpPage.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function hideHelpPage() {
    const helpPage = document.getElementById('helpPage');
    if (helpPage) {
        helpPage.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// ============================================
// 积分成就页面
// ============================================
async function showPointsPage() {
    const pointsPage = document.getElementById('pointsPage');
    if (pointsPage) {
        pointsPage.classList.add('active');
        document.body.style.overflow = 'hidden';
        await loadUserPointsData();
        await renderWishList();
    }
}

function hidePointsPage() {
    const pointsPage = document.getElementById('pointsPage');
    if (pointsPage) {
        pointsPage.classList.remove('active');
        document.body.style.overflow = '';
    }
}

async function loadUserPointsData() {
    try {
        const response = await API.points.getOverview();
        const data = response.data;
        
        const balanceEl = document.getElementById('pointsBalance');
        const weekEl = document.getElementById('pointsWeek');
        const monthEl = document.getElementById('pointsMonth');
        
        if (balanceEl) balanceEl.textContent = data.balance || 0;
        if (weekEl) weekEl.textContent = data.week_earned || 0;
        if (monthEl) monthEl.textContent = data.month_earned || 0;
        
        if (currentUser) {
            currentUser.total_points = data.balance || 0;
        }
    } catch (error) {
        console.error('加载积分数据失败:', error);
    }
}

// ============================================
// 愿望清单
// ============================================
async function renderWishList() {
    const container = document.getElementById('wishesList');
    if (!container) return;
    
    try {
        const response = await API.points.getWishes();
        const wishes = response.data || [];
        const sortType = document.getElementById('wishSort')?.value || 'default';
        
        // 排序
        if (sortType === 'cost_asc') wishes.sort((a, b) => a.cost - b.cost);
        else if (sortType === 'cost_desc') wishes.sort((a, b) => b.cost - a.cost);
        else if (sortType === 'created_desc') wishes.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        
        if (wishes.length === 0) {
            container.innerHTML = `
                <div class="wish-empty-state">
                    <div class="wish-empty-icon">🎁</div>
                    <h4 class="wish-empty-title">还没有添加愿望</h4>
                    <p class="wish-empty-desc">点击"添加愿望"按钮，添加你想要的奖励吧！</p>
                    <button class="btn-add-first-wish" onclick="showAddWishModal()">
                        <span style="margin-right: 4px;">+</span> 添加第一个愿望
                    </button>
                </div>
            `;
            return;
        }
        
        const balance = currentUser?.total_points || 0;
        
        container.innerHTML = wishes.map(wish => `
            <div class="wish-item ${wish.status === 'redeemed' ? 'redeemed' : ''}">
                <div class="wish-icon">${wish.status === 'redeemed' ? '✅' : '🎁'}</div>
                <div class="wish-info">
                    <div class="wish-name">${escapeHtml(wish.title)} ${wish.status === 'redeemed' ? '<span class="redeemed-badge">已兑换</span>' : ''}</div>
                    <div class="wish-desc">${escapeHtml(wish.description || '')}</div>
                </div>
                <div class="wish-cost">${wish.cost}⭐</div>
                <div class="wish-actions">
                    ${wish.status !== 'redeemed' ? `
                        <button class="btn-redeem-wish" ${balance < wish.cost ? 'disabled' : ''} onclick="redeemWish(${wish.id})">兑换</button>
                        <button class="btn-edit-wish" onclick="editWish(${wish.id})">编辑</button>
                    ` : ''}
                    <button class="btn-delete-wish" onclick="deleteWish(${wish.id})">删除</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载愿望清单失败:', error);
        container.innerHTML = '<p style="text-align:center;color:#EF4444;padding:20px;">加载失败，请重试</p>';
    }
}

function showAddWishModal() {
    document.getElementById('wishModalTitle').textContent = '添加愿望';
    document.getElementById('wishEditId').value = '';
    document.getElementById('wishTitle').value = '';
    document.getElementById('wishDesc').value = '';
    document.getElementById('wishCost').value = 10;
    document.getElementById('wishModal').classList.add('active');
}

function closeWishModal() {
    document.getElementById('wishModal').classList.remove('active');
}

function editWish(id) {
    // 从当前渲染的列表中找
    // 由于我们每次都重新请求，这里简单处理：先查找DOM或者重新请求
    API.points.getWishes().then(res => {
        const wish = res.data.find(w => w.id === id);
        if (!wish) return;
        document.getElementById('wishModalTitle').textContent = '编辑愿望';
        document.getElementById('wishEditId').value = wish.id;
        document.getElementById('wishTitle').value = wish.title;
        document.getElementById('wishDesc').value = wish.description || '';
        document.getElementById('wishCost').value = wish.cost;
        document.getElementById('wishModal').classList.add('active');
    });
}

async function saveWish() {
    const id = document.getElementById('wishEditId').value;
    const title = document.getElementById('wishTitle').value.trim();
    const description = document.getElementById('wishDesc').value.trim();
    const cost = parseInt(document.getElementById('wishCost').value, 10);
    
    if (!title) {
        showToast('请输入愿望名称', 'error');
        return;
    }
    if (!cost || cost < 1) {
        showToast('所需星星至少为1', 'error');
        return;
    }
    
    try {
        if (id) {
            await API.points.updateWish(id, { title, description, cost });
            showToast('愿望更新成功');
        } else {
            await API.points.createWish({ title, description, cost });
            showToast('愿望添加成功');
        }
        closeWishModal();
        await renderWishList();
    } catch (error) {
        showToast(error.message || '保存失败', 'error');
    }
}

async function deleteWish(id) {
    if (!confirm('确定要删除这个愿望吗？')) return;
    try {
        await API.points.deleteWish(id);
        showToast('愿望已删除');
        await renderWishList();
    } catch (error) {
        showToast(error.message || '删除失败', 'error');
    }
}

async function redeemWish(id) {
    try {
        await API.points.redeemWish(id);
        showToast('愿望兑换成功！');
        await loadUserPointsData();
        await renderWishList();
        await loadUserInfo();
    } catch (error) {
        showToast(error.message || '兑换失败', 'error');
    }
}

// ============================================
// 成就系统
// ============================================
async function showAchievementsModal() {
    document.getElementById('achievementsModal').classList.add('active');
    await renderAchievements();
}

function closeAchievementsModal() {
    document.getElementById('achievementsModal').classList.remove('active');
}

async function renderAchievements() {
    const container = document.getElementById('achievementsGrid');
    if (!container) return;
    
    try {
        const response = await API.points.getAchievements();
        const achievements = response.data || [];
        
        container.innerHTML = achievements.map(ach => {
            const isLocked = !ach.unlocked;
            const isClaimed = ach.claimed;
            return `
                <div class="achievement-item ${isLocked ? 'locked' : (isClaimed ? 'claimed' : 'unlocked')}">
                    <div class="achievement-icon">${ach.icon || '🏅'}</div>
                    <div class="achievement-name">${escapeHtml(ach.name)}</div>
                    <div class="achievement-desc">${escapeHtml(ach.description)}</div>
                    <div class="achievement-reward">+${ach.reward_points}⭐</div>
                    ${!isLocked && !isClaimed ? `
                        <button class="btn-claim-achievement" onclick="claimAchievement(${ach.id})">领取奖励</button>
                    ` : `
                        <div class="achievement-status">${isClaimed ? '已领取' : '未解锁'}</div>
                    `}
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('加载成就失败:', error);
        container.innerHTML = '<p style="text-align:center;color:#EF4444;">加载失败</p>';
    }
}

async function claimAchievement(id) {
    try {
        const res = await API.points.claimAchievement(id);
        showToast(res.message || '领取成功！');
        await renderAchievements();
        await loadUserPointsData();
        await loadUserInfo();
    } catch (error) {
        showToast(error.message || '领取失败', 'error');
    }
}

// ============================================
// 积分历史
// ============================================
async function showHistoryModal() {
    document.getElementById('historyModal').classList.add('active');
    await renderHistory();
}

function closeHistoryModal() {
    document.getElementById('historyModal').classList.remove('active');
}

async function renderHistory() {
    const container = document.getElementById('historyList');
    const emptyEl = document.getElementById('historyEmpty');
    if (!container) return;
    
    try {
        const response = await API.points.getHistory({ page: 1, pageSize: 50 });
        const list = response.data.list || [];
        
        if (list.length === 0) {
            container.innerHTML = '';
            emptyEl.style.display = 'block';
            return;
        }
        
        emptyEl.style.display = 'none';
        container.innerHTML = list.map(item => `
            <div class="history-item">
                <div class="history-info">
                    <div class="history-desc">${escapeHtml(item.description || item.source || '')}</div>
                    <div class="history-date">${new Date(item.created_at).toLocaleString('zh-CN')}</div>
                </div>
                <div class="history-points ${item.type === 'earn' ? 'earn' : 'spend'}">
                    ${item.type === 'earn' ? '+' : ''}${item.points}⭐
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载历史失败:', error);
        container.innerHTML = '<p style="text-align:center;color:#EF4444;">加载失败</p>';
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function redeemCode() {
    // 创建兑换码输入模态框
    let redeemModal = document.getElementById('redeemCodeModal');
    
    if (!redeemModal) {
        redeemModal = document.createElement('div');
        redeemModal.id = 'redeemCodeModal';
        redeemModal.className = 'modal-overlay';
        redeemModal.innerHTML = `
            <div class="modal-container" style="max-width: 400px;">
                <div class="modal-header">
                    <div class="modal-title-section">
                        <h3 class="modal-title">兑换会员码</h3>
                        <p class="modal-subtitle">输入您的会员兑换码以解锁高级功能</p>
                    </div>
                    <button class="modal-close" onclick="closeRedeemCodeModal()">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label class="form-label">兑换码</label>
                        <input type="text" class="form-input" id="redeemCodeInput" placeholder="请输入兑换码">
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-create" onclick="submitRedeemCode()">兑换</button>
                    <button class="btn btn-cancel" onclick="closeRedeemCodeModal()">取消</button>
                </div>
            </div>
        `;
        document.body.appendChild(redeemModal);
    }
    
    redeemModal.classList.add('active');
    document.getElementById('redeemCodeInput').value = '';
    document.getElementById('redeemCodeInput').focus();
}

function closeRedeemCodeModal() {
    const modal = document.getElementById('redeemCodeModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

async function submitRedeemCode() {
    const codeInput = document.getElementById('redeemCodeInput');
    const code = codeInput ? codeInput.value.trim() : '';
    
    if (!code) {
        showToast('请输入兑换码', 'error');
        return;
    }
    
    try {
        // 调用API兑换会员码
        const response = await fetch('/api/users/redeem', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + API.utils.getToken()
            },
            body: JSON.stringify({ code: code })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('兑换成功！会员已激活');
            closeRedeemCodeModal();
            // 刷新用户数据
            await loadUserInfo();
        } else {
            showToast(result.message || '兑换码无效', 'error');
        }
    } catch (error) {
        console.error('兑换失败:', error);
        showToast('兑换失败，请稍后重试', 'error');
    }
}

// ============================================
// 习惯管理视图
// ============================================
function showHabitManageView() {
    // 创建习惯管理视图容器
    let manageView = document.getElementById('habitManageView');
    
    if (!manageView) {
        manageView = document.createElement('div');
        manageView.id = 'habitManageView';
        manageView.className = 'more-page';
        manageView.innerHTML = `
            <header class="more-header" style="background: linear-gradient(135deg, #4A7BF7 0%, #3D6BE6 100%);">
                <div class="more-header-content">
                    <button class="back-btn-white" onclick="hideHabitManageView()">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="15 18 9 12 15 6"></polyline>
                        </svg>
                    </button>
                    <div class="more-titles">
                        <h1 class="more-main-title">习惯管理</h1>
                        <p class="more-sub-title">管理您的所有行为习惯</p>
                    </div>
                </div>
            </header>
            <div class="more-content">
                <div class="habit-manage-actions" style="display: flex; gap: 12px; margin-bottom: 20px;">
                    <button class="btn btn-primary" onclick="openHabitModal(); hideHabitManageView();">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                            <line x1="12" y1="5" x2="12" y2="19"></line>
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                        新建习惯
                    </button>
                    <button class="btn btn-batch" onclick="showBatchEditModal()">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                        批量编辑
                    </button>
                </div>
                <div id="habitManageList" class="habit-manage-list">
                    <!-- 习惯列表将在这里渲染 -->
                </div>
            </div>
        `;
        document.body.appendChild(manageView);
    }
    
    // 加载习惯列表
    renderHabitManageList();
    
    manageView.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function hideHabitManageView() {
    const manageView = document.getElementById('habitManageView');
    if (manageView) {
        manageView.classList.remove('active');
        document.body.style.overflow = '';
    }
}

async function renderHabitManageList() {
    const listContainer = document.getElementById('habitManageList');
    if (!listContainer) return;
    
    try {
        const response = await API.habits.getList({ status: 'active' });
        const habitList = response.data.list || [];
        
        if (habitList.length === 0) {
            listContainer.innerHTML = `
                <div class="habit-empty-state" style="padding: 40px; text-align: center;">
                    <p style="color: #6B7280;">暂无习惯，点击"新建习惯"开始创建</p>
                </div>
            `;
            return;
        }
        
        listContainer.innerHTML = habitList.map(habit => `
            <div class="habit-manage-item" data-id="${habit.id}" style="
                background: white;
                border-radius: 12px;
                padding: 16px 20px;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                gap: 16px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            ">
                <div class="habit-icon" style="
                    width: 48px;
                    height: 48px;
                    background: ${habit.color || '#4A7BF7'};
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    flex-shrink: 0;
                ">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 24px; height: 24px;">
                        ${getIconSvg(habit.icon)}
                    </svg>
                </div>
                <div class="habit-info" style="flex: 1;">
                    <h4 style="font-size: 16px; font-weight: 600; color: #1F2937; margin-bottom: 4px;">${habit.name}</h4>
                    <p style="font-size: 13px; color: #6B7280;">${getHabitTypeText(habit.habit_type)} · ${habit.points > 0 ? '+' : ''}${habit.points}⭐</p>
                </div>
                <div class="habit-actions" style="display: flex; gap: 8px;">
                    <button class="nav-btn" onclick="editHabit(${habit.id})" style="padding: 8px 16px; font-size: 13px;">
                        编辑
                    </button>
                    <button class="nav-btn" onclick="deleteHabit(${habit.id})" style="padding: 8px 16px; font-size: 13px; color: #EF4444;">
                        删除
                    </button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('加载习惯管理列表失败:', error);
        listContainer.innerHTML = '<p style="text-align: center; color: #EF4444;">加载失败，请重试</p>';
    }
}

// ============================================
// 个人资料编辑
// ============================================
function editProfile() {
    // 关闭用户下拉菜单
    const userDropdown = document.getElementById('userDropdown');
    if (userDropdown) {
        userDropdown.classList.remove('show');
    }
    
    // 创建个人资料编辑模态框
    let profileModal = document.getElementById('profileModal');
    
    if (!profileModal) {
        profileModal = document.createElement('div');
        profileModal.id = 'profileModal';
        profileModal.className = 'modal-overlay';
        document.body.appendChild(profileModal);
    }
    
    const nickname = currentUser?.nickname || '';
    const username = currentUser?.username || '';
    
    profileModal.innerHTML = `
        <div class="modal-container" style="max-width: 450px;">
            <div class="modal-header">
                <div class="modal-title-section">
                    <h3 class="modal-title">编辑个人资料</h3>
                    <p class="modal-subtitle">修改您的个人信息</p>
                </div>
                <button class="modal-close" onclick="closeProfileModal()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label">昵称</label>
                    <input type="text" class="form-input" id="profileNickname" value="${nickname}" placeholder="请输入昵称">
                </div>
                <div class="form-group">
                    <label class="form-label">用户名</label>
                    <input type="text" class="form-input" value="${username}" disabled style="background: #F3F4F6; color: #9CA3AF;">
                    <p class="form-hint">用户名不可修改</p>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-create" onclick="saveProfile()">保存</button>
                <button class="btn btn-cancel" onclick="closeProfileModal()">取消</button>
            </div>
        </div>
    `;
    
    profileModal.classList.add('active');
    document.getElementById('profileNickname').focus();
}

function closeProfileModal() {
    const modal = document.getElementById('profileModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

async function saveProfile() {
    const nickname = document.getElementById('profileNickname').value.trim();
    
    if (!nickname) {
        showToast('请输入昵称', 'error');
        return;
    }
    
    try {
        await API.auth.updateProfile({ nickname });
        
        // 更新本地数据
        if (currentUser) {
            currentUser.nickname = nickname;
        }
        
        // 更新UI
        document.getElementById('userName').textContent = nickname;
        document.getElementById('userAvatar').textContent = nickname.charAt(0);
        
        showToast('个人资料已更新');
        closeProfileModal();
        
    } catch (error) {
        showToast(error.message || '保存失败', 'error');
    }
}

// ============================================
// 积分商城
// ============================================
function showRedeemModal() {
    // 创建积分商城模态框
    let shopModal = document.getElementById('redeemShopModal');
    
    if (!shopModal) {
        shopModal = document.createElement('div');
        shopModal.id = 'redeemShopModal';
        shopModal.className = 'modal-overlay';
        document.body.appendChild(shopModal);
    }
    
    // 商品数据
    const shopItems = [
        { id: 1, name: '额外存储空间', desc: '增加100MB存储空间', cost: 50, icon: '💾' },
        { id: 2, name: '自定义主题', desc: '解锁专属主题配色', cost: 100, icon: '🎨' },
        { id: 3, name: '高级统计报告', desc: '获取详细数据分析', cost: 150, icon: '📊' },
        { id: 4, name: '会员体验卡', desc: '3天高级会员体验', cost: 200, icon: '⭐' },
        { id: 5, name: '虚拟宠物食物', desc: '喂养您的电子宠物', cost: 20, icon: '🍎' },
        { id: 6, name: '专属头像框', desc: '炫酷头像框装饰', cost: 80, icon: '👤' }
    ];
    
    const userPoints = currentUser?.total_points || 0;
    
    shopModal.innerHTML = `
        <div class="modal-container" style="max-width: 500px; max-height: 80vh; overflow-y: auto;">
            <div class="modal-header">
                <div class="modal-title-section">
                    <h3 class="modal-title">积分商城</h3>
                    <p class="modal-subtitle">使用星星积分兑换奖励 · 当前积分: <strong>${userPoints}⭐</strong></p>
                </div>
                <button class="modal-close" onclick="closeRedeemShopModal()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="modal-body">
                <div class="shop-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
                    ${shopItems.map(item => `
                        <div class="shop-item" style="
                            background: #F9FAFB;
                            border-radius: 12px;
                            padding: 16px;
                            text-align: center;
                            border: 2px solid ${userPoints >= item.cost ? '#4A7BF7' : '#E5E7EB'};
                            opacity: ${userPoints >= item.cost ? 1 : 0.6};
                        ">
                            <div style="font-size: 36px; margin-bottom: 8px;">${item.icon}</div>
                            <h4 style="font-size: 15px; font-weight: 600; color: #1F2937; margin-bottom: 4px;">${item.name}</h4>
                            <p style="font-size: 12px; color: #6B7280; margin-bottom: 12px;">${item.desc}</p>
                            <button 
                                class="btn ${userPoints >= item.cost ? 'btn-primary' : 'btn-cancel'}" 
                                style="width: 100%; justify-content: center;"
                                onclick="${userPoints >= item.cost ? `redeemItem(${item.id})` : ''}"
                                ${userPoints < item.cost ? 'disabled' : ''}
                            >
                                ${item.cost}⭐ 兑换
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
    
    shopModal.classList.add('active');
}

function closeRedeemShopModal() {
    const modal = document.getElementById('redeemShopModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

async function redeemItem(itemId) {
    const shopItems = [
        { id: 1, name: '额外存储空间', cost: 50 },
        { id: 2, name: '自定义主题', cost: 100 },
        { id: 3, name: '高级统计报告', cost: 150 },
        { id: 4, name: '会员体验卡', cost: 200 },
        { id: 5, name: '虚拟宠物食物', cost: 20 },
        { id: 6, name: '专属头像框', cost: 80 }
    ];
    
    const item = shopItems.find(i => i.id === itemId);
    if (!item) return;
    
    if (!confirm(`确定要花费 ${item.cost}⭐ 兑换「${item.name}」吗？`)) {
        return;
    }
    
    try {
        // 调用API进行兑换
        const response = await fetch('/api/points/redeem', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + API.utils.getToken()
            },
            body: JSON.stringify({ item_id: itemId, cost: item.cost })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(`成功兑换「${item.name}」！`);
            
            // 更新用户积分
            if (currentUser) {
                currentUser.total_points = (currentUser.total_points || 0) - item.cost;
            }
            
            // 刷新商城显示
            closeRedeemShopModal();
            showRedeemModal();
            
            // 刷新用户数据
            await loadUserInfo();
        } else {
            showToast(result.message || '兑换失败', 'error');
        }
    } catch (error) {
        console.error('兑换失败:', error);
        showToast('兑换失败，请稍后重试', 'error');
    }
}

// 批量编辑模态框（习惯管理中使用）
function showBatchEditModal() {
    showToast('批量编辑功能开发中...');
}


// ============================================
// 电子宠物系统
// ============================================
let currentPet = null;

const PET_EMOJIS = {
    cat: '🐱',
    dog: '🐶',
    rabbit: '🐰',
    bird: '🦜'
};

// 初始化宠物系统
function initPetSystem() {
    // 不需要每分钟更新，页面打开时从后端获取即可
}

// 显示电子宠物页面
async function showPetPage() {
    let page = document.getElementById('petPage');
    if (!page) {
        page = createPetPage();
        document.body.appendChild(page);
    }
    page.style.display = 'block';
    page.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // 加载宠物数据
    await loadPetData();
}

async function loadPetData() {
    try {
        const res = await API.points.getPet();
        currentPet = res.data;
        renderPetPage();
    } catch (error) {
        console.error('加载宠物失败:', error);
    }
}

function createPetPage() {
    const page = document.createElement('div');
    page.id = 'petPage';
    page.className = 'page-overlay';
    page.style.cssText = `
        position: fixed;
        top: 0;
        left: 220px;
        right: 0;
        bottom: 0;
        background: linear-gradient(180deg, #F5F7FA 0%, #F0F4F8 100%);
        z-index: 200;
        display: none;
        overflow-y: auto;
    `;
    
    page.innerHTML = `
        <div class="pet-page-container" id="petPageContainer">
            <!-- 内容由 renderPetPage 动态填充 -->
        </div>
        <style>
            @keyframes bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-10px); }
            }
        </style>
    `;
    return page;
}

function renderPetPage() {
    const container = document.getElementById('petPageContainer');
    if (!container) return;
    
    if (!currentPet) {
        // 领养页面
        container.innerHTML = `
            <header style="background: linear-gradient(135deg, #F59E0B 0%, #F97316 50%, #EA580C 100%); padding: 30px 40px; position: relative; overflow: hidden;">
                <div style="position: relative; z-index: 1;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                        <button onclick="hidePetPage()" style="background: rgba(255,255,255,0.2); border: none; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; color: white; flex-shrink: 0;">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="15 18 9 12 15 6"></polyline>
                            </svg>
                        </button>
                        <h1 style="color: white; font-size: 24px; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">领养电子宠物</h1>
                    </div>
                    <p style="color: rgba(255,255,255,0.9); font-size: 14px; margin-left: 48px;">选择一只小伙伴，陪伴你一起学习成长</p>
                </div>
            </header>
            <div style="padding: 20px; max-width: 600px; margin: 0 auto;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="font-size: 80px; margin-bottom: 16px;">🐾</div>
                    <h2 style="font-size: 20px; font-weight: 600; color: #1F2937; margin-bottom: 8px;">你还没有宠物</h2>
                    <p style="color: #6B7280; font-size: 14px;">领养一只电子宠物，用星星照顾它一起成长吧！</p>
                </div>
                
                <div style="background: white; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div class="form-group" style="margin-bottom: 16px;">
                        <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px;">宠物名字</label>
                        <input type="text" id="adoptPetName" class="form-input" placeholder="例如：小星星" style="width: 100%;">
                    </div>
                    <div class="form-group">
                        <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 12px;">选择宠物</label>
                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;">
                            <div class="pet-select-item" data-type="cat" onclick="selectPetType('cat')" style="text-align: center; padding: 16px; border: 2px solid #F59E0B; border-radius: 12px; cursor: pointer; background: #FFFBEB;">
                                <div style="font-size: 36px; margin-bottom: 4px;">🐱</div>
                                <div style="font-size: 13px; color: #374151;">小猫</div>
                            </div>
                            <div class="pet-select-item" data-type="dog" onclick="selectPetType('dog')" style="text-align: center; padding: 16px; border: 2px solid #E5E7EB; border-radius: 12px; cursor: pointer;">
                                <div style="font-size: 36px; margin-bottom: 4px;">🐶</div>
                                <div style="font-size: 13px; color: #374151;">小狗</div>
                            </div>
                            <div class="pet-select-item" data-type="rabbit" onclick="selectPetType('rabbit')" style="text-align: center; padding: 16px; border: 2px solid #E5E7EB; border-radius: 12px; cursor: pointer;">
                                <div style="font-size: 36px; margin-bottom: 4px;">🐰</div>
                                <div style="font-size: 13px; color: #374151;">小兔</div>
                            </div>
                            <div class="pet-select-item" data-type="bird" onclick="selectPetType('bird')" style="text-align: center; padding: 16px; border: 2px solid #E5E7EB; border-radius: 12px; cursor: pointer;">
                                <div style="font-size: 36px; margin-bottom: 4px;">🦜</div>
                                <div style="font-size: 13px; color: #374151;">小鸟</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <button onclick="adoptPet()" style="width: 100%; padding: 16px; background: linear-gradient(135deg, #F59E0B, #D97706); color: white; border: none; border-radius: 12px; font-size: 16px; font-weight: 500; cursor: pointer;">
                    立即领养
                </button>
            </div>
        `;
        window.selectedPetType = 'cat';
        return;
    }
    
    const emoji = PET_EMOJIS[currentPet.type] || '🐱';
    const isSleeping = currentPet.is_sleeping;
    
    container.innerHTML = `
        <header style="background: linear-gradient(135deg, #F59E0B 0%, #F97316 50%, #EA580C 100%); padding: 30px 40px; position: relative; overflow: hidden;">
            <div style="position: relative; z-index: 1;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <button onclick="hidePetPage()" style="background: rgba(255,255,255,0.2); border: none; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; color: white; flex-shrink: 0;">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="15 18 9 12 15 6"></polyline>
                        </svg>
                    </button>
                    <h1 style="color: white; font-size: 24px; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">我的电子宠物</h1>
                </div>
                <p style="color: rgba(255,255,255,0.9); font-size: 14px; margin-left: 48px;">照顾你的宠物，让它健康成长</p>
            </div>
        </header>
        
        <div style="padding: 20px; max-width: 600px; margin: 0 auto;">
            <div style="text-align: center; margin-bottom: 30px;">
                <div id="petCharacter" style="font-size: 100px; margin-bottom: 16px; animation: ${isSleeping ? 'none' : 'bounce 2s infinite'};">${isSleeping ? '😴' : emoji}</div>
                <div style="display: inline-block; background: #FEF3C7; color: #92400E; padding: 4px 16px; border-radius: 20px; font-size: 14px; font-weight: 500; margin-bottom: 8px;">
                    Lv.<span id="petLevel">${currentPet.level}</span>
                </div>
                <h2 id="petName" style="font-size: 24px; font-weight: 600; color: #1F2937; margin-bottom: 12px;">${escapeHtml(currentPet.name)}</h2>
                
                <div style="background: #E5E7EB; height: 12px; border-radius: 6px; overflow: hidden; max-width: 300px; margin: 0 auto 8px;">
                    <div id="expFill" style="background: linear-gradient(90deg, #F59E0B, #F97316); height: 100%; width: ${(currentPet.exp / currentPet.max_exp * 100)}%; transition: width 0.3s;"></div>
                </div>
                <p style="font-size: 12px; color: #6B7280;">EXP: <span id="petExp">${currentPet.exp}</span> / <span id="petMaxExp">${currentPet.max_exp}</span></p>
            </div>
            
            <div style="background: white; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <span style="font-size: 14px; color: #374151;">🍖 饱食度</span>
                        <span style="font-size: 14px; color: #6B7280;">${Math.round(currentPet.hunger)}%</span>
                    </div>
                    <div style="background: #E5E7EB; height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="background: #22C55E; height: 100%; width: ${currentPet.hunger}%; transition: width 0.3s;"></div>
                    </div>
                </div>
                <div style="margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <span style="font-size: 14px; color: #374151;">😊 心情</span>
                        <span style="font-size: 14px; color: #6B7280;">${Math.round(currentPet.happiness)}%</span>
                    </div>
                    <div style="background: #E5E7EB; height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="background: #F59E0B; height: 100%; width: ${currentPet.happiness}%; transition: width 0.3s;"></div>
                    </div>
                </div>
                <div style="margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <span style="font-size: 14px; color: #374151;">⚡ 精力</span>
                        <span style="font-size: 14px; color: #6B7280;">${Math.round(currentPet.energy)}%</span>
                    </div>
                    <div style="background: #E5E7EB; height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="background: #3B82F6; height: 100%; width: ${currentPet.energy}%; transition: width 0.3s;"></div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <span style="font-size: 14px; color: #374151;">✨ 清洁</span>
                        <span style="font-size: 14px; color: #6B7280;">${Math.round(currentPet.cleanliness)}%</span>
                    </div>
                    <div style="background: #E5E7EB; height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="background: #8B5CF6; height: 100%; width: ${currentPet.cleanliness}%; transition: width 0.3s;"></div>
                    </div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 20px;">
                <button onclick="feedPet()" style="background: linear-gradient(135deg, #22C55E, #16A34A); color: white; border: none; padding: 16px; border-radius: 12px; font-size: 16px; font-weight: 500; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <span>🍖</span> 喂食 (-1⭐)
                </button>
                <button onclick="playWithPet()" style="background: linear-gradient(135deg, #F59E0B, #F97316); color: white; border: none; padding: 16px; border-radius: 12px; font-size: 16px; font-weight: 500; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <span>🎮</span> 玩耍
                </button>
                <button onclick="cleanPet()" style="background: linear-gradient(135deg, #8B5CF6, #7C3AED); color: white; border: none; padding: 16px; border-radius: 12px; font-size: 16px; font-weight: 500; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <span>🛁</span> 清洁
                </button>
                <button onclick="toggleSleep()" style="background: linear-gradient(135deg, #3B82F6, #2563EB); color: white; border: none; padding: 16px; border-radius: 12px; font-size: 16px; font-weight: 500; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <span>${isSleeping ? '☀️' : '💤'}</span> ${isSleeping ? '醒来' : '睡觉'}
                </button>
            </div>
            
            <div style="background: #FEF3C7; border-radius: 12px; padding: 16px; color: #92400E; font-size: 14px; line-height: 1.6;">
                <p style="margin-bottom: 8px;"><strong>💡 小贴士：</strong></p>
                <ul style="margin-left: 16px;">
                    <li>每天记得喂食，保持宠物饱食度</li>
                    <li>和宠物玩耍可以提升心情</li>
                    <li>宠物升级可以获得星星奖励</li>
                    <li>宠物睡觉时精力恢复更快</li>
                </ul>
            </div>
        </div>
    `;
}

function selectPetType(type) {
    window.selectedPetType = type;
    document.querySelectorAll('.pet-select-item').forEach(el => {
        if (el.dataset.type === type) {
            el.style.borderColor = '#F59E0B';
            el.style.background = '#FFFBEB';
        } else {
            el.style.borderColor = '#E5E7EB';
            el.style.background = 'white';
        }
    });
}

async function adoptPet() {
    const name = document.getElementById('adoptPetName')?.value.trim();
    if (!name) {
        showToast('请给宠物取个名字', 'error');
        return;
    }
    try {
        await API.points.adoptPet({ name, type: window.selectedPetType || 'cat' });
        showToast('领养成功！');
        await loadPetData();
        await loadUserInfo();
    } catch (error) {
        showToast(error.message || '领养失败', 'error');
    }
}

async function feedPet() {
    try {
        const res = await API.points.feedPet();
        showToast(res.message || '喂食成功！');
        currentPet = res.data.pet;
        if (res.data.level_up) {
            showToast(`🎉 宠物升级到 Lv.${res.data.new_level}！奖励${res.data.bonus}⭐`, 'success');
        }
        renderPetPage();
        await loadUserInfo();
    } catch (error) {
        showToast(error.message || '喂食失败', 'error');
    }
}

async function playWithPet() {
    try {
        const res = await API.points.playWithPet();
        showToast(res.message || '玩耍成功！');
        currentPet = res.data.pet;
        if (res.data.level_up) {
            showToast(`🎉 宠物升级到 Lv.${res.data.new_level}！奖励${res.data.bonus}⭐`, 'success');
        }
        renderPetPage();
        await loadUserInfo();
    } catch (error) {
        showToast(error.message || '玩耍失败', 'error');
    }
}

async function cleanPet() {
    try {
        const res = await API.points.cleanPet();
        showToast(res.message || '清洁成功！');
        currentPet = res.data.pet;
        if (res.data.level_up) {
            showToast(`🎉 宠物升级到 Lv.${res.data.new_level}！奖励${res.data.bonus}⭐`, 'success');
        }
        renderPetPage();
        await loadUserInfo();
    } catch (error) {
        showToast(error.message || '清洁失败', 'error');
    }
}

async function toggleSleep() {
    try {
        const res = await API.points.toggleSleep();
        showToast(res.message || '操作成功');
        currentPet = res.data;
        renderPetPage();
    } catch (error) {
        showToast(error.message || '操作失败', 'error');
    }
}

function hidePetPage() {
    const page = document.getElementById('petPage');
    if (page) {
        page.style.display = 'none';
        page.classList.remove('active');
    }
    document.body.style.overflow = '';
}

// ============================================
// 习惯日历更新
// ============================================
function updateHabitCalendar() {
    // 使用习惯当前的日期
    const habitCurrentDate = currentDate;
    const year = habitCurrentDate.getFullYear();
    const month = habitCurrentDate.getMonth();
    const date = habitCurrentDate.getDate();
    const day = habitCurrentDate.getDay();
    
    // 计算当前周的起始日期（周一）
    const weekStart = new Date(habitCurrentDate);
    const dayOfWeek = day === 0 ? 6 : day - 1;
    weekStart.setDate(date - dayOfWeek);
    
    // 计算周数
    const weekNum = getWeekNumber(habitCurrentDate);
    const weekTitle = document.getElementById('habitWeekTitle');
    if (weekTitle) {
        weekTitle.textContent = `${year}年${month + 1}月第${weekNum}周`;
    }
    
    // 更新习惯日历格子
    const dayCells = document.querySelectorAll('.habit-week-calendar .day-cell');
    const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    
    dayCells.forEach((cell, index) => {
        const cellDate = new Date(weekStart);
        cellDate.setDate(weekStart.getDate() + index);
        
        const cellMonth = cellDate.getMonth() + 1;
        const cellDay = cellDate.getDate();
        const dateStr = cellDate.toISOString().split('T')[0];
        
        const dayNameEl = cell.querySelector('.day-name');
        const dayDateEl = cell.querySelector('.day-date');
        const dayStatusEl = cell.querySelector('.day-status');
        
        if (dayNameEl) dayNameEl.textContent = weekDays[index];
        if (dayDateEl) dayDateEl.textContent = `${cellMonth}/${cellDay}`;
        cell.setAttribute('data-date', dateStr);
        
        // 检查是否是今天
        const today = API.utils.getBeijingDateStr();
        cell.classList.remove('active', 'today');
        if (dateStr === today) {
            cell.classList.add('today');
        }
        if (cellDate.toDateString() === habitCurrentDate.toDateString()) {
            cell.classList.add('active');
        }
        
        // 更新打卡状态显示
        if (dayStatusEl) {
            const hasCheckin = checkins.some(c => c.checkin_date === dateStr && c.status === 'completed');
            dayStatusEl.className = 'day-status' + (hasCheckin ? ' completed' : '');
        }
        
        // 点击事件
        cell.onclick = () => {
            currentDate = new Date(cellDate);
            updateHabitCalendar();
        };
    });
}

function changeHabitWeek(direction) {
    currentDate.setDate(currentDate.getDate() + (direction * 7));
    updateHabitCalendar();
}

function goToHabitToday() {
    currentDate = API.utils.getBeijingTime();
    updateHabitCalendar();
}
