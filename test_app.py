#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单的Flask测试应用
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "MusicGenius测试页面 - 成功运行!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True) 