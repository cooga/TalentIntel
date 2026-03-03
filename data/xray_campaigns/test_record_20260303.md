# X-Ray Search 测试记录 - 2026-03-03

## 测试目标
验证 Google X-Ray Search 流程的可行性，生成可点击的搜索链接

## 测试时间
2026-03-03 22:55:15 (Asia/Hong_Kong)

## 生成配置

### 4个搜索策略

| 策略ID | 名称 | 目标公司 | 预期发现量 |
|--------|------|----------|-----------|
| na_ai_wireless | 北美 AI+无线工程师 | Qualcomm, NVIDIA, Intel, Samsung, Apple, Meta | 30-50人 |
| china_wireless | 华系通信算法专家 | Huawei, ZTE, HiSilicon, OPPO, vivo, Xiaomi | 20-40人 |
| eu_research | 欧洲无线研究机构 | Ericsson, Nokia, Bell Labs, InterDigital, Keysight | 15-30人 |
| apac_talent | 亚太无线AI人才 | MediaTek, Samsung, Sony, NEC, NTT | 10-20人 |

### 生成的搜索链接
总计 **20个** 分页链接（每策略5页，每页10个结果）

**策略1: 北美 AI+无线工程师**
- 第1页: https://www.google.com/search?q=site%3Alinkedin.com%2Fin+... (1-10)
- 第2页: https://www.google.com/search?q=site%3Alinkedin.com%2Fin+... (11-20)
- 第3页: https://www.google.com/search?q=site%3Alinkedin.com%2Fin+... (21-30)
- 第4页: https://www.google.com/search?q=site%3Alinkedin.com%2Fin+... (31-40)
- 第5页: https://www.google.com/search?q=site%3Alinkedin.com%2Fin+... (41-50)

**搜索语法示例:**
```
site:linkedin.com/in 
("Qualcomm" OR "NVIDIA" OR "Intel" OR "Samsung" OR "Apple" OR "Meta") 
("AI Engineer" OR "Wireless Engineer" OR "Research Scientist" OR "ML Engineer") 
("5G" OR "Deep Learning" OR "MIMO" OR "Wireless Communication") 
("United States" OR "Canada") 
-"recruiter" -"HR" -"sales"
```

## 输出文件

| 文件 | 路径 | 说明 |
|------|------|------|
| HTML报告 | `data/xray_campaigns/xray_links_20260303.html` | 可视化搜索链接页面 |
| JSON配置 | `data/xray_campaigns/campaign_20260303_225515.json` | 搜索策略结构化数据 |
| 测试链接 | `data/test_links.txt` | 5个示例LinkedIn档案链接 |
| 测试记录 | `data/xray_campaigns/test_record_20260303.md` | 本文件 |

## 批量评估测试

### 测试结果
- **测试时间**: 2026-03-03 22:58
- **测试链接数**: 5个
- **评估配置**: max_profiles=2
- **结果**: ⚠️ 浏览器超时（需要图形界面或有头模式）

### 问题诊断
浏览器在访问 LinkedIn 时出现超时，可能原因：
1. 无头模式（headless）下 LinkedIn 页面加载异常
2. 需要图形界面支持
3. 网络延迟或防火墙限制

### 解决方案
**方案1: 本地手动运行**
```bash
# 在有图形界面的机器上运行
python3 scripts/batch_evaluate.py data/test_links.txt --max-profiles 5
```

**方案2: 使用已验证的单独评估脚本**
```bash
# 使用之前验证过的 main.py
python3 -m src.main
```

## 下一步测试计划

### Phase 1: 手动验证（待执行）
1. 打开 HTML 报告
2. 点击搜索链接，验证 Google 返回结果
3. 使用 Linkclump 批量提取 LinkedIn 链接
4. 记录实际获取的档案数量

### Phase 2: 批量评估（待执行）
1. 将提取的链接保存到 `data/test_links.txt`
2. 在本地机器上运行批量评估
3. 记录评估结果和高匹配人才

### Phase 3: 自动化抓取（可选）
1. 配置代理池
2. 运行 `python3 scripts/xray_scraper.py`
3. 验证抓取成功率和反检测效果

## 预期结果

**候选池规模:**
- 每页10个结果，5页 = 50个档案/策略
- 4个策略 = 200个潜在候选人
- 考虑重复和无效链接，预计有效档案: 150-180个

**评估转化率:**
- 匹配度 >0.7 (高匹配): 预计 5-10%
- 匹配度 0.5-0.7 (中匹配): 预计 15-20%
- 匹配度 <0.5 (低匹配): 预计 70-80%

## 风险评估

| 风险点 | 可能性 | 影响 | 缓解措施 |
|--------|--------|------|----------|
| Google 验证码 | 中 | 高 | 使用代理池，控制请求频率 |
| LinkedIn 限流 | 低 | 中 | 档案间30-60秒延时，每日上限20人 |
| 搜索结果为空 | 低 | 中 | 调整关键词，扩大搜索范围 |
| 档案重复率高 | 中 | 低 | 去重机制，多策略交叉验证 |

## 测试结论

✅ **链接生成成功** - 20个可点击搜索链接已生成
✅ **HTML报告正常** - 可视化界面可正常使用
✅ **配置结构化** - JSON格式便于后续自动化处理
✅ **测试数据准备** - 5个示例链接已创建

⚠️ **批量评估待验证** - 需要在有图形界面的环境中运行

---
*记录时间: 2026-03-03 22:55*
*更新: 2026-03-03 23:00*
*记录者: Kobe*
