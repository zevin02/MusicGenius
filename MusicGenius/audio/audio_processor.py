import numpy as np
import librosa
import matplotlib.pyplot as plt
import soundfile as sf
from scipy import signal

class AudioProcessor:
    """音频处理类，提供音频分析和处理功能"""
    
    def __init__(self, sr=22050, n_fft=2048, hop_length=512):
        """初始化音频处理器
        
        Args:
            sr (int): 采样率
            n_fft (int): FFT窗口大小
            hop_length (int): 帧移
        """
        self.sr = sr
        self.n_fft = n_fft
        self.hop_length = hop_length
    
    def load_audio(self, file_path, sr=None):
        """加载音频文件
        
        Args:
            file_path (str): 音频文件路径
            sr (int, optional): 目标采样率，默认为None（使用文件原始采样率）
        
        Returns:
            tuple: (音频数据, 采样率)
        """
        if sr is None:
            sr = self.sr
        
        y, sr = librosa.load(file_path, sr=sr)
        return y, sr
    
    def save_audio(self, y, file_path, sr=None):
        """保存音频文件
        
        Args:
            y (ndarray): 音频数据
            file_path (str): 保存路径
            sr (int, optional): 采样率，默认为None（使用预设采样率）
        """
        if sr is None:
            sr = self.sr
        
        sf.write(file_path, y, sr)
    
    def extract_features(self, y, sr=None):
        """提取音频特征
        
        Args:
            y (ndarray): 音频数据
            sr (int, optional): 采样率
        
        Returns:
            dict: 包含各种音频特征的字典
        """
        if sr is None:
            sr = self.sr
        
        # 梅尔频谱
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length)
        
        # 色度特征
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length)
        
        # 过零率
        zcr = librosa.feature.zero_crossing_rate(y, hop_length=self.hop_length)
        
        # 频谱质心
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length)
        
        # MFCC
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length, n_mfcc=13)
        
        # 节拍检测
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        
        # 基频估计
        f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), 
                                                     fmax=librosa.note_to_hz('C7'), sr=sr)
        
        features = {
            'mel_spectrogram': mel_spec,
            'chroma': chroma,
            'zero_crossing_rate': zcr,
            'spectral_centroid': spectral_centroid,
            'mfcc': mfcc,
            'tempo': tempo,
            'beat_times': beat_times,
            'f0': f0,
            'voiced_flag': voiced_flag,
            'voiced_probs': voiced_probs
        }
        
        return features
    
    def analyze_rhythm(self, y, sr=None):
        """分析音频的节奏特征
        
        Args:
            y (ndarray): 音频数据
            sr (int, optional): 采样率
        
        Returns:
            dict: 节奏特征
        """
        if sr is None:
            sr = self.sr
        
        # 检测节拍
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        
        # 计算节拍强度
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        pulse = librosa.beat.plp(onset_envelope=onset_env, sr=sr)
        
        # 计算节奏模式
        rhythm_pattern = np.correlate(onset_env, onset_env, mode='full')
        rhythm_pattern = rhythm_pattern[len(rhythm_pattern)//2:]
        
        return {
            'tempo': tempo,
            'beat_times': beat_times,
            'beat_frames': beat_frames,
            'onset_env': onset_env,
            'pulse': pulse,
            'rhythm_pattern': rhythm_pattern
        }
    
    def analyze_harmony(self, y, sr=None):
        """分析音频的和声特征
        
        Args:
            y (ndarray): 音频数据
            sr (int, optional): 采样率
        
        Returns:
            dict: 和声特征
        """
        if sr is None:
            sr = self.sr
        
        # 计算色度特征
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_fft=self.n_fft, hop_length=self.hop_length)
        
        # 估计和弦
        chroma_avg = np.mean(chroma, axis=1)
        
        # 调性强度
        key_strengths = librosa.key_strength(y=y, sr=sr)
        key_index = np.argmax(np.mean(key_strengths, axis=1))
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        estimated_key = keys[key_index % 12]
        estimated_mode = 'major' if key_index < 12 else 'minor'
        
        return {
            'chroma': chroma,
            'chroma_avg': chroma_avg,
            'key_strengths': key_strengths,
            'estimated_key': estimated_key,
            'estimated_mode': estimated_mode
        }
    
    def plot_waveform(self, y, sr=None, title="Waveform"):
        """绘制音频波形图
        
        Args:
            y (ndarray): 音频数据
            sr (int, optional): 采样率
            title (str, optional): 图表标题
        """
        if sr is None:
            sr = self.sr
        
        plt.figure(figsize=(12, 4))
        librosa.display.waveshow(y, sr=sr)
        plt.title(title)
        plt.tight_layout()
        
    def plot_spectrogram(self, y, sr=None, title="Spectrogram"):
        """绘制频谱图
        
        Args:
            y (ndarray): 音频数据
            sr (int, optional): 采样率
            title (str, optional): 图表标题
        """
        if sr is None:
            sr = self.sr
        
        D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
        plt.figure(figsize=(12, 4))
        librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log')
        plt.colorbar(format='%+2.0f dB')
        plt.title(title)
        plt.tight_layout()

    def plot_features(self, features, title_prefix=""):
        """绘制提取的特征
        
        Args:
            features (dict): 特征字典
            title_prefix (str, optional): 标题前缀
        """
        plt.figure(figsize=(12, 8))
        
        # 绘制梅尔频谱
        plt.subplot(3, 2, 1)
        librosa.display.specshow(librosa.power_to_db(features['mel_spectrogram'], ref=np.max),
                                y_axis='mel', x_axis='time')
        plt.title(f'{title_prefix}Mel Spectrogram')
        plt.colorbar(format='%+2.0f dB')
        
        # 绘制色度图
        plt.subplot(3, 2, 2)
        librosa.display.specshow(features['chroma'], y_axis='chroma', x_axis='time')
        plt.title(f'{title_prefix}Chromagram')
        plt.colorbar()
        
        # 绘制MFCC
        plt.subplot(3, 2, 3)
        librosa.display.specshow(features['mfcc'], x_axis='time')
        plt.title(f'{title_prefix}MFCC')
        plt.colorbar()
        
        # 绘制频谱质心
        plt.subplot(3, 2, 4)
        plt.semilogy(features['spectral_centroid'].T)
        plt.title(f'{title_prefix}Spectral Centroid')
        plt.xlabel('Time')
        plt.ylabel('Hz')
        
        # 绘制过零率
        plt.subplot(3, 2, 5)
        plt.plot(features['zero_crossing_rate'].T)
        plt.title(f'{title_prefix}Zero Crossing Rate')
        plt.xlabel('Time')
        
        # 绘制F0基频
        plt.subplot(3, 2, 6)
        plt.plot(features['f0'])
        plt.title(f'{title_prefix}F0 Frequency')
        plt.xlabel('Time')
        plt.ylabel('Hz')
        
        plt.tight_layout() 