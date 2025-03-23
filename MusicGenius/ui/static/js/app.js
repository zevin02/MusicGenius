/**
 * MusicGenius Web应用客户端JavaScript
 */

// 当文档加载完成时执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('MusicGenius应用已加载');
    
    // 注册所有表单提交事件监听器
    registerFormListeners();
    
    // 给所有音频播放器添加事件监听器
    setupAudioPlayers();
});

/**
 * 为所有创作表单注册事件监听器
 */
function registerFormListeners() {
    // 旋律生成表单
    const melodyForm = document.getElementById('melody-form');
    if (melodyForm) {
        melodyForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const container = document.getElementById('melody-form-container');
            
            try {
                showMessage(container, '正在生成旋律...');
                
                const formData = new FormData(melodyForm);
                const response = await fetch('/generate_melody', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error('生成旋律失败');
                }
                
                const data = await response.json();
                showMessage(container, '旋律生成成功！');
                showAudioPlayer(container, data.audio_url);
                
            } catch (error) {
                showMessage(container, error.message, true);
            }
        });
    }
    
    // 风格迁移表单
    const styleForm = document.getElementById('style-form');
    if (styleForm) {
        styleForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const container = document.getElementById('style-form-container');
            
            try {
                showMessage(container, '正在转换风格...');
                
                const formData = new FormData(styleForm);
                const response = await fetch('/transfer_style', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error('风格转换失败');
                }
                
                const data = await response.json();
                showMessage(container, '风格转换成功！');
                showAudioPlayer(container, data.audio_url);
                
            } catch (error) {
                showMessage(container, error.message, true);
            }
        });
    }
    
    // 伴奏生成表单
    const accompanimentForm = document.getElementById('accompaniment-form');
    if (accompanimentForm) {
        accompanimentForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const container = document.getElementById('accompaniment-form-container');
            
            try {
                showMessage(container, '正在生成伴奏...');
                
                const formData = new FormData(accompanimentForm);
                const response = await fetch('/generate_accompaniment', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error('生成伴奏失败');
                }
                
                const data = await response.json();
                showMessage(container, '伴奏生成成功！');
                showAudioPlayer(container, data.audio_url);
                
            } catch (error) {
                showMessage(container, error.message, true);
            }
        });
    }
    
    // 效果处理表单
    const effectsForm = document.getElementById('effects-form');
    if (effectsForm) {
        effectsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitFormWithAjax(this, '/apply_effects', handleEffectsResponse);
        });
    }
    
    // 轨道合并表单
    const mergeForm = document.getElementById('merge-form');
    if (mergeForm) {
        mergeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitFormWithAjax(this, '/merge_tracks', handleMergeResponse);
        });
    }
}

/**
 * 使用AJAX提交表单数据
 * @param {HTMLFormElement} form 表单元素
 * @param {string} endpoint 提交端点
 * @param {Function} callback 回调函数
 */
function submitFormWithAjax(form, endpoint, callback) {
    // 显示加载动画
    showLoading(form);
    
    // 收集表单数据
    const formData = new FormData(form);
    
    // 发送AJAX请求
    fetch(endpoint, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // 隐藏加载动画
        hideLoading(form);
        
        // 调用回调函数处理响应
        if (callback) {
            callback(data, form);
        }
    })
    .catch(error => {
        console.error('请求错误:', error);
        hideLoading(form);
        showError(form, '提交请求时出现错误，请稍后再试');
    });
}

/**
 * 处理旋律生成响应
 * @param {Object} response 服务器响应
 * @param {HTMLFormElement} form 表单元素
 */
function handleMelodyResponse(response, form) {
    if (response.success) {
        showSuccess(form, response.message);
        
        // 更新音频播放器
        updateAudioPlayer('melody-player', response.output_file);
        
        // 显示下载按钮
        showDownloadButton(form.querySelector('.result-section'), response.output_file);
    } else {
        showError(form, response.message || '生成旋律失败');
    }
}

/**
 * 处理风格迁移响应
 * @param {Object} response 服务器响应
 * @param {HTMLFormElement} form 表单元素
 */
function handleStyleResponse(response, form) {
    if (response.success) {
        showSuccess(form, response.message);
        
        // 更新音频播放器
        updateAudioPlayer('style-player', response.output_file);
        
        // 显示下载按钮
        showDownloadButton(form.querySelector('.result-section'), response.output_file);
    } else {
        showError(form, response.message || '风格迁移失败');
    }
}

/**
 * 处理伴奏生成响应
 * @param {Object} response 服务器响应
 * @param {HTMLFormElement} form 表单元素
 */
function handleAccompResponse(response, form) {
    if (response.success) {
        showSuccess(form, response.message);
        
        // 更新音频播放器
        updateAudioPlayer('accompaniment-player', response.output_file);
        
        // 显示下载按钮
        showDownloadButton(form.querySelector('.result-section'), response.output_file);
    } else {
        showError(form, response.message || '生成伴奏失败');
    }
}

/**
 * 处理效果处理响应
 * @param {Object} response 服务器响应
 * @param {HTMLFormElement} form 表单元素
 */
function handleEffectsResponse(response, form) {
    if (response.success) {
        showSuccess(form, response.message);
        
        // 更新音频播放器
        updateAudioPlayer('effects-player', response.output_file);
        
        // 显示下载按钮
        showDownloadButton(form.querySelector('.result-section'), response.output_file);
    } else {
        showError(form, response.message || '应用效果失败');
    }
}

/**
 * 处理轨道合并响应
 * @param {Object} response 服务器响应
 * @param {HTMLFormElement} form 表单元素
 */
function handleMergeResponse(response, form) {
    if (response.success) {
        showSuccess(form, response.message);
        
        // 更新音频播放器
        updateAudioPlayer('merge-player', response.output_file);
        
        // 显示下载按钮
        showDownloadButton(form.querySelector('.result-section'), response.output_file);
    } else {
        showError(form, response.message || '合并轨道失败');
    }
}

/**
 * 设置音频播放器
 */
function setupAudioPlayers() {
    // 查找所有音频播放器
    const players = document.querySelectorAll('.audio-player');
    
    players.forEach(player => {
        // 添加事件监听器
        const audio = player.querySelector('audio');
        const playBtn = player.querySelector('.play-btn');
        
        if (audio && playBtn) {
            playBtn.addEventListener('click', function() {
                if (audio.paused) {
                    audio.play();
                    this.textContent = '暂停';
                } else {
                    audio.pause();
                    this.textContent = '播放';
                }
            });
            
            // 监听播放结束事件
            audio.addEventListener('ended', function() {
                playBtn.textContent = '播放';
            });
        }
    });
}

/**
 * 更新音频播放器源
 * @param {string} playerId 播放器ID
 * @param {string} audioFile 音频文件路径
 */
function updateAudioPlayer(playerId, audioFile) {
    const player = document.getElementById(playerId);
    if (!player) return;
    
    const audio = player.querySelector('audio');
    if (audio) {
        audio.src = audioFile;
        player.style.display = 'block';
    }
}

/**
 * 显示下载按钮
 * @param {HTMLElement} container 容器元素
 * @param {string} filePath 文件路径
 */
function showDownloadButton(container, filePath) {
    if (!container) return;
    
    // 创建或更新下载按钮
    let downloadBtn = container.querySelector('.download-btn');
    
    if (!downloadBtn) {
        downloadBtn = document.createElement('a');
        downloadBtn.className = 'btn download-btn';
        downloadBtn.textContent = '下载';
        container.appendChild(downloadBtn);
    }
    
    downloadBtn.href = filePath;
    downloadBtn.style.display = 'inline-block';
}

/**
 * 显示加载动画
 * @param {HTMLElement} container 容器元素
 */
function showLoading(container) {
    const submitBtn = container.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span> 处理中...';
    }
}

/**
 * 隐藏加载动画
 * @param {HTMLElement} container 容器元素
 */
function hideLoading(container) {
    const submitBtn = container.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = submitBtn.getAttribute('data-original-text') || '提交';
    }
}

/**
 * 显示成功消息
 * @param {HTMLElement} container 容器元素
 * @param {string} message 消息内容
 */
function showSuccess(container, message) {
    showMessage(container, message, 'success');
}

/**
 * 显示错误消息
 * @param {HTMLElement} container 容器元素
 * @param {string} message 消息内容
 */
function showError(container, message) {
    showMessage(container, message, true);
}

/**
 * 显示消息
 * @param {HTMLElement} container 容器元素
 * @param {string} message 消息内容
 * @param {boolean} isError 是否为错误消息
 */
function showMessage(container, message, isError = false) {
    const messageDiv = container.querySelector('.message');
    messageDiv.textContent = message;
    messageDiv.style.display = 'block';
    messageDiv.className = `message ${isError ? 'error' : ''}`;
}

function hideMessage(container) {
    const messageDiv = container.querySelector('.message');
    messageDiv.style.display = 'none';
}

function showAudioPlayer(container, audioUrl) {
    const player = container.querySelector('.audio-player');
    const audio = player.querySelector('audio');
    audio.src = audioUrl;
    player.style.display = 'block';
} 