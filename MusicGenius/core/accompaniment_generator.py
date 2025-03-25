"""
伴奏生成器模块
"""

import numpy as np
from typing import List
from midiutil import MIDIFile

class AccompanimentGenerator:
    """伴奏生成器类"""
    
    def __init__(self):
        """初始化伴奏生成器"""
        self.sample_rate = 44100
        
        # 定义和弦进行
        self.chord_progressions = {
            '古典': [
                ['C', 'G', 'Am', 'F'],  # I-V-vi-IV
                ['C', 'F', 'G', 'C'],   # I-IV-V-I
                ['Am', 'F', 'C', 'G']   # vi-IV-I-V
            ],
            '爵士': [
                ['Cm7', 'Fm7', 'Bb7', 'Eb7'],  # ii-V-I-IV
                ['Dm7', 'G7', 'Cm7', 'F7'],    # ii-V-i-IV
                ['Am7', 'D7', 'Gm7', 'C7']     # vi-ii-V-I
            ],
            '流行': [
                ['C', 'G', 'Am', 'F'],  # I-V-vi-IV
                ['C', 'Em', 'F', 'G'],  # I-iii-IV-V
                ['Am', 'F', 'C', 'G']   # vi-IV-I-V
            ],
            '民谣': [
                ['C', 'F', 'G', 'C'],   # I-IV-V-I
                ['C', 'G', 'Am', 'F'],  # I-V-vi-IV
                ['Am', 'F', 'C', 'G']   # vi-IV-I-V
            ],
            '电子': [
                ['C', 'G', 'Am', 'F'],  # I-V-vi-IV
                ['C', 'Em', 'F', 'G'],  # I-iii-IV-V
                ['Am', 'F', 'C', 'G']   # vi-IV-I-V
            ],
            '蓝调': [
                ['C7', 'F7', 'C7', 'G7', 'F7', 'C7'],  # 12小节蓝调
                ['C7', 'F7', 'C7', 'C7', 'F7', 'F7', 'C7', 'C7', 'G7', 'F7', 'C7', 'G7']
            ]
        }
        
        # 定义乐器音色
        self.instruments = {
            '钢琴': 0,
            '吉他': 24,
            '贝斯': 32,
            '弦乐': 48,
            '管乐': 56,
            '电子合成器': 80
        }
        
        # 定义节奏模式
        self.rhythm_patterns = {
            '钢琴': [1.0, 0.5, 0.5, 1.0, 0.5, 0.5],
            '吉他': [0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
            '贝斯': [1.0, 0.5, 0.5, 1.0, 0.5, 0.5],
            '弦乐': [2.0, 2.0],
            '管乐': [1.0, 0.5, 0.5, 1.0, 0.5, 0.5],
            '电子合成器': [0.25, 0.25, 0.25, 0.25, 0.5, 0.5]
        }
    
    def generate(self, style: str, instruments: List[str]) -> np.ndarray:
        """生成伴奏
        
        Args:
            style: 音乐风格
            instruments: 乐器列表
            
        Returns:
            np.ndarray: 生成的伴奏音频数据
        """
        # 创建MIDI文件
        midi = MIDIFile(len(instruments))
        midi.addTempo(0, 0, 120)  # 120 BPM
        
        # 获取和弦进行
        chord_progression = np.random.choice(self.chord_progressions[style])
        
        # 为每个乐器生成伴奏
        for i, instrument in enumerate(instruments):
            # 设置乐器音色
            midi.addProgramChange(i, 0, 0, self.instruments[instrument])
            
            # 生成该乐器的伴奏
            self._generate_instrument_accompaniment(
                midi, i, instrument, chord_progression
            )
        
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
    
    def _generate_instrument_accompaniment(self, midi: MIDIFile, track: int,
                                        instrument: str, chord_progression: List[str]):
        """生成单个乐器的伴奏
        
        Args:
            midi: MIDI文件对象
            track: 轨道号
            instrument: 乐器名称
            chord_progression: 和弦进行
        """
        # 获取节奏模式
        rhythm = self.rhythm_patterns[instrument]
        
        # 生成伴奏音符
        time = 0
        for chord in chord_progression:
            # 获取和弦音符
            chord_notes = self._get_chord_notes(chord)
            
            # 根据节奏模式添加音符
            for duration in rhythm:
                # 随机选择和弦中的音符
                note = np.random.choice(chord_notes)
                midi.addNote(track, 0, note, time, duration, 100)
                time += duration
    
    def _get_chord_notes(self, chord: str) -> List[int]:
        """获取和弦的音符
        
        Args:
            chord: 和弦名称
            
        Returns:
            List[int]: MIDI音符列表
        """
        # 定义音符基准值（C4 = 60）
        base_notes = {
            'C': 60, 'C#': 61, 'D': 62, 'D#': 63, 'E': 64, 'F': 65,
            'F#': 66, 'G': 67, 'G#': 68, 'A': 69, 'A#': 70, 'B': 71
        }
        
        # 定义和弦类型
        chord_types = {
            '': [0, 4, 7],           # 大三和弦
            'm': [0, 3, 7],          # 小三和弦
            '7': [0, 4, 7, 10],      # 属七和弦
            'm7': [0, 3, 7, 10]      # 小七和弦
        }
        
        # 解析和弦
        root = chord[0]
        if len(chord) > 1 and chord[1] == '#':
            root = chord[:2]
            chord_type = chord[2:]
        else:
            chord_type = chord[1:]
        
        # 获取和弦音符
        base_note = base_notes[root]
        intervals = chord_types.get(chord_type, chord_types[''])
        
        return [base_note + interval for interval in intervals]
    
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