"""
旋律生成器模块
"""

import numpy as np
import os
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
            '电子': [0, 2, 3, 7, 9, 10, 12],     # 电子音阶（带有增强的半音）
            '蓝调': [0, 3, 5, 6, 7, 10, 12]      # 蓝调音阶
        }
        
        # 定义节奏模式
        self.rhythm_patterns = {
            '古典': [1.0, 0.5, 0.5, 1.0, 0.5, 0.5],
            '爵士': [0.5, 0.25, 0.25, 0.5, 0.25, 0.25],
            '流行': [1.0, 0.5, 0.5, 1.0, 0.5, 0.5],
            '民谣': [1.0, 1.0, 1.0, 1.0],
            '电子': [0.25, 0.25, 0.25, 0.25, 0.5, 0.5],
            '蓝调': [0.75, 0.25, 0.5, 0.5]
        }
        
        # 中文乐器名称到英文的映射
        self.instrument_name_map = {
            '钢琴': 'Piano',
            '吉他': 'Acoustic Guitar',
            '小提琴': 'Violin',
            '大提琴': 'Cello',
            '小号': 'Trumpet',
            '萨克斯': 'Saxophone',
            '长笛': 'Flute',
            '贝斯': 'Bass',
            '单簧管': 'Clarinet',
        }
        
        # 定义各种乐器对应的MIDI程序编号（General MIDI标准）
        self.instruments = {
            'Piano': 0,          # 大钢琴
            'Acoustic Guitar': 24,  # 民谣吉他
            'Electric Guitar': 27,  # 电吉他
            'Violin': 40,        # 小提琴
            'Cello': 42,         # 大提琴
            'Trumpet': 56,       # 小号
            'Saxophone': 65,     # 萨克斯
            'Flute': 73,         # 长笛
            'Synth Lead': 80,    # 合成主音
            'Synth Pad': 88,     # 合成音垫
            'Bass': 33,          # 指拨贝斯
            'Drums': 0,          # 鼓组（特殊处理）
            'Clarinet': 71,      # 单簧管
        }
        
        # 定义不同风格的基础音符范围
        self.base_notes = {
            '古典': (60, 84),  # C4-C6
            '爵士': (55, 79),  # G3-G5
            '流行': (60, 84),  # C4-C6
            '民谣': (59, 83),  # B3-B5
            '电子': (48, 72),  # C3-C5
            '蓝调': (55, 79)   # G3-G5
        }
    
    def generate(self, style: str, length: int = 8, seed: Optional[str] = None, instrument_name: str = 'Piano') -> np.ndarray:
        """生成旋律
        
        Args:
            style: 音乐风格
            length: 旋律长度（小节数）
            seed: 随机种子
            instrument_name: 乐器名称（支持中文或英文）
            
        Returns:
            np.ndarray: 生成的旋律音频数据
        """
        if seed:
            np.random.seed(hash(seed) % 2**32)
        
        # 确保使用有效的风格
        if style not in self.scales:
            print(f"未知风格: {style}，使用默认风格：古典")
            style = '古典'
        
        # 将中文乐器名称转换为英文
        if instrument_name in self.instrument_name_map:
            instrument_name = self.instrument_name_map[instrument_name]
        
        # 确保使用有效的乐器
        if instrument_name not in self.instruments:
            print(f"未知乐器: {instrument_name}，使用默认乐器：Piano")
            instrument_name = 'Piano'
        
        print(f"使用风格: {style}")
        print(f"使用乐器: {instrument_name}")
        
        # 获取音阶和节奏模式
        scale = self.scales[style]
        rhythm = self.rhythm_patterns[style]
        base_note_range = self.base_notes[style]
        instrument = self.instruments[instrument_name]
        
        print('开始生成MIDI音符')
        
        # 生成MIDI音符
        midi_notes = self._generate_midi_notes(scale, rhythm, length, base_note_range)
        
        print('开始将MIDI转换为音频')
        
        # 将MIDI转换为音频
        audio = self._midi_to_audio(midi_notes, instrument)
        
        return audio
    
    def _generate_midi_notes(self, scale: List[int], rhythm: List[float], 
                           length: int, note_range: tuple) -> List[tuple]:
        """生成MIDI音符
        
        Args:
            scale: 音阶
            rhythm: 节奏模式
            length: 旋律长度（小节数）
            note_range: 音符范围 (最低音, 最高音)
            
        Returns:
            List[tuple]: MIDI音符列表，每个元素为(音高, 开始时间, 持续时间)
        """
        notes = []
        time = 0
        beats_per_bar = 4
        min_note, max_note = note_range
        
        for bar in range(length):
            for beat in range(beats_per_bar):
                # 随机决定是播放音符还是休止符
                if np.random.random() > 0.2:  # 80%的概率播放音符
                    # 随机选择基础音符
                    base_note = np.random.randint(min_note, max_note - 12)  # 确保有足够的范围应用音阶
                    
                    # 从音阶中选择相对音高
                    scale_note = np.random.choice(scale)
                    
                    # 计算实际音高
                    pitch = base_note + scale_note
                    
                    # 确保音高在合理范围内
                    pitch = max(min(pitch, 108), 21)  # MIDI音符范围: 21-108
                    
                    # 随机选择节奏
                    duration = np.random.choice(rhythm)
                    
                    # 添加音符
                    notes.append((pitch, time, duration))
                else:
                    # 休止符
                    duration = np.random.choice(rhythm)
                
                time += duration
        
        return notes
    
    def _midi_to_audio(self, notes: List[tuple], instrument: int) -> np.ndarray:
        """将MIDI音符转换为音频
        
        Args:
            notes: MIDI音符列表
            instrument: MIDI乐器编号
            
        Returns:
            np.ndarray: 音频数据
        """
        # 创建MIDI文件
        midi = MIDIFile(1)
        midi.addTempo(0, 0, 120)  # 120 BPM
        
        # 设置乐器
        midi.addProgramChange(0, 0, 0, instrument)
        
        # 添加音符
        for pitch, time, duration in notes:
            midi.addNote(0, 0, pitch, time, duration, 100)
        
        # 保存MIDI文件
        midi_filename = 'temp.mid'
        with open(midi_filename, 'wb') as f:
            midi.writeFile(f)

        print(f"MIDI文件已创建: {midi_filename}")
        print(f"使用乐器编号: {instrument}")

        # 将MIDI转换为音频
        audio = self._synthesize_midi(midi_filename)
        
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
        # 在这个地方挂掉了
        # 生成临时WAV文件
        wav_file = 'temp.wav'
        # 创建一个空的 WAV 文件
        # 这里我们创建一个长度为0的音频文件
        sf.write(wav_file, np.zeros((0,)), 44100)  # 44100 是采样率
        soundfont_path = '/usr/share/sounds/sf2/FluidR3_GM.sf2'
        result = subprocess.run(['fluidsynth', '-ni', soundfont_path, midi_file, '-F', wav_file, '-r', str(self.sample_rate)])
        
        # 读取音频数据
        audio, _ = sf.read(wav_file)
        
        # 删除临时文件
        import os
        os.remove(wav_file)
        
        return audio 