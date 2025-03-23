/**
 * MusicGenius 曲目详情页脚本文件
 * 处理曲目详情页的交互和操作
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化MIDI可视化
    initializeMidiVisualizer();
    
    // 设置播放控制
    setupPlaybackControls();
    
    // 设置标签编辑
    setupTagsEditing();
    
    // 设置删除确认
    setupDeleteConfirmation();
    
    // 设置曲目编辑
    setupTrackEditing();
    
    // 设置曲目派生功能
    setupTrackDerivation();
});

/**
 * 初始化MIDI可视化
 */
function initializeMidiVisualizer() {
    const container = document.getElementById('midiVisualizer');
    const midiPath = container?.getAttribute('data-midi-path');
    
    if (!container || !midiPath) return;
    
    // 清空容器
    container.innerHTML = '<div class="text-center py-3"><i class="fas fa-spinner fa-spin me-2"></i>加载MIDI可视化...</div>';
    
    // 初始化可视化工具
    setTimeout(() => {
        const visualizer = new MidiVisualizer('midiVisualizer');
        visualizer.loadMidiFromUrl(midiPath)
            .then(() => {
                console.log('MIDI可视化加载完成');
                document.getElementById('visualizerLoading')?.classList.add('d-none');
            })
            .catch(error => {
                console.error('MIDI可视化加载失败:', error);
                container.innerHTML = '<div class="text-center py-3 text-danger"><i class="fas fa-exclamation-circle me-2"></i>MIDI可视化加载失败</div>';
            });
    }, 500);
}

/**
 * 设置播放控制
 */
function setupPlaybackControls() {
    const playButton = document.getElementById('playTrackBtn');
    const trackPath = playButton?.getAttribute('data-track-path');
    
    if (!playButton || !trackPath) return;
    
    let audio = null;
    
    // 播放按钮点击事件
    playButton.addEventListener('click', function() {
        if (!audio) {
            audio = new Audio(trackPath);
            audio.addEventListener('ended', function() {
                playButton.innerHTML = '<i class="fas fa-play me-2"></i>播放';
                updatePlaybackProgress(0);
            });
            
            // 设置进度更新
            audio.addEventListener('timeupdate', function() {
                if (audio.duration) {
                    const progress = (audio.currentTime / audio.duration) * 100;
                    updatePlaybackProgress(progress);
                }
            });
        }
        
        if (audio.paused) {
            audio.play();
            playButton.innerHTML = '<i class="fas fa-pause me-2"></i>暂停';
        } else {
            audio.pause();
            playButton.innerHTML = '<i class="fas fa-play me-2"></i>播放';
        }
    });
    
    // 进度条控制
    const progressBar = document.getElementById('playbackProgress');
    if (progressBar) {
        progressBar.addEventListener('click', function(e) {
            if (!audio || !audio.duration) return;
            
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const clickPercent = x / rect.width;
            
            // 设置播放位置
            audio.currentTime = clickPercent * audio.duration;
            updatePlaybackProgress(clickPercent * 100);
        });
    }
}

/**
 * 更新播放进度
 * @param {number} progress - 进度百分比 (0-100)
 */
function updatePlaybackProgress(progress) {
    const progressBar = document.getElementById('playbackProgressBar');
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
    
    const progressText = document.getElementById('playbackProgressText');
    if (progressText) {
        progressText.textContent = `${Math.round(progress)}%`;
    }
}

/**
 * 设置标签编辑
 */
function setupTagsEditing() {
    const tagsForm = document.getElementById('tagsForm');
    const addTagBtn = document.getElementById('addTagBtn');
    const tagInput = document.getElementById('newTagInput');
    const tagsList = document.getElementById('tagsList');
    const trackId = tagsForm?.getAttribute('data-track-id');
    
    if (!tagsForm || !addTagBtn || !tagInput || !tagsList || !trackId) return;
    
    // 添加标签按钮点击事件
    addTagBtn.addEventListener('click', function() {
        const tagValue = tagInput.value.trim();
        if (!tagValue) return;
        
        addTag(tagValue, trackId);
        tagInput.value = '';
    });
    
    // 标签输入框回车事件
    tagInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTagBtn.click();
        }
    });
    
    // 初始化删除标签按钮
    document.querySelectorAll('.tag-delete-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tag = this.getAttribute('data-tag');
            removeTag(tag, trackId);
        });
    });
}

/**
 * 添加标签
 * @param {string} tag - 标签文本
 * @param {string} trackId - 曲目ID
 */
function addTag(tag, trackId) {
    fetch(`/track/${trackId}/add_tag`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tag: tag })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('添加标签失败');
        }
        return response.json();
    })
    .then(data => {
        // 添加新标签到UI
        const tagsList = document.getElementById('tagsList');
        const newTag = document.createElement('span');
        newTag.className = 'badge bg-secondary me-2 mb-2 tag-badge p-2';
        newTag.innerHTML = `
            ${tag}
            <button type="button" class="btn-close btn-close-white ms-2 tag-delete-btn" 
                data-tag="${tag}" aria-label="删除">
            </button>
        `;
        
        const deleteBtn = newTag.querySelector('.tag-delete-btn');
        deleteBtn.addEventListener('click', function() {
            removeTag(tag, trackId);
        });
        
        tagsList.appendChild(newTag);
        
        // 显示成功消息
        showToast('添加标签', data.message, 'success');
    })
    .catch(error => {
        console.error('添加标签错误:', error);
        showToast('添加失败', error.message, 'danger');
    });
}

/**
 * 移除标签
 * @param {string} tag - 标签文本
 * @param {string} trackId - 曲目ID
 */
function removeTag(tag, trackId) {
    fetch(`/track/${trackId}/remove_tag`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tag: tag })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('移除标签失败');
        }
        return response.json();
    })
    .then(data => {
        // 从UI中移除标签
        const tagElements = document.querySelectorAll('.tag-badge');
        tagElements.forEach(el => {
            const tagText = el.textContent.trim();
            if (tagText === tag) {
                el.remove();
            }
        });
        
        // 显示成功消息
        showToast('移除标签', data.message, 'success');
    })
    .catch(error => {
        console.error('移除标签错误:', error);
        showToast('移除失败', error.message, 'danger');
    });
}

/**
 * 设置删除确认
 */
function setupDeleteConfirmation() {
    const deleteButton = document.getElementById('deleteTrackBtn');
    const trackId = deleteButton?.getAttribute('data-track-id');
    
    if (!deleteButton || !trackId) return;
    
    // 删除按钮点击事件
    deleteButton.addEventListener('click', function() {
        if (confirm('确定要删除此曲目吗？此操作无法撤销。')) {
            deleteTrack(trackId);
        }
    });
}

/**
 * 删除曲目
 * @param {string} trackId - 曲目ID
 */
function deleteTrack(trackId) {
    fetch(`/delete_track/${trackId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('删除曲目失败');
        }
        return response.json();
    })
    .then(data => {
        // 显示成功消息
        showToast('删除成功', data.message, 'success');
        
        // 重定向到音乐库页面
        setTimeout(() => {
            window.location.href = '/library';
        }, 1000);
    })
    .catch(error => {
        console.error('删除错误:', error);
        showToast('删除失败', error.message, 'danger');
    });
}

/**
 * 设置曲目编辑
 */
function setupTrackEditing() {
    const editForm = document.getElementById('editTrackForm');
    const trackId = editForm?.getAttribute('data-track-id');
    
    if (!editForm || !trackId) return;
    
    // 提交编辑表单
    editForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const title = document.getElementById('editTitle').value;
        const artist = document.getElementById('editArtist').value;
        const genre = document.getElementById('editGenre').value;
        
        if (!title) {
            showToast('验证错误', '标题不能为空', 'warning');
            return;
        }
        
        // 显示加载状态
        const submitButton = document.getElementById('saveEditBtn');
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>保存中...';
        submitButton.disabled = true;
        
        // 提交编辑
        fetch(`/track/${trackId}/edit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                artist: artist,
                genre: genre
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('更新曲目信息失败');
            }
            return response.json();
        })
        .then(data => {
            // 更新页面上的曲目信息
            document.querySelector('h1.track-title').textContent = title;
            
            const artistDisplay = document.querySelector('.track-artist');
            if (artistDisplay) {
                artistDisplay.textContent = artist || '未知艺术家';
            }
            
            const genreDisplay = document.querySelector('.track-genre');
            if (genreDisplay) {
                genreDisplay.textContent = genre || '未分类';
            }
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('editTrackModal'));
            modal.hide();
            
            // 显示成功消息
            showToast('更新成功', data.message, 'success');
        })
        .catch(error => {
            console.error('更新错误:', error);
            showToast('更新失败', error.message, 'danger');
        })
        .finally(() => {
            // 恢复按钮状态
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        });
    });
}

/**
 * 设置曲目派生功能
 */
function setupTrackDerivation() {
    const createAccompanimentBtn = document.getElementById('createAccompanimentBtn');
    const transferStyleBtn = document.getElementById('transferStyleBtn');
    const applyEffectsBtn = document.getElementById('applyEffectsBtn');
    
    // 生成伴奏按钮
    if (createAccompanimentBtn) {
        const trackId = createAccompanimentBtn.getAttribute('data-track-id');
        
        createAccompanimentBtn.addEventListener('click', function() {
            window.location.href = `/create?generate_accompaniment=${trackId}`;
        });
    }
    
    // 风格迁移按钮
    if (transferStyleBtn) {
        const trackId = transferStyleBtn.getAttribute('data-track-id');
        
        transferStyleBtn.addEventListener('click', function() {
            window.location.href = `/create?transfer_style=${trackId}`;
        });
    }
    
    // 应用音频特效按钮
    if (applyEffectsBtn) {
        const trackId = applyEffectsBtn.getAttribute('data-track-id');
        
        applyEffectsBtn.addEventListener('click', function() {
            window.location.href = `/create?apply_effects=${trackId}`;
        });
    }
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