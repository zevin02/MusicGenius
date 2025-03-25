"""
数据库模块
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    """数据库管理类"""
    
    def __init__(self, db_file: str = 'music_genius.db'):
        """初始化数据库
        
        Args:
            db_file: 数据库文件路径
        """
        self.db_file = db_file
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 创建作品表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compositions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                accompaniment_file TEXT NOT NULL,
                melody_file TEXT NOT NULL,
                effects TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_composition(self, title: str, description: str,
                       accompaniment_file: str, melody_file: str,
                       effects: str, created_at: datetime) -> int:
        """添加新作品
        
        Args:
            title: 作品标题
            description: 作品描述
            accompaniment_file: 伴奏文件路径
            melody_file: 旋律文件路径
            effects: 效果JSON字符串
            created_at: 创建时间
            
        Returns:
            int: 作品ID
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO compositions (
                title, description, accompaniment_file, melody_file,
                effects, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, accompaniment_file, melody_file,
              effects, created_at, created_at))
        
        composition_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return composition_id
    
    def get_composition(self, composition_id: int) -> Optional[Dict]:
        """获取作品信息
        
        Args:
            composition_id: 作品ID
            
        Returns:
            Optional[Dict]: 作品信息，如果不存在则返回None
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM compositions WHERE id = ?
        ''', (composition_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
            
        return {
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'accompaniment_file': row[3],
            'melody_file': row[4],
            'effects': json.loads(row[5]),
            'created_at': row[6],
            'updated_at': row[7]
        }
    
    def list_compositions(self) -> List[Dict]:
        """获取所有作品列表
        
        Returns:
            List[Dict]: 作品列表
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM compositions ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'accompaniment_file': row[3],
            'melody_file': row[4],
            'effects': json.loads(row[5]),
            'created_at': row[6],
            'updated_at': row[7]
        } for row in rows]
    
    def delete_composition(self, composition_id: int) -> bool:
        """删除作品
        
        Args:
            composition_id: 作品ID
            
        Returns:
            bool: 是否删除成功
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM compositions WHERE id = ?
        ''', (composition_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success 