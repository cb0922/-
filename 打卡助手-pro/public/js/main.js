// ============================================
// 小打卡 Pro - 主JavaScript文件
// ============================================

// 全局状态
let currentUser = null;
let habits = [];
let currentDate = API.utils.getBeijingTime();

// ============================================
// 初始化
// ============================================
document.addEventListener('DOMContentLoaded', async function() {
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
    window.location.href = '/dashboard';
}

function goToLogs() {
    window.location.href = '/logs';
}

function editProfile() {
    showToast('个人资料编辑功能开发中...');
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
        
    } catch (error) {
        console.error('加载习惯列表失败:', error);
    }
}

function renderHabitList() {
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
                    <span class="habit-points">+${habit.points}⭐</span>
                </div>
                <button class="btn-checkin" onclick="checkinHabit(${habit.id})" ${isCheckedInToday(habit.id) ? 'disabled' : ''}>
                    ${isCheckedInToday(habit.id) ? '已打卡' : '打卡'}
                </button>
            </div>
        </div>
    `).join('');
}

function getIconSvg(icon) {
    const icons = {
        star: '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>',
        book: '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>',
        sun: '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>',
        activity: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>',
        moon: '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>',
        heart: '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>',
        default: '<circle cx="12" cy="12" r="10"></circle><path d="M12 8v4l3 3"></path>'
    };
    return icons[icon] || icons.default;
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

function isCheckedInToday(habitId) {
    // 获取今天的北京日期
    const today = API.utils.getBeijingDateStr();
    // 从打卡记录中检查今天是否已打卡
    // 注意：实际检查逻辑需要根据返回的打卡记录来实现
    return false;
}

async function checkinHabit(habitId) {
    try {
        const response = await API.checkins.checkin(habitId);
        showToast('打卡成功！+' + response.data.points_earned + '⭐');
        
        // 刷新数据
        await loadStats();
        await loadHabits();
        
    } catch (error) {
        showToast(error.message || '打卡失败', 'error');
    }
}

// ============================================
// 统计数据
// ============================================
async function loadStats() {
    try {
        const response = await API.checkins.getStats();
        const stats = response.data;
        
        // 更新统计卡片
        document.querySelectorAll('.stat-value.blue').forEach((el, index) => {
            if (index === 2) el.textContent = stats.today.habits_completed || 0;
            if (index === 3) {
                const rate = stats.today.habits_completed > 0 
                    ? Math.round((stats.today.habits_completed / habits.length) * 100) 
                    : 0;
                el.textContent = rate + '%';
            }
        });
        
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}

// ============================================
// 习惯模态框
// ============================================
function openHabitModal() {
    const modal = document.getElementById('habitModal');
    if (modal) {
        modal.classList.add('active');
    }
}

function closeHabitModal() {
    const modal = document.getElementById('habitModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

async function createHabit() {
    const nameInput = document.querySelector('#habitModal .form-input');
    const name = nameInput ? nameInput.value.trim() : '';
    
    if (!name) {
        showToast('请输入习惯名称', 'error');
        return;
    }
    
    try {
        await API.habits.create({
            name: name,
            description: '',
            icon: 'star',
            color: '#4A7BF7',
            habit_type: 'daily_once',
            points: 1
        });
        
        showToast('习惯创建成功');
        closeHabitModal();
        await loadHabits();
        
    } catch (error) {
        showToast(error.message || '创建失败', 'error');
    }
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
    if (typeof updateCalendar === 'function') {
        updateCalendar();
    }
    
    // 其他初始化...
    initAnimations();
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
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    document.querySelector(`.tab-btn[data-tab="${tabName}"]`)?.classList.add('active');
    document.getElementById(`${tabName}Tab`)?.classList.add('active');
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

// 页面跳转函数
function showPointsPage() {
    showToast('会员功能开发中...');
}

function showHelpPage() {
    showToast('帮助页面开发中...');
}

function showMorePage() {
    showToast('更多功能开发中...');
}

function hidePointsPage() {}
function hideHelpPage() {}
function hideMorePage() {}
