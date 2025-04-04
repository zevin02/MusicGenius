import os
import glob
import numpy as np
import pretty_midi
from music21 import converter, instrument, note, chord, stream
import librosa

def list_midi_files(directory, recursive=True):
    """列出目录中的所有MIDI文件
    
    Args:
        directory (str): 目录路径
        recursive (bool): 是否递归搜索子目录
    
    Returns:
        list: MIDI文件路径列表
    """
    pattern = os.path.join(directory, '**', '*.mid') if recursive else os.path.join(directory, '*.mid')
    midi_files = glob.glob(pattern, recursive=recursive)
    
    pattern = os.path.join(directory, '**', '*.midi') if recursive else os.path.join(directory, '*.midi')
    midi_files.extend(glob.glob(pattern, recursive=recursive))
    
    return sorted(midi_files)

def midi_to_notes(midi_path):
    """从MIDI文件中提取音符信息
    
    Args:
        midi_path (str): MIDI文件路径
    
    Returns:
        list: 音符对象列表
    """
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    notes = []
    
    for instrument in midi_data.instruments:
        # 跳过鼓声轨道
        if instrument.is_drum:
            continue
            
        for note in instrument.notes:
            notes.append({
                'pitch': note.pitch,
                'start': note.start,
                'end': note.end,
                'velocity': note.velocity,
                'instrument': instrument.program
            })
    
    return sorted(notes, key=lambda x: x['start'])

def notes_to_midi(notes, output_path, tempo=120, program=0):
    """将音符信息转换为MIDI文件
    
    Args:
        notes (list): 音符对象列表
        output_path (str): 输出MIDI文件路径
        tempo (int): 曲目速度 (BPM)
        program (int): 乐器编号 (0-127)
    """
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    instrument = pretty_midi.Instrument(program=program)
    
    for note_info in notes:
        note = pretty_midi.Note(
            velocity=note_info.get('velocity', 100),
            pitch=note_info['pitch'],
            start=note_info['start'],
            end=note_info['end']
        )
        instrument.notes.append(note)
    
    midi.instruments.append(instrument)
    midi.write(output_path)

def midi_to_audio(midi_path, output_path, sr=22050):
    """将MIDI文件转换为音频文件
    
    Args:
        midi_path (str): MIDI文件路径
        output_path (str): 输出音频文件路径
        sr (int): 采样率
    """
    import fluidsynth
    import soundfile as sf
    
    fs = fluidsynth.Synth()
    fs.start(driver="pulseaudio") # 或者其他驱动，如'alsa', 'coreaudio'等
    
    # 加载音库（需要事先安装SoundFont文件）
    sf2_path = '/usr/share/sounds/sf2/FluidR3_GM.sf2'  # 调整为您的sf2文件路径
    sfid = fs.sfload(sf2_path)
    fs.program_select(0, sfid, 0, 0)
    
    # 合成音频
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    audio_data = midi_data.fluidsynth(fs=sr)
    
    # 保存音频
    sf.write(output_path, audio_data, sr)
    
    # 清理
    fs.delete()

def extract_chords(midi_path):
    """从MIDI文件中提取和弦进行
    
    Args:
        midi_path (str): MIDI文件路径
    
    Returns:
        list: 和弦列表，每个和弦是一个(时间, 和弦名称)元组
    """
    midi = converter.parse(midi_path)
    chords = []
    
    # 提取和弦
    for element in midi.flat.getElementsByClass('Chord'):
        chords.append((element.offset, element.pitchedCommonName))
    
    return chords

def extract_key(midi_path):
    """从MIDI文件中提取调式
    
    Args:
        midi_path (str): MIDI文件路径
    
    Returns:
        tuple: (调式, 大调/小调)
    """
    from music21 import analysis
    
    midi = converter.parse(midi_path)
    key = analysis.discrete.analyzeStream(midi, 'key')
    
    if key is None:
        return None, None
    
    return key.tonic.name, key.mode

def get_tempo(midi_path):
    """获取MIDI文件的速度
    
    Args:
        midi_path (str): MIDI文件路径
    
    Returns:
        float: 速度 (BPM)
    """
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    return midi_data.get_tempo_changes()[1][0] if len(midi_data.get_tempo_changes()[1]) > 0 else 120.0

def get_instruments(midi_path):
    """获取MIDI文件中的乐器信息
    
    Args:
        midi_path (str): MIDI文件路径
    
    Returns:
        list: 乐器对象列表
    """
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    instruments = []
    
    for i, inst in enumerate(midi_data.instruments):
        instruments.append({
            'index': i,
            'name': pretty_midi.program_to_instrument_name(inst.program) if not inst.is_drum else 'Drums',
            'is_drum': inst.is_drum,
            'program': inst.program,
            'note_count': len(inst.notes)
        })
    
    return instruments

def quantize_notes(notes, ticks_per_beat=480):
    """量化音符时值
    
    Args:
        notes (list): 音符对象列表
        ticks_per_beat (int): 每拍的tick数
    
    Returns:
        list: 量化后的音符对象列表
    """
    quantized_notes = []
    
    for note_info in notes:
        # 将时间转换为tick
        start_tick = round(note_info['start'] * ticks_per_beat)
        end_tick = round(note_info['end'] * ticks_per_beat)
        
        # 量化到最近的tick
        start_tick = round(start_tick / 60) * 60
        end_tick = round(end_tick / 60) * 60
        
        # 转换回秒
        quantized_note = note_info.copy()
        quantized_note['start'] = start_tick / ticks_per_beat
        quantized_note['end'] = end_tick / ticks_per_beat
        
        quantized_notes.append(quantized_note)
    
    return quantized_notes

def transpose_midi(midi_path, output_path, semitones):
    """转调MIDI文件
    
    Args:
        midi_path (str): 输入MIDI文件路径
        output_path (str): 输出MIDI文件路径
        semitones (int): 转调半音数
    """
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    
    for instrument in midi_data.instruments:
        for note in instrument.notes:
            note.pitch += semitones
    
    midi_data.write(output_path)

def merge_midi_files(midi_paths, output_path, align='sequential'):
    """合并多个MIDI文件
    
    Args:
        midi_paths (list): MIDI文件路径列表
        output_path (str): 输出MIDI文件路径
        align (str): 合并方式，'sequential'顺序排列，'parallel'同时播放
    """
    if align == 'sequential':
        # 顺序合并
        merged_midi = pretty_midi.PrettyMIDI()
        current_time = 0
        
        for midi_path in midi_paths:
            midi_data = pretty_midi.PrettyMIDI(midi_path)
            max_end_time = 0
            
            for instrument in midi_data.instruments:
                new_instrument = pretty_midi.Instrument(program=instrument.program, is_drum=instrument.is_drum)
                
                for note in instrument.notes:
                    new_note = pretty_midi.Note(
                        velocity=note.velocity,
                        pitch=note.pitch,
                        start=note.start + current_time,
                        end=note.end + current_time
                    )
                    new_instrument.notes.append(new_note)
                    max_end_time = max(max_end_time, note.end)
                
                merged_midi.instruments.append(new_instrument)
            
            current_time += max_end_time
        
        merged_midi.write(output_path)
    
    elif align == 'parallel':
        # 并行合并（同时播放）
        merged_midi = pretty_midi.PrettyMIDI()
        
        for midi_path in midi_paths:
            midi_data = pretty_midi.PrettyMIDI(midi_path)
            
            for instrument in midi_data.instruments:
                new_instrument = pretty_midi.Instrument(program=instrument.program, is_drum=instrument.is_drum)
                new_instrument.notes = instrument.notes
                merged_midi.instruments.append(new_instrument)
        
        merged_midi.write(output_path)
    
    else:
        raise ValueError("align参数必须是'sequential'或'parallel'")

def midi_to_spectrogram(midi_path, sr=22050, n_fft=2048, hop_length=512):
    """将MIDI文件转换为频谱图
    
    Args:
        midi_path (str): MIDI文件路径
        sr (int): 采样率
        n_fft (int): FFT窗口大小
        hop_length (int): 帧移
    
    Returns:
        ndarray: 频谱图
    """
    # 先将MIDI转换为音频
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    audio_data = midi_data.fluidsynth(fs=sr)
    
    # 计算频谱图
    spectrogram = librosa.feature.melspectrogram(y=audio_data, sr=sr, n_fft=n_fft, hop_length=hop_length)
    spectrogram_db = librosa.power_to_db(spectrogram, ref=np.max)
    
    return spectrogram_db

def extract_midi_features(midi_path):
    """提取MIDI文件的特征
    
    Args:
        midi_path (str): MIDI文件路径
    
    Returns:
        dict: 特征字典
    """
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    
    # 注意密度（每秒的平均音符数）
    note_density = len(midi_data.get_onsets()) / midi_data.get_end_time() if midi_data.get_end_time() > 0 else 0
    
    # 音高范围
    all_notes = []
    for instrument in midi_data.instruments:
        if not instrument.is_drum:
            all_notes.extend([note.pitch for note in instrument.notes])
    
    pitch_range = max(all_notes) - min(all_notes) if all_notes else 0
    
    # 和弦密度（同时弹奏的平均音符数）
    if all_notes:
        onsets = midi_data.get_onsets()
        chord_density = len(all_notes) / len(onsets) if len(onsets) > 0 else 0
    else:
        chord_density = 0
    
    # 平均音符持续时间
    note_durations = []
    for instrument in midi_data.instruments:
        note_durations.extend([note.end - note.start for note in instrument.notes])
    
    avg_note_duration = sum(note_durations) / len(note_durations) if note_durations else 0
    
    return {
        'note_density': note_density,
        'pitch_range': pitch_range,
        'chord_density': chord_density,
        'avg_note_duration': avg_note_duration,
        'tempo': midi_data.get_tempo_changes()[1][0] if len(midi_data.get_tempo_changes()[1]) > 0 else 120.0,
        'duration': midi_data.get_end_time(),
        'num_instruments': len(midi_data.instruments),
        'num_notes': sum(len(instrument.notes) for instrument in midi_data.instruments)
    }


def wav_to_midi(wav_path, midi_path):
    """将WAV文件转换为MIDI文件"""
    # 加载音频文件
    y, sr = librosa.load(wav_path)

    # 使用音高检测算法（如音高跟踪）来提取音符
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

    # 创建一个新的MIDI对象
    midi_data = pretty_midi.PrettyMIDI()

    # 创建一个乐器
    instrument = pretty_midi.Instrument(program=0)  # 0表示钢琴

    # 遍历音高数据，创建音符
    for t in range(pitches.shape[1]):
        for p in range(pitches.shape[0]):
            if pitches[p, t] > 0:  # 检查音高是否有效
                note = pretty_midi.Note(
                    velocity=100,  # 音量
                    pitch=int(pitches[p, t]),  # 音高
                    start=t * (1.0 / sr),  # 开始时间
                    end=(t + 1) * (1.0 / sr)  # 结束时间
                )
                instrument.notes.append(note)

    # 将乐器添加到MIDI数据中
    midi_data.instruments.append(instrument)

    # 保存MIDI文件
    midi_data.write(midi_path)