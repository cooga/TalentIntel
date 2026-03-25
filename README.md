# TalentIntel - 数字人才研究员

一个模拟人类研究行为的智能Agent，用于合规地收集和分析人才信息。

> **核心原则**: 不是爬虫，而是数字员工；不是批量抓取，而是深度理解

---

## 架构概述

### 核心设计理念

```
传统爬虫                    TalentIntel 数字研究员
─────────────────────────────────────────────────────────
速度优先（秒级遍历）   →    质量优先（分钟级深度阅读）
批量请求              →    会话式浏览
结构化提取            →    LLM理解+判断
24/7不间断            →    人类工作时间+休息
无状态                →    长期记忆（知识图谱）
```

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     TalentIntel 系统架构                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Layer 1: 行为模拟层 (Behavior Simulation)          │   │
│  │  ├── 鼠标轨迹：贝塞尔曲线 + Perlin噪声（手抖模拟）   │   │
│  │  ├── 阅读模式：200 WPM ± 30，泊松分布建模           │   │
│  │  ├── 滚动行为：非匀速 + 停顿 + 回滚                 │   │
│  │  └── 工作节奏：09:00-18:00，45分钟工作+休息         │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Layer 2: 浏览器管理 (Browser Management)           │   │
│  │  ├── Playwright + 自定义 stealth 脚本               │   │
│  │  ├── WebGL/Canvas 指纹噪声注入                      │   │
│  │  ├── 真实浏览器 Profile（多账号隔离）               │   │
│  │  └── 会话持久化（自动恢复登录状态）                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Layer 3: 认知理解层 (Cognitive Layer)              │   │
│  │  ├── LLM 页面解析（理解而非抓取）                   │   │
│  │  ├── 人才价值评分（AI能力 + Wireless能力）          │   │
│  │  ├── 关联推理（与已知人才的关系网）                 │   │
│  │  └── 决策引擎：深挖 / 跳过 / 记录 / 标记            │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Layer 4: 任务调度 (Task Orchestration)             │   │
│  │  ├── 每日"工作计划"生成（基于优先级队列）           │   │
│  │  ├── 断点续传（会话状态持久化）                     │   │
│  │  ├── 限流保护（30-60秒冷却，每日上限3人）           │   │
│  │  └── 工作日志（研究员-style 记录）                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Layer 5: 数据沉淀 (Data Persistence)               │   │
│  │  ├── 原始浏览记录（截图、HTML）                     │   │
│  │  ├── 结构化人才档案（JSON格式）                     │   │
│  │  ├── 置信度评分与匹配理由                           │   │
│  │  └── 每日汇总报告（Markdown）                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd Project/TalentIntel

# 运行安装脚本
./setup.sh
```

### 2. 配置账号

```bash
# 复制配置模板
cp config/researcher.example.yaml config/researcher.yaml

# 编辑配置文件
# - 填入 LinkedIn 小号邮箱
# - 调整工作时段、阅读速度等参数

# 设置密码（环境变量方式，不写入文件）
export LINKEDIN_PASSWORD="your_linkedin_password"
export KIMI_API_KEY="your_kimi_api_key"  # 可选，用于LLM评估
```

### 3. 定义目标人才画像

编辑 `config/targets.yaml`：

```yaml
targets:
  - name: "AI-Wireless Researchers"
    priority: high
    criteria:
      keywords:
        - "machine learning wireless"
        - "deep learning 5G"
        - "AI communication"
      locations:
        - "United States"
        - "Canada"
      education:
        - "PhD"
        - "PostDoc"
```

### 4. 运行研究员

```bash
# 首次运行（可见浏览器，便于调试）
python3 -m src.main

# 后续运行（后台模式）
python3 -m src.main --headless
```

---

## 核心工作流程

### 完整执行流程

```
启动
  ↓
加载配置 (researcher.yaml, targets.yaml)
  ↓
启动隐身浏览器 (Playwright + Stealth)
  ↓
自动登录 LinkedIn（使用保存的session）
  ↓
按目标画像搜索关键词
  ↓
对于每个候选档案:
    ├── 冷却等待 (30-60秒)
    ├── 访问档案页面
    ├── 模拟人类阅读:
    │   ├── 鼠标移动到关键区域
    │   ├── 基于内容长度计算停留时间
    │   └── 自然滚动 + 停顿
    ├── LLM评估人才价值
    │   ├── AI能力评分 (junior/senior/expert)
    │   ├── Wireless能力评分
    │   └── 综合匹配分数 (0-1)
    └── 如果匹配度>0.5:
        ├── 保存结构化档案
        └── 记录到发现列表
  ↓
生成每日汇总报告
  ↓
关闭浏览器，保存会话状态
```

### 输出示例

**每日发现报告** (`data/findings/2026-03-02/report.md`)：

```markdown
# 人才研究发现汇总 - 2026-03-02

## 总计: 2 人
- 🔥 高优先级: 1 人
- ⭐ 中优先级: 1 人

## 🏆 TOP 人才

### 1. Yousef Shawky
- **匹配分数**: 0.75 | **优先级**: HIGH
- **职位**: Senior AI Researcher at Bell Labs
- **AI 能力**: expert (10年经验，多篇arXiv论文)
- **Wireless 能力**: senior (5年项目经验，3项专利)
- **亮点**: PhD + 北美大厂经验，AI + 6G交叉背景
- **建议**: 立即联系，邀请合作
- **档案链接**: https://www.linkedin.com/in/yousef-shawky-ba0239167
```

---

## 合规与风险控制

### 反检测机制

| 检测点 | 应对措施 |
|--------|----------|
| WebDriver 检测 | 覆盖 `navigator.webdriver` 属性 |
| 指纹检测 | Canvas/WebGL 噪声注入，真实字体列表 |
| 行为分析 | 贝塞尔曲线鼠标，人类阅读速度，工作时段 |
| 频率限制 | 30-60秒/档案，每日上限3人，随机冷却 |
| 账号关联 | 独立浏览器 Profile，隔离 Cookie/缓存 |

### 合规边界

| ✅ 安全做法 | ❌ 避免行为 |
|------------|------------|
| 使用真实个人账号登录 | 批量注册假账号 |
| 模拟人类阅读速度 (~3分钟/档案) | 秒级快速翻页 |
| 每日3-5人，分散在不同时段 | 系统性遍历大量档案 |
| 仅获取公开可见信息 | 突破隐私设置或付费墙 |
| 随机停顿，模拟思考时间 | 机械化匀速操作 |

---

## 项目结构

```
TalentIntel/
├── README.md                 # 本文件
├── requirements.txt          # Python依赖
├── setup.sh                  # 一键安装脚本
├── config/
│   ├── researcher.yaml       # 研究员配置
│   ├── search_keywords.yaml  # 搜索关键词配置
│   ├── target_companies.yaml # 目标公司列表
│   └── extended_keywords.yaml # 扩展关键词
├── src/                      # 源代码（待重构）
├── scripts/                  # 数据处理脚本
│   ├── unify_candidates_db.py    # 合并所有候选人数据
│   ├── clean_candidates_db.py    # 清理模拟数据
│   └── generate_csv_report.py    # 生成CSV报告
├── data/                     # 数据目录
│   ├── .gitignore            # 忽略浏览器缓存等
│   ├── unified_candidates_db.json    # 统一数据库（完整数据）
│   ├── clean_candidates_db.json      # 清理后数据库（推荐）
│   ├── chinese_talent_summary.json   # 华人人才汇总
│   ├── active/               # 活跃候选人档案
│   │   ├── candidates.json   # 活跃候选人主文件
│   │   └── candidates/       # 候选人详细档案 (001_xxx.json)
│   ├── research/             # X-Ray研究发现
│   │   ├── DISCOVERED_CANDIDATES_*.json
│   │   ├── ROUND2_DISCOVERED_*.json
│   │   └── *_CANDIDATES_*.json
│   ├── xray_searches/        # X-Ray搜索原始结果
│   │   ├── spacex_search_results.json
│   │   ├── nvidia_search_results_final.json
│   │   └── qualcomm_*.json
│   ├── daily_search/         # 每日搜索任务
│   ├── findings/             # 历史研究发现（按日期）
│   ├── exports/              # 导出文件
│   │   ├── csv/              # CSV报告
│   │   └── reports/          # Markdown报告
│   └── profiles/             # 浏览器指纹/会话（gitignored）
└── logs/                     # 工作日志
```

### 数据使用说明

**主数据库文件：**
- `data/clean_candidates_db.json` - **推荐使用**，不含模拟数据，118位真实候选人
- `data/unified_candidates_db.json` - 完整数据库（含所有来源）

**CSV报告生成：**
```bash
cd Project/TalentIntel
python3 scripts/clean_candidates_db.py
# 输出: /tmp/clean_candidates_report_YYYY-MM-DD.csv
```

**数据清理原则：**
- ❌ 所有模拟数据已删除（原 phase2/simulated_data/）
- ❌ 浏览器缓存数据已忽略（.gitignore）
- ✅ 仅保留真实候选人数据

---

## 实测结果

### 验证记录 (2026-03-02)

| 指标 | 结果 |
|------|------|
| LinkedIn登录 | ✅ 成功，无验证挑战 |
| 反检测 | ✅ 无异常提示，会话保持正常 |
| 鼠标行为 | ✅ 轨迹自然，无机械感 |
| 阅读模拟 | ✅ 停留时间合理（3-15秒/区块） |
| 搜索成功率 | ✅ 找到10个候选，查看3个 |
| 人才匹配 | ✅ 2个匹配度>0.5 |
| 限流保护 | ✅ 未触发任何限制 |

### 发现案例

1. **Yousef Shawky** - 匹配度 0.75
   - Bell Labs Senior AI Researcher
   - 10年AI + 5年Wireless，3项专利
   - 保存: `data/findings/2026-03-02/yousef_shawky_234520.json`

2. **Owen Wen** - 匹配度 0.60
   - ML Engineer at Wireless Tech Co.
   - AI + 5G交叉背景
   - 保存: `data/findings/2026-03-02/owen_wen_234512.json`

---

## 后续优化方向

- [ ] 多平台扩展（GitHub交叉验证、Google Scholar）
- [ ] 人才长期跟踪（职业变动自动提醒）
- [ ] 知识图谱构建（人才关系网络）
- [ ] 自动 outreach（个性化联系消息生成）

---

## License

Internal use only.
