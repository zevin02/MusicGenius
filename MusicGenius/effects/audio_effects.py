import numpy as np
from scipy import signal
import librosa

class AudioEffects:
    """音频特效处理类，提供各种音频特效"""
    
    def __init__(self, sr=22050):
        """初始化音频特效处理器
        
        Args:
            sr (int): 采样率
        """
        self.sr = sr
    
    def apply_reverb(self, y, room_size=0.8, damping=0.5, wet_level=0.3, dry_level=0.7):
        """应用混响效果
        
        Args:
            y (ndarray): 音频数据
            room_size (float): 房间大小 (0.0-1.0)
            damping (float): 阻尼系数 (0.0-1.0)
            wet_level (float): 湿信号电平 (0.0-1.0)
            dry_level (float): 干信号电平 (0.0-1.0)
        
        Returns:
            ndarray: 处理后的音频数据
        """
        # 简化的Schroeder混响实现
        comb_filters = [0.86, 0.83, 0.80, 0.78]
        allpass_filters = [0.7, 0.6]
        
        # 转换room_size为延迟线长度的系数
        room_size_factor = 0.95 + room_size * 0.049
        
        # 延迟线长度（以样本为单位）- 跟据room_size调整
        delays = [int(self.sr * t * room_size_factor) for t in [0.0297, 0.0371, 0.0411, 0.0437]]
        allpass_delays = [int(self.sr * t) for t in [0.005, 0.0017]]
        
        # 衰减系数 - 根据damping调整
        decays = [f * (1.0 - damping * 0.15) for f in comb_filters]
        
        y_wet = np.zeros_like(y)
        
        # 应用并联梳状滤波器
        for i, (delay, decay) in enumerate(zip(delays, decays)):
            y_comb = np.zeros_like(y)
            for n in range(len(y)):
                if n >= delay:
                    y_comb[n] = y[n] + decay * y_comb[n - delay]
                else:
                    y_comb[n] = y[n]
            y_wet += y_comb / len(delays)
        
        # 应用全通滤波器
        for i, (g, delay) in enumerate(zip(allpass_filters, allpass_delays)):
            y_allpass = np.zeros_like(y_wet)
            for n in range(len(y_wet)):
                if n >= delay:
                    y_allpass[n] = g * y_wet[n] + y_wet[n - delay] - g * y_allpass[n - delay]
                else:
                    y_allpass[n] = y_wet[n]
            y_wet = y_allpass
        
        # 混合干湿信号
        return dry_level * y + wet_level * y_wet
    
    def apply_delay(self, y, delay_time=0.5, feedback=0.5, wet_level=0.5, dry_level=0.5):
        """应用延迟效果
        
        Args:
            y (ndarray): 音频数据
            delay_time (float): 延迟时间（秒）
            feedback (float): 反馈系数 (0.0-0.9)
            wet_level (float): 湿信号电平 (0.0-1.0)
            dry_level (float): 干信号电平 (0.0-1.0)
        
        Returns:
            ndarray: 处理后的音频数据
        """
        # 将延迟时间转换为样本数
        delay_samples = int(delay_time * self.sr)
        
        # 确保feedback不会导致发散
        feedback = min(0.9, max(0, feedback))
        
        # 创建输出数组
        y_out = np.zeros(len(y) + delay_samples)
        y_out[:len(y)] = y
        
        # 应用延迟和反馈
        for i in range(len(y)):
            if i + delay_samples < len(y_out):
                y_out[i + delay_samples] += feedback * y[i]
        
        # 截取输出并混合干湿信号
        y_wet = y_out[:len(y)]
        return dry_level * y + wet_level * y_wet
    
    def apply_chorus(self, y, rate=0.5, depth=0.002, wet_level=0.5, dry_level=0.5, voices=3):
        """应用合唱效果
        
        Args:
            y (ndarray): 音频数据
            rate (float): 调制率（Hz）
            depth (float): 调制深度（秒）
            wet_level (float): 湿信号电平 (0.0-1.0)
            dry_level (float): 干信号电平 (0.0-1.0)
            voices (int): 合唱声部数量
        
        Returns:
            ndarray: 处理后的音频数据
        """
        # 将深度转换为样本数
        depth_samples = int(depth * self.sr)
        
        # 创建输出数组
        y_wet = np.zeros_like(y)
        
        # 为每个声部生成LFO
        for voice in range(voices):
            # 每个声部使用略微不同的参数
            voice_rate = rate * (0.9 + 0.2 * (voice / voices))
            voice_depth = depth_samples * (0.9 + 0.2 * (voice / voices))
            voice_phase = 2 * np.pi * (voice / voices)
            
            # 生成时间向量
            t = np.arange(len(y)) / self.sr
            
            # 计算LFO调制的延迟
            delay = np.sin(2 * np.pi * voice_rate * t + voice_phase)
            delay = (delay + 1) * voice_depth / 2  # 归一化到 [0, depth]
            delay_samples = delay * self.sr
            
            # 生成调制后的采样索引
            indices = np.arange(len(y), dtype=np.float32)
            indices_modulated = indices - delay_samples
            
            # 对索引进行边界检查
            valid_indices = (indices_modulated >= 0) & (indices_modulated < len(y) - 1)
            indices_modulated = indices_modulated[valid_indices]
            
            # 线性插值
            indices_int = np.floor(indices_modulated).astype(np.int32)
            alpha = indices_modulated - indices_int
            
            y_modulated = np.zeros_like(y)
            y_modulated[valid_indices] = (1 - alpha) * y[indices_int] + alpha * y[indices_int + 1]
            
            # 累加声部
            y_wet += y_modulated / voices
        
        # 混合干湿信号
        return dry_level * y + wet_level * y_wet
    
    def apply_distortion(self, y, amount=0.5, wet_level=0.5, dry_level=0.5):
        """应用失真效果
        
        Args:
            y (ndarray): 音频数据
            amount (float): 失真量 (0.0-1.0)
            wet_level (float): 湿信号电平 (0.0-1.0)
            dry_level (float): 干信号电平 (0.0-1.0)
        
        Returns:
            ndarray: 处理后的音频数据
        """
        # 映射amount到更有用的范围
        gain = 1.0 + 9.0 * amount
        
        # 软剪裁函数
        def soft_clip(x, a=1.0):
            return np.sign(x) * (1.0 - np.exp(-a * np.abs(x)))
        
        # 应用增益并软剪裁
        y_wet = soft_clip(y * gain, 1.0 + 5.0 * amount)
        
        # 标准化输出
        if np.max(np.abs(y_wet)) > 0:
            y_wet = y_wet / np.max(np.abs(y_wet))
        
        # 混合干湿信号
        return dry_level * y + wet_level * y_wet
    
    def apply_flanger(self, y, rate=0.2, depth=0.002, feedback=0.5, wet_level=0.7, dry_level=0.7):
        """应用镶边效果
        
        Args:
            y (ndarray): 音频数据
            rate (float): 调制率（Hz）
            depth (float): 调制深度（秒）
            feedback (float): 反馈系数 (-0.9-0.9)
            wet_level (float): 湿信号电平 (0.0-1.0)
            dry_level (float): 干信号电平 (0.0-1.0)
        
        Returns:
            ndarray: 处理后的音频数据
        """
        # 将深度转换为样本数
        depth_samples = int(depth * self.sr)
        
        # 创建输出和缓冲器
        y_out = np.copy(y)
        buffer = np.zeros_like(y)
        
        # 生成时间向量
        t = np.arange(len(y)) / self.sr
        
        # 计算LFO调制的延迟
        delay = np.sin(2 * np.pi * rate * t)
        delay = (delay + 1) * depth_samples / 2  # 归一化到 [0, depth_samples]
        
        # 应用镶边效果
        for i in range(len(y)):
            # 计算当前索引的延迟（向下取整）
            d = int(delay[i])
            
            if i >= d:
                # 当前输出 = 当前输入 + 延迟反馈
                buffer[i] = y[i] + feedback * buffer[i-d]
            else:
                buffer[i] = y[i]
        
        # 混合干湿信号
        return dry_level * y + wet_level * buffer
    
    def apply_phaser(self, y, rate=0.5, depth=6, wet_level=0.5, dry_level=0.5):
        """应用相位器效果
        
        Args:
            y (ndarray): 音频数据
            rate (float): 调制率（Hz）
            depth (int): 全通滤波器数量
            wet_level (float): 湿信号电平 (0.0-1.0)
            dry_level (float): 干信号电平 (0.0-1.0)
        
        Returns:
            ndarray: 处理后的音频数据
        """
        # 确保深度是整数
        depth = int(depth)
        
        # 生成时间向量
        t = np.arange(len(y)) / self.sr
        
        # 创建LFO
        lfo = 0.5 + 0.5 * np.sin(2 * np.pi * rate * t)
        
        # 串联全通滤波器的中心频率 (Hz)
        min_freq = 200
        max_freq = 1600
        
        # 创建输出
        y_out = np.copy(y)
        
        # 应用多个全通滤波器
        for i in range(depth):
            # 计算调制的频率
            center_freq = min_freq + (max_freq - min_freq) * lfo
            
            # 设计全通滤波器系数
            b, a = signal.iirpeak(center_freq, 5.0, self.sr, 'peak')
            
            # 应用滤波器
            y_out = signal.lfilter(b, a, y_out)
        
        # 混合干湿信号
        return dry_level * y + wet_level * y_out
    
    def apply_eq(self, y, low_gain=1.0, mid_gain=1.0, high_gain=1.0):
        """应用三段均衡效果
        
        Args:
            y (ndarray): 音频数据
            low_gain (float): 低频增益
            mid_gain (float): 中频增益
            high_gain (float): 高频增益
        
        Returns:
            ndarray: 处理后的音频数据
        """
        # 低频滤波器 (500 Hz 以下)
        b_low, a_low = signal.butter(4, 500 / (self.sr/2), 'lowpass')
        y_low = signal.lfilter(b_low, a_low, y)
        
        # 中频滤波器 (500 Hz - 2000 Hz)
        b_mid, a_mid = signal.butter(4, [500 / (self.sr/2), 2000 / (self.sr/2)], 'bandpass')
        y_mid = signal.lfilter(b_mid, a_mid, y)
        
        # 高频滤波器 (2000 Hz 以上)
        b_high, a_high = signal.butter(4, 2000 / (self.sr/2), 'highpass')
        y_high = signal.lfilter(b_high, a_high, y)
        
        # 应用增益并混合
        return low_gain * y_low + mid_gain * y_mid + high_gain * y_high
    
    def apply_compressor(self, y, threshold=-20, ratio=4.0, attack=0.01, release=0.1):
        """应用压缩器效果
        
        Args:
            y (ndarray): 音频数据
            threshold (float): 阈值 (dB)
            ratio (float): 压缩比
            attack (float): 起音时间 (秒)
            release (float): 释放时间 (秒)
        
        Returns:
            ndarray: 处理后的音频数据
        """
        # 将阈值从dB转换为线性单位
        threshold_linear = 10 ** (threshold / 20.0)
        
        # 计算包络
        y_abs = np.abs(y)
        env = np.zeros_like(y_abs)
        
        # 转换时间常数到采样
        attack_samples = int(attack * self.sr)
        release_samples = int(release * self.sr)
        
        # 创建简单的包络追踪器
        a_attack = np.exp(-1.0 / attack_samples) if attack_samples > 0 else 0
        a_release = np.exp(-1.0 / release_samples) if release_samples > 0 else 0
        
        # 计算包络
        for i in range(len(y_abs)):
            if i == 0:
                env[i] = y_abs[i]
            elif y_abs[i] > env[i-1]:
                env[i] = a_attack * env[i-1] + (1 - a_attack) * y_abs[i]
            else:
                env[i] = a_release * env[i-1] + (1 - a_release) * y_abs[i]
        
        # 计算增益
        gain = np.ones_like(env)
        mask = env > threshold_linear
        
        if ratio != 1.0:
            gain[mask] = (threshold_linear + (env[mask] - threshold_linear) / ratio) / env[mask]
        
        # 应用增益
        return y * gain
    
    def apply_pitch_shift(self, y, semitones=0):
        """应用音高移位效果
        
        Args:
            y (ndarray): 音频数据
            semitones (float): 音高偏移量（半音）
        
        Returns:
            ndarray: 处理后的音频数据
        """
        return librosa.effects.pitch_shift(y, sr=self.sr, n_steps=semitones)
    
    def apply_time_stretch(self, y, rate=1.0):
        """应用时间拉伸效果
        
        Args:
            y (ndarray): 音频数据
            rate (float): 拉伸率（<1: 变慢, >1: 变快）
        
        Returns:
            ndarray: 处理后的音频数据
        """
        return librosa.effects.time_stretch(y, rate=rate) 