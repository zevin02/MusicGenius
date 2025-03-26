import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
import os
import pickle
from music21 import note, chord, stream, instrument, tempo
# 这个是高质量，符合音乐规律的旋律，生成midi文件 
class LSTMMelodyGenerator:
    """基于LSTM的旋律生成模型"""
    
    def __init__(self, sequence_length=100, model_path=None):
        """初始化LSTM旋律生成器
        
        Args:
            sequence_length (int): 输入序列长度
            model_path (str, optional): 预训练模型路径
        """
        self.sequence_length = sequence_length
        self.model = None
        self.notes = []
        self.note_to_int = {}
        self.int_to_note = {}
        self.vocab_size = 0
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def prepare_sequences(self, notes, pitch_names):
        """准备训练序列
        
        Args:
            notes (list): 音符列表
            pitch_names (list): 音高名称列表
        
        Returns:
            tuple: (网络输入, 网络输出目标)
        """
        self.note_to_int = dict((note, number) for number, note in enumerate(pitch_names))
        self.int_to_note = dict((number, note) for number, note in enumerate(pitch_names))
        
        network_input = []
        network_output = []
        
        # 创建输入序列和对应输出
        for i in range(0, len(notes) - self.sequence_length, 1):
            sequence_in = notes[i:i + self.sequence_length]
            sequence_out = notes[i + self.sequence_length]
            network_input.append([self.note_to_int[char] for char in sequence_in])
            network_output.append(self.note_to_int[sequence_out])
        
        # 重塑输入为LSTM的格式 [样本数, 时间步, 特征]
        n_patterns = len(network_input)
        network_input = np.reshape(network_input, (n_patterns, self.sequence_length, 1))
        
        # 归一化输入
        network_input = network_input / float(self.vocab_size)
        
        # 独热编码输出
        network_output = tf.keras.utils.to_categorical(network_output, num_classes=self.vocab_size)
        
        return network_input, network_output
    
    def build_model(self, input_shape, vocab_size):
        """构建LSTM模型
        
        Args:
            input_shape (tuple): 输入形状 (sequence_length, 1)
            vocab_size (int): 词汇表大小
        """
        self.model = Sequential()
        
        # 第一层LSTM
        self.model.add(LSTM(256, input_shape=input_shape, return_sequences=True))
        self.model.add(Dropout(0.3))
        self.model.add(BatchNormalization())
        
        # 第二层LSTM
        self.model.add(LSTM(256, return_sequences=True))
        self.model.add(Dropout(0.3))
        self.model.add(BatchNormalization())
        
        # 第三层LSTM
        self.model.add(LSTM(128))
        self.model.add(Dropout(0.3))
        self.model.add(BatchNormalization())
        
        # 输出层
        self.model.add(Dense(vocab_size, activation='softmax'))
        
        # 编译模型
        self.model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
        
        # 打印模型摘要
        self.model.summary()
    
    def train(self, midi_files, epochs=100, batch_size=64, save_path='model/lstm_melody.h5'):
        """训练模型
        
        Args:
            midi_files (list): MIDI文件路径列表
            epochs (int): 训练轮次
            batch_size (int): 批次大小
            save_path (str): 保存模型路径
        """
        # 获取所有音符
        self.notes = []
        for file in midi_files:
            self.notes.extend(self._get_notes(file))
        
        # 获取所有不同的音符名称
        pitch_names = sorted(set(self.notes))
        self.vocab_size = len(pitch_names)
        
        # 准备序列
        network_input, network_output = self.prepare_sequences(self.notes, pitch_names)
        
        # 构建模型
        self.build_model((self.sequence_length, 1), self.vocab_size)
        
        # 创建检查点回调
        checkpoint = ModelCheckpoint(
            save_path,
            monitor='loss',
            verbose=1,
            save_best_only=True,
            mode='min'
        )
        
        # 早停回调
        early_stopping = EarlyStopping(
            monitor='loss',
            patience=10,
            verbose=1,
            restore_best_weights=True
        )
        
        callbacks_list = [checkpoint, early_stopping]
        
        # 训练模型
        self.model.fit(
            network_input, 
            network_output,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks_list
        )
        
        # 保存音符映射
        with open(os.path.join(os.path.dirname(save_path), 'note_mappings.pkl'), 'wb') as f:
            pickle.dump((self.note_to_int, self.int_to_note, self.vocab_size), f)

    # 用户操作触发LSTM 的调用：1.生成旋律（用户在网页上选择风格，长度等参数，提交旋律生成请求）
    # 2. 训练模型，用户上传MIDI 文件，训练新的LSTM 模型
    # 3.
    # 这个地方负责生成旋律  
    def generate_melody(self, seed_notes, num_notes=100, temperature=1.0):
        """生成旋律
        
        Args:
            seed_notes (list): 种子音符序列
            num_notes (int): 要生成的音符数量
            temperature (float): 生成的随机性 (0.0-1.0)
        
        Returns:
            list: 生成的音符序列
        """
        if not self.model:
            raise ValueError("模型尚未构建或加载")
        
        # 将种子音符转换为整数
        pattern = [self.note_to_int[note] for note in seed_notes]
        prediction_output = []
        
        # 生成新的音符
        for _ in range(num_notes):
            # 准备输入
            prediction_input = np.reshape(pattern, (1, len(pattern), 1))
            prediction_input = prediction_input / float(self.vocab_size)
            
            # 预测下一个音符
            prediction = self.model.predict(prediction_input, verbose=0)[0]
            
            # 应用温度采样
            prediction = self._apply_temperature(prediction, temperature)
            
            # 采样下一个音符
            index = np.random.choice(range(len(prediction)), p=prediction)
            result = self.int_to_note[index]
            prediction_output.append(result)
            
            # 更新种子序列
            pattern.append(index)
            pattern = pattern[1:len(pattern)]
        
        return prediction_output
    
    def generate_midi(self, output_path, seed_notes=None, num_notes=200, temperature=1.0, tempo_bpm=120, instrument_name='Piano'):
        """生成MIDI文件
        
        Args:
            output_path (str): 输出MIDI文件路径
            seed_notes (list, optional): 种子音符，如果为None则随机选择
            num_notes (int): 要生成的音符数量
            temperature (float): 生成的随机性 (0.0-1.0)
            tempo_bpm (int): 曲目速度 (每分钟拍数)
            instrument_name (str): 乐器名称
        """
        if not self.model:
            raise ValueError("模型尚未构建或加载")
        
        if seed_notes is None:
            # 随机选择种子序列
            start = np.random.randint(0, len(self.notes) - self.sequence_length)
            seed_notes = self.notes[start:start + self.sequence_length]
        
        # 生成音符
        prediction_output = self.generate_melody(seed_notes, num_notes, temperature)
        
        # 创建音乐流
        output_notes = stream.Stream()
        
        # 设置速度
        output_notes.append(tempo.MetronomeMark(number=tempo_bpm))
        
        # 设置乐器
        output_notes.append(instrument.fromString(instrument_name))
        
        # 添加音符
        offset = 0
        for pattern in prediction_output:
            # 处理和弦
            if ('.' in pattern) or pattern.isdigit():
                notes_in_chord = pattern.split('.')
                chord_notes = []
                for current_note in notes_in_chord:
                    new_note = note.Note(current_note)
                    new_note.storedInstrument = instrument.fromString(instrument_name)
                    chord_notes.append(new_note)
                new_chord = chord.Chord(chord_notes)
                new_chord.offset = offset
                output_notes.append(new_chord)
            # 处理休止符
            elif pattern == 'REST':
                new_note = note.Rest()
                new_note.offset = offset
                new_note.quarterLength = 0.5
                output_notes.append(new_note)
            # 处理单个音符
            else:
                new_note = note.Note(pattern)
                new_note.offset = offset
                new_note.storedInstrument = instrument.fromString(instrument_name)
                output_notes.append(new_note)
            
            # 移动偏移量，使得音符有序放置
            offset += 0.5
        
        # 写入MIDI文件
        midi_stream = stream.Stream(output_notes)
        midi_stream.write('midi', fp=output_path)
    
    def load_model(self, model_path):
        """加载预训练模型
        
        Args:
            model_path (str): 模型文件路径
        """
        # 加载模型
        self.model = load_model(model_path)
        
        # 加载音符映射
        mapping_path = os.path.join(os.path.dirname(model_path), 'note_mappings.pkl')
        if os.path.exists(mapping_path):
            with open(mapping_path, 'rb') as f:
                self.note_to_int, self.int_to_note, self.vocab_size = pickle.load(f)
    
    def save_model(self, model_path):
        """保存模型
        
        Args:
            model_path (str): 保存模型路径
        """
        if not self.model:
            raise ValueError("没有模型可保存")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # 保存模型
        self.model.save(model_path)
        
        # 保存音符映射
        with open(os.path.join(os.path.dirname(model_path), 'note_mappings.pkl'), 'wb') as f:
            pickle.dump((self.note_to_int, self.int_to_note, self.vocab_size), f)
    
    def _get_notes(self, midi_path):
        """从MIDI文件中提取音符
        
        Args:
            midi_path (str): MIDI文件路径
        
        Returns:
            list: 音符列表
        """
        from music21 import converter
        
        notes = []
        
        try:
            midi = converter.parse(midi_path)
            
            # 提取所有乐器部分
            parts = instrument.partitionByInstrument(midi)
            
            if parts:  # 文件有乐器部分
                notes_to_parse = parts.parts[0].recurse()
            else:  # 文件没有乐器部分
                notes_to_parse = midi.flat.notes
            
            # 提取音符、和弦和休止符
            for element in notes_to_parse:
                if isinstance(element, note.Note):
                    notes.append(str(element.pitch))
                elif isinstance(element, chord.Chord):
                    notes.append('.'.join(str(n) for n in element.normalOrder))
                elif isinstance(element, note.Rest):
                    notes.append('REST')
        except Exception as e:
            print(f"处理MIDI文件 {midi_path} 时出错: {e}")
        
        return notes
    
    def _apply_temperature(self, predictions, temperature):
        """应用温度采样
        
        Args:
            predictions (ndarray): 预测概率
            temperature (float): 温度参数
        
        Returns:
            ndarray: 调整后的概率
        """
        if temperature == 1.0:
            return predictions
        
        # 应用温度
        predictions = np.log(predictions + 1e-10) / temperature
        predictions = np.exp(predictions)
        
        # 重新归一化
        predictions = predictions / np.sum(predictions)
        
        return predictions 