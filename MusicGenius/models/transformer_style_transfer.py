import tensorflow as tf
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Input, Dense, Dropout, LayerNormalization, MultiHeadAttention
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
import numpy as np
import os
import pickle
from .lstm_melody_generator import LSTMMelodyGenerator

class TransformerBlock(tf.keras.layers.Layer):
    """Transformer编码器块"""
    
    def __init__(self, embed_dim, num_heads, ff_dim, rate=0.1):
        """初始化Transformer块
        
        Args:
            embed_dim (int): 嵌入维度
            num_heads (int): 注意力头数量
            ff_dim (int): 前馈网络维度
            rate (float): Dropout比率
        """
        super(TransformerBlock, self).__init__()
        self.att = MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
        self.ffn = tf.keras.Sequential([
            Dense(ff_dim, activation="relu"),
            Dense(embed_dim),
        ])
        self.layernorm1 = LayerNormalization(epsilon=1e-6)
        self.layernorm2 = LayerNormalization(epsilon=1e-6)
        self.dropout1 = Dropout(rate)
        self.dropout2 = Dropout(rate)
    
    def call(self, inputs, training):
        """前向传播
        
        Args:
            inputs (tensor): 输入张量
            training (bool): 是否在训练模式
        
        Returns:
            tensor: 输出张量
        """
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)

class PositionalEncoding(tf.keras.layers.Layer):
    """位置编码层"""
    
    def __init__(self, position, d_model):
        """初始化位置编码层
        
        Args:
            position (int): 序列最大长度
            d_model (int): 嵌入维度
        """
        super(PositionalEncoding, self).__init__()
        self.pos_encoding = self.positional_encoding(position, d_model)
    
    def get_angles(self, position, i, d_model):
        """计算位置编码的角度
        
        Args:
            position (tensor): 位置索引
            i (tensor): 维度索引
            d_model (int): 嵌入维度
        
        Returns:
            tensor: 角度值
        """
        angles = 1 / tf.pow(10000, (2 * (i // 2)) / tf.cast(d_model, tf.float32))
        return position * angles
    
    def positional_encoding(self, position, d_model):
        """生成位置编码
        
        Args:
            position (int): 序列最大长度
            d_model (int): 嵌入维度
        
        Returns:
            tensor: 位置编码
        """
        angle_rads = self.get_angles(
            position=tf.range(position, dtype=tf.float32)[:, tf.newaxis],
            i=tf.range(d_model, dtype=tf.float32)[tf.newaxis, :],
            d_model=d_model
        )
        
        # 应用正弦函数到偶数索引
        sines = tf.math.sin(angle_rads[:, 0::2])
        
        # 应用余弦函数到奇数索引
        cosines = tf.math.cos(angle_rads[:, 1::2])
        
        pos_encoding = tf.concat([sines, cosines], axis=-1)
        pos_encoding = pos_encoding[tf.newaxis, ...]
        
        return tf.cast(pos_encoding, tf.float32)
    
    def call(self, inputs):
        """前向传播
        
        Args:
            inputs (tensor): 输入张量
        
        Returns:
            tensor: 添加了位置编码的输出
        """
        return inputs + self.pos_encoding[:, :tf.shape(inputs)[1], :]

class TransformerStyleTransfer:
    """基于Transformer的音乐风格迁移模型"""
    
    def __init__(self, sequence_length=100, embed_dim=256, num_heads=4, ff_dim=512, model_path=None):
        """初始化Transformer风格迁移模型
        
        Args:
            sequence_length (int): 输入序列长度
            embed_dim (int): 嵌入维度
            num_heads (int): 注意力头数量
            ff_dim (int): 前馈网络维度
            model_path (str, optional): 预训练模型路径
        """
        self.sequence_length = sequence_length
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.model = None
        self.note_generator = LSTMMelodyGenerator(sequence_length=sequence_length)
        self.style_encodings = {}
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def build_model(self, vocab_size):
        """构建Transformer模型
        
        Args:
            vocab_size (int): 词汇表大小
        """
        # 输入层
        inputs = Input(shape=(self.sequence_length, 1))
        
        # 嵌入层
        embedding_layer = Dense(self.embed_dim)(inputs)
        
        # 位置编码
        pos_encoding = PositionalEncoding(self.sequence_length, self.embed_dim)(embedding_layer)
        
        # Transformer块
        x = pos_encoding
        for _ in range(2):  # 使用2个Transformer块
            x = TransformerBlock(self.embed_dim, self.num_heads, self.ff_dim)(x)
        
        # 输出层
        outputs = Dense(vocab_size, activation="softmax")(x)
        
        # 创建模型
        self.model = Model(inputs=inputs, outputs=outputs)
        
        # 编译模型
        self.model.compile(
            optimizer="adam",
            loss="categorical_crossentropy",
            metrics=["accuracy"]
        )
        
        # 打印模型摘要
        self.model.summary()
    
    def learn_style(self, midi_files, style_name, epochs=50, batch_size=32, save_path='model/transformer_style.h5'):
        """学习特定风格的音乐
        
        Args:
            midi_files (list): MIDI文件路径列表
            style_name (str): 风格名称
            epochs (int): 训练轮次
            batch_size (int): 批次大小
            save_path (str): 保存模型路径
        """
        # 使用LSTM模型处理MIDI文件
        self.note_generator.train(midi_files, epochs=1, batch_size=batch_size)
        
        # 获取LSTM模型提取的音符数据
        notes = self.note_generator.notes
        pitch_names = sorted(set(notes))
        vocab_size = len(pitch_names)
        
        # 准备序列
        network_input, network_output = self.note_generator.prepare_sequences(notes, pitch_names)
        
        # 构建Transformer模型
        if self.model is None:
            self.build_model(vocab_size)
        
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
            patience=5,
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
        
        # 提取并保存风格编码
        style_encoding = self.extract_style_embedding(network_input[:10])
        self.style_encodings[style_name] = style_encoding
        
        # 保存风格编码
        with open(os.path.join(os.path.dirname(save_path), 'style_encodings.pkl'), 'wb') as f:
            pickle.dump(self.style_encodings, f)
    
    def extract_style_embedding(self, input_sequences):
        """提取风格嵌入
        
        Args:
            input_sequences (ndarray): 输入序列
        
        Returns:
            ndarray: 风格嵌入向量
        """
        # 使用模型的中间层输出作为风格嵌入
        embedding_model = Model(
            inputs=self.model.input,
            outputs=self.model.get_layer(index=2).output  # 第一个Transformer块的输出
        )
        style_embedding = embedding_model.predict(input_sequences)
        return np.mean(style_embedding, axis=0)  # 对多个序列的嵌入取平均
    
    def transfer_style(self, source_notes, target_style, num_notes=200, temperature=1.0):
        """将源旋律转换为目标风格
        
        Args:
            source_notes (list): 源音符序列
            target_style (str): 目标风格名称
            num_notes (int): 要生成的音符数量
            temperature (float): 生成的随机性 (0.0-1.0)
        
        Returns:
            list: 风格迁移后的音符序列
        """
        if target_style not in self.style_encodings:
            raise ValueError(f"未找到风格 '{target_style}'，请先学习该风格")
        
        # 将源音符转换为网络输入
        source_indices = [self.note_generator.note_to_int[note] for note in source_notes]
        source_input = np.reshape(source_indices, (1, len(source_indices), 1))
        source_input = source_input / float(self.note_generator.vocab_size)
        
        # 获取源风格嵌入
        source_embedding = self.extract_style_embedding(source_input)
        
        # 获取目标风格嵌入
        target_embedding = self.style_encodings[target_style]
        
        # 创建一个中间模型来修改嵌入
        embedding_layer = self.model.layers[1]  # 嵌入层
        
        # 获取源序列的嵌入
        source_embed = embedding_layer(source_input)
        
        # 创建风格迁移嵌入（简单线性插值）
        style_weight = 0.7  # 风格权重
        transferred_embed = (1 - style_weight) * source_embed + style_weight * target_embedding
        
        # 使用修改后的嵌入生成输出
        transferred_output = []
        pattern = source_indices[-self.sequence_length:]
        
        for _ in range(num_notes):
            # 准备输入
            prediction_input = np.reshape(pattern, (1, len(pattern), 1))
            prediction_input = prediction_input / float(self.note_generator.vocab_size)
            
            # 获取嵌入
            embed = embedding_layer(prediction_input)
            
            # 应用风格迁移
            embed = (1 - style_weight) * embed + style_weight * target_embedding
            
            # 使用后续层生成输出
            x = self.model.layers[2](embed)  # 位置编码
            x = self.model.layers[3](x)  # 第一个Transformer块
            x = self.model.layers[4](x)  # 第二个Transformer块
            prediction = self.model.layers[5](x)[0, -1]  # 输出层
            
            # 应用温度采样
            prediction = self._apply_temperature(prediction, temperature)
            
            # 采样下一个音符
            index = np.random.choice(range(len(prediction)), p=prediction)
            result = self.note_generator.int_to_note[index]
            transferred_output.append(result)
            
            # 更新种子序列
            pattern.append(index)
            pattern = pattern[1:]
        
        return transferred_output
    
    def generate_midi_with_style(self, output_path, source_notes=None, target_style=None, num_notes=200, temperature=1.0, tempo_bpm=120, instrument_name='Piano'):
        """生成具有特定风格的MIDI文件
        
        Args:
            output_path (str): 输出MIDI文件路径
            source_notes (list, optional): 源音符，如果为None则随机选择
            target_style (str): 目标风格名称
            num_notes (int): 要生成的音符数量
            temperature (float): 生成的随机性 (0.0-1.0)
            tempo_bpm (int): 曲目速度 (每分钟拍数)
            instrument_name (str): 乐器名称
        """
        if self.model is None:
            raise ValueError("模型尚未构建或加载")
        
        if source_notes is None:
            # 随机选择种子序列
            start = np.random.randint(0, len(self.note_generator.notes) - self.sequence_length)
            source_notes = self.note_generator.notes[start:start + self.sequence_length]
        
        # 如果提供了目标风格，执行风格迁移
        if target_style:
            prediction_output = self.transfer_style(source_notes, target_style, num_notes, temperature)
        else:
            # 否则使用LSTM生成器生成旋律
            prediction_output = self.note_generator.generate_melody(source_notes, num_notes, temperature)
        
        # 使用LSTM生成器的函数来创建MIDI文件
        self.note_generator.generate_midi(output_path, seed_notes=None, num_notes=0, tempo_bpm=tempo_bpm, instrument_name=instrument_name)
        
        # 注意：由于我们已经生成了旋律，所以上面的调用主要是创建MIDI文件结构
        # 现在我们需要替换生成的音符与我们的风格迁移结果
        
        # 这里简化处理，直接使用LSTM的generate_midi功能
        # 在实际应用中，你可能需要更精确地控制MIDI生成过程
        from music21 import stream, tempo, instrument, note, chord
        
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
        # 加载自定义层
        custom_objects = {
            'TransformerBlock': TransformerBlock,
            'PositionalEncoding': PositionalEncoding
        }
        
        # 加载模型
        self.model = load_model(model_path, custom_objects=custom_objects)
        
        # 加载风格编码
        style_encodings_path = os.path.join(os.path.dirname(model_path), 'style_encodings.pkl')
        if os.path.exists(style_encodings_path):
            with open(style_encodings_path, 'rb') as f:
                self.style_encodings = pickle.load(f)
        
        # 继承LSTM生成器的音符映射
        self.note_generator.load_model(os.path.join(os.path.dirname(model_path), 'lstm_melody.h5'))
    
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
        
        # 保存风格编码
        with open(os.path.join(os.path.dirname(model_path), 'style_encodings.pkl'), 'wb') as f:
            pickle.dump(self.style_encodings, f)
        
        # 保存LSTM生成器
        self.note_generator.save_model(os.path.join(os.path.dirname(model_path), 'lstm_melody.h5'))
    
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