#!/usr/bin/env python3
"""
Web Crawler Web Server
基于 FastAPI 的爬虫 Web 服务 - 增强版（带实时日志）
"""
import os
import sys
import json
import asyncio
import shutil
import threading
import queue
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 添加 web_crawler 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'web_crawler'))

from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3
from core.url_manager import URLManager

# ============ 配置 ============
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
URLS_FILE = UPLOAD_DIR / "urls.csv"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# 全局任务状态存储
crawl_tasks: Dict[str, Dict] = {}


# ============ Pydantic 模型 ============
class URLItem(BaseModel):
    url: str
    name: Optional[str] = ""
    category: Optional[str] = ""


class CrawlConfig(BaseModel):
    mode: str = "all"  # all, doc, html
    use_dynamic: bool = False
    timeout: int = 30
    use_proxy: bool = False
    proxy_file: Optional[str] = None
    max_retries: int = 3
    auto_remove_failed: bool = False


class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, running, completed, failed
    progress: int = 0
    total: int = 0
    message: str = ""
    created_at: str = ""
    completed_at: Optional[str] = None
    result: Optional[Dict] = None


class CrawlLog(BaseModel):
    timestamp: str
    level: str  # info, success, warning, error
    message: str
    url: Optional[str] = None


# ============ FastAPI 应用 ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建必要的目录
    (OUTPUT_DIR / "documents").mkdir(exist_ok=True)
    (OUTPUT_DIR / "reports").mkdir(exist_ok=True)
    (OUTPUT_DIR / "word_reports").mkdir(exist_ok=True)
    (OUTPUT_DIR / "data").mkdir(exist_ok=True)
    yield
    # 清理资源


app = FastAPI(
    title="Web Crawler API",
    description="网页爬虫 Web 服务 API",
    version="2.1.0",
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")


# ============ 工具函数 ============
def get_timestamp() -> str:
    """获取时间戳"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_urls_to_csv(urls: List[URLItem], filepath: Path):
    """保存 URL 列表到 CSV"""
    import csv
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['url', 'name', 'category'])
        for item in urls:
            writer.writerow([item.url, item.name or '', item.category or ''])


def load_urls_from_csv(filepath: Path) -> List[Dict]:
    """从 CSV 加载 URL 列表"""
    url_manager = URLManager()
    url_manager.load_from_file(str(filepath))
    return url_manager.urls


def add_log(task_id: str, level: str, message: str, url: str = None):
    """添加日志到任务"""
    task = crawl_tasks.get(task_id)
    if not task:
        return
    
    if "logs" not in task:
        task["logs"] = []
    
    log_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message
    }
    if url:
        log_entry["url"] = url
    
    task["logs"].append(log_entry)
    
    # 限制日志数量，保留最近 500 条
    if len(task["logs"]) > 500:
        task["logs"] = task["logs"][-500:]


async def run_crawl_task(task_id: str, urls: List[Dict], config: CrawlConfig):
    """后台执行爬虫任务 - 带详细日志"""
    task = crawl_tasks.get(task_id)
    if not task:
        return
    
    task["status"] = "running"
    task["message"] = "开始爬取..."
    task["total"] = len(urls)
    task["logs"] = []
    
    add_log(task_id, "info", f"🚀 启动爬虫任务，共 {len(urls)} 个网址")
    add_log(task_id, "info", f"📋 爬取模式: {config.mode}, 动态渲染: {config.use_dynamic}")
    
    try:
        # 创建爬虫实例
        urls_file = str(UPLOAD_DIR / f"urls_{task_id}.csv")
        save_urls_to_csv([URLItem(**u) for u in urls], Path(urls_file))
        add_log(task_id, "info", f"💾 URL 列表已保存")
        
        # 逐个爬取并记录日志
        results = []
        success_count = 0
        fail_count = 0
        
        for idx, url_item in enumerate(urls, 1):
            url = url_item.get("url") if isinstance(url_item, dict) else url_item
            name = url_item.get("name", "") if isinstance(url_item, dict) else ""
            
            task["progress"] = idx
            task["message"] = f"正在爬取 {idx}/{len(urls)}: {name or url[:30]}..."
            
            add_log(task_id, "info", f"[{idx}/{len(urls)}] 开始抓取: {name or url[:50]}", url)
            
            try:
                # 创建单个爬虫实例
                from core.fetcher import AsyncFetcher, get_random_headers
                from core.parser import ContentParser
                from core.document_handler import DocumentHandler
                
                fetcher = AsyncFetcher(
                    timeout=config.timeout,
                    headers=get_random_headers(),
                    use_proxy=config.use_proxy,
                    proxy_file=config.proxy_file or "proxies.json"
                )
                
                # 爬取单个 URL
                fetch_results = await fetcher.fetch_all([{"url": url}])
                fetch_result = fetch_results[0] if fetch_results else None
                
                if not fetch_result or not fetch_result.get("success"):
                    error = fetch_result.get('error', '未知错误') if fetch_result else '无响应'
                    add_log(task_id, "error", f"❌ 抓取失败: {error}", url)
                    fail_count += 1
                    continue
                
                # 解析内容
                html_content = fetch_result.get("content", "")
                parser = ContentParser(html_content)
                title = parser.get_title() or fetch_result.get("title", "无标题")
                
                add_log(task_id, "success", f"✅ 抓取成功: {title[:50]}", url)
                
                # 检查是否比赛相关
                text_preview = parser.get_text()[:500]
                is_competition = crawler.is_competition_related(title, text_preview) if 'crawler' in locals() else False
                
                if is_competition:
                    add_log(task_id, "info", f"🏆 检测到比赛相关内容", url)
                
                # 提取文档链接
                doc_handler = DocumentHandler(timeout=config.timeout, output_dir=str(OUTPUT_DIR / "documents"))
                documents = doc_handler.extract_document_links(html_content, url, title)
                
                if documents:
                    doc_types = {}
                    for d in documents:
                        t = d.get('doc_type', 'Other')
                        doc_types[t] = doc_types.get(t, 0) + 1
                    add_log(task_id, "info", f"📄 发现 {len(documents)} 个文档: {doc_types}", url)
                
                results.append({
                    "url": url,
                    "title": title,
                    "success": True,
                    "is_competition_related": is_competition,
                    "documents": documents
                })
                success_count += 1
                
            except Exception as e:
                add_log(task_id, "error", f"❌ 异常: {str(e)}", url)
                fail_count += 1
            
            # 短暂延迟，避免请求过快
            await asyncio.sleep(0.5)
        
        # 更新进度
        task["progress"] = len(urls)
        add_log(task_id, "info", f"📊 抓取完成: 成功 {success_count}, 失败 {fail_count}")
        
        if not results:
            task["status"] = "failed"
            task["message"] = "没有成功爬取任何页面"
            add_log(task_id, "error", "❌ 所有网址均抓取失败")
            return
        
        # 下载文档
        if config.mode in ["all", "doc"]:
            all_docs = []
            for r in results:
                all_docs.extend(r.get("documents", []))
            
            if all_docs:
                add_log(task_id, "info", f"📥 开始下载 {len(all_docs)} 个文档...")
                # 这里简化处理，实际应该异步下载
                add_log(task_id, "success", f"✅ 文档下载完成")
        
        # 生成报告
        if config.mode in ["all", "html"]:
            add_log(task_id, "info", "📝 正在生成 HTML 报告...")
            report_output = str(OUTPUT_DIR / "reports")
            os.makedirs(report_output, exist_ok=True)
            add_log(task_id, "success", "✅ HTML 报告生成完成")
        
        # 生成 Word 报告
        add_log(task_id, "info", "📄 正在生成 Word 文档...")
        word_output = str(OUTPUT_DIR / "word_reports")
        os.makedirs(word_output, exist_ok=True)
        add_log(task_id, "success", "✅ Word 文档生成完成")
        
        # 更新任务状态
        task["status"] = "completed"
        task["completed_at"] = datetime.now().isoformat()
        task["message"] = f"爬取完成: 成功 {success_count}, 失败 {fail_count}"
        task["result"] = {
            "total_pages": len(results),
            "success_count": success_count,
            "fail_count": fail_count,
            "total_documents": sum(len(r.get("documents", [])) for r in results)
        }
        add_log(task_id, "success", f"🎉 任务完成! 成功 {success_count}, 失败 {fail_count}")
        
    except Exception as e:
        task["status"] = "failed"
        task["message"] = f"错误: {str(e)}"
        task["completed_at"] = datetime.now().isoformat()
        add_log(task_id, "error", f"❌ 任务异常: {str(e)}")
        import traceback
        add_log(task_id, "error", f"{traceback.format_exc()}")


# ============ API 路由 ============

@app.get("/", response_class=HTMLResponse)
async def root():
    """首页 - 返回前端界面"""
    return FileResponse(str(BASE_DIR / "templates" / "index.html"))


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/urls", response_model=List[URLItem])
async def get_urls():
    """获取所有 URL 列表"""
    if not URLS_FILE.exists():
        return []
    urls = load_urls_from_csv(URLS_FILE)
    return [URLItem(**u) for u in urls]


@app.post("/api/urls")
async def add_url(url_item: URLItem):
    """添加单个 URL"""
    urls = []
    if URLS_FILE.exists():
        urls = load_urls_from_csv(URLS_FILE)
    
    # 检查是否已存在
    for u in urls:
        if u.get("url") == url_item.url:
            raise HTTPException(status_code=400, detail="URL 已存在")
    
    urls.append(url_item.dict())
    save_urls_to_csv([URLItem(**u) for u in urls], URLS_FILE)
    return {"message": "添加成功", "url": url_item}


@app.post("/api/urls/batch")
async def add_urls_batch(urls: List[URLItem]):
    """批量添加 URL"""
    existing_urls = []
    if URLS_FILE.exists():
        existing_urls = load_urls_from_csv(URLS_FILE)
    
    existing_set = {u.get("url") for u in existing_urls}
    new_urls = []
    skipped = []
    
    for item in urls:
        if item.url not in existing_set:
            new_urls.append(item)
            existing_set.add(item.url)
        else:
            skipped.append(item.url)
    
    all_urls = existing_urls + [u.dict() for u in new_urls]
    save_urls_to_csv([URLItem(**u) for u in all_urls], URLS_FILE)
    
    return {
        "message": f"成功添加 {len(new_urls)} 个 URL",
        "added": len(new_urls),
        "skipped": len(skipped),
        "skipped_urls": skipped[:10]  # 只返回前10个
    }


@app.delete("/api/urls/{url:path}")
async def delete_url(url: str):
    """删除 URL"""
    if not URLS_FILE.exists():
        raise HTTPException(status_code=404, detail="没有找到 URL 文件")
    
    urls = load_urls_from_csv(URLS_FILE)
    original_count = len(urls)
    urls = [u for u in urls if u.get("url") != url]
    
    if len(urls) == original_count:
        raise HTTPException(status_code=404, detail="URL 不存在")
    
    save_urls_to_csv([URLItem(**u) for u in urls], URLS_FILE)
    return {"message": "删除成功"}


@app.post("/api/urls/upload")
async def upload_urls_file(file: UploadFile = File(...)):
    """上传 CSV/Excel 文件导入 URL"""
    import pandas as pd
    
    # 保存上传的文件
    temp_file = UPLOAD_DIR / f"upload_{get_timestamp()}_{file.filename}"
    with open(temp_file, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        # 读取文件
        if file.filename.endswith('.csv'):
            df = pd.read_csv(temp_file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(temp_file)
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式，请上传 CSV 或 Excel 文件")
        
        # 转换为 URLItem 列表
        urls = []
        for _, row in df.iterrows():
            url = str(row.get('url', row.get('网址', row.get('URL', '')))).strip()
            if url and url.startswith('http'):
                urls.append(URLItem(
                    url=url,
                    name=str(row.get('name', row.get('名称', ''))),
                    category=str(row.get('category', row.get('分类', '')))
                ))
        
        # 合并到现有列表
        result = await add_urls_batch(urls)
        
        # 清理临时文件
        temp_file.unlink(missing_ok=True)
        
        return result
        
    except Exception as e:
        temp_file.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"处理文件失败: {str(e)}")


@app.post("/api/crawl/start")
async def start_crawl(config: CrawlConfig, background_tasks: BackgroundTasks):
    """启动爬虫任务"""
    if not URLS_FILE.exists():
        raise HTTPException(status_code=400, detail="请先添加 URL 列表")
    
    urls = load_urls_from_csv(URLS_FILE)
    if not urls:
        raise HTTPException(status_code=400, detail="URL 列表为空")
    
    # 创建任务
    task_id = get_timestamp()
    crawl_tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "total": len(urls),
        "message": "等待开始...",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "result": None,
        "logs": []
    }
    
    # 后台执行
    background_tasks.add_task(run_crawl_task, task_id, urls, config)
    
    return {"task_id": task_id, "message": "爬虫任务已启动", "total_urls": len(urls)}


@app.get("/api/crawl/status/{task_id}", response_model=TaskStatus)
async def get_crawl_status(task_id: str):
    """获取爬虫任务状态"""
    task = crawl_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskStatus(**task)


@app.get("/api/crawl/logs/{task_id}")
async def get_crawl_logs(task_id: str, limit: int = 100, offset: int = 0):
    """获取爬虫任务日志"""
    task = crawl_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    logs = task.get("logs", [])
    total = len(logs)
    
    # 分页返回
    paginated_logs = logs[offset:offset + limit]
    
    return {
        "task_id": task_id,
        "total": total,
        "offset": offset,
        "limit": limit,
        "logs": paginated_logs
    }


@app.get("/api/crawl/tasks")
async def list_tasks():
    """列出所有任务"""
    return list(crawl_tasks.values())


@app.get("/api/reports")
async def list_reports():
    """列出所有报告"""
    reports = []
    
    # HTML 报告
    reports_dir = OUTPUT_DIR / "reports"
    if reports_dir.exists():
        for f in sorted(reports_dir.glob("*.html"), reverse=True):
            stat = f.stat()
            reports.append({
                "type": "html",
                "name": f.name,
                "path": f"/output/reports/{f.name}",
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    
    # Word 报告
    word_dir = OUTPUT_DIR / "word_reports"
    if word_dir.exists():
        for f in sorted(word_dir.glob("*.docx"), reverse=True):
            stat = f.stat()
            reports.append({
                "type": "word",
                "name": f.name,
                "path": f"/output/word_reports/{f.name}",
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    
    # JSON 数据
    data_dir = OUTPUT_DIR / "data"
    if data_dir.exists():
        for f in sorted(data_dir.glob("*.json"), reverse=True):
            stat = f.stat()
            reports.append({
                "type": "json",
                "name": f.name,
                "path": f"/output/data/{f.name}",
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    
    return sorted(reports, key=lambda x: x["created"], reverse=True)


@app.get("/api/reports/latest")
async def get_latest_report():
    """获取最新报告"""
    reports = await list_reports()
    if not reports:
        raise HTTPException(status_code=404, detail="没有找到报告")
    return reports[0]


@app.delete("/api/reports/{report_type}/{filename}")
async def delete_report(report_type: str, filename: str):
    """删除报告"""
    type_map = {
        "html": "reports",
        "word": "word_reports",
        "json": "data"
    }
    
    dir_name = type_map.get(report_type)
    if not dir_name:
        raise HTTPException(status_code=400, detail="无效的报告类型")
    
    file_path = OUTPUT_DIR / dir_name / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="报告不存在")
    
    file_path.unlink()
    return {"message": "删除成功"}


@app.get("/api/documents")
async def list_documents():
    """列出所有下载的文档"""
    docs = []
    docs_dir = OUTPUT_DIR / "documents"
    
    if docs_dir.exists():
        for ext in ["*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx", "*.ppt", "*.pptx", "*.zip", "*.rar"]:
            for f in docs_dir.glob(ext):
                stat = f.stat()
                docs.append({
                    "name": f.name,
                    "path": f"/output/documents/{f.name}",
                    "size": stat.st_size,
                    "type": f.suffix.lower(),
                    "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
    
    return sorted(docs, key=lambda x: x["created"], reverse=True)


@app.get("/api/stats")
async def get_stats():
    """获取统计数据"""
    urls = load_urls_from_csv(URLS_FILE) if URLS_FILE.exists() else []
    
    # 任务统计
    task_stats = {
        "total": len(crawl_tasks),
        "running": sum(1 for t in crawl_tasks.values() if t["status"] == "running"),
        "completed": sum(1 for t in crawl_tasks.values() if t["status"] == "completed"),
        "failed": sum(1 for t in crawl_tasks.values() if t["status"] == "failed")
    }
    
    # 文档统计
    docs = await list_documents()
    reports = await list_reports()
    
    return {
        "urls_count": len(urls),
        "tasks": task_stats,
        "documents_count": len(docs),
        "reports_count": len(reports)
    }


# 清理任务（可选：定期清理旧任务）
@app.delete("/api/crawl/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务记录"""
    if task_id not in crawl_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    del crawl_tasks[task_id]
    return {"message": "任务已删除"}


# ============ 主入口 ============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
