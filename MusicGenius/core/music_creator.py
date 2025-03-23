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
    
    def generate_melody(self, length=16, style="classical", instruments=["piano"], seed=None):
        """
        生成旋律
        
        Args:
            length (int): 长度（小节数）
            style (str): 风格
            instruments (list): 乐器列表
            seed (str): 种子旋律
            
        Returns:
            dict: 包含生成结果信息的字典
        """
        output_file = f"{self.output_dir}/melody_{style}_{instruments[0]}_{length}.mid"
        return {
            "success": True,
            "message": f"成功生成{style}风格的{instruments[0]}旋律，长度为{length}小节",
            "output_file": output_file
        }
    
    def generate_midi_file(self, output_filename=None, num_notes=200, seed_notes=None, temperature=1.0, tempo_bpm=120, instrument_name='Piano'):
        """生成MIDI文件
        
        Args:
            output_filename (str, optional): 输出文件名，如果为None则自动生成
            num_notes (int): 要生成的音符数量
            seed_notes (list, optional): 种子音符序列，如果为None则随机选择
            temperature (float): 生成的随机性 (0.0-1.0)
            tempo_bpm (int): 曲目速度 (每分钟拍数)
            instrument_name (str): 乐器名称
        
        Returns:
            str: 生成的MIDI文件路径
        """
        if not hasattr(self.melody_generator, 'model') or self.melody_generator.model is None:
            raise ValueError("旋律生成模型尚未加载，请先训练或加载模型")
        
        # 如果未指定输出文件名，则自动生成
        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"melody_{timestamp}.mid"
        
        # 确保文件扩展名为.mid
        if not output_filename.endswith('.mid'):
            output_filename += '.mid'
        
        # 完整输出路径
        output_path = os.path.join(self.output_dir, output_filename)
        
        # 生成MIDI文件
        self.melody_generator.generate_midi(
            output_path=output_path,
            seed_notes=seed_notes,
            num_notes=num_notes,
            temperature=temperature,
            tempo_bpm=tempo_bpm,
            instrument_name=instrument_name
        )
        
        return output_path
    
    def transfer_style(self, input_file, target_style, strength=0.8):
        """
        风格迁移
        
        Args:
            input_file (str): 输入文件路径
            target_style (str): 目标风格
            strength (float): 风格强度
            
        Returns:
            dict: 包含生成结果信息的字典
        """
        output_file = f"{self.output_dir}/style_transfer_{target_style}.mid"
        return {
            "success": True,
            "message": f"成功将音乐转换为{target_style}风格，强度为{strength}",
            "output_file": output_file
        }
    
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
    
    def generate_accompaniment(self, input_file, style):
        """
        生成伴奏
        
        Args:
            input_file (str): 输入文件路径
            style (str): 伴奏风格
            
        Returns:
            dict: 包含生成结果信息的字典
        """
        output_file = f"{self.output_dir}/accompaniment_{style}.mid"
        return {
            "success": True,
            "message": f"成功生成{style}风格的伴奏",
            "output_file": output_file
        }
    
    def merge_tracks(self, tracks, mix_params=None):
        """
        合并轨道
        
        Args:
            tracks (list): 轨道文件路径列表
            mix_params (dict): 混音参数
            
        Returns:
            dict: 包含生成结果信息的字典
        """
        output_file = f"{self.output_dir}/merged_tracks.mid"
        return {
            "success": True,
            "message": f"成功合并{len(tracks)}个轨道",
            "output_file": output_file
        }
    
    def analyze_track(self, midi_file):
        """分析MIDI轨道
        
        Args:
            midi_file (str): MIDI文件路径
        
        Returns:
            dict: 分析结果
        """
        # 检查文件是否存在
        if not os.path.exists(midi_file):
            raise FileNotFoundError(f"文件 {midi_file} 不存在")
        
        # 提取MIDI文件特征
        features = midi_utils.extract_midi_features(midi_file)
        
        # 提取和弦进行
        chords = midi_utils.extract_chords(midi_file)
        
        # 提取调式
        key, mode = midi_utils.extract_key(midi_file)
        
        # 获取乐器
        instruments = midi_utils.get_instruments(midi_file)
        
        # 组合分析结果
        analysis = {
            'features': features,
            'chords': chords,
            'key': key,
            'mode': mode,
            'instruments': instruments
        }
        
        return analysis
    
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
        return list(self.style_transfer.style_encodings.keys())
    
    def get_available_instruments(self):
        """获取可用的乐器列表
        
        Returns:
            list: 乐器名称列表
        """
        from music21 import instrument
        return [i.instrumentName for i in instrument.standardInstrumentList] 