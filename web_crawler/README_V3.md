# 比赛通知爬虫 V3.0

## 功能特性

### 1. 多格式文档支持
支持下载各种比赛通知文档格式：
- **PDF** (.pdf)
- **Word** (.doc, .docx, .dot, .dotx, .rtf)
- **Excel** (.xls, .xlsx, .xlsm, .xlsb, .csv)
- **PowerPoint** (.ppt, .pptx, .pps, .ppsx)
- **压缩包** (.zip, .rar, .7z, .tar, .gz, .bz2)
- **文本** (.txt)
- **WPS** (.wps, .et, .dps)

文档自动按类型分类保存。

### 2. 自动删除无效网址
智能管理网址列表：
- 自动记录每个网址的失败次数
- 3次失败后自动从列表中删除
- 避免浪费时间在无效网址上
- 自动清理404/403/无法访问的网址

### 3. 反爬机制
- User-Agent轮换（50+个真实浏览器UA）
- 请求间隔随机化（1-3秒）
- 代理IP支持（HTTP/HTTPS/SOCKS5）
- 完整的浏览器请求头伪装

### 4. 多种输出格式
- **Word报告** - 完整比赛通知内容
- **HTML报告** - 可视化浏览
- **JSON数据** - 结构化数据
- **分类文档** - 按类型整理的下载文件

### 5. 全国网址库
内置78个官方教育网站：
- 全国电教馆网站
- 教科委网站
- 省市区教育资源中心

## 快速开始

### GUI模式（推荐）
```bash
python app_gui.py
```

### 命令行模式
```bash
# 基础爬取
python enhanced_crawler_v3.py --urls urls.csv

# 使用代理
python enhanced_crawler_v3.py --urls urls.csv --proxy

# 仅下载文档
python enhanced_crawler_v3.py --urls urls.csv --mode doc

# 禁用自动删除
python enhanced_crawler_v3.py --urls urls.csv --no-auto-remove
```

## 项目结构

```
web_crawler/
├── app_gui.py                 # PyQt6桌面应用
├── enhanced_crawler_v3.py     # V3主程序
├── core/
│   ├── document_handler.py    # 多格式文档处理器
│   ├── proxy_manager.py       # 代理管理
│   ├── anti_detection.py      # 反检测模块
│   ├── fetcher.py             # 异步爬取
│   ├── parser.py              # HTML解析
│   └── url_manager.py         # URL管理
├── word_generator.py          # Word报告生成
├── report_generator.py        # HTML报告生成
└── urls.csv                   # 网址列表
```

## 配置说明

### 代理配置
创建 `proxies.json`:
```json
[
  {
    "host": "proxy.example.com",
    "port": 8080,
    "protocol": "http",
    "username": "user",
    "password": "pass"
  }
]
```

### 自动删除配置
默认3次失败后删除，可通过参数调整：
```bash
# 设置5次失败后删除
python enhanced_crawler_v3.py --urls urls.csv --max-retries 5

# 完全禁用自动删除
python enhanced_crawler_v3.py --urls urls.csv --no-auto-remove
```

## 输出目录结构

```
output/
├── documents/          # 下载的文档
│   ├── PDF/
│   ├── Word/
│   ├── Excel/
│   ├── PowerPoint/
│   └── Archive/
├── word_reports/       # Word报告
├── reports/            # HTML报告
└── data/               # JSON数据
```

## 版本历史

- **V3.0** - 多格式文档支持，自动删除无效网址
- **V2.0** - 代理IP支持，反检测增强
- **V1.0** - 基础PDF爬取功能
