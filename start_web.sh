#!/bin/bash

# 比赛通知爬虫 Web 服务启动脚本

echo "======================================"
echo "   Web Crawler Web Server"
echo "======================================"

# 检查是否在项目根目录
if [ ! -d "web_crawler" ] || [ ! -d "web_server" ]; then
    echo "错误：请在项目根目录运行此脚本"
    exit 1
fi

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -q -r web_server/requirements.txt

# 创建必要的目录
echo "创建目录..."
mkdir -p web_server/uploads
mkdir -p web_server/output/{documents,reports,word_reports,data}

# 启动服务
echo ""
echo "======================================"
echo "  服务启动中..."
echo "  访问地址: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"
echo "======================================"
echo ""

cd web_server
export PYTHONPATH=$(dirname $(pwd))
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
