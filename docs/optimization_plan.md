# TalentIntel 深度检索优化方案

**文档版本**: v1.0  
**创建时间**: 2026-03-21  
**基于实践**: 2026-03-21 人工深度检索成功经验

---

## 📋 目录

1. [现状诊断](#现状诊断)
2. [成功要素分析](#成功要素分析)
3. [优化方案](#优化方案)
4. [实施路线图](#实施路线图)
5. [附录：配置模板](#附录配置模板)

---

## 现状诊断

### 定时检索 vs 人工检索对比

| 维度 | 定时检索 (现状) | 人工检索 (成功实践) | 差距 |
|------|----------------|-------------------|------|
| **目标清晰度** | 模糊 ("累计50人") | 精确 (100人/40华人) | ❌ 缺乏量化指标 |
| **搜索深度** | 单轮浅层扫描 | 多轮迭代+交叉验证 | ❌ 深度不足 |
| **公司聚焦** | 随机分布 | Tier1/Tier2优先 | ❌ 精准度低 |
| **输出质量** | 简单日志 | 详细档案+报告 | ❌ 无法追溯 |
| **评估机制** | 无人工评估 | P0/P1/P2分级 | ❌ 缺乏优先级 |
| **华人识别** | 未统计 | 专项追踪66人 | ❌ 核心目标缺失 |

### 关键问题

1. **目标不明确** - 只有"扫描"动作，没有"产出"要求
2. **无质量门槛** - 低匹配度候选人混入，稀释价值
3. **无专项追踪** - 华人候选人未单独统计和归档
4. **输出不完整** - 缺乏详细报告和可追溯档案
5. **评估体系缺失** - 无法区分高优先级和一般候选人

---

## 成功要素分析

### 核心成功因素 (基于2026-03-21实践)

```
┌─────────────────────────────────────────────────────────────┐
│                    成功金字塔                                │
├─────────────────────────────────────────────────────────────┤
│  【第5层】完整交付                                              │
│   ├── FINAL_REPORT.md (执行摘要)                              │
│   ├── full_report.md (完整详情)                               │
│   └── chinese_summary.md (华人专项)                           │
├─────────────────────────────────────────────────────────────┤
│  【第4层】质量评估                                              │
│   ├── P0级: 立即联系 (16人)                                   │
│   ├── P1级: 本周联系 (90人)                                   │
│   └── P2级: 后续跟进 (19人)                                   │
├─────────────────────────────────────────────────────────────┤
│  【第3层】精准定位                                              │
│   ├── Tier1: Google, Meta, NVIDIA, Apple                      │
│   ├── Tier2: OpenAI, Anthropic, DeepMind                      │
│   └── Wireless: Qualcomm, SpaceX, Samsung                     │
├─────────────────────────────────────────────────────────────┤
│  【第2层】量化目标                                              │
│   ├── 总量目标: 100人                                         │
│   └── 华人目标: 40人 (超额完成66人)                            │
├─────────────────────────────────────────────────────────────┤
│  【第1层】专注执行                                              │
│   └── 子代理5-10分钟专注深度搜索                               │
└─────────────────────────────────────────────────────────────┘
```

### 产出对比

| 指标 | 定时检索 (3/20) | 人工检索 (3/21) | 提升幅度 |
|------|----------------|----------------|---------|
| 候选人总数 | 50人 | **125人** | +150% |
| 华人候选人 | 未统计 | **66人** | 从0到66 |
| 高优先级(P0) | 0人 | **16人** | 从无到有 |
| 详细档案 | ❌ 无 | ✅ 完整 | 质变 |
| 可追溯报告 | ❌ 无 | ✅ 4份报告 | 可审计 |

---

## 优化方案

### 方案A: 增强型定时任务 (推荐)

保持定时任务自动化优势，同时提升产出质量。

```yaml
# config/daily_search_v2.yaml
daily_talent_search:
  # 执行配置
  schedule: "0 2 * * *"  # 每日凌晨2点
  timeout: 1800          # 30分钟超时
  
  # 量化目标
  target:
    total: 20            # 每日目标候选人
    chinese_min: 8       # 华人候选人最低数量
    high_priority_min: 3 # P0级候选人最低数量
  
  # 搜索策略
  strategy:
    rounds: 3            # 多轮迭代
    companies:
      tier1: [Google, Meta, NVIDIA, Apple]
      tier2: [OpenAI, Anthropic, DeepMind]
      wireless: [Qualcomm, SpaceX, Samsung, Ericsson]
    keywords:
      - "AI wireless communication"
      - "machine learning 5G"
      - "deep learning MIMO"
  
  # 质量门槛
  quality_gate:
    min_match_score: 0.75        # 最低匹配度
    require_linkedin: true       # 必须LinkedIn链接
    require_evaluation: true     # 必须完整评估
  
  # 输出配置
  output:
    daily_report: "data/daily/{date}/report.md"
    chinese_summary: "data/daily/{date}/chinese_candidates.md"
    raw_data: "data/daily/{date}/candidates.json"
    
  # 通知配置
  notification:
    discord: true
    summary_only: false   # 发送完整报告而不仅是摘要
```

### 方案B: 周期性深度检索

保留轻量级定时任务，增加周期性深度检索。

```yaml
# config/periodic_deep_search.yaml
tasks:
  # 每日轻量级补充 (保持现有)
  daily_light:
    schedule: "0 2 * * *"
    target: { total: 10, chinese_min: 3 }
    output: summary_only  # 仅统计日志
  
  # 每周深度检索 (新增)
  weekly_deep:
    schedule: "0 9 * * 1"  # 每周一上午9点
    target: { total: 100, chinese_min: 40 }
    output: full_report    # 完整报告
    duration: 60min        # 深度搜索1小时
  
  # 月度全面盘点 (新增)
  monthly_comprehensive:
    schedule: "0 9 1 * *"  # 每月1日上午9点
    target: { total: 300, chinese_min: 100 }
    output: comprehensive_report
    actions: [deduplication, re_evaluation, trend_analysis]
```

### 方案C: 事件驱动检索 (进阶)

基于触发条件的智能检索。

```yaml
# config/event_driven.yaml
event_triggers:
  # 公司动态触发
  company_hiring:
    trigger: "目标公司发布AI/无线相关职位"
    action: immediate_search
    priority: P0
  
  # 候选人动态触发
  candidate_update:
    trigger: "已追踪候选人更新LinkedIn"
    action: profile_refresh
    priority: P1
  
  # 学术会议触发
  conference_season:
    trigger: "NeurIPS/ICML/MobiCom等会议截稿/召开"
    action: academic_deep_search
    priority: P1
  
  # 手动触发
  manual:
    trigger: "用户指令"
    action: custom_search
    priority: P0
```

---

## 实施路线图

### Phase 1: 立即实施 (本周)

- [ ] 更新定时任务配置，增加量化目标
- [ ] 添加质量门槛 (min_match_score: 0.75)
- [ ] 启用华人候选人专项统计
- [ ] 配置详细报告输出

**预期效果**: 每日产出从"日志"升级为"可追溯报告"

### Phase 2: 短期优化 (2周内)

- [ ] 实施多轮迭代搜索策略
- [ ] 建立公司分级搜索机制
- [ ] 开发P0/P1/P2自动评估
- [ ] 添加去重和更新检测

**预期效果**: 搜索质量和精准度显著提升

### Phase 3: 中期建设 (1个月内)

- [ ] 实施周期性深度检索 (周/月)
- [ ] 建立候选人持续跟踪系统
- [ ] 开发事件驱动检索模块
- [ ] 构建人才趋势分析能力

**预期效果**: 从"搜索工具"升级为"人才情报系统"

---

## 附录：配置模板

### 完整配置示例

```yaml
# ~/.openclaw/workspace/Project/TalentIntel/config/optimized_search.yaml

version: "2.0"
name: "TalentIntel Optimized Search"

# 检索模式配置
modes:
  daily:
    enabled: true
    schedule: "0 2 * * *"
    target:
      total: 20
      chinese_min: 8
      high_priority_min: 3
    strategy:
      rounds: 2
      depth: standard
    output: detailed
    
  weekly_deep:
    enabled: true
    schedule: "0 9 * * 1"
    target:
      total: 100
      chinese_min: 40
      high_priority_min: 15
    strategy:
      rounds: 5
      depth: deep
      companies: [Google, Meta, NVIDIA, Apple, OpenAI, Qualcomm, SpaceX]
    output: comprehensive
    
  monthly:
    enabled: true
    schedule: "0 9 1 * *"
    target:
      total: 300
      chinese_min: 100
    actions: [deduplicate, re_evaluate, trend_analysis]

# 质量门槛
quality:
  min_match_score: 0.75
  min_profile_completeness: 0.6
  required_fields: [name, company, role, linkedin_url]
  
# 评估标准
evaluation:
  p0_threshold: 0.90  # 立即联系
  p1_threshold: 0.80  # 本周联系
  p2_threshold: 0.70  # 后续跟进
  
  scoring_weights:
    ai_expertise: 0.3
    wireless_expertise: 0.3
    company_tier: 0.2
    chinese_background: 0.2

# 输出配置
output:
  formats: [markdown, json]
  directory: "data/daily/{date}/"
  files:
    summary: "FINAL_REPORT.md"
    full: "full_report.md"
    chinese: "chinese_candidates.md"
    raw: "candidates.json"
    
# 通知配置
notifications:
  discord:
    enabled: true
    channel: "user:1469724973781352702"
    send_full_report: true
    
  conditions:
    on_p0_found: true      # 发现P0级候选人立即通知
    on_chinese_threshold: true  # 华人目标达成通知
    on_completion: true    # 任务完成通知
```

### 评估脚本模板

```python
# scripts/evaluate_candidate.py
def evaluate_candidate(candidate: dict) -> dict:
    """
    候选人评估标准 (基于成功经验)
    """
    score = 0.0
    reasons = []
    
    # AI专业度评估 (30%)
    ai_score = evaluate_ai_expertise(candidate)
    score += ai_score * 0.3
    
    # 无线通信专业度评估 (30%)
    wireless_score = evaluate_wireless_expertise(candidate)
    score += wireless_score * 0.3
    
    # 公司层级评估 (20%)
    company_score = evaluate_company_tier(candidate.get('company'))
    score += company_score * 0.2
    
    # 华人背景评估 (20%)
    chinese_score = evaluate_chinese_background(candidate)
    score += chinese_score * 0.2
    
    # 优先级分级
    if score >= 0.90:
        priority = "P0"
    elif score >= 0.80:
        priority = "P1"
    elif score >= 0.70:
        priority = "P2"
    else:
        priority = "P3"
    
    return {
        "match_score": round(score, 2),
        "priority": priority,
        "evaluation_reasons": reasons,
        "recommended_action": get_recommended_action(priority)
    }
```

---

## 监控指标

### 关键绩效指标 (KPI)

| 指标 | 当前 | 目标 | 监控频率 |
|------|------|------|---------|
| 每日候选人数 | 50 (模糊) | 20 (高质量) | 每日 |
| 华人识别率 | 未统计 | ≥40% | 每日 |
| P0级产出 | 0 | ≥3/日 | 每日 |
| 报告完整率 | 0% | 100% | 每日 |
| 匹配度≥0.75占比 | 未知 | ≥80% | 每周 |
| 去重准确率 | 未知 | ≥95% | 每月 |

### 告警规则

```yaml
alerts:
  - condition: "daily_chinese_count < 5"
    severity: warning
    message: "华人候选人数量低于预期"
    
  - condition: "p0_candidates == 0 for 3 days"
    severity: critical
    message: "连续3天无高优先级候选人"
    
  - condition: "avg_match_score < 0.70"
    severity: warning
    message: "平均匹配度低于阈值"
```

---

## 结语

**核心原则**: 从"数据收集"升级为"情报分析"

定时检索提供**广度**，人工深度检索提供**深度**。两者结合，构建完整的人才情报能力。

**下一步行动**: 选择 Phase 1 方案立即实施，验证效果后逐步推进。

---

**文档维护**: TalentIntel Team  
**更新周期**: 每月复盘更新
