# TalentIntel Phase 2 顶层设计文档
## 社交动态洞察与关系拓源系统

**版本**: v1.0  
**日期**: 2026-03-26  
**目标**: 通过社交动态发现招聘机会点，通过社交图谱扩展候选人网络

---

## 1. 系统愿景

### 1.1 Phase 1 vs Phase 2 对比

| 维度 | Phase 1: 人才拓源 | Phase 2: 关系洞察 |
|------|------------------|------------------|
| **核心目标** | 发现候选人 | 理解候选人+发现机会 |
| **数据类型** | 静态档案信息 | 动态社交行为 |
| **分析深度** | 个人资质评估 | 关系网络+行为意图 |
| **输出价值** | 候选人名单 | 招聘时机+关联网络 |
| **技术重点** | X-Ray搜索+验证 | 监控+图谱+推理 |

### 1.2 Phase 2 双目标

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 2 双目标架构                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐    ┌─────────────────────────┐   │
│  │   目标一: 机会发现   │    │    目标二: 关系拓源     │   │
│  │   Opportunity       │    │    Network Expansion    │   │
│  │   Detection         │    │                         │   │
│  ├─────────────────────┤    ├─────────────────────────┤   │
│  │ • 职业变动信号      │    │ • 同事/同伴发现         │   │
│  │ • 项目参与动态      │    │ • 社交网络图谱          │   │
│  │ • 情绪/满意度分析   │    │ • 二度人脉挖掘          │   │
│  │ • 最佳接触时机      │    │ • 团队结构分析          │   │
│  └──────────┬──────────┘    └────────────┬────────────┘   │
│             │                            │                 │
│             └────────────┬───────────────┘                 │
│                          │                                  │
│              ┌───────────▼────────────┐                    │
│              │   统一输出: 行动建议    │                    │
│              │   - 何时联系          │                    │
│              │   - 通过谁联系        │                    │
│              │   - 说什么话题        │                    │
│              └────────────────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 系统架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TalentIntel Phase 2 架构                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     应用层 (Application)                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │   │
│  │  │ 机会雷达     │  │ 关系图谱     │  │ 智能行动建议引擎     │  │   │
│  │  │ Dashboard    │  │ Explorer     │  │ Action Recommender   │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│  ┌───────────────────────────────▼──────────────────────────────────┐   │
│  │                     服务层 (Services)                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │   │
│  │  │ Social       │  │ Graph        │  │ Opportunity  │            │   │
│  │  │ Monitor      │  │ Builder      │  │ Detector     │            │   │
│  │  │ Service      │  │ Service      │  │ Service      │            │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│  ┌───────────────────────────────▼──────────────────────────────────┐   │
│  │                     引擎层 (Engines)                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │   │
│  │  │ 行为监控     │  │ 图谱推理     │  │ 意图识别     │            │   │
│  │  │ Monitor      │  │ Graph        │  │ Intent       │            │   │
│  │  │ Engine       │  │ Engine       │  │ Engine       │            │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│  ┌───────────────────────────────▼──────────────────────────────────┐   │
│  │                     数据层 (Data Layer)                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │   │
│  │  │ 社交动态库   │  │ 关系图谱库   │  │ 机会事件库   │            │   │
│  │  │ Social DB    │  │ Graph DB     │  │ Opportunity  │            │   │
│  │  │ (Time-series)│  │ (Neo4j)      │  │ DB           │            │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 与现有架构的集成

```
Phase 1 现有组件          Phase 2 新增组件
─────────────────────────────────────────────────────
                          
┌─────────────────┐      ┌─────────────────────────┐
│ src/collectors/ │◄────►│ src/social_monitor/     │
│   LinkedIn      │      │   ActivityTracker       │
│   X-Ray         │      │   PostAnalyzer          │
└─────────────────┘      │   EngagementWatcher     │
                         └─────────────────────────┘
┌─────────────────┐      ┌─────────────────────────┐
│ src/cognition/  │◄────►│ src/intent_detection/   │
│   LLM Evaluator │      │   JobChangeSignals      │
│   Scorer        │      │   SentimentAnalyzer     │
└─────────────────┘      │   OpportunityScorer     │
                         └─────────────────────────┘
┌─────────────────┐      ┌─────────────────────────┐
│ src/graph/      │◄────►│ src/network_builder/    │
│   (existing)    │      │   ColleagueFinder       │
│                 │      │   ConnectionPath        │
│                 │      │   TeamAnalyzer          │
└─────────────────┘      └─────────────────────────┘
┌─────────────────┐      ┌─────────────────────────┐
│ src/storage/    │◄────►│ src/timeline/           │
│   JSON DB       │      │   ActivityLog           │
│                 │      │   ChangeHistory         │
│                 │      │   OpportunityQueue      │
└─────────────────┘      └─────────────────────────┘
```

---

## 3. 核心模块设计

### 3.1 社交动态监控模块 (Social Monitor)

#### 3.1.1 功能职责

```python
class SocialMonitorService:
    """
    社交动态监控服务
    - 跟踪候选人的 LinkedIn 动态
    - 检测职业变动信号
    - 分析内容情绪与意图
    """
    
    def __init__(self):
        self.activity_tracker = ActivityTracker()
        self.change_detector = ChangeDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    async def monitor_candidate(self, candidate_id: str):
        """监控单个候选人的社交动态"""
        # 1. 获取最新活动
        activities = await self.fetch_recent_activities(candidate_id)
        
        # 2. 检测变化
        changes = self.change_detector.detect(activities)
        
        # 3. 分析情绪
        sentiment = self.sentiment_analyzer.analyze(activities)
        
        # 4. 生成机会评分
        opportunity_score = self.calculate_opportunity(changes, sentiment)
        
        return MonitorResult(
            candidate_id=candidate_id,
            changes=changes,
            sentiment=sentiment,
            opportunity_score=opportunity_score
        )
```

#### 3.1.2 监控信号类型

| 信号类别 | 具体信号 | 机会权重 | 说明 |
|---------|---------|---------|------|
| **职业变动** | 职位变更 | ⭐⭐⭐⭐⭐ | 刚换工作/升职 |
| | 公司变更 | ⭐⭐⭐⭐⭐ | 入职新公司 |
| | 状态改为"Open to work" | ⭐⭐⭐⭐⭐ | 明确求职信号 |
| **项目动态** | 新项目发布 | ⭐⭐⭐⭐ | 展示新能力 |
| | 论文/专利发布 | ⭐⭐⭐⭐ | 学术影响力提升 |
| | 开源项目贡献 | ⭐⭐⭐ | 技术活跃度 |
| **情绪信号** | 抱怨当前工作 | ⭐⭐⭐⭐ | 离职倾向 |
| | 点赞招聘内容 | ⭐⭐⭐ | 求职兴趣 |
| | 分享行业机会 | ⭐⭐⭐ | 开放心态 |
| **社交网络** | 新增大量联系人 | ⭐⭐ | 网络扩张期 |
| | 与前同事重新连接 | ⭐⭐⭐ | 可能考虑跳槽 |

### 3.2 社交图谱构建模块 (Social Graph Builder)

#### 3.2.1 图谱数据模型

```cypher
// Neo4j 图模型定义

// 节点类型
(:Person {
    id: string,
    name: string,
    company: string,
    title: string,
    location: string,
    ai_score: float,
    wireless_score: float,
    is_target: boolean,      // 是否为目标候选人
    is_entry: boolean        // 是否作为入口点
})

(:Company {
    name: string,
    industry: string,
    size: string,
    location: string
})

(:School {
    name: string,
    country: string
})

(:Skill {
    name: string,
    category: string        // AI | Wireless | General
})

// 关系类型
(:Person)-[:WORKS_AT {
    start_date: date,
    end_date: date,
    is_current: boolean
}]->(:Company)

(:Person)-[:COLLEAGUE {
    company: string,
    overlap_period: string,
    strength: float         // 关系强度 0-1
}]->(:Person)

(:Person)-[:MANAGES]->(:Person)

(:Person)-[:STUDIED_AT {
    degree: string,
    year: int
}]->(:School)

(:Person)-[:HAS_SKILL {
    proficiency: string,    // expert | advanced | intermediate
    endorsements: int
}]->(:Skill)

(:Person)-[:CONNECTED {
    platform: string,       // linkedin | github | etc
    connection_date: date
}]->(:Person)
```

#### 3.2.2 图谱构建流程

```python
class SocialGraphBuilder:
    """
    社交图谱构建器
    - 从LinkedIn提取关系数据
    - 构建多维度关系网络
    - 发现潜在候选人路径
    """
    
    def build_graph_from_candidate(self, entry_candidate: Candidate):
        """以候选人为入口构建关系图谱"""
        
        # Layer 1: 直接连接 (1度)
        direct_connections = self.fetch_connections(entry_candidate)
        
        # Layer 2: 同事关系
        colleagues = self.find_colleagues(entry_candidate)
        
        # Layer 3: 共同兴趣/技能
        skill_peers = self.find_skill_peers(entry_candidate)
        
        # 构建图谱
        with self.graph_db.session() as session:
            # 创建入口节点
            session.run("""
                MERGE (p:Person {id: $id})
                SET p.name = $name, p.company = $company, 
                    p.is_entry = true, p.is_target = true
            """, **entry_candidate.to_dict())
            
            # 添加连接
            for conn in direct_connections:
                session.run("""
                    MATCH (entry:Person {id: $entry_id})
                    MERGE (p:Person {id: $conn_id})
                    SET p.name = $conn_name, p.company = $conn_company
                    MERGE (entry)-[:CONNECTED {platform: 'linkedin'}]->(p)
                """, entry_id=entry_candidate.id, **conn)
            
            # 添加同事关系
            for colleague in colleagues:
                session.run("""
                    MATCH (entry:Person {id: $entry_id})
                    MERGE (p:Person {id: $col_id})
                    SET p.name = $col_name
                    MERGE (entry)-[:COLLEAGUE {
                        company: $company,
                        strength: $strength
                    }]->(p)
                """, entry_id=entry_candidate.id, **colleague)
```

### 3.3 机会检测引擎 (Opportunity Detection Engine)

#### 3.3.1 机会评分算法

```python
class OpportunityScorer:
    """
    招聘机会评分引擎
    综合考虑多个维度计算最佳接触时机
    """
    
    # 权重配置
    WEIGHTS = {
        'job_change_signal': 0.35,      # 职业变动信号
        'sentiment_score': 0.25,         # 情绪倾向
        'activity_level': 0.15,          # 活跃度
        'network_expansion': 0.10,       # 网络扩张
        'skill_relevance': 0.10,         # 技能相关度
        'timing_factor': 0.05            # 时机因素
    }
    
    def calculate_opportunity_score(self, candidate: Candidate) -> OpportunityScore:
        """计算候选人的招聘机会评分"""
        
        # 1. 职业变动信号 (0-100)
        job_change_score = self.detect_job_change_signals(candidate)
        
        # 2. 情绪分析 (0-100, 越高越负面/想离开)
        sentiment_score = self.analyze_sentiment(candidate.recent_activities)
        
        # 3. 活跃度 (0-100)
        activity_score = self.calculate_activity_level(candidate)
        
        # 4. 网络扩张 (0-100)
        network_score = self.analyze_network_expansion(candidate)
        
        # 5. 技能匹配度 (0-100)
        skill_score = self.calculate_skill_match(candidate)
        
        # 6. 时机因素 (0-100)
        timing_score = self.calculate_timing_factor(candidate)
        
        # 加权计算
        total_score = (
            job_change_score * self.WEIGHTS['job_change_signal'] +
            sentiment_score * self.WEIGHTS['sentiment_score'] +
            activity_score * self.WEIGHTS['activity_level'] +
            network_score * self.WEIGHTS['network_expansion'] +
            skill_score * self.WEIGHTS['skill_relevance'] +
            timing_score * self.WEIGHTS['timing_factor']
        )
        
        # 确定机会等级
        if total_score >= 80:
            level = OpportunityLevel.HIGH
            recommendation = "立即联系"
        elif total_score >= 60:
            level = OpportunityLevel.MEDIUM
            recommendation = "本周内联系"
        elif total_score >= 40:
            level = OpportunityLevel.LOW
            recommendation = "保持监控"
        else:
            level = OpportunityLevel.NONE
            recommendation = "暂不联系"
        
        return OpportunityScore(
            candidate_id=candidate.id,
            total_score=total_score,
            level=level,
            recommendation=recommendation,
            breakdown={
                'job_change': job_change_score,
                'sentiment': sentiment_score,
                'activity': activity_score,
                'network': network_score,
                'skill': skill_score,
                'timing': timing_score
            }
        )
```

#### 3.3.2 机会信号检测规则

```yaml
# 机会信号检测规则配置
signals:
  job_change:
    - pattern: "excited to announce.*new (role|position|opportunity)"
      weight: 100
      description: "宣布新职位"
    
    - pattern: "starting.*(new job|new role|new position)"
      weight: 95
      description: "即将开始新工作"
    
    - pattern: "#OpenToWork|open to (new opportunities|work)"
      weight: 100
      description: "明确求职信号"
    
    - pattern: "last day at|farewell to|saying goodbye to.*team"
      weight: 90
      description: "离职信号"
  
  sentiment_negative:
    - pattern: "frustrated with|tired of|burned out|stuck in"
      weight: 80
      description: "工作挫败感"
    
    - pattern: "looking for.*change|ready for.*new challenge"
      weight: 70
      description: "寻求变化"
  
  positive_engagement:
    - pattern: "congratulations.*(new role|promotion)|welcoming.*to the team"
      weight: 30
      description: "他人职业变动互动"
    
    - pattern: "hiring|we're looking for|join our team"
      weight: 40
      description: "参与招聘内容"
```

### 3.4 智能行动建议引擎 (Action Recommendation Engine)

#### 3.4.1 建议生成逻辑

```python
class ActionRecommendationEngine:
    """
    智能行动建议引擎
    基于机会评分和社交图谱生成个性化 outreach 建议
    """
    
    def generate_recommendation(self, candidate: Candidate) -> ActionPlan:
        """生成针对候选人的行动建议"""
        
        # 1. 获取机会评分
        opp_score = self.opportunity_scorer.calculate(candidate)
        
        # 2. 查找最佳联系路径
        connection_paths = self.graph_builder.find_connection_paths(candidate)
        
        # 3. 分析话题切入点
        talking_points = self.generate_talking_points(candidate)
        
        # 4. 确定最佳时机
        best_timing = self.suggest_timing(candidate, opp_score)
        
        # 5. 生成个性化消息模板
        message_templates = self.generate_message_templates(
            candidate, 
            talking_points,
            connection_paths
        )
        
        return ActionPlan(
            candidate_id=candidate.id,
            opportunity_score=opp_score,
            priority=self.determine_priority(opp_score),
            recommended_actions=[
                {
                    'type': 'connection_request',
                    'timing': best_timing,
                    'via': connection_paths[0] if connection_paths else 'direct',
                    'message': message_templates['connection']
                },
                {
                    'type': 'engagement',
                    'content': talking_points[0] if talking_points else None,
                    'platform': 'linkedin'
                },
                {
                    'type': 'follow_up',
                    'delay_days': 7,
                    'message': message_templates['follow_up']
                }
            ],
            talking_points=talking_points,
            connection_paths=connection_paths
        )
    
    def generate_talking_points(self, candidate: Candidate) -> List[TalkingPoint]:
        """生成话题切入点"""
        talking_points = []
        
        # 分析最近动态
        for activity in candidate.recent_activities:
            if activity.type == 'post':
                # 技术分享
                if any(kw in activity.content for kw in ['AI', 'machine learning', 'wireless', '5G', '6G']):
                    talking_points.append(TalkingPoint(
                        topic='technical',
                        content=f"对他分享的{self.extract_topic(activity.content)}内容表达兴趣",
                        angle='technical_discussion'
                    ))
                
                # 项目成就
                if any(kw in activity.content for kw in ['launch', 'release', 'ship', 'deploy']):
                    talking_points.append(TalkingPoint(
                        topic='achievement',
                        content=f"祝贺{activity.project_name}项目上线",
                        angle='appreciation'
                    ))
        
        # 共同连接
        mutual_connections = self.graph_builder.find_mutual_connections(candidate)
        if mutual_connections:
            talking_points.append(TalkingPoint(
                topic='network',
                content=f"通过共同联系人 {mutual_connections[0].name} 建立连接",
                angle='warm_intro'
            ))
        
        # 教育背景
        if candidate.school in ['Stanford', 'MIT', 'Berkeley', 'CMU']:
            talking_points.append(TalkingPoint(
                topic='alumni',
                content=f"同为{candidate.school}校友",
                angle='alumni_connection'
            ))
        
        return talking_points
```

---

## 4. 数据存储设计

### 4.1 数据库选型

| 数据类型 | 存储方案 | 选型理由 |
|---------|---------|---------|
| **社交动态** | MongoDB | 灵活的文档结构，适合存储多变的社交内容 |
| **关系图谱** | Neo4j | 原生图数据库，高效的关系查询 |
| **时间序列** | TimescaleDB | 活动历史的时间序列分析 |
| **缓存** | Redis | 实时机会评分和热点数据 |
| **主数据** | PostgreSQL | 候选人主数据，ACID保障 |

### 4.2 数据模型

```python
# MongoDB - 社交动态集合
{
    "_id": ObjectId("..."),
    "candidate_id": "zhican_chen_001",
    "platform": "linkedin",
    "activity_type": "post",  # post | like | comment | job_change | connection
    "content": "Excited to announce...",
    "timestamp": ISODate("2026-03-26T10:30:00Z"),
    "engagement": {
        "likes": 45,
        "comments": 8,
        "shares": 3
    },
    "sentiment": {
        "score": 0.8,  # -1 to 1
        "label": "positive",
        "keywords": ["excited", "new opportunity"]
    },
    "extracted_signals": [
        {"type": "job_change", "confidence": 0.95, "description": "宣布新职位"}
    ],
    "raw_html": "...",
    "screenshot_url": "s3://..."
}

# PostgreSQL - 机会评分表
CREATE TABLE opportunity_scores (
    id SERIAL PRIMARY KEY,
    candidate_id VARCHAR(100) REFERENCES candidates(id),
    calculated_at TIMESTAMP DEFAULT NOW(),
    total_score DECIMAL(5,2),
    level VARCHAR(20),  -- HIGH | MEDIUM | LOW | NONE
    job_change_score DECIMAL(5,2),
    sentiment_score DECIMAL(5,2),
    activity_score DECIMAL(5,2),
    network_score DECIMAL(5,2),
    skill_score DECIMAL(5,2),
    timing_score DECIMAL(5,2),
    recommendation TEXT,
    expires_at TIMESTAMP  -- 评分有效期
);

# Neo4j - 图谱节点和关系
# (见 3.2.1 节)
```

---

## 5. 监控与更新机制

### 5.1 监控频率策略

```python
class MonitoringSchedule:
    """
    分级监控频率策略
    根据候选人价值和机会评分动态调整监控频率
    """
    
    SCHEDULES = {
        'critical': {  # 高价值 + 高机会
            'interval_hours': 6,
            'max_per_day': 4,
            'deep_analysis': True
        },
        'high_priority': {  # 高价值 + 中机会
            'interval_hours': 12,
            'max_per_day': 2,
            'deep_analysis': True
        },
        'standard': {  # 普通候选人
            'interval_hours': 24,
            'max_per_day': 1,
            'deep_analysis': False
        },
        'low_frequency': {  # 低优先级
            'interval_hours': 72,
            'max_per_day': 0,  # 不主动监控
            'deep_analysis': False
        }
    }
    
    def get_schedule(self, candidate: Candidate) -> dict:
        """根据候选人属性确定监控频率"""
        
        # 获取最新机会评分
        opp_score = self.get_latest_opportunity_score(candidate.id)
        
        # 获取候选人价值评分
        value_score = candidate.match_score
        
        # 分级逻辑
        if value_score >= 0.85 and opp_score.total_score >= 70:
            return self.SCHEDULES['critical']
        elif value_score >= 0.75 and opp_score.total_score >= 50:
            return self.SCHEDULES['high_priority']
        elif value_score >= 0.60:
            return self.SCHEDULES['standard']
        else:
            return self.SCHEDULES['low_frequency']
```

### 5.2 实时告警机制

```python
class OpportunityAlertSystem:
    """
    机会实时告警系统
    当检测到高价值机会时立即通知
    """
    
    ALERT_CHANNELS = ['discord', 'email']  # 可扩展
    
    async def check_and_alert(self, monitor_result: MonitorResult):
        """检查结果并触发告警"""
        
        # 高优先级机会
        if monitor_result.opportunity_score.level == OpportunityLevel.HIGH:
            await self.send_high_priority_alert(monitor_result)
        
        # 职业变动事件
        if monitor_result.has_job_change_signal:
            await self.send_job_change_alert(monitor_result)
        
        # 图谱扩展发现
        if monitor_result.new_connections_found:
            await self.send_network_expansion_alert(monitor_result)
    
    async def send_high_priority_alert(self, result: MonitorResult):
        """发送高优先级告警"""
        candidate = await self.get_candidate(result.candidate_id)
        
        message = f"""
🔥 **高优先级机会告警**

**候选人**: {candidate.name}
**公司**: {candidate.company}
**职位**: {candidate.title}
**机会评分**: {result.opportunity_score.total_score:.1f}/100

**检测到的信号**:
{self.format_signals(result.changes)}

**建议行动**:
{result.opportunity_score.recommendation}

**查看详情**: [Dashboard](https://talentintel.cooga.uk/candidates/{candidate.id})
        """
        
        await self.discord_notifier.send(
            channel='talent-opportunities',
            message=message
        )
```

---

## 6. 实施路线图

### 6.1 阶段划分

```
Phase 2 实施计划
────────────────────────────────────────────────────────

Week 1-2: 基础设施
├── 搭建 Neo4j 图谱数据库
├── 设计并实现数据模型
├── 实现社交动态存储 (MongoDB)
└── 建立监控任务调度系统

Week 3-4: 核心引擎
├── 实现社交动态监控引擎
├── 实现职业变动信号检测
├── 实现情绪分析模块
└── 实现机会评分算法

Week 5-6: 图谱构建
├── 实现同事关系发现
├── 实现共同连接分析
├── 实现团队结构推断
└── 构建二度人脉扩展

Week 7-8: 智能建议
├── 实现行动建议引擎
├── 实现消息模板生成
├── 实现话题切入点分析
└── 集成 Discord 告警

Week 9-10: 整合测试
├── 端到端流程测试
├── 性能优化
├── 限流与合规检查
└── 文档完善
```

### 6.2 优先级队列

| 优先级 | 功能模块 | 业务价值 | 技术难度 | 建议迭代 |
|-------|---------|---------|---------|---------|
| P0 | 职业变动检测 | ⭐⭐⭐⭐⭐ | 中 | Week 1-2 |
| P0 | 机会评分引擎 | ⭐⭐⭐⭐⭐ | 中 | Week 2-3 |
| P1 | 同事关系发现 | ⭐⭐⭐⭐ | 中 | Week 3-4 |
| P1 | 实时告警系统 | ⭐⭐⭐⭐ | 低 | Week 4 |
| P2 | 二度人脉扩展 | ⭐⭐⭐ | 高 | Week 5-6 |
| P2 | 智能消息生成 | ⭐⭐⭐ | 中 | Week 6-7 |
| P3 | 团队结构分析 | ⭐⭐ | 高 | Week 8+ |

---

## 7. 风险控制与合规

### 7.1 反检测策略增强

```python
class StealthEnhancements:
    """
    Phase 2 反检测增强
    针对社交监控场景的特殊处理
    """
    
    # 监控行为模式
    MONITORING_PATTERNS = {
        # 随机访问时间（避免规律性）
        'visit_times': [
            ('09:00', '11:00'),
            ('14:00', '16:00'),
            ('20:00', '22:00')
        ],
        
        # 浏览深度随机化
        'browse_depth': {
            'min_profiles': 1,
            'max_profiles': 5,
            'distribution': 'gaussian'  # 正态分布
        },
        
        # 动态冷却时间
        'cooldown': {
            'base': 60,  # 基础60秒
            'variance': 30,  # ±30秒随机
            'jitter': True  # 添加随机抖动
        }
    }
    
    def apply_stealth_pattern(self, session):
        """应用隐身模式"""
        # 随机化 User-Agent
        session.headers['User-Agent'] = self.rotate_user_agent()
        
        # 随机化屏幕分辨率
        session.viewport = self.random_viewport()
        
        # 随机化时区
        session.timezone = self.random_timezone()
        
        # 添加随机延迟
        self.random_delay()
```

### 7.2 合规边界

| 数据类型 | 处理方式 | 合规性 |
|---------|---------|-------|
| 公开帖子内容 | 可获取并分析 | ✅ 公开信息 |
| 个人档案基础信息 | 可获取 | ✅ 公开可见 |
| 连接列表 | 仅分析可见部分 | ⚠️ 需控制频率 |
| 私信内容 | **不获取** | ❌ 隐私边界 |
| 私密小组内容 | **不获取** | ❌ 隐私边界 |
| "仅好友可见"内容 | **不获取** | ❌ 隐私边界 |

---

## 8. 成功指标

### 8.1 技术指标

| 指标 | 目标值 | 测量方式 |
|-----|-------|---------|
| 职业变动检测准确率 | ≥85% | 人工抽样验证 |
| 机会评分相关性 | ≥0.7 | 与转化结果相关性 |
| 图谱关系准确率 | ≥80% | 抽样核实 |
| 系统可用性 | ≥99% | 监控告警 |
| API响应时间 | <500ms | P95延迟 |

### 8.2 业务指标

| 指标 | 目标值 | 说明 |
|-----|-------|------|
| 机会发现率 | 每周≥3个高优先级 | 可联系的机会 |
| 关系扩展率 | 每个目标扩展≥5个新候选 | 二度人脉 |
| 响应率提升 | 相比冷 outreach 提升2倍 | 通过时机优化 |
| 招聘周期缩短 | 平均缩短30% | 从发现到入职 |

---

## 9. 附录

### 9.1 关键接口定义

```python
# 社交监控服务接口
class ISocialMonitor(ABC):
    @abstractmethod
    async def monitor_candidate(self, candidate_id: str) -> MonitorResult:
        pass
    
    @abstractmethod
    async def batch_monitor(self, candidate_ids: List[str]) -> List[MonitorResult]:
        pass

# 图谱服务接口
class IGraphService(ABC):
    @abstractmethod
    async def build_from_candidate(self, candidate_id: str) -> Graph:
        pass
    
    @abstractmethod
    async def find_connection_paths(self, from_id: str, to_id: str) -> List[Path]:
        pass
    
    @abstractmethod
    async def expand_network(self, candidate_id: str, depth: int = 2) -> List[Candidate]:
        pass

# 机会检测服务接口
class IOpportunityService(ABC):
    @abstractmethod
    async def calculate_score(self, candidate_id: str) -> OpportunityScore:
        pass
    
    @abstractmethod
    async def get_hot_opportunities(self, limit: int = 10) -> List[Opportunity]:
        pass
```

### 9.2 依赖组件

```yaml
# requirements-phase2.txt

# 图数据库
neo4j-python-driver==5.15.0

# 文档数据库
pymongo==4.6.0
motor==3.3.0  # async MongoDB

# 时序数据库
timescale-python==0.1.0

# 自然语言处理
openai>=1.0.0
transformers==4.36.0  # 情感分析

# 任务调度
celery==5.3.0
redis==5.0.0

# 消息通知
discord-webhook==1.2.0

# 数据处理
pandas==2.1.0
networkx==3.2.0
```

---

**文档结束**

作者: TalentIntel Team  
最后更新: 2026-03-26
