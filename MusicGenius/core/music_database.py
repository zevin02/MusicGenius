"""
MusicGenius - 音乐数据库管理模块

MySQL表结构：

1. tracks表 (曲目表)
CREATE TABLE tracks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255),
    artist VARCHAR(255),
    genre VARCHAR(100),
    filepath VARCHAR(512) UNIQUE,
    duration FLOAT,
    tempo FLOAT,
    `key` VARCHAR(10),
    mode VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    features JSON,
    INDEX idx_title (title),
    INDEX idx_artist (artist),
    INDEX idx_genre (genre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

2. tags表 (标签表)
CREATE TABLE tags (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

3. track_tags表 (曲目-标签关联表)
CREATE TABLE track_tags (
    track_id BIGINT,
    tag_id BIGINT,
    PRIMARY KEY (track_id, tag_id),
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    INDEX idx_track_id (track_id),
    INDEX idx_tag_id (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

4. instruments表 (乐器表)
CREATE TABLE instruments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    track_id BIGINT,
    name VARCHAR(100),
    program INT,
    is_drum BOOLEAN,
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
    INDEX idx_track_id (track_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

import os
import json
import mysql.connector
from mysql.connector import Error
import pandas as pd
from datetime import datetime
from ..utils import midi_utils

class MusicDatabase:
    """音乐数据库管理类，用于管理音乐曲目库"""
    
    def __init__(self, host='localhost', user='root', password='', database='music_genius'):
        """初始化音乐数据库
        
        Args:
            host (str): MySQL服务器地址
            user (str): 数据库用户名
            password (str): 数据库密码
            database (str): 数据库名称
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """连接到数据库"""
        self.conn = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )
        self.cursor = self.conn.cursor()
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        """创建数据库表"""
        # 曲目表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracks (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            title VARCHAR(255),
            artist VARCHAR(255),
            genre VARCHAR(100),
            filepath VARCHAR(512) UNIQUE,
            duration FLOAT,
            tempo FLOAT,
            `key` VARCHAR(10),
            mode VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            features JSON,
            INDEX idx_title (title),
            INDEX idx_artist (artist),
            INDEX idx_genre (genre)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        ''')
        
        # 标签表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) UNIQUE,
            INDEX idx_name (name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        ''')
        
        # 曲目-标签关联表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS track_tags (
            track_id BIGINT,
            tag_id BIGINT,
            PRIMARY KEY (track_id, tag_id),
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
            INDEX idx_track_id (track_id),
            INDEX idx_tag_id (tag_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        ''')
        
        # 乐器表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS instruments (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            track_id BIGINT,
            name VARCHAR(100),
            program INT,
            is_drum BOOLEAN,
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
            INDEX idx_track_id (track_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        ''')
        
        self.conn.commit()
    
    def add_track(self, filepath, title=None, artist=None, genre=None, tags=None, extract_features=True):
        """添加音乐曲目
        
        Args:
            filepath (str): MIDI文件路径
            title (str, optional): 曲目标题，如果为None则使用文件名
            artist (str, optional): 艺术家
            genre (str, optional): 曲风
            tags (list, optional): 标签列表
            extract_features (bool): 是否提取特征
        
        Returns:
            int: 曲目ID
        """
        # 检查文件是否存在
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件 {filepath} 不存在")
        
        # 如果标题为空，使用文件名
        if title is None:
            title = os.path.splitext(os.path.basename(filepath))[0]
        
        # 提取MIDI文件信息
        try:
            tempo = midi_utils.get_tempo(filepath)
            key, mode = midi_utils.extract_key(filepath)
            duration = midi_utils.extract_midi_features(filepath)['duration']
            
            # 提取特征
            features = {}
            if extract_features:
                features = midi_utils.extract_midi_features(filepath)
            
            # 将特征转换为JSON字符串
            features_json = json.dumps(features)
            
            # 添加曲目
            self.cursor.execute('''
            INSERT INTO tracks (title, artist, genre, filepath, duration, tempo, key, mode, created_at, features)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, artist, genre, filepath, duration, tempo, key, mode, datetime.now(), features_json))
            
            track_id = self.cursor.lastrowid
            
            # 添加标签
            if tags:
                for tag in tags:
                    tag_id = self.add_tag(tag)
                    self.cursor.execute('''
                    INSERT OR IGNORE INTO track_tags (track_id, tag_id)
                    VALUES (?, ?)
                    ''', (track_id, tag_id))
            
            # 添加乐器信息
            instruments = midi_utils.get_instruments(filepath)
            for inst in instruments:
                self.cursor.execute('''
                INSERT INTO instruments (track_id, name, program, is_drum)
                VALUES (?, ?, ?, ?)
                ''', (track_id, inst['name'], inst['program'], inst['is_drum']))
            
            self.conn.commit()
            return track_id
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"添加曲目 {filepath} 时出错: {e}")
    
    def add_tag(self, tag_name):
        """添加标签
        
        Args:
            tag_name (str): 标签名称
        
        Returns:
            int: 标签ID
        """
        self.cursor.execute('''
        INSERT OR IGNORE INTO tags (name)
        VALUES (?)
        ''', (tag_name,))
        
        self.cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
        tag_id = self.cursor.fetchone()[0]
        return tag_id
    
    def get_track(self, track_id):
        """获取曲目信息
        
        Args:
            track_id (int): 曲目ID
        
        Returns:
            dict: 曲目信息
        """
        self.cursor.execute('''
        SELECT id, title, artist, genre, filepath, duration, tempo, key, mode, created_at, features
        FROM tracks
        WHERE id = ?
        ''', (track_id,))
        
        track = self.cursor.fetchone()
        if not track:
            return None
        
        track_dict = {
            'id': track[0],
            'title': track[1],
            'artist': track[2],
            'genre': track[3],
            'filepath': track[4],
            'duration': track[5],
            'tempo': track[6],
            'key': track[7],
            'mode': track[8],
            'created_at': track[9],
            'features': json.loads(track[10]) if track[10] else {}
        }
        
        # 获取标签
        self.cursor.execute('''
        SELECT t.name
        FROM tags t
        JOIN track_tags tt ON t.id = tt.tag_id
        WHERE tt.track_id = ?
        ''', (track_id,))
        
        tags = [row[0] for row in self.cursor.fetchall()]
        track_dict['tags'] = tags
        
        # 获取乐器
        self.cursor.execute('''
        SELECT name, program, is_drum
        FROM instruments
        WHERE track_id = ?
        ''', (track_id,))
        
        instruments = [{'name': row[0], 'program': row[1], 'is_drum': bool(row[2])} for row in self.cursor.fetchall()]
        track_dict['instruments'] = instruments
        
        return track_dict
    
    def update_track(self, track_id, title=None, artist=None, genre=None):
        """更新曲目信息
        
        Args:
            track_id (int): 曲目ID
            title (str, optional): 曲目标题
            artist (str, optional): 艺术家
            genre (str, optional): 曲风
        
        Returns:
            bool: 是否成功更新
        """
        # 构建更新字段
        update_fields = []
        params = []
        
        if title is not None:
            update_fields.append("title = %s")
            params.append(title)
        
        if artist is not None:
            update_fields.append("artist = %s")
            params.append(artist)
        
        if genre is not None:
            update_fields.append("genre = %s")
            params.append(genre)
        
        if not update_fields:
            return False
        
        # 执行更新
        query = f"UPDATE tracks SET {', '.join(update_fields)} WHERE id = %s"
        params.append(track_id)
        
        self.cursor.execute(query, params)
        self.conn.commit()
        
        return self.cursor.rowcount > 0
    
    def delete_track(self, track_id):
        """删除曲目
        
        Args:
            track_id (int): 曲目ID
        
        Returns:
            bool: 是否成功删除
        """
        try:
            # 删除相关的标签关联
            self.cursor.execute("DELETE FROM track_tags WHERE track_id = %s", (track_id,))
            
            # 删除相关的乐器信息
            self.cursor.execute("DELETE FROM instruments WHERE track_id = %s", (track_id,))
            
            # 删除曲目
            self.cursor.execute("DELETE FROM tracks WHERE id = %s", (track_id,))
            
            self.conn.commit()
            return self.cursor.rowcount > 0
        except:
            self.conn.rollback()
            return False
    
    def search_tracks(self, query=None, genre=None, tag=None, key=None, tempo_range=None, limit=100):
        """搜索曲目
        
        Args:
            query (str, optional): 搜索关键词（标题或艺术家）
            genre (str, optional): 曲风
            tag (str, optional): 标签
            key (str, optional): 调式
            tempo_range (tuple, optional): 速度范围，如(90, 120)
            limit (int): 返回结果数量限制
        
        Returns:
            list: 曲目列表
        """
        sql = '''
        SELECT DISTINCT t.id, t.title, t.artist, t.genre, t.filepath, t.duration, t.tempo, t.key, t.mode
        FROM tracks t
        '''
        
        params = []
        where_clauses = []
        
        # 如果有标签条件，添加JOIN
        if tag:
            sql += '''
            JOIN track_tags tt ON t.id = tt.track_id
            JOIN tags tg ON tt.tag_id = tg.id
            '''
            where_clauses.append("tg.name = %s")
            params.append(tag)
        
        # 添加其他条件
        if query:
            where_clauses.append("(t.title LIKE %s OR t.artist LIKE %s)")
            params.extend([f"%{query}%", f"%{query}%"])
        
        if genre:
            where_clauses.append("t.genre = %s")
            params.append(genre)
        
        if key:
            where_clauses.append("t.key = %s")
            params.append(key)
        
        if tempo_range:
            where_clauses.append("t.tempo BETWEEN %s AND %s")
            params.extend(tempo_range)
        
        # 组合WHERE子句
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        
        # 添加限制
        sql += f" LIMIT {limit}"
        
        # 执行查询
        self.cursor.execute(sql, params)
        results = self.cursor.fetchall()
        
        # 格式化结果
        tracks = []
        for row in results:
            track = {
                'id': row[0],
                'title': row[1],
                'artist': row[2],
                'genre': row[3],
                'filepath': row[4],
                'duration': row[5],
                'tempo': row[6],
                'key': row[7],
                'mode': row[8]
            }
            tracks.append(track)
        
        return tracks
    
    def get_all_genres(self):
        """获取所有曲风
        
        Returns:
            list: 曲风列表
        """
        self.cursor.execute("SELECT DISTINCT genre FROM tracks WHERE genre IS NOT NULL")
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_all_tags(self):
        """获取所有标签
        
        Returns:
            list: 标签列表
        """
        self.cursor.execute("SELECT name FROM tags")
        return [row[0] for row in self.cursor.fetchall()]
    
    def add_tracks_from_directory(self, directory, recursive=True, genre=None, tags=None):
        """从目录批量添加MIDI文件
        
        Args:
            directory (str): 目录路径
            recursive (bool): 是否递归搜索子目录
            genre (str, optional): 曲风
            tags (list, optional): 标签列表
        
        Returns:
            int: 添加的曲目数量
        """
        midi_files = midi_utils.list_midi_files(directory, recursive)
        count = 0
        
        for filepath in midi_files:
            try:
                self.add_track(
                    filepath=filepath,
                    title=None,  # 使用文件名
                    artist=None,
                    genre=genre,
                    tags=tags,
                    extract_features=True
                )
                count += 1
            except Exception as e:
                print(f"添加曲目 {filepath} 时出错: {e}")
        
        return count
    
    def get_track_statistics(self):
        """获取数据库统计信息
        
        Returns:
            dict: 统计信息
        """
        stats = {}
        
        # 总曲目数
        self.cursor.execute("SELECT COUNT(*) FROM tracks")
        stats['total_tracks'] = self.cursor.fetchone()[0]
        
        # 曲风分布
        self.cursor.execute('''
        SELECT genre, COUNT(*) as count
        FROM tracks
        WHERE genre IS NOT NULL
        GROUP BY genre
        ORDER BY count DESC
        ''')
        stats['genre_distribution'] = {row[0]: row[1] for row in self.cursor.fetchall()}
        
        # 调式分布
        self.cursor.execute('''
        SELECT key, mode, COUNT(*) as count
        FROM tracks
        WHERE key IS NOT NULL AND mode IS NOT NULL
        GROUP BY key, mode
        ORDER BY count DESC
        ''')
        stats['key_distribution'] = {f"{row[0]} {row[1]}": row[2] for row in self.cursor.fetchall()}
        
        # 速度分布
        self.cursor.execute('''
        SELECT 
            CASE
                WHEN tempo < 60 THEN 'Very Slow (<60)'
                WHEN tempo BETWEEN 60 AND 90 THEN 'Slow (60-90)'
                WHEN tempo BETWEEN 90 AND 120 THEN 'Moderate (90-120)'
                WHEN tempo BETWEEN 120 AND 160 THEN 'Fast (120-160)'
                ELSE 'Very Fast (>160)'
            END as tempo_range,
            COUNT(*) as count
        FROM tracks
        WHERE tempo IS NOT NULL
        GROUP BY tempo_range
        ORDER BY 
            CASE tempo_range
                WHEN 'Very Slow (<60)' THEN 1
                WHEN 'Slow (60-90)' THEN 2
                WHEN 'Moderate (90-120)' THEN 3
                WHEN 'Fast (120-160)' THEN 4
                WHEN 'Very Fast (>160)' THEN 5
            END
        ''')
        stats['tempo_distribution'] = {row[0]: row[1] for row in self.cursor.fetchall()}
        
        return stats
    
    def export_to_csv(self, output_path):
        """导出数据库到CSV文件
        
        Args:
            output_path (str): 输出CSV文件路径
        """
        # 查询所有曲目
        self.cursor.execute('''
        SELECT id, title, artist, genre, filepath, duration, tempo, key, mode, created_at
        FROM tracks
        ''')
        
        tracks = self.cursor.fetchall()
        columns = ['id', 'title', 'artist', 'genre', 'filepath', 'duration', 'tempo', 'key', 'mode', 'created_at']
        
        df = pd.DataFrame(tracks, columns=columns)
        df.to_csv(output_path, index=False)
    
    def import_from_csv(self, csv_path, extract_features=True):
        """从CSV文件导入数据库
        
        Args:
            csv_path (str): CSV文件路径
            extract_features (bool): 是否提取特征
        
        Returns:
            int: 导入的曲目数量
        """
        df = pd.read_csv(csv_path)
        count = 0
        
        for _, row in df.iterrows():
            filepath = row['filepath']
            
            # 检查文件是否存在
            if not os.path.exists(filepath):
                print(f"文件 {filepath} 不存在，跳过")
                continue
            
            try:
                self.add_track(
                    filepath=filepath,
                    title=row.get('title'),
                    artist=row.get('artist'),
                    genre=row.get('genre'),
                    tags=None,  # CSV中没有标签
                    extract_features=extract_features
                )
                count += 1
            except Exception as e:
                print(f"导入曲目 {filepath} 时出错: {e}")
        
        return count 

    def get_total_tracks(self):
        """获取总曲目数
        
        Returns:
            int: 总曲目数
        """
        self.cursor.execute("SELECT COUNT(*) FROM tracks")
        total_tracks = self.cursor.fetchone()[0]
        return total_tracks

    def get_all_genres(self):
        """获取所有曲风
        
        Returns:
            list: 曲风列表
        """
        self.cursor.execute("SELECT DISTINCT genre FROM tracks WHERE genre IS NOT NULL")
        genres = [row[0] for row in self.cursor.fetchall()]
        return genres