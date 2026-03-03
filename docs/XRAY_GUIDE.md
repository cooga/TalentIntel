# Google X-Ray Search 快速上手指南

## 🎯 方案概述

**问题**: LinkedIn 直接搜索候选池太小、反爬严格

**解决方案**: Google X-Ray Search + 浏览器批量提取 + 自动化评估

**优势**:
- ✅ 合法合规（Google 公开搜索）
- ✅ 发现量大（50-100人/批次）
- ✅ 无反爬风险（人工浏览 + 插件提取）
- ✅ 自动化评估（TalentIntel 数字研究员）

---

## 📋 三步走流程

### 第一步：生成搜索链接

```bash
cd Project/TalentIntel
python3 scripts/xray_campaign.py
```

**输出**:
- `data/xray_campaigns/xray_links_YYYYMMDD.html` - HTML报告（含可点击链接）
- `data/xray_campaigns/campaign_*.json` - 搜索配置

### 第二步：浏览器批量提取

1. **打开 HTML 报告**
   ```bash
   open data/xray_campaigns/xray_links_20260303.html
   ```

2. **安装浏览器插件**
   - Chrome: [Linkclump](https://chrome.google.com/webstore/detail/linkclump/gpmkpgdbdhciadajoafejkkbpbcfjmfg)
   - Firefox: [Multi-Link Paste](https://addons.mozilla.org/en-US/firefox/addon/multilinkpaste/)

3. **批量提取链接**
   - 点击搜索链接，打开 Google 结果页
   - 使用 Linkclump 框选所有 LinkedIn 链接
   - 复制到剪贴板

4. **保存链接列表**
   ```bash
   # 粘贴到文本文件
   vim data/linkedin_links.txt
   # 每行一个链接
   ```

### 第三步：自动化批量评估

```bash
python3 scripts/batch_evaluate.py data/linkedin_links.txt --max-profiles 20
```

**输出**:
- `data/batch_evaluations/batch_results_*.json` - 所有评估结果
- `data/batch_evaluations/high_matches_*.json` - 高匹配人才（≥0.7）
- `data/batch_evaluations/batch_report_*.md` - Markdown报告

---

## 🔍 搜索策略说明

| 策略 | 目标人群 | 预期发现量 |
|------|----------|-----------|
| 北美大厂 AI+无线 | Qualcomm/NVIDIA/Intel/Samsung/Apple/Meta | 30-50人 |
| 华系通信算法 | 华为/中兴/海思/OPPO/vivo/小米 | 20-40人 |
| 欧洲无线研究 | Ericsson/Nokia/Bell Labs/InterDigital | 15-30人 |
| 亚太无线AI | MediaTek/Samsung/Sony/NEC/NTT | 10-20人 |

**总计**: 每批次可发现 **75-140** 个潜在候选人

---

## ⚙️ 高级配置

### 修改搜索策略

编辑 `scripts/xray_campaign.py`，修改 `STRATEGIES` 字典：

```python
STRATEGIES = {
    "my_custom_search": {
        "name": "我的定制搜索",
        "companies": ["目标公司1", "目标公司2"],
        "titles": ["职位关键词1", "职位关键词2"],
        "skills": ["技能关键词1", "技能关键词2"],
        "locations": ["目标地区1", "目标地区2"],
        "exclude": ["排除关键词1", "排除关键词2"],
    },
}
```

### 调整评估参数

```bash
python3 scripts/batch_evaluate.py links.txt \
    --min-score 0.6 \      # 提高最低匹配分数
    --max-profiles 30      # 评估更多人
```

---

## 🛡️ 合规与风险控制

### Google 搜索限制
- **请求频率**: 每页间 10-15 秒延时（已内置）
- **每日上限**: 建议不超过 100 个档案
- **IP 轮换**: 如需大规模抓取，建议使用代理

### LinkedIn 访问限制
- **档案间延时**: 30-60 秒（已内置）
- **每日上限**: 建议不超过 20-30 个档案评估
- **人类行为**: 浏览器可见模式，模拟阅读停顿

---

## 📊 输出示例

### 高匹配人才报告

```markdown
# 批量人才评估报告

## 🏆 高匹配人才 (≥0.7)

### 1. Khuong N.
- **匹配分数**: 0.92
- **职位**: Staff Research Engineer II
- **公司**: Samsung Research America
- **地点**: Plano, Texas
- **档案**: https://www.linkedin.com/in/nguyen-404b2570/

**AI能力**: expert
**Wireless能力**: expert

**匹配理由**:
- Perfect AI + Wireless Communication intersection
- PhD in CS from top US university (Texas A&M)
- 8 years at Samsung Research America
- Active research output: papers and patents

💡 建议: Immediate outreach - exceptional match
```

---

## 🔧 故障排除

### 问题1: Google 搜索结果为空
- 检查搜索查询语法是否正确
- 尝试减少关键词数量
- 更换不同的搜索策略

### 问题2: LinkedIn 登录失败
- 检查环境变量 `LINKEDIN_PASSWORD`
- 确认小号未被限制
- 尝试手动登录一次

### 问题3: 评估分数偏低
- 调整 `config/targets.yaml` 中的关键词
- 降低 `min_match_score` 阈值
- 检查 LLM 配置是否正确

---

## 🚀 下一步优化

- [ ] 集成代理池支持
- [ ] 添加 GitHub 代码能力验证
- [ ] 添加 Google Scholar 学术影响力验证
- [ ] 建立人才长期跟踪机制
- [ ] 开发 Chrome 插件自动提取

---

## 📚 相关文件

| 文件 | 说明 |
|------|------|
| `scripts/xray_campaign.py` | 生成搜索链接 |
| `scripts/batch_evaluate.py` | 批量评估人才 |
| `scripts/xray_scraper.py` | 自动化抓取（实验性）|
| `config/targets.yaml` | 人才画像配置 |
| `docs/XRAY_GUIDE.md` | 本指南 |
