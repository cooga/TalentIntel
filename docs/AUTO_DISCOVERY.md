# 全自动人才发现系统使用指南

## 🚀 系统概述

`auto_discovery.py` 是一个全自动化的 X-Ray 人才发现系统，整合了：
- **代理池管理** - 自动轮换、健康检查、失败恢复
- **Google X-Ray 搜索** - 自动搜索 LinkedIn 档案
- **LinkedIn 评估** - 智能人才匹配（需配合 LLM）
- **反爬虫对策** - 浏览器指纹伪装、随机延时、验证码检测

## 📋 前置要求

### 1. 安装依赖
```bash
pip install aiohttp pyyaml
```

### 2. 配置代理（必需）

**为什么需要代理？**
- Google 对频繁请求会返回验证码（429）
- LinkedIn 会封禁异常 IP
- 代理池可实现请求分散，降低被封风险

**获取代理：**

**付费代理（推荐）:**
- [Bright Data](https://brightdata.com/) - 住宅代理，质量最高
- [Oxylabs](https://oxylabs.io/) - 数据中心代理，速度快
- [Smartproxy](https://smartproxy.com/) - 性价比高

**免费代理（不稳定）:**
- https://www.proxy-list.download/
- https://free-proxy-list.net/

**配置方式:**

```bash
# 复制模板
cp config/proxies.example.yaml config/proxies.yaml

# 编辑配置文件
vim config/proxies.yaml
```

示例配置:
```yaml
proxies:
  - host: "your-proxy.com"
    port: 8080
    username: "your_username"
    password: "your_password"
    
  - host: "backup-proxy.com"
    port: 8080
    username: "your_username"
    password: "your_password"
```

### 3. 配置 LLM API（可选）

如需完整的人才评估功能，需要配置 LLM API Key：

```bash
export KIMI_API_KEY="your_kimi_api_key"
# 或
export OPENAI_API_KEY="your_openai_api_key"
```

## 🎯 使用方法

### 基础用法

```bash
cd Project/TalentIntel
python3 scripts/auto_discovery.py
```

### 自定义搜索策略

编辑 `scripts/auto_discovery.py` 中的 `main()` 函数：

```python
results = await discovery.discover(
    companies=["Qualcomm", "NVIDIA", "Intel", "Samsung"],
    titles=["AI Engineer", "Wireless Engineer", "Research Scientist"],
    skills=["5G", "Deep Learning", "MIMO", "AI"],
    locations=["United States", "Canada", "Singapore"],
    search_pages=3,      # Google 搜索页数
    max_profiles=20,     # 评估档案数上限
)
```

### 命令行参数（高级）

创建自定义脚本调用：

```python
import asyncio
from scripts.auto_discovery import AutoTalentDiscovery

async def custom_search():
    discovery = AutoTalentDiscovery()
    
    # 加载代理配置
    with open("config/proxies.yaml") as f:
        config = yaml.safe_load(f)
        for p in config["proxies"]:
            discovery.add_proxy(
                p["host"], 
                p["port"], 
                p.get("username"), 
                p.get("password")
            )
    
    await discovery.initialize()
    
    # 华系人才搜索
    results = await discovery.discover(
        companies=["Huawei", "ZTE", "HiSilicon", "OPPO", "vivo"],
        titles=["算法工程师", "通信算法", "AI Engineer"],
        skills=["5G", "MIMO", "OFDM", "深度学习"],
        locations=["China", "Singapore"],
        search_pages=5,
        max_profiles=30,
    )
    
    return results

if __name__ == "__main__":
    asyncio.run(custom_search())
```

## ⚙️ 反爬虫策略详解

### 1. 代理池管理

```python
- 健康检查: 启动时验证所有代理
- 自动轮换: 每次请求切换代理
- 失败降级: 连续失败3次自动剔除
- 自动恢复: 30分钟后尝试重新启用
```

### 2. 请求频率控制

```python
Google搜索:
  - 页面间延时: 5-10秒
  
LinkedIn访问:
  - 档案间延时: 30-60秒
  - 每日上限: 建议20个档案
```

### 3. 浏览器指纹伪装

```python
- User-Agent轮换: Chrome/Firefox/Safari
- Accept-Language: 多语言混合
- Referer: 模拟真实来源
- 请求头: 完整的浏览器特征
```

### 4. 验证码检测

```python
自动检测:
  - "captcha" 关键词
  - "429 Too Many Requests"
  - "unusual traffic"
  
应对策略:
  - 立即切换代理
  - 记录失败次数
  - 长延时后重试
```

## 📊 输出结果

### 结果文件
```
data/auto_discovery/
├── results_20260303_143022.json    # 完整结果
└── ...
```

### 结果格式
```json
{
  "discovered_at": "2026-03-03T14:30:22",
  "total_discovered": 15,
  "browser_stats": {
    "requests": 25,
    "success": 20,
    "captcha_hits": 3,
    "blocks": 2
  },
  "profiles": [
    {
      "url": "https://www.linkedin.com/in/example/",
      "name": "John Doe",
      "match_score": 0.85,
      "priority": "HIGH",
      "evaluated_at": "2026-03-03T14:32:15"
    }
  ]
}
```

## ⚠️ 风险提示

### 1. Google 限制
- 免费代理容易被识别
- 建议使用住宅代理
- 控制请求频率（每IP每日<100次）

### 2. LinkedIn 限制
- 新账号容易被限制
- 建议使用老账号
- 严格限制访问频率

### 3. 法律合规
- 仅获取公开信息
- 不用于垃圾营销
- 遵守平台 ToS

## 🔧 故障排除

### 问题1: 所有代理都失败
```
症状: "无可用代理" 或全部超时
解决: 
  1. 检查代理配置
  2. 验证代理可用性
  3. 更换高质量代理
```

### 问题2: 频繁遇到验证码
```
症状: "遇到验证码，切换代理"
解决:
  1. 增加代理数量
  2. 使用住宅代理
  3. 增大延时时间
```

### 问题3: LinkedIn 登录失败
```
症状: 无法获取档案内容
解决:
  1. 使用已登录的session
  2. 检查账号状态
  3. 使用浏览器插件辅助
```

## 📈 性能优化

### 并发控制
```python
# 默认配置已优化，如需调整：
semaphore = asyncio.Semaphore(3)  # 限制并发数
```

### 代理质量
```
推荐配置:
- 住宅代理: 10-20个
- 数据中心代理: 20-50个
- 轮换间隔: 每请求切换
```

### 延时策略
```python
# 保守配置（安全但慢）
await browser.random_delay(10, 20)  # 10-20秒

# 激进配置（快但风险高）  
await browser.random_delay(3, 5)    # 3-5秒
```

## 🎯 实战建议

### 小规模测试（推荐起步）
```python
search_pages=2      # 搜索2页
max_profiles=5      # 评估5人
```

### 中等规模
```python
search_pages=5      # 搜索5页
max_profiles=20     # 评估20人
proxies=10          # 10个代理
```

### 大规模（需专业代理）
```python
search_pages=10     # 搜索10页
max_profiles=50     # 评估50人
proxies=50+         # 50+个代理
```

## 📚 相关文档

- [XRAY_GUIDE.md](./XRAY_GUIDE.md) - X-Ray搜索基础指南
- [README.md](../README.md) - 项目主文档
- [ARCHITECTURE.md](../ARCHITECTURE.md) - 系统架构详解

---

*最后更新: 2026-03-03*
*作者: Kobe*
