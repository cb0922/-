// 当前选中的日期
let currentDate = new Date(2026, 3, 2); // 2026年4月2日

// Tab 切换功能
function switchTab(tabName) {
    // 移除所有active类
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // 添加active类到当前选中的tab
    document.querySelector(`.tab-btn[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}Tab`).classList.add('active');
}

// 更新日历显示
function updateCalendar() {
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
    document.getElementById('weekTitle').textContent = `${year}年${month + 1}月第${weekNum}周`;
    
    // 更新日期格子
    const dayCells = document.querySelectorAll('.day-cell');
    const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    
    dayCells.forEach((cell, index) => {
        const cellDate = new Date(weekStart);
        cellDate.setDate(weekStart.getDate() + index);
        
        const cellMonth = cellDate.getMonth() + 1;
        const cellDay = cellDate.getDate();
        
        cell.querySelector('.day-name').textContent = weekDays[index];
        cell.querySelector('.day-date').textContent = `${cellMonth}/${cellDay}`;
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

// 切换周
function changeWeek(direction) {
    currentDate.setDate(currentDate.getDate() + (direction * 7));
    updateCalendar();
}

// 回到今天
function goToToday() {
    currentDate = new Date();
    updateCalendar();
}

// 关闭通知横幅
function closeBanner() {
    const banner = document.getElementById('notificationBanner');
    banner.style.opacity = '0';
    banner.style.transform = 'translateY(-10px)';
    setTimeout(() => {
        banner.style.display = 'none';
    }, 300);
}

// 统计卡片点击效果
document.querySelectorAll('.stat-card.clickable').forEach(card => {
    card.addEventListener('click', function() {
        // 移除其他卡片的active状态
        document.querySelectorAll('.stat-card.clickable').forEach(c => {
            c.classList.remove('active');
        });
        // 添加当前卡片的active状态
        this.classList.add('active');
        
        // 获取卡片标签
        const label = this.querySelector('.stat-label').textContent;
        console.log(`点击了: ${label}`);
    });
});

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 添加一些动画效果
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
    
    // 通知横幅动画
    const banner = document.getElementById('notificationBanner');
    if (banner) {
        banner.style.opacity = '0';
        banner.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            banner.style.transition = 'all 0.3s ease';
            banner.style.opacity = '1';
            banner.style.transform = 'translateY(0)';
        }, 300);
    }
    
    // 初始化日历
    updateCalendar();
    
    // 初始化习惯列表日历
    initHabitCalendar();
    
    // 筛选标签切换
    const filterTags = document.querySelectorAll('.filter-tag');
    filterTags.forEach(tag => {
        tag.addEventListener('click', function() {
            filterTags.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // 视图切换
    const viewBtns = document.querySelectorAll('.view-toggle .view-btn:not(.refresh-btn)');
    viewBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            viewBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });
});

// 模拟数据更新（演示用）
function updateStats() {
    // 可以在这里添加实时数据更新逻辑
    console.log('更新统计数据...');
}

// 每分钟更新一次数据
setInterval(updateStats, 60000);

// 习惯列表页面当前日期
let habitCurrentDate = new Date(2026, 3, 2);

// 初始化习惯列表日历
function initHabitCalendar() {
    updateHabitCalendar();
}

// 更新习惯列表日历
function updateHabitCalendar() {
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
    
    // 更新日期格子
    const dayCells = document.querySelectorAll('.habit-week-calendar .day-cell');
    const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    
    dayCells.forEach((cell, index) => {
        const cellDate = new Date(weekStart);
        cellDate.setDate(weekStart.getDate() + index);
        
        const cellMonth = cellDate.getMonth() + 1;
        const cellDay = cellDate.getDate();
        
        cell.querySelector('.day-name').textContent = weekDays[index];
        cell.querySelector('.day-date').textContent = `${cellMonth}/${cellDay}`;
        
        // 检查是否是当前选中日期
        cell.classList.remove('active');
        if (cellDate.toDateString() === habitCurrentDate.toDateString()) {
            cell.classList.add('active');
        }
        
        // 点击事件
        cell.onclick = () => {
            habitCurrentDate = new Date(cellDate);
            updateHabitCalendar();
        };
    });
}

// 习惯列表切换周
function changeHabitWeek(direction) {
    habitCurrentDate.setDate(habitCurrentDate.getDate() + (direction * 7));
    updateHabitCalendar();
}

// 习惯列表回到今天
function goToHabitToday() {
    habitCurrentDate = new Date();
    updateHabitCalendar();
}

// ===== 习惯管理模态框功能 =====
let selectedIcon = 'star';
let selectedColor = '#4A7BF7';

// 打开模态框
function openHabitModal() {
    const modal = document.getElementById('habitModal');
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// 关闭模态框
function closeHabitModal() {
    const modal = document.getElementById('habitModal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

// 切换到习惯管理视图
function showHabitManageView() {
    // 隐藏习惯列表，显示习惯管理
    const habitListContent = document.querySelector('.habit-list-header').parentElement;
    
    // 创建习惯管理视图
    const manageViewHTML = `
        <div class="habit-manage-view" id="habitManageView">
            <div class="habit-manage-header">
                <div class="habit-title-section">
                    <div class="back-btn" onclick="showHabitListView()">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="15 18 9 12 15 6"></polyline>
                        </svg>
                    </div>
                    <div class="habit-titles">
                        <h2 class="habit-main-title">行为习惯管理</h2>
                        <p class="habit-sub-title">创建和管理您的行为习惯</p>
                    </div>
                </div>
                <div class="habit-actions">
                    <button class="btn btn-primary" onclick="openHabitModal()">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;">
                            <line x1="12" y1="5" x2="12" y2="19"></line>
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                        新建习惯
                    </button>
                    <button class="btn btn-outline">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;">
                            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                            <circle cx="9" cy="7" r="4"></circle>
                            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                        </svg>
                        导入其他用户习惯
                    </button>
                    <button class="btn btn-outline">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                        </svg>
                        添加默认习惯
                    </button>
                </div>
            </div>
            <div class="habit-manage-content">
                <div class="habit-empty-state">
                    <div class="habit-empty-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="#4A90E2" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <path d="M12 8v4l3 3"></path>
                        </svg>
                    </div>
                    <h3 class="habit-empty-title">还没有行为习惯</h3>
                    <p class="habit-empty-desc">创建你的第一个行为习惯，开始培养好习惯，赚取星星积分吧！</p>
                    <button class="btn btn-primary btn-create-first" onclick="openHabitModal()">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;">
                            <line x1="12" y1="5" x2="12" y2="19"></line>
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                        创建第一个习惯
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // 保存当前列表内容
    if (!document.getElementById('habitListContent')) {
        habitListContent.innerHTML = '<div id="habitListContent" style="display:none;"></div>' + habitListContent.innerHTML;
    }
    
    // 替换为管理视图
    habitListContent.innerHTML = manageViewHTML;
}

// 返回习惯列表视图
function showHabitListView() {
    location.reload(); // 简单刷新页面回到列表视图
}

// 创建习惯
function createHabit() {
    const nameInput = document.querySelector('.modal-body .form-input');
    const name = nameInput.value.trim();
    
    if (!name) {
        alert('请输入习惯名称');
        return;
    }
    
    console.log('创建习惯:', {
        name: name,
        icon: selectedIcon,
        color: selectedColor
    });
    
    closeHabitModal();
    
    // 清空表单
    nameInput.value = '';
    document.querySelector('.form-textarea').value = '';
}

// 点击模态框外部关闭
function initModalOverlay() {
    const modal = document.getElementById('habitModal');
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeHabitModal();
        }
    });
    
    // 图标选择
    const iconItems = document.querySelectorAll('.icon-item');
    iconItems.forEach(item => {
        item.addEventListener('click', function() {
            iconItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            selectedIcon = this.dataset.icon;
            updatePreview();
        });
    });
    
    // 颜色选择
    const colorItems = document.querySelectorAll('.color-item');
    colorItems.forEach(item => {
        item.addEventListener('click', function() {
            colorItems.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            selectedColor = this.dataset.color;
            updatePreview();
        });
    });
}

// 更新预览
function updatePreview() {
    const previewIcon = document.getElementById('previewIcon');
    previewIcon.style.background = selectedColor;
    
    // 获取选中图标的SVG
    const activeIcon = document.querySelector('.icon-item.active svg');
    if (activeIcon) {
        previewIcon.innerHTML = activeIcon.outerHTML;
    }
}

// 初始化模态框
initModalOverlay();

// ===== 积分和成就页面功能 =====
function showPointsPage() {
    const pointsPage = document.getElementById('pointsPage');
    pointsPage.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function hidePointsPage() {
    const pointsPage = document.getElementById('pointsPage');
    pointsPage.classList.remove('active');
    document.body.style.overflow = '';
}

// 点击统计卡片上的

// 点击统计卡片上的"积分成就"打开积分页面
document.addEventListener('DOMContentLoaded', function() {
    // 找到积分成就卡片并添加点击事件
    const pointsCard = document.querySelector('.stat-card.clickable .stat-icon.trophy');
    if (pointsCard) {
        pointsCard.closest('.stat-card').addEventListener('click', showPointsPage);
    }
    
    // 找到使用帮助卡片并添加点击事件
    const helpCard = document.querySelector('.stat-card.clickable .stat-icon.help');
    if (helpCard) {
        helpCard.closest('.stat-card').addEventListener('click', showHelpPage);
    }
    
    // 找到其他卡片并添加点击事件
    const moreCard = document.querySelector('.stat-card.clickable .stat-more');
    if (moreCard) {
        moreCard.closest('.stat-card').addEventListener('click', showMorePage);
    }
});

// ===== 使用帮助页面功能 =====
function showHelpPage() {
    const helpPage = document.getElementById('helpPage');
    helpPage.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function hideHelpPage() {
    const helpPage = document.getElementById('helpPage');
    helpPage.classList.remove('active');
    document.body.style.overflow = '';
}

// ===== 其他功能页面功能 =====
function showMorePage() {
    const morePage = document.getElementById('morePage');
    morePage.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function hideMorePage() {
    const morePage = document.getElementById('morePage');
    morePage.classList.remove('active');
    document.body.style.overflow = '';
}
