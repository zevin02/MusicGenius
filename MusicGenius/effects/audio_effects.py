import numpy as np
from scipy import signal
import librosa
import warnings

class AudioEffects:
    """音频特效处理类，提供各种音频特效"""
    
    def __init__(self, sr=22050):
        """初始化音频特效处理器
        
        Args:
            sr (int): 采样率
        """
        self.sr = sr
    
    def _safe_normalize(self, y, threshold=0.95):
        """安全归一化数组，处理极端值
        
        Args:
            y (ndarray): 输入音频数据
            threshold (float): 最大绝对值阈值，默认0.95
            
        Returns:
            ndarray: 归一化后的数据
        """
        # 检查并处理无效值
        if np.isnan(y).any() or np.isinf(y).any():
            warnings.warn("发现无效值 (NaN/Inf)，已替换为0")
            y = np.nan_to_num(y, nan=0.0, posinf=threshold, neginf=-threshold)
        
        # 归一化音频数据，避免削波
        max_val = np.max(np.abs(y))
        if max_val > threshold:
            return y / max_val * threshold
        return y
    
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
        # 参数边界检查
        room_size = np.clip(room_size, 0.0, 1.0)
        damping = np.clip(damping, 0.0, 1.0)
        wet_level = np.clip(wet_level, 0.0, 1.0)
        dry_level = np.clip(dry_level, 0.0, 1.0)
        
        try:
            # 简化的Schroeder混响实现
            # 疏状滤波器稀疏(控制放射次数和衰减速度)
            comb_filters = [0.86, 0.83, 0.80, 0.78]
            # 全通滤波器系数（调整混响的扩散感，让声音更自然）
            allpass_filters = [0.7, 0.6]
            
            # 转换room_size为延迟线长度的系数
            room_size_factor = 0.95 + room_size * 0.049 # 延迟时间随房间增加而略微增加
            
            # 延迟线长度（以样本为单位）- 跟据room_size调整
            delays = [int(self.sr * t * room_size_factor) for t in [0.0297, 0.0371, 0.0411, 0.0437]]
            allpass_delays = [int(self.sr * t) for t in [0.005, 0.0017]]
            
            # 衰减系数 - 根据damping调整
            decays = [f * (1.0 - damping * 0.15) for f in comb_filters]
            
            # 创建湿信号数组
            y_wet = np.zeros_like(y)# 创建一个和原始音频形状相同的全零数组
            
            # 应用并联梳状滤波器
            # 模拟多次反射
            for i, (delay, decay) in enumerate(zip(delays, decays)):
                y_comb = np.zeros_like(y)   # 单个梳状滤波器的输出
                for n in range(len(y)):
                    if n >= delay:
                        y_comb[n] = y[n] + decay * y_comb[n - delay]
                    else:
                        y_comb[n] = y[n]
                y_wet += y_comb / len(delays)
            
            # 应用全通滤波器 （扩散混响，让声音更自然）
            for i, (g, delay) in enumerate(zip(allpass_filters, allpass_delays)):
                y_allpass = np.zeros_like(y_wet)
                for n in range(len(y_wet)):
                    if n >= delay:
                        # 全通公式：输出=增益*输入+前delay点输入-增益*前delay点的输出
                        y_allpass[n] = g * y_wet[n] + y_wet[n - delay] - g * y_allpass[n - delay]
                    else:
                        y_allpass[n] = y_wet[n]
                y_wet = y_allpass
            
            # 归一化湿信号
            y_wet = self._safe_normalize(y_wet)
            
            # 混合干湿信号
            result = dry_level * y + wet_level * y_wet
            return self._safe_normalize(result)
            
        except Exception as e:
            warnings.warn(f"混响效果处理出错: {str(e)}，返回原始音频")
            return y
    
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
        try:
            # 参数边界检查
            delay_time = max(0.01, min(2.0, delay_time))  # 限制延迟时间范围
            feedback = max(0.0, min(0.9, feedback))       # 限制反馈，避免发散
            wet_level = np.clip(wet_level, 0.0, 1.0)
            dry_level = np.clip(dry_level, 0.0, 1.0)
            
            # 将延迟时间转换为样本数
            delay_samples = int(delay_time * self.sr)
            
            # 优化的延迟实现
            # 创建较短的输出数组以节省内存
            max_repeats = min(10, int(1.0 / (1.0 - feedback)) if feedback < 1.0 else 10)
            extra_length = delay_samples * max_repeats
            
            # 创建输出数组
            y_out = np.zeros(len(y) + extra_length)
            y_out[:len(y)] = y
            
            # 应用延迟和反馈
            current_feedback = feedback
            for repeat in range(1, max_repeats + 1):
                if current_feedback < 0.01:  # 当反馈太小时停止
                    break
                    
                start = repeat * delay_samples
                end = start + len(y)
                if end <= len(y_out):
                    y_out[start:end] += current_feedback * y
                    current_feedback *= feedback
            
            # 截取输出并混合干湿信号
            y_wet = y_out[:len(y)]
            
            # 混合干湿信号并归一化
            result = dry_level * y + wet_level * y_wet
            return self._safe_normalize(result)
            
        except Exception as e:
            warnings.warn(f"延迟效果处理出错: {str(e)}，返回原始音频")
            return y
    
    def apply_chorus(self, y, rate=0.5, depth=0.002, voices=3):
        """应用合唱效果
        
        Args:
            y (ndarray): 音频数据
            rate (float): 调制率（Hz）
            depth (float): 调制深度（秒）
            voices (int): 合唱声部数量
        
        Returns:
            ndarray: 处理后的音频数据
        """
        try:
            # 参数边界检查
            rate = max(0.1, min(5.0, rate))
            depth = max(0.0001, min(0.01, depth))
            voices = max(1, min(8, voices))
            
            # 将深度转换为样本数
            depth_samples = int(depth * self.sr)
            max_depth_samples = int(0.03 * self.sr)  # 最大30ms
            depth_samples = min(depth_samples, max_depth_samples)
            
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
                
                # 舍入到整数，避免插值错误
                delay_samples_int = np.round(delay).astype(np.int32)
                
                # 创建调制后的信号
                y_modulated = np.zeros_like(y)
                
                # 一个更安全的版本，避免索引越界
                for i in range(len(y)):
                    idx = i - delay_samples_int[i]
                    if 0 <= idx < len(y):
                        y_modulated[i] = y[idx]
                
                # 累加声部
                y_wet += y_modulated / voices
            
            # 混合干湿信号并归一化
            result = dry_level * y + wet_level * y_wet
            return self._safe_normalize(result)
            
        except Exception as e:
            warnings.warn(f"合唱效果处理出错: {str(e)}，返回原始音频")
            return y
    
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
        try:
            # 参数边界检查
            amount = np.clip(amount, 0.0, 1.0)
            wet_level = np.clip(wet_level, 0.0, 1.0)
            dry_level = np.clip(dry_level, 0.0, 1.0)
            
            # 映射amount到更有用的范围
            gain = 1.0 + 9.0 * amount
            
            # 安全软剪裁 - 避免指数溢出
            def safe_soft_clip(x, a=1.0):
                # 避免指数溢出
                x_limited = np.clip(a * np.abs(x), -30, 30)
                return np.sign(x) * (1.0 - np.exp(-x_limited))
            
            # 应用增益并软剪裁
            y_wet = safe_soft_clip(y * gain, 1.0 + 5.0 * amount)
            
            # 标准化输出
            y_wet = self._safe_normalize(y_wet)
            
            # 混合干湿信号
            result = dry_level * y + wet_level * y_wet
            return self._safe_normalize(result)
            
        except Exception as e:
            warnings.warn(f"失真效果处理出错: {str(e)}，返回原始音频")
            return y
    
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
        try:
            # 参数边界检查 - 限制增益范围以避免过度放大
            low_gain = np.clip(low_gain, 0.0, 4.0)
            mid_gain = np.clip(mid_gain, 0.0, 4.0)
            high_gain = np.clip(high_gain, 0.0, 4.0)
            
            # 低频滤波器 (500 Hz 以下)
            b_low, a_low = signal.butter(2, 500 / (self.sr/2), 'lowpass')
            y_low = signal.lfilter(b_low, a_low, y)
            
            # 中频滤波器 (500 Hz - 2000 Hz)
            b_mid, a_mid = signal.butter(2, [500 / (self.sr/2), 2000 / (self.sr/2)], 'bandpass')
            y_mid = signal.lfilter(b_mid, a_mid, y)
            
            # 高频滤波器 (2000 Hz 以上)
            b_high, a_high = signal.butter(2, 2000 / (self.sr/2), 'highpass')
            y_high = signal.lfilter(b_high, a_high, y)
            
            # 应用增益并混合
            result = low_gain * y_low + mid_gain * y_mid + high_gain * y_high
            return self._safe_normalize(result)
            
        except Exception as e:
            warnings.warn(f"均衡器效果处理出错: {str(e)}，返回原始音频")
            return y