import os
import json
import shutil
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import tempfile
from datetime import datetime
from ..core import MusicCreator, MusicDatabase
from ..utils import midi_utils

class MusicGeniusWebApp:
    """基于Flask的MusicGenius Web应用"""
    
    def __init__(self, model_dir='models', output_dir='output', db_path='data/music_database.db',
                 upload_folder='uploads', static_folder='static', template_folder='templates',
                 host='0.0.0.0', port=5000, debug=True):
        """初始化Web应用
        
        Args:
            model_dir (str): 模型目录
            output_dir (str): 输出目录
            db_path (str): 数据库文件路径
            upload_folder (str): 上传文件目录
            static_folder (str): 静态文件目录
            template_folder (str): 模板文件目录
            host (str): 主机地址
            port (int): 端口号
            debug (bool): 是否开启调试模式
        """
        self.model_dir = model_dir
        self.output_dir = output_dir
        self.upload_folder = upload_folder
        self.db_path = db_path
        
        # 确保目录存在
        os.makedirs(model_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 创建核心组件
        self.music_creator = MusicCreator(model_dir=model_dir, output_dir=output_dir)
        self.music_db = MusicDatabase(db_path=db_path)
        
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
    
    def _register_routes(self):
        """注册所有路由"""
        
        @self.app.route('/')
        def index():
            """主页"""
            # 获取统计信息
            stats = self.music_db.get_track_statistics()
            
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
            # 获取查询参数
            query = request.args.get('query', '')
            genre = request.args.get('genre', '')
            tag = request.args.get('tag', '')
            
            # 搜索曲目
            tracks = self.music_db.search_tracks(query=query, genre=genre, tag=tag)
            
            # 获取所有曲风和标签，用于筛选
            genres = self.music_db.get_all_genres()
            tags = self.music_db.get_all_tags()
            
            return render_template('library.html',
                                tracks=tracks,
                                genres=genres,
                                tags=tags,
                                query=query,
                                selected_genre=genre,
                                selected_tag=tag)
        
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
            
            return render_template('create.html',
                                available_styles=available_styles,
                                available_instruments=available_instruments)
        
        @self.app.route('/generate_melody', methods=['POST'])
        def generate_melody():
            """生成旋律API"""
            try:
                # 获取参数
                num_notes = int(request.form.get('num_notes', 200))
                temperature = float(request.form.get('temperature', 1.0))
                tempo_bpm = int(request.form.get('tempo_bpm', 120))
                instrument_name = request.form.get('instrument', 'Piano')
                
                # 生成MIDI文件
                output_path = self.music_creator.generate_midi_file(
                    num_notes=num_notes,
                    temperature=temperature,
                    tempo_bpm=tempo_bpm,
                    instrument_name=instrument_name
                )
                
                # 获取相对路径
                relative_path = os.path.relpath(output_path, self.output_dir)
                
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
                    effects_params['reverb'] = {
                        'room_size': float(request.form.get('reverb_room_size', 0.8)),
                        'damping': float(request.form.get('reverb_damping', 0.5)),
                        'wet_level': float(request.form.get('reverb_wet_level', 0.3)),
                        'dry_level': float(request.form.get('reverb_dry_level', 0.7))
                    }
                
                # 延迟
                if 'delay' in request.form and request.form['delay'] == 'on':
                    effects_params['delay'] = {
                        'delay_time': float(request.form.get('delay_time', 0.5)),
                        'feedback': float(request.form.get('delay_feedback', 0.5)),
                        'wet_level': float(request.form.get('delay_wet_level', 0.5)),
                        'dry_level': float(request.form.get('delay_dry_level', 0.5))
                    }
                
                # 合唱
                if 'chorus' in request.form and request.form['chorus'] == 'on':
                    effects_params['chorus'] = {
                        'rate': float(request.form.get('chorus_rate', 0.5)),
                        'depth': float(request.form.get('chorus_depth', 0.002)),
                        'wet_level': float(request.form.get('chorus_wet_level', 0.5)),
                        'dry_level': float(request.form.get('chorus_dry_level', 0.5)),
                        'voices': int(request.form.get('chorus_voices', 3))
                    }
                
                # 失真
                if 'distortion' in request.form and request.form['distortion'] == 'on':
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
            return send_from_directory(self.output_dir, filename, as_attachment=True)
        
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
    
    def run(self):
        """运行Web应用"""
        self.app.run(host=self.host, port=self.port, debug=self.debug)
    
    def get_app(self):
        """获取Flask应用对象
        
        Returns:
            Flask: Flask应用对象
        """
        return self.app 