/**
 * MusicGenius MIDI可视化工具
 * 提供在网页上展示MIDI文件内容的可视化功能
 */

class MidiVisualizer {
    /**
     * 创建MIDI可视化实例
     * @param {string} containerId - 可视化容器的DOM ID
     * @param {Object} options - 配置选项
     */
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`找不到ID为${containerId}的容器元素`);
            return;
        }
        
        // 默认配置
        this.options = {
            noteHeight: 8,
            noteSpacing: 1,
            pixelsPerTimeStep: 30,
            noteColors: {
                default: '#6200ea', // 主色调为紫色
                drums: '#ff6d00',    // 鼓点为橙色
                bass: '#2979ff'      // 低音为蓝色
            },
            backgroundColor: '#1a1a1a',
            timeScale: 1.0,
            ...options
        };
        
        // 初始化属性
        this.midiData = null;
        this.synth = null;
        this.isPlaying = false;
        this.currentTimeMs = 0;
        this.animationFrameId = null;
        this.startTime = 0;
        
        // 初始化可视化区域
        this._initVisualization();
    }
    
    /**
     * 初始化可视化区域
     * @private
     */
    _initVisualization() {
        // 清空容器
        this.container.innerHTML = '';
        this.container.style.backgroundColor = this.options.backgroundColor;
        this.container.style.position = 'relative';
        this.container.style.overflow = 'hidden';
        
        // 创建画布
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.container.clientWidth;
        this.canvas.height = this.container.clientHeight;
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = 0;
        this.canvas.style.left = 0;
        this.container.appendChild(this.canvas);
        
        // 获取绘图上下文
        this.ctx = this.canvas.getContext('2d');
        
        // 创建播放指示线
        this.playLine = document.createElement('div');
        this.playLine.className = 'play-line';
        this.playLine.style.position = 'absolute';
        this.playLine.style.width = '2px';
        this.playLine.style.height = '100%';
        this.playLine.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        this.playLine.style.left = '20%';
        this.playLine.style.top = 0;
        this.playLine.style.zIndex = 2;
        this.container.appendChild(this.playLine);
        
        // 创建信息显示层
        this.infoLayer = document.createElement('div');
        this.infoLayer.className = 'info-layer';
        this.infoLayer.style.position = 'absolute';
        this.infoLayer.style.bottom = '10px';
        this.infoLayer.style.left = '10px';
        this.infoLayer.style.color = 'rgba(255, 255, 255, 0.7)';
        this.infoLayer.style.fontSize = '12px';
        this.infoLayer.style.zIndex = 3;
        this.container.appendChild(this.infoLayer);
        
        // 添加调整大小事件监听
        window.addEventListener('resize', () => this._handleResize());
    }
    
    /**
     * 处理窗口大小调整
     * @private
     */
    _handleResize() {
        this.canvas.width = this.container.clientWidth;
        this.canvas.height = this.container.clientHeight;
        
        if (this.midiData) {
            this._renderMidi();
        }
    }
    
    /**
     * 从URL加载MIDI文件
     * @param {string} url - MIDI文件URL
     * @returns {Promise} - 加载完成的Promise
     */
    loadMidiFromUrl(url) {
        return new Promise((resolve, reject) => {
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`无法加载MIDI文件: ${response.statusText}`);
                    }
                    return response.arrayBuffer();
                })
                .then(arrayBuffer => {
                    this._processMidiArrayBuffer(arrayBuffer);
                    resolve();
                })
                .catch(error => {
                    console.error('加载MIDI文件失败:', error);
                    this._showError('无法加载MIDI文件');
                    reject(error);
                });
        });
    }
    
    /**
     * 从文件加载MIDI数据
     * @param {File} file - MIDI文件对象
     * @returns {Promise} - 加载完成的Promise
     */
    loadMidiFromFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                try {
                    this._processMidiArrayBuffer(e.target.result);
                    resolve();
                } catch (error) {
                    console.error('处理MIDI文件失败:', error);
                    this._showError('无法解析MIDI文件');
                    reject(error);
                }
            };
            
            reader.onerror = (e) => {
                console.error('读取MIDI文件失败:', e);
                this._showError('读取文件失败');
                reject(e);
            };
            
            reader.readAsArrayBuffer(file);
        });
    }
    
    /**
     * 处理MIDI ArrayBuffer数据
     * @param {ArrayBuffer} buffer - MIDI文件的ArrayBuffer数据
     * @private
     */
    _processMidiArrayBuffer(buffer) {
        try {
            // 使用Tone.js的Midi对象解析MIDI文件
            // 注意：实际实现中需要引入Tone.js库
            this.midiData = new Tone.Midi(buffer);
            
            // 初始化合成器
            this._initSynth();
            
            // 渲染MIDI数据
            this._renderMidi();
            
            // 显示MIDI信息
            this._updateInfoLayer();
            
            // 重置播放状态
            this.currentTimeMs = 0;
            this.isPlaying = false;
            
        } catch (error) {
            console.error('处理MIDI数据失败:', error);
            this._showError('无法解析MIDI数据');
            throw error;
        }
    }
    
    /**
     * 初始化音频合成器
     * @private
     */
    _initSynth() {
        // 实际实现中需要使用Tone.js创建真实的合成器
        // 这里仅为示例代码框架
        this.synth = {}; // 替换为实际的Tone.js合成器
    }
    
    /**
     * 渲染MIDI数据到画布
     * @private
     */
    _renderMidi() {
        if (!this.midiData || !this.ctx) return;
        
        // 清空画布
        this.ctx.fillStyle = this.options.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        const tracks = this.midiData.tracks;
        if (!tracks || tracks.length === 0) {
            this._showError('MIDI文件不包含任何轨道');
            return;
        }
        
        // 计算MIDI数据的总时长（毫秒）
        const totalDuration = this.midiData.duration * 1000;
        
        // 计算可见区域
        const playLinePosition = parseFloat(this.playLine.style.left) / 100;
        const visibleWidth = this.canvas.width;
        const totalWidth = totalDuration * this.options.pixelsPerTimeStep / 1000 * this.options.timeScale;
        
        // 计算偏移量，使播放线在合适的位置
        const offset = playLinePosition * visibleWidth - (this.currentTimeMs / totalDuration) * totalWidth;
        
        // 绘制网格线
        this._drawGrid(totalWidth, offset);
        
        // 为每个轨道绘制音符
        tracks.forEach((track, trackIndex) => {
            this._drawTrack(track, trackIndex, totalWidth, offset);
        });
    }
    
    /**
     * 绘制背景网格
     * @param {number} totalWidth - 总宽度
     * @param {number} offset - X轴偏移量
     * @private
     */
    _drawGrid(totalWidth, offset) {
        // 绘制水平网格线（代表音高）
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        this.ctx.lineWidth = 1;
        
        // 每个八度音阶绘制一条线
        for (let note = 0; note <= 127; note += 12) {
            const y = this.canvas.height - (note * (this.options.noteHeight + this.options.noteSpacing));
            if (y >= 0 && y <= this.canvas.height) {
                this.ctx.beginPath();
                this.ctx.moveTo(0, y);
                this.ctx.lineTo(this.canvas.width, y);
                this.ctx.stroke();
            }
        }
        
        // 绘制垂直网格线（代表时间）
        const secondWidth = this.options.pixelsPerTimeStep * this.options.timeScale;
        const secondCount = Math.ceil(totalWidth / secondWidth);
        
        for (let i = 0; i <= secondCount; i++) {
            const x = i * secondWidth + offset;
            if (x >= 0 && x <= this.canvas.width) {
                this.ctx.beginPath();
                this.ctx.moveTo(x, 0);
                this.ctx.lineTo(x, this.canvas.height);
                this.ctx.stroke();
            }
        }
    }
    
    /**
     * 绘制单个MIDI轨道
     * @param {Object} track - MIDI轨道数据
     * @param {number} trackIndex - 轨道索引
     * @param {number} totalWidth - 总宽度
     * @param {number} offset - X轴偏移量
     * @private
     */
    _drawTrack(track, trackIndex, totalWidth, offset) {
        // 根据轨道类型选择颜色
        let noteColor = this.options.noteColors.default;
        
        // 根据轨道名称或通道检测特殊类型轨道
        const trackName = track.name.toLowerCase();
        const channel = track.channel;
        
        if (channel === 9 || trackName.includes('drum') || trackName.includes('percussion')) {
            noteColor = this.options.noteColors.drums;
        } else if (trackName.includes('bass') || trackName.includes('低音')) {
            noteColor = this.options.noteColors.bass;
        }
        
        // 绘制每个音符
        track.notes.forEach(note => {
            // 计算音符位置和大小
            const x = (note.time * 1000 * this.options.pixelsPerTimeStep / 1000 * this.options.timeScale) + offset;
            const y = this.canvas.height - (note.midi * (this.options.noteHeight + this.options.noteSpacing));
            const width = note.duration * 1000 * this.options.pixelsPerTimeStep / 1000 * this.options.timeScale;
            const height = this.options.noteHeight;
            
            // 确保音符在可见区域内
            if (x + width >= 0 && x <= this.canvas.width && y + height >= 0 && y <= this.canvas.height) {
                // 绘制音符矩形
                this.ctx.fillStyle = noteColor;
                this.ctx.fillRect(x, y, Math.max(2, width), height);
                
                // 为音符添加边框
                this.ctx.strokeStyle = 'rgba(0, 0, 0, 0.3)';
                this.ctx.lineWidth = 1;
                this.ctx.strokeRect(x, y, Math.max(2, width), height);
            }
        });
    }
    
    /**
     * 更新信息显示层
     * @private
     */
    _updateInfoLayer() {
        if (!this.midiData) return;
        
        const { tracks, name, duration } = this.midiData;
        const trackCount = tracks.length;
        const totalNotes = tracks.reduce((sum, track) => sum + track.notes.length, 0);
        
        const durationFormatted = this._formatTime(duration);
        
        this.infoLayer.innerHTML = `
            <div>${name || 'Unnamed MIDI'} | ${trackCount}个轨道 | ${totalNotes}个音符 | 时长: ${durationFormatted}</div>
        `;
    }
    
    /**
     * 格式化时间为分钟:秒
     * @param {number} timeInSeconds - 秒数
     * @returns {string} 格式化后的时间
     * @private
     */
    _formatTime(timeInSeconds) {
        const minutes = Math.floor(timeInSeconds / 60);
        const seconds = Math.floor(timeInSeconds % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
    
    /**
     * 显示错误信息
     * @param {string} message - 错误信息
     * @private
     */
    _showError(message) {
        // 清空画布
        this.ctx.fillStyle = this.options.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 显示错误信息
        this.ctx.fillStyle = '#ff5252';
        this.ctx.font = '16px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(message, this.canvas.width / 2, this.canvas.height / 2);
        
        // 更新信息层
        this.infoLayer.innerHTML = `<div class="error">${message}</div>`;
    }
    
    /**
     * 播放MIDI
     */
    play() {
        if (!this.midiData || this.isPlaying) return;
        
        this.isPlaying = true;
        this.startTime = Date.now() - this.currentTimeMs;
        
        // 开始动画
        this._animate();
        
        // 初始化并播放合成器（实际播放需要使用Tone.js）
        // 此处仅为框架示例
        console.log('播放MIDI');
    }
    
    /**
     * 暂停MIDI播放
     */
    pause() {
        if (!this.isPlaying) return;
        
        this.isPlaying = false;
        this.currentTimeMs = Date.now() - this.startTime;
        
        // 取消动画
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
        
        // 暂停合成器（实际暂停需要使用Tone.js）
        // 此处仅为框架示例
        console.log('暂停MIDI');
    }
    
    /**
     * 停止MIDI播放并重置位置
     */
    stop() {
        this.pause();
        this.currentTimeMs = 0;
        this._renderMidi();
        
        // 停止合成器（实际停止需要使用Tone.js）
        // 此处仅为框架示例
        console.log('停止MIDI');
    }
    
    /**
     * 跳转到指定时间位置
     * @param {number} timeMs - 目标时间（毫秒）
     */
    seekTo(timeMs) {
        const duration = this.midiData ? this.midiData.duration * 1000 : 0;
        this.currentTimeMs = Math.max(0, Math.min(timeMs, duration));
        
        if (this.isPlaying) {
            this.startTime = Date.now() - this.currentTimeMs;
        }
        
        this._renderMidi();
    }
    
    /**
     * 动画帧更新函数
     * @private
     */
    _animate() {
        if (!this.isPlaying) return;
        
        // 计算当前时间
        this.currentTimeMs = Date.now() - this.startTime;
        
        // 检查是否播放完成
        const duration = this.midiData ? this.midiData.duration * 1000 : 0;
        if (this.currentTimeMs >= duration) {
            this.stop();
            return;
        }
        
        // 重新渲染
        this._renderMidi();
        
        // 请求下一帧
        this.animationFrameId = requestAnimationFrame(() => this._animate());
    }
    
    /**
     * 设置播放速度
     * @param {number} speed - 播放速度（1.0为正常速度）
     */
    setPlaybackSpeed(speed) {
        this.options.timeScale = 1 / speed;
        this._renderMidi();
        
        // 更新播放状态
        if (this.isPlaying) {
            this.pause();
            this.play();
        }
    }
}

// 如果在浏览器环境中，将类暴露给全局
if (typeof window !== 'undefined') {
    window.MidiVisualizer = MidiVisualizer;
}

// 如果在Node.js环境中，导出类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MidiVisualizer;
} 