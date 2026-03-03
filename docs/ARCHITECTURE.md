# TalentIntel 架构详解

## 1. 行为模拟层 (Behavior Simulation)

### 1.1 鼠标轨迹算法

**贝塞尔曲线 + Perlin噪声**

```python
# 核心思想：人类手部移动不是直线，而是平滑曲线 + 微抖动
class BezierCurve:
    def generate(p0, p3, variance=0.2):
        # 1. 计算起点终点连线
        # 2. 在线的中垂线方向随机偏移，生成控制点 p1, p2
        # 3. 三阶贝塞尔公式生成路径点
        # 4. 叠加 Perlin 噪声模拟手抖
```

**参数调优**：
- `variance=0.2`: 曲线弯曲程度
- `speed_factor=0.3`: 整体移动速度
- `tremor_amplitude=2.0`: 手抖幅度（像素）

### 1.2 阅读模式建模

**WPM (Words Per Minute) 泊松分布**

```python
class ReadingSimulator:
    wpm_mean = 200      # 平均阅读速度
    wpm_std = 30        # 标准差
    
    def calculate_time(text, content_type):
        # 1. 统计词数
        # 2. 从泊松分布采样实际WPM
        # 3. 根据内容类型调整（帖子0.6x，长文1.3x）
        # 4. 添加随机性（0.7-1.4x）
        # 5. 最短停留3秒
```

**内容类型乘数**：
| 类型 | 乘数 | 说明 |
|------|------|------|
| profile | 1.0 | 标准阅读 |
| post | 0.6 | 快速浏览 |
| article | 1.3 | 仔细阅读 |
| list | 0.4 | 扫描式 |
| experience | 1.2 | 工作经历仔细看 |

### 1.3 工作节奏管理

**人类作息模拟**

```
工作时间: 09:00 - 18:00
午休:     12:00 - 13:00
连续工作: 45分钟（上限）
休息:     5-15分钟（随机）
```

**实现逻辑**：
- 非工作时间拒绝执行
- 每45分钟强制休息
- 任务间随机停顿（5秒±50%）

---

## 2. 浏览器管理层 (Browser Management)

### 2.1 反检测策略

**覆盖的关键检测点**：

```javascript
// 1. WebDriver 检测
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// 2. Chrome 对象伪装
window.chrome = {
    runtime: {},
    loadTimes: function() {},
    csi: function() {},
    app: {}
};

// 3. 插件列表（真实化）
navigator.plugins = [
    {name: "Chrome PDF Plugin", ...},
    {name: "Chrome PDF Viewer", ...}
];

// 4. 语言设置
navigator.languages = ['en-US', 'en'];

// 5. Permissions API 重写
navigator.permissions.query = (params) => {
    // 返回合理默认值
};
```

### 2.2 会话管理

**持久化策略**：
- 使用 Playwright 的 `user_data_dir`
- 登录状态保存为本地 Profile
- 下次启动自动恢复，无需重复登录

**多账号隔离**：
```
data/profiles/
├── linkedin_01/    # 小号1
├── linkedin_02/    # 小号2（备用）
└── ...
```

---

## 3. 认知理解层 (Cognitive Layer)

### 3.1 LLM 人才评估

**评估维度**：

```yaml
评估框架:
  AI能力:
    等级: junior / mid / senior / expert
    证据: 工作年限、项目描述、技术栈
  
  Wireless能力:
    等级: junior / mid / senior / expert
    证据: 领域关键词、专利、论文
  
  综合匹配:
    分数: 0-1
    权重: AI能力 40% + Wireless能力 40% + 背景 20%
```

**提示词设计**（简化版）：

```
你是一个资深HR和AI领域专家。
请分析以下LinkedIn档案，评估其与"AI+Wireless交叉领域研究"的匹配度。

输入：
- 档案文本内容
- 目标画像要求

输出格式（JSON）：
{
  "ai_capability": {"level": "senior", "evidence": "..."},
  "wireless_capability": {"level": "mid", "evidence": "..."},
  "overall_score": 0.75,
  "priority": "HIGH",
  "match_reasons": ["..."],
  "concerns": ["..."],
  "recommendation": "..."
}
```

### 3.2 降级策略

当 LLM 不可用时，使用规则评估：

```python
def rule_based_evaluate(profile_text, keywords):
    score = 0
    
    # 关键词匹配
    for keyword in keywords:
        if keyword in profile_text.lower():
            score += 0.1
    
    # 职位级别
    if "senior" in title or "lead" in title:
        score += 0.2
    if "phd" in education:
        score += 0.15
    
    return min(score, 1.0)
```

---

## 4. 任务调度层 (Task Orchestration)

### 4.1 限流策略

**核心参数**：

```yaml
limits:
  daily_profiles: 3        # 每日查看上限（保守起步）
  daily_connections: 5     # 每日连接请求上限
  cooldown_min: 30         # 档案间最短冷却（秒）
  cooldown_max: 60         # 档案间最长冷却（秒）
  session_duration: 45min  # 连续工作上限
```

**随机化策略**：
- 冷却时间在 30-60 秒间随机
- 阅读速度在 200±30 WPM 间随机
- 鼠标轨迹每次不同

### 4.2 断点续传

```python
class SessionManager:
    def save_checkpoint(self):
        # 保存当前进度到 JSON
        {
            "last_profile_url": "...",
            "candidates_viewed": 3,
            "candidates_saved": 2,
            "timestamp": "..."
        }
    
    def resume_from_checkpoint(self):
        # 从断点恢复
```

---

## 5. 数据沉淀层 (Data Persistence)

### 5.1 人才档案 Schema

```json
{
  "id": "yousef_shawky_ba0239167",
  "source": "linkedin",
  "url": "https://www.linkedin.com/in/yousef-shawky-ba0239167",
  "name": "Yousef Shawky",
  "title": "Senior AI Researcher",
  "company": "Bell Labs",
  
  "evaluation": {
    "ai_capability": {
      "level": "expert",
      "score": 0.9,
      "evidence": "10年AI研究，多篇arXiv论文"
    },
    "wireless_capability": {
      "level": "senior", 
      "score": 0.8,
      "evidence": "5年无线AI项目，3项专利"
    },
    "overall_score": 0.75,
    "priority": "HIGH",
    "match_reasons": ["强AI+Wireless交叉", "PhD+大厂经验"],
    "recommendation": "立即联系"
  },
  
  "raw_snapshot": {
    "html_hash": "...",
    "screenshot_path": "...",
    "collected_at": "2026-03-02T21:45:00Z"
  }
}
```

### 5.2 每日报告生成

```python
def generate_daily_report(date, findings):
    report = f"""
    # 人才研究发现汇总 - {date}
    
    ## 总计: {len(findings)} 人
    - 🔥 高优先级: {count_high} 人
    - ⭐ 中优先级: {count_medium} 人
    
    ## 🏆 TOP 人才
    {render_top_candidates(findings, top_n=5)}
    """
    
    # 保存到 data/findings/{date}/report.md
```

---

## 6. 扩展设计

### 6.1 多平台架构

```
┌────────────────────────────────────────┐
│           TalentIntel Core             │
├────────────────────────────────────────┤
│  Platform Adapters                     │
│  ├── LinkedInAdapter  (已实现)        │
│  ├── GitHubAdapter    (计划中)        │
│  ├── ScholarAdapter   (计划中)        │
│  └── TwitterAdapter   (计划中)        │
├────────────────────────────────────────┤
│  Common Interface                      │
│  - search(criteria)                    │
│  - view_profile(url)                   │
│  - extract_data(html)                  │
└────────────────────────────────────────┘
```

### 6.2 知识图谱

```
人才节点: {id, name, skills, company}
    ↓
关系边:
  - 同事关系 (同公司)
  - 合作关系 (共同论文)
  - 引用关系 (技术博客引用)
  - 社交关系 (互相关注)
```

---

## 7. 监控与调试

### 7.1 日志级别

```python
# DEBUG: 鼠标轨迹坐标、阅读时间计算
# INFO:  页面访问、人才评估结果
# WARN:  限流触发、页面加载超时
# ERROR: 登录失败、Anti-bot检测
```

### 7.2 调试工具

```bash
# 查看搜索页面结构
python3 tests/debug_search.py

# 测试单个档案评估
python3 tests/test_profile_view.py --url "..."

# 检查 LLM 配置
python3 -c "from src.cognition.llm import LLMClient; print(LLMClient().test())"
```

---

## 8. 安全清单

部署前检查：

- [ ] 使用小号而非主账号
- [ ] 每日上限设为3-5人（起步）
- [ ] 密码通过环境变量注入
- [ ] API Key 不提交到 Git
- [ ] 运行日志定期清理
- [ ] 遵守目标平台 ToS
