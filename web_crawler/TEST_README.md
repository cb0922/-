# GUI问题测试方案

## 问题分析

GUI报错 "Crawl failed with code 2" 可能的原因：

1. **事件循环冲突** - GUI使用QThread，爬虫使用asyncio.run()，可能冲突
2. **路径问题** - 工作目录不正确导致文件找不到
3. **异常未捕获** - 爬虫内部异常导致返回码非零

## 测试步骤

### 步骤1: 测试命令行版本（验证核心功能）

```bash
cd C:\Users\PC\kim\web_crawler
python start_crawler.py --urls urls.csv --mode doc --output ./test_output --no-auto-remove
```

如果这能正常工作，说明爬虫核心没问题，问题在GUI。

### 步骤2: 测试核心功能（验证事件循环）

```bash
python test_crawl_core.py
```

这个脚本直接调用爬虫API，不通过GUI。

### 步骤3: 测试极简版GUI

```bash
python gui_simple.py
```

或双击 `run_simple_gui.bat`

这是最简化的GUI版本，只保留核心功能，用于隔离问题。

### 步骤4: 如果极简版正常，测试完整版GUI

```bash
python start_fixed.py
```

或双击 `start_gui_fixed.bat`

## 常见问题

### 问题: "RuntimeError: asyncio.run() cannot be called from a running event loop"

**解决**: 安装 nest-asyncio
```bash
pip install nest-asyncio
```

### 问题: "FileNotFoundError" 或返回码2

**解决**: 确保工作目录正确，所有文件路径使用绝对路径

### 问题: 文档下载失败

**解决**: 
1. 检查输出目录权限
2. 检查 `output/documents/` 目录是否可写
3. 查看 `test_output` 目录中的日志

## 如果还有问题

请运行诊断工具并提供输出：

```bash
python diagnose_gui.py > diagnosis_log.txt 2>&1
```

然后将 `diagnosis_log.txt` 内容提供给我。
