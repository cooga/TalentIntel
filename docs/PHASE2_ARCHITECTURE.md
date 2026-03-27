# TalentIntel Phase 2 - Social Intelligence System
# 社交动态洞察与社交图谱拓源系统

## 🎯 阶段目标

### 目标 1：招聘机会点识别
通过分析候选人的社交动态（LinkedIn posts, activity, profile updates），识别：
- 换工作意向信号（Open to work, 更新求职偏好）
- 职业变动信号（职位变动、公司变动）
- 技术成就信号（发表论文、获得专利、项目发布）
- 职业不满信号（吐槽、离职 anniversary、频繁更新档案）

### 目标 2：社交图谱拓源
通过 LinkedIn 社交关系，发现：
- 直接同事（同公司、同部门）
- 前同事（共同工作经历）
- 校友/同行（同学校、同领域）
- 2度关系（朋友的朋友）潜在候选人

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TalentIntel Phase 2 - Social Intelligence                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Social Monitor (社交监控器)                        │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ Profile      │  │ Activity     │  │ Network      │              │   │
│  │  │ Tracker      │  │ Scanner      │  │ Explorer     │              │   │
│  │  │ (档案追踪)    │  │ (动态扫描)    │  │ (关系探索)    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Signal Detector (信号检测器)                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ Opportunity  │  │ Career       │  │ Sentiment    │              │   │
│  │  │ Signals      │  │ Changes      │  │ Analysis     │              │   │
│  │  │ (机会信号)    │  │ (变动信号)    │  │ (情感分析)    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Graph Builder (图谱构建器)                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ Colleague    │  │ Alumni       │  │ 2nd Degree   │              │   │
│  │  │ Discovery    │  │ Network      │  │ Expansion    │              │   │
│  │  │ (同事发现)    │  │ (校友网络)    │  │ (二度拓源)    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Opportunity Engine (机会引擎)                      │   │
│  │  - 招聘时机评分                                                       │   │
│  │  - 接触策略建议                                                       │   │
│  │  - 个性化话术生成                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Data Layer (数据层)                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ Social       │  │ Graph        │  │ Opportunity  │              │   │
│  │  │ Activity DB  │  │ Network DB   │  │ Queue        │              │   │
│  │  │ (社交动态)    │  │ (关系图谱)    │  │ (机会队列)    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 模块设计

### 1. Social Monitor (社交监控器)

#### 1.1 Profile Tracker (档案追踪)
**职责**: 定期追踪候选人 LinkedIn 档案变化
```python
class ProfileTracker:
    """档案变化追踪器"""
    
    def track_changes(self, candidate_id: str) -> ProfileDelta:
        """
        检测档案变化
        Returns: 职位、公司、标题、照片的变化
        """
        pass
    
    def detect_job_seeking_signals(self, profile: dict) -> List[Signal]:
        """
        检测求职信号:
        - "Open to work" badge
        - 频繁更新档案
        - 添加求职偏好
        """
        pass
```

**检测信号**:
| 信号类型 | 检测方法 | 权重 |
|---------|---------|------|
| Open to work | 检查profile header | ⭐⭐⭐⭐⭐ |
| 职位变动 | 对比历史position数据 | ⭐⭐⭐⭐⭐ |
| 档案更新频率 | 30天内更新次数>3 | ⭐⭐⭐⭐ |
| 求职偏好 | #opentowork, 技能标签变化 | ⭐⭐⭐⭐ |
| 技能扩充 | 新增AI/无线相关技能 | ⭐⭐⭐ |

#### 1.2 Activity Scanner (动态扫描)
**职责**: 扫描候选人 LinkedIn 动态（posts, articles, likes, comments）
```python
class ActivityScanner:
    """社交动态扫描器"""
    
    def scan_recent_activity(self, candidate_id: str, days: int = 30) -> ActivityFeed:
        """扫描最近动态"""
        pass
    
    def detect_achievement_signals(self, activities: List[Activity]) -> List[Signal]:
        """
        检测成就信号:
        - 论文发表
        - 项目发布
        - 获得专利
        - 获奖/认可
        """
        pass
    
    def detect_frustration_signals(self, activities: List[Activity]) -> List[Signal]:
        """
        检测不满信号:
        - 吐槽类post
        - 离职 anniversary post
        - 工作压力大相关分享
        """
        pass
```

**动态分析维度**:
| 维度 | 检测内容 | 数据源 |
|-----|---------|--------|
| 原创Post | 内容关键词、情感倾向 | LinkedIn feed |
| 点赞互动 | 关注的领域、同行关系 | LinkedIn activity |
| 评论参与 | 专业讨论、观点表达 | LinkedIn comments |
| 分享转载 | 感兴趣的内容类型 | LinkedIn shares |

#### 1.3 Network Explorer (关系探索)
**职责**: 探索候选人的 LinkedIn 社交网络
```python
class NetworkExplorer:
    """社交网络探索器"""
    
    def get_mutual_connections(self, candidate_id: str, degree: int = 2) -> List[Connection]:
        """
        获取共同联系人
        degree=1: 直接联系人
        degree=2: 朋友的朋友
        """
        pass
    
    def discover_colleagues(self, candidate_id: str) -> List[Connection]:
        """
        发现同事关系:
        - 同公司 (current/previous)
        - 重叠时间段
        - 相似职位/部门
        """
        pass
    
    def discover_alumni_network(self, candidate_id: str) -> List[Connection]:
        """
        发现校友网络:
        - 同学校
        - 相似专业/研究方向
        - 毕业时间相近
        """
        pass
```

---

### 2. Signal Detector (信号检测器)

#### 2.1 信号分类体系
```
招聘机会信号 (Opportunity Signals)
├── 高优先级 (Hot Lead)
│   ├── 🟢 Open to work badge 亮起
│   ├── 🟢 职位变为 "Actively looking"
│   └── 🟢 加入求职群组
├── 中优先级 (Warm Lead)
│   ├── 🟡 刚离职 (<30天)
│   ├── 🟡 毕业/完成博士后 (<60天)
│   └── 🟡 频繁更新技能 (AI/无线相关)
└── 低优先级 (Cold Lead)
    ├── 🔵 周年纪念帖 (暗示回顾/展望)
    ├── 🔵 分享求职建议
    └── 🔵 转发招聘信息

职业变动信号 (Career Change Signals)
├── 职位变动
│   ├── 升职/降职
│   ├── 转岗
│   └── 离职
├── 公司变动
│   ├── 换公司
│   ├── 公司被收购
│   └── 公司裁员
└── 地理位置变动
    ├── 换城市
    └── 换国家

情感倾向信号 (Sentiment Signals)
├── 积极信号
│   ├── 分享技术成就
│   ├── 发布项目成果
│   └── 获得认可/奖励
└── 消极信号
    ├── 工作吐槽
    ├── 加班抱怨
    └── 离职暗示
```

#### 2.2 信号评分算法
```python
def calculate_opportunity_score(signals: List[Signal]) -> float:
    """
    招聘机会评分算法
    
    评分维度:
    1. 信号强度 (weight: 40%)
       - Hot: 1.0, Warm: 0.6, Cold: 0.3
    
    2. 信号时效性 (weight: 30%)
       - <7天: 1.0, <30天: 0.8, <90天: 0.5
    
    3. 信号组合 (weight: 20%)
       - 多个相关信号叠加加分
    
    4. 候选人匹配度 (weight: 10%)
       - 原匹配分数作为基础
    
    Returns: 0-1 机会分数
    """
    pass
```

---

### 3. Graph Builder (图谱构建器)

#### 3.1 图数据模型
```python
# Neo4j / NetworkX 图模型

class Person(Node):
    """人物节点"""
    linkedin_id: str
    name: str
    current_company: str
    current_title: str
    match_score: float
    
class Company(Node):
    """公司节点"""
    name: str
    industry: str
    
class School(Node):
    """学校节点"""
    name: str
    
class WorksAt(Relationship):
    """工作关系"""
    from_date: datetime
    to_date: Optional[datetime]
    title: str
    
class StudiedAt(Relationship):
    """教育关系"""
    degree: str
    field: str
    graduation_year: int
    
class ConnectedTo(Relationship):
    """LinkedIn连接关系"""
    connection_date: datetime
    interaction_score: float  # 互动频率
```

#### 3.2 拓源算法
```python
class NetworkExpansionStrategy:
    """网络拓源策略"""
    
    def expand_via_colleagues(self, seed_candidate: Candidate, depth: int = 2) -> List[Candidate]:
        """
        通过同事关系拓源
        
        算法:
        1. 获取种子候选人的同事 (同公司/同时间段)
        2. 对每个同事，获取他们的同事
        3. 过滤出符合画像的新候选人
        """
        pass
    
    def expand_via_alumni(self, seed_candidate: Candidate) -> List[Candidate]:
        """
        通过校友关系拓源
        
        算法:
        1. 获取种子候选人的学校
        2. 查找同学校、同专业、同时期的校友
        3. 评估校友的职业轨迹和技术方向
        """
        pass
    
    def expand_via_interaction(self, seed_candidate: Candidate) -> List[Candidate]:
        """
        通过社交互动拓源
        
        算法:
        1. 分析种子候选人点赞/评论的人
        2. 分析关注相同话题的人
        3. 找出技术影响力大的相关人物
        """
        pass
```

---

### 4. Opportunity Engine (机会引擎)

#### 4.1 招聘时机评分
```python
class OpportunityEngine:
    """招聘机会引擎"""
    
    def calculate_timing_score(self, candidate: Candidate) -> TimingScore:
        """
        计算招聘时机评分
        
        Returns:
        {
            "score": 0-100,
            "urgency": "immediate|soon|watch",
            "best_contact_window": "2026-04-01 to 2026-04-15",
            "reasoning": "解释评分的理由"
        }
        """
        pass
    
    def generate_outreach_strategy(self, candidate: Candidate) -> Strategy:
        """
        生成接触策略
        
        Returns:
        {
            "channel": "LinkedIn DM|Email|Referral",
            "timing": "具体时机建议",
            "approach": "cold|warm|hot",
            "talking_points": ["切入点1", "切入点2"],
            "personalized_message": "个性化消息模板"
        }
        """
        pass
```

#### 4.2 接触策略矩阵
| 机会分数 | 时机 | 策略 | 渠道 | 话术风格 |
|---------|------|------|------|---------|
| 90-100 | 🔥 立即 | 直接邀约 | LinkedIn DM | 紧迫+高价值 |
| 70-89 | ⚡ 本周 | 价值展示 | LinkedIn DM + Email | 专业+机会 |
| 50-69 | 📅 本月 | 关系建立 | 评论互动 + DM | 友好+长期 |
| <50 | 👀 观察 | 内容营销 | 发布相关内容 | 被动吸引 |

---

## 📊 数据模型

### Social Activity 表
```sql
CREATE TABLE social_activities (
    id UUID PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(id),
    platform VARCHAR(50),  -- linkedin, github, twitter
    activity_type VARCHAR(50),  -- post, like, comment, share, profile_update
    content TEXT,
    activity_date TIMESTAMP,
    sentiment_score FLOAT,  -- -1 to 1
    extracted_signals JSONB,  -- 提取的信号
    raw_data JSONB,  -- 原始数据
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Network Graph 表
```sql
CREATE TABLE network_connections (
    id UUID PRIMARY KEY,
    from_candidate_id UUID REFERENCES candidates(id),
    to_candidate_id UUID REFERENCES candidates(id),
    connection_type VARCHAR(50),  -- colleague, alumni, 1st_degree, 2nd_degree
    relationship_strength FLOAT,  -- 0-1
    common_companies JSONB,
    common_schools JSONB,
    interaction_score FLOAT,  -- 互动频率
    discovered_at TIMESTAMP DEFAULT NOW()
);
```

### Opportunity Queue 表
```sql
CREATE TABLE opportunity_queue (
    id UUID PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(id),
    opportunity_score FLOAT,
    urgency_level VARCHAR(20),  -- immediate, high, medium, low
    detected_signals JSONB,
    recommended_action TEXT,
    contact_window_start DATE,
    contact_window_end DATE,
    status VARCHAR(20),  -- pending, contacted, responded, converted, closed
    assigned_to VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔄 工作流程

### 每日流程
```
09:00 - 启动社交监控扫描
        ↓
09:30 - 检测档案变化和动态更新
        ↓
10:00 - 运行信号检测算法
        ↓
10:30 - 更新机会队列（新增/升级/降级）
        ↓
11:00 - 生成今日待办（高优先级候选人）
        ↓
18:00 - 执行网络拓源任务（发现新候选人）
```

### 触发器机制
| 触发条件 | 动作 | 通知渠道 |
|---------|------|---------|
| 候选人 Open to work | 立即添加到热队列 | Discord |
| 高分候选人职位变动 | 更新档案并重新评分 | Discord |
| 发现新相关候选人 | 添加到待验证列表 | - |
| 机会分数 > 80 | 生成接触策略并通知 | Discord |

---

## 🚀 实施计划

### Phase 2A: 基础监控 (1-2周)
- [ ] 实现 Profile Tracker（档案变化检测）
- [ ] 实现 Activity Scanner（动态扫描）
- [ ] 基础信号检测（Open to work, 职位变动）
- [ ] 数据存储层搭建

### Phase 2B: 信号分析 (2-3周)
- [ ] 实现 Signal Detector（信号分类和评分）
- [ ] 情感分析模块
- [ ] 机会评分算法
- [ ] 触发器机制

### Phase 2C: 图谱拓源 (2-3周)
- [ ] 实现 Network Explorer
- [ ] 图数据库搭建（Neo4j/NetworkX）
- [ ] 同事/校友发现算法
- [ ] 2度关系拓源

### Phase 2D: 机会引擎 (1-2周)
- [ ] 机会时机评分
- [ ] 接触策略生成
- [ ] 个性化话术模板
- [ ] Discord 通知集成

---

## 📝 待办事项

- [ ] 创建 Phase 2 工程目录结构
- [ ] 设计数据库 Schema
- [ ] 实现 Social Monitor 核心模块
- [ ] 集成 LinkedIn API / Browser automation
- [ ] 实现信号检测算法
- [ ] 搭建图数据库
- [ ] 实现拓源算法
- [ ] 开发机会引擎
- [ ] 集成 Discord 通知
- [ ] 编写测试用例

---

## 🔗 依赖

- LinkedIn 已登录 Profile（复用 Phase 1）
- Phase 1 清洗后的候选人数据库
- Neo4j / NetworkX 图数据库
- NLP 库（情感分析）
- Discord Webhook（通知）

---

*Created: 2026-03-27*
*Phase: Architecture Design*
