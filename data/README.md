# TalentIntel 数据目录结构规范

**版本**: 2.1  
**更新日期**: 2026-03-27  
**适用范围**: Phase 2 及后续阶段

---

## 📊 当前数据快照 (2026-03-27)

| 数据文件 | 数量 | 说明 |
|----------|------|------|
| `clean_candidates_db.json` | 90人 | 已验证候选人总库 |
| `chinese_talent_summary.json` | 72人 | 海外华人专家（≥0.7分61人） |
| `verification_progress.json` | - | LinkedIn验证进度追踪 |
| `verification_summary.json` | - | 验证结果汇总 |
| `linkedin_verification_report.json` | - | LinkedIn验证报告 |
| `daily_search/` | 7天 | 最近7日搜索任务 |

**目标达成**: 72/40 华人候选人 (180% ✓)

---

## 📁 目录结构总览

```
Project/TalentIntel/data/
├── README.md                          # 本文件
│
├── clean_candidates_db.json          # ✅ 核心数据库：90位已验证候选人
├── chinese_talent_summary.json       # ✅ 华人人才汇总：72位专家
├── verification_progress.json        # LinkedIn验证进度
├── verification_summary.json         # 验证结果汇总
├── linkedin_verification_report.json # LinkedIn验证报告
│
├── active/                            # 活跃人才池
│   ├── candidates.json               # 当前有效候选人主库
│   └── candidates/                   # 详细档案目录
│
├── daily_search/                      # 每日搜索任务
│   ├── search_tasks_20260323_020034.json
│   ├── search_tasks_20260324_020141.json
│   ├── search_tasks_20260325_020040.json
│   ├── search_tasks_20260326_020224.json
│   └── search_tasks_20260327_020306.json
│
├── monitor_results/                   # 监控结果
│   └── monitor_report_20260327_000606.json
│
├── backups/                           # 自动备份
│   └── clean_candidates_20260326_225246.json
│
├── findings/                          # 研究发现（按日期）
│   └── 2026-03-24/
│
├── exports/                           # 导出文件
│
├── phase2/                            # Phase 2 历史数据
│   └── daily/2026-03-20/
│
└── profiles/                          # 浏览器Profile（.gitignore）
```

---

## 📍 关键文件说明

### 核心数据库

| 文件 | 用途 | 更新频率 |
|------|------|----------|
| `clean_candidates_db.json` | 主数据库，90位已验证候选人 | 每日更新 |
| `chinese_talent_summary.json` | 华人人才专项汇总 | 每日更新 |
| `verification_progress.json` | LinkedIn档案验证进度 | 实时更新 |
| `verification_summary.json` | 验证结果统计 | 每次验证后 |

### 每日搜索任务

```
data/daily_search/search_tasks_YYYYMMDD_HHMMSS.json
```
- 每日自动搜索的配置和结果
- 保留最近7天记录
- 自动清理旧文件

### 监控结果

```
data/monitor_results/monitor_report_YYYYMMDD_HHMMSS.json
```
- 人才监控系统输出
- 包含新发现候选人

---

## 🔄 数据流转规范

```
每日搜索 / X-Ray搜索
    ↓
原始数据 → verification_progress.json
    ↓
LinkedIn验证
    ↓
验证通过 → clean_candidates_db.json
    ↓
华人筛选 → chinese_talent_summary.json
    ↓
生成报告 → CHINESE_TALENT_OVERALL_REPORT.md
```

---

## ⚠️ 命名规范

### 文件名规范
- 使用小写字母、数字、下划线
- 日期格式: `YYYYMMDD` 或 `YYYYMMDD_HHMMSS`
- 个人档案: `{序号}_{姓}_{名}.json`

### 禁止行为
- ❌ 不要把同一数据复制到多个位置
- ❌ 不要手动修改核心数据库文件

### 必须遵循
- ✅ 所有数据变更通过脚本操作
- ✅ 重要修改前自动备份
- ✅ 更新本文件当目录结构变更

---

## 📝 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-03-27 | 2.1 | 更新数据快照：90位已验证候选人，72位华人专家 |
| 2026-03-22 | 2.0 | Phase 2 开始，重构目录结构 |
| 2026-03-04 | 1.0 | Phase 1 初始结构 (已弃用) |

---

## 📈 数据来源分布

**72位华人候选人来源**:
- NVIDIA: 12人
- Qualcomm: 7人
- AMD: 6人
- Marvell: 6人
- Intel: 5人
- Apple: 5人
- 其他: 31人

**地区分布**:
- United States: 66人
- UK: 3人
- Hong Kong: 3人

---

## 🎯 数据质量

| 指标 | 数值 |
|------|------|
| 总候选人 | 90人 |
| 已验证LinkedIn | 62人 |
| 华人候选人 | 72人 |
| 高分(≥0.7) | 61人 |
| 北美地区 | 66人 |

---

*最后更新: 2026-03-27*
