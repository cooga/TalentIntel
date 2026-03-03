# 代理与CAPTCHA配置指南

## 一、代理信息需求

### 1. 代理类型对比

| 类型 | 住宅代理 (Residential) | 数据中心代理 (Datacenter) |
|------|----------------------|-------------------------|
| **来源** | 真实家庭网络IP | 机房服务器IP |
| **匿名性** | ⭐⭐⭐⭐⭐ 极高 | ⭐⭐⭐ 中等 |
| **速度** | ⭐⭐⭐ 中等 (1-10 Mbps) | ⭐⭐⭐⭐⭐ 快 (10-100 Mbps) |
| **价格** | $5-15/GB | $1-3/GB |
| **Google识别率** | 极低 (<5%) | 中等 (20-40%) |
| **LinkedIn识别率** | 极低 (<3%) | 中等 (15-30%) |
| **推荐用途** | 大规模生产环境 | 测试/小规模 |

### 2. 推荐代理服务商

#### 🏆 第一梯队（高质量）

**Bright Data (原Luminati)**
- 网站: https://brightdata.com/
- 类型: 住宅代理
- 价格: $5.04/GB 起
- 特点: 
  - 7200万+住宅IP
  - 99.9%成功率
  - 全球195个国家
  - 支持ASN/城市级定位
- 配置示例:
```yaml
- host: "brd.superproxy.io"
  port: 22225
  username: "brd-customer-[CUSTOMER_ID]-zone-[ZONE]"
  password: "[PASSWORD]"
```

**Oxylabs**
- 网站: https://oxylabs.io/
- 类型: 住宅 + 数据中心
- 价格: $8/GB (住宅) / $0.8/IP (数据中心)
- 特点:
  - 1亿+住宅IP
  - 自动轮换
  - 99.95%成功率
- 配置示例:
```yaml
- host: "pr.oxylabs.io"
  port: 7777
  username: "customer-[USERNAME]"
  password: "[PASSWORD]"
```

**Smartproxy**
- 网站: https://smartproxy.com/
- 类型: 住宅代理
- 价格: $2.5/GB 起
- 特点:
  - 4000万+IP
  - 性价比高
  - 3天退款保证
- 配置示例:
```yaml
- host: "gate.smartproxy.com"
  port: 7000
  username: "user-[USERNAME]"
  password: "[PASSWORD]"
```

#### 🥈 第二梯队（性价比）

**IPRoyal**
- 网站: https://iproyal.com/
- 类型: 住宅 + ISP
- 价格: $1.75/GB
- 特点: 无过期流量，永久有效

**ProxyEmpire**
- 网站: https://proxyempire.io/
- 类型: 住宅 + 移动
- 价格: $2.97/GB
- 特点: 支持移动端代理

**PacketStream**
- 网站: https://packetstream.io/
- 类型: 住宅
- 价格: $1/GB
- 特点: 便宜但IP质量一般

### 3. 代理数量建议

| 规模 | Google页数 | 评估人数 | 代理数量 | 类型 |
|------|-----------|---------|---------|------|
| 测试 | 2-3页 | 5-10人 | 3-5个 | 数据中心 |
| 小型 | 5页 | 20人 | 5-10个 | 混合 |
| 中型 | 10页 | 50人 | 10-20个 | 住宅为主 |
| 大型 | 20页 | 100人+ | 20-50个 | 住宅 |

### 4. 完整代理配置示例

创建 `config/proxies.yaml`:

```yaml
proxies:
  # === 住宅代理 (推荐主力) ===
  - host: "brd.superproxy.io"
    port: 22225
    username: "brd-customer-XXX-zone-residential"
    password: "your_password_here"
    
  - host: "brd.superproxy.io" 
    port: 22225
    username: "brd-customer-XXX-zone-residential2"
    password: "your_password_here"
    
  - host: "pr.oxylabs.io"
    port: 7777
    username: "customer-username"
    password: "your_password_here"
    
  - host: "gate.smartproxy.com"
    port: 7000
    username: "user-username"
    password: "your_password_here"
    
  - host: "gate.smartproxy.com"
    port: 7001
    username: "user-username"
    password: "your_password_here"

  # === 数据中心代理 (备选) ===
  - host: "dc.oxylabs.io"
    port: 8000
    username: "customer-username"
    password: "your_password_here"
    
  - host: "proxy.packetstream.io"
    port: 31112
    username: "username"
    password: "your_password_here"
    
  - host: "us.proxy.iproyal.com"
    port: 12323
    username: "username"
    password: "your_password_here"
    
  - host: "gate.visitormetric.io"
    port: 8000
    username: "username"
    password: "your_password_here"
    
  - host: "proxy.peet.ws"
    port: 8080
    username: null
    password: null
```

### 5. 代理配置加载脚本

```python
# 添加到你的代码中
import yaml

def load_proxies_from_config(discovery):
    """从YAML加载代理配置"""
    with open("config/proxies.yaml", 'r') as f:
        config = yaml.safe_load(f)
        
    for p in config["proxies"]:
        discovery.add_proxy(
            host=p["host"],
            port=p["port"],
            username=p.get("username"),
            password=p.get("password")
        )
    
    print(f"✅ 已加载 {len(config['proxies'])} 个代理")
```

---

## 二、CAPTCHA解决服务

### 1. 当前验证码检测

系统已内置验证码检测，触发时会：
- 🔴 立即控制台警报
- 🔄 自动切换代理重试
- ⏸️ 连续3次触发时建议暂停

但**无法自动解决验证码**，需要人工介入或使用第三方服务。

### 2. 推荐CAPTCHA解决服务

#### reCAPTCHA v2/v3 解决

**2Captcha** (最流行)
- 网站: https://2captcha.com/
- 价格: 
  - reCAPTCHA v2: $2.99/1000次
  - reCAPTCHA v3: $2.99/1000次
  - hCaptcha: $3.99/1000次
- API示例:
```python
import requests

def solve_recaptcha(site_key, page_url, api_key):
    """使用2Captcha解决reCAPTCHA"""
    # 提交任务
    submit_url = "http://2captcha.com/in.php"
    data = {
        "key": api_key,
        "method": "userrecaptcha",
        "googlekey": site_key,
        "pageurl": page_url,
        "json": 1
    }
    
    response = requests.post(submit_url, data=data).json()
    captcha_id = response.get("request")
    
    # 等待结果
    result_url = f"http://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}&json=1"
    
    for _ in range(30):  # 最多等150秒
        time.sleep(5)
        result = requests.get(result_url).json()
        if result.get("status") == 1:
            return result.get("request")  # 返回token
    
    return None
```

**Anti-Captcha**
- 网站: https://anti-captcha.com/
- 价格: $2/1000次
- 特点: 速度更快，成功率更高

**CapSolver** (新兴)
- 网站: https://www.capsolver.com/
- 价格: $0.8/1000次
- 特点: 价格便宜，支持AI识别

### 3. 集成CAPTCHA解决到系统

```python
# 增强版浏览器类 - 添加CAPTCHA自动解决
class AntiDetectBrowserWithCaptchaSolver(AntiDetectBrowser):
    """带CAPTCHA解决的浏览器"""
    
    def __init__(self, proxy_pool, notifier, captcha_api_key=None):
        super().__init__(proxy_pool, notifier)
        self.captcha_api_key = captcha_api_key
        self.captcha_solver = captcha_api_key
        
    async def solve_captcha_if_present(self, html: str, url: str) -> Optional[str]:
        """检测并解决CAPTCHA"""
        if not self.is_captcha(html):
            return None
            
        if not self.captcha_api_key:
            print("⚠️  未配置CAPTCHA解决服务，跳过")
            return None
        
        # 提取site_key (reCAPTCHA)
        site_key_match = re.search(r'data-sitekey="([^"]+)"', html)
        if site_key_match:
            site_key = site_key_match.group(1)
            print(f"🔍 发现reCAPTCHA，开始解决...")
            
            # 调用2Captcha
            token = await self._call_2captcha(site_key, url)
            return token
        
        return None
    
    async def _call_2captcha(self, site_key: str, page_url: str) -> Optional[str]:
        """调用2Captcha API"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # 提交任务
            async with session.post(
                "http://2captcha.com/in.php",
                data={
                    "key": self.captcha_api_key,
                    "method": "userrecaptcha",
                    "googlekey": site_key,
                    "pageurl": page_url,
                    "json": 1
                }
            ) as resp:
                data = await resp.json()
                captcha_id = data.get("request")
            
            # 轮询结果
            for i in range(30):
                await asyncio.sleep(5)
                
                async with session.get(
                    f"http://2captcha.com/res.php?key={self.captcha_api_key}&action=get&id={captcha_id}&json=1"
                ) as resp:
                    result = await resp.json()
                    if result.get("status") == 1:
                        print(f"✅ CAPTCHA解决成功")
                        return result.get("request")
                    elif result.get("request") == "CAPCHA_NOT_READY":
                        print(f"⏳ CAPTCHA解决中... ({i+1}/30)")
                    else:
                        print(f"❌ CAPTCHA解决失败: {result}")
                        return None
        
        return None
```

### 4. 验证码警报配置

当前警报输出示例:
```
🚨 【验证码警报 #1】 23:45:12
======================================================================
⚠️  检测到验证码/反爬验证！

📍 位置: https://www.google.com/search?q=...
🔌 代理: 47.74.152.29:8888

💡 建议操作:
1. 检查代理池状态
2. 增加延时时间
3. 更换更高质量代理
4. 暂停运行，稍后重试

⏳ 系统将自动切换代理并重试...
======================================================================
```

**如果要发送到手机/Discord**:
```python
async def notify_discord(message: str):
    """发送Discord通知"""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if webhook_url:
        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json={"content": message})
```

---

## 三、配置清单

### 环境变量设置

```bash
# 必需
export KIMI_API_KEY="your_kimi_api_key_here"

# 代理认证 (如果使用)
export PROXY_USERNAME="your_proxy_username"
export PROXY_PASSWORD="your_proxy_password"

# CAPTCHA解决 (可选)
export CAPTCHA_2C_API_KEY="your_2captcha_key"

# 通知 (可选)
export DISCORD_WEBHOOK_URL="your_discord_webhook"
```

### 文件配置

1. **config/proxies.yaml** - 代理列表
2. **config/captcha.yaml** - CAPTCHA服务配置
3. **.env** - 环境变量 (添加到.gitignore)

### 预算估算

| 规模 | 每月搜索 | 代理费用 | CAPTCHA费用 | 总计 |
|------|---------|---------|------------|------|
| 测试 | 100人 | $10 (5代理) | $5 | $15 |
| 小型 | 500人 | $30 (10代理) | $20 | $50 |
| 中型 | 2000人 | $80 (20代理) | $80 | $160 |
| 大型 | 10000人 | $200 (50代理) | $400 | $600 |

---

## 四、快速开始

1. **注册代理服务** (推荐Bright Data)
2. **复制配置模板**:
   ```bash
   cp config/proxies_10.yaml config/proxies.yaml
   vim config/proxies.yaml  # 填入真实代理
   ```
3. **设置环境变量**:
   ```bash
   export KIMI_API_KEY="your_key"
   ```
4. **运行**:
   ```bash
   python3 scripts/auto_discovery_enhanced.py
   ```

需要我帮你配置具体的代理服务商或CAPTCHA服务吗？
