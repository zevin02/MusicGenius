# MusicGenius - 智能音乐创作平台

MusicGenius是一个基于Python和Flask的智能音乐创作平台，它能够帮助用户生成旋律、进行风格迁移、添加伴奏等音乐创作任务。

## 功能特点

- 智能旋律生成：支持多种音乐风格（古典、流行、爵士等）
- 风格迁移：将现有音乐转换为不同的音乐风格
- 伴奏生成：为旋律自动生成配套伴奏
- 音乐库管理：保存和管理您的音乐作品

## 系统要求

- Python 3.8+
- Flask
- FluidSynth（用于MIDI到WAV的转换）
- SoundFont文件（用于音频合成）

## 安装步骤

1. 克隆项目：
```bash
git clone https://github.com/yourusername/MusicGenius.git
cd MusicGenius
```

2. 安装Python依赖：
```bash
pip install -r requirements.txt
```

3. 安装系统依赖：
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install fluidsynth
sudo apt-get install fluid-soundfont-gm

# CentOS/RHEL
sudo yum install fluidsynth
sudo yum install fluid-soundfont-gm

# macOS
brew install fluidsynth
```

4. 创建必要的目录：
```bash
mkdir -p output models data uploads
```

## 使用说明

1. 启动应用：
```bash
python3 main.py
```

2. 在浏览器中访问：
```
http://localhost:5000
```

3. 使用功能：
   - 点击"创作"进入创作页面
   - 选择音乐风格和参数
   - 点击"生成旋律"按钮
   - 在音频播放器中试听生成的音乐
   - 可以下载或保存到音乐库

## 目录结构

```
MusicGenius/
├── main.py              # 主程序入口
├── music_generator.py   # 音乐生成核心模块
├── requirements.txt     # Python依赖列表
├── ui/                  # 用户界面模块
│   ├── templates/      # HTML模板
│   ├── static/        # 静态资源
│   └── web_app.py     # Web应用逻辑
├── models/             # 模型存储目录
├── output/            # 生成的音乐文件
├── data/              # 数据存储
└── uploads/           # 上传文件临时存储
```

## 常见问题

1. 如果没有声音输出，请检查：
   - 是否已安装FluidSynth和SoundFont
   - 系统音量设置是否正确
   - 浏览器是否支持音频播放

2. 如果生成的音乐文件过大：
   - 可以调整生成参数中的长度
   - 检查音频质量设置

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request来帮助改进项目。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件到：[您的邮箱]

## 致谢

感谢以下开源项目的支持：
- Flask
- FluidSynth
- Python-MIDI