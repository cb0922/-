// ============================================
// 学习计划高级功能 - AI创建、批量添加、完整表单
// ============================================

// ============================================
// 1. 完善的添加计划表单（带完整字段）
// ============================================
function showAddPlanModal() {
    let modal = document.getElementById('addPlanModal');
    if (!modal) {
        modal = createAddPlanModal();
        document.body.appendChild(modal);
    }
    
    // 重置表单
    resetPlanForm();
    modal.classList.add('active');
}

function createAddPlanModal() {
    const modal = document.createElement('div');
    modal.id = 'addPlanModal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-container" style="max-width: 500px; max-height: 85vh; overflow-y: auto;">
            <div class="modal-header">
                <div class="modal-title-section">
                    <h3 class="modal-title">添加学习计划</h3>
                    <p class="modal-subtitle">创建详细的学习计划，设置时间和提醒</p>
                </div>
                <button class="modal-close" onclick="closeAddPlanModal()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            
            <div class="modal-body">
                <!-- 计划名称 -->
                <div class="form-group">
                    <label class="form-label">计划名称 <span style="color: #EF4444;">*</span></label>
                    <input type="text" class="form-input" id="planName" placeholder="例如：数学作业、英语阅读30分钟">
                </div>
                
                <!-- 学科分类 -->
                <div class="form-group">
                    <label class="form-label">学科分类</label>
                    <div class="form-select-wrapper">
                        <select class="form-select" id="planSubject">
                            <option value="">请选择学科</option>
                            <option value="语文">语文</option>
                            <option value="数学">数学</option>
                            <option value="英语">英语</option>
                            <option value="物理">物理</option>
                            <option value="化学">化学</option>
                            <option value="生物">生物</option>
                            <option value="历史">历史</option>
                            <option value="地理">地理</option>
                            <option value="政治">政治</option>
                            <option value="其他">其他</option>
                        </select>
                        <svg class="select-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                    </div>
                </div>
                
                <!-- 预计时间 -->
                <div class="form-group">
                    <label class="form-label">预计时间（分钟） <span style="color: #EF4444;">*</span></label>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                        <button type="button" class="time-quick-btn" data-time="15" onclick="selectPlanTime(15)">15分钟</button>
                        <button type="button" class="time-quick-btn" data-time="30" onclick="selectPlanTime(30)">30分钟</button>
                        <button type="button" class="time-quick-btn" data-time="45" onclick="selectPlanTime(45)">45分钟</button>
                        <button type="button" class="time-quick-btn" data-time="60" onclick="selectPlanTime(60)">1小时</button>
                        <button type="button" class="time-quick-btn" data-time="90" onclick="selectPlanTime(90)">1.5小时</button>
                        <button type="button" class="time-quick-btn" data-time="120" onclick="selectPlanTime(120)">2小时</button>
                    </div>
                    <input type="number" class="form-input" id="planTime" placeholder="自定义时间（分钟）" style="margin-top: 8px;" min="1" max="480">
                </div>
                
                <!-- 优先级 -->
                <div class="form-group">
                    <label class="form-label">优先级</label>
                    <div style="display: flex; gap: 12px;">
                        <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                            <input type="radio" name="planPriority" value="high" style="cursor: pointer;">
                            <span style="color: #EF4444;">🔴 高</span>
                        </label>
                        <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                            <input type="radio" name="planPriority" value="medium" checked style="cursor: pointer;">
                            <span style="color: #F59E0B;">🟡 中</span>
                        </label>
                        <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                            <input type="radio" name="planPriority" value="low" style="cursor: pointer;">
                            <span style="color: #22C55E;">🟢 低</span>
                        </label>
                    </div>
                </div>
                
                <!-- 计划内容/备注 -->
                <div class="form-group">
                    <label class="form-label">计划内容/备注</label>
                    <textarea class="form-textarea" id="planContent" placeholder="详细描述计划内容，例如：完成第3单元练习题，背诵单词50个..."></textarea>
                </div>
                
                <!-- 关联习惯 -->
                <div class="form-group">
                    <label class="form-label">关联习惯（可选）</label>
                    <div class="form-select-wrapper">
                        <select class="form-select" id="planRelatedHabit">
                            <option value="">不关联习惯</option>
                            <!-- 动态加载习惯选项 -->
                        </select>
                        <svg class="select-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                    </div>
                    <p class="form-hint">关联习惯后，完成计划会自动打卡对应习惯</p>
                </div>
            </div>
            
            <div class="modal-footer">
                <button class="btn btn-create" onclick="savePlanForm()">创建计划</button>
                <button class="btn btn-cancel" onclick="closeAddPlanModal()">取消</button>
            </div>
        </div>
        
        <style>
            .time-quick-btn {
                padding: 6px 12px;
                border: 1px solid #E5E7EB;
                background: white;
                border-radius: 6px;
                font-size: 13px;
                cursor: pointer;
                transition: all 0.2s;
            }
            .time-quick-btn:hover {
                border-color: #4A7BF7;
                color: #4A7BF7;
            }
            .time-quick-btn.active {
                background: #4A7BF7;
                color: white;
                border-color: #4A7BF7;
            }
        </style>
    `;
    
    // 加载习惯选项
    setTimeout(() => loadHabitOptions(), 0);
    
    return modal;
}

function loadHabitOptions() {
    const select = document.getElementById('planRelatedHabit');
    if (!select || habits.length === 0) return;
    
    let options = '<option value="">不关联习惯</option>';
    habits.forEach(habit => {
        options += `<option value="${habit.id}">${habit.name}</option>`;
    });
    select.innerHTML = options;
}

function selectPlanTime(minutes) {
    document.getElementById('planTime').value = minutes;
    document.querySelectorAll('.time-quick-btn').forEach(btn => {
        btn.classList.toggle('active', parseInt(btn.dataset.time) === minutes);
    });
}

function resetPlanForm() {
    document.getElementById('planName').value = '';
    document.getElementById('planSubject').value = '';
    document.getElementById('planTime').value = '';
    document.getElementById('planContent').value = '';
    document.getElementById('planRelatedHabit').value = '';
    document.querySelectorAll('.time-quick-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector('input[name="planPriority"][value="medium"]').checked = true;
}

function closeAddPlanModal() {
    const modal = document.getElementById('addPlanModal');
    if (modal) modal.classList.remove('active');
}

function savePlanForm() {
    const name = document.getElementById('planName').value.trim();
    const subject = document.getElementById('planSubject').value;
    const time = parseInt(document.getElementById('planTime').value) || 30;
    const content = document.getElementById('planContent').value.trim();
    const priority = document.querySelector('input[name="planPriority"]:checked').value;
    const relatedHabit = document.getElementById('planRelatedHabit').value;
    
    if (!name) {
        showToast('请输入计划名称', 'error');
        return;
    }
    
    const plan = {
        id: Date.now(),
        name: subject ? `[${subject}] ${name}` : name,
        estimatedTime: time,
        completed: false,
        completedTime: 0,
        content: content,
        priority: priority,
        relatedHabit: relatedHabit || null,
        createdAt: API.utils.getBeijingDateStr()
    };
    
    studyPlans.push(plan);
    saveStudyPlans();
    renderStudyPlans();
    closeAddPlanModal();
    
    showToast('学习计划添加成功');
}

// ============================================
// 2. 批量添加功能
// ============================================
function showBatchAddModal() {
    let modal = document.getElementById('batchAddModal');
    if (!modal) {
        modal = createBatchAddModal();
        document.body.appendChild(modal);
    }
    modal.classList.add('active');
}

function createBatchAddModal() {
    const modal = document.createElement('div');
    modal.id = 'batchAddModal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-container" style="max-width: 600px; max-height: 85vh; overflow-y: auto;">
            <div class="modal-header">
                <div class="modal-title-section">
                    <h3 class="modal-title">批量添加学习计划</h3>
                    <p class="modal-subtitle">一次添加多个计划，每行一个，格式：计划名称 | 预计时间（分钟）</p>
                </div>
                <button class="modal-close" onclick="closeBatchAddModal()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            
            <div class="modal-body">
                <!-- 示例说明 -->
                <div style="background: #F3F4F6; border-radius: 8px; padding: 12px; margin-bottom: 16px; font-size: 13px; color: #6B7280;">
                    <strong>输入格式示例：</strong><br>
                    数学作业 | 45<br>
                    英语单词背诵 | 30<br>
                    语文阅读理解 | 60<br>
                    <br>
                    <strong>提示：</strong>每行一个计划，用 | 分隔名称和时间。不填写时间默认为30分钟。
                </div>
                
                <!-- 学科选择 -->
                <div class="form-group">
                    <label class="form-label">默认学科（可选）</label>
                    <div class="form-select-wrapper">
                        <select class="form-select" id="batchPlanSubject">
                            <option value="">不指定学科</option>
                            <option value="语文">语文</option>
                            <option value="数学">数学</option>
                            <option value="英语">英语</option>
                            <option value="物理">物理</option>
                            <option value="化学">化学</option>
                            <option value="其他">其他</option>
                        </select>
                        <svg class="select-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                    </div>
                </div>
                
                <!-- 批量输入 -->
                <div class="form-group">
                    <label class="form-label">计划列表 <span style="color: #EF4444;">*</span></label>
                    <textarea class="form-textarea" id="batchPlanInput" rows="10" placeholder="数学作业 | 45&#10;英语单词背诵 | 30&#10;语文阅读理解 | 60"></textarea>
                </div>
                
                <!-- 快捷添加 -->
                <div class="form-group">
                    <label class="form-label">快捷模板</label>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                        <button type="button" class="template-btn" onclick="applyBatchTemplate('morning')">📚 晨读计划</button>
                        <button type="button" class="template-btn" onclick="applyBatchTemplate('homework')">✏️ 作业计划</button>
                        <button type="button" class="template-btn" onclick="applyBatchTemplate('review')">📝 复习计划</button>
                        <button type="button" class="template-btn" onclick="applyBatchTemplate('english')">🇬🇧 英语学习</button>
                        <button type="button" class="template-btn" onclick="applyBatchTemplate('math')">🔢 数学练习</button>
                    </div>
                </div>
            </div>
            
            <div class="modal-footer">
                <button class="btn btn-create" onclick="saveBatchPlans()">批量创建</button>
                <button class="btn btn-cancel" onclick="closeBatchAddModal()">取消</button>
            </div>
        </div>
        
        <style>
            .template-btn {
                padding: 6px 12px;
                border: 1px solid #E5E7EB;
                background: white;
                border-radius: 6px;
                font-size: 13px;
                cursor: pointer;
                transition: all 0.2s;
            }
            .template-btn:hover {
                border-color: #4A7BF7;
                background: #EFF6FF;
            }
        </style>
    `;
    return modal;
}

function applyBatchTemplate(template) {
    const input = document.getElementById('batchPlanInput');
    const subjectSelect = document.getElementById('batchPlanSubject');
    
    const templates = {
        morning: `晨读-语文 | 20
晨读-英语 | 15
古诗词背诵 | 10`,
        homework: `数学作业 | 45
语文作业 | 30
英语作业 | 30`,
        review: `数学错题复习 | 30
语文课文复习 | 20
英语单词复习 | 20`,
        english: `英语单词记忆 | 30
英语听力练习 | 20
英语阅读理解 | 30`,
        math: `数学公式整理 | 15
数学练习题 | 45
数学错题订正 | 30`
    };
    
    if (templates[template]) {
        input.value = templates[template];
        // 自动选择对应学科
        if (template === 'english') subjectSelect.value = '英语';
        else if (template === 'math') subjectSelect.value = '数学';
    }
}

function closeBatchAddModal() {
    const modal = document.getElementById('batchAddModal');
    if (modal) modal.classList.remove('active');
}

function saveBatchPlans() {
    const input = document.getElementById('batchPlanInput').value.trim();
    const subject = document.getElementById('batchPlanSubject').value;
    
    if (!input) {
        showToast('请输入计划内容', 'error');
        return;
    }
    
    const lines = input.split('\n').filter(line => line.trim());
    let addedCount = 0;
    
    lines.forEach(line => {
        // 解析格式：计划名称 | 时间
        const parts = line.split('|').map(p => p.trim());
        const name = parts[0];
        const time = parts[1] ? parseInt(parts[1]) : 30;
        
        if (name) {
            const plan = {
                id: Date.now() + Math.random(),
                name: subject ? `[${subject}] ${name}` : name,
                estimatedTime: time || 30,
                completed: false,
                completedTime: 0,
                createdAt: API.utils.getBeijingDateStr()
            };
            studyPlans.push(plan);
            addedCount++;
        }
    });
    
    if (addedCount > 0) {
        saveStudyPlans();
        renderStudyPlans();
        closeBatchAddModal();
        showToast(`成功添加 ${addedCount} 个学习计划`);
    } else {
        showToast('没有有效的计划内容', 'error');
    }
}

// ============================================
// 3. AI创建功能（支持KIM API）
// ============================================
function showAICreateModal() {
    let modal = document.getElementById('aiCreateModal');
    if (!modal) {
        modal = createAICreateModal();
        document.body.appendChild(modal);
    }
    modal.classList.add('active');
}

function createAICreateModal() {
    const modal = document.createElement('div');
    modal.id = 'aiCreateModal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-container" style="max-width: 600px; max-height: 85vh; overflow-y: auto;">
            <div class="modal-header">
                <div class="modal-title-section">
                    <h3 class="modal-title">🤖 AI智能创建学习计划</h3>
                    <p class="modal-subtitle">描述你的学习目标，AI会为你生成合适的学习计划</p>
                </div>
                <button class="modal-close" onclick="closeAICreateModal()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            
            <div class="modal-body">
                <!-- 需求输入 -->
                <div class="form-group">
                    <label class="form-label">描述你的学习目标 <span style="color: #EF4444;">*</span></label>
                    <textarea class="form-textarea" id="aiPlanPrompt" rows="4" placeholder="例如：我是一名初二学生，明天要考数学，需要复习三角形和函数相关内容，预计有2小时时间..."></textarea>
                </div>
                
                <!-- 快捷选项 -->
                <div class="form-group">
                    <label class="form-label">快捷选项</label>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                        <button type="button" class="ai-preset-btn" onclick="setAIPrompt('明天要考数学，需要复习代数方程和几何图形')">📐 数学备考</button>
                        <button type="button" class="ai-preset-btn" onclick="setAIPrompt('需要背诵50个英语单词，练习听力和阅读')">🇬🇧 英语学习</button>
                        <button type="button" class="ai-preset-btn" onclick="setAIPrompt('周末要完成语文作业，包括作文和阅读理解')">📖 语文作业</button>
                        <button type="button" class="ai-preset-btn" onclick="setAIPrompt('期中考试复习，需要系统复习各科知识点')">📝 期中复习</button>
                        <button type="button" class="ai-preset-btn" onclick="setAIPrompt('暑假学习计划，每天安排2小时学习时间')">☀️ 暑假计划</button>
                    </div>
                </div>
                
                <!-- 高级选项 -->
                <div class="form-group">
                    <label class="form-label" style="cursor: pointer;" onclick="toggleAdvancedOptions()">
                        <span id="advancedToggle">▼</span> 高级选项
                    </label>
                    <div id="aiAdvancedOptions" style="display: none; margin-top: 12px; padding: 12px; background: #F9FAFB; border-radius: 8px;">
                        <div style="margin-bottom: 12px;">
                            <label style="font-size: 13px; color: #6B7280; display: block; margin-bottom: 6px;">学习时长（小时）</label>
                            <input type="range" id="aiStudyHours" min="0.5" max="8" step="0.5" value="2" style="width: 100%;" oninput="updateHoursDisplay(this.value)">
                            <span id="hoursDisplay" style="font-size: 13px; color: #4A7BF7;">2小时</span>
                        </div>
                        <div>
                            <label style="font-size: 13px; color: #6B7280; display: block; margin-bottom: 6px;">计划风格</label>
                            <select id="aiPlanStyle" style="width: 100%; padding: 8px; border: 1px solid #E5E7EB; border-radius: 6px;">
                                <option value="balanced">平衡型 - 劳逸结合</option>
                                <option value="intensive">密集型 - 高效冲刺</option>
                                <option value="relaxed">轻松型 - 循序渐进</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <!-- AI生成结果 -->
                <div id="aiResultSection" style="display: none;">
                    <div class="form-group">
                        <label class="form-label">AI生成的学习计划</label>
                        <div id="aiGeneratedPlans" style="background: #F0FDF4; border: 1px solid #86EFAC; border-radius: 8px; padding: 12px; max-height: 200px; overflow-y: auto;">
                            <!-- 生成的计划将显示在这里 -->
                        </div>
                    </div>
                </div>
                
                <!-- 加载状态 -->
                <div id="aiLoading" style="display: none; text-align: center; padding: 20px;">
                    <div style="display: inline-block; width: 32px; height: 32px; border: 3px solid #E5E7EB; border-top-color: #4A7BF7; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                    <p style="color: #6B7280; margin-top: 8px;">AI正在生成学习计划...</p>
                </div>
            </div>
            
            <div class="modal-footer" id="aiModalFooter">
                <button class="btn btn-create" onclick="generateAIPlans()" id="aiGenerateBtn">🤖 AI生成计划</button>
                <button class="btn btn-cancel" onclick="closeAICreateModal()">取消</button>
            </div>
        </div>
        
        <style>
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            .ai-preset-btn {
                padding: 8px 14px;
                border: 1px solid #E5E7EB;
                background: white;
                border-radius: 20px;
                font-size: 13px;
                cursor: pointer;
                transition: all 0.2s;
            }
            .ai-preset-btn:hover {
                border-color: #8B5CF6;
                background: #F5F3FF;
                color: #8B5CF6;
            }
            .ai-plan-item {
                background: white;
                border-radius: 8px;
                padding: 10px 12px;
                margin-bottom: 8px;
                border: 1px solid #D1FAE5;
            }
            .ai-plan-item:last-child {
                margin-bottom: 0;
            }
        </style>
    `;
    return modal;
}

function setAIPrompt(text) {
    document.getElementById('aiPlanPrompt').value = text;
}

function toggleAdvancedOptions() {
    const section = document.getElementById('aiAdvancedOptions');
    const toggle = document.getElementById('advancedToggle');
    if (section.style.display === 'none') {
        section.style.display = 'block';
        toggle.textContent = '▲';
    } else {
        section.style.display = 'none';
        toggle.textContent = '▼';
    }
}

function updateHoursDisplay(value) {
    document.getElementById('hoursDisplay').textContent = value + '小时';
}

// 模拟AI生成计划（实际使用时替换为KIM API调用）
async function generateAIPlans() {
    const prompt = document.getElementById('aiPlanPrompt').value.trim();
    const hours = parseFloat(document.getElementById('aiStudyHours').value) || 2;
    const style = document.getElementById('aiPlanStyle').value;
    
    if (!prompt) {
        showToast('请描述你的学习目标', 'error');
        return;
    }
    
    // 显示加载状态
    document.getElementById('aiLoading').style.display = 'block';
    document.getElementById('aiGenerateBtn').disabled = true;
    
    try {
        // TODO: 调用KIM API
        // const response = await callKIMAPI(prompt, hours, style);
        
        // 模拟AI响应（延迟1.5秒模拟思考过程）
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // 模拟生成的计划
        const generatedPlans = simulateAIResponse(prompt, hours, style);
        
        // 显示结果
        displayAIResults(generatedPlans);
        
    } catch (error) {
        showToast('AI生成失败，请重试', 'error');
        console.error('AI生成错误:', error);
    } finally {
        document.getElementById('aiLoading').style.display = 'none';
        document.getElementById('aiGenerateBtn').disabled = false;
    }
}

// 模拟AI响应（实际使用时删除此函数，替换为真实API调用）
function simulateAIResponse(prompt, hours, style) {
    const totalMinutes = hours * 60;
    const plans = [];
    
    // 根据关键词生成相关计划
    if (prompt.includes('数学')) {
        plans.push({ name: '数学公式复习', time: Math.round(totalMinutes * 0.25), subject: '数学' });
        plans.push({ name: '数学例题练习', time: Math.round(totalMinutes * 0.35), subject: '数学' });
        plans.push({ name: '数学错题整理', time: Math.round(totalMinutes * 0.25), subject: '数学' });
        plans.push({ name: '数学模拟测试', time: Math.round(totalMinutes * 0.15), subject: '数学' });
    } else if (prompt.includes('英语')) {
        plans.push({ name: '英语单词背诵', time: Math.round(totalMinutes * 0.3), subject: '英语' });
        plans.push({ name: '英语听力练习', time: Math.round(totalMinutes * 0.25), subject: '英语' });
        plans.push({ name: '英语阅读理解', time: Math.round(totalMinutes * 0.25), subject: '英语' });
        plans.push({ name: '英语写作练习', time: Math.round(totalMinutes * 0.2), subject: '英语' });
    } else if (prompt.includes('语文')) {
        plans.push({ name: '语文课文朗读', time: Math.round(totalMinutes * 0.2), subject: '语文' });
        plans.push({ name: '语文古诗词背诵', time: Math.round(totalMinutes * 0.25), subject: '语文' });
        plans.push({ name: '语文阅读理解', time: Math.round(totalMinutes * 0.3), subject: '语文' });
        plans.push({ name: '语文作文练习', time: Math.round(totalMinutes * 0.25), subject: '语文' });
    } else {
        // 通用计划
        const count = style === 'intensive' ? 4 : style === 'relaxed' ? 3 : 4;
        const timePerPlan = Math.round(totalMinutes / count);
        plans.push({ name: '知识点复习', time: timePerPlan, subject: '' });
        plans.push({ name: '练习题完成', time: timePerPlan, subject: '' });
        plans.push({ name: '错题整理', time: timePerPlan, subject: '' });
        if (count === 4) {
            plans.push({ name: '模拟测试', time: timePerPlan, subject: '' });
        }
    }
    
    // 根据风格调整时间
    if (style === 'intensive') {
        plans.forEach(p => p.time = Math.round(p.time * 0.9));
    } else if (style === 'relaxed') {
        plans.forEach(p => p.time = Math.round(p.time * 1.1));
    }
    
    return plans;
}

// TODO: 实现真实的KIM API调用
async function callKIMAPI(prompt, hours, style) {
    // KIM API配置
    const KIM_API_KEY = 'YOUR_KIM_API_KEY'; // 需要替换为实际的API Key
    const KIM_API_URL = 'https://api.kimi.moonshot.cn/v1/chat/completions';
    
    const requestBody = {
        model: 'kimi-latest',
        messages: [
            {
                role: 'system',
                content: '你是一个学习规划助手。根据用户的需求，生成合理的学习计划。每个计划包含名称和预计时间（分钟）。返回JSON数组格式。'
            },
            {
                role: 'user',
                content: `请为我生成学习计划。需求：${prompt}。可用时间：${hours}小时。风格：${style}。请返回JSON数组格式，每个元素包含name和time字段。`
            }
        ],
        response_format: { type: 'json_object' }
    };
    
    const response = await fetch(KIM_API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${KIM_API_KEY}`
        },
        body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
        throw new Error('API调用失败');
    }
    
    const data = await response.json();
    return JSON.parse(data.choices[0].message.content);
}

function displayAIResults(plans) {
    const container = document.getElementById('aiGeneratedPlans');
    const resultSection = document.getElementById('aiResultSection');
    const footer = document.getElementById('aiModalFooter');
    
    let html = '';
    plans.forEach((plan, index) => {
        html += `
            <div class="ai-plan-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: #1F2937;">${plan.name}</strong>
                        ${plan.subject ? `<span style="background: #4A7BF7; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-left: 8px;">${plan.subject}</span>` : ''}
                    </div>
                    <span style="color: #6B7280; font-size: 13px;">${plan.time}分钟</span>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    resultSection.style.display = 'block';
    
    // 更新按钮
    footer.innerHTML = `
        <button class="btn btn-create" onclick="applyAIPlans()">✓ 应用这些计划</button>
        <button class="btn" onclick="generateAIPlans()" style="background: #F3F4F6; color: #374151;">🔄 重新生成</button>
        <button class="btn btn-cancel" onclick="closeAICreateModal()">取消</button>
    `;
}

function applyAIPlans() {
    const planItems = document.querySelectorAll('.ai-plan-item');
    let addedCount = 0;
    
    planItems.forEach(item => {
        const name = item.querySelector('strong').textContent;
        const timeText = item.querySelector('span:last-child').textContent;
        const time = parseInt(timeText) || 30;
        const subjectBadge = item.querySelector('span:first-child');
        const subject = subjectBadge && subjectBadge.textContent !== timeText ? subjectBadge.textContent : '';
        
        const plan = {
            id: Date.now() + Math.random(),
            name: subject ? `[${subject}] ${name}` : name,
            estimatedTime: time,
            completed: false,
            completedTime: 0,
            createdAt: API.utils.getBeijingDateStr()
        };
        
        studyPlans.push(plan);
        addedCount++;
    });
    
    if (addedCount > 0) {
        saveStudyPlans();
        renderStudyPlans();
        closeAICreateModal();
        showToast(`成功添加 ${addedCount} 个AI生成的学习计划`);
    }
}

function closeAICreateModal() {
    const modal = document.getElementById('aiCreateModal');
    if (modal) {
        modal.classList.remove('active');
        // 重置状态
        setTimeout(() => {
            document.getElementById('aiPlanPrompt').value = '';
            document.getElementById('aiResultSection').style.display = 'none';
            document.getElementById('aiModalFooter').innerHTML = `
                <button class="btn btn-create" onclick="generateAIPlans()" id="aiGenerateBtn">🤖 AI生成计划</button>
                <button class="btn btn-cancel" onclick="closeAICreateModal()">取消</button>
            `;
        }, 300);
    }
}

// 修改原有的addStudyPlan函数，使用新的表单
function addStudyPlan() {
    showAddPlanModal();
}
