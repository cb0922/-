# 使用 Python 3.11 官方镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY web_server/requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY web_crawler /app/web_crawler/
COPY web_server /app/web_server/

# 创建必要的目录
RUN mkdir -p /app/web_server/uploads /app/web_server/output/documents \
    /app/web_server/output/reports /app/web_server/output/word_reports \
    /app/web_server/output/data

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 启动命令
WORKDIR /app/web_server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
