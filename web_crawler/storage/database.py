"""
数据存储模块
支持 JSON、CSV、SQLite 多种存储格式
"""
import json
import csv
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd


class BaseStorage:
    """存储基类"""
    
    def save(self, data: List[Dict], **kwargs) -> str:
        raise NotImplementedError
    
    def load(self, **kwargs) -> List[Dict]:
        raise NotImplementedError


class JSONStorage(BaseStorage):
    """JSON 文件存储"""
    
    def __init__(self, file_path: Optional[str] = None):
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"data_{timestamp}.json"
        self.file_path = file_path
    
    def save(self, data: List[Dict], append: bool = True) -> str:
        """
        保存数据到JSON文件
        :param append: 是否追加模式
        """
        existing_data = []
        
        if append and os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
            except:
                existing_data = []
        
        # 添加爬取时间戳
        for item in data:
            if 'crawled_at' not in item:
                item['crawled_at'] = datetime.now().isoformat()
        
        all_data = existing_data + data
        
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(self.file_path)) or '.', exist_ok=True)
        
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        return self.file_path
    
    def load(self) -> List[Dict]:
        """加载JSON数据"""
        if not os.path.exists(self.file_path):
            return []
        
        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]


class CSVStorage(BaseStorage):
    """CSV 文件存储"""
    
    def __init__(self, file_path: Optional[str] = None):
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"data_{timestamp}.csv"
        self.file_path = file_path
    
    def save(self, data: List[Dict], append: bool = True) -> str:
        """保存数据到CSV文件"""
        if not data:
            return self.file_path
        
        # 添加爬取时间戳
        for item in data:
            if 'crawled_at' not in item:
                item['crawled_at'] = datetime.now().isoformat()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(self.file_path)) or '.', exist_ok=True)
        
        # 扁平化嵌套字典
        flat_data = [self._flatten(item) for item in data]
        
        # 获取所有字段
        fieldnames = set()
        for item in flat_data:
            fieldnames.update(item.keys())
        fieldnames = sorted(fieldnames)
        
        mode = 'a' if append and os.path.exists(self.file_path) else 'w'
        header = not (append and os.path.exists(self.file_path))
        
        with open(self.file_path, mode, newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if header:
                writer.writeheader()
            writer.writerows(flat_data)
        
        return self.file_path
    
    def load(self) -> List[Dict]:
        """加载CSV数据"""
        if not os.path.exists(self.file_path):
            return []
        
        with open(self.file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def _flatten(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """扁平化嵌套字典"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


class SQLiteStorage(BaseStorage):
    """SQLite 数据库存储"""
    
    def __init__(self, db_path: Optional[str] = None, table_name: str = "crawled_data"):
        if db_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            db_path = f"data_{timestamp}.db"
        self.db_path = db_path
        self.table_name = table_name
    
    def save(self, data: List[Dict], append: bool = True) -> str:
        """保存数据到SQLite数据库"""
        if not data:
            return self.db_path
        
        # 添加爬取时间戳
        for item in data:
            if 'crawled_at' not in item:
                item['crawled_at'] = datetime.now().isoformat()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)) or '.', exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有字段
        all_fields = set()
        for item in data:
            all_fields.update(self._flatten(item).keys())
        
        # 创建表
        fields_def = ', '.join([f'"{f}" TEXT' for f in all_fields])
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {fields_def}
            )
        ''')
        
        # 插入数据
        for item in data:
            flat_item = self._flatten(item)
            columns = ', '.join([f'"{k}"' for k in flat_item.keys()])
            placeholders = ', '.join(['?' for _ in flat_item])
            values = [str(v) if v is not None else '' for v in flat_item.values()]
            
            cursor.execute(
                f'INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})',
                values
            )
        
        conn.commit()
        conn.close()
        
        return self.db_path
    
    def load(self, limit: Optional[int] = None) -> List[Dict]:
        """加载数据库数据"""
        if not os.path.exists(self.db_path):
            return []
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = f'SELECT * FROM {self.table_name}'
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def query(self, sql: str, params: tuple = ()) -> List[Dict]:
        """执行自定义SQL查询"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def _flatten(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """扁平化嵌套字典"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten(v, new_key, sep).items())
            else:
                items.append((new_key, str(v) if v is not None else ''))
        return dict(items)


class DataStorage:
    """统一数据存储接口"""
    
    def __init__(self, storage_type: str = "json", file_path: Optional[str] = None):
        """
        :param storage_type: 存储类型: json, csv, sqlite
        :param file_path: 文件路径
        """
        self.storage_type = storage_type.lower()
        
        if self.storage_type == "json":
            self.storage = JSONStorage(file_path)
        elif self.storage_type == "csv":
            self.storage = CSVStorage(file_path)
        elif self.storage_type == "sqlite":
            self.storage = SQLiteStorage(file_path)
        else:
            raise ValueError(f"不支持的存储类型: {storage_type}")
    
    def save(self, data: List[Dict], append: bool = True) -> str:
        """保存数据"""
        return self.storage.save(data, append=append)
    
    def load(self, **kwargs) -> List[Dict]:
        """加载数据"""
        return self.storage.load(**kwargs)
    
    def export_to(self, target_type: str, target_path: str):
        """导出到其他格式"""
        data = self.load()
        
        if target_type == "json":
            storage = JSONStorage(target_path)
        elif target_type == "csv":
            storage = CSVStorage(target_path)
        elif target_type == "sqlite":
            storage = SQLiteStorage(target_path)
        else:
            raise ValueError(f"不支持的导出类型: {target_type}")
        
        return storage.save(data, append=False)


# 存储管理器
class StorageManager:
    """存储管理器，支持多种存储后端"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def save(self, data: List[Dict], 
             name: Optional[str] = None,
             formats: List[str] = None) -> Dict[str, str]:
        """
        保存数据到多种格式
        :param data: 要保存的数据
        :param name: 文件名（不含扩展名）
        :param formats: 存储格式列表
        :return: 各格式的文件路径
        """
        if formats is None:
            formats = ["json"]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = name or f"crawled_data_{timestamp}"
        
        saved_paths = {}
        
        for fmt in formats:
            file_path = os.path.join(self.data_dir, f"{name}.{fmt}")
            storage = DataStorage(fmt, file_path)
            saved_path = storage.save(data, append=False)
            saved_paths[fmt] = saved_path
        
        return saved_paths
