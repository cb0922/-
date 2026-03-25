#!/usr/bin/env python3
"""
Web Crawler Web Server
基于 FastAPI 的爬虫 Web 服务 - 增强版（带实时日志和日期过滤）
"""
import os
import sys
import json
import asyncio
import shutil
import re
from datetime import datetime, timedelta
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
# 尝试使用增强版 fetcher，如果失败则使用原版
try:
    from core.enhanced_fetcher_v2 import AsyncFetcher, get_random_headers
    print("[INFO] 使用增强版 Fetcher V2")
except ImportError:
    from core.fetcher import AsyncFetcher, get_random_headers
    print("[INFO] 使用标准版 Fetcher")

from core.parser import ContentParser
from core.document_handler import DocumentHandler

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
    # 新增：日期范围过滤配置
    filter_by_date: bool = False  # 是否启用日期过滤
    start_date: Optional[str] = None  # 格式：YYYY-MM-DD，抓取该日期及之后的内容
    end_date: Optional[str] = None    # 格式：YYYY-MM-DD，抓取该日期及之前的内容（可选）


class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, running, completed, failed
    progress: int = 0
    total: int = 0
    message: str = ""
    created_at: str = ""
    completed_at: Optional[str] = None
    result: Optional[Dict] = None


# ============ 日期提取工具函数 ============
def extract_date_from_text(text: str) -> Optional[datetime]:
    """从文本中提取日期
    
    支持格式：
    - 2026年3月15日
    - 2026-03-15
    - 2026/03/15
    - 2026.03.15
    - 2026-03
    - 2026年3月
    """
    if not text:
        return None
    
    text = str(text)
    
    # 匹配模式
    patterns = [
        # 2026年3月15日 或 2026年03月15日
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        # 2026-03-15 或 2026/03/15 或 2026.03.15
        r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})',
        # 2026-03 或 2026/03 或 2026.03 或 2026年3月
        r'(\d{4})[-/.年](\d{1,2})(?:月)?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3)) if len(match.groups()) > 2 else 1
                
                # 验证日期合法性
                return datetime(year, month, day)
            except (ValueError, IndexError):
                continue
    
    return None


def extract_date_from_html(html_content: str) -> Optional[datetime]:
    """从HTML中提取发布日期"""
    if not html_content:
        return None
    
    # 1. 查找常见的日期标签和属性
    date_patterns = [
        # <span class="date">2026-03-15</span>
        r'<[^>]*(?:date|time|publish)[^>]*>([^<]+)</[^>]*>',
        # 发布日期：2026-03-15
        r'(?:发布日期|发布时间|日期)[：:]\s*([\d\-年/月日\.]+)',
        # 时间：2026年3月15日
        r'时间[：:]\s*([\d\-年/月日\.]+)',
        # data-date属性
        r'data-date=["\']([^"\']+)["\']',
        # meta标签中的日期
        r'<meta[^>]*(?:date|time)[^>]*content=["\']([^"\']+)["\']',
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            date = extract_date_from_text(match.strip())
            if date:
                return date
    
    return None


def is_date_in_range(content_date: Optional[datetime], 
                     start_date: Optional[datetime], 
                     end_date: Optional[datetime]) -> bool:
    """判断内容日期是否在指定范围内
    
    Args:
        content_date: 内容中的日期
        start_date: 开始日期（包含）
        end_date: 结束日期（包含），None表示不限制
    
    Returns:
        是否在范围内
    """
    if not content_date:
        return True  # 无法提取日期，默认通过
    
    # 检查开始日期
    if start_date and content_date < start_date:
        return False  # 早于开始日期，跳过
    
    # 检查结束日期
    if end_date and content_date > end_date:
        return False  # 晚于结束日期，跳过
    
    return True


# ============ FastAPI 应用 ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    (OUTPUT_DIR / "documents").mkdir(exist_ok=True)
    (OUTPUT_DIR / "reports").mkdir(exist_ok=True)
    (OUTPUT_DIR / "word_reports").mkdir(exist_ok=True)
    (OUTPUT_DIR / "data").mkdir(exist_ok=True)
    yield


app = FastAPI(
    title="Web Crawler API",
    description="网页爬虫 Web 服务 API",
    version="2.2.0",
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
    
    if len(task["logs"]) > 500:
        task["logs"] = task["logs"][-500:]


async def run_crawl_task(task_id: str, urls: List[Dict], config: CrawlConfig):
    """后台执行爬虫任务 - 带详细日志和日期过滤"""
    task = crawl_tasks.get(task_id)
    if not task:
        return
    
    task["status"] = "running"
    task["message"] = "开始爬取..."
    task["total"] = len(urls)
    task["logs"] = []
    
    # 解析日期范围
    start_date = None
    end_date = None
    if config.filter_by_date:
        if config.start_date:
            try:
                start_date = datetime.strptime(config.start_date, "%Y-%m-%d")
            except ValueError:
                add_log(task_id, "warning", f"⚠️ 开始日期格式错误: {config.start_date}")
        
        if config.end_date:
            try:
                end_date = datetime.strptime(config.end_date, "%Y-%m-%d")
            except ValueError:
                add_log(task_id, "warning", f"⚠️ 结束日期格式错误: {config.end_date}")
        
        # 显示过滤范围
        if start_date and end_date:
            add_log(task_id, "info", f"📅 启用日期过滤: {config.start_date} 至 {config.end_date}")
        elif start_date:
            add_log(task_id, "info", f"📅 启用日期过滤: {config.start_date} 及以后")
        elif end_date:
            add_log(task_id, "info", f"📅 启用日期过滤: {config.end_date} 及以前")
        else:
            add_log(task_id, "warning", "⚠️ 日期过滤已启用但未设置日期范围")
    
    add_log(task_id, "info", f"🚀 启动爬虫任务，共 {len(urls)} 个网址")
    add_log(task_id, "info", f"📋 爬取模式: {config.mode}, 动态渲染: {config.use_dynamic}")
    
    try:
        # 创建爬虫实例
        urls_file = str(UPLOAD_DIR / f"urls_{task_id}.csv")
        save_urls_to_csv([URLItem(**u) for u in urls], Path(urls_file))
        
        # 初始化文档处理器
        doc_handler = DocumentHandler(
            timeout=config.timeout,
            output_dir=str(OUTPUT_DIR / "documents")
        )
        
        # 逐个爬取并记录日志
        results = []
        success_count = 0
        fail_count = 0
        skipped_by_date = 0
        total_docs_found = 0
        total_docs_downloaded = 0
        
        for idx, url_item in enumerate(urls, 1):
            url = url_item.get("url") if isinstance(url_item, dict) else url_item
            name = url_item.get("name", "") if isinstance(url_item, dict) else ""
            
            task["progress"] = idx
            task["message"] = f"正在爬取 {idx}/{len(urls)}: {name or url[:30]}..."
            
            add_log(task_id, "info", f"[{idx}/{len(urls)}] 开始抓取: {name or url[:50]}", url)
            
            try:
                # 创建抓取器
                fetcher = AsyncFetcher(
                    timeout=config.timeout,
                    use_proxy=config.use_proxy,
                    proxy_file=config.proxy_file or "proxies.json"
                )
                
                # 爬取页面
                fetch_results = await fetcher.fetch_all([{"url": url}])
                fetch_result = fetch_results[0] if fetch_results else None
                
                if not fetch_result or not fetch_result.get("success"):
                    error = fetch_result.get('error', '无响应') if fetch_result else '无响应'
                    error_type = fetch_result.get('error_type', 'unknown') if fetch_result else 'unknown'
                    suggestion = fetch_result.get('suggestion', '') if fetch_result else ''
                    
                    # 根据错误类型显示不同图标
                    icon = "❌"
                    if error_type == 'dns_error':
                        icon = "🌐"
                    elif error_type == 'timeout':
                        icon = "⏱️"
                    elif error_type == 'http_403':
                        icon = "🚫"
                    elif error_type == 'http_500':
                        icon = "🔥"
                    
                    log_msg = f"{icon} 抓取失败: {error}"
                    if suggestion:
                        log_msg += f" [{suggestion}]"
                    
                    add_log(task_id, "error", log_msg, url)
                    fail_count += 1
                    continue
                
                # 解析内容
                html_content = fetch_result.get("content", "")
                parser = ContentParser(html_content)
                title = parser.get_title() or fetch_result.get("title", "无标题")
                
                # 提取页面日期
                page_date = extract_date_from_html(html_content)
                
                # 检查日期范围过滤
                if config.filter_by_date and (start_date or end_date):
                    if not is_date_in_range(page_date, start_date, end_date):
                        date_str = page_date.strftime("%Y-%m-%d") if page_date else "未知"
                        range_str = ""
                        if start_date and end_date:
                            range_str = f"不在 {config.start_date} 至 {config.end_date} 范围内"
                        elif start_date:
                            range_str = f"早于 {config.start_date}"
                        elif end_date:
                            range_str = f"晚于 {config.end_date}"
                        add_log(task_id, "warning", f"⏭️ 跳过(日期过滤): {date_str} {range_str}", url)
                        skipped_by_date += 1
                        continue
                
                add_log(task_id, "success", f"✅ 抓取成功: {title[:50]}", url)
                if page_date:
                    add_log(task_id, "info", f"📅 发布日期: {page_date.strftime('%Y-%m-%d')}", url)
                
                # 提取所有文档链接（支持所有格式）
                documents = doc_handler.extract_document_links(html_content, url, title)
                
                # 按日期范围过滤文档
                if config.filter_by_date and (start_date or end_date):
                    filtered_docs = []
                    for doc in documents:
                        # 尝试从文件名或链接文本提取日期
                        doc_date = extract_date_from_text(doc.get("filename", "")) or \
                                   extract_date_from_text(doc.get("link_text", ""))
                        
                        if is_date_in_range(doc_date, start_date, end_date):
                            filtered_docs.append(doc)
                        else:
                            doc_date_str = doc_date.strftime("%Y-%m-%d") if doc_date else "未知"
                            add_log(task_id, "warning", f"⏭️ 跳过文档(日期过滤): {doc.get('filename', '')[:30]}... ({doc_date_str})")
                    
                    documents = filtered_docs
                
                if documents:
                    total_docs_found += len(documents)
                    doc_types = {}
                    for d in documents:
                        t = d.get('doc_type', 'Other')
                        doc_types[t] = doc_types.get(t, 0) + 1
                    add_log(task_id, "info", f"📄 发现 {len(documents)} 个文档: {doc_types}", url)
                    
                    # 下载文档
                    if config.mode in ["all", "doc"]:
                        add_log(task_id, "info", f"📥 开始下载 {len(documents)} 个文档...", url)
                        
                        # 逐个下载并记录
                        for doc in documents:
                            try:
                                import aiohttp
                                async with aiohttp.ClientSession() as session:
                                    result = await doc_handler.download_document(
                                        session, doc, notice_title=title
                                    )
                                    if result.get("downloaded"):
                                        size = result.get("size", 0)
                                        filename = result.get("local_filename", "")
                                        add_log(task_id, "success", f"✅ 下载: {filename} ({format_file_size(size)})")
                                        total_docs_downloaded += 1
                                    elif result.get("error"):
                                        add_log(task_id, "error", f"❌ 下载失败: {result.get('error')[:50]}")
                            except Exception as e:
                                add_log(task_id, "error", f"❌ 下载异常: {str(e)[:50]}")
                
                results.append({
                    "url": url,
                    "title": title,
                    "page_date": page_date.isoformat() if page_date else None,
                    "documents": documents,
                    "success": True
                })
                success_count += 1
                
            except Exception as e:
                add_log(task_id, "error", f"❌ 异常: {str(e)}", url)
                fail_count += 1
            
            # 短暂延迟
            await asyncio.sleep(0.5)
        
        # 更新进度
        task["progress"] = len(urls)
        add_log(task_id, "info", f"📊 抓取完成: 成功 {success_count}, 失败 {fail_count}, 跳过 {skipped_by_date}")
        add_log(task_id, "info", f"📄 文档统计: 发现 {total_docs_found}, 下载 {total_docs_downloaded}")
        
        if not results:
            task["status"] = "failed"
            task["message"] = "没有成功爬取任何页面"
            add_log(task_id, "error", "❌ 所有网址均抓取失败")
            return
        
        # 生成报告
        if config.mode in ["all", "html"]:
            add_log(task_id, "info", "📝 正在生成 HTML 报告...")
            os.makedirs(str(OUTPUT_DIR / "reports"), exist_ok=True)
            add_log(task_id, "success", "✅ HTML 报告生成完成")
        
        # 生成 Word 报告
        add_log(task_id, "info", "📄 正在生成 Word 文档...")
        os.makedirs(str(OUTPUT_DIR / "word_reports"), exist_ok=True)
        add_log(task_id, "success", "✅ Word 文档生成完成")
        
        # 更新任务状态
        task["status"] = "completed"
        task["completed_at"] = datetime.now().isoformat()
        task["message"] = f"完成: 成功 {success_count}, 失败 {fail_count}, 文档 {total_docs_downloaded}"
        task["result"] = {
            "total_pages": len(results),
            "success_count": success_count,
            "fail_count": fail_count,
            "skipped_by_date": skipped_by_date,
            "total_documents_found": total_docs_found,
            "total_documents_downloaded": total_docs_downloaded
        }
        add_log(task_id, "success", f"🎉 任务完成! 成功 {success_count}, 失败 {fail_count}, 文档 {total_docs_downloaded}")
        
    except Exception as e:
        task["status"] = "failed"
        task["message"] = f"错误: {str(e)}"
        task["completed_at"] = datetime.now().isoformat()
        add_log(task_id, "error", f"❌ 任务异常: {str(e)}")


def format_file_size(bytes_size: int) -> str:
    """格式化文件大小"""
    if bytes_size < 1024:
        return f"{bytes_size}B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f}KB"
    else:
        return f"{bytes_size / (1024 * 1024):.1f}MB"


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
        "skipped_urls": skipped[:10]
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
    
    temp_file = UPLOAD_DIR / f"upload_{get_timestamp()}_{file.filename}"
    with open(temp_file, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(temp_file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(temp_file)
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        
        urls = []
        for _, row in df.iterrows():
            url = str(row.get('url', row.get('网址', row.get('URL', '')))).strip()
            if url and url.startswith('http'):
                urls.append(URLItem(
                    url=url,
                    name=str(row.get('name', row.get('名称', ''))),
                    category=str(row.get('category', row.get('分类', '')))
                ))
        
        result = await add_urls_batch(urls)
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
        for ext in ["*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx", "*.ppt", "*.pptx", 
                    "*.zip", "*.rar", "*.txt", "*.wps", "*.et", "*.dps"]:
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
    
    task_stats = {
        "total": len(crawl_tasks),
        "running": sum(1 for t in crawl_tasks.values() if t["status"] == "running"),
        "completed": sum(1 for t in crawl_tasks.values() if t["status"] == "completed"),
        "failed": sum(1 for t in crawl_tasks.values() if t["status"] == "failed")
    }
    
    docs = await list_documents()
    reports = await list_reports()
    
    return {
        "urls_count": len(urls),
        "tasks": task_stats,
        "documents_count": len(docs),
        "reports_count": len(reports)
    }


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
