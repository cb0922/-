/**
 * Web Crawler Web App - 增强版（带实时日志）
 * 前端 JavaScript 控制器
 */

// API 基础 URL
const API_BASE = '';

// 当前任务 ID
let currentTaskId = null;
let statusCheckInterval = null;
let logsCheckInterval = null;
let lastLogOffset = 0;

// ===== 页面初始化 =====
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initEventListeners();
    loadDashboardData();
    loadURLs();
    loadReports();
    loadDocuments();
});

// ===== 导航 =====
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            showPage(page);
            
            // 更新活动状态
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

function showPage(page) {
    // 隐藏所有页面
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    // 显示目标页面
    const targetPage = document.getElementById(`${page}-page`);
    if (targetPage) {
        targetPage.classList.add('active');
    }
    
    // 更新页面标题
    const titles = {
        'dashboard': '控制台',
        'urls': '网址管理',
        'crawler': '爬取任务',
        'reports': '报告查看',
        'documents': '文档下载'
    };
    document.querySelector('.page-title').textContent = titles[page] || '控制台';
    
    // 更新导航状态
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === page);
    });
    
    // 加载对应页面数据
    if (page === 'dashboard') loadDashboardData();
    if (page === 'urls') loadURLs();
    if (page === 'reports') loadReports();
    if (page === 'documents') loadDocuments();
}

// ===== 事件监听 =====
function initEventListeners() {
    // 刷新按钮
    document.getElementById('refreshBtn')?.addEventListener('click', () => {
        loadDashboardData();
        showToast('数据已刷新', 'success');
    });
    
    // 添加网址
    document.getElementById('addUrlBtn')?.addEventListener('click', () => {
        const url = document.getElementById('newUrl').value.trim();
        const name = document.getElementById('newUrlName').value.trim();
        if (url) {
            addURL(url, name);
        } else {
            showToast('请输入网址', 'warning');
        }
    });
    
    // 快速添加
    document.getElementById('quickAddBtn')?.addEventListener('click', () => {
        const url = document.getElementById('newUrl').value.trim();
        const name = document.getElementById('newUrlName').value.trim();
        if (url) {
            addURL(url, name);
        } else {
            showToast('请输入网址', 'warning');
        }
    });
    
    // 回车添加
    document.getElementById('newUrl')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const url = e.target.value.trim();
            const name = document.getElementById('newUrlName').value.trim();
            if (url) addURL(url, name);
        }
    });
    
    // 导入文件
    document.getElementById('importBtn')?.addEventListener('click', () => {
        document.getElementById('fileInput').click();
    });
    
    document.getElementById('fileInput')?.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) uploadURLsFile(file);
    });
    
    // 开始爬取
    document.getElementById('startCrawlBtn')?.addEventListener('click', startCrawl);
    
    // 日期过滤开关
    document.getElementById('filterByDate')?.addEventListener('change', (e) => {
        const dateConfig = document.getElementById('dateFilterConfig');
        if (dateConfig) {
            dateConfig.style.display = e.target.checked ? 'block' : 'none';
        }
    });
    
    // 刷新报告
    document.getElementById('refreshReportsBtn')?.addEventListener('click', loadReports);
    
    // 刷新文档
    document.getElementById('refreshDocsBtn')?.addEventListener('click', loadDocuments);
}

// ===== API 请求 =====
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${url}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '请求失败');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast(error.message, 'error');
        throw error;
    }
}

// ===== 仪表板数据 =====
async function loadDashboardData() {
    try {
        // 加载统计数据
        const stats = await apiRequest('/api/stats');
        document.getElementById('stat-urls').textContent = stats.urls_count || 0;
        document.getElementById('stat-tasks').textContent = stats.tasks?.completed || 0;
        document.getElementById('stat-docs').textContent = stats.documents_count || 0;
        document.getElementById('stat-reports').textContent = stats.reports_count || 0;
        
        // 加载最近任务
        const tasks = await apiRequest('/api/crawl/tasks');
        const recentTasks = tasks.slice(-5).reverse();
        const tasksContainer = document.getElementById('recent-tasks');
        
        if (recentTasks.length === 0) {
            tasksContainer.innerHTML = '<p class="empty-state">暂无任务记录</p>';
        } else {
            tasksContainer.innerHTML = recentTasks.map(task => `
                <div class="task-item">
                    <div class="task-status ${task.status}">
                        <i class="fas ${getStatusIcon(task.status)}"></i>
                    </div>
                    <div class="task-info">
                        <h4>任务 ${task.task_id}</h4>
                        <p>${task.message} • ${formatDate(task.created_at)}</p>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('加载仪表板数据失败:', error);
    }
}

// ===== URL 管理 =====
async function loadURLs() {
    try {
        const urls = await apiRequest('/api/urls');
        const tbody = document.getElementById('urlsTableBody');
        
        if (urls.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-cell">暂无数据</td></tr>';
        } else {
            tbody.innerHTML = urls.map(u => `
                <tr>
                    <td title="${u.url}">${truncate(u.url, 50)}</td>
                    <td>${u.name || '-'}</td>
                    <td>${u.category || '-'}</td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="deleteURL('${encodeURIComponent(u.url)}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('加载 URL 失败:', error);
    }
}

async function addURL(url, name = '', category = '') {
    try {
        await apiRequest('/api/urls', {
            method: 'POST',
            body: JSON.stringify({ url, name, category })
        });
        showToast('添加成功', 'success');
        document.getElementById('newUrl').value = '';
        document.getElementById('newUrlName').value = '';
        loadURLs();
        loadDashboardData();
    } catch (error) {
        // 错误已在 apiRequest 中处理
    }
}

async function deleteURL(encodedUrl) {
    const url = decodeURIComponent(encodedUrl);
    if (!confirm('确定要删除这个网址吗？')) return;
    
    try {
        await apiRequest(`/api/urls/${encodeURIComponent(url)}`, {
            method: 'DELETE'
        });
        showToast('删除成功', 'success');
        loadURLs();
        loadDashboardData();
    } catch (error) {
        // 错误已在 apiRequest 中处理
    }
}

async function uploadURLsFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE}/api/urls/upload`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast(`成功导入 ${result.added} 个网址`, 'success');
            loadURLs();
            loadDashboardData();
        } else {
            throw new Error(result.detail || '导入失败');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
    
    // 清空文件输入
    document.getElementById('fileInput').value = '';
}

// ===== 爬取任务 =====
async function startCrawl() {
    const config = {
        mode: document.getElementById('crawlMode').value,
        use_dynamic: document.getElementById('useDynamic').checked,
        timeout: parseInt(document.getElementById('timeout').value),
        use_proxy: document.getElementById('useProxy').checked,
        max_retries: parseInt(document.getElementById('maxRetries').value),
        auto_remove_failed: document.getElementById('autoRemove').checked,
        // 新增：日期范围过滤配置
        filter_by_date: document.getElementById('filterByDate').checked,
        start_date: document.getElementById('startDate').value,
        end_date: document.getElementById('endDate').value || null
    };
    
    try {
        const result = await apiRequest('/api/crawl/start', {
            method: 'POST',
            body: JSON.stringify(config)
        });
        
        currentTaskId = result.task_id;
        lastLogOffset = 0;
        showToast('爬虫任务已启动', 'success');
        
        // 显示进度卡片
        document.getElementById('progressCard').style.display = 'block';
        document.getElementById('startCrawlBtn').disabled = true;
        
        // 清空日志显示
        const logContent = document.getElementById('logContent');
        if (logContent) {
            logContent.innerHTML = '';
        }
        
        // 开始检查状态
        startStatusCheck();
        startLogsCheck();
        
    } catch (error) {
        // 错误已在 apiRequest 中处理
    }
}

function startStatusCheck() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    statusCheckInterval = setInterval(async () => {
        if (!currentTaskId) return;
        
        try {
            const status = await apiRequest(`/api/crawl/status/${currentTaskId}`);
            updateProgress(status);
            
            if (status.status === 'completed' || status.status === 'failed') {
                clearInterval(statusCheckInterval);
                clearInterval(logsCheckInterval);
                document.getElementById('startCrawlBtn').disabled = false;
                
                if (status.status === 'completed') {
                    showToast('爬取完成！', 'success');
                    loadReports();
                    loadDocuments();
                } else {
                    showToast('爬取失败: ' + status.message, 'error');
                }
                
                loadDashboardData();
            }
        } catch (error) {
            console.error('检查状态失败:', error);
        }
    }, 2000);
}

function startLogsCheck() {
    if (logsCheckInterval) {
        clearInterval(logsCheckInterval);
    }
    
    // 立即获取一次日志
    fetchNewLogs();
    
    // 定期获取新日志
    logsCheckInterval = setInterval(fetchNewLogs, 1000);
}

async function fetchNewLogs() {
    if (!currentTaskId) return;
    
    try {
        const response = await apiRequest(`/api/crawl/logs/${currentTaskId}?offset=${lastLogOffset}&limit=50`);
        
        if (response.logs && response.logs.length > 0) {
            appendLogsToDisplay(response.logs);
            lastLogOffset += response.logs.length;
        }
    } catch (error) {
        console.error('获取日志失败:', error);
    }
}

function appendLogsToDisplay(logs) {
    const logContent = document.getElementById('logContent');
    if (!logContent) return;
    
    logs.forEach(log => {
        const logLine = document.createElement('div');
        logLine.className = `log-line log-${log.level}`;
        
        // 根据日志级别添加图标
        let icon = 'ℹ️';
        if (log.level === 'success') icon = '✅';
        if (log.level === 'error') icon = '❌';
        if (log.level === 'warning') icon = '⚠️';
        
        logLine.innerHTML = `<span class="log-time">[${log.timestamp}]</span> <span class="log-icon">${icon}</span> <span class="log-message">${escapeHtml(log.message)}</span>`;
        
        logContent.appendChild(logLine);
    });
    
    // 自动滚动到底部
    logContent.scrollTop = logContent.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateProgress(status) {
    const percent = status.total > 0 ? Math.round((status.progress / status.total) * 100) : 0;
    
    const progressStatus = document.getElementById('progressStatus');
    const progressPercent = document.getElementById('progressPercent');
    const progressFill = document.getElementById('progressFill');
    const progressMessage = document.getElementById('progressMessage');
    
    if (progressStatus) progressStatus.textContent = getStatusText(status.status);
    if (progressPercent) progressPercent.textContent = `${percent}%`;
    if (progressFill) progressFill.style.width = `${percent}%`;
    if (progressMessage) progressMessage.textContent = status.message;
}

// ===== 报告管理 =====
async function loadReports() {
    try {
        const reports = await apiRequest('/api/reports');
        const grid = document.getElementById('reportsGrid');
        
        if (reports.length === 0) {
            grid.innerHTML = '<p class="empty-state">暂无报告</p>';
        } else {
            grid.innerHTML = reports.map(r => `
                <div class="report-card">
                    <div class="report-icon ${r.type}">
                        <i class="fas ${getFileIcon(r.type)}"></i>
                    </div>
                    <div class="report-info">
                        <h4>${r.name}</h4>
                        <p>${formatFileSize(r.size)} • ${formatDate(r.created)}</p>
                    </div>
                    <div class="report-actions">
                        <a href="${r.path}" class="btn btn-primary btn-sm" download>
                            <i class="fas fa-download"></i>
                        </a>
                        ${r.type === 'html' ? `
                            <a href="${r.path}" target="_blank" class="btn btn-secondary btn-sm">
                                <i class="fas fa-eye"></i>
                            </a>
                        ` : ''}
                        <button class="btn btn-danger btn-sm" onclick="deleteReport('${r.type}', '${r.name}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('加载报告失败:', error);
    }
}

async function deleteReport(type, filename) {
    if (!confirm('确定要删除这个报告吗？')) return;
    
    try {
        await apiRequest(`/api/reports/${type}/${filename}`, {
            method: 'DELETE'
        });
        showToast('删除成功', 'success');
        loadReports();
        loadDashboardData();
    } catch (error) {
        // 错误已在 apiRequest 中处理
    }
}

// ===== 文档管理 =====
async function loadDocuments() {
    try {
        const docs = await apiRequest('/api/documents');
        const list = document.getElementById('documentsList');
        
        if (docs.length === 0) {
            list.innerHTML = '<p class="empty-state">暂无文档</p>';
        } else {
            list.innerHTML = docs.map(d => `
                <div class="document-item">
                    <div class="doc-icon ${d.type.replace('.', '')}">
                        <i class="fas ${getFileIcon(d.type)}"></i>
                    </div>
                    <div class="doc-info">
                        <h4>${d.name}</h4>
                        <p>${formatDate(d.created)}</p>
                    </div>
                    <span class="doc-size">${formatFileSize(d.size)}</span>
                    <a href="${d.path}" class="btn btn-primary btn-sm" download>
                        <i class="fas fa-download"></i> 下载
                    </a>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('加载文档失败:', error);
    }
}

// ===== 工具函数 =====
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas fa-${icons[type]} toast-icon"></i>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // 自动消失
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function getStatusIcon(status) {
    const icons = {
        pending: 'fa-clock',
        running: 'fa-spinner',
        completed: 'fa-check',
        failed: 'fa-times'
    };
    return icons[status] || 'fa-question';
}

function getStatusText(status) {
    const texts = {
        pending: '等待中',
        running: '进行中',
        completed: '已完成',
        failed: '失败'
    };
    return texts[status] || status;
}

function getFileIcon(type) {
    const icons = {
        html: 'fa-file-code',
        word: 'fa-file-word',
        doc: 'fa-file-word',
        docx: 'fa-file-word',
        json: 'fa-file-code',
        pdf: 'fa-file-pdf',
        xls: 'fa-file-excel',
        xlsx: 'fa-file-excel',
        ppt: 'fa-file-powerpoint',
        pptx: 'fa-file-powerpoint',
        zip: 'fa-file-archive',
        rar: 'fa-file-archive'
    };
    return icons[type] || 'fa-file';
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
}

function formatFileSize(bytes) {
    if (!bytes) return '-';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
}

function truncate(str, length) {
    if (!str) return '-';
    return str.length > length ? str.substring(0, length) + '...' : str;
}
