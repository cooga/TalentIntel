# TalentIntel 架构设计文档

> **项目代号**: Sentinel  
> **版本**: v1.0  
> **日期**: 2026-03-01  
> **目标**: 开源情报（OSINT）持续监控与人才状态推断系统

---

## 1. 系统概述

### 1.1 核心目标

TalentIntel/Sentinel 是一个**无需 LinkedIn API** 的人才情报监控系统，通过多源开源数据（GitHub、Twitter/X、公开演讲、技术博客等）的持续监控，推断目标人物的职业状态变化、技术兴趣迁移、人际网络扩展等关键信号。

### 1.2 核心设计原则

| 原则 | 说明 |
|------|------|
| **差分优先** | 只监控和存储"变化点"，而非全量数据 |
| **信号推断** | 通过间接信号推断直接信息（如 LinkedIn 状态）|
| **低感知** | 避免高频主动抓取，采用被动监听和缓存策略 |
| **级联验证** | 单一信号不可信，多源交叉验证 |
| **基线学习** | 为每个人建立"正常行为模式"基线，异常即信号 |

### 1.3 系统边界

```
┌─────────────────────────────────────────────────────────────────┐
│                        TalentIntel/Sentinel                      │
├─────────────────────────────────────────────────────────────────┤
│  ✅ 包含                                                         │
│    - GitHub 公开数据监控（profile, commits, repos, orgs）        │
│    - Twitter/X 公开推文与互动分析                                 │
│    - LinkedIn 多源数据获取（见第3.6节）                          │
│    - 公开演讲、播客、技术博客内容提取                             │
│    - 多源身份关联与实体解析                                       │
│    - 状态变化推断与预警                                           │
│    - 知识图谱构建与时间线追踪                                     │
│                                                                 │
│  ⚠️ 有条件包含                                                   │
│    - LinkedIn 直接抓取（需要反检测策略和代理）                    │
│                                                                 │
│  ❌ 不包含                                                       │
│    - 私有数据获取（非公开档案、私信）                             │
│    - 主动社交工程或钓鱼                                          │
│    - 实时消息推送（采用批处理轮询）                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 架构总览

### 2.1 分层架构图

```
┌────────────────────────────────────────────────────────────────────┐
│                         应用层 (Application)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │   CLI 工具    │  │  API 服务    │  │     告警通知模块          │ │
│  │  (管理/查询)  │  │  (REST/gRPC) │  │  (Discord/邮件/ webhook) │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
├────────────────────────────────────────────────────────────────────┤
│                         核心引擎层 (Core Engine)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │   实体解析器  │  │   状态机引擎  │  │      置信度评分器         │ │
│  │ (Entity      │  │   (State     │  │   (Confidence Scorer)    │ │
│  │  Resolver)   │  │   Machine)   │  │                          │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
├────────────────────────────────────────────────────────────────────┤
│                         推断引擎层 (Inference)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │  共现分析     │  │  时间异常检测 │  │      代码取证分析         │ │
│  │ (Co-occurren-│  │  (Temporal   │  │   (Commit Forensics)     │ │
│  │  ce Analysis)│  │   Anomaly)   │  │                          │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐                                │
│  │  写作风格指纹 │  │  交叉验证引擎 │                                │
│  │  (Stylometry)│  │  (Cross-Ref) │                                │
│  └──────────────┘  └──────────────┘                                │
├────────────────────────────────────────────────────────────────────┤
│                         采集层 (Collectors)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   GitHub     │  │   Twitter/X  │  │   LinkedIn   │             │
│  │  采集器      │  │   采集器     │  │   采集器     │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│  ┌──────────────┐                                                  │
│  │  演讲/播客    │                                                  │
│  │   采集器     │                                                  │
│  └──────────────┘                                                  │
├────────────────────────────────────────────────────────────────────┤
│                         触发与调度层 (Triggers)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │  定时轮询     │  │  事件监听    │  │      级联检测器           │ │
│  │  (Scheduled) │  │  (Event-Driv-│  │   (Cascade Detector)     │ │
│  │              │  │   en)        │  │                          │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
├────────────────────────────────────────────────────────────────────┤
│                         存储层 (Storage)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │  实体数据库   │  │  知识图谱    │  │      时间线存储           │ │
│  │  (SQLite/    │  │  (NetworkX/  │  │   (Event Sourcing)       │ │
│  │   PostgreSQL)│  │   Neo4j)     │  │                          │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

```
                    ┌─────────────────────────────────────┐
                    │           目标人物注册               │
                    │  (Watchlist: github_user, twitter) │
                    └──────────────────┬──────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │          基线建立阶段               │
                    │  (2周静默观察，建立正常行为模式)      │
                    └──────────────────┬──────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
┌───────────────┐            ┌─────────────────┐            ┌───────────────┐
│  GitHub Events│            │ Twitter Timeline│            │ 其他数据源     │
│   API 轮询    │            │    监听         │            │ (演讲/博客)    │
└───────┬───────┘            └────────┬────────┘            └───────┬───────┘
        │                             │                             │
        └─────────────────────────────┼─────────────────────────────┘
                                      │
                    ┌─────────────────▼─────────────────┐
                    │           差分检测器               │
                    │  (比对上次的 snapshot，发现变化)    │
                    └─────────────────┬─────────────────┘
                                      │ 变化事件
                                      ▼
                    ┌─────────────────────────────────────┐
                    │           事件分类器                 │
                    │  [代码提交][社交互动][资料变更][内容] │
                    └──────────────────┬──────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
┌───────────────┐            ┌─────────────────┐            ┌───────────────┐
│  直接信号处理  │            │ 间接推断引擎     │            │  级联检测      │
│ (commit时间/  │            │ (共现/时序/风格) │            │ (关联人变化→  │
│  org变更)     │            │                 │            │  推断目标)     │
└───────┬───────┘            └────────┬────────┘            └───────┬───────┘
        │                             │                             │
        └─────────────────────────────┼─────────────────────────────┘
                                      │
                    ┌─────────────────▼─────────────────┐
                    │           置信度聚合               │
                    │  (多信号加权，生成 0-1 置信度分数)  │
                    └─────────────────┬─────────────────┘
                                      │
                    ┌─────────────────▼─────────────────┐
                    │           状态机更新               │
                    │  [在职][观望][面试][交接][入职]    │
                    └─────────────────┬─────────────────┘
                                      │
                    ┌─────────────────▼─────────────────┐
                    │           告警决策                 │
                    │  (阈值判断 + 去重 + 优先级排序)     │
                    └─────────────────┬─────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │           通知输出                   │
                    │  (Discord / 日志 / API callback)    │
                    └─────────────────────────────────────┘
```

---

## 3. 核心模块详解

### 3.1 实体解析与身份关联 (Entity Resolution)

**目标**: 将分散在多个平台的碎片化信息关联到同一个真实人物。

#### 3.1.1 身份指纹系统

```python
class IdentityFingerprint:
    """
    跨平台身份关联的多维指纹
    """
    
    # 硬匹配特征（高置信度）
    hard_signals = {
        'email_hash': '邮箱的 SHA256 哈希',
        'website_domain': '个人网站域名',
        'cross_links': '平台间互链（GitHub bio 中的 Twitter 链接）',
        'username_exact': '用户名完全一致'
    }
    
    # 软匹配特征（需组合验证）
    soft_signals = {
        'username_variants': '用户名变体（johndoe, john-doe, jdoe）',
        'avatar_phash': '头像感知哈希相似度',
        'name_similarity': '显示名称相似度',
        'location': '地理位置一致性',
        'bio_keywords': '个人简介关键词重叠'
    }
    
    # 行为特征（长期验证）
    behavioral_signals = {
        'writing_style_vector': '写作风格嵌入向量',
        'active_hours': '活跃时间分布',
        'tech_stack': '技术栈重叠',
        'mention_network': '被提及/互动的共同人群'
    }
```

#### 3.1.2 用户名变体生成器

```python
def generate_username_variants(base_name: str) -> List[str]:
    """
    生成可能的用户名变体
    
    Example: "john doe" → 
        - johndoe
        - john-doe
        - john_doe
        - jdoe
        - doejohn
        - johnd
        - johndoe123
    """
    variants = set()
    
    # 基础变体
    clean = base_name.lower().replace(' ', '')
    variants.add(clean)
    variants.add(clean.replace(' ', '-'))
    variants.add(clean.replace(' ', '_'))
    
    # 缩写变体
    parts = base_name.lower().split()
    if len(parts) >= 2:
        variants.add(parts[0][0] + parts[1])  # jdoe
        variants.add(parts[0] + parts[1][0])  # johnd
        variants.add(parts[1] + parts[0])     # doejohn
    
    # 常见后缀
    for v in list(variants):
        for suffix in ['', '123', 'dev', 'io', 'hq']:
            variants.add(v + suffix)
    
    return list(variants)
```

#### 3.1.3 置信度评分算法

```python
def calculate_identity_match_score(signals: dict) -> float:
    """
    多信号加权置信度评分
    
    权重设计原则：
    - 硬信号：高权重，单一即可确认
    - 软信号：中等权重，需组合
    - 行为信号：低权重，长期验证
    """
    weights = {
        'email_match': 0.95,
        'cross_link_verified': 0.90,
        'website_match': 0.85,
        'username_exact': 0.80,
        'avatar_similarity': 0.70,  # >90% 相似度
        'name_similarity': 0.60,    # Levenshtein 距离
        'location_match': 0.50,
        'writing_style_cosine': 0.40,  # 余弦相似度
        'mention_overlap': 0.35
    }
    
    # 加权计算
    score = 0.0
    total_weight = 0.0
    
    for signal, value in signals.items():
        if signal in weights and value:
            weight = weights[signal]
            if isinstance(value, bool):
                score += weight
            elif isinstance(value, float):  # 相似度分数
                score += weight * value
            total_weight += weight
    
    # 归一化
    return min(score / total_weight * len(signals), 1.0) if total_weight > 0 else 0.0
```

---

### 3.2 状态机引擎 (State Machine)

**目标**: 将离散的信号转化为连续的、可解释的职业状态。

#### 3.2.1 职业状态定义

```python
from enum import Enum, auto

class CareerState(Enum):
    """人才职业状态枚举"""
    
    # 稳定期
    STABLE = auto()           # 在职稳定，无异常信号
    
    # 观察期
    OBSERVING = auto()        # 出现少量异常信号，值得观察
    
    # 活跃期
    JOB_HUNTING = auto()      # 明显求职信号（更新简历、关注招聘）
    INTERVIEWING = auto()     # 面试阶段（时间异常、关注目标公司员工）
    
    # 过渡期
    HANDING_OVER = auto()     # 交接期（commit 风格变化、清理文档）
    
    # 转换完成
    TRANSITIONED = auto()     # 已确认入职新公司
    
    # 特殊状态
    STARTUP_READY = auto()    # 可能准备创业（关注投资人、频繁参会）
    SABBATICAL = auto()       # 可能休假/间隔年（全面静默）
    UNKNOWN = auto()          # 信息不足
```

#### 3.2.2 状态转换图

```
                    ┌─────────────┐
         ┌──────────│   STABLE    │◄────────────┐
         │          │  (在职稳定)  │             │
         │          └──────┬──────┘             │
         │                 │ 异常信号            │
         │                 ▼                    │
         │          ┌─────────────┐             │
         │          │  OBSERVING  │             │
         │          │  (观察期)   │             │
         │          └──────┬──────┘             │
         │                 │
         │    ┌────────────┼────────────┐
         │    │            │            │
         ▼    ▼            ▼            ▼
    ┌─────────┐    ┌─────────────┐   ┌─────────────┐
    │JOB_HUNT-│    │ STARTUP_    │   │  SABBATI-   │
    │  ING    │    │   READY     │   │   CAL       │
    │ (求职)  │    │ (准备创业)   │   │  (休假)     │
    └────┬────┘    └─────────────┘   └─────────────┘
         │
         │ 关注目标公司员工
         ▼
    ┌─────────┐
    │ INTERV- │
    │  IEWING │
    │ (面试期) │
    └────┬────┘
         │
         │ commit 风格变化
         ▼
    ┌─────────┐
    │ HANDING │
    │  _OVER  │
    │ (交接期) │
    └────┬────┘
         │
         │ 官宣/确认
         ▼
    ┌─────────┐
    │ TRANSIT-│◄──────────────────────────────────┐
    │  IONED  │                                   │
    │ (已入职) │                                   │
    └─────────┘                                   │
                                                  │
                                                  │ (新工作稳定后)
                                                  │
                                                  │
```

#### 3.2.3 状态推断规则引擎

```python
class StateInferenceEngine:
    """
    基于信号组合的状态推断
    """
    
    INFERENCE_RULES = [
        # 规则1: 关注招聘相关账号 + 更新 GitHub profile
        {
            'name': 'job_hunting_signal_1',
            'conditions': [
                'new_follows_include_hr_accounts',
                'github_profile_updated_recently',
                'tweet_contains_job_keywords'
            ],
            'state': CareerState.JOB_HUNTING,
            'confidence': 0.75
        },
        
        # 规则2: 时间异常 + 关注目标公司员工
        {
            'name': 'interviewing_signal_1',
            'conditions': [
                'commit_pattern_anomaly_detected',
                'new_follows_target_company_employees',
                'weekday_activity_drop > 30%'
            ],
            'state': CareerState.INTERVIEWING,
            'confidence': 0.80
        },
        
        # 规则3: 提交风格变化（交接信号）
        {
            'name': 'handover_signal_1',
            'conditions': [
                'commit_messages_contain_handover_keywords',
                'documentation_commits_surge',
                'code_deletion_ratio_high'
            ],
            'state': CareerState.HANDING_OVER,
            'confidence': 0.70
        },
        
        # 规则4: 组织变更确认
        {
            'name': 'transition_confirmed',
            'conditions': [
                'github_org_changed',
                'twitter_bio_company_updated',
                'announcement_post_detected'
            ],
            'state': CareerState.TRANSITIONED,
            'confidence': 0.95
        }
    ]
    
    def evaluate_rules(self, signals: dict) -> List[StatePrediction]:
        """评估所有规则，返回可能的状态预测"""
        predictions = []
        
        for rule in self.INFERENCE_RULES:
            matched_conditions = sum(
                1 for cond in rule['conditions'] if signals.get(cond, False)
            )
            coverage = matched_conditions / len(rule['conditions'])
            
            if coverage >= 0.5:  # 至少50%条件匹配
                predictions.append(StatePrediction(
                    state=rule['state'],
                    confidence=rule['confidence'] * coverage,
                    matched_conditions=matched_conditions,
                    rule_name=rule['name']
                ))
        
        return sorted(predictions, key=lambda p: p.confidence, reverse=True)
```

---

### 3.3 推断引擎 (Inference Engine)

**目标**: 从看似无关的信号中推断出隐藏的状态变化。

#### 3.3.1 时间异常检测 (Temporal Anomaly Detection)

```python
class TemporalAnalyzer:
    """
    通过时间模式变化推断状态
    """
    
    def __init__(self, baseline_days: int = 14):
        self.baseline_days = baseline_days
    
    def analyze_commit_patterns(self, commits: List[Commit]) -> AnomalyReport:
        """
        分析代码提交时间模式的变化
        
        正常模式: 工作日 9-18 点集中
        异常信号:
        - 分散到全天 → 可能弹性工作/面试请假
        - 周末骤减 → 可能忙于面试准备
        - 深夜增加 → 可能交接期加班
        """
        
        # 计算时间分布特征
        hourly_distribution = self._calculate_hourly_distribution(commits)
        weekday_ratio = self._calculate_weekday_ratio(commits)
        
        # 与基线对比
        baseline = self._get_baseline()
        
        anomalies = []
        
        # 检测1: 工作日活跃度下降
        if weekday_ratio < baseline.weekday_ratio * 0.7:
            anomalies.append(Anomaly(
                type='weekday_activity_drop',
                severity='high' if weekday_ratio < 0.5 else 'medium',
                description=f'工作日活跃度下降 {(1-weekday_ratio/baseline.weekday_ratio)*100:.0f}%'
            ))
        
        # 检测2: 时间分布离散度增加
        current_entropy = self._calculate_time_entropy(hourly_distribution)
        if current_entropy > baseline.entropy * 1.5:
            anomalies.append(Anomaly(
                type='dispersed_activity',
                severity='medium',
                description='活动时间分布变得分散，可能弹性办公或请假'
            ))
        
        # 检测3: 深夜提交激增
        late_night_ratio = self._calculate_late_night_ratio(commits)
        if late_night_ratio > baseline.late_night_ratio * 2:
            anomalies.append(Anomaly(
                type='late_night_surge',
                severity='low',
                description='深夜提交增加，可能处于项目收尾/交接期'
            ))
        
        return AnomalyReport(anomalies=anomalies)
```

#### 3.3.2 共现网络分析 (Co-occurrence Analysis)

```python
class CooccurrenceAnalyzer:
    """
    通过社交共现推断职业关系
    
    核心假设：
    - 频繁同时出现在某公司的员工互动中 → 可能已入职/面试
    - 突然开始与某投资人频繁互动 → 可能准备创业
    - 与前同事互动减少 → 可能已离职
    """
    
    def analyze_social_proximity(
        self, 
        target: Entity, 
        reference_group: List[Entity],
        window_days: int = 30
    ) -> ProximityReport:
        """
        分析目标与参考群体的社交接近度变化
        """
        
        # 获取历史互动数据
        historical = self._get_interactions(target, days=90)  # 基线期
        recent = self._get_interactions(target, days=window_days)  # 近期
        
        # 计算与参考群体的互动比例
        historical_ratio = self._calculate_group_ratio(historical, reference_group)
        recent_ratio = self._calculate_group_ratio(recent, reference_group)
        
        change = recent_ratio - historical_ratio
        
        signals = []
        
        if change > 0.3:  # 互动比例增加30%以上
            signals.append(SocialSignal(
                type='increased_company_proximity',
                target_company=reference_group[0].company,
                confidence=min(change + 0.5, 0.95),
                evidence=f'与该公司员工互动比例从 {historical_ratio:.1%} 增至 {recent_ratio:.1%}'
            ))
        
        return ProximityReport(signals=signals, change_ratio=change)
```

#### 3.3.3 代码提交取证 (Commit Forensics)

```python
class CommitForensics:
    """
    从代码提交记录中提取职业状态信号
    """
    
    # 交接期关键词
    HANDOVER_KEYWORDS = [
        'cleanup', 'clean up', 'refactor', 'document',
        'readme', 'handover', 'hand over', 'transfer',
        'deprecate', 'archive', 'finalize'
    ]
    
    # 求职准备期关键词
    PREPARATION_KEYWORDS = [
        'portfolio', 'demo', 'showcase', 'resume',
        'blog', 'article', 'tutorial', 'talk'
    ]
    
    def analyze_commit_messages(self, commits: List[Commit]) -> ForensicsReport:
        """分析提交消息中的信号词"""
        
        handover_commits = []
        prep_commits = []
        
        for commit in commits:
            msg = commit.message.lower()
            
            if any(kw in msg for kw in self.HANDOVER_KEYWORDS):
                handover_commits.append(commit)
            
            if any(kw in msg for kw in self.PREPARATION_KEYWORDS):
                prep_commits.append(commit)
        
        signals = []
        
        # 交接信号
        if len(handover_commits) >= 3:  # 至少3个相关提交
            signals.append(CommitSignal(
                type='handover_preparation',
                confidence=min(len(handover_commits) * 0.15, 0.85),
                evidence=f'最近发现 {len(handover_commits)} 个交接相关提交'
            ))
        
        # 个人品牌建设信号
        if len(prep_commits) >= 2:
            signals.append(CommitSignal(
                type='personal_brand_building',
                confidence=min(len(prep_commits) * 0.2, 0.75),
                evidence=f'最近有 {len(prep_commits)} 个与内容建设相关的提交'
            ))
        
        return ForensicsReport(signals=signals)
    
    def analyze_code_churn(self, commits: List[Commit]) -> ChurnReport:
        """
        分析代码增删模式
        
        高删除率 + 文档提交 = 可能的交接
        """
        total_additions = sum(c.additions for c in commits)
        total_deletions = sum(c.deletions for c in commits)
        
        if total_additions == 0:
            deletion_ratio = 1.0
        else:
            deletion_ratio = total_deletions / (total_additions + total_deletions)
        
        if deletion_ratio > 0.7:  # 70%以上是删除
            return ChurnReport(
                signal='high_deletion_ratio',
                confidence=0.65,
                ratio=deletion_ratio,
                interpretation='高代码删除率，可能在进行清理/交接'
            )
        
        return None
```

---

### 3.4 触发与调度系统 (Trigger System)

**目标**: 平衡监控实时性与反爬/限流风险。

#### 3.4.1 分层监控频率

```python
class MonitoringScheduler:
    """
    分层监控调度器
    
    设计原则：
    - 高频信号：事件驱动，Webhook/RSS
    - 中频信号：定时轮询，指数退避
    - 低频信号：每日/每周批量
    """
    
    SCHEDULE_CONFIG = {
        # 高频：事件驱动或短轮询
        'github_events': {
            'type': 'polling',
            'interval_minutes': 30,
            'priority': 'high',
            'method': 'ETag_conditional'  # 使用 ETag 避免重复请求
        },
        
        'twitter_timeline': {
            'type': 'polling',
            'interval_minutes': 60,
            'priority': 'high',
            'backoff_strategy': 'exponential'  # 限流时指数退避
        },
        
        # 中频：定时轮询
        'profile_metadata': {
            'type': 'polling',
            'interval_hours': 6,
            'priority': 'medium'
        },
        
        'following_list': {
            'type': 'polling',
            'interval_hours': 12,
            'priority': 'medium'
        },
        
        # 低频：批量分析
        'deep_network_analysis': {
            'type': 'batch',
            'schedule': '0 2 * * 0',  # 每周日凌晨2点
            'priority': 'low'
        },
        
        'baseline_update': {
            'type': 'batch',
            'schedule': '0 4 * * 1',  # 每周一凌晨4点
            'priority': 'low'
        }
    }
```

#### 3.4.2 级联触发器 (Cascade Triggers)

```python
class CascadeTrigger:
    """
    级联触发器：一个信号触发深度检查
    
    示例流程：
    1. 目标发推"今天去山景城出差"
    2. 触发器激活 → 检查最近关注列表
    3. 发现新增关注 Google 员工
    4. 触发深度模式 → 检查 GitHub commit 时间
    5. 发现工作日提交减少
    6. 综合推断：正在 Google 面试
    """
    
    TRIGGER_MAP = {
        'tweet_location': {
            'keywords': ['山景城', 'Menlo Park', '西雅图', '面试', 'onsite'],
            'cascade_actions': [
                'check_recent_follows',
                'analyze_commit_pattern_last_7d',
                'search_cooccurrence_in_photos'
            ]
        },
        
        'github_org_change': {
            'cascade_actions': [
                'verify_twitter_bio_update',
                'check_announcement_post',
                'update_career_timeline'
            ]
        },
        
        'new_follows_surge': {
            'threshold': 5,  # 一周内新增关注超过5人
            'cascade_actions': [
                'analyze_new_follows_affiliation',
                'check_mutual_connections',
                'update_relation_graph'
            ]
        }
    }
```

---

### 3.5 知识图谱与时间线 (Knowledge Graph & Timeline)

#### 3.5.1 实体关系图谱

```python
class TalentKnowledgeGraph:
    """
    人才情报知识图谱
    
    节点类型:
    - Person: 目标人物
    - Company: 公司/组织
    - Technology: 技术栈
    - Project: 项目/仓库
    - Event: 事件（演讲、发布）
    - Content: 内容（文章、推文）
    
    边类型:
    - WORKS_AT: 任职关系（带时间范围）
    - FOLLOWS: 关注关系
    - CONTRIBUTES_TO: 贡献关系
    - MENTIONS: 提及关系
    - CO_OCCURS: 共现关系
    - SIMILAR_TO: 相似关系
    """
    
    def add_person(self, person: Person) -> Node:
        """添加人物节点"""
        return self.graph.add_node(
            id=person.id,
            type='Person',
            properties={
                'name': person.name,
                'github_username': person.github,
                'twitter_handle': person.twitter,
                'current_company': person.company,
                'current_state': person.state.value,
                'state_confidence': person.state_confidence,
                'last_updated': person.last_updated
            }
        )
    
    def add_work_relation(self, person: Node, company: Node, 
                         start_date: date, end_date: date = None):
        """添加任职关系（支持时间范围）"""
        return self.graph.add_edge(
            from_node=person,
            to_node=company,
            type='WORKS_AT',
            properties={
                'start_date': start_date,
                'end_date': end_date,
                'is_current': end_date is None,
                'confidence': self._calculate_confidence()
            }
        )
```

#### 3.5.2 事件溯源时间线

```python
class EventSourcedTimeline:
    """
    事件溯源模式的时间线存储
    
    优点：
    - 完整历史可追溯
    - 支持状态回溯
    - 便于审计和验证
    """
    
    class EventType(Enum):
        PROFILE_UPDATED = auto()
        COMMIT_CREATED = auto()
        TWEET_POSTED = auto()
        FOLLOW_ADDED = auto()
        STATE_CHANGED = auto()
        RELATION_DETECTED = auto()
        ALERT_TRIGGERED = auto()
    
    def append_event(self, entity_id: str, event_type: EventType,
                    payload: dict, timestamp: datetime = None):
        """
        追加事件到时间线
        
        事件结构:
        {
            'event_id': 'uuid',
            'entity_id': 'person_123',
            'event_type': 'STATE_CHANGED',
            'timestamp': '2024-01-15T10:30:00Z',
            'payload': {
                'from_state': 'STABLE',
                'to_state': 'INTERVIEWING',
                'confidence': 0.82,
                'triggering_signals': [...]
            },
            'version': 1
        }
        """
        event = {
            'event_id': str(uuid.uuid4()),
            'entity_id': entity_id,
            'event_type': event_type.value,
            'timestamp': timestamp or datetime.utcnow(),
            'payload': payload,
            'version': self._get_next_version(entity_id)
        }
        
        self.event_store.append(event)
        self._update_projection(entity_id, event)
        
        return event
```

---


---

## 3.6 LinkedIn 数据获取策略 (LinkedIn Acquisition)

**重要说明**: LinkedIn 拥有业界最严格的反爬机制，包括动态渲染、行为指纹检测、IP 风控等。本节介绍多层级数据获取策略，从低风险到高覆盖。

### 3.6.1 策略分层架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LinkedIn 数据获取策略                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Tier 1: 零风险层 (间接获取)                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  • 搜索引擎缓存 (Google Cache)                                │  │
│  │  • 第三方聚合服务 API (Proxycurl, RocketReach)                │  │
│  │  • 公开分享链接 (Open to Work 徽章, 公开档案)                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          ↓ 数据补充                                 │
│  Tier 2: 低风险层 (匿名获取)                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  • 无头浏览器 + 代理池 (住宅 IP 轮换)                         │  │
│  │  • 反指纹技术 (undetected-chromedriver, playwright-stealth)   │  │
│  │  • 人机行为模拟 (随机延迟、鼠标轨迹)                          │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          ↓ 深度数据                                 │
│  Tier 3: 高覆盖层 (认证获取)                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  • 可信账号池 (真实用户账号轮换)                              │  │
│  │  • 会话保持 (Cookie 持久化、登录态维护)                       │  │
│  │  • 请求频率控制 (行为模式模拟)                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.6.2 零风险层：第三方聚合服务

**推荐服务对比:**

| 服务 | 定价 | 优势 | 劣势 | 适用场景 |
|------|------|------|------|----------|
| **Proxycurl** | $0.01-0.02/请求 | 数据完整、API稳定、反爬处理完善 | 付费、无历史数据 | 批量档案获取 |
| **RocketReach** | 订阅制 | 联系信息丰富、企业数据完善 | 较贵、LinkedIn占比有限 | 高管/销售线索 |
| **Nubela** | 免费+付费 | 有免费额度、实时性好 | 覆盖率低 | 小规模测试 |
| **SerpAPI** | 按量计费 | 搜索引擎整合、多源数据 | 依赖Google索引 | 补充验证 |
| **PeopleDataLabs** | $0.10/记录 | 多源聚合、数据清洗好 | 价格较高 | 数据富化 |

**实现示例:**

```python
class ProxycurlAdapter:
    """
    Proxycurl API 适配器
    用于获取 LinkedIn 公开档案数据
    """
    
    API_BASE = "https://nubela.co/proxycurl/api/v2"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}'
        })
    
    async def get_profile(self, linkedin_url: str) -> Profile:
        """
        获取 LinkedIn 档案
        
        返回字段:
        - 基本信息: name, headline, location
        - 工作经历: experiences (company, title, start_date, end_date)
        - 教育背景: education
        - 技能: skills
        - 最近活动: articles, activities
        """
        url = f"{self.API_BASE}/linkedin"
        params = {
            'linkedin_profile_url': linkedin_url,
            'use_cache': 'if-recent'  # 优先使用缓存
        }
        
        response = await self._make_request(url, params)
        return self._parse_profile(response)
```

### 3.6.3 低风险层：反检测浏览器采集

**技术栈:**

```python
class StealthLinkedInCollector:
    """
    反检测 LinkedIn 采集器
    
    核心技术:
    1. undetected-chromedriver: 绕过基本 bot 检测
    2. 住宅代理轮换: 避免 IP 封禁
    3. 行为指纹伪装: 模拟真实用户
    """
    
    def __init__(self, proxy_pool: ProxyPool):
        self.proxy_pool = proxy_pool
        self.driver_config = {
            'headless': True,
            'use_subprocess': True,
            'window_size': (1920, 1080),
            'user_agent_rotation': True
        }
    
    def _create_stealth_driver(self) -> WebDriver:
        """创建反检测浏览器实例"""
        import undetected_chromedriver as uc
        
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # 代理配置
        proxy = self.proxy_pool.get_residential_proxy()
        options.add_argument(f'--proxy-server={proxy}')
        
        driver = uc.Chrome(options=options, **self.driver_config)
        
        # 注入反指纹脚本
        self._inject_stealth_scripts(driver)
        
        return driver
```

### 3.6.4 数据提取与清洗

**LinkedIn 特有字段映射:**

```python
class LinkedInDataExtractor:
    """
    LinkedIn 数据提取与标准化
    """
    
    def detect_job_change_signals(self, profile: Profile) -> List[Signal]:
        """
        从 LinkedIn 数据检测职业变动信号
        
        信号类型:
        1. Open to Work 徽章激活
        2. Headline 变化（如添加"Seeking new opportunities"）
        3. 近期频繁更新 profile
        4. 新增大量技能
        5. 活跃度突然增加
        """
        signals = []
        
        # 检测 Open to Work
        if profile.open_to_work:
            signals.append(Signal(
                type='linkedin_open_to_work',
                confidence=0.95,
                description='已激活 Open to Work 徽章',
                source='linkedin'
            ))
        
        # 检测 Headline 求职关键词
        job_keywords = ['seeking', 'open to', 'available for', 'looking for']
        if any(kw in profile.headline.lower() for kw in job_keywords):
            signals.append(Signal(
                type='linkedin_headline_job_seeking',
                confidence=0.85,
                description=f'Headline 包含求职关键词',
                source='linkedin'
            ))
        
        return signals
```

### 3.6.5 风险与合规

| 风险 | 缓解措施 |
|------|----------|
| IP 封禁 | 住宅代理轮换、请求频率限制、异常检测后退避 |
| 账号封禁 | 多账号池、分级使用、冷启动策略 |
| 法律风险 | 仅采集公开数据、遵守 robots.txt、数据最小化原则 |
| 数据质量 | 多源交叉验证、置信度评分、人工抽样审核 |

**使用优先级建议:**

1. **首选**: 第三方聚合 API（Proxycurl 等）- 稳定、合法
2. **补充**: 搜索引擎缓存 - 免费、零风险
3. **深度**: 反检测采集 - 需代理投资、技术维护
4. **最后手段**: 可信账号池 - 高风险、需持续维护


---

## 4. 数据存储设计

### 4.1 数据库选型

| 存储类型 | 选型 | 用途 |
|---------|------|------|
| **主数据库** | SQLite (单用户) / PostgreSQL (多用户) | 实体数据、配置、事件日志 |
| **图数据库** | NetworkX (内存) / Neo4j (生产) | 关系图谱、网络分析 |
| **时序数据** | InfluxDB (可选) / PostgreSQL + TimescaleDB | 监控指标、状态变化趋势 |
| **缓存** | 文件系统 / Redis | API 响应缓存、ETag |
| **向量存储** | FAISS / Chroma | 写作风格嵌入、相似度搜索 |

### 4.2 核心数据模型

```sql
-- 人物实体表
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 平台账号
    github_username TEXT UNIQUE,
    twitter_handle TEXT UNIQUE,
    personal_website TEXT,
    
    -- 当前状态
    current_state TEXT,
    state_confidence REAL,
    state_updated_at TIMESTAMP,
    
    -- 当前任职
    current_company TEXT,
    current_title TEXT,
    
    -- 基线数据
    baseline_commit_pattern TEXT,  -- JSON
    baseline_active_hours TEXT,    -- JSON
    
    -- 元数据
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 5,  -- 1-10, 越高越优先监控
    tags TEXT  -- JSON array
);

-- 平台快照表（差分存储）
CREATE TABLE platform_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT REFERENCES entities(id),
    platform TEXT,  -- github, twitter, etc.
    snapshot_hash TEXT,  -- 用于快速比对
    snapshot_data TEXT,  -- JSON 完整数据
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_entity_platform_time (entity_id, platform, captured_at)
);

-- 事件日志表（事件溯源）
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE,
    entity_id TEXT REFERENCES entities(id),
    event_type TEXT,
    timestamp TIMESTAMP,
    payload TEXT,  -- JSON
    version INTEGER,
    
    INDEX idx_entity_time (entity_id, timestamp),
    INDEX idx_type_time (event_type, timestamp)
);

-- 关系表
CREATE TABLE relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_entity TEXT REFERENCES entities(id),
    to_entity TEXT REFERENCES entities(id),
    relation_type TEXT,  -- WORKS_AT, FOLLOWS, MENTIONS, etc.
    confidence REAL,
    evidence TEXT,  -- JSON
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_from_type (from_entity, relation_type),
    INDEX idx_to_type (to_entity, relation_type)
);

-- 信号检测表
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT REFERENCES entities(id),
    signal_type TEXT,
    confidence REAL,
    source_platform TEXT,
    source_data TEXT,  -- JSON
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_processed BOOLEAN DEFAULT FALSE,
    
    INDEX idx_entity_processed (entity_id, is_processed),
    INDEX idx_detected_time (detected_at)
);

-- 告警表
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT REFERENCES entities(id),
    alert_type TEXT,
    severity TEXT,  -- low, medium, high, critical
    title TEXT,
    description TEXT,
    confidence REAL,
    evidence TEXT,  -- JSON
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    acknowledged_by TEXT,
    
    INDEX idx_entity_severity (entity_id, severity),
    INDEX idx_triggered (triggered_at)
);
```

---

## 5. API 设计

### 5.1 RESTful API 概览

```
/api/v1/
├── entities/              # 人才实体管理
│   ├── GET    /          # 列出所有监控目标
│   ├── POST   /          # 添加新目标
│   ├── GET    /{id}      # 获取目标详情
│   ├── PUT    /{id}      # 更新目标信息
│   ├── DELETE /{id}      # 移除监控目标
│   └── GET    /{id}/timeline  # 获取时间线
│
├── signals/               # 信号查询
│   ├── GET    /          # 列出检测到的信号
│   └── GET    /{id}      # 获取信号详情
│
├── alerts/                # 告警管理
│   ├── GET    /          # 列出告警
│   ├── GET    /{id}      # 获取告警详情
│   └── POST   /{id}/ack  # 确认告警
│
├── analysis/              # 分析接口
│   ├── GET    /network/{id}   # 获取关系网络
│   ├── GET    /state/{id}     # 获取状态推断
│   └── POST   /infer          # 手动触发推断
│
└── admin/                 # 管理接口
    ├── GET    /health         # 健康检查
    ├── GET    /stats          # 系统统计
    └── POST   /trigger/{job}  # 手动触发任务
```

### 5.2 核心 API 示例

**添加监控目标:**
```http
POST /api/v1/entities/
Content-Type: application/json

{
  "name": "John Doe",
  "github_username": "johndoe",
  "twitter_handle": "johndoe_dev",
  "personal_website": "https://johndoe.dev",
  "tags": ["ai", "distributed-systems"],
  "priority": 8
}

Response:
{
  "id": "ent_123456",
  "name": "John Doe",
  "status": "created",
  "baseline_established": false,
  "monitoring_started_at": "2024-01-15T10:30:00Z",
  "next_check_at": "2024-01-15T11:00:00Z"
}
```

**获取状态推断:**
```http
GET /api/v1/analysis/state/ent_123456

Response:
{
  "entity_id": "ent_123456",
  "current_state": "INTERVIEWING",
  "confidence": 0.82,
  "state_updated_at": "2024-01-20T14:22:00Z",
  "signals": [
    {
      "type": "commit_pattern_anomaly",
      "confidence": 0.75,
      "description": "工作日提交减少 40%"
    },
    {
      "type": "increased_company_proximity",
      "confidence": 0.88,
      "description": "与 Google 员工互动增加 300%"
    }
  ],
  "possible_next_states": [
    {"state": "HANDING_OVER", "probability": 0.45},
    {"state": "STABLE", "probability": 0.30}
  ]
}
```

---

## 6. 安全与合规

### 6.1 数据采集边界

| 行为 | 是否允许 | 说明 |
|------|---------|------|
| 抓取公开 GitHub profile | ✅ 允许 | 完全公开数据 |
| 抓取公开 Twitter 推文 | ✅ 允许 | 公开账号的公开内容 |
| 抓取公开演讲幻灯片 | ✅ 允许 | 公开分享的资料 |
| 抓取 LinkedIn 非公开档案 | ❌ 禁止 | 违反 ToS |
| 尝试登录他人账号 | ❌ 禁止 | 违法行为 |
| 社工或钓鱼 | ❌ 禁止 | 违法行为 |
| 购买第三方数据 | ⚠️ 谨慎 | 需验证数据来源合法性 |

### 6.2 技术防护措施

```python
class RateLimiter:
    """
    速率限制器，避免触发平台风控
    """
    
    # 各平台限制配置
    LIMITS = {
        'github': {
            'requests_per_hour': 5000,  # 认证用户
            'burst_limit': 100,
            'retry_after_header': True
        },
        'twitter': {
            'requests_per_15min': 450,  # API v2
            'burst_limit': 50,
            'exponential_backoff': True
        }
    }
    
    def __init__(self, platform: str):
        self.platform = platform
        self.config = self.LIMITS[platform]
        self.request_history = deque(maxlen=1000)
    
    async def acquire(self):
        """获取执行许可"""
        now = time.time()
        
        # 清理过期记录
        cutoff = now - 3600  # 1小时
        while self.request_history and self.request_history[0] < cutoff:
            self.request_history.popleft()
        
        # 检查限制
        if len(self.request_history) >= self.config['requests_per_hour']:
            wait_time = 3600 - (now - self.request_history[0])
            logger.warning(f"Rate limit reached, waiting {wait_time}s")
            await asyncio.sleep(wait_time)
        
        self.request_history.append(now)
```

### 6.3 数据保留策略

- **原始 API 响应**: 保留 7 天，用于调试和审计
- **差分快照**: 保留 90 天
- **事件日志**: 永久保留
- **关系图谱**: 定期归档历史版本

---

## 7. 部署与运维

### 7.1 部署架构

```
┌─────────────────────────────────────────────────────────┐
│                     生产环境部署                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐      ┌─────────────────────┐      │
│  │   Nginx 反向代理 │◄────►│  TalentIntel API    │      │
│  │   (SSL/TLS)     │      │  (FastAPI/uvicorn)  │      │
│  └─────────────────┘      └─────────────────────┘      │
│                                    │                    │
│                                    ▼                    │
│                          ┌─────────────────────┐       │
│                          │   任务调度器         │       │
│                          │  (APScheduler/      │       │
│                          │   Celery Beat)      │       │
│                          └─────────────────────┘       │
│                                    │                    │
│                    ┌───────────────┼───────────────┐   │
│                    ▼               ▼               ▼   │
│           ┌────────────┐  ┌────────────┐  ┌──────────┐ │
│           │ 工作队列   │  │  事件队列  │  │ 通知队列 │ │
│           │ (Celery)   │  │  (Redis)   │  │ (Celery) │ │
│           └────────────┘  └────────────┘  └──────────┘ │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                  数据层                              │ │
│  │  PostgreSQL (主库)  Redis (缓存)  Neo4j (图谱)     │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 7.2 配置管理

```yaml
# config/production.yaml

app:
  name: TalentIntel
  version: 1.0.0
  debug: false
  log_level: INFO

database:
  url: ${DATABASE_URL}
  pool_size: 10
  max_overflow: 20

redis:
  url: ${REDIS_URL}
  
monitoring:
  # 全局监控配置
  github:
    token: ${GITHUB_TOKEN}
    requests_per_hour: 4000  # 保守策略
    
  twitter:
    bearer_token: ${TWITTER_BEARER_TOKEN}
    requests_per_15min: 400
    
  # 调度配置
  schedules:
    github_events: "*/30 * * * *"      # 每30分钟
    twitter_timeline: "0 * * * *"       # 每小时
    profile_metadata: "0 */6 * * *"     # 每6小时
    deep_analysis: "0 2 * * 0"          # 每周日

# 告警配置
alerts:
  discord:
    webhook_url: ${DISCORD_WEBHOOK_URL}
    min_severity: medium
  
  email:
    smtp_host: ${SMTP_HOST}
    smtp_port: 587
    username: ${SMTP_USER}
    password: ${SMTP_PASS}
    to_address: ${ALERT_EMAIL}

# 状态机阈值
state_machine:
  min_confidence_for_alert: 0.70
  require_multiple_signals: true
  
# 身份关联阈值
entity_resolution:
  min_match_score: 0.75
  require_hard_signal: true
```

---

## 8. 路线图

### Phase 1: MVP (2-3 周)

- [x] 架构设计文档
- [ ] 核心数据模型与数据库
- [ ] GitHub 差分监控模块
- [ ] Twitter 基础监听
- [ ] 实体解析（硬匹配）
- [ ] CLI 工具（添加/查看目标）
- [ ] Discord 告警通知

### Phase 2: 推断引擎 (2-3 周)

- [ ] 时间异常检测
- [ ] 提交取证分析
- [ ] 状态机引擎
- [ ] 共现网络分析
- [ ] 基线自动学习
- [ ] 关系图谱可视化

### Phase 3: 智能化 (3-4 周)

- [ ] 写作风格指纹
- [ ] 级联触发器
- [ ] 置信度评分优化
- [ ] 预测模型（下一步状态）
- [ ] API 服务
- [ ] Web 仪表板

### Phase 4: 规模化 (持续)

- [ ] 多实例部署
- [ ] 分布式任务队列
- [ ] 高级反检测策略
- [ ] 自动化报告生成
- [ ] 与现有 TalentScout 系统集成

---

## 9. 附录

### 9.1 术语表

| 术语 | 定义 |
|------|------|
| **OSINT** | Open Source Intelligence，开源情报 |
| **Entity Resolution** | 实体解析，将多源碎片化信息关联到同一实体 |
| **Differential Monitoring** | 差分监控，只关注变化点而非全量数据 |
| **Baseline** | 基线，目标人物的正常行为模式 |
| **ETag** | HTTP 缓存验证机制，用于条件请求 |
| **Stylometry** | 写作风格分析，通过文本特征识别作者 |
| **Cascade Trigger** | 级联触发器，一个信号触发深度检查 |
| **Event Sourcing** | 事件溯源，通过事件流重建状态 |

### 9.2 参考资料

- [GitHub Events API](https://docs.github.com/en/rest/activity/events)
- [Twitter API v2](https://developer.twitter.com/en/docs/twitter-api)
- [OSINT Framework](https://osintframework.com/)
- [Perceptual Hashing](http://www.phash.org/)
- [Stylometry Research](https://www.cs.drexel.edu/~sa379/papers/compsurv_stylometry.pdf)

---

**文档维护**: 随系统迭代持续更新  
**最后更新**: 2026-03-01
