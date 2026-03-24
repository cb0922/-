# 网页信息采集爬虫工具

一个简单易用的网页信息采集工具，支持从表格导入URL、异步并发爬取、多格式数据存储。

## 功能特点

- **URL管理**: 支持从 CSV/Excel 文件批量导入网址
- **异步爬取**: 基于 aiohttp 的高性能异步爬虫
- **内容解析**: 自动提取标题、正文、链接、图片等
- **多格式存储**: 支持 JSON、CSV、SQLite 三种格式
- **配置灵活**: 可调节并发数、超时时间、请求间隔

## 快速开始

### 1. 安装依赖

```bash
cd web_crawler
pip install -r requirements.txt
```

### 2. 准备URL列表

创建 CSV 或 Excel 文件，包含以下列：
- `url` - 要爬取的网页地址（必需）
- `name` - 网站名称（可选）
- `category` - 分类（可选）
- `priority` - 优先级（可选）

```csv
url,name,category,priority
https://example.com/news,示例新闻站,新闻,1
https://example.com/blog,示例博客,博客,2
```

或使用命令创建模板：

```bash
python main.py --template urls.csv
```

### 3. 运行爬虫

```bash
# 基础用法
python main.py --urls urls.csv

# 指定输出格式
python main.py --urls urls.csv --format json,csv

# 调整爬虫参数
python main.py --urls urls.csv --concurrency 10 --delay 0.5
```

### 4. 快速运行（简化版）

编辑 `run.py` 中的配置后直接运行：

```bash
python run.py
```

## 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--urls` | `-u` | URL源文件路径 | 必需 |
| `--format` | `-f` | 输出格式 (json/csv/sqlite) | json |
| `--output` | `-o` | 输出文件名 | 自动生成 |
| `--parser` | `-p` | 解析器类型 (auto/article) | auto |
| `--concurrency` | `-c` | 并发请求数 | 5 |
| `--timeout` | `-t` | 请求超时时间(秒) | 30 |
| `--delay` | `-d` | 请求间隔(秒) | 1.0 |
| `--template` | | 创建URL模板文件 | |

## 项目结构

```
web_crawler/
├── config/           # 配置文件
│   └── settings.py   # 爬虫和存储配置
├── core/             # 核心模块
│   ├── url_manager.py    # URL管理
│   ├── fetcher.py        # 异步爬取
│   └── parser.py         # 内容解析
├── storage/          # 存储模块
│   └── database.py       # 数据存储
├── data/             # 数据输出目录
├── logs/             # 日志目录
├── main.py           # 主控脚本
├── run.py            # 简化运行脚本
├── requirements.txt  # 依赖列表
└── README.md         # 使用说明
```

## 代码使用示例

```python
from core.url_manager import URLManager
from core.fetcher import AsyncFetcher
from core.parser import ContentParser
from storage.database import StorageManager

# 1. 加载URL
url_manager = URLManager()
url_manager.load_from_file("urls.csv")

# 2. 爬取
fetcher = AsyncFetcher(concurrency=5)
results = fetcher.run(url_manager.urls)

# 3. 解析
for result in results:
    if result["success"]:
        parser = ContentParser(result["content"])
        print(parser.get_title())
        print(parser.get_text())

# 4. 存储
storage = StorageManager("./data")
storage.save(parsed_data, formats=["json", "csv"])
```

## 注意事项

1. **遵守robots.txt**: 爬取前请检查目标网站的 robots.txt 文件
2. **控制频率**: 合理设置 `--delay` 参数，避免对目标网站造成压力
3. **合法使用**: 仅用于爬取公开信息，遵守相关法律法规
4. **数据隐私**: 妥善保管爬取的数据，不用于非法用途

## 依赖库

- aiohttp - 异步HTTP请求
- beautifulsoup4 - HTML解析
- pandas - 数据处理
- lxml - XML/HTML解析器
- tqdm - 进度条显示
