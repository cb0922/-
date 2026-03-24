# 比赛通知爬虫 - Web 部署指南

本文档介绍如何将本地爬虫工具部署为 Web 服务到腾讯云服务器。

## 📁 项目结构

```
kim/
├── web_crawler/          # 原始爬虫代码
│   ├── core/            # 核心模块
│   ├── enhanced_crawler_v3.py
│   └── ...
├── web_server/          # Web 服务代码
│   ├── main.py          # FastAPI 主入口
│   ├── api/             # API 路由
│   ├── static/          # 静态文件(CSS/JS)
│   ├── templates/       # HTML 模板
│   ├── uploads/         # 上传文件存储
│   └── requirements.txt # Python 依赖
├── Dockerfile           # Docker 构建配置
├── docker-compose.yml   # Docker Compose 配置
├── nginx.conf           # Nginx 配置
└── DEPLOY.md           # 本文档
```

## 🚀 快速部署（推荐）

### 方法一：使用 Docker Compose（最简单）

#### 1. 在腾讯云服务器上准备环境

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker
```

#### 2. 上传项目代码

```bash
# 在项目根目录打包
cd kim
tar czvf web-crawler.tar.gz web_crawler/ web_server/ Dockerfile docker-compose.yml

# 上传到服务器（本地执行）
scp web-crawler.tar.gz root@你的服务器IP:/root/

# 在服务器上解压
ssh root@你的服务器IP
tar xzvf web-crawler.tar.gz
cd kim
```

#### 3. 启动服务

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 4. 访问服务

打开浏览器访问：`http://你的服务器IP:8000`

---

### 方法二：手动部署（无 Docker）

#### 1. 安装 Python 3.11

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip

# 验证安装
python3.11 --version
```

#### 2. 上传并配置项目

```bash
# 创建项目目录
mkdir -p /opt/web-crawler
cd /opt/web-crawler

# 上传代码（本地执行）
scp -r web_crawler web_server root@你的服务器IP:/opt/web-crawler/

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r web_server/requirements.txt
```

#### 3. 创建启动脚本

```bash
cat > start.sh << 'EOF'
#!/bin/bash
cd /opt/web-crawler
source venv/bin/activate
cd web_server
export PYTHONPATH=/opt/web-crawler
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
echo $! > app.pid
echo "服务已启动，PID: $(cat app.pid)"
EOF

chmod +x start.sh
./start.sh
```

#### 4. 配置 systemd 服务（可选，推荐）

```bash
sudo tee /etc/systemd/system/web-crawler.service << 'EOF'
[Unit]
Description=Web Crawler Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/web-crawler/web_server
Environment=PYTHONPATH=/opt/web-crawler
ExecStart=/opt/web-crawler/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable web-crawler
sudo systemctl start web-crawler

# 查看状态
sudo systemctl status web-crawler
```

---

### 方法三：使用 Nginx 反向代理（生产环境推荐）

#### 1. 安装 Nginx

```bash
sudo apt install -y nginx
```

#### 2. 配置 Nginx

```bash
# 复制配置文件
sudo cp nginx.conf /etc/nginx/sites-available/web-crawler

# 启用配置
sudo ln -s /etc/nginx/sites-available/web-crawler /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # 删除默认配置

# 测试并重载
sudo nginx -t
sudo systemctl reload nginx
```

#### 3. 配置防火墙

```bash
# 开放 80 端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp  # 如果需要 HTTPS
sudo ufw reload
```

---

## 🔒 安全配置（生产环境必需）

### 1. 配置 HTTPS（使用 Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 2. 配置防火墙

```bash
# 只开放必要的端口
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 3. 配置访问控制（可选）

在 `web_server/main.py` 中添加基础认证：

```python
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

@app.get("/")
async def root(credentials: HTTPBasicCredentials = Depends(security)):
    # 验证用户名密码
    if credentials.username != "admin" or credentials.password != "your-password":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return FileResponse(str(BASE_DIR / "templates" / "index.html"))
```

---

## 📊 运维管理

### 查看日志

```bash
# Docker 方式
docker-compose logs -f

# Systemd 方式
sudo journalctl -u web-crawler -f

# 手动方式
tail -f /opt/web-crawler/web_server/app.log
```

### 备份数据

```bash
# 备份上传的 URL 和输出文件
tar czvf backup-$(date +%Y%m%d).tar.gz /opt/web-crawler/data/

# 自动备份脚本（添加到 crontab）
echo "0 2 * * * tar czvf /backup/web-crawler-$(date +\%Y\%m\%d).tar.gz /opt/web-crawler/data/" | sudo crontab -
```

### 更新部署

```bash
# Docker 方式
docker-compose down
docker-compose up -d --build

# Systemd 方式
cd /opt/web-crawler
git pull  # 如果使用 git
sudo systemctl restart web-crawler
```

---

## 🐛 故障排查

### 服务无法启动

```bash
# 检查端口占用
sudo lsof -i :8000

# 检查日志
docker-compose logs

# 检查依赖
pip list | grep -E "fastapi|uvicorn"
```

### 无法访问

```bash
# 检查服务状态
curl http://localhost:8000/api/health

# 检查防火墙
sudo ufw status

# 检查安全组（腾讯云控制台）
```

### 爬虫失败

```bash
# 检查网址文件是否存在
cat /opt/web-crawler/web_server/uploads/urls.csv

# 手动测试爬虫
cd /opt/web-crawler/web_server
python3 -c "from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3; print('导入成功')"
```

---

## 📝 腾讯云特定配置

### 1. 安全组配置

在腾讯云控制台 > 云服务器 > 安全组中，添加规则：

| 方向 | 协议 | 端口 | 源IP | 策略 |
|------|------|------|------|------|
| 入站 | TCP | 22 | 0.0.0.0/0 | 允许 |
| 入站 | TCP | 80 | 0.0.0.0/0 | 允许 |
| 入站 | TCP | 443 | 0.0.0.0/0 | 允许 |
| 入站 | TCP | 8000 | 0.0.0.0/0 | 允许（如果使用直接访问）|

### 2. 轻量应用服务器

如果使用腾讯云轻量应用服务器，注意：
- 防火墙规则在控制台单独配置
- 默认可能没有 ufw，使用腾讯云提供的防火墙

### 3. 使用腾讯云镜像加速

```bash
# 配置 Docker 使用腾讯云镜像
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com"
  ]
}
EOF
sudo systemctl restart docker
```

---

## 🔧 功能说明

### Web 界面功能

1. **控制台**：查看统计信息、最近任务、快速操作
2. **网址管理**：添加/删除/导入网址，支持 CSV/Excel 批量导入
3. **爬取任务**：配置爬虫参数，启动任务，实时查看进度
4. **报告查看**：查看/下载 HTML、Word、JSON 报告
5. **文档下载**：管理下载的文档文件

### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/urls` | GET/POST | URL 列表/添加 |
| `/api/urls/upload` | POST | 批量导入 URL |
| `/api/crawl/start` | POST | 启动爬虫任务 |
| `/api/crawl/status/{id}` | GET | 获取任务状态 |
| `/api/reports` | GET | 获取报告列表 |
| `/api/documents` | GET | 获取文档列表 |

---

## 💡 注意事项

1. **存储空间**：定期清理旧报告和文档，避免磁盘占满
2. **内存使用**：爬虫任务可能占用较多内存，建议服务器内存 >= 2GB
3. **并发控制**：根据需要调整 `max_retries` 和并发数
4. **合法合规**：确保爬虫行为符合目标网站的 robots.txt 和使用条款

---

如有问题，请检查日志或联系开发团队。
