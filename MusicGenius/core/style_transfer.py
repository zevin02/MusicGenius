"""
风格迁移模块
"""

import numpy as np
from typing import Optional
import librosa
import soundfile as sf

class StyleTransfer:
    """风格迁移类"""
    
    def __init__(self):
        """初始化风格迁移器"""
        self.sample_rate = 44100
        
        # 定义风格特征
        self.style_features = {
            '古典': {
                'tempo': 120,
                'dynamics': 0.8,
                'articulation': 0.9,
                'reverb': 0.3
            },
            '爵士': {
                'tempo': 140,
                'dynamics': 0.7,
                'articulation': 0.8,
                'reverb': 0.4
            },
            '流行': {
                'tempo': 130,
                'dynamics': 0.6,
                'articulation': 0.7,
                'reverb': 0.5
            },
            '民谣': {
                'tempo': 100,
                'dynamics': 0.5,
                'articulation': 0.6,
                'reverb': 0.2
            },
            '电子': {
                'tempo': 150,
                'dynamics': 0.9,
                'articulation': 0.5,
                'reverb': 0.6
            },
            '蓝调': {
                'tempo': 110,
                'dynamics': 0.6,
                'articulation': 0.7,
                'reverb': 0.3
            }
        }
    
    def transfer_style(self, audio: np.ndarray, target_style: str,
                      strength: float = 0.8) -> np.ndarray:
        """迁移音乐风格
        
        Args:
            audio: 输入音频数据
            target_style: 目标风格
            strength: 迁移强度（0-1）
            
        Returns:
            np.ndarray: 处理后的音频数据
        """
        # 获取目标风格特征
        style_feature = self.style_features.get(target_style, self.style_features['古典'])
        
        # 调整速度
        tempo_ratio = style_feature['tempo'] / 120  # 基准速度120 BPM
        audio = self._adjust_tempo(audio, tempo_ratio)
        
        # 调整动态范围
        audio = self._adjust_dynamics(audio, style_feature['dynamics'])
        
        # 调整发音
        audio = self._adjust_articulation(audio, style_feature['articulation'])
        
        # 添加混响
        audio = self._add_reverb(audio, style_feature['reverb'])
        
        return audio
    
    def _adjust_tempo(self, audio: np.ndarray, ratio: float) -> np.ndarray:
        """调整速度
        
        Args:
            audio: 输入音频数据
            ratio: 速度比例
            
        Returns:
            np.ndarray: 处理后的音频数据
        """
        return librosa.effects.time_stretch(audio, rate=ratio)
    
    def _adjust_dynamics(self, audio: np.ndarray, level: float) -> np.ndarray:
        """调整动态范围
        
        Args:
            audio: 输入音频数据
            level: 动态范围级别（0-1）
            
        Returns:
            np.ndarray: 处理后的音频数据
        """
        # 计算当前动态范围
        current_dynamic = np.max(np.abs(audio))
        
        # 调整动态范围
        target_dynamic = level * 0.9  # 留出一些余量
        ratio = target_dynamic / current_dynamic
        
        return audio * ratio
    
    def _adjust_articulation(self, audio: np.ndarray, level: float) -> np.ndarray:
        """调整发音
        
        Args:
            audio: 输入音频数据
            level: 发音级别（0-1）
            
        Returns:
            np.ndarray: 处理后的音频数据
        """
        # 使用包络来调整发音
        envelope = librosa.effects.preemphasis(audio, coef=0.97)
        
        # 混合原始音频和包络
        return audio * (1 - level) + envelope * level
    
    def _add_reverb(self, audio: np.ndarray, level: float) -> np.ndarray:
        """添加混响效果
        
        Args:
            audio: 输入音频数据
            level: 混响级别（0-1）
            
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
        
        return audio * (1 - level) + reverb * level 