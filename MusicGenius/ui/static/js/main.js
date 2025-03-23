/**
 * MusicGenius 主页脚本文件
 * 处理首页的交互和统计数据
 */

document.addEventListener('DOMContentLoaded', function() {
    // 获取统计数据和可用风格的动画
    animateNumbers();
    
    // 初始化工具提示
    initializeTooltips();
    
    // 处理导航高亮
    highlightCurrentNav();
});

/**
 * 为统计数字添加从0到目标值的动画效果
 */
function animateNumbers() {
    const statsElements = document.querySelectorAll('[id$="Count"], [id$="Total"]');
    
    statsElements.forEach(element => {
        const finalValue = parseInt(element.textContent, 10);
        if (!isNaN(finalValue)) {
            let startValue = 0;
            const duration = 1500; // 动画持续时间（毫秒）
            const frameDuration = 1000 / 60; // 60fps
            const totalFrames = Math.round(duration / frameDuration);
            const increment = finalValue / totalFrames;
            
            let currentFrame = 0;
            
            const counter = setInterval(() => {
                currentFrame++;
                const value = Math.round(increment * currentFrame);
                
                if (currentFrame === totalFrames) {
                    element.textContent = finalValue;
                    clearInterval(counter);
                } else {
                    element.textContent = value;
                }
            }, frameDuration);
        }
    });
}

/**
 * 初始化Bootstrap工具提示
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * 高亮当前页面的导航项
 */
function highlightCurrentNav() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath) {
            link.classList.add('active');
        } else if (currentPath.includes('/track/') && href.includes('/library')) {
            // 特殊情况：在曲目详情页面时高亮"音乐库"导航项
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

/**
 * 处理演示功能的点击事件
 */
document.querySelectorAll('.demo-feature').forEach(button => {
    button.addEventListener('click', function(e) {
        e.preventDefault();
        const featureType = this.getAttribute('data-feature');
        
        // 显示功能演示信息
        showFeatureDemo(featureType);
    });
});

/**
 * 显示功能演示信息
 * @param {string} featureType - 功能类型
 */
function showFeatureDemo(featureType) {
    const demoMessages = {
        'melody': '旋律生成功能可以基于您的偏好创建原创音乐',
        'style': '风格迁移功能可以将您的音乐转换为不同音乐流派的风格',
        'effects': '音频特效可以为您的音乐添加专业级的音效处理',
        'accompaniment': '伴奏生成可以为您的旋律自动创建和声与配乐'
    };
    
    const message = demoMessages[featureType] || '请在创作中心体验此功能';
    
    // 创建提示框
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-primary border-0 fade show';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // 添加到文档中
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        container.appendChild(toast);
    } else {
        toastContainer.appendChild(toast);
    }
    
    // 初始化Bootstrap提示框
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 3000
    });
    
    // 显示提示框
    bsToast.show();
}

/**
 * 页面滚动效果
 */
window.addEventListener('scroll', function() {
    const scrollPosition = window.scrollY;
    const navbar = document.querySelector('.navbar');
    
    if (scrollPosition > 50) {
        navbar.classList.add('navbar-shrink');
    } else {
        navbar.classList.remove('navbar-shrink');
    }
}); 