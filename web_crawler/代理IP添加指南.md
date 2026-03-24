# 代理IP添加指南

## 一、代理IP的作用

使用代理IP可以：
- 突破网站的IP封锁（解决403错误）
- 隐藏真实IP地址
- 提高爬虫成功率
- 分布式爬取提高效率

---

## 二、添加代理IP的三种方式

### 方式1：直接编辑代理文件（推荐）

#### 步骤：

1. **创建或编辑 `proxies.json` 文件**

```bash
# 在项目目录下创建文件
notepad proxies.json
```

2. **添加代理信息**

```json
[
  {
    "host": "127.0.0.1",
    "port": 7890,
    "protocol": "http",
    "username": null,
    "password": null,
    "name": "Clash本地代理",
    "is_working": true
  },
  {
    "host": "123.45.67.89",
    "port": 8080,
    "protocol": "http",
    "username": "myuser",
    "password": "mypass",
    "name": "付费代理1",
    "is_working": true
  },
  {
    "host": "proxy.example.com",
    "port": 1080,
    "protocol": "socks5",
    "username": "user",
    "password": "pass",
    "name": "SOCKS5代理",
    "is_working": true
  }
]
```

#### 字段说明：

| 字段 | 必填 | 说明 | 示例 |
|------|------|------|------|
| host | ✅ | 代理服务器IP或域名 | "192.168.1.1" |
| port | ✅ | 代理端口 | 8080 |
| protocol | ✅ | 协议类型 | "http"/"https"/"socks5" |
| username | ❌ | 用户名（认证用） | "user" |
| password | ❌ | 密码（认证用） | "pass" |
| name | ❌ | 代理名称（备注） | "北京代理" |
| is_working | ❌ | 是否可用 | true/false |

---

### 方式2：使用TXT文本文件（简单）

#### 步骤：

1. **创建 `proxies.txt` 文件**

```bash
notepad proxies.txt
```

2. **每行添加一个代理**

```
# HTTP代理（无认证）
http://192.168.1.1:8080

# HTTP代理（有认证）
http://user:pass@proxy.example.com:8080

# HTTPS代理
https://secure.proxy.com:8443

# SOCKS5代理
socks5://127.0.0.1:1080

# SOCKS5代理（有认证）
socks5://user:pass@socks.proxy.com:1080
```

3. **导入到程序**

**GUI方式：**
- 打开程序 → 设置标签页
- 勾选"使用代理IP"
- 点击"浏览..."选择 `proxies.txt`
- 点击"测试代理"验证

**代码方式：**
```python
from core.proxy_manager import ProxyManager

manager = ProxyManager("proxies.json")
manager.import_from_file("proxies.txt", format="txt")
print(f"成功导入 {len(manager.proxies)} 个代理")
```

---

### 方式3：使用GUI界面添加

#### 步骤：

1. **打开程序**
```bash
python app_gui.py
```

2. **切换到"设置"标签页**

3. **配置代理：**
   - 勾选 ✅ "使用代理IP"
   - 选择代理类型（自动轮换/HTTP/HTTPS/SOCKS5）
   - 指定代理文件路径（默认 `proxies.json`）

4. **添加单个代理：**
   - 点击"添加代理..."按钮
   - 填写代理信息：
     - 代理主机：IP地址或域名
     - 代理端口：端口号
     - 代理协议：http/https/socks5
     - 用户名：（可选）
     - 密码：（可选）
   - 点击"确定"

5. **测试代理：**
   - 点击"测试代理"按钮
   - 等待测试结果
   - 查看可用代理数量

6. **保存并开始使用**

---

## 三、代码方式添加代理

### 方法1：运行时添加

```python
from core.proxy_manager import ProxyManager, Proxy

# 创建代理管理器
manager = ProxyManager("proxies.json")

# 添加单个代理
proxy = Proxy(
    host="192.168.1.1",
    port=8080,
    protocol="http",
    username="user",      # 可选
    password="pass",      # 可选
    name="我的代理"       # 可选
)

manager.add_proxy(proxy)
print(f"代理添加成功: {proxy}")
```

### 方法2：批量添加

```python
from core.proxy_manager import ProxyManager

# 代理列表
proxy_list = [
    "http://192.168.1.1:8080",
    "http://user:pass@proxy1.com:8080",
    "https://proxy2.com:8443",
    "socks5://127.0.0.1:1080",
]

manager = ProxyManager("proxies.json")

for proxy_str in proxy_list:
    success = manager.add_proxy_from_string(proxy_str)
    if success:
        print(f"✓ 添加成功: {proxy_str}")
    else:
        print(f"✗ 添加失败或已存在: {proxy_str}")

print(f"\n当前共有 {len(manager.proxies)} 个代理")
```

### 方法3：爬虫运行时指定

```python
from enhanced_crawler_v3 import EnhancedCompetitionCrawlerV3

# 创建爬虫时使用代理
crawler = EnhancedCompetitionCrawlerV3(
    use_proxy=True,
    proxy_file="proxies.json"
)

# 或者命令行方式
# python enhanced_crawler_v3.py --urls urls.csv --proxy --proxy-file my_proxies.json
```

---

## 四、获取代理IP的渠道

### 4.1 付费代理（推荐 - 稳定可靠）

| 提供商 | 网址 | 特点 | 价格参考 |
|--------|------|------|----------|
| 站大爷 | www.zdaye.com | 高质量，低延迟 | ¥50-200/月 |
| 快代理 | www.kuaidaili.com | 种类多，API支持 | ¥30-150/月 |
| 芝麻代理 | www.zhimahttp.com | 动态IP，海量池 | 按量计费 |
| 阿布云 | www.abuyun.com | 隧道代理，稳定 | ¥100+/月 |
| 极光代理 | www.jiguangdaili.com | 速度快，覆盖广 | ¥40-180/月 |

**付费代理优点：**
- 稳定性高（99%+可用率）
- 速度快（<100ms延迟）
- 支持API自动提取
- 专属客服支持

### 4.2 免费代理（测试用）

| 网站 | 网址 | 稳定性 | 速度 |
|------|------|--------|------|
| 站大爷免费版 | www.zdaye.com/free | 低 | 慢 |
| 快代理免费版 | www.kuaidaili.com/free | 中 | 中 |
| 西刺代理 | www.xicidaili.com | 低 | 慢 |
| 免费代理IP库 | ip.jiangxianli.com | 中 | 中 |

**免费代理缺点：**
- 可用率低（30-60%）
- 速度慢（>500ms延迟）
- 有效期短（几分钟到几小时）
- 多人共用易被封锁

### 4.3 自建代理

#### 使用VPS搭建

```bash
# 购买VPS后（推荐：阿里云/腾讯云/AWS）
# 安装Shadowsocks或V2Ray

# Shadowsocks示例
pip install shadowsocks
ssserver -p 8388 -k password -m aes-256-cfb

# 然后在proxies.json中添加
# {
#   "host": "你的VPS_IP",
#   "port": 8388,
#   "protocol": "socks5",
#   "name": "自建代理"
# }
```

#### 使用云服务器弹性IP

```python
# 阿里云/腾讯云API管理弹性IP
# 实现IP自动轮换
# 需要编写额外脚本
```

---

## 五、代理配置示例

### 示例1：本地Clash/V2Ray代理

如果你使用Clash或V2Ray等工具：

```json
[
  {
    "host": "127.0.0.1",
    "port": 7890,
    "protocol": "http",
    "name": "Clash HTTP"
  },
  {
    "host": "127.0.0.1",
    "port": 7891,
    "protocol": "socks5",
    "name": "Clash SOCKS5"
  }
]
```

### 示例2：多个付费代理轮换

```json
[
  {
    "host": "proxy1.zdaye.com",
    "port": 8080,
    "protocol": "http",
    "username": "your_user",
    "password": "your_pass",
    "name": "站大爷-北京"
  },
  {
    "host": "proxy2.zdaye.com",
    "port": 8080,
    "protocol": "http",
    "username": "your_user",
    "password": "your_pass",
    "name": "站大爷-上海"
  },
  {
    "host": "proxy.kuaidaili.com",
    "port": 8080,
    "protocol": "http",
    "username": "your_user",
    "password": "your_pass",
    "name": "快代理"
  }
]
```

### 示例3：混合协议代理

```json
[
  {
    "host": "http-proxy.com",
    "port": 8080,
    "protocol": "http",
    "name": "HTTP代理"
  },
  {
    "host": "https-proxy.com",
    "port": 8443,
    "protocol": "https",
    "name": "HTTPS代理"
  },
  {
    "host": "socks-proxy.com",
    "port": 1080,
    "protocol": "socks5",
    "name": "SOCKS5代理"
  }
]
```

---

## 六、代理测试与验证

### 6.1 GUI测试

1. 打开程序 → 设置标签页
2. 配置代理文件
3. 点击"测试代理"按钮
4. 查看测试结果：
   - ✅ 可用代理数量
   - ⏱️ 平均延迟
   - 📊 成功率统计

### 6.2 命令行测试

```python
import asyncio
from core.proxy_manager import ProxyManager

async def test_proxies():
    manager = ProxyManager("proxies.json")
    
    print(f"共有 {len(manager.proxies)} 个代理")
    print("开始测试...\n")
    
    results = await manager.test_all_proxies()
    
    working = sum(1 for _, is_working, _ in results if is_working)
    print(f"\n测试结果: {working}/{len(results)} 个代理可用")
    
    # 打印详细信息
    for proxy, is_working, latency in results:
        status = "✓" if is_working else "✗"
        latency_str = f"{latency:.2f}s" if latency else "N/A"
        print(f"{status} {proxy.name or proxy.host}: {latency_str}")

# 运行测试
asyncio.run(test_proxies())
```

### 6.3 单个代理测试

```python
import asyncio
import aiohttp

async def test_single_proxy():
    proxy_url = "http://user:pass@proxy.example.com:8080"
    test_url = "http://httpbin.org/ip"
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(test_url, proxy=proxy_url, ssl=False) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✓ 代理工作正常")
                    print(f"  返回IP: {data.get('origin', 'unknown')}")
                else:
                    print(f"✗ HTTP错误: {resp.status}")
    except Exception as e:
        print(f"✗ 代理测试失败: {e}")

asyncio.run(test_single_proxy())
```

---

## 七、常见问题

### Q1: 如何知道代理是否工作？

**A:** 使用GUI的"测试代理"功能，或运行测试脚本。查看输出中的HTTP状态码：
- 200 = 成功
- 403 = 代理被拒绝
- 407 = 需要认证
- 超时 = 代理不可用

### Q2: 需要认证信息的代理怎么配置？

**A:** 在JSON中添加username和password字段：
```json
{
  "host": "proxy.example.com",
  "port": 8080,
  "protocol": "http",
  "username": "your_username",
  "password": "your_password"
}
```

### Q3: 免费代理为什么不稳定？

**A:** 免费代理的问题：
- 多人共用，负载高
- 有效期短，几分钟就失效
- 速度慢，延迟高
- 容易被目标网站封锁

**建议:** 重要任务使用付费代理

### Q4: 代理添加后爬虫还是不工作？

**A:** 检查以下几点：
1. 代理是否真的可用（用测试功能验证）
2. 代理协议是否正确（http/https/socks5）
3. 认证信息是否正确
4. 目标网站是否还有其他反爬机制
5. 查看爬虫日志中的代理连接信息

### Q5: 如何自动获取最新代理？

**A:** 付费代理通常提供API接口：

```python
import requests

# 示例：快代理API
api_url = "https://dps.kdlapi.com/api/getdps/"
params = {
    "orderid": "your_order_id",
    "num": 10,
    "format": "json"
}

response = requests.get(api_url, params=params)
proxies = response.json()

# 保存到文件
with open("proxies_auto.json", "w") as f:
    json.dump(proxies, f)
```

---

## 八、最佳实践

### 1. 代理数量
- 小规模爬取：3-5个代理
- 中等规模：10-20个代理
- 大规模：50+个代理

### 2. 代理质量
- 优先使用付费代理
- 定期测试代理可用性
- 及时移除失效代理

### 3. 轮换策略
- 程序会自动轮换代理
- 失败的代理会被标记
- 连续失败3次的代理会被禁用

### 4. 安全提示
- 不要在代码中硬编码代理密码
- 定期更换代理密码
- 使用环境变量存储敏感信息

---

## 九、快速开始

### 最快方式（5分钟）：

1. **购买付费代理**（推荐快代理/站大爷）
2. **获取代理信息**：IP、端口、用户名、密码
3. **创建 `proxies.json`**：
```json
[
  {
    "host": "你的代理IP",
    "port": 8080,
    "protocol": "http",
    "username": "你的用户名",
    "password": "你的密码"
  }
]
```
4. **运行爬虫**：
```bash
python enhanced_crawler_v3.py --urls urls.csv --proxy
```

完成！爬虫会自动使用代理访问目标网站。
