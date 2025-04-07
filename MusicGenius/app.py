#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MusicGenius - 智能音乐创作APP
主入口文件
"""

import os
import sys
import json
import shutil
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
import argparse  # 新增：导入 argparse 模块

# 添加当前目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

# 导入相关模块
from .core.music_creator import MusicCreator
from .core.music_database import MusicDatabase
from .utils import midi_utils

class MusicGeniusApp:
    """MusicGenius应用主类"""
    
    def __init__(self, model_dir='models', output_dir='output', 
                 db_host='localhost', db_user='root', db_password='', db_name='music_genius',
                 upload_folder='uploads', static_folder='ui/static', template_folder='ui/templates',
                 host='0.0.0.0', port=5000, debug=True):
        """初始化应用
        
        Args:
            model_dir (str): 模型目录
            output_dir (str): 输出目录
            db_host (str): MySQL服务器地址
            db_user (str): MySQL用户名
            db_password (str): MySQL密码
            db_name (str): MySQL数据库名
            upload_folder (str): 上传文件目录
            static_folder (str): 静态文件目录
            template_folder (str): 模板文件目录
            host (str): 主机地址
            port (int): 端口号
            debug (bool): 是否开启调试模式
        """
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_dir = model_dir
        self.output_dir = output_dir
        self.upload_folder = upload_folder
        
        # 确保目录存在
        os.makedirs(model_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(upload_folder, exist_ok=True)
        
        # 创建核心组件
        self.music_creator = MusicCreator(model_dir=model_dir, output_dir=output_dir)
        self.music_db = MusicDatabase(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        
    # 创建Flask应用
        self.app = Flask(__name__,
                         static_folder=static_folder,
                         template_folder=template_folder)
        self.app.config['SECRET_KEY'] = 'music_genius_secret_key'
        self.app.config['UPLOAD_FOLDER'] = upload_folder
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传大小为16MB
        
        # 注册路由
        self._register_routes()
        
        # 运行设置
        self.host = host
        self.port = port
        self.debug = debug
        
        # 注册自定义Jinja2过滤器
        @self.app.template_filter('basename')
        def basename_filter(path):
            """获取文件路径的基本名称"""
            if not path:
                return ''
            return os.path.basename(path)
        
        @self.app.template_filter('format_datetime')
        def format_datetime_filter(value):
            """格式化日期时间"""
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass
            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%d %H:%M:%S')
            return value
    
    def _register_routes(self):
        """注册所有路由"""
        
        @self.app.route('/')
        def index():
            """主页"""
            # 获取统计信息
            stats = {
                'total_tracks': self.music_db.get_total_tracks(),
                'genres': self.music_db.get_all_genres(),
                'instruments': self.music_creator.get_available_instruments()
            }
            
            # 获取可用的风格
            available_styles = self.music_creator.get_available_styles()
            
            # 获取可用的乐器
            available_instruments = self.music_creator.get_available_instruments()
        
            return render_template('index.html', 
                              stats=stats, 
                              available_styles=available_styles,
                              available_instruments=available_instruments)
    
        @self.app.route('/library')
        def library():
            """音乐库页面"""
            print('library')
            try:
                return render_template('library.html')
            except Exception as e:
                print(f"Error in library route: {str(e)}")
                return render_template('error.html', error=str(e))
        
        @self.app.route('/track/<int:track_id>')
        def track_detail(track_id):
            """曲目详情页面"""
            track = self.music_db.get_track(track_id)
            if not track:
                flash('曲目不存在', 'error')
                return redirect(url_for('library'))
            
            # 分析曲目
            try:
                analysis = self.music_creator.analyze_track(track['filepath'])
            except Exception as e:
                analysis = {'error': str(e)}
            
            return render_template('track_detail.html', track=track, analysis=analysis)
        
        @self.app.route('/create')
        def create():
            """创作页面"""
            # 获取可用的风格
            available_styles = self.music_creator.get_available_styles()
            
            # 获取可用的乐器
            available_instruments = self.music_creator.get_available_instruments()
            
            # 可用效果列表
            available_effects = [
                {'name': '延迟', 'description': '添加回声效果'},
                {'name': '合唱', 'description': '添加合唱效果'},
                {'name': '混响', 'description': '添加空间感'},
                {'name': '失真', 'description': '添加失真效果'},
                {'name': '均衡器', 'description': '调整音色'}
            ]
            
            return render_template('create.html',
                                available_styles=available_styles,
                                available_instruments=available_instruments,
                                available_effects=available_effects)
        
        @self.app.route('/generate_melody', methods=['POST'])
        def generate_melody():
            """生成旋律API"""
            try:
                # 获取参数
                num_notes = int(request.form.get('num_notes', 200))  # 音符数量
                temperature = float(request.form.get('temperature', 1.0))  # 随机性参数
                tempo_bpm = int(request.form.get('tempo_bpm', 120))  # 节拍数
                instrument_name = request.form.get('instrument', 'Piano')  # 乐器
                generator_type = request.form.get('generator_type', 'simple')  # 生成器类型：'simple' 或 'lstm'
                style = request.form.get('style', '古典')  # 音乐风格
                
                # 解析特效参数
                effects = []
                effects_config = {}
                # 音频效果器参数配置模块
                # 功能：工具用户表单选择激活音频特效，并配置dsp算法参数
                # 混响
                if 'reverb' in request.form and request.form['reverb'] == 'on':
                    print('添加混响效果')
                    # schroeder 混响模型参数
                    effects.append('reverb')
                    effects_config['reverb'] = {
                        'room_size': float(request.form.get('reverb_room_size', 0.8)), # 早期放射密度
                        'damping': float(request.form.get('reverb_damping', 0.5)), # 混响尾音的明亮度
                        'wet_level': float(request.form.get('reverb_wet_level', 0.3)), # 体现声场融合度
                        'dry_level': float(request.form.get('reverb_dry_level', 0.7)) # 声音清晰度
                    }
                    # 理论依据：Schroeder人工混响算法（全通滤波器+梳状滤波器串联）
                
                # 延迟
                if 'delay' in request.form and request.form['delay'] == 'on':
                    print('添加延迟效果')
                    # 延迟线(Delay Line)参数
                    effects.append('delay')
                    effects_config['delay'] = {
                        'delay_time': float(request.form.get('delay_time', 0.5)), #对应声波反射路径长度
                        'feedback': float(request.form.get('delay_feedback', 0.5)), #决定回声衰减速率
                        'wet_level': float(request.form.get('delay_wet_level', 0.5)),# 延迟信号混合比
                        'dry_level': float(request.form.get('delay_dry_level', 0.5))# 原始信号保留比
                    }
                    # 技术实现：环形缓冲区+反馈网络，数学表达式 y[n] = x[n] + α·y[n−D]
                
                # TODO ：合唱 有问题
                if 'chorus' in request.form and request.form['chorus'] == 'on':
                    print('添加合唱效果')
                    effects.append('chorus')
                    effects_config['chorus'] = {
                        'rate': float(request.form.get('chorus_rate', 0.5)), # LFO调制频率 (Hz)，典型范围0.1-5Hz
                        'depth': float(request.form.get('chorus_depth', 0.002)), # 调制深度（秒），对应音高偏移量（±半音）
                        'voices': int(request.form.get('chorus_voices', 3)) # 虚拟声源数量，多声道叠加产生空间感
                    }
                    # 核心算法：多延迟线并行 + 低频振荡器(LFO)调制
                    # 常见问题：未做抗混叠处理会导致高频失真
                
                # 失真
                if 'distortion' in request.form and request.form['distortion'] == 'on':
                    print('添加失真效果')
                    # 非线性波形塑形参数
                    effects.append('distortion')
                    effects_config['distortion'] = {
                        'amount': float(request.form.get('distortion_amount', 0.5)),    # 失真强度 (0.0-1.0)，对应波形削波程度
                        'wet_level': float(request.form.get('distortion_wet_level', 0.5)),  # 失真信号混合比
                        'dry_level': float(request.form.get('distortion_dry_level', 0.5)) # 原始信号保留比
                    }
                
                # 均衡器
                if 'eq' in request.form and request.form['eq'] == 'on':
                    print('添加均衡器效果')

                    effects.append('eq')
                    effects_config['eq'] = {
                        'low_gain': float(request.form.get('eq_low_gain', 1.0)),# 低频增益（Hz范围: 20-250Hz）
                        'mid_gain': float(request.form.get('eq_mid_gain', 1.0)),# 中频增益（Hz范围: 250-4kHz）
                        'high_gain': float(request.form.get('eq_high_gain', 1.0)) # 高频增益（Hz范围: 4k-20kHz）
                    }
                    # 实现方案：并联二阶IIR滤波器组（低通/带通/高通）
      
                # 生成MIDI文件
                output_path = self.music_creator.generate_melody(
                    style=style,
                    num_notes=num_notes,
                    temperature=temperature,
                    tempo_bpm=tempo_bpm,
                    instrument_name=instrument_name,
                    generator_type=generator_type,
                    effects=effects if effects else None,
                    effects_config=effects_config if effects_config else None
                )
                print('finish make')
                # 获取相对路径
                relative_path = os.path.relpath(output_path, self.output_dir)# 获取了文件名
                midi_filename='temp.mid'
                self.music_db.add_track(filepath=midi_filename,title=relative_path,genre=style)
                os.remove(midi_filename)
                return jsonify({
                    'success': True,
                    'midi_file': relative_path,
                    'message': '旋律生成成功！'
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'生成旋律失败: {str(e)}'
                })
            
        @self.app.route('/transfer_style', methods=['POST'])
        def transfer_style():
            """风格迁移API"""
            try:
                # 确保上传文件目录存在
                os.makedirs(self.app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # 获取上传的MIDI文件
                if 'midi_file' not in request.files:
                    return jsonify({
                        'success': False,
                        'message': '没有上传MIDI文件'
                    })
                
                file = request.files['midi_file']
                if file.filename == '':
                    return jsonify({
                        'success': False,
                        'message': '没有选择文件'
                    })
                
                # 保存上传的文件
                filename = secure_filename(file.filename)
                upload_path = os.path.join(self.app.config['UPLOAD_FOLDER'], filename)
                file.save(upload_path)
                
                # 获取参数
                target_style = request.form.get('style', '')
                temperature = float(request.form.get('temperature', 1.0))
                tempo_bpm = request.form.get('tempo_bpm', '')
                tempo_bpm = int(tempo_bpm) if tempo_bpm.isdigit() else None
                
                # 执行风格迁移
                output_path = self.music_creator.transfer_style(
                    midi_file=upload_path,
                    target_style=target_style,
                    temperature=temperature,
                    tempo_bpm=tempo_bpm
                )
                
                # 获取相对路径
                relative_path = os.path.relpath(output_path, self.output_dir)
                return jsonify({
                    'success': True,
                    'midi_file': relative_path,
                    'message': '风格迁移成功！'
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'风格迁移失败: {str(e)}'
                })
        
        @self.app.route('/apply_effects', methods=['POST'])
        def apply_effects():
            """应用音频特效API"""
            try:
                # 确保上传文件目录存在
                os.makedirs(self.app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # 获取上传的MIDI文件
                if 'midi_file' not in request.files:
                    return jsonify({
                        'success': False,
                        'message': '没有上传MIDI文件'
                    })
                
                file = request.files['midi_file']
                if file.filename == '':
                    return jsonify({
                        'success': False,
                        'message': '没有选择文件'
                    })
                
                # 保存上传的文件
                filename = secure_filename(file.filename)
                upload_path = os.path.join(self.app.config['UPLOAD_FOLDER'], filename)
                file.save(upload_path)
                
                # 获取特效参数
                effects_params = {}
                
                # 混响
                if 'reverb' in request.form and request.form['reverb'] == 'on':
                    print('reverb')
                    effects_params['reverb'] = {
                        'room_size': float(request.form.get('reverb_room_size', 0.8)),
                        'damping': float(request.form.get('reverb_damping', 0.5)),
                        'wet_level': float(request.form.get('reverb_wet_level', 0.3)),
                        'dry_level': float(request.form.get('reverb_dry_level', 0.7))
                    }
                
                # 延迟
                if 'delay' in request.form and request.form['delay'] == 'on':
                    print('delay')

                    effects_params['delay'] = {
                        'delay_time': float(request.form.get('delay_time', 0.5)),
                        'feedback': float(request.form.get('delay_feedback', 0.5)),
                        'wet_level': float(request.form.get('delay_wet_level', 0.5)),
                        'dry_level': float(request.form.get('delay_dry_level', 0.5))
                    }
                
                # 合唱
                if 'chorus' in request.form and request.form['chorus'] == 'on':
                    print('chorus')

                    effects_params['chorus'] = {
                        'rate': float(request.form.get('chorus_rate', 0.5)),
                        'depth': float(request.form.get('chorus_depth', 0.002)),
                        'wet_level': float(request.form.get('chorus_wet_level', 0.5)),
                        'dry_level': float(request.form.get('chorus_dry_level', 0.5)),
                        'voices': int(request.form.get('chorus_voices', 3))
                    }
                
                # 失真
                if 'distortion' in request.form and request.form['distortion'] == 'on':
                    print('distortion')

                    effects_params['distortion'] = {
                        'amount': float(request.form.get('distortion_amount', 0.5)),
                        'wet_level': float(request.form.get('distortion_wet_level', 0.5)),
                        'dry_level': float(request.form.get('distortion_dry_level', 0.5))
                    }
                
                # 应用特效
                output_path = self.music_creator.apply_effects(
                    midi_file=upload_path,
                    effects_config=effects_params
                )
                
                # 获取相对路径
                relative_path = os.path.relpath(output_path, self.output_dir)
                
                return jsonify({
                    'success': True,
                    'audio_file': relative_path,
                    'message': '音频特效应用成功！'
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'应用特效失败: {str(e)}'
                })
        
        @self.app.route('/generate_accompaniment', methods=['POST'])
        def generate_accompaniment():
            """生成伴奏API"""
            try:
                # 确保上传文件目录存在
                os.makedirs(self.app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # 获取上传的MIDI文件
                if 'midi_file' not in request.files:
                    return jsonify({
                        'success': False,
                        'message': '没有上传MIDI文件'
                    })
                
                file = request.files['midi_file']
                if file.filename == '':
                    return jsonify({
                        'success': False,
                        'message': '没有选择文件'
                    })
            
                # 保存上传的文件
                filename = secure_filename(file.filename)
                upload_path = os.path.join(self.app.config['UPLOAD_FOLDER'], filename)
                file.save(upload_path)
                
                # 获取参数
                style = request.form.get('accompaniment_style', 'pop')
                
                # 生成伴奏
                output_path = self.music_creator.generate_accompaniment(
                    melody_midi=upload_path,
                    style=style
                )
                
                # 获取相对路径
                relative_path = os.path.relpath(output_path, self.output_dir)
                
                return jsonify({
                    'success': True,
                    'midi_file': relative_path,
                    'message': '伴奏生成成功！'
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'生成伴奏失败: {str(e)}'
                })
        
        @self.app.route('/merge_tracks', methods=['POST'])
        def merge_tracks():
            """合并轨道API"""
            try:
                # 确保上传文件目录存在
                os.makedirs(self.app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # 获取上传的MIDI文件
                if 'midi_files[]' not in request.files:
                    return jsonify({
                        'success': False,
                        'message': '没有上传MIDI文件'
                    })
                
                files = request.files.getlist('midi_files[]')
                if not files or files[0].filename == '':
                    return jsonify({
                        'success': False,
                        'message': '没有选择文件'
                    })
                
                # 保存上传的文件
                midi_paths = []
                for file in files:
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(self.app.config['UPLOAD_FOLDER'], filename)
                    file.save(upload_path)
                    midi_paths.append(upload_path)
                
                # 获取参数
                align = request.form.get('align', 'sequential')
                
                # 合并轨道
                output_path = self.music_creator.merge_tracks(
                    midi_files=midi_paths,
                    align=align
                )
                
                # 获取相对路径
                relative_path = os.path.relpath(output_path, self.output_dir)
            
                return jsonify({
                    'success': True,
                        'midi_file': relative_path,
                        'message': '轨道合并成功！'
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                        'message': f'合并轨道失败: {str(e)}'
                    })
        
        @self.app.route('/output/<path:filename>')
        def download_file(filename):
            """下载输出文件"""
            try:
                print(f"Attempting to download file: {filename}")
                print(f"Output directory: {self.output_dir}")
                print(f"Full path: {os.path.join(self.output_dir, filename)}")
                
                # 检查文件是否存在
                full_path1 = os.path.join(self.output_dir, filename)
                full_path = os.path.join(self.base_dir, full_path1)
                print(full_path)
                if not os.path.exists(full_path):
                    print(f"File not found: {full_path}")
                    return jsonify({
                        'success': False,
                        'message': f'File not found: {filename}'
                    }), 404
                    
                # 如果文件存在，返回文件
                dire = os.path.join(self.base_dir, self.output_dir)
                #!!! 必须要用绝对路径
                return send_from_directory(
                    directory=dire,
                    path=filename,
                    as_attachment=True,
                    mimetype='audio/wav'
                )
            except Exception as e:
                print(f"Error in download_file: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'Error downloading file: {str(e)}'
                }), 500
            
        @self.app.route('/add_to_library', methods=['POST'])
        def add_to_library():
            """添加到音乐库API"""
            try:
                # 获取参数
                filepath = request.form.get('filepath', '')
                title = request.form.get('title', '')
                artist = request.form.get('artist', '')
                genre = request.form.get('genre', '')
                tags = request.form.get('tags', '').split(',') if request.form.get('tags', '') else []
                
                # 检查文件是否存在
                full_path = os.path.join(self.output_dir, filepath)
                if not os.path.exists(full_path):
                    return jsonify({
                        'success': False,
                        'message': f'文件 {filepath} 不存在'
                    })
                
                # 添加到音乐库
                track_id = self.music_db.add_track(
                    filepath=full_path,
                    title=title,
                    artist=artist,
                    genre=genre,
                    tags=tags
                )
                
                return jsonify({
                    'success': True,
                    'track_id': track_id,
                    'message': '成功添加到音乐库！'
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'添加到音乐库失败: {str(e)}'
                })
        
        @self.app.route('/import_files', methods=['POST'])
        def import_files():
            """导入文件到音乐库API"""
            try:
                # 确保上传文件目录存在
                os.makedirs(self.app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # 获取上传的MIDI文件
                if 'midi_files[]' not in request.files:
                    return jsonify({
                        'success': False,
                        'message': '没有上传MIDI文件'
                    })
                
                files = request.files.getlist('midi_files[]')
                if not files or files[0].filename == '':
                    return jsonify({
                        'success': False,
                        'message': '没有选择文件'
                    })
                
                # 获取参数
                genre = request.form.get('genre', '')
                tags = request.form.get('tags', '').split(',') if request.form.get('tags', '') else []
                
                # 保存上传的文件并添加到音乐库
                imported_count = 0
                for file in files:
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(self.app.config['UPLOAD_FOLDER'], filename)
                    file.save(upload_path)
                    
                    try:
                        self.music_db.add_track(
                            filepath=upload_path,
                            title=None,  # 使用文件名
                            artist=None,
                            genre=genre,
                            tags=tags
                        )
                        imported_count += 1
                    except Exception as e:
                        print(f"导入 {filename} 失败: {e}")
                
                return jsonify({
                    'success': True,
                    'count': imported_count,
                    'message': f'成功导入 {imported_count} 个文件到音乐库！'
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'导入文件失败: {str(e)}'
                })
        
        @self.app.route('/delete_track/<int:track_id>', methods=['POST'])
        def delete_track(track_id):
            """删除曲目API"""
            try:
                result = self.music_db.delete_track(track_id)
                if result:
                    return jsonify({
                        'success': True,
                        'message': '曲目删除成功！'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': '删除曲目失败'
                    })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'删除曲目失败: {str(e)}'
                })
        
        @self.app.route('/learn', methods=['GET'])
        def learn():
            """学习页面"""
            return render_template('learn.html')
        
        @self.app.route('/train_melody_model', methods=['POST'])
        def train_melody_model():
            """训练旋律模型API"""
            try:
                # 检查是否选择了音乐库中的曲目
                track_ids = request.form.getlist('track_ids[]')
                
                if not track_ids:
                    return jsonify({
                        'success': False,
                        'message': '请选择至少一个曲目进行训练'
                    })
                
                # 获取所选曲目的MIDI文件路径
                midi_files = []
                for track_id in track_ids:
                    track = self.music_db.get_track(int(track_id))
                    if track and os.path.exists(track['filepath']):
                        midi_files.append(track['filepath'])
                
                if not midi_files:
                    return jsonify({
                        'success': False,
                        'message': '所选曲目中没有有效的MIDI文件'
                    })
                
                # 获取训练参数
                sequence_length = int(request.form.get('sequence_length', 100))
                epochs = int(request.form.get('epochs', 50))
                batch_size = int(request.form.get('batch_size', 64))
                
                # 训练模型
                model_path = self.music_creator.train_melody_model(
                    midi_files=midi_files,
                    sequence_length=sequence_length,
                    epochs=epochs,
                    batch_size=batch_size
                )
                
                return jsonify({
                    'success': True,
                    'model_path': model_path,
                    'message': '旋律模型训练成功！'
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'训练旋律模型失败: {str(e)}'
                })
        
        @self.app.route('/learn_style', methods=['POST'])
        def learn_style_api():
            """学习风格API"""
            try:
                # 检查是否选择了音乐库中的曲目
                track_ids = request.form.getlist('track_ids[]')
                
                if not track_ids:
                    return jsonify({
                        'success': False,
                        'message': '请选择至少一个曲目进行训练'
                    })
                
                # 获取所选曲目的MIDI文件路径
                midi_files = []
                for track_id in track_ids:
                    track = self.music_db.get_track(int(track_id))
                    if track and os.path.exists(track['filepath']):
                        midi_files.append(track['filepath'])
                
                if not midi_files:
                    return jsonify({
                        'success': False,
                        'message': '所选曲目中没有有效的MIDI文件'
                    })
                
                # 获取训练参数
                style_name = request.form.get('style_name', '')
                epochs = int(request.form.get('epochs', 30))
                batch_size = int(request.form.get('batch_size', 32))
                
                if not style_name:
                    return jsonify({
                        'success': False,
                        'message': '请输入风格名称'
                    })
                
                # 学习风格
                model_path = self.music_creator.learn_style(
                    midi_files=midi_files,
                    style_name=style_name,
                    epochs=epochs,
                    batch_size=batch_size
                )
            
                return jsonify({
                    'success': True,
                        'model_path': model_path,
                        'message': f'风格"{style_name}"学习成功！'
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                        'message': f'学习风格失败: {str(e)}'
                    })
        
        @self.app.route('/list_compositions')
        def list_compositions():
            """获取所有音乐作品的列表"""
            print('list_compositions')
            try:
                tracks = self.music_db.search_tracks()
                # 转换为前端期望的格式
                compositions = []
                for track in tracks:
                    # 构建作品对象
                    composition = {
                        'id': track['id'],
                        'title': track['title'],
                        'description': track.get('genre', ''),
                        'effects': track.get('tags', []),
                        'accompaniment_file': f"/output/{os.path.basename(track['filepath'])}"
                    }
                    compositions.append(composition)
                    
                return jsonify(compositions)
            except Exception as e:
                print(f"Error in list_compositions route: {str(e)}")
                return jsonify([])
    
    def run(self):
        """运行Web应用"""
        self.app.run(host=self.host, port=self.port, debug=self.debug)
    
    def get_app(self):
        """获取Flask应用对象
        
        Returns:
            Flask: Flask应用对象
        """
        return self.app



def main():
    """主函数，启动Web应用程序"""
    # 使用 argparse 解析命令行参数
    parser = argparse.ArgumentParser(description="启动 MusicGenius 应用")
    parser.add_argument('--db_host', type=str, default='localhost', help='MySQL 服务器地址')
    parser.add_argument('--db_user', type=str, default='root', help='MySQL 用户名')
    parser.add_argument('--db_password', type=str, default='root123@', help='MySQL 密码')  # 必填参数
    parser.add_argument('--db_name', type=str, default='music_genius', help='MySQL 数据库名')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='应用主机地址')
    parser.add_argument('--port', type=int, default=5000, help='应用端口号')
    parser.add_argument('--debug', action='store_true', help='是否开启调试模式')
    
    args = parser.parse_args()  # 解析命令行参数

    # 创建应用实例
    app = MusicGeniusApp(
        db_host=args.db_host,
        db_user=args.db_user,
        db_password=args.db_password,  # 使用命令行参数
        db_name=args.db_name,
        host=args.host,
        port=args.port,
        debug=args.debug
    )
    
    # 运行应用
    app.run()

if __name__ == "__main__":
    main() 