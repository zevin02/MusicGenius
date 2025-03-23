/**
 * MusicGenius 音乐库页面脚本
 * 处理音乐库页面的交互和功能
 */

document.addEventListener('DOMContentLoaded', function() {
    // 设置搜索和筛选功能
    setupSearchAndFilter();
    
    // 设置音轨操作按钮
    setupTrackOperations();
    
    // 设置文件导入功能
    setupFileImport();
    
    // 设置排序功能
    setupSorting();
    
    // 设置分页功能
    setupPagination();
});

/**
 * 设置搜索和筛选功能
 */
function setupSearchAndFilter() {
    const searchForm = document.getElementById('searchForm');
    
    if (!searchForm) return;
    
    // 获取表单元素
    const queryInput = document.getElementById('query');
    const genreSelect = document.getElementById('genre');
    const tagSelect = document.getElementById('tag');
    
    // 添加输入事件，实现实时搜索
    let searchTimeout;
    
    function debounceSearch() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performSearch();
        }, 300);
    }
    
    if (queryInput) {
        queryInput.addEventListener('input', debounceSearch);
    }
    
    // 添加选择事件，实现筛选
    if (genreSelect) {
        genreSelect.addEventListener('change', () => {
            performSearch();
        });
    }
    
    if (tagSelect) {
        tagSelect.addEventListener('change', () => {
            performSearch();
        });
    }
    
    // 表单提交事件
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        performSearch();
    });
}

/**
 * 执行搜索
 */
function performSearch() {
    const searchForm = document.getElementById('searchForm');
    
    if (!searchForm) return;
    
    // 获取表单数据
    const formData = new FormData(searchForm);
    const query = formData.get('query') || '';
    const genre = formData.get('genre') || '';
    const tag = formData.get('tag') || '';
    const page = formData.get('page') || 1;
    
    // 构建查询字符串
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (genre) params.append('genre', genre);
    if (tag) params.append('tag', tag);
    if (page > 1) params.append('page', page);
    
    // 显示加载状态
    const tableBody = document.querySelector('tbody');
    if (tableBody) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4">
                    <i class="fas fa-spinner fa-spin me-2"></i>正在搜索...
                </td>
            </tr>
        `;
    }
    
    // 发送API请求
    fetch(`/library?${params.toString()}&format=json`)
        .then(response => response.json())
        .then(data => {
            // 更新界面
            updateResultsList(data.tracks, data.total);
            
            // 更新分页
            if (data.pagination) {
                updatePagination(data.pagination.current_page, data.pagination.total_pages);
            }
            
            // 更新URL，但不刷新页面
            const url = new URL(window.location);
            url.search = params.toString();
            window.history.pushState({}, '', url);
        })
        .catch(error => {
            console.error('Search error:', error);
            if (tableBody) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center py-4 text-danger">
                            <i class="fas fa-exclamation-circle me-2"></i>搜索出错: ${error.message}
                        </td>
                    </tr>
                `;
            }
        });
}

/**
 * 更新结果列表
 * @param {Array} tracks - 曲目数组
 * @param {number} totalResults - 结果总数
 */
function updateResultsList(tracks, totalResults) {
    const tableBody = document.querySelector('tbody');
    const resultsContainer = document.querySelector('.card-body');
    
    if (!tableBody || !resultsContainer) return;
    
    if (tracks && tracks.length > 0) {
        // 有结果，更新表格
        tableBody.innerHTML = '';
        
        tracks.forEach(track => {
            const row = document.createElement('tr');
            row.dataset.trackId = track.id;
            
            // 格式化标签
            const tagsHtml = track.tags && track.tags.length > 0
                ? track.tags.map(tag => `<span class="badge bg-secondary">${tag}</span>`).join(' ')
                : '<span class="text-muted">无标签</span>';
            
            // 格式化日期
            const date = new Date(track.created_at);
            const formattedDate = `${date.getFullYear()}-${(date.getMonth()+1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
            
            row.innerHTML = `
                <td>
                    <a href="/track/${track.id}" class="fw-bold text-decoration-none">
                        ${track.title}
                    </a>
                </td>
                <td>${track.artist || '未知'}</td>
                <td>
                    ${track.genre 
                        ? `<span class="badge bg-primary">${track.genre}</span>` 
                        : '<span class="text-muted">未分类</span>'}
                </td>
                <td>${tagsHtml}</td>
                <td>${formattedDate}</td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline-success play-track-btn" data-track-path="${track.filepath}">
                            <i class="fas fa-play"></i>
                        </button>
                        <a href="${track.filepath}" download class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-download"></i>
                        </a>
                        <button class="btn btn-sm btn-outline-danger delete-track-btn" data-track-id="${track.id}" data-track-title="${track.title}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            
            tableBody.appendChild(row);
        });
        
        // 重新设置音轨操作
        setupTrackOperations();
    } else {
        // 无结果
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4">
                    <i class="fas fa-music fa-2x text-muted mb-3"></i>
                    <p>未找到符合条件的曲目</p>
                </td>
            </tr>
        `;
    }
    
    // 更新结果数量
    const countElement = document.querySelector('.card-header h4');
    if (countElement) {
        countElement.textContent = `曲目 (${totalResults})`;
    }
}

/**
 * 设置音轨操作按钮
 */
function setupTrackOperations() {
    // 播放按钮
    document.querySelectorAll('.play-track-btn').forEach(button => {
        button.addEventListener('click', function() {
            const trackPath = this.getAttribute('data-track-path');
            playTrack(trackPath, this);
        });
    });
    
    // 删除按钮
    document.querySelectorAll('.delete-track-btn').forEach(button => {
        button.addEventListener('click', function() {
            const trackId = this.getAttribute('data-track-id');
            const trackTitle = this.getAttribute('data-track-title');
            prepareTrackDeletion(trackId, trackTitle);
        });
    });
}

/**
 * 准备删除音轨
 * @param {number} trackId - 音轨ID
 * @param {string} trackTitle - 音轨标题
 */
function prepareTrackDeletion(trackId, trackTitle) {
    const modal = document.getElementById('deleteTrackModal');
    if (!modal) return;
    
    // 更新模态框内容
    const titleSpan = document.getElementById('deleteTrackTitle');
    if (titleSpan) {
        titleSpan.textContent = trackTitle;
    }
    
    // 设置确认按钮事件
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (confirmBtn) {
        // 清除之前的事件
        const newBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);
        
        // 设置新事件
        newBtn.addEventListener('click', function() {
            deleteTrack(trackId);
        });
    }
    
    // 显示模态框
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
}

/**
 * 删除音轨
 * @param {number} trackId - 音轨ID
 */
function deleteTrack(trackId) {
    // 发送删除请求
    fetch(`/delete_track/${trackId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        // 隐藏模态框
        const modal = document.getElementById('deleteTrackModal');
        if (modal) {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            modalInstance.hide();
        }
        
        if (data.success) {
            // 移除表格行
            const row = document.querySelector(`tr[data-track-id="${trackId}"]`);
            if (row) {
                row.classList.add('fade-out');
                setTimeout(() => {
                    row.remove();
                    
                    // 更新计数
                    const countElement = document.querySelector('.card-header h4');
                    if (countElement) {
                        const currentCount = parseInt(countElement.textContent.match(/\d+/)[0], 10);
                        countElement.textContent = `曲目 (${currentCount - 1})`;
                    }
                    
                    // 如果表格为空，显示无结果消息
                    const rows = document.querySelectorAll('tbody tr');
                    if (rows.length === 0) {
                        const tableBody = document.querySelector('tbody');
                        if (tableBody) {
                            tableBody.innerHTML = `
                                <tr>
                                    <td colspan="6" class="text-center py-4">
                                        <i class="fas fa-music fa-2x text-muted mb-3"></i>
                                        <p>音乐库中暂无曲目</p>
                                    </td>
                                </tr>
                            `;
                        }
                    }
                }, 300);
            }
            
            // 显示成功消息
            showToast('删除成功', '曲目已成功删除', 'success');
        } else {
            // 显示错误消息
            showToast('删除失败', data.error || '删除曲目时发生错误', 'error');
        }
    })
    .catch(error => {
        console.error('Delete error:', error);
        showToast('删除错误', '请求处理失败，请稍后再试', 'error');
    });
}

/**
 * 播放音轨
 * @param {string} trackPath - 音轨路径
 * @param {Element} button - 播放按钮元素
 */
function playTrack(trackPath, button) {
    // 获取音频播放器容器
    const playerContainer = document.getElementById('audioPlayerContainer');
    const playerTitle = document.getElementById('audioPlayerTitle');
    const playBtn = document.getElementById('audioPlayerPlayBtn');
    const pauseBtn = document.getElementById('audioPlayerPauseBtn');
    const progressBar = document.getElementById('audioProgressBar');
    const currentTimeDisplay = document.getElementById('audioCurrentTime');
    const durationDisplay = document.getElementById('audioDuration');
    
    if (!playerContainer || !playerTitle || !playBtn || !pauseBtn || !progressBar) return;
    
    // 创建音频元素
    const audio = new Audio(trackPath);
    
    // 设置曲目标题
    const trackRow = button.closest('tr');
    const trackTitle = trackRow ? trackRow.querySelector('a').textContent.trim() : '正在播放';
    playerTitle.textContent = trackTitle;
    
    // 显示播放器
    playerContainer.classList.add('active');
    
    // 设置音频事件
    audio.addEventListener('loadedmetadata', function() {
        // 显示总时长
        const duration = Math.floor(audio.duration);
        const minutes = Math.floor(duration / 60);
        const seconds = duration % 60;
        durationDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    });
    
    audio.addEventListener('timeupdate', function() {
        // 更新进度条
        const progress = (audio.currentTime / audio.duration) * 100;
        progressBar.style.width = `${progress}%`;
        
        // 更新当前时间
        const currentTime = Math.floor(audio.currentTime);
        const minutes = Math.floor(currentTime / 60);
        const seconds = currentTime % 60;
        currentTimeDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    });
    
    audio.addEventListener('ended', function() {
        // 重置播放器状态
        playBtn.classList.remove('d-none');
        pauseBtn.classList.add('d-none');
    });
    
    // 设置播放/暂停按钮
    playBtn.addEventListener('click', function() {
        audio.play();
        playBtn.classList.add('d-none');
        pauseBtn.classList.remove('d-none');
    });
    
    pauseBtn.addEventListener('click', function() {
        audio.pause();
        pauseBtn.classList.add('d-none');
        playBtn.classList.remove('d-none');
    });
    
    // 设置关闭按钮
    const closeBtn = document.getElementById('audioPlayerCloseBtn');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            audio.pause();
            playerContainer.classList.remove('active');
        });
    }
    
    // 开始播放
    audio.play();
    playBtn.classList.add('d-none');
    pauseBtn.classList.remove('d-none');
    
    // 保存到全局变量，以便在切换曲目时停止当前播放
    if (window.currentAudio) {
        window.currentAudio.pause();
    }
    window.currentAudio = audio;
}

/**
 * 设置文件导入功能
 */
function setupFileImport() {
    const importForm = document.getElementById('importFilesForm');
    const confirmBtn = document.getElementById('confirmImportBtn');
    
    if (!importForm || !confirmBtn) return;
    
    confirmBtn.addEventListener('click', function() {
        // 获取表单数据
        const formData = new FormData(importForm);
        
        // 检查必填项
        const files = formData.getAll('midi_files[]');
        if (files.length === 0 || !files[0].name) {
            showToast('错误', '请选择要导入的MIDI文件', 'error');
            return;
        }
        
        // 更新按钮状态
        const originalText = confirmBtn.innerHTML;
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>导入中...';
        
        // 发送请求
        fetch('/import_files', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // 恢复按钮状态
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = originalText;
            
            // 关闭模态框
            const modal = document.getElementById('importFilesModal');
            if (modal) {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                modalInstance.hide();
            }
            
            if (data.success) {
                // 显示成功消息
                const message = `成功导入 ${data.imported_count} 个文件`;
                showToast('导入成功', message, 'success');
                
                // 刷新页面显示新导入的文件
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                // 显示错误消息
                showToast('导入失败', data.error || '导入文件时发生错误', 'error');
            }
        })
        .catch(error => {
            console.error('Import error:', error);
            
            // 恢复按钮状态
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = originalText;
            
            showToast('导入错误', '请求处理失败，请稍后再试', 'error');
        });
    });
    
    // 重置表单当模态框关闭时
    const importModal = document.getElementById('importFilesModal');
    if (importModal) {
        importModal.addEventListener('hidden.bs.modal', function() {
            importForm.reset();
        });
    }
}

/**
 * 设置排序功能
 */
function setupSorting() {
    const sortButtons = document.querySelectorAll('th[data-sort]');
    
    sortButtons.forEach(button => {
        button.addEventListener('click', function() {
            const sortField = this.getAttribute('data-sort');
            const currentOrder = this.getAttribute('data-order') || 'asc';
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            
            // 重置所有排序图标
            sortButtons.forEach(btn => {
                btn.classList.remove('sorting-asc', 'sorting-desc');
                btn.setAttribute('data-order', '');
                const icon = btn.querySelector('.sort-icon');
                if (icon) icon.className = 'sort-icon fas fa-sort';
            });
            
            // 设置当前排序状态
            this.classList.add(`sorting-${newOrder}`);
            this.setAttribute('data-order', newOrder);
            
            // 更新图标
            const icon = this.querySelector('.sort-icon');
            if (icon) {
                icon.className = `sort-icon fas fa-sort-${newOrder === 'asc' ? 'up' : 'down'}`;
            }
            
            // 获取当前表单参数
            const form = document.getElementById('searchForm');
            const formData = new FormData(form);
            
            // 添加排序参数
            formData.append('sort', sortField);
            formData.append('order', newOrder);
            
            // 执行搜索
            const params = new URLSearchParams(formData);
            window.location.href = `/library?${params.toString()}`;
        });
    });
}

/**
 * 设置分页功能
 */
function setupPagination() {
    const paginationContainer = document.querySelector('.pagination');
    
    if (!paginationContainer) return;
    
    // 添加点击事件
    paginationContainer.addEventListener('click', function(e) {
        if (e.target.tagName === 'A') {
            e.preventDefault();
            
            const page = e.target.getAttribute('data-page');
            if (!page) return;
            
            // 获取当前表单参数
            const form = document.getElementById('searchForm');
            const formData = new FormData(form);
            
            // 更新页码参数
            formData.set('page', page);
            
            // 执行搜索
            const params = new URLSearchParams(formData);
            window.location.href = `/library?${params.toString()}`;
        }
    });
}

/**
 * 更新分页组件
 * @param {number} currentPage - 当前页码
 * @param {number} totalPages - 总页数
 */
function updatePagination(currentPage, totalPages) {
    const paginationContainer = document.querySelector('.pagination');
    
    if (!paginationContainer) return;
    
    // 清空当前分页
    paginationContainer.innerHTML = '';
    
    // 只有一页时不显示分页
    if (totalPages <= 1) return;
    
    // 添加"上一页"按钮
    const prevItem = document.createElement('li');
    prevItem.className = `page-item ${currentPage <= 1 ? 'disabled' : ''}`;
    prevItem.innerHTML = `
        <a class="page-link" href="#" data-page="${currentPage - 1}" ${currentPage <= 1 ? 'tabindex="-1" aria-disabled="true"' : ''}>
            <i class="fas fa-chevron-left"></i>
        </a>
    `;
    paginationContainer.appendChild(prevItem);
    
    // 确定显示的页码范围
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    
    if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
    }
    
    // 添加页码按钮
    for (let i = startPage; i <= endPage; i++) {
        const pageItem = document.createElement('li');
        pageItem.className = `page-item ${i === currentPage ? 'active' : ''}`;
        pageItem.innerHTML = `
            <a class="page-link" href="#" data-page="${i}">${i}</a>
        `;
        paginationContainer.appendChild(pageItem);
    }
    
    // 添加"下一页"按钮
    const nextItem = document.createElement('li');
    nextItem.className = `page-item ${currentPage >= totalPages ? 'disabled' : ''}`;
    nextItem.innerHTML = `
        <a class="page-link" href="#" data-page="${currentPage + 1}" ${currentPage >= totalPages ? 'tabindex="-1" aria-disabled="true"' : ''}>
            <i class="fas fa-chevron-right"></i>
        </a>
    `;
    paginationContainer.appendChild(nextItem);
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