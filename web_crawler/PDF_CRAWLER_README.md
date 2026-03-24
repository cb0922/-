# 比赛通知PDF专用爬虫使用说明

## 功能简介

专门用于爬取网页上的比赛信息通知和公告PDF文件。自动识别、筛选并下载与比赛相关的PDF文件。

## 核心功能

1. **自动PDF检测** - 从网页中自动提取所有PDF链接
2. **智能筛选** - 自动识别与比赛/通知相关的PDF
3. **批量下载** - 并发下载PDF文件到本地
4. **详细报告** - 生成扫描和下载的详细报告

## 使用方法

### 1. 准备URL列表

创建 `urls.csv` 文件，包含要爬取的网页URL：

```csv
url
https://wkds.zhyww.cn/
https://www.ncet.edu.cn/zhuzhan/sytztg/20250430/6449.html
```

### 2. 运行爬虫

#### 模式1: 扫描并下载所有PDF
```bash
python crawl_pdfs.py --urls urls.csv
```

#### 模式2: 只扫描，不下载
```bash
python crawl_pdfs.py --urls urls.csv --scan-only
```

#### 模式3: 只下载与比赛相关的PDF（推荐）
```bash
python crawl_pdfs.py --urls urls.csv --competition-only
```

#### 模式4: 指定输出目录
```bash
python crawl_pdfs.py --urls urls.csv --output my_competitions
```

### 3. 查看结果

#### 下载的PDF文件
```
pdfs/
└── competitions/
    ├── wkds8new.pdf    # 第八届语文报杯通知
    └── wkds9new.pdf    # 第九届语文报杯通知
```

#### 扫描结果（JSON格式）
```
data/pdf_scan_YYYYMMDD_HHMMSS.json
```

#### 文本报告
```
data/pdf_report_YYYYMMDD_HHMMSS.txt
```

## 识别规则

### 比赛相关关键词
爬虫会自动识别包含以下关键词的PDF：

- 大赛、比赛、竞赛
- 征集、评选、征稿
- 通知、公告、公示
- 简章、方案、指南

### PDF链接特征
支持检测以下格式的PDF链接：

- `xxx.pdf`
- `xxx.pdf?param=value`
- `/download/xxx.pdf`
- `/files/xxx.pdf`

## 输出示例

### 控制台输出
```
============================================================
COMPETITION PDF CRAWLER
比赛通知PDF专用爬虫
============================================================

加载URL列表: urls.csv
共加载 4 个URL

[1/3] 爬取 4 个网页...
爬取完成: 3/4 成功

[2/3] 提取PDF链接...
  [2个PDF] "语文报杯"全国语文微课大赛...
  [0个PDF] 教育部教育技术与资源发展中心...
  [0个PDF] 企鹅教师助手...

共发现 2 个PDF链接
其中与比赛/通知相关的PDF: 2 个

将下载与比赛相关的 2 个PDF

[3/3] 下载PDF文件 (共2个)...

下载完成!
  新下载: 2 个
  已存在: 0 个
  失败: 0 个
  总大小: 0.32 MB

============================================================
任务完成!
============================================================
```

### 文本报告示例
```
============================================================
比赛通知PDF扫描报告
============================================================

扫描网页数: 4
成功爬取: 3
发现PDF总数: 2
比赛相关PDF: 2

------------------------------------------------------------
详细PDF列表
------------------------------------------------------------

网页: "语文报杯"全国语文微课大赛
URL: https://wkds.zhyww.cn/
PDF数量: 2

  1. 关于组织参加第九届"语文报杯"全国语文微课大赛的通知（PDF）
     URL: https://wkds.zhyww.cn/wkds6/images/game9/wkds9new.pdf
     文件名: wkds9new.pdf
     [比赛相关]
     上下文: "语文报杯"全国语文微课大赛是语文报社为深入贯彻落实...
```

## 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--urls` | `-u` | URL源文件路径（必需） | - |
| `--scan-only` | - | 只扫描，不下载PDF | False |
| `--competition-only` | - | 只下载比赛相关PDF | False |
| `--output` | `-o` | PDF输出目录 | `./pdfs` |
| `--timeout` | `-t` | 请求超时时间（秒） | 30 |

## 文件结构

```
web_crawler/
├── crawl_pdfs.py          # 主程序
├── core/
│   ├── pdf_handler.py     # PDF处理器
│   ├── parser.py          # HTML解析器（含PDF提取）
│   └── ...
├── pdfs/                  # PDF下载目录
│   └── competitions/      # 比赛相关PDF
├── data/                  # 扫描结果和报告
│   ├── pdf_scan_*.json
│   └── pdf_report_*.txt
└── PDF_CRAWLER_README.md  # 本文件
```

## 注意事项

1. **合法性** - 请确保有权限下载目标网站的PDF文件
2. **网络** - 某些网站可能需要更长的超时时间（使用 `--timeout` 调整）
3. **存储** - 大量PDF会占用磁盘空间，注意清理
4. **反爬** - 部分网站可能有反爬虫机制，适当调整 `--delay` 参数

## 扩展功能（可选）

### 安装PDF解析库提取文本

```bash
pip install pdfplumber
```

安装后可提取PDF中的文本内容进行分析。

## 更新日志

- **v1.0** - 初始版本
  - 支持PDF链接自动检测
  - 支持比赛相关PDF智能筛选
  - 支持批量下载
  - 支持详细报告生成
