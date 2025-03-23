#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MusicGenius - 智能音乐创作APP
主入口文件
"""

import os
import sys
import json
from werkzeug.utils import secure_filename
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

# 导入相关模块
from flask import Flask, render_template, request, jsonify, send_from_directory
from music_generator import MusicGenerator

def create_app():
    """创建一个简化版的Flask应用程序，用于演示"""
    # 创建Flask应用
    app = Flask(__name__, 
                template_folder='MusicGenius/ui/templates',
                static_folder='MusicGenius/ui/static')
    
    # 创建音乐生成器实例
    generator = MusicGenerator()
    
    # 确保必要的目录存在
    os.makedirs('models', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    
    # 首页路由
    @app.route('/')
    def index():
        # 简单的统计信息
        stats = {
            'total_tracks': 0,
            'genres': {'流行': 5, '古典': 3, '爵士': 2},
            'instruments': {'钢琴': 10, '吉他': 5, '小提琴': 3}
        }
        
        # 可用风格列表
        available_styles = ['古典', '流行', '爵士', '电子', '民谣', '蓝调']
        
        # 可用乐器列表  
        available_instruments = ['钢琴', '吉他', '小提琴', '大提琴', '长笛', '萨克斯', '电子合成器']
        
        return render_template('index.html', 
                          stats=stats, 
                          available_styles=available_styles,
                          available_instruments=available_instruments)
    
    # 音乐库路由
    @app.route('/library')
    def library():
        return render_template('library.html')
    
    # 创作页面路由
    @app.route('/create')
    def create():
        # 可用风格列表
        available_styles = ['古典', '流行', '爵士', '电子', '民谣', '蓝调']
        
        # 可用乐器列表  
        available_instruments = ['钢琴', '吉他', '小提琴', '大提琴', '长笛', '萨克斯', '电子合成器']
        
        return render_template('create.html',
                             available_styles=available_styles,
                             available_instruments=available_instruments)
    
    # 生成旋律API
    @app.route('/generate_melody', methods=['POST'])
    def generate_melody():
        try:
            style = request.form.get('style')
            instrument = request.form.get('instrument')
            length = int(request.form.get('length', 8))
            seed = request.form.get('seed', '')
            
            # 使用音乐生成器生成旋律
            output_file = generator.generate_melody(style, length, seed)
            
            return jsonify({
                'success': True,
                'message': '旋律生成成功',
                'audio_url': output_file
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'生成旋律失败: {str(e)}'
            }), 500
    
    # 风格迁移API
    @app.route('/transfer_style', methods=['POST'])
    def transfer_style():
        try:
            if 'input_file' not in request.files:
                return jsonify({
                    'success': False,
                    'message': '未上传文件'
                }), 400
                
            file = request.files['input_file']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'message': '未选择文件'
                }), 400
                
            target_style = request.form.get('target_style')
            strength = float(request.form.get('strength', 80)) / 100
            
            # 保存上传的文件
            filename = secure_filename(file.filename)
            input_path = os.path.join('uploads', filename)
            file.save(input_path)
            
            # 使用音乐生成器进行风格迁移
            output_file = generator.transfer_style(input_path, target_style, strength)
            
            return jsonify({
                'success': True,
                'message': '风格迁移成功',
                'audio_url': output_file
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'风格迁移失败: {str(e)}'
            }), 500
    
    # 生成伴奏API
    @app.route('/generate_accompaniment', methods=['POST'])
    def generate_accompaniment():
        try:
            if 'input_file' not in request.files:
                return jsonify({
                    'success': False,
                    'message': '未上传文件'
                }), 400
                
            file = request.files['input_file']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'message': '未选择文件'
                }), 400
                
            style = request.form.get('style')
            
            # 保存上传的文件
            filename = secure_filename(file.filename)
            input_path = os.path.join('uploads', filename)
            file.save(input_path)
            
            # 使用音乐生成器生成伴奏
            output_file = generator.generate_accompaniment(input_path, style)
            
            return jsonify({
                'success': True,
                'message': '伴奏生成成功',
                'audio_url': output_file
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'生成伴奏失败: {str(e)}'
            }), 500
    
    # 输出文件下载路由
    @app.route('/output/<path:filename>')
    def download_file(filename):
        return send_from_directory('output', filename)
    
    return app

def main():
    """主函数，启动Web应用程序"""
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main() 