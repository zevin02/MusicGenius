#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
音乐生成模块
提供基本的音乐生成功能
"""

import os
import random
from midiutil import MIDIFile
import subprocess

class MusicGenerator:
    """音乐生成器类"""
    
    def __init__(self):
        """初始化音乐生成器"""
        self.output_dir = 'output'
        os.makedirs(self.output_dir, exist_ok=True)
        self.notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        self.octaves = [4, 5]  # 默认使用中音区
        self.styles = {
            '古典': {'scale': [0, 2, 4, 5, 7, 9, 11], 'rhythm': [1, 0.5, 0.25]},
            '流行': {'scale': [0, 2, 4, 5, 7, 9, 10], 'rhythm': [0.5, 0.25, 0.125]},
            '爵士': {'scale': [0, 2, 3, 5, 7, 9, 10], 'rhythm': [0.75, 0.5, 0.25]},
            '电子': {'scale': [0, 2, 4, 7, 9], 'rhythm': [0.25, 0.125]},
            '民谣': {'scale': [0, 2, 4, 5, 7, 9, 10], 'rhythm': [1, 0.5]},
            '蓝调': {'scale': [0, 3, 5, 6, 7, 10], 'rhythm': [1, 0.75]}
        }
        
    def note_to_number(self, note, octave):
        """将音符名称转换为MIDI音符编号"""
        base = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
        return base[note] + (octave + 1) * 12
    
    def generate_melody(self, style, length=8, seed=''):
        """生成MIDI旋律并转换为WAV格式"""
        # 创建MIDI文件
        degrees  = [60, 62, 64, 65, 67, 69, 71, 72]  # MIDI音符编号（C4到C5）
        track    = 0
        channel  = 0
        time     = 0    # 起始时间（以拍为单位）
        duration = 1    # 每个音符的持续时间（以拍为单位）
        tempo    = 120  # 每分钟120拍
        volume   = 100  # 音量（0-127）

        # 创建MIDI文件对象，包含1个轨道
        MyMIDI = MIDIFile(1)
        MyMIDI.addTempo(track, time, tempo)

        # 根据风格调整音符选择
        if style == '古典':
            degrees = [60, 62, 64, 65, 67, 69, 71, 72]  # C大调音阶
        elif style == '爵士':
            degrees = [60, 63, 65, 66, 67, 70, 72]  # 蓝调音阶
        elif style == '流行':
            degrees = [60, 62, 64, 67, 69]  # 五声音阶

        # 生成旋律
        for i in range(length):
            pitch = random.choice(degrees)
            MyMIDI.addNote(track, channel, pitch, time + i, duration, volume)

        # 保存MIDI文件
        midi_filename = os.path.join(self.output_dir, f'melody_{random.randint(1000, 9999)}.mid')
        with open(midi_filename, "wb") as output_file:
            MyMIDI.writeFile(output_file)

        # 将MIDI转换为WAV
        wav_filename = midi_filename.replace('.mid', '.wav')
        self.midi_to_wav(midi_filename, wav_filename)
        
        # 返回相对路径
        return os.path.basename(wav_filename)

    def midi_to_wav(self, midi_file, wav_file):
        """将MIDI文件转换为WAV格式"""
        soundfont = '/usr/share/sounds/sf2/FluidR3_GM.sf2'  # 默认的SoundFont文件
        command = [
            'fluidsynth',
            '-ni',
            soundfont,
            midi_file,
            '-F',
            wav_file,
            '-r',
            '44100'
        ]
        subprocess.run(command)
        
    def transfer_style(self, input_file, target_style, strength=0.8):
        """风格迁移功能（示例实现）"""
        # 这里应该实现实际的风格迁移逻辑
        # 当前仅返回输入文件
        return input_file
    
    def generate_accompaniment(self, input_file, style):
        """生成伴奏功能（示例实现）"""
        # 这里应该实现实际的伴奏生成逻辑
        # 当前仅返回输入文件
        return input_file 