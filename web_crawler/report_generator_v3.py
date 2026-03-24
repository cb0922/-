#!/usr/bin/env python3
"""
兼容V3的报告生成器
适配 enhanced_crawler_v3 的结果格式
"""
import os
import sys
from datetime import datetime
from typing import List, Dict
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 尝试导入原ReportGenerator的方法
from report_generator import ReportGenerator as BaseReportGenerator


class ReportGeneratorV3(BaseReportGenerator):
    """兼容V3的报告生成器"""
    
    def __init__(self, data: List[Dict], title: str = "网页爬取报告", output_dir: str = None):
        # 转换V3数据格式为标准格式
        converted_data = self._convert_v3_data(data)
        super().__init__(converted_data, title, output_dir)
    
    def _convert_v3_data(self, data: List[Dict]) -> List[Dict]:
        """将V3数据格式转换为标准格式"""
        converted = []
        
        for item in data:
            if not item:
                continue
            
            # V3使用 "success" 而不是 "status"
            success = item.get("success", False)
            status = 200 if success else item.get("status", 0)
            
            # 转换文档数量为 links_count
            all_docs = item.get("all_documents", [])
            competition_docs = item.get("competition_documents", [])
            
            converted_item = {
                "url": item.get("url", ""),
                "title": item.get("title", "无标题"),
                "text": item.get("text", ""),
                "status": status,
                "success": success,
                "is_competition_related": item.get("is_competition_related", False),
                "links_count": len(all_docs),  # 用文档数代替链接数
                "images_count": len(competition_docs),  # 用比赛文档数代替图片数
                "all_documents": all_docs,
                "competition_documents": competition_docs,
                "crawled_at": item.get("crawled_at", ""),
                "content": item.get("content", ""),
            }
            
            converted.append(converted_item)
        
        return converted


# 保持与原ReportGenerator相同的接口
class ReportGenerator(ReportGeneratorV3):
    """别名，保持兼容性"""
    pass


if __name__ == "__main__":
    # 测试
    test_data = [
        {
            "url": "http://example.com",
            "title": "测试",
            "text": "测试内容",
            "success": True,
            "is_competition_related": True,
            "all_documents": [],
            "competition_documents": [],
            "crawled_at": "2024-01-01T00:00:00"
        }
    ]
    
    gen = ReportGenerator(test_data)
    path = gen.generate()
    print(f"报告已生成: {path}")
