# TalentIntel - 数字人才研究员

> **核心定位**: 自动化发现 + LLM理解 + 低频人工验证  
> **目标人群**: 海外华人AI+无线通信交叉领域人才  
> **数据来源**: 北美大厂(Google/NVIDIA/SpaceX/Samsung等)

---

## 🚀 快速开始

### 1. 检索前准备 (必读)

每次检索前，回顾检查清单:

```bash
# 阅读检查清单 (2-3分钟)
cat PRE_SEARCH_CHECKLIST.md

# 阅读经验教训 (如上次已读过可跳过)
cat LESSONS_LEARNED.md
```

### 2. 配置环境

```bash
# 设置GitHub Token (提高API限额)
export GITHUB_TOKEN="your_github_token"

# 进入工作目录
cd ~/.openclaw/workspace/Project/TalentIntel
```

### 3. 执行检索

```bash
# 方案A: 运行完整流程 (推荐)
python3 coordinator.py

# 方案B: 单独运行特定挖掘器
python3 scripts/bigtech_talent_miner.py      # 北美大厂
python3 scripts/github_talent_miner.py       # GitHub开发者
python3 scripts/academic_talent_miner.py     # 学术界
```

### 4. 人工验证 (高频候选人)

```bash
# 查看今日发现的候选人
cat data/daily/$(date +%Y-%m-%d)/report.md

# 使用agent-browser验证LinkedIn
agent-browser open "https://www.google.com/search?q=[姓名]+[公司]+LinkedIn"

# 更新验证结果到report.md
```

---

## 📊 项目结构

```
TalentIntel/
├── README.md                   # 本文件
├── LESSONS_LEARNED.md          # ⭐ 经验教训记录
├── PRE_SEARCH_CHECKLIST.md     # ⭐ 检索前检查清单
├── README_v2.md                # 详细架构文档
├── coordinator.py              # 主协调器
│
├── scripts/                    # 挖掘脚本
│   ├── bigtech_talent_miner.py    # 北美大厂人才
│   ├── github_talent_miner.py     # GitHub开发者
│   ├── academic_talent_miner.py   # 学术界人才
│   └── aggregate_talent_data.py   # 数据汇总
│
├── data/                       # 数据目录
│   └── daily/                  # 每日发现
│       └── 2026-03-20/
│           ├── report.md
│           ├── talents_final.json
│           └── verify_*.json
│
└── config/                     # 配置文件
    └── targets.yaml            # 目标人才画像
```

---

## 🎯 使用流程

### 标准工作流

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 检索前准备                                          │
│  ├── 阅读 PRE_SEARCH_CHECKLIST.md                          │
│  ├── 回顾 LESSONS_LEARNED.md                               │
│  └── 确认目标公司/地点/关键词                               │
├─────────────────────────────────────────────────────────────┤
│  Step 2: 自动发现                                            │
│  ├── 运行 coordinator.py 或特定挖掘器                       │
│  └── 生成候选人列表 (data/daily/YYYYMMDD/)                  │
├─────────────────────────────────────────────────────────────┤
│  Step 3: 华人筛选                                            │
│  ├── 算法: 姓名拼音匹配                                     │
│  └── 标记疑似华人候选人                                     │
├─────────────────────────────────────────────────────────────┤
│  Step 4: 人工验证 (≤3人/日)                                  │
│  ├── Google搜索确认身份                                     │
│  ├── LinkedIn档案核实                                       │
│  └── 记录: 公司/职位/地点/LinkedIn URL                      │
├─────────────────────────────────────────────────────────────┤
│  Step 5: 输出报告                                            │
│  ├── Markdown报告 (report.md)                               │
│  ├── JSON数据 (talents_final.json)                          │
│  └── LinkedIn链接汇总                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 关键文档导航

| 文档 | 用途 | 阅读时机 |
|------|------|---------|
| [PRE_SEARCH_CHECKLIST.md](PRE_SEARCH_CHECKLIST.md) | 检索前回顾清单 | **每次检索前必读** |
| [LESSONS_LEARNED.md](LESSONS_LEARNED.md) | 经验教训记录 | 首次使用前、每周回顾 |
| [README_v2.md](README_v2.md) | 详细架构文档 | 系统理解、故障排查 |

---

## 🛠️ 工具链

### 主要脚本

| 脚本 | 用途 | 命令 |
|------|------|------|
| `coordinator.py` | 全流程自动化 | `python3 coordinator.py` |
| `bigtech_talent_miner.py` | 北美大厂挖掘 | `python3 scripts/bigtech_talent_miner.py` |
| `github_talent_miner.py` | GitHub开发者 | `python3 scripts/github_talent_miner.py --location California` |
| `academic_talent_miner.py` | 学术界人才 | `python3 scripts/academic_talent_miner.py` |

### 辅助工具

```bash
# 数据汇总
python3 scripts/aggregate_talent_data.py

# 浏览器验证
agent-browser open "[URL]"
```

---

## 📈 成功案例

### 2026-03-20 突破案例

**背景**: 从0开始，目标海外华人AI+无线通信人才

**策略**:
- 数据源: LinkedIn + Google X-Ray (替代arXiv)
- 目标公司: Google/NVIDIA/SpaceX/Samsung
- 地点: California/Seattle
- 华人识别: 姓名拼音 + 背景验证

**成果**:
- 发现10+北美大厂候选人
- 验证4位海外华人(Wei C., Jenny Chu, Yaxiong Xie, Xianbin Wang)
- 确认6家目标公司人才分布

**关键经验**: 记录在 [LESSONS_LEARNED.md](LESSONS_LEARNED.md)

---

## ⚙️ 配置说明

### 环境变量

```bash
# 必须 (提高GitHub API限额)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"

# 可选 (LLM评估)
export KIMI_API_KEY="sk-xxxxxxxxxxxx"
```

### 自定义搜索

编辑脚本文件调整参数:

```python
# scripts/bigtech_talent_miner.py
TARGET_COMPANIES = [
    'Google', 'NVIDIA', 'Samsung',
    'SpaceX', 'Qualcomm', 'Nokia'
]

LOCATIONS = [
    'California', 'Seattle', 'Texas',
    'New York', 'Toronto'
]
```

---

## 🎯 最佳实践

### DO ✅
- 每次检索前回顾 **PRE_SEARCH_CHECKLIST.md**
- 使用精准结构化搜索关键词
- 双通道验证华人身份(姓名+背景)
- 控制人工验证频率(≤3人/日)
- 及时记录到 LESSONS_LEARNED.md

### DON'T ❌
- 不要纯依赖学术论文数据库(arXiv)
- 不要使用宽泛关键词
- 不要全自动验证(误差率高)
- 不要忽视地点筛选
- 不要混淆公司标签与具体能力

---

## 📞 故障排查

| 问题 | 解决方案 |
|------|---------|
| Google搜索被限流 | 等待5分钟后重试，或更换IP |
| LinkedIn需要登录 | 使用agent-browser手动验证 |
| GitHub API限流 | 检查GITHUB_TOKEN是否设置 |
| 不确定是否华人 | 标记"疑似"，待人工验证 |
| 结果质量低 | 回顾LESSONS_LEARNED，优化关键词 |

---

## 📅 维护计划

| 频率 | 任务 |
|------|------|
| 每次检索 | 阅读PRE_SEARCH_CHECKLIST.md |
| 每周 | 回顾本周发现质量，更新关键词 |
| 每月 | 更新LESSONS_LEARNED.md，优化脚本 |
| 每季度 | 评估整体人才库，调整目标公司 |

---

**版本**: v2.1  
**更新日期**: 2026-03-20  
**下次更新**: 2026-03-27
