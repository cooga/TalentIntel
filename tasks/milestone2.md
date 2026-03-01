# TalentIntel - Milestone 2 开发任务

## 任务目标
完成自动化监控和信号检测系统开发，实现目标人物的 GitHub 活动能被自动监控，异常信号被记录。

## 详细需求

### 1. 定时调度系统 (APScheduler)
实现 `MonitoringScheduler` 类：
- `src/core/scheduler.py`
- 使用 APScheduler 进行任务调度
- 支持间隔任务 (IntervalTrigger)
- 支持定时任务 (CronTrigger)
- 任务管理：添加、删除、暂停、恢复、立即触发

### 2. GitHub Events 监控
实现 `GitHubMonitor` 类：
- `src/monitor/github_monitor.py`
- 自动获取 GitHub Profile 变化
- 获取并存储 GitHub Events
- 检测 Profile 变化并生成事件
- 支持单个实体监控和批量监控

### 3. 基线自动学习
实现 `BaselineLearner` 类：
- `src/monitor/baseline_learner.py`
- 分析历史事件数据
- 学习提交模式（按天、按小时）
- 学习活跃时间段
- 计算活动频率统计
- 将基线数据保存到 Entity

### 4. 时间异常检测
实现 `TemporalAnalyzer` 类：
- `src/monitor/temporal_analyzer.py`
- 检测异常提交时间
- 检测提交频率异常（飙升/下降）
- 检测活动模式变化
- 检测周末活动异常
- 生成异常信号

### 5. 信号存储与查询
实现 `SignalService` 类：
- `src/sentinel/signal_service.py`
- 创建信号（支持去重）
- 查询信号（多条件过滤）
- 标记信号已处理
- 获取信号统计
- 批量操作

## 技术要求
- Python 3.10+
- APScheduler 3.x (异步支持)
- SQLAlchemy 2.0 (异步)
- 与 Milestone 1 代码风格保持一致
- 使用 structlog 进行日志记录

## 验收标准
- [ ] MonitoringScheduler 能够调度和执行定时任务
- [ ] GitHubMonitor 能够自动获取 GitHub 数据并检测变化
- [ ] BaselineLearner 能够从历史数据学习行为基线
- [ ] TemporalAnalyzer 能够检测时间相关的异常
- [ ] SignalService 能够存储和查询信号
- [ ] 所有组件能够协同工作
- [ ] CLI 新增监控相关命令

## CLI 命令扩展
新增以下命令：
- `sentinel monitor start` - 启动监控调度器
- `sentinel monitor status` - 查看调度器状态
- `sentinel monitor run` - 手动运行一次监控
- `sentinel baseline learn <entity_id>` - 学习实体基线
- `sentinel baseline update-all` - 更新所有实体基线
- `sentinel signals list` - 列出信号
- `sentinel signals stats` - 查看信号统计

## 文件结构
```
src/
├── core/
│   ├── database.py      # 已有
│   └── scheduler.py     # 新增 - 调度器
├── monitor/
│   ├── __init__.py      # 新增
│   ├── github_monitor.py    # 新增 - GitHub 监控
│   ├── baseline_learner.py  # 新增 - 基线学习
│   └── temporal_analyzer.py # 新增 - 时间分析
├── sentinel/
│   ├── entity_service.py    # 已有
│   └── signal_service.py    # 新增 - 信号服务
└── cli/
    └── main.py          # 更新 - 添加新命令
```

## 注意事项
1. 保持异步编程风格
2. 使用现有的数据库会话管理
3. 日志使用结构化输出
4. 错误处理要完善
5. 支持优雅关闭

## 输出
完成所有代码后，提交到 git 并推送。
