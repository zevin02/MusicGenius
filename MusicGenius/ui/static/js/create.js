/**
 * MusicGenius 创作页面脚本
 * 处理音乐创作相关功能的前端交互
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有标签页
    initializeAllTabs();
    
    // 设置各功能模块
    setupMelodyGeneration();
    setupStyleTransfer();
    setupAudioEffects();
    setupAccompanimentGeneration();
    setupTrackMerging();
    setupLibrarySaving();
    
    // 处理URL参数
    initializeFromUrlParams();
});

/**
 * 初始化所有标签页
 */
function initializeAllTabs() {
    const tabLinks = document.querySelectorAll('.nav-link[data-bs-toggle="tab"]');
    
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetTab = this.getAttribute('href');
            
            // 保存当前活动标签页到会话存储
            sessionStorage.setItem('activeCreationTab', targetTab);
            
            // 如果切换到可视化组件，可能需要调整尺寸
            if (targetTab === '#visualization-tab') {
                // 通知可视化组件调整尺寸
                if (window.midiVisualizer) {
                    setTimeout(() => window.midiVisualizer.resize(), 100);
                }
            }
        });
    });
    
    // 恢复上次活动的标签页
    const activeTab = sessionStorage.getItem('activeCreationTab');
    if (activeTab) {
        const tabElement = document.querySelector(`.nav-link[href="${activeTab}"]`);
        if (tabElement) {
            const tab = new bootstrap.Tab(tabElement);
            tab.show();
        }
    }
}

/**
 * 设置旋律生成功能
 */
function setupMelodyGeneration() {
    const melodyForm = document.getElementById('melodyGenerationForm');
    
    if (!melodyForm) return;

    // 确保事件处理程序只绑定一次
    melodyForm.removeEventListener('submit', handleSubmit); // 移除之前的事件处理程序
    melodyForm.addEventListener('submit', handleSubmit); // 绑定新的事件处理程序
}

function handleSubmit(e) {
    e.preventDefault();  // 阻止默认提交行为

    // 获取表单数据
    const formData = new FormData(this); // 使用 this 获取表单数据

    // 更新UI状态
    const submitButton = this.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.disabled = true;  // 禁用按钮
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>生成中...';

    // 显示进度条
    const progressContainer = document.getElementById('melodyProgressContainer');
    if (progressContainer) {
        progressContainer.classList.remove('d-none');
    }

    // 发送API请求
    fetch('/generate_melody', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // 更新UI状态
        submitButton.disabled = false;  // 请求完成后启用按钮
        submitButton.innerHTML = originalText;

        // 隐藏进度条
        if (progressContainer) {
            progressContainer.classList.add('d-none');
        }

        if (data.success) {
            // 显示结果区域
            const resultSection = document.getElementById('melodyResultSection');
            if (resultSection) {
                resultSection.classList.remove('d-none');
            }

            // 更新下载链接
            const downloadLink = document.getElementById('melodyDownloadLink');
            if (downloadLink) {
                downloadLink.href = data.output_file;
            }

            // 设置播放按钮
            setupMidiPlayer('melodyPlayButton', data.output_file);

            // 初始化MIDI可视化
            initializeMidiVisualizer('melodyVisualizer', data.output_file);

            // 设置保存到库按钮
            setupSaveToLibrary('melodySaveToLibraryButton', data.output_file);

            // 显示成功消息
            showToast('旋律生成成功', '您的旋律已生成，您可以播放、下载或保存到音乐库', 'success');
        } else {
            // 显示错误消息
            // showToast('生成失败', data.error || '生成旋律时发生错误', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        submitButton.disabled = false;  // 请求失败后启用按钮
        submitButton.innerHTML = originalText;

        if (progressContainer) {
            progressContainer.classList.add('d-none');
        }

        showToast('错误', '请求处理失败，请稍后再试', 'error');
    });
}

/**
 * 设置风格迁移功能
 */
function setupStyleTransfer() {
    const styleForm = document.getElementById('styleTransferForm');
    
    if (!styleForm) return;
    
    styleForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 获取表单数据
        const formData = new FormData(styleForm);
        
        // 检查必要文件
        const sourceFile = styleForm.querySelector('input[name="source_file"]').files[0];
        if (!sourceFile && !formData.get('source_track_id')) {
            showToast('错误', '请选择源MIDI文件或从音乐库选择曲目', 'error');
            return;
        }
        
        // 更新UI状态
        const submitButton = styleForm.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>处理中...';
        
        // 显示进度条
        const progressContainer = document.getElementById('styleProgressContainer');
        if (progressContainer) {
            progressContainer.classList.remove('d-none');
        }
        
        // 发送API请求
        fetch('/transfer_style', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // 更新UI状态
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
            
            // 隐藏进度条
            if (progressContainer) {
                progressContainer.classList.add('d-none');
            }
            
            if (data.success) {
                // 显示结果区域
                const resultSection = document.getElementById('styleResultSection');
                if (resultSection) {
                    resultSection.classList.remove('d-none');
                }
                
                // 更新下载链接
                const downloadLink = document.getElementById('styleDownloadLink');
                if (downloadLink) {
                    downloadLink.href = data.output_file;
                }
                
                // 设置播放按钮
                setupMidiPlayer('stylePlayButton', data.output_file);
                
                // 初始化MIDI可视化
                initializeMidiVisualizer('styleVisualizer', data.output_file);
                
                // 设置保存到库按钮
                setupSaveToLibrary('styleSaveToLibraryButton', data.output_file);
                
                // 显示成功消息
                showToast('风格迁移成功', '风格迁移已完成，您可以播放、下载或保存到音乐库', 'success');
            } else {
                // 显示错误消息
                showToast('处理失败', data.error || '风格迁移时发生错误', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
            
            if (progressContainer) {
                progressContainer.classList.add('d-none');
            }
            
            showToast('错误', '请求处理失败，请稍后再试', 'error');
        });
    });
}

/**
 * 设置音频特效功能
 */
function setupAudioEffects() {
    const effectsForm = document.getElementById('audioEffectsForm');
    
    if (!effectsForm) return;
    
    // 初始化滑块显示值
    effectsForm.querySelectorAll('input[type="range"]').forEach(slider => {
        const valueDisplay = document.getElementById(`${slider.id}Value`);
        if (valueDisplay) {
            valueDisplay.textContent = slider.value;
        }
        
        slider.addEventListener('input', function() {
            if (valueDisplay) {
                valueDisplay.textContent = this.value;
            }
        });
    });
    
    // 处理特效激活状态
    effectsForm.querySelectorAll('.effect-toggle').forEach(toggle => {
        toggle.addEventListener('change', function() {
            const effectId = this.getAttribute('data-effect-id');
            const sliders = document.querySelectorAll(`.effect-slider[data-effect-id="${effectId}"]`);
            
            sliders.forEach(slider => {
                const sliderContainer = slider.closest('.mb-3');
                if (this.checked) {
                    sliderContainer.classList.remove('disabled');
                    slider.disabled = false;
                } else {
                    sliderContainer.classList.add('disabled');
                    slider.disabled = true;
                }
            });
        });
        
        // 初始状态
        toggle.dispatchEvent(new Event('change'));
    });
    
    effectsForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 获取表单数据
        const formData = new FormData(effectsForm);
        
        // 检查必要文件
        const sourceFile = effectsForm.querySelector('input[name="source_file"]').files[0];
        if (!sourceFile && !formData.get('source_track_id')) {
            showToast('错误', '请选择源MIDI文件或从音乐库选择曲目', 'error');
            return;
        }
        
        // 更新UI状态
        const submitButton = effectsForm.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>处理中...';
        
        // 显示进度条
        const progressContainer = document.getElementById('effectsProgressContainer');
        if (progressContainer) {
            progressContainer.classList.remove('d-none');
        }
        
        // 发送API请求
        fetch('/apply_effects', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // 更新UI状态
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
            
            // 隐藏进度条
            if (progressContainer) {
                progressContainer.classList.add('d-none');
            }
            
            if (data.success) {
                // 显示结果区域
                const resultSection = document.getElementById('effectsResultSection');
                if (resultSection) {
                    resultSection.classList.remove('d-none');
                }
                
                // 更新下载链接
                const downloadLink = document.getElementById('effectsDownloadLink');
                if (downloadLink) {
                    downloadLink.href = data.output_file;
                }
                
                // 音频特效可能会生成音频文件而不是MIDI
                if (data.output_type === 'audio') {
                    // 设置音频播放器
                    setupAudioPlayer('effectsPlayButton', data.output_file);
                    
                    // 初始化波形图
                    initializeWaveform('effectsVisualizer', data.output_file);
                } else {
                    // 设置MIDI播放器
                    setupMidiPlayer('effectsPlayButton', data.output_file);
                    
                    // 初始化MIDI可视化
                    initializeMidiVisualizer('effectsVisualizer', data.output_file);
                }
                
                // 设置保存到库按钮
                setupSaveToLibrary('effectsSaveToLibraryButton', data.output_file);
                
                // 显示成功消息
                showToast('音频特效已应用', '特效处理已完成，您可以播放、下载或保存到音乐库', 'success');
            } else {
                // 显示错误消息
                showToast('处理失败', data.error || '应用音频特效时发生错误', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
            
            if (progressContainer) {
                progressContainer.classList.add('d-none');
            }
            
            showToast('错误', '请求处理失败，请稍后再试', 'error');
        });
    });
}

/**
 * 设置伴奏生成功能
 */
function setupAccompanimentGeneration() {
    const accompanimentForm = document.getElementById('accompanimentForm');
    
    if (!accompanimentForm) return;
    
    accompanimentForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 获取表单数据
        const formData = new FormData(accompanimentForm);
        
        // 检查必要文件
        const melodyFile = accompanimentForm.querySelector('input[name="melody_file"]').files[0];
        if (!melodyFile && !formData.get('melody_track_id')) {
            showToast('错误', '请选择旋律MIDI文件或从音乐库选择曲目', 'error');
            return;
        }
        
        // 更新UI状态
        const submitButton = accompanimentForm.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>生成中...';
        
        // 显示进度条
        const progressContainer = document.getElementById('accompanimentProgressContainer');
        if (progressContainer) {
            progressContainer.classList.remove('d-none');
        }
        
        // 发送API请求
        fetch('/generate_accompaniment', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // 更新UI状态
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
            
            // 隐藏进度条
            if (progressContainer) {
                progressContainer.classList.add('d-none');
            }
            
            if (data.success) {
                // 显示结果区域
                const resultSection = document.getElementById('accompanimentResultSection');
                if (resultSection) {
                    resultSection.classList.remove('d-none');
                }
                
                // 更新下载链接
                const downloadLink = document.getElementById('accompanimentDownloadLink');
                if (downloadLink) {
                    downloadLink.href = data.output_file;
                }
                
                // 设置播放按钮
                setupMidiPlayer('accompanimentPlayButton', data.output_file);
                
                // 初始化MIDI可视化
                initializeMidiVisualizer('accompanimentVisualizer', data.output_file);
                
                // 设置保存到库按钮
                setupSaveToLibrary('accompanimentSaveToLibraryButton', data.output_file);
                
                // 显示成功消息
                showToast('伴奏生成成功', '伴奏已生成，您可以播放、下载或保存到音乐库', 'success');
            } else {
                // 显示错误消息
                showToast('生成失败', data.error || '生成伴奏时发生错误', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
            
            if (progressContainer) {
                progressContainer.classList.add('d-none');
            }
            
            showToast('错误', '请求处理失败，请稍后再试', 'error');
        });
    });
}

/**
 * 设置轨道合并功能
 */
function setupTrackMerging() {
    const mergeForm = document.getElementById('trackMergingForm');
    const trackContainer = document.getElementById('trackFilesContainer');
    const addTrackButton = document.getElementById('addTrackButton');
    
    if (!mergeForm || !trackContainer || !addTrackButton) return;
    
    // 添加轨道输入
    let trackCount = 1;
    
    addTrackButton.addEventListener('click', function() {
        trackCount++;
        
        const trackRow = document.createElement('div');
        trackRow.className = 'track-row mb-3';
        trackRow.innerHTML = `
            <div class="input-group">
                <span class="input-group-text">轨道 ${trackCount}</span>
                <input type="file" class="form-control" name="track_files[]" accept=".mid,.midi">
                <button type="button" class="btn btn-outline-danger remove-track-btn">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        trackContainer.appendChild(trackRow);
        
        // 添加删除按钮事件
        trackRow.querySelector('.remove-track-btn').addEventListener('click', function() {
            trackContainer.removeChild(trackRow);
        });
    });
    
    mergeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 获取表单数据
        const formData = new FormData(mergeForm);
        
        // 检查是否至少有两个轨道
        const trackFiles = mergeForm.querySelectorAll('input[name="track_files[]"]');
        let fileCount = 0;
        
        trackFiles.forEach(input => {
            if (input.files.length > 0) {
                fileCount++;
            }
        });
        
        if (fileCount < 2) {
            showToast('错误', '请至少选择两个MIDI文件进行合并', 'error');
            return;
        }
        
        // 更新UI状态
        const submitButton = mergeForm.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>合并中...';
        
        // 显示进度条
        const progressContainer = document.getElementById('mergeProgressContainer');
        if (progressContainer) {
            progressContainer.classList.remove('d-none');
        }
        
        // 发送API请求
        fetch('/merge_tracks', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // 更新UI状态
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
            
            // 隐藏进度条
            if (progressContainer) {
                progressContainer.classList.add('d-none');
            }
            
            if (data.success) {
                // 显示结果区域
                const resultSection = document.getElementById('mergeResultSection');
                if (resultSection) {
                    resultSection.classList.remove('d-none');
                }
                
                // 更新下载链接
                const downloadLink = document.getElementById('mergeDownloadLink');
                if (downloadLink) {
                    downloadLink.href = data.output_file;
                }
                
                // 设置播放按钮
                setupMidiPlayer('mergePlayButton', data.output_file);
                
                // 初始化MIDI可视化
                initializeMidiVisualizer('mergeVisualizer', data.output_file);
                
                // 设置保存到库按钮
                setupSaveToLibrary('mergeSaveToLibraryButton', data.output_file);
                
                // 显示成功消息
                showToast('轨道合并成功', '轨道已合并，您可以播放、下载或保存到音乐库', 'success');
            } else {
                // 显示错误消息
                showToast('合并失败', data.error || '合并轨道时发生错误', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
            
            if (progressContainer) {
                progressContainer.classList.add('d-none');
            }
            
            showToast('错误', '请求处理失败，请稍后再试', 'error');
        });
    });
}

/**
 * 设置保存到音乐库功能
 */
function setupLibrarySaving() {
    const saveButtons = document.querySelectorAll('[id$="SaveToLibraryButton"]');
    
    saveButtons.forEach(button => {
        // 初始状态为禁用
        button.disabled = true;
    });
}

/**
 * 设置保存到音乐库的按钮
 * @param {string} buttonId - 按钮ID
 * @param {string} filepath - 文件路径
 */
function setupSaveToLibrary(buttonId, filepath) {
    const saveButton = document.getElementById(buttonId);
    
    if (!saveButton) return;
    
    // 启用按钮
    saveButton.disabled = false;
    
    saveButton.addEventListener('click', function() {
        // 显示保存对话框
        const saveModal = document.getElementById('saveToLibraryModal');
        if (saveModal) {
            const bsModal = new bootstrap.Modal(saveModal);
            
            // 设置文件路径
            const filePathInput = saveModal.querySelector('input[name="filepath"]');
            if (filePathInput) {
                filePathInput.value = filepath;
            }
            
            bsModal.show();
        }
    });
}

/**
 * 初始化MIDI可视化组件
 * @param {string} containerId - 容器ID
 * @param {string} midiUrl - MIDI文件URL
 */
function initializeMidiVisualizer(containerId, midiUrl) {
    const container = document.getElementById(containerId);
    
    if (!container) return;
    
    // 如果存在旧的可视化组件，清除它
    container.innerHTML = '';
    
    // 创建可视化组件
    const visualizer = new MidiVisualizer(containerId, {
        height: 250,
        noteColor: '#6200ea',
        backgroundColor: '#1a1a1a',
        gridColor: '#333333'
    });
    
    // 加载MIDI文件
    visualizer.loadMidiFromUrl(midiUrl);
    
    // 保存引用
    window.midiVisualizer = visualizer;
}

/**
 * 初始化波形图组件
 * @param {string} containerId - 容器ID
 * @param {string} audioUrl - 音频文件URL
 */
function initializeWaveform(containerId, audioUrl) {
    const container = document.getElementById(containerId);
    
    if (!container) return;
    
    // 如果存在旧的波形图，清除它
    container.innerHTML = '';
    
    // 创建波形图元素
    const waveform = document.createElement('div');
    waveform.className = 'waveform-display';
    container.appendChild(waveform);
    
    // 使用wavesurfer.js或类似库显示波形图
    // 这里需要引入wavesurfer.js库
    if (window.WaveSurfer) {
        const wavesurfer = WaveSurfer.create({
            container: waveform,
            waveColor: '#6200ea',
            progressColor: '#03dac6',
            cursorColor: '#f5f5f5',
            barWidth: 2,
            barRadius: 3,
            responsive: true,
            height: 200,
            barGap: 2
        });
        
        wavesurfer.load(audioUrl);
    }
}

/**
 * 设置MIDI播放器
 * @param {string} buttonId - 按钮ID
 * @param {string} midiUrl - MIDI文件URL
 */
function setupMidiPlayer(buttonId, midiUrl) {
    const playButton = document.getElementById(buttonId);
    
    if (!playButton) return;
    
    playButton.addEventListener('click', function() {
        // 如果有全局播放器实例，停止它
        if (window.currentPlayer) {
            window.currentPlayer.stop();
        }
        
        // 如果可视化组件可用，使用它来播放
        if (window.midiVisualizer) {
            window.midiVisualizer.play();
        }
    });
}

/**
 * 设置音频播放器
 * @param {string} buttonId - 按钮ID
 * @param {string} audioUrl - 音频文件URL
 */
function setupAudioPlayer(buttonId, audioUrl) {
    const playButton = document.getElementById(buttonId);
    
    if (!playButton) return;
    
    // 创建音频元素
    const audio = new Audio(audioUrl);
    
    playButton.addEventListener('click', function() {
        if (audio.paused) {
            audio.play();
            playButton.innerHTML = '<i class="fas fa-pause"></i>';
        } else {
            audio.pause();
            playButton.innerHTML = '<i class="fas fa-play"></i>';
        }
    });
    
    audio.addEventListener('ended', function() {
        playButton.innerHTML = '<i class="fas fa-play"></i>';
    });
    
    // 保存引用
    window.currentPlayer = audio;
}

/**
 * 从URL参数初始化页面状态
 */
function initializeFromUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // 风格迁移源
    const styleSource = urlParams.get('style_source');
    if (styleSource) {
        const styleSourceInput = document.querySelector('input[name="source_track_id"]');
        if (styleSourceInput) {
            styleSourceInput.value = styleSource;
            
            // 切换到风格迁移标签
            const styleTab = document.querySelector('[href="#style-transfer-tab"]');
            if (styleTab) {
                const tab = new bootstrap.Tab(styleTab);
                tab.show();
            }
        }
    }
    
    // 应用特效
    const applyEffects = urlParams.get('apply_effects');
    if (applyEffects) {
        const effectsInput = document.querySelector('input[name="source_track_id"]');
        if (effectsInput) {
            effectsInput.value = applyEffects;
            
            // 切换到音频特效标签
            const effectsTab = document.querySelector('[href="#audio-effects-tab"]');
            if (effectsTab) {
                const tab = new bootstrap.Tab(effectsTab);
                tab.show();
            }
        }
    }
    
    // 生成伴奏
    const generateAccompaniment = urlParams.get('generate_accompaniment');
    if (generateAccompaniment) {
        const accompanimentInput = document.querySelector('input[name="melody_track_id"]');
        if (accompanimentInput) {
            accompanimentInput.value = generateAccompaniment;
            
            // 切换到伴奏生成标签
            const accompanimentTab = document.querySelector('[href="#accompaniment-tab"]');
            if (accompanimentTab) {
                const tab = new bootstrap.Tab(accompanimentTab);
                tab.show();
            }
        }
    }
}

/**
 * 显示消息提示
 * @param {string} title - 提示标题
 * @param {string} message - 提示内容
 * @param {string} type - 提示类型：success, error, warning, info
 */
function showToast(title, message, type = 'info') {
    // 获取类型对应的颜色和图标
    let bgClass = 'bg-info';
    let icon = 'info-circle';
    
    switch (type) {
        case 'success':
            bgClass = 'bg-success';
            icon = 'check-circle';
            break;
        case 'error':
            bgClass = 'bg-danger';
            icon = 'exclamation-circle';
            break;
        case 'warning':
            bgClass = 'bg-warning';
            icon = 'exclamation-triangle';
            break;
    }
    
    // 创建Toast元素
    const toastElement = document.createElement('div');
    toastElement.className = `toast align-items-center ${bgClass} text-white border-0`;
    toastElement.setAttribute('role', 'alert');
    toastElement.setAttribute('aria-live', 'assertive');
    toastElement.setAttribute('aria-atomic', 'true');
    
    toastElement.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${icon} me-2"></i>
                <strong>${title}</strong>: ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // 添加到容器
    let toastContainer = document.querySelector('.toast-container');
    
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.appendChild(toastElement);
    
    // 初始化Toast
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    
    toast.show();
} 