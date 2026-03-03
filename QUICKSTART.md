# TalentIntel - 快速启动指南

## 🚀 5分钟快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/cooga/TalentIntel.git
cd TalentIntel
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置代理（必需）
```bash
cp config/proxies.example.yaml config/proxies.yaml
# 编辑 config/proxies.yaml 填入你的代理
```

### 4. 运行全自动发现
```bash
python3 scripts/auto_discovery.py
```

## 📊 工作流程

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Proxy Pool     │────▶│  Google X-Ray    │────▶│  LinkedIn       │
│  (代理轮换)      │     │  (搜索档案)       │     │  (评估匹配度)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                        │                       │
         ▼                        ▼                       ▼
   健康检查/失败恢复          验证码检测/自动重试        行为模拟/智能评估
```

## 🎯 三种使用方式

### 方式1: 全自动（推荐）
```bash
# 全自动运行，配置代理后即可使用
python3 scripts/auto_discovery.py
```

**特点:**
- ✅ 全自动运行
- ✅ 代理自动轮换
- ✅ 反爬虫自动处理
- ✅ 结果自动保存

**需要:** 代理池（付费代理推荐）

### 方式2: 半自动（平衡）
```bash
# 1. 生成搜索链接
python3 scripts/xray_campaign.py

# 2. 手动在浏览器中打开 data/xray_campaigns/xray_links_*.html
# 3. 使用 Linkclump 插件批量复制 LinkedIn 链接
# 4. 保存到文件后批量评估
python3 scripts/batch_evaluate.py data/my_links.txt
```

**特点:**
- ✅ 无需代理（Google部分手动）
- ✅ LinkedIn部分自动化
- ⚠️ 需要人工干预

### 方式3: 手动（最安全）
```bash
# 1. 生成搜索链接
python3 scripts/xray_campaign.py

# 2. 手动浏览 Google 搜索结果
# 3. 手动复制 LinkedIn 链接
# 4. 逐个运行评估
python3 -m src.main
```

**特点:**
- ✅ 零反爬风险
- ✅ 完全可控
- ⚠️ 效率最低

## ⚙️ 反爬虫策略对比

| 策略 | 全自动 | 半自动 | 手动 |
|------|--------|--------|------|
| Google 搜索 | 代理池轮换 | 浏览器手动 | 浏览器手动 |
| LinkedIn 访问 | 行为模拟 | 自动化 | 手动 |
| 验证码处理 | 自动切换代理 | 人工处理 | 无风险 |
| 封号风险 | 中（需好代理）| 低 | 极低 |
| 效率 | 高 | 中 | 低 |

## 📈 预期效果

**每批次运行:**
- 搜索发现: 150-200个档案
- 高匹配人才: 8-18人（>0.7分）
- 中匹配人才: 23-36人（0.5-0.7分）
- 运行时间: 1-3小时

## 🛡️ 安全建议

### 代理选择
```
推荐: 住宅代理（Residential Proxy）
- Bright Data
- Oxylabs
- Smartproxy

预算有限: 数据中心代理
- 需要更多数量轮换
- 失败率较高
```

### 频率控制
```python
# 保守设置（安全）
search_pages=3      # 搜索3页
max_profiles=10     # 评估10人
proxy_count=10      # 10个代理

# 激进设置（高效但风险高）
search_pages=10     # 搜索10页
max_profiles=50     # 评估50人
proxy_count=50      # 50个代理
```

## 🔧 常见问题

### Q: 为什么需要代理？
**A:** Google 和 LinkedIn 都有反爬机制，频繁请求会导致：
- IP 被封
- 验证码挑战
- 账号限制

代理池可以分散请求，降低风险。

### Q: 免费代理可以用吗？
**A:** 可以但不推荐：
- 稳定性差
- 容易被识别
- 速度慢

建议至少使用付费数据中心代理，最好是住宅代理。

### Q: 运行一次需要多久？
**A:** 取决于配置：
- 小规模（5档案）: 5-10分钟
- 中规模（20档案）: 30-60分钟
- 大规模（50档案）: 2-4小时

### Q: 如何查看结果？
**A:** 结果自动保存到：
```
data/auto_discovery/results_YYYYMMDD_HHMMSS.json
```

包含完整的人才档案和匹配分数。

## 📚 文档索引

| 文档 | 内容 |
|------|------|
| [README.md](../README.md) | 项目概述和架构 |
| [AUTO_DISCOVERY.md](./AUTO_DISCOVERY.md) | 全自动系统详解 |
| [XRAY_GUIDE.md](./XRAY_GUIDE.md) | X-Ray搜索指南 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 技术架构文档 |
| [TEST_SUMMARY.md](../TEST_SUMMARY.md) | 测试记录 |

## 🎉 开始使用

选择适合你的方式，立即开始发现人才：

```bash
# 全自动（需代理）
python3 scripts/auto_discovery.py

# 或半自动（推荐起步）
python3 scripts/xray_campaign.py
# 然后手动打开生成的HTML报告
```

---

**GitHub:** https://github.com/cooga/TalentIntel

**最后更新:** 2026-03-03
