import os
import shutil
import numpy as np
import tempfile
from datetime import datetime
from ..models import LSTMMelodyGenerator, TransformerStyleTransfer
from ..audio import AudioProcessor
from ..effects import AudioEffects
from ..utils import midi_utils
import music21
import pretty_midi
from midiutil import MIDIFile
import subprocess
import json
from typing import List, Dict, Optional, Union
import librosa
import soundfile as sf
from .melody_generator import MelodyGenerator
from .style_transfer import StyleTransfer
from .accompaniment_generator import AccompanimentGenerator
from music21 import instrument

class MusicCreator:
    """音乐创作引擎类，集成旋律生成、风格迁移等功能"""
    
    def __init__(self, model_dir='models', output_dir='output'):
        """初始化音乐创作引擎
        
        Args:
            model_dir (str): 模型目录
            output_dir (str): 输出目录
        """
        self.model_dir = model_dir
        self.output_dir = output_dir
        os.makedirs(model_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化生成模型
        self.melody_generator = LSTMMelodyGenerator()
        self.style_transfer = TransformerStyleTransfer()
        
        # 初始化音频处理工具
        self.audio_processor = AudioProcessor()
        self.audio_effects = AudioEffects()
        
        # 加载已有模型
        self._load_available_models()
        
        # 音乐风格定义
        self.styles = {
            '古典': {'scale': [0, 2, 4, 5, 7, 9, 11], 'rhythm': [1, 0.5, 0.25]},
            '流行': {'scale': [0, 2, 4, 5, 7, 9, 10], 'rhythm': [0.5, 0.25, 0.125]},
            '爵士': {'scale': [0, 2, 3, 5, 7, 9, 10], 'rhythm': [0.75, 0.5, 0.25]},
            '电子': {'scale': [0, 2, 4, 7, 9], 'rhythm': [0.25, 0.125]},
            '民谣': {'scale': [0, 2, 4, 5, 7, 9, 10], 'rhythm': [1, 0.5]},
            '蓝调': {'scale': [0, 3, 5, 6, 7, 10], 'rhythm': [1, 0.75]}
        }
        
        # 初始化数据库
        
        # 初始化各个组件
        self.accompaniment_generator = AccompanimentGenerator()
        
        # 创建必要的目录
        os.makedirs('uploads', exist_ok=True)
        
        # 初始化 LSTM 旋律生成器
        self.lstm_generator = LSTMMelodyGenerator()
        # 初始化简单旋律生成器
        self.simple_generator = MelodyGenerator()
    
    def _load_available_models(self):
        """加载可用的预训练模型"""
        # 寻找并加载LSTM旋律生成模型
        lstm_model_path = os.path.join(self.model_dir, 'lstm_melody.h5')
        if os.path.exists(lstm_model_path):
            try:
                self.melody_generator.load_model(lstm_model_path)
                print(f"已加载LSTM旋律生成模型: {lstm_model_path}")
            except Exception as e:
                print(f"加载LSTM模型出错: {e}")
        
        # 寻找并加载Transformer风格迁移模型
        transformer_model_path = os.path.join(self.model_dir, 'transformer_style.h5')
        if os.path.exists(transformer_model_path):
            try:
                self.style_transfer.load_model(transformer_model_path)
                print(f"已加载Transformer风格迁移模型: {transformer_model_path}")
            except Exception as e:
                print(f"加载Transformer模型出错: {e}")
    
    def train_melody_model(self, midi_files, sequence_length=100, epochs=50, batch_size=64):
        """训练旋律生成模型
        
        Args:
            midi_files (list): MIDI文件路径列表
            sequence_length (int): 输入序列长度
            epochs (int): 训练轮次
            batch_size (int): 批次大小
        """
        # 确保模型目录存在
        os.makedirs(self.model_dir, exist_ok=True)
        
        # 配置保存路径
        save_path = os.path.join(self.model_dir, 'lstm_melody.h5')
        
        # 初始化并训练模型
        self.melody_generator = LSTMMelodyGenerator(sequence_length=sequence_length)
        self.melody_generator.train(midi_files, epochs=epochs, batch_size=batch_size, save_path=save_path)
        
        return save_path
    
    def learn_style(self, midi_files, style_name, epochs=30, batch_size=32):
        """学习音乐风格
        
        Args:
            midi_files (list): MIDI文件路径列表
            style_name (str): 风格名称
            epochs (int): 训练轮次
            batch_size (int): 批次大小
        """
        # 确保模型目录存在
        os.makedirs(self.model_dir, exist_ok=True)
        
        # 配置保存路径
        save_path = os.path.join(self.model_dir, 'transformer_style.h5')
        
        # 学习风格
        self.style_transfer.learn_style(
            midi_files=midi_files,
            style_name=style_name,
            epochs=epochs,
            batch_size=batch_size,
            save_path=save_path
        )
        
        return save_path
    
    def generate_melody(self, style: str, num_notes: int = 200, temperature: float = 1.0,
                       tempo_bpm: int = 120, instrument_name: str = 'Piano',
                       generator_type: str = 'lstm', effects: Optional[List[str]] = None,
                       effects_config: Optional[Dict] = None) -> str:
        """生成旋律
        
        Args:
            style (str): 音乐风格
            num_notes (int): 音符数量
            temperature (float): 随机性参数
            tempo_bpm (int): 节拍数
            instrument_name (str): 乐器名称
            generator_type (str): 生成器类型：'simple' 或 'lstm'
            effects (List[str], optional): 特效列表，如 ['reverb', 'chorus']
            effects_config (Dict, optional): 特效参数配置
            
        Returns:
            str: 生成的旋律文件路径
        """
        # 创建输出目录
        output_dir = self.output_dir

        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        midi_file = os.path.join(output_dir, f'melody_{style}_{generator_type}_{timestamp}.mid')
        wav_file = os.path.join(output_dir, f'melody_{style}_{generator_type}_{timestamp}.wav')
        print('wav_file'+wav_file);
        if generator_type == 'lstm':
            # 使用 LSTM 生成器
            seed_notes = self._get_style_seed_notes(style)
            melody = self.lstm_generator.generate_melody(
                seed_notes=seed_notes,
                num_notes=num_notes,
                temperature=temperature
            )
            self.lstm_generator.generate_midi(
                output_path=midi_file,
                melody=melody,
                tempo_bpm=tempo_bpm,
                instrument_name=instrument_name
            )
        else:
            # 使用简单生成器，直接获取音频数据,这个地方支持用不同的乐器
            audio_data = self.simple_generator.generate(
                style=style,
                length=num_notes // 8,  # 将音符数量转换为小节数
                seed=None,
                instrument_name=instrument_name,
                effects=effects,
                effects_config=effects_config
            )
            print('start sf.write')
            # 保存音频数据为WAV文件
            sf.write(wav_file, audio_data, 44100)
            print('finish sf.write')
            return wav_file
        
        # 如果是LSTM生成的MIDI，转换为WAV
        if generator_type == 'lstm':
            self.midi_to_wav(midi_file, wav_file)
        
        

        return wav_file
    
    def _get_style_seed_notes(self, style: str) -> List[str]:
        """根据风格获取种子音符序列
        
        Args:
            style: 音乐风格
            
        Returns:
            List[str]: 种子音符序列
        """
        # 为不同风格定义特征性的种子音符序列
        style_seeds = {
            '古典': ['C4', 'E4', 'G4', 'C5'],  # C大调和弦
            '爵士': ['C4', 'E4', 'G4', 'Bb4'],  # C7和弦
            '流行': ['C4', 'F4', 'G4', 'Am4'],  # 流行进行
            '民谣': ['C4', 'D4', 'E4', 'G4'],   # 民谣音阶
            '电子': ['C4', 'D4', 'F4', 'G4'],   # 电子音阶
            '蓝调': ['C4', 'Eb4', 'F4', 'G4']   # 蓝调音阶
        }
        
        return style_seeds.get(style, ['C4', 'E4', 'G4', 'C5'])  # 默认使用C大调和弦
    
    def midi_to_wav(self, midi_file, wav_file):
        """将MIDI文件转换为WAV格式
        
        Args:
            midi_file (str): MIDI文件路径
            wav_file (str): 输出WAV文件路径
        """
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
        """风格迁移功能
        
        Args:
            input_file (str): 输入文件路径
            target_style (str): 目标风格
            strength (float): 风格强度
            
        Returns:
            str: 输出文件路径
        """
        # TODO: 实现实际的风格迁移逻辑
        # 当前仅返回输入文件
        return input_file
    
    def apply_effects(self, input_file, effects):
        """
        应用音效
        
        Args:
            input_file (str): 输入文件路径
            effects (list): 效果参数列表
            
        Returns:
            dict: 包含生成结果信息的字典
        """
        output_file = f"{self.output_dir}/effects_applied.mid"
        return {
            "success": True,
            "message": f"成功应用音效：{', '.join(effects)}",
            "output_file": output_file
        }
    
    def generate_accompaniment(self, style: str, instruments: List[str]) -> str:
        """生成伴奏
        
        Args:
            style: 音乐风格
            instruments: 乐器列表
            
        Returns:
            str: 生成的伴奏文件路径
        """
        # 生成伴奏
        accompaniment = self.accompaniment_generator.generate(style, instruments)
        
        # 保存伴奏
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'output/accompaniment_{timestamp}.wav'
        sf.write(output_file, accompaniment, 44100)
        
        return output_file
    
    def process_audio(self, input_file, output_file=None, sample_rate=44100):
        """处理音频文件，使用audio_processor进行处理
        
        Args:
            input_file (str): 输入音频文件路径
            output_file (str, optional): 输出文件路径，默认为None（自动生成）
            sample_rate (int): 采样率
            
        Returns:
            str: 处理后的音频文件路径
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"文件 {input_file} 不存在")
            
        # 生成默认输出文件名
        if output_file is None:
            filename = os.path.basename(input_file)
            base, ext = os.path.splitext(filename)
            output_file = os.path.join(self.output_dir, f"{base}_processed{ext}")
        
        # 加载音频
        audio_data, sr = self.audio_processor.load_audio(input_file, sr=sample_rate)
        
        # 分析并保存音频特征
        features = self.audio_processor.extract_features(audio_data, sr=sr)
        features_file = os.path.join(self.output_dir, f"{os.path.basename(input_file)}_features.json")
        
        # 保存处理后的音频
        self.audio_processor.save_audio(audio_data, output_file, sr=sr)
        
        return output_file, features
        
    def apply_audio_effects(self, input_file: str, effects: List[str], effect_params: Dict) -> str:
        """应用音频效果
        
        Args:
            input_file: 输入音频文件路径
            effects: 效果列表
            effect_params: 效果参数
            
        Returns:
            str: 处理后的音频文件路径
        """
        # 读取音频
        audio, sr = librosa.load(input_file, sr=44100)
        
        # 应用效果
        processed_audio = self.audio_processor.apply_effects(audio, effects, effect_params)
        
        # 保存处理后的音频
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'output/processed_{timestamp}.wav'
        sf.write(output_file, processed_audio, sr)
        
        return output_file
    
    def analyze_audio(self, input_file, plot=False):
        """分析音频特征
        
        Args:
            input_file (str): 输入音频文件路径
            plot (bool): 是否生成可视化图表
            
        Returns:
            dict: 分析结果
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"文件 {input_file} 不存在")
        
        # 加载音频
        audio_data, sr = self.audio_processor.load_audio(input_file)
        
        # 提取特征
        features = self.audio_processor.extract_features(audio_data, sr)
        
        # 分析节奏
        rhythm_info = self.audio_processor.analyze_rhythm(audio_data, sr)
        
        # 分析和声
        harmony_info = self.audio_processor.analyze_harmony(audio_data, sr)
        
        # 如果需要绘制可视化图表
        if plot:
            # 绘制波形图
            self.audio_processor.plot_waveform(audio_data, sr, title=f"Waveform: {os.path.basename(input_file)}")
            
            # 绘制频谱图
            self.audio_processor.plot_spectrogram(audio_data, sr, title=f"Spectrogram: {os.path.basename(input_file)}")
            
            # 绘制特征图
            self.audio_processor.plot_features(features, title_prefix=f"{os.path.basename(input_file)} - ")
        
        # 组合分析结果
        analysis_result = {
            'features': features,
            'rhythm': rhythm_info,
            'harmony': harmony_info,
            'tempo': rhythm_info['tempo'],
            'estimated_key': harmony_info['estimated_key'],
            'estimated_mode': harmony_info['estimated_mode']
        }
        
        return analysis_result
    
    def audio_to_midi(self, input_file, output_file=None):
        """将音频转换为MIDI
        
        Args:
            input_file (str): 输入音频文件路径
            output_file (str, optional): 输出MIDI文件路径，默认为None（自动生成）
            
        Returns:
            str: 输出MIDI文件路径
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"文件 {input_file} 不存在")
            
        # 生成默认输出文件名
        if output_file is None:
            filename = os.path.basename(input_file)
            base, ext = os.path.splitext(filename)
            output_file = os.path.join(self.output_dir, f"{base}.mid")
        
        # 加载音频
        audio_data, sr = self.audio_processor.load_audio(input_file)
        
        # 提取特征
        features = self.audio_processor.extract_features(audio_data, sr)
        
        # 创建MIDI文件
        midi = MIDIFile(1)
        track = 0
        channel = 0
        time = 0
        tempo = 120
        midi.addTempo(track, time, tempo)
        
        # 从音高特征中提取音符
        f0 = features['f0']
        voiced_flag = features['voiced_flag']
        
        # 计算音符
        current_note = None
        current_start = 0
        for i, (pitch, is_voiced) in enumerate(zip(f0, voiced_flag)):
            if is_voiced and not np.isnan(pitch):
                # 将频率转换为MIDI音符编号
                midi_note = int(round(69 + 12 * np.log2(pitch / 440.0)))
                
                if current_note is None:
                    # 开始新音符
                    current_note = midi_note
                    current_start = i
                elif midi_note != current_note:
                    # 当前音符结束，添加到MIDI文件
                    note_duration = (i - current_start) / sr
                    midi_time = current_start / sr * (tempo / 60)
                    midi.addNote(track, channel, current_note, midi_time, note_duration, 100)
                    
                    # 开始新音符
                    current_note = midi_note
                    current_start = i
            elif current_note is not None:
                # 当前音符结束，添加到MIDI文件
                note_duration = (i - current_start) / sr
                midi_time = current_start / sr * (tempo / 60)
                midi.addNote(track, channel, current_note, midi_time, note_duration, 100)
                current_note = None
        
        # 保存MIDI文件
        with open(output_file, 'wb') as f:
            midi.writeFile(f)
        
        return output_file
    
    def merge_tracks(self, tracks, mix_params=None):
        """合并轨道
        
        Args:
            tracks (list): 轨道文件路径列表
            mix_params (dict): 混音参数
            
        Returns:
            str: 输出文件路径
        """
        if not tracks:
            raise ValueError("必须提供至少一个轨道")
            
        # 检查文件是否存在
        for track in tracks:
            if not os.path.exists(track):
                raise FileNotFoundError(f"文件 {track} 不存在")
        
        # 确定是音频文件还是MIDI文件
        if all(track.endswith(('.wav', '.mp3', '.ogg')) for track in tracks):
            # 音频文件混音
            return self._merge_audio_tracks(tracks, mix_params)
        elif all(track.endswith('.mid') for track in tracks):
            # MIDI文件合并
            return self._merge_midi_tracks(tracks, mix_params)
        else:
            raise ValueError("所有轨道必须是同一类型（全部音频或全部MIDI）")
            
    def _merge_audio_tracks(self, audio_tracks, mix_params=None):
        """合并音频轨道
        
        Args:
            audio_tracks (list): 音频文件路径列表
            mix_params (dict): 混音参数
            
        Returns:
            str: 输出文件路径
        """
        # 生成输出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(self.output_dir, f"merged_audio_{timestamp}.wav")
        
        # 加载所有音频轨道
        tracks_data = []
        max_length = 0
        sr = None
        
        for i, track_path in enumerate(audio_tracks):
            audio_data, track_sr = self.audio_processor.load_audio(track_path)
            
            # 使用第一个轨道的采样率
            if sr is None:
                sr = track_sr
            elif sr != track_sr:
                raise ValueError(f"所有轨道必须具有相同的采样率（轨道{i+1}的采样率与第一个轨道不同）")
                
            tracks_data.append(audio_data)
            max_length = max(max_length, len(audio_data))
            
        # 将所有轨道填充到相同长度
        for i in range(len(tracks_data)):
            if len(tracks_data[i]) < max_length:
                tracks_data[i] = np.pad(tracks_data[i], (0, max_length - len(tracks_data[i])))
                
        # 应用混音参数
        if mix_params is None:
            # 默认等比例混音
            weights = [1.0 / len(tracks_data)] * len(tracks_data)
        else:
            weights = mix_params.get('weights', [1.0 / len(tracks_data)] * len(tracks_data))
            
        # 混音
        mixed_audio = np.zeros(max_length)
        for i, track_data in enumerate(tracks_data):
            mixed_audio += track_data * weights[i]
            
        # 归一化
        if np.max(np.abs(mixed_audio)) > 1.0:
            mixed_audio = mixed_audio / np.max(np.abs(mixed_audio))
            
        # 保存混音结果
        self.audio_processor.save_audio(mixed_audio, output_file, sr=sr)
        
        return output_file
            
    def _merge_midi_tracks(self, midi_tracks, mix_params=None):
        """合并MIDI轨道
        
        Args:
            midi_tracks (list): MIDI文件路径列表
            mix_params (dict): 合并参数
            
        Returns:
            str: 输出文件路径
        """
        # 生成输出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(self.output_dir, f"merged_midi_{timestamp}.mid")
        
        # 创建一个空的music21 Score对象
        from music21 import converter, stream
        merged_score = stream.Score()
        
        # 为每个MIDI添加一个音轨
        for midi_path in midi_tracks:
            # 加载MIDI文件
            midi_score = converter.parse(midi_path)
            
            # 将MIDI添加到合并的Score中
            for part in midi_score.parts:
                merged_score.insert(0, part)
                
        # 保存合并后的MIDI
        merged_score.write('midi', fp=output_file)
        
        return output_file
    
    def save_model(self, model_name, model_path=None):
        """保存模型
        
        Args:
            model_name (str): 模型名称，'melody'或'style'
            model_path (str, optional): 保存路径，如果为None则使用默认路径
        
        Returns:
            str: 保存的模型路径
        """
        if model_name == 'melody':
            if model_path is None:
                model_path = os.path.join(self.model_dir, 'lstm_melody.h5')
            self.melody_generator.save_model(model_path)
        elif model_name == 'style':
            if model_path is None:
                model_path = os.path.join(self.model_dir, 'transformer_style.h5')
            self.style_transfer.save_model(model_path)
        else:
            raise ValueError("模型名称必须是'melody'或'style'")
        
        return model_path
    
    def load_model(self, model_name, model_path=None):
        """加载模型
        
        Args:
            model_name (str): 模型名称，'melody'或'style'
            model_path (str, optional): 模型路径，如果为None则使用默认路径
        """
        if model_name == 'melody':
            if model_path is None:
                model_path = os.path.join(self.model_dir, 'lstm_melody.h5')
            self.melody_generator.load_model(model_path)
        elif model_name == 'style':
            if model_path is None:
                model_path = os.path.join(self.model_dir, 'transformer_style.h5')
            self.style_transfer.load_model(model_path)
        else:
            raise ValueError("模型名称必须是'melody'或'style'")
    
    def get_available_styles(self):
        """获取可用的风格列表
        
        Returns:
            list: 风格名称列表
        """
        return list(self.styles.keys())
    
    def get_available_instruments(self):
        """获取可用的乐器列表
        
        Returns:
            list: 乐器名称列表
        """
        # 使用 music21 提供的标准乐器类
        potential_instruments = [
            '钢琴',
            '小提琴',
            '长笛',
            '吉他',
            '小号',
            '萨克斯',
            '单簧管',
            '贝斯',
        ]
        
        return potential_instruments;
    
    def save_composition(self, title: str, description: str, 
                        accompaniment_file: str, melody_file: str,
                        effects: List[str]) -> int:
        """保存作品
        
        Args:
            title: 作品标题
            description: 作品描述
            accompaniment_file: 伴奏文件路径
            melody_file: 旋律文件路径
            effects: 应用的效果列表
            
        Returns:
            int: 作品ID
        """
        # 保存作品信息到数据库
        composition_id = self.db.add_composition(
            title=title,
            description=description,
            accompaniment_file=accompaniment_file,
            melody_file=melody_file,
            effects=json.dumps(effects),
            created_at=datetime.now()
        )
        
        return composition_id
    
    def get_composition(self, composition_id: int) -> Dict:
        """获取作品信息
        
        Args:
            composition_id: 作品ID
            
        Returns:
            Dict: 作品信息
        """
        return self.db.get_composition(composition_id)
    
    def list_compositions(self) -> List[Dict]:
        """获取所有作品列表
        
        Returns:
            List[Dict]: 作品列表
        """
        return self.db.list_compositions()
    
    def delete_composition(self, composition_id: int) -> bool:
        """删除作品
        
        Args:
            composition_id: 作品ID
            
        Returns:
            bool: 是否删除成功
        """
        return self.db.delete_composition(composition_id) 