"""
旋律生成器模块
"""
# numpy是一个类似的array
import numpy as np
import os
from typing import Optional, List, Dict
from midiutil import MIDIFile
# 这个也是旋律生成的模块：但是这边生成简单的旋律，
# MIDI与音频的本质区别：midi值包含音符的符号化信息（音高，时长，力度），不包含声音波形，无法进行信号处理
# 音频：有采样点组成的波形信号，是DSP操作的对象,


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
    # TODO:从前端传来的随机性和节拍数也没有被使用到
    def generate(self, style: str, length: int = 8, seed: Optional[str] = None, instrument_name: str = 'Piano', 
                 effects: Optional[List[str]] = None, effects_config: Optional[Dict] = None) -> np.ndarray:
        """生成旋律
        
        Args:
            style: 音乐风格
            length: 旋律长度（小节数）
            seed: 随机种子
            instrument_name: 乐器名称（支持中文或英文）
            effects: 效果列表，如['reverb', 'chorus']
            effects_config: 效果参数配置
            
        Returns:
            np.ndarray: 生成的旋律音频数据
        """
        # 设置随机数种子通过hassh生成一个随机数种子，rand（n），输出n个整数
        if seed:
            np.random.seed(hash(seed) % 2**32)
        
        # 确保使用有效的风格
        if style not in self.scales:
            print(f"未知风格: {style}，使用默认风格：古典")
            style = '古典' # 没设置就使用默认的古典风格
        
        # 将instrument 从中文乐器名称转换为英文
        if instrument_name in self.instrument_name_map:
            instrument_name = self.instrument_name_map[instrument_name]
        
        # 确保使用有效的乐器
        if instrument_name not in self.instruments:
            print(f"未知乐器: {instrument_name}，使用默认乐器：Piano")
            instrument_name = 'Piano'
        
        print(f"使用风格: {style}")
        print(f"使用乐器: {instrument_name}")
        if effects:
            print(f"使用特效: {', '.join(effects)}")
        
        # 获取音阶和节奏模式
        scale = self.scales[style] # 音阶
        rhythm = self.rhythm_patterns[style] # rhythm 韵律
        base_note_range = self.base_notes[style]    # 获取该风格对应到的音阶范围
        instrument = self.instruments[instrument_name] # 获取对应到midi标准的乐器编号
        
        print('开始生成MIDI音符')
        
        # TODO:还需要传入随机数和节拍数，和:生成MIDI音符
        midi_notes = self._generate_midi_notes(scale, rhythm, length, base_note_range) # 生成的音符midi音符
        
        # midi中只包含了音符的音高，时间和力度，不包含具体的音频波形，而音频处理通常是在音频信号中进行的（必须是生成音频之后应用音效）
        print('开始将MIDI转换为音频')
        
        # 将MIDI转换为音频
        audio = self._midi_to_audio(midi_notes, instrument)
        
        # 应用特效（如果有）
        if effects and effects_config:
            print('应用音频特效')
            audio = self._apply_effects(audio, effects, effects_config)
        
        return audio
    
    #  TODO:添加随机性和节拍数的参数 
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
        notes = []  # 初始化一个空的列表来存储生成的音符信息
        time = 0    # 初始化时间变量，表明当前音符的开始时间
        beats_per_bar = 4   # 设置每小节有4拍，（4/4拍是最常见的节奏）
        min_note, max_note = note_range # 从传入的参数中获取音符范围
        
        # 外层循环：生成指定数量的小节，（length参数只决定生成多少个小节）
        for bar in range(length):
            # 内层循环：处理每小节中的每一拍
            for beat in range(beats_per_bar):
                
                # 随机决定是播放音符还是休止符（生成0-1之间的随机数）
                if np.random.random() > 0.2:  # 80%的概率播放音符
                    # 随机选择基础音符
                    base_note = np.random.randint(min_note, max_note - 12)  # 确保有足够的范围应用音阶
                    
                    # 从音阶中随机选择相对音高
                    scale_note = np.random.choice(scale)
                    
                    # 计算实际音高
                    pitch = base_note + scale_note
                    
                    # 确保音高在合理范围内（21-108）
                    pitch = max(min(pitch, 108), 21)  # MIDI音符范围: 21-108
                    
                    # 随机选择节奏 从给定的节奏模式中随机选择一个韵律
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
        midi = MIDIFile(1) # 参数1 表示音轨数量 （只生成一段音频）,独立的事件通道
        midi.addTempo(0, 0, 120)  # 120 BPM  第0个音轨 
        
        # 设置乐器 ，乐器的音色
        midi.addProgramChange(0, 0, 0, instrument) # 通道0
        
        # 添加音符 遍历所有的音符添加到音轨中
        for pitch, time, duration in notes:
            # 添加音符 参数: 音轨编号, 通道编号, 时间（以1/100秒为单位）, 持续时间（以1/100秒为单位）, 音量（0-127）
            midi.addNote(0, 0, pitch, time, duration, 100)
        
        # 保存MIDI文件
        midi_filename = 'temp.mid'
        with open(midi_filename, 'wb') as f:# 'wb' 表示写入二进制文件，将生成的写入到临时的mid文件中
            midi.writeFile(f)

        print(f"MIDI文件已创建: {midi_filename}")
        print(f"使用乐器编号: {instrument}")

        # 将MIDI转换为音频
        audio = self._synthesize_midi(midi_filename)
        
        return audio
    

    # 将mid转化成音频
    def _synthesize_midi(self, midi_file: str) -> np.ndarray:
        """合成MIDI文件为音频
        
        Args:
            midi_file: MIDI文件路径
            
        Returns:
            np.ndarray: 音频数据
        """
        # 使用FluidSynth合成MIDI
        import subprocess # 用于执行命令行工具
        import soundfile as sf # 用于音频文件的读写
        # 在这个地方挂掉了
        # 生成临时WAV文件
        wav_file = 'temp.wav'
        # 创建一个空的 WAV 文件
        # 这里我们创建一个长度为0的音频文件
        # 参数说明：文件名，空数组数组，采样率

        sf.write(wav_file, np.zeros((0,)), 44100)  # 44100 是采样率
        soundfont_path = '/usr/share/sounds/sf2/FluidR3_GM.sf2'
        result = subprocess.run(['fluidsynth', '-ni', soundfont_path, midi_file, '-F', wav_file, '-r', str(self.sample_rate)])
        
        # 执行完毕后，我们删除临时文件
        # 读取音频数据
        audio, _ = sf.read(wav_file) # 读取申城的wav文件
        
        # 删除临时文件
        import os
        os.remove(wav_file)
        
        return audio 
    

    # 数字信号处理（DSP）和音频特效的关系密切，
    # 音频特效（混响，均衡器，延迟）本质上是对音频波形（数字信号）的数字运算，需要以下dsp的核心技术
    # 1. 时域处理（增益调整，动态范围压缩）：直接修改采样点的振幅值
    # 2. 频域处理（均衡器，滤波器）通过傅立叶变化（FFT），将音频转化到频域，修改特定的频率，再逆变化回时域
    # 3. 卷积运算（混响效果） ：将音频信号和冲击响应进行卷集（模拟不同空间的混响效果）


    def _apply_effects(self, audio: np.ndarray, effects: List[str], effects_config: Dict) -> np.ndarray:
        """应用音频特效
        
        Args:
            audio: 音频数据
            effects: 特效列表
            effects_config: 特效配置参数
            
        Returns:
            np.ndarray: 处理后的音频数据
        """
        from ..effects.audio_effects import AudioEffects
        
        # 创建音频特效处理器
        audio_effects = AudioEffects(sr=self.sample_rate)
        
        # 处理后的音频
        processed_audio = audio.copy()
        
        try:
            # 应用每个特效
            for effect in effects:
                effect_params = effects_config.get(effect, {})
                
                if effect == 'reverb':
                    print(f"应用混响效果，参数: {effect_params}")
                    processed_audio = audio_effects.apply_reverb(
                        processed_audio,
                        room_size=effect_params.get('room_size', 0.8),
                        damping=effect_params.get('damping', 0.5),
                        wet_level=effect_params.get('wet_level', 0.3),
                        dry_level=effect_params.get('dry_level', 0.7)
                    )
                elif effect == 'delay':
                    print(f"应用延迟效果，参数: {effect_params}")
                    # 改进的延迟效果实现
                    delay_time = effect_params.get('delay_time', 0.5)  # 秒
                    feedback = effect_params.get('feedback', 0.5)
                    wet_level = effect_params.get('wet_level', 0.5)
                    dry_level = effect_params.get('dry_level', 0.5)
                    
                    delay_samples = int(delay_time * self.sample_rate)
                    
                    # 创建延迟缓冲区
                    delayed_signal = np.zeros_like(processed_audio)
                    if delay_samples < len(processed_audio):
                        delayed_signal[delay_samples:] = processed_audio[:-delay_samples]
                    
                    # 添加反馈
                    temp_buffer = delayed_signal.copy()
                    for i in range(1, 5):  # 限制反馈次数，避免过度计算
                        if delay_samples * i < len(processed_audio):
                            feedback_gain = feedback ** i
                            if feedback_gain < 0.01:  # 当反馈增益太小时停止
                                break
                            temp_buffer[delay_samples * i:] += processed_audio[:-(delay_samples * i)] * feedback_gain
                    
                    # 混合原始信号和延迟信号
                    processed_audio = processed_audio * dry_level + temp_buffer * wet_level
                    
                    # 归一化，避免削波
                    max_amplitude = np.max(np.abs(processed_audio))
                    if max_amplitude > 0.95:
                        processed_audio = processed_audio / max_amplitude * 0.95
                
                elif effect == 'chorus':
                    print(f"应用合唱效果，参数: {effect_params}")
                    processed_audio = audio_effects.apply_chorus(
                        processed_audio,
                        rate=effect_params.get('rate', 0.5),
                        depth=effect_params.get('depth', 0.002),
                        voices=effect_params.get('voices', 3)
                    )
                elif effect == 'distortion':
                    print(f"应用失真效果，参数: {effect_params}")
                    processed_audio = audio_effects.apply_distortion(
                        processed_audio,
                        amount=effect_params.get('amount', 0.5),
                        wet_level=effect_params.get('wet_level', 0.5),
                        dry_level=effect_params.get('dry_level', 0.5)
                    )
                elif effect == 'eq':
                    print(f"应用均衡器效果，参数: {effect_params}")
                    processed_audio = audio_effects.apply_eq(
                        processed_audio,
                        low_gain=effect_params.get('low_gain', 1.0),
                        mid_gain=effect_params.get('mid_gain', 1.0),
                        high_gain=effect_params.get('high_gain', 1.0)
                    )
                    
                # 检查处理后的音频数据是否有效
                if np.isnan(processed_audio).any() or np.isinf(processed_audio).any():
                    print(f"警告: 特效 {effect} 产生了无效数据，恢复为原始音频")
                    processed_audio = audio.copy()
                    break
            
            # 最终归一化，确保不会有削波
            max_amplitude = np.max(np.abs(processed_audio))
            if max_amplitude > 0.95:
                processed_audio = processed_audio / max_amplitude * 0.95
            
        except Exception as e:
            print(f"应用特效时出错: {str(e)}")
            # 出错时返回原始音频
            return audio
        
        return processed_audio 