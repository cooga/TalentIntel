# TalentIntel 数据目录结构规范

**版本**: 2.0  
**更新日期**: 2026-03-22  
**适用范围**: Phase 2 及后续阶段

---

## 📁 目录结构总览

```
Project/TalentIntel/data/
├── README.md                          # 本文件
│
├── active/                            # ✅ 活跃人才池 (核心数据)
│   ├── candidates.json               # 当前有效候选人主库
│   ├── candidates/                   # 详细档案目录
│   │   ├── 001_sarah_chen.json
│   │   ├── 002_michael_wang.json
│   │   └── ...
│   └── reports/                      # 汇总报告
│       ├── weekly_report_20260322.md
│       └── monthly_summary_202603.md
│
├── phase1_archive/                   # 📦 Phase 1 历史归档 (X-Ray搜索)
│   ├── raw/                          # 原始抓取数据
│   │   ├── 2026-03-02/
│   │   ├── 2026-03-03/
│   │   └── ...
│   ├── cleaned/                      # 清理后保留的有效数据
│   │   └── valid_chinese_20260322.json
│   └── invalid/                      # 已排除的数据
│       └── invalid_candidates_20260322.json
│
├── phase2/                           # 🎯 Phase 2 工作区 (LinkedIn数字研究员)
│   ├── raw/                          # 原始LinkedIn浏览数据
│   │   └── YYYYMMDD_HHMMSS/
│   ├── validated/                    # 验证通过的数据
│   │   └── YYYYMMDD/
│   └── pending/                      # 待审核数据
│
├── sources/                          # 🌐 数据源配置
│   ├── linkedin/                     # LinkedIn相关
│   │   ├── profiles/                 # 浏览器Profile
│   │   ├── sessions/                 # 会话状态
│   │   └── credentials/              # 认证信息 (.gitignore)
│   ├── github/                       # GitHub数据源
│   ├── xray/                         # X-Ray搜索配置
│   └── apis/                         # 第三方API配置
│
├── queue/                            # ⏳ 任务队列
│   ├── to_review/                    # 待人工审核
│   ├── to_contact/                   # 待联系
│   ├── contacted/                    # 已联系
│   └── follow_up/                    # 需跟进
│
├── system/                           # ⚙️ 系统数据
│   ├── logs/                         # 运行日志
│   ├── checkpoints/                  # 断点续传
│   ├── metrics/                      # 统计指标
│   └── cache/                        # 临时缓存
│
└── exports/                          # 📤 导出数据
    ├── reports/                      # 报告输出
    ├── csv/                          # CSV格式导出
    └── integrations/                 # 第三方系统集成

```

---

## 📍 关键文件路径规范

### 1. 活跃人才池 (Active Pool)

**主库文件**:
```
data/active/candidates.json
```
- 用途: 当前所有有效华人候选人的主索引
- 格式: JSON数组，每人一条记录
- 更新: 实时更新，每次发现新人即追加

**个人档案**:
```
data/active/candidates/{序号}_{姓氏}_{名字}.json
```
- 示例: `001_sarah_chen.json`, `002_michael_wang.json`
- 包含: 完整LinkedIn档案、评估结果、验证状态、联系记录

**周报告**:
```
data/active/reports/weekly_report_YYYYMMDD.md
```

---

### 2. Phase 1 归档 (X-Ray搜索历史)

**原始数据**:
```
data/phase1_archive/raw/{日期}/
```
- 保留原始抓取数据，仅用于追溯
- 不再主动使用

**清理后保留**:
```
data/phase1_archive/cleaned/valid_chinese_20260322.json
```
- 6位有效华人候选人

**已排除数据**:
```
data/phase1_archive/invalid/invalid_candidates_20260322.json
```
- 44位已排除候选人及原因

---

### 3. Phase 2 工作区 (LinkedIn数字研究员)

**原始浏览数据**:
```
data/phase2/raw/{YYYYMMDD_HHMMSS}/
```
- 每次LinkedIn会话的原始数据
- 按时间戳分目录

**验证通过**:
```
data/phase2/validated/{YYYYMMDD}/candidate_{序号}.json
```

**待审核**:
```
data/phase2/pending/review_queue.json
```

---

### 4. 队列系统

**待人工审核**:
```
data/queue/to_review/
```

**待联系**:
```
data/queue/to_contact/priority_{P0|P1|P2}.json
```

**已联系**:
```
data/queue/contacted/{候选人姓名}/
├── contact_log.json
└── responses/
```

---

## 🔄 数据流转规范

```
Phase 2 发现
    ↓
[data/phase2/raw/] 原始数据
    ↓
自动验证 (LLM评估)
    ↓
[data/phase2/pending/] 待审核
    ↓
人工审核 (ethnicity确认)
    ↓
[data/phase2/validated/] 验证通过
    ↓
合并到活跃池
    ↓
[data/active/candidates.json] 主库更新
    ↓
[data/queue/to_contact/] 进入联系队列
```

---

## ⚠️ 命名规范

### 文件名规范
- 使用小写字母、数字、下划线
- 日期格式: `YYYYMMDD` 或 `YYYYMMDD_HHMMSS`
- 个人档案: `{序号}_{姓}_{名}.json`

### 禁止行为
- ❌ 不要创建多个同义目录 (如 findings/ 和 candidates/)
- ❌ 不要把同一数据复制到多个位置
- ❌ 不要使用中文目录名

### 必须遵循
- ✅ 所有新数据必须走 validation → active 流程
- ✅ 删除旧目录前先确认数据已迁移
- ✅ 更新本文件当目录结构变更

---

## 📊 当前数据快照 (2026-03-22)

```
data/
├── active/
│   └── candidates.json (36人)
├── phase1_archive/
│   ├── cleaned/valid_chinese_20260322.json (6人)
│   └── invalid/invalid_candidates_20260322.json (44人)
├── phase2/
│   ├── daily/2026-03-21/candidates_full_data.json (31人)
│   └── validated/chinese_candidates_20260321.json (31人)
└── [其他系统目录]
```

**总计有效华人候选人**: 36人 (目标: 40人)
**缺口**: 4人

**Phase 2 成果**: 3月21日单日发现 31位华人候选人！
- Google: Robert Liu (Palo Alto)
- NVIDIA: Alex Zhang, Yaxiong Xie, Emily Chen (Santa Clara/San Jose/Redmond)
- Apple: Amy Li, Daniel Wu (Seattle/Austin)
- Stanford: Lisa Zhang
- 及其他25位

---

## 📝 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-03-22 | 2.0 | Phase 2 开始，重构目录结构，明确分离Phase 1归档 |
| 2026-03-04 | 1.0 | Phase 1 初始结构 (已弃用) |

---

## 🎯 下一步行动

1. 创建新的目录结构
2. 迁移现有有效数据到 `active/`
3. 归档 Phase 1 数据到 `phase1_archive/`
4. 开始 Phase 2 搜索，数据进入 `phase2/`

