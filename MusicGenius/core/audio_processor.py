"""
音频处理模块
"""

import numpy as np
import librosa
from typing import List, Dict, Union
from scipy import signal

class AudioProcessor:
    """音频处理类"""
    
    def __init__(self):
        """初始化音频处理器"""
        self.sample_rate = 44100
    
    def apply_effects(self, audio: np.ndarray, effects: List[str], 
                     effect_params: Dict) -> np.ndarray:
        """应用音频效果
        
        Args:
            audio: 输入音频数据
            effects: 效果列表
            effect_params: 效果参数
            
        Returns:
            np.ndarray: 处理后的音频数据
        """
        processed_audio = audio.copy()
        
        for effect in effects:
            if effect == 'delay':
                processed_audio = self.apply_delay(
                    processed_audio,
                    delay_time=effect_params.get('delay_time', 0.3),
                    feedback=effect_params.get('feedback', 0.3)
                )
            elif effect == 'chorus':
                processed_audio = self.apply_chorus(
                    processed_audio,
                    rate=effect_params.get('rate', 1.5),
                    depth=effect_params.get('depth', 0.002),
                    mix=effect_params.get('mix', 0.5)
                )
            elif effect == 'reverb':
                processed_audio = self.apply_reverb(
                    processed_audio,
                    room_size=effect_params.get('room_size', 0.8),
                    damping=effect_params.get('damping', 0.5),
                    mix=effect_params.get('mix', 0.3)
                )
            elif effect == 'distortion':
                processed_audio = self.apply_distortion(
                    processed_audio,
                    amount=effect_params.get('amount', 0.5)
                )
            elif effect == 'equalizer':
                processed_audio = self.apply_equalizer(
                    processed_audio,
                    gains=effect_params.get('gains', [0, 0, 0, 0, 0])
                )
        
        return processed_audio
    
    def apply_delay(self, audio: np.ndarray, delay_time: float = 0.3,
                   feedback: float = 0.3) -> np.ndarray:
        """应用延迟效果
        
        Args:
            audio: 输入音频数据
            delay_time: 延迟时间（秒）
            feedback: 反馈量（0-1）
            
        Returns:
            np.ndarray: 处理后的音频数据
        """
        delay_samples = int(delay_time * self.sample_rate)
        delayed = np.zeros_like(audio)
        delayed[delay_samples:] = audio[:-delay_samples] * feedback
        
        return audio + delayed
    
    def apply_chorus(self, audio: np.ndarray, rate: float = 1.5,
                    depth: float = 0.002, mix: float = 0.5) -> np.ndarray:
        """应用合唱效果
        
        Args:
            audio: 输入音频数据
            rate: 调制速率（Hz）
            depth: 调制深度
            mix: 混合比例（0-1）
            
        Returns:
            np.ndarray: 处理后的音频数据
        """
        t = np.arange(len(audio)) / self.sample_rate
        mod = np.sin(2 * np.pi * rate * t)
        delay = depth * mod * self.sample_rate
        
        delayed = np.zeros_like(audio)
        for i in range(len(audio)):
            delay_idx = int(i + delay[i])
            if 0 <= delay_idx < len(audio):
                delayed[i] = audio[delay_idx]
        
        return audio * (1 - mix) + delayed * mix
    
    def apply_reverb(self, audio: np.ndarray, room_size: float = 0.8,
                    damping: float = 0.5, mix: float = 0.3) -> np.ndarray:
        """应用混响效果
        
        Args:
            audio: 输入音频数据
            room_size: 房间大小（0-1）
            damping: 阻尼（0-1）
            mix: 混合比例（0-1）
            
        Returns:
            np.ndarray: 处理后的音频数据
        """
        # 简单的混响实现
        delay_times = [0.03, 0.05, 0.07, 0.11, 0.13]
        decay_factors = [0.7, 0.5, 0.3, 0.2, 0.1]
        
        reverb = np.zeros_like(audio)
        for delay, decay in zip(delay_times, decay_factors):
            delay_samples = int(delay * self.sample_rate)
            delayed = np.zeros_like(audio)
            delayed[delay_samples:] = audio[:-delay_samples] * decay
            reverb += delayed
        
        return audio * (1 - mix) + reverb * mix
    
    def apply_distortion(self, audio: np.ndarray, amount: float = 0.5) -> np.ndarray:
        """应用失真效果
        
        Args:
            audio: 输入音频数据
            amount: 失真程度（0-1）
            
        Returns:
            np.ndarray: 处理后的音频数据
        """
        # 简单的软失真
        return np.tanh(audio * (1 + amount * 10))
    
    def apply_equalizer(self, audio: np.ndarray, gains: List[float]) -> np.ndarray:
        """应用均衡器效果
        
        Args:
            audio: 输入音频数据
            gains: 各频段增益（dB）
            
        Returns:
            np.ndarray: 处理后的音频数据
        """
        # 简单的5段均衡器
        freqs = [60, 250, 1000, 4000, 16000]
        bands = []
        
        for freq in freqs:
            # 创建带通滤波器
            b, a = signal.butter(2, [freq * 0.8 / (self.sample_rate/2),
                                   freq * 1.2 / (self.sample_rate/2)],
                               btype='band')
            bands.append((b, a))
        
        # 应用均衡器
        processed = np.zeros_like(audio)
        for (b, a), gain in zip(bands, gains):
            filtered = signal.filtfilt(b, a, audio)
            processed += filtered * (10 ** (gain / 20))
        
        return processed 