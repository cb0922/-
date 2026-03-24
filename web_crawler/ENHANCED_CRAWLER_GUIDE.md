# 增强型比赛通知综合爬虫使用指南

## 功能概述

这是一个功能全面的比赛通知爬虫，支持以下特性：

1. **PDF文件抓取** - 自动下载比赛通知PDF到本地
2. **网页内容抓取** - 提取网页形式的比赛通知并生成可视化HTML报告
3. **JavaScript动态加载支持** - 可渲染SPA单页应用的内容（需要Playwright）
4. **智能分类** - 自动识别比赛相关内容

## 文件说明

```
web_crawler/
├── enhanced_crawler.py          # 主程序 - 增强型爬虫
├── crawl_pdfs.py                # PDF专用爬虫（原版）
├── setup_dynamic_crawler.py     # Playwright安装脚本
├── report_generator.py          # HTML报告生成器
└── ENHANCED_CRAWLER_GUIDE.md    # 本指南
```

## 安装步骤

### 1. 基础依赖（已安装）

```bash
pip install -r requirements.txt
```

### 2. JavaScript动态渲染支持（可选）

如果需要抓取SPA单页应用（如企鹅教师助手）：

```bash
python setup_dynamic_crawler.py
```

或手动安装：

```bash
pip install playwright
python -m playwright install chromium
```

## 使用方法

### 快速开始

```bash
cd web_crawler
python enhanced_crawler.py --urls urls.csv
```

### 命令行参数

```bash
python enhanced_crawler.py --urls urls.csv [OPTIONS]
```

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--urls` | `-u` | URL源文件路径（必需） | - |
| `--mode` | `-m` | 抓取模式：`all`/`pdf`/`html` | `all` |
| `--dynamic` | `-d` | 启用JavaScript动态渲染 | False |
| `--timeout` | `-t` | 请求超时时间（秒） | 30 |
| `--output` | `-o` | 输出目录 | `./output` |

### 使用示例

#### 1. 抓取所有内容（PDF + HTML可视化）

```bash
python enhanced_crawler.py --urls urls.csv --mode all
```

#### 2. 仅抓取PDF文件

```bash
python enhanced_crawler.py --urls urls.csv --mode pdf
```

#### 3. 仅生成网页可视化报告

```bash
python enhanced_crawler.py --urls urls.csv --mode html
```

#### 4. 启用JavaScript动态渲染

对于SPA单页应用（如React/Vue应用）：

```bash
python enhanced_crawler.py --urls urls.csv --dynamic
```

#### 5. 完整功能（动态渲染 + 所有内容）

```bash
python enhanced_crawler.py --urls urls.csv --mode all --dynamic --timeout 60
```

## 输出文件

### 1. PDF文件

保存位置：`pdfs/competitions/`

```
pdfs/competitions/
├── 第九届语文报杯全国语文微课大.pdf
└── 第八届语文报杯全国语文微课大.pdf
```

### 2. HTML可视化报告

保存位置：`reports/report_YYYYMMDD_HHMMSS.html`

报告包含：
- 统计概览卡片
- 搜索功能
- 每个网站的内容摘要
- 关键词标签
- 可折叠的正文内容
- 元数据（链接数、图片数等）

### 3. JSON数据

保存位置：`output/data/enhanced_crawl_*.json`

包含详细的结构化数据，方便二次处理。

## 工作流程

```
┌─────────────────┐
│   读取URL列表    │
└────────┬────────┘
         ▼
┌─────────────────┐
│   爬取网页      │◄──── 静态HTTP / 动态渲染(Playwright)
└────────┬────────┘
         ▼
┌─────────────────┐
│   内容分析      │
│  - 标题提取     │
│  - 比赛相关检测 │
│  - PDF链接提取  │
└────────┬────────┘
         ▼
┌─────────────────┐     ┌─────────────────┐
│   下载PDF       │────►│   生成HTML报告  │
└─────────────────┘     └─────────────────┘
```

## 抓取模式对比

| 模式 | PDF下载 | HTML报告 | 适用场景 |
|------|---------|----------|----------|
| `all` | ✅ | ✅ | 全面抓取 |
| `pdf` | ✅ | ❌ | 只需要文档 |
| `html` | ❌ | ✅ | 只需要浏览内容 |

## 动态渲染说明

### 什么是动态渲染？

现代网站（如React、Vue、Angular应用）使用JavaScript动态加载内容。传统爬虫只能获取初始HTML框架，无法获取实际内容。

### 哪些网站需要动态渲染？

- 单页应用（SPA）
- 内容通过AJAX加载的网站
- 需要用户交互才显示内容的网站

### 示例

**企鹅教师助手** (`aiteach.qq.com`)：

- 不使用 `--dynamic`：只能获取1769字符的框架HTML
- 使用 `--dynamic`：可以获取完整的渲染后内容

### 性能注意

动态渲染比静态抓取慢3-5倍，建议：
- 只对需要动态渲染的网站使用
- 增加超时时间 `--timeout 60`

## 常见问题

### Q1: 为什么某些网站抓取失败？

可能原因：
- 网站有反爬虫机制（如优教杯403错误）
- 需要动态渲染（使用 `--dynamic`）
- 网络问题或超时（增加 `--timeout`）

### Q2: 为什么PDF文件命名不完整？

文件名长度限制为100字符（系统限制），超长部分会被截断。

### Q3: 如何批量添加URL？

编辑 `urls.csv` 文件：

```csv
url
https://example1.com/
https://example2.com/
```

### Q4: 如何查看历史抓取结果？

- PDF文件：`pdfs/competitions/`
- HTML报告：`reports/` 目录
- JSON数据：`output/data/` 或 `data/` 目录

## 升级路线图

### 已完成功能 ✅

- [x] PDF自动下载
- [x] 网页内容可视化报告
- [x] JavaScript动态渲染支持
- [x] 智能比赛内容识别
- [x] 批量URL处理

### 计划功能 📋

- [ ] 定时自动抓取
- [ ] 邮件通知新公告
- [ ] PDF内容OCR提取
- [ ] 增量更新（只抓取新内容）
- [ ] 多线程并发优化

## 技术架构

```
EnhancedCompetitionCrawler
├── crawl_single_sync()      # 单页面爬取
│   ├── Static (requests)    # 静态抓取
│   └── Dynamic (Playwright) # 动态渲染
├── download_pdfs()          # PDF下载
├── generate_html_report()   # HTML报告生成
└── save_json_data()         # 数据持久化
```

## 联系与支持

如有问题或建议，请查看项目文档或提交反馈。

---

**更新日期**: 2026-03-20  
**版本**: v2.0 - Enhanced Edition
