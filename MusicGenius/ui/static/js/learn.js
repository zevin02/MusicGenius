/**
 * MusicGenius 学习中心脚本文件
 * 处理学习页面的交互和模型训练相关操作
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化标签页
    initializeTabs();
    
    // 设置旋律模型训练
    setupMelodyModelTraining();
    
    // 设置风格学习
    setupStyleLearning();
    
    // 设置训练进度显示
    setupProgressTracking();
});

/**
 * 初始化标签页
 */
function initializeTabs() {
    // 为滑块控件添加值更新功能
    document.querySelectorAll('input[type="range"]').forEach(slider => {
        const valueSpan = document.getElementById(`${slider.id}Value`);
        if (valueSpan) {
            valueSpan.textContent = slider.value;
            
            slider.addEventListener('input', function() {
                valueSpan.textContent = this.value;
            });
        }
    });
}

/**
 * 设置旋律模型训练
 */
function setupMelodyModelTraining() {
    const melodyForm = document.getElementById('melodyModelForm');
    if (!melodyForm) return;
    
    // 文件选择器变化时更新所选文件显示
    const fileInput = document.getElementById('melodyTrainingFiles');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileCount = this.files.length;
            const fileListContainer = document.getElementById('melodySelectedFilesList');
            
            if (fileListContainer) {
                if (fileCount > 0) {
                    let html = '<ul class="list-group mt-2">';
                    for (let i = 0; i < fileCount; i++) {
                        const file = this.files[i];
                        html += `
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                <span><i class="fas fa-file-audio me-2"></i>${file.name}</span>
                                <span class="badge bg-secondary rounded-pill">${(file.size / 1024).toFixed(1)} KB</span>
                            </li>
                        `;
                    }
                    html += '</ul>';
                    fileListContainer.innerHTML = html;
                } else {
                    fileListContainer.innerHTML = '';
                }
            }
        });
    }
    
    // 表单提交
    melodyForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 获取表单数据
        const files = document.getElementById('melodyTrainingFiles').files;
        const epochs = document.getElementById('melodyEpochs').value;
        const learningRate = document.getElementById('melodyLearningRate').value;
        const batchSize = document.getElementById('melodyBatchSize').value;
        const modelName = document.getElementById('melodyModelName').value;
        
        if (files.length === 0) {
            showToast('训练错误', '请选择至少一个MIDI文件作为训练数据', 'warning');
            return;
        }
        
        if (!modelName) {
            showToast('训练错误', '请输入模型名称', 'warning');
            return;
        }
        
        // 显示加载状态
        const trainButton = document.getElementById('trainMelodyBtn');
        const originalText = trainButton.innerHTML;
        trainButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>准备训练...';
        trainButton.disabled = true;
        
        // 创建FormData
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('training_files', files[i]);
        }
        formData.append('epochs', epochs);
        formData.append('learning_rate', learningRate);
        formData.append('batch_size', batchSize);
        formData.append('model_name', modelName);
        
        // 显示训练进度区域
        const progressArea = document.getElementById('melodyTrainingProgress');
        progressArea.classList.remove('d-none');
        const progressBar = document.getElementById('melodyProgressBar');
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', 0);
        progressBar.textContent = '0%';
        
        document.getElementById('melodyTrainingStatus').textContent = '准备训练数据...';
        
        // 调用API开始训练
        fetch('/train_melody_model', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('训练请求失败');
            }
            return response.json();
        })
        .then(data => {
            // 保存训练任务ID，用于轮询进度
            if (data.task_id) {
                startProgressPolling('melody', data.task_id);
                
                document.getElementById('melodyTrainingStatus').textContent = '训练已开始，这可能需要一些时间...';
                
                // 显示训练消息
                showToast('训练开始', data.message, 'success');
            } else {
                throw new Error('没有获取到训练任务ID');
            }
        })
        .catch(error => {
            console.error('训练错误:', error);
            document.getElementById('melodyTrainingStatus').textContent = '训练失败: ' + error.message;
            showToast('训练失败', error.message, 'danger');
            
            // 恢复按钮状态
            trainButton.innerHTML = originalText;
            trainButton.disabled = false;
        });
    });
}

/**
 * 设置风格学习
 */
function setupStyleLearning() {
    const styleForm = document.getElementById('styleModelForm');
    if (!styleForm) return;
    
    // 文件选择器变化时更新所选文件显示
    const fileInput = document.getElementById('styleTrainingFiles');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileCount = this.files.length;
            const fileListContainer = document.getElementById('styleSelectedFilesList');
            
            if (fileListContainer) {
                if (fileCount > 0) {
                    let html = '<ul class="list-group mt-2">';
                    for (let i = 0; i < fileCount; i++) {
                        const file = this.files[i];
                        html += `
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                <span><i class="fas fa-file-audio me-2"></i>${file.name}</span>
                                <span class="badge bg-secondary rounded-pill">${(file.size / 1024).toFixed(1)} KB</span>
                            </li>
                        `;
                    }
                    html += '</ul>';
                    fileListContainer.innerHTML = html;
                } else {
                    fileListContainer.innerHTML = '';
                }
            }
        });
    }
    
    // 表单提交
    styleForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 获取表单数据
        const files = document.getElementById('styleTrainingFiles').files;
        const epochs = document.getElementById('styleEpochs').value;
        const learningRate = document.getElementById('styleLearningRate').value;
        const styleModelName = document.getElementById('styleModelName').value;
        const styleDescription = document.getElementById('styleDescription').value;
        
        if (files.length === 0) {
            showToast('学习错误', '请选择至少一个MIDI文件作为风格样本', 'warning');
            return;
        }
        
        if (!styleModelName) {
            showToast('学习错误', '请输入风格名称', 'warning');
            return;
        }
        
        // 显示加载状态
        const learnButton = document.getElementById('learnStyleBtn');
        const originalText = learnButton.innerHTML;
        learnButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>准备学习...';
        learnButton.disabled = true;
        
        // 创建FormData
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('style_files', files[i]);
        }
        formData.append('epochs', epochs);
        formData.append('learning_rate', learningRate);
        formData.append('style_name', styleModelName);
        formData.append('description', styleDescription);
        
        // 显示训练进度区域
        const progressArea = document.getElementById('styleTrainingProgress');
        progressArea.classList.remove('d-none');
        const progressBar = document.getElementById('styleProgressBar');
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', 0);
        progressBar.textContent = '0%';
        
        document.getElementById('styleTrainingStatus').textContent = '准备风格数据...';
        
        // 调用API开始学习风格
        fetch('/learn_style', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('风格学习请求失败');
            }
            return response.json();
        })
        .then(data => {
            // 保存训练任务ID，用于轮询进度
            if (data.task_id) {
                startProgressPolling('style', data.task_id);
                
                document.getElementById('styleTrainingStatus').textContent = '风格学习已开始，这可能需要一些时间...';
                
                // 显示学习消息
                showToast('学习开始', data.message, 'success');
            } else {
                throw new Error('没有获取到学习任务ID');
            }
        })
        .catch(error => {
            console.error('学习错误:', error);
            document.getElementById('styleTrainingStatus').textContent = '学习失败: ' + error.message;
            showToast('学习失败', error.message, 'danger');
            
            // 恢复按钮状态
            learnButton.innerHTML = originalText;
            learnButton.disabled = false;
        });
    });
}

/**
 * 设置进度跟踪
 */
function setupProgressTracking() {
    // 这里设置全局变量，用于存储轮询间隔ID
    window.progressIntervals = {
        melody: null,
        style: null
    };
}

/**
 * 开始轮询进度
 * @param {string} taskType - 任务类型（melody 或 style）
 * @param {string} taskId - 任务ID
 */
function startProgressPolling(taskType, taskId) {
    // 清除之前可能存在的轮询
    if (window.progressIntervals[taskType]) {
        clearInterval(window.progressIntervals[taskType]);
    }
    
    // 设置轮询间隔
    window.progressIntervals[taskType] = setInterval(() => {
        pollTrainingProgress(taskType, taskId);
    }, 3000); // 每3秒轮询一次
}

/**
 * 轮询训练进度
 * @param {string} taskType - 任务类型（melody 或 style）
 * @param {string} taskId - 任务ID
 */
function pollTrainingProgress(taskType, taskId) {
    const endpoint = taskType === 'melody' ? '/train_melody_model' : '/learn_style';
    
    fetch(`${endpoint}/progress/${taskId}`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('获取进度失败');
        }
        return response.json();
    })
    .then(data => {
        // 更新进度条和状态
        updateProgressUI(taskType, data);
        
        // 如果任务完成或失败，停止轮询
        if (['completed', 'failed'].includes(data.status)) {
            clearInterval(window.progressIntervals[taskType]);
            window.progressIntervals[taskType] = null;
            
            // 恢复按钮状态
            const buttonId = taskType === 'melody' ? 'trainMelodyBtn' : 'learnStyleBtn';
            const buttonText = taskType === 'melody' ? '开始训练' : '开始学习';
            const button = document.getElementById(buttonId);
            
            if (button) {
                button.innerHTML = `<i class="fas fa-play me-2"></i>${buttonText}`;
                button.disabled = false;
            }
            
            // 显示完成或失败消息
            if (data.status === 'completed') {
                showToast(
                    taskType === 'melody' ? '训练完成' : '学习完成', 
                    data.message, 
                    'success'
                );
                
                // 添加"使用此模型"按钮
                const modelLink = document.createElement('a');
                modelLink.href = '/create' + (taskType === 'melody' ? '' : '?style_source=' + data.model_id);
                modelLink.className = 'btn btn-success mt-3';
                modelLink.innerHTML = `<i class="fas fa-magic me-2"></i>使用此${taskType === 'melody' ? '模型' : '风格'}`;
                
                const progressArea = document.getElementById(`${taskType}TrainingProgress`);
                progressArea.appendChild(modelLink);
            } else {
                showToast(
                    taskType === 'melody' ? '训练失败' : '学习失败', 
                    data.message, 
                    'danger'
                );
            }
        }
    })
    .catch(error => {
        console.error('获取进度错误:', error);
        document.getElementById(`${taskType}TrainingStatus`).textContent = '获取进度失败: ' + error.message;
    });
}

/**
 * 更新进度UI
 * @param {string} taskType - 任务类型（melody 或 style）
 * @param {Object} data - 进度数据
 */
function updateProgressUI(taskType, data) {
    const progressBar = document.getElementById(`${taskType}ProgressBar`);
    const statusText = document.getElementById(`${taskType}TrainingStatus`);
    
    if (!progressBar || !statusText) return;
    
    // 更新进度条
    const progress = data.progress !== undefined ? Math.round(data.progress * 100) : 0;
    progressBar.style.width = `${progress}%`;
    progressBar.setAttribute('aria-valuenow', progress);
    progressBar.textContent = `${progress}%`;
    
    // 更新状态文本
    switch (data.status) {
        case 'initializing':
            statusText.textContent = '初始化中...';
            break;
        case 'preprocessing':
            statusText.textContent = '预处理数据...';
            break;
        case 'training':
            statusText.textContent = `训练中: 第 ${data.current_epoch}/${data.total_epochs} 轮, 损失: ${data.loss ? data.loss.toFixed(4) : 'N/A'}`;
            break;
        case 'completed':
            statusText.textContent = `训练完成! 总共耗时: ${formatTime(data.elapsed_time)}`;
            break;
        case 'failed':
            statusText.textContent = `训练失败: ${data.error || '未知错误'}`;
            break;
        default:
            statusText.textContent = data.message || '正在处理...';
    }
    
    // 如果有详细日志，更新日志区域
    if (data.logs) {
        const logArea = document.getElementById(`${taskType}TrainingLogs`);
        if (logArea) {
            logArea.textContent = data.logs;
            logArea.scrollTop = logArea.scrollHeight; // 滚动到底部
        }
    }
}

/**
 * 格式化时间（秒数转换为可读格式）
 * @param {number} seconds - 秒数
 * @returns {string} - 格式化后的时间
 */
function formatTime(seconds) {
    if (seconds === undefined || seconds === null) return 'N/A';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    let result = '';
    if (hours > 0) result += `${hours}小时`;
    if (minutes > 0) result += `${minutes}分钟`;
    if (remainingSeconds > 0 || result === '') result += `${remainingSeconds}秒`;
    
    return result;
}

/**
 * 显示toast消息
 * @param {string} title - 消息标题
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型（success, danger, warning等）
 */
function showToast(title, message, type) {
    // 查找或创建toasts容器
    let toastContainer = document.querySelector('.toast-container');
    
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // 创建toast元素
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="关闭"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // 初始化并显示toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    
    // 在toast隐藏后移除元素
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
    
    toast.show();
} 