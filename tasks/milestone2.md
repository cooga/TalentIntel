# TalentIntel - Milestone 2 开发任务

## 任务目标
完成自动化监控和信号检测系统。

## 详细需求

### 1. 定时调度系统 (src/triggers/scheduler.py)
实现 `MonitoringScheduler` 类：
- 使用 APScheduler 实现异步任务调度
- 支持分层监控频率：
  - 高频(30min): GitHub Events
  - 中频(6h): Profile 元数据
  - 低频(每日): 深度分析
- 配置化调度规则
- 优雅启停机制

### 2. GitHub Events 监控 (src/collectors/github_monitor.py)
实现 `GitHubMonitor` 类：
- 监控所有活跃实体的 GitHub 活动
- 使用差分检测发现变化
- 将变化存储为 Signal
- 更新 PlatformSnapshot
- 异常处理和重试机制

### 3. 基线自动学习 (src/core/baseline.py)
实现 `BaselineLearner` 类：
- 收集实体的历史行为数据
- 计算正常模式：
  - 活跃时间分布
  - 提交频率模式
  - 互动模式
- 存储基线到 Entity.baseline_commit_pattern
- 基线置信度评估

### 4. 时间异常检测 (src/inference/temporal_anomaly.py)
实现 `TemporalAnalyzer` 类：
- 分析 commit 时间模式变化
- 检测信号：
  - 工作日活跃度下降 >30%
  - 活动时间分散度增加
  - 深夜提交激增
- 生成异常 Signal

### 5. 信号存储与管理 (src/sentinel/signal_service.py)
实现 `SignalService` 类：
- create_signal() - 创建信号
- get_signals() - 查询信号（支持过滤）
- mark_signal_processed() - 标记已处理
- get_unprocessed_signals() - 获取未处理信号

### 6. CLI 增强 (src/cli/main.py 新增命令)
添加命令：
- `sentinel run` - 启动监控调度器（前台运行）
- `sentinel run --daemon` - 后台运行（以后实现）
- `sentinel signals [entity_id]` - 查看信号列表
- `sentinel baseline learn <entity_id>` - 手动学习基线

## 技术要求
- 所有数据库操作使用 AsyncSession
- 调度器使用 APScheduler 的 AsyncIOScheduler
- 信号处理使用队列模式，便于后续扩展
- 完善的日志记录
- 类型注解完整

## 验收标准
- [ ] 调度器能按计划执行监控任务
- [ ] 能检测 GitHub profile 变化并生成 Signal
- [ ] 能为实体学习基线并存储
- [ ] 能检测时间异常并生成 Signal
- [ ] CLI 命令可用
- [ ] 代码通过 mypy 类型检查

## 开发 Worktree
在 `/Users/cooga/.openclaw/workspace/Project/TalentIntel-dev` 目录开发
基于 `develop` 分支

## 参考文档
- `docs/ARCHITECTURE.md` - 架构设计
- `docs/DEVELOPMENT_PLAN.md` - 开发计划
- Milestone 1 代码作为基础
