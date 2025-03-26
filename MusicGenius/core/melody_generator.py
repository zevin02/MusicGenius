"""
旋律生成器模块
"""

import numpy as np
from typing import Optional, List
from midiutil import MIDIFile
# 这个也是旋律生成的模块：但是这边生成简单的旋律，
class MelodyGenerator:
    """旋律生成器类"""
    
    def __init__(self):
        """初始化旋律生成器"""
        self.sample_rate = 44100
        
        # 定义音阶
        self.scales = {
            '古典': [0, 2, 4, 5, 7, 9, 11, 12],  # C大调
            '爵士': [0, 3, 5, 6, 7, 10, 12],     # 蓝调音阶
            '流行': [0, 2, 4, 7, 9, 12],         # 五声音阶
            '民谣': [0, 2, 4, 5, 7, 9, 11, 12],  # C大调
            '电子': [0, 2, 4, 5, 7, 9, 11, 12],  # C大调
            '蓝调': [0, 3, 5, 6, 7, 10, 12]      # 蓝调音阶
        }
        
        # 定义节奏模式
        self.rhythm_patterns = {
            '古典': [1.0, 0.5, 0.5, 1.0, 0.5, 0.5],
            '爵士': [0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
            '流行': [1.0, 0.5, 0.5, 1.0, 0.5, 0.5],
            '民谣': [1.0, 0.5, 0.5, 1.0, 0.5, 0.5],
            '电子': [0.25, 0.25, 0.25, 0.25, 0.5, 0.5],
            '蓝调': [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        }
    
    def generate(self, style: str, length: int = 8, seed: Optional[str] = None) -> np.ndarray:
        """生成旋律
        
        Args:
            style: 音乐风格
            length: 旋律长度（小节数）
            seed: 随机种子
            
        Returns:
            np.ndarray: 生成的旋律音频数据
        """
        if seed:
            np.random.seed(hash(seed) % 2**32)
        
        # 获取音阶和节奏模式
        scale = self.scales.get(style, self.scales['古典'])
        rhythm = self.rhythm_patterns.get(style, self.rhythm_patterns['古典'])
        
        # 生成MIDI音符
        midi_notes = self._generate_midi_notes(scale, rhythm, length)
        
        # 将MIDI转换为音频
        audio = self._midi_to_audio(midi_notes)
        
        return audio
    
    def _generate_midi_notes(self, scale: List[int], rhythm: List[float], 
                           length: int) -> List[tuple]:
        """生成MIDI音符
        
        Args:
            scale: 音阶
            rhythm: 节奏模式
            length: 旋律长度（小节数）
            
        Returns:
            List[tuple]: MIDI音符列表，每个元素为(音高, 开始时间, 持续时间)
        """
        notes = []
        time = 0
        beats_per_bar = 4
        
        for bar in range(length):
            for beat in range(beats_per_bar):
                # 随机选择音高
                pitch = 60 + np.random.choice(scale)  # 从C4开始
                
                # 随机选择节奏
                duration = np.random.choice(rhythm)
                
                notes.append((pitch, time, duration))
                time += duration
        
        return notes
    
    def _midi_to_audio(self, notes: List[tuple]) -> np.ndarray:
        """将MIDI音符转换为音频
        
        Args:
            notes: MIDI音符列表
            
        Returns:
            np.ndarray: 音频数据
        """
        # 创建MIDI文件
        midi = MIDIFile(1)
        midi.addTempo(0, 0, 120)  # 120 BPM
        
        # 添加音符
        for pitch, time, duration in notes:
            midi.addNote(0, 0, pitch, time, duration, 100)
        
        # 保存MIDI文件
        midi_filename = 'temp.mid'
        with open(midi_filename, 'wb') as f:
            midi.writeFile(f)
        
        # 将MIDI转换为音频
        audio = self._synthesize_midi(midi_filename)
        
        # 删除临时文件
        import os
        os.remove(midi_filename)
        
        return audio
    
    def _synthesize_midi(self, midi_file: str) -> np.ndarray:
        """合成MIDI文件为音频
        
        Args:
            midi_file: MIDI文件路径
            
        Returns:
            np.ndarray: 音频数据
        """
        # 使用FluidSynth合成MIDI
        import subprocess
        import soundfile as sf
        
        # 生成临时WAV文件
        wav_file = 'temp.wav'
        subprocess.run(['fluidsynth', '-ni', 'soundfont.sf2', midi_file, '-F', wav_file, '-r', str(self.sample_rate)])
        
        # 读取音频数据
        audio, _ = sf.read(wav_file)
        
        # 删除临时文件
        import os
        os.remove(wav_file)
        
        return audio 