"""
URL 管理模块
支持从 CSV/Excel 文件导入网址列表
"""
import pandas as pd
import os
from urllib.parse import urlparse
from typing import List, Dict, Optional
import json


class URLManager:
    """URL 管理器：负责加载、验证和管理待爬取的URL列表"""
    
    def __init__(self, column_mapping: Optional[Dict] = None):
        self.urls = []
        self.column_mapping = column_mapping or {
            "url": ["url", "网址", "链接", "link", "href", "地址"],
            "name": ["name", "名称", "标题", "title", "站点"],
            "category": ["category", "分类", "类别", "type", "类型"],
            "priority": ["priority", "优先级", "level"],
        }
    
    def load_from_file(self, file_path: str) -> List[Dict]:
        """
        从文件加载URL列表
        支持格式: .csv, .xlsx, .xls
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".csv":
            df = pd.read_csv(file_path, encoding="utf-8")
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}，请使用 CSV 或 Excel 文件")
        
        # 标准化列名
        df = self._normalize_columns(df)
        
        # 转换为字典列表
        urls = []
        for _, row in df.iterrows():
            url_item = self._parse_row(row)
            if url_item and self._validate_url(url_item.get("url")):
                urls.append(url_item)
        
        self.urls = urls
        print(f"成功加载 {len(urls)} 个有效URL")
        return urls
    
    def load_from_json(self, file_path: str) -> List[Dict]:
        """从JSON文件加载URL列表"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        urls = []
        for item in data:
            if isinstance(item, str):
                if self._validate_url(item):
                    urls.append({"url": item})
            elif isinstance(item, dict):
                if self._validate_url(item.get("url")):
                    urls.append(item)
        
        self.urls = urls
        print(f"成功加载 {len(urls)} 个有效URL")
        return urls
    
    def add_url(self, url: str, **metadata) -> bool:
        """添加单个URL"""
        if not self._validate_url(url):
            return False
        
        url_item = {"url": url, **metadata}
        self.urls.append(url_item)
        return True
    
    def add_urls(self, urls: List[str]) -> int:
        """批量添加URL"""
        count = 0
        for url in urls:
            if self.add_url(url):
                count += 1
        return count
    
    def get_urls(self, category: Optional[str] = None, 
                 priority: Optional[int] = None) -> List[Dict]:
        """获取URL列表，支持筛选"""
        result = self.urls
        
        if category:
            result = [u for u in result if u.get("category") == category]
        
        if priority is not None:
            result = [u for u in result if u.get("priority") == priority]
        
        return result
    
    def get_url_list(self) -> List[str]:
        """获取纯URL字符串列表"""
        return [u.get("url") for u in self.urls if u.get("url")]
    
    def save_to_json(self, file_path: str):
        """保存URL列表到JSON文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.urls, f, ensure_ascii=False, indent=2)
        print(f"URL列表已保存到: {file_path}")
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        # 创建列名映射
        col_map = {}
        for standard_name, variants in self.column_mapping.items():
            for col in df.columns:
                if col.lower() in [v.lower() for v in variants]:
                    col_map[col] = standard_name
                    break
        
        # 重命名列
        df = df.rename(columns=col_map)
        return df
    
    def _parse_row(self, row: pd.Series) -> Optional[Dict]:
        """解析单行数据"""
        url = row.get("url")
        if pd.isna(url):
            return None
        
        item = {"url": str(url).strip()}
        
        # 添加其他字段
        for field in ["name", "category", "priority"]:
            value = row.get(field)
            if not pd.isna(value):
                item[field] = str(value).strip()
        
        return item
    
    def _validate_url(self, url: str) -> bool:
        """验证URL格式"""
        if not url or not isinstance(url, str):
            return False
        
        url = url.strip()
        
        # 基本格式检查
        if not url.startswith(("http://", "https://")):
            return False
        
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def get_stats(self) -> Dict:
        """获取URL统计信息"""
        stats = {
            "total": len(self.urls),
            "by_category": {},
            "by_priority": {}
        }
        
        for url_item in self.urls:
            cat = url_item.get("category", "未分类")
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
            
            pri = url_item.get("priority", "默认")
            stats["by_priority"][pri] = stats["by_priority"].get(pri, 0) + 1
        
        return stats


# 示例URL表格模板生成器
def create_url_template(output_path: str = "url_template.csv"):
    """创建URL导入模板文件"""
    data = {
        "url": [
            "https://example.com/news",
            "https://example.com/blog"
        ],
        "name": ["示例新闻站", "示例博客"],
        "category": ["新闻", "博客"],
        "priority": [1, 2]
    }
    
    df = pd.DataFrame(data)
    
    if output_path.endswith(".csv"):
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
    else:
        df.to_excel(output_path, index=False)
    
    print(f"模板文件已创建: {output_path}")
    return output_path
