# TalentIntel Lessons Learned - 经验教训记录

> **记录日期**: 2026-03-20  
> **版本**: v1.0  
> **状态**: 从0到1突破验证完成

---

## 🎯 核心突破

### 从失败到成功的转变

| 维度 | 失败模式 (Before) | 成功模式 (After) |
|------|------------------|-----------------|
| **数据源** | arXiv学术论文 | LinkedIn职业档案 + Google X-Ray |
| **目标人群** | 国内学者(Xidian University) | 北美大厂工程师(Google/NVIDIA/SpaceX) |
| **搜索策略** | 宽泛关键词 | 精准结构化查询 |
| **验证方式** | 全自动(错误率高) | 自动+人工验证(精准) |
| **华人识别** | 未针对性筛选 | 姓名拼音+背景双通道 |

---

## ✅ 成功经验清单

### 1. 数据源优先级 (由高到低)

```
Tier 1 (必选): LinkedIn + Google X-Ray搜索
├── 优势: 职业信息完整、实时更新、覆盖全球
├── 适用: 产业界人才、工程师、研究人员
└── 限制: 需人工处理验证码、每日搜索限额

Tier 2 (辅助): GitHub API
├── 优势: 技术栈可见、开源贡献可量化
├── 适用: 开发者、工程师、技术专家
└── 限制: 非开发者覆盖率低

Tier 3 (补充): arXiv/Semantic Scholar
├── 优势: 学术影响力可衡量
├── 适用: 学术人才、研究员、博士生
└── 限制: 产业界人才少、国内学者多

Tier 4 (深度): 公司官网/会议演讲
├── 优势: 权威信息源
├── 适用: 高管、关键岗位
└── 限制: 手动操作、效率低
```

### 2. 搜索关键词黄金公式

**基础模板**:
```
site:linkedin.com "[公司名]" "[技能1]" OR "[技能2]" "[职位]" "[地点1]" OR "[地点2]"
```

**实际案例**:
```
# SpaceX Starlink无线工程师
site:linkedin.com "SpaceX" "wireless" OR "Starlink" engineer "California"

# NVIDIA无线通信专家
site:linkedin.com "NVIDIA" "wireless" OR "5G" OR "6G" engineer "California" OR "Seattle"

# Google无线系统工程师
site:linkedin.com "Google" "wireless systems" engineer "Mountain View" OR "Sunnyvale"
```

**关键词库**:
```yaml
公司:
  - Google
  - NVIDIA
  - Samsung
  - Nokia
  - SpaceX
  - Qualcomm
  - Intel
  - Meta
  - Amazon
  - Apple
  - Ericsson

技能:
  - wireless
  - 5G / 6G
  - MIMO
  - beamforming
  - signal processing
  - RF
  - mmWave
  - satellite
  - Starlink

职位:
  - engineer
  - researcher
  - scientist
  - architect
  - manager

地点:
  - California
  - Seattle
  - Texas
  - New York
  - Toronto
  - Vancouver
  - London
```

### 3. 华人识别双通道验证法

**通道A: 姓名拼音识别** (准确率~80%)
```python
CHINESE_SURNAMES = [
    'zhang', 'li', 'wang', 'liu', 'chen', 'yang', 
    'zhao', 'huang', 'zhou', 'wu', 'xu', 'sun', 'hu',
    'zhu', 'gao', 'lin', 'he', 'guo', 'ma', 'luo',
    'liang', 'song', 'zheng', 'xie', 'han', 'tang',
    'feng', 'yu', 'dong', 'xiao', 'cheng', 'cao',
    'yuan', 'deng', 'xue', 'tian', 'pan', 'wei', 'jiang'
]
```

**通道B: 教育背景验证** (准确率~90%)
- 国内本科 + 海外硕博
- 国内大学: Tsinghua, Peking, Fudan, SJTU, USTC等
- 海外工作: Google, NVIDIA, SpaceX等

**注意误区**:
- ❌ "Kim"可能是韩裔而非华裔
- ❌ "Chen"可能是越南裔
- ✅ 需结合LinkedIn档案照片/教育经历确认

### 4. 人工验证标准化流程

**触发条件**: 匹配分数 ≥ 0.7 或 疑似华人候选人

**验证步骤**:
```
Step 1: Google搜索确认身份
    └── 查询: "[姓名]" [公司] [职位] LinkedIn

Step 2: LinkedIn档案核实
    └── 检查: 当前职位、教育背景、工作经历

Step 3: 华人身份确认
    └── 检查: 照片、教育经历(国内大学)、姓名拼音

Step 4: 关键信息记录
    └── 记录: 公司、职位、地点、LinkedIn URL、背景亮点
```

**日限额**: 最多3人深度验证(控制时间成本)

### 5. 输出标准化格式

**Markdown报告模板**:
```markdown
## 候选人: [姓名]

**基础信息**:
- 公司: [公司名称]
- 职位: [职位名称]
- 地点: [城市, 州/省, 国家]
- LinkedIn: [URL]

**背景亮点**:
- 前工作经历: [重要公司经历]
- 教育背景: [学校]
- 特殊技能: [AI+无线交叉经验]

**华人确认**: [是/否/疑似]
**匹配分数**: [0.0-1.0]
**优先级**: [P0/P1/P2]
```

---

## ❌ 失败教训清单

### 教训1: 不要迷信学术论文数据库
**问题**: arXiv搜索返回大量国内学者(Xidian University占80%+)
**根因**: 
- 国内学者发文量大
- 海外产业界工程师发文少
**解决**: 产业界人才用LinkedIn, 学术界用arXiv

### 教训2: 避免宽泛关键词
**错误**:
```
"wireless communication AI researcher"
```
**正确**:
```
site:linkedin.com "SpaceX" "Starlink" engineer California
```

### 教训3: 全自动验证不可靠
**问题**: 纯脚本判断华人身份误差率高
**案例**: 
- 误把韩国人识别为华人
- 国内学者vs海外华人混淆
**解决**: 必须人工验证LinkedIn档案

### 教训4: 不要忽视地点筛选
**问题**: 无地点筛选导致结果混杂
**影响**: 国内、欧洲、北美结果混在一起
**解决**: 明确指定目标地点(California/Seattle/Texas)

### 教训5: 公司标签≠能力匹配
**警示案例**:
- ❌ "Google工程师" ≠ "无线通信专家"
- ✅ 需确认具体项目: "Google Wireless Systems Engineer"
- ✅ 更有价值: "SpaceX Starlink Engineer"

---

## 🛠️ 工具链使用指南

### 脚本工具矩阵

| 工具 | 用途 | 适用场景 | 命令示例 |
|------|------|---------|---------|
| `github_talent_miner.py` | GitHub开发者挖掘 | 技术栈验证 | `python3 scripts/github_talent_miner.py --location California` |
| `academic_talent_miner.py` | 学术人才挖掘 | 研究者发现 | `python3 scripts/academic_talent_miner.py` |
| `bigtech_talent_miner.py` | 大厂人才挖掘 | 产业界人才 | `python3 scripts/bigtech_talent_miner.py` |
| `coordinator.py` | 全流程协调 | 每日自动运行 | `python3 coordinator.py` |

### 环境变量配置
```bash
# 必须设置
export GITHUB_TOKEN="your_github_token"  # 提高API限额

# 可选设置
export KIMI_API_KEY="your_kimi_api_key"  # LLM评估(如需要)
```

### 数据目录结构
```
data/
├── daily/                    # 每日发现
│   └── 2026-03-20/
│       ├── report.md         # 人工可读报告
│       ├── talents_final.json # 结构化数据
│       └── verify_*.json     # 待验证任务
├── findings/                 # 深度调研结果
└── xray_campaigns/           # X-Ray搜索链接
```

---

## 📋 每次检索前回顾清单

详见: [PRE_SEARCH_CHECKLIST.md](PRE_SEARCH_CHECKLIST.md)

核心检查项:
- [ ] 目标公司列表已更新
- [ ] 搜索关键词已优化
- [ ] 地点筛选已确认
- [ ] GitHub Token已设置(如需要)
- [ ] 人工验证配额已确认(≤3人/日)
- [ ] 上次经验教训已回顾

---

## 🔄 持续优化机制

### 周度复盘
- 回顾本周发现的人才质量
- 分析误报/漏报案例
- 更新关键词库和公司列表

### 月度更新
- 更新LESSONS_LEARNED.md
- 优化工具脚本
- 扩展数据源(如需要)

### 季度战略
- 评估整体人才库质量
- 调整目标公司优先级
- 更新人才画像定义

---

**最后更新**: 2026-03-20  
**下次回顾**: 2026-03-27
