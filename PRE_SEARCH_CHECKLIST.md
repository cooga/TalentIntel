# TalentIntel Pre-Search Checklist - 检索前回顾清单

> **使用说明**: 每次执行人才检索任务前，必须回顾此清单  
> **预计时间**: 2-3分钟  
> **目的**: 确保方法论一致性，避免重复犯错

---

## 📋 检查清单

### Phase 1: 目标确认 (30秒)

- [ ] **明确目标人群**
  - [ ] 产业界工程师 (推荐)
  - [ ] 学术研究者
  - [ ] 两者兼顾

- [ ] **确认地理范围**
  ```
  目标地点:
  □ California (硅谷、洛杉矶)
  □ Seattle (华盛顿州)
  □ Texas (奥斯汀、达拉斯)
  □ New York (纽约州)
  □ Toronto/Vancouver (加拿大)
  □ 其他: ___________
  ```

- [ ] **华人聚焦确认**
  ```
  □ 是，只关注华人候选人
  □ 否，全球人才
  □ 优先华人，其他也可
  ```

---

### Phase 2: 数据源选择 (30秒)

- [ ] **选择主数据源** (必选其一)
  ```
  □ LinkedIn + Google X-Ray (产业界首选)
    └── 适用: Google/NVIDIA/SpaceX等大厂工程师
  
  □ GitHub API (开发者验证)
    └── 适用: 技术栈深度评估
  
  □ arXiv + Semantic Scholar (学术界)
    └── 适用: 博士后、研究员、教授
  
  □ 组合模式: LinkedIn为主 + GitHub验证
  ```

- [ ] **确认工具准备**
  ```
  □ GitHub Token已设置 (export GITHUB_TOKEN=...)
  □ 网络连接正常
  □ 浏览器可访问LinkedIn
  □ 数据目录已创建 (data/daily/YYYYMMDD)
  ```

---

### Phase 3: 搜索策略回顾 (60秒)

- [ ] **关键词公式检查**
  ```
  模板: site:linkedin.com "[公司]" "[技能]" "[职位]" "[地点]"
  
  实际查询:
  _________________________________________________
  
  检查点:
  □ 包含site:linkedin.com限定
  □ 公司名称用引号精确匹配
  □ 技能关键词用OR连接
  □ 地点已指定
  ```

- [ ] **目标公司列表确认**
  ```
  优先级P0 (必搜):
  □ Google
  □ NVIDIA
  □ SpaceX/Starlink
  □ Samsung
  
  优先级P1 (选搜):
  □ Qualcomm
  □ Intel
  □ Nokia
  □ Meta
  
  其他: ___________
  ```

- [ ] **技能关键词库**
  ```
  核心技能 (至少选2):
  □ wireless
  □ 5G / 6G
  □ MIMO / beamforming
  □ AI / machine learning
  □ signal processing
  □ RF / mmWave
  □ satellite / Starlink
  ```

---

### Phase 4: 华人识别策略 (30秒)

- [ ] **双通道验证确认**
  ```
  通道A - 姓名识别:
  □ 已加载华人姓氏库
  □ 脚本已配置拼音匹配
  
  通道B - 背景验证:
  □ 将检查教育经历
  □ 将核实LinkedIn档案照片
  ```

- [ ] **常见误区回顾**
  ```
  □ Kim可能是韩裔
  □ Chen可能是越南裔
  □ 必须人工验证LinkedIn档案
  □ 不要仅凭姓名判断
  ```

---

### Phase 5: 人工验证准备 (30秒)

- [ ] **时间预算确认**
  ```
  今日人工验证配额: ___/3 人
  (建议不超过3人，控制时间成本)
  ```

- [ ] **验证流程回顾**
  ```
  Step 1: Google搜索 "[姓名] [公司] LinkedIn"
  Step 2: 打开LinkedIn档案
  Step 3: 确认当前职位和公司
  Step 4: 检查教育背景(国内大学?)
  Step 5: 记录关键信息到report.md
  ```

- [ ] **输出模板准备**
  ```
  data/daily/[YYYYMMDD]/ 目录已创建
  □ report.md 文件已初始化
  □ talents_final.json 可写入
  ```

---

## 📚 经验教训快速回顾

### 必读 (10秒)

**成功经验**:
1. ✅ LinkedIn + Google X-Ray是产业界人才的最佳数据源
2. ✅ 精准关键词 > 宽泛关键词
3. ✅ 华人识别需双通道验证
4. ✅ 每日人工验证≤3人

**失败教训**:
1. ❌ arXiv主要返回国内学者(80%+)
2. ❌ 全自动验证误差率高
3. ❌ 无地点筛选导致结果混杂
4. ❌ 公司标签≠能力匹配(需看具体项目)

### 上次检索关键发现

```
日期: 2026-03-20
突破: 从0到1验证10+北美大厂候选人
Top发现:
- Wei C. (NVIDIA) - 华人
- Jenny Chu (SpaceX) - 华人
- Sanjay Verghese (Google) - 前SpaceX

问题记录:
- ___________________________________
- ___________________________________
```

---

## 🚀 执行命令

### 快速启动 (推荐)

```bash
cd ~/.openclaw/workspace/Project/TalentIntel

# 运行完整流程
python3 coordinator.py

# 或单独运行某阶段
python3 scripts/bigtech_talent_miner.py
python3 scripts/github_talent_miner.py --location California
```

### 人工验证模式

```bash
# 生成验证任务后，手动执行:
agent-browser open "https://www.google.com/search?q=[姓名]+[公司]+LinkedIn"

# 记录结果到:
# data/daily/[YYYYMMDD]/report.md
```

---

## ✅ 最终确认

**我已确认**:
- [ ] 本次检索目标人群已明确
- [ ] 数据源策略已选择
- [ ] 搜索关键词已优化
- [ ] 地点筛选已确认
- [ ] 华人识别策略已回顾
- [ ] 人工验证配额已规划
- [ ] 上次经验教训已回顾

**开始检索时间**: _______  
**预计完成时间**: _______

---

## 📞 问题处理

**如遇问题**:
1. Google搜索被限流 → 等待5分钟后重试
2. LinkedIn需要登录 → 使用agent-browser手动验证
3. GitHub API限流 → 检查GITHUB_TOKEN是否设置
4. 不确定是否华人 → 标记"疑似"，待人工验证

**参考文档**:
- [LESSONS_LEARNED.md](LESSONS_LEARNED.md) - 详细经验教训
- [README_v2.md](README_v2.md) - 系统架构说明
- 各脚本 --help 获取使用说明
