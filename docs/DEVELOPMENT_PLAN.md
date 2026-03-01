# TalentIntel 开发计划与里程碑

> **项目**: Sentinel - 人才情报监控系统  
> **启动日期**: 2026-03-01  
> **开发模式**: Claude Code 主开发 + Kobe 项目管理

---

## 开发里程碑

### ✅ Milestone 1: 核心骨架 ~~(3-4天)~~ 
**状态**: 已完成 (2026-03-01)  
**耗时**: ~1小时  
**目标**: 可运行的基础框架

**交付物**:
- [x] 数据库模型 (SQLAlchemy)
- [x] 实体管理模块 (增删改查)
- [x] GitHub 基础监控 (差分检测)
- [x] CLI 工具 (添加目标、查看状态)
- [x] 配置系统

**检查点**: 能够添加目标人物，手动触发 GitHub 数据获取 ✅

**代码统计**:
- 18 个 Python 文件
- ~2,300 行代码
- 5 个数据模型 (Entity, Event, Signal, Alert, PlatformSnapshot)
- 完整的 CLI 命令 (init, add, list, status, fetch, delete, update)

---

### ✅ Milestone 2: 监控与信号 ~~(3-4天)~~
**状态**: 已完成 (2026-03-01)
**耗时**: ~1小时
**目标**: 自动化监控和信号检测

**交付物**:
- [x] 定时调度系统 (APScheduler)
- [x] GitHub Events 监控
- [x] 基线自动学习
- [x] 时间异常检测
- [x] 信号存储与查询

**检查点**: 目标人物的 GitHub 活动能被自动监控，异常信号被记录 ✅

**代码统计**:
- 新增 5 个核心模块
- MonitoringScheduler (APScheduler)
- GitHubMonitor (事件监控)
- BaselineLearner (基线学习)
- TemporalAnalyzer (时间异常检测)
- SignalService (信号服务)
- CLI 新增命令: monitor, baseline, signals

---

### 🎯 Milestone 3: 状态机与推断 (4-5天)
**目标**: 智能状态推断

**交付物**:
- [ ] 状态机引擎实现
- [ ] 提交取证分析
- [ ] 状态转换规则
- [ ] 置信度评分
- [ ] Discord 告警通知

**检查点**: 系统能自动推断职业状态并发送告警

---

### 🎯 Milestone 4: LinkedIn 集成 (5-6天)
**目标**: LinkedIn 数据获取

**交付物**:
- [ ] Proxycurl 适配器
- [ ] 反检测采集器框架
- [ ] LinkedIn 数据提取
- [ ] 多源数据融合
- [ ] 交叉验证

**检查点**: LinkedIn 数据与 GitHub 数据能交叉验证

---

### 🎯 Milestone 5: 完善与优化 (4-5天)
**目标**: 生产就绪

**交付物**:
- [ ] API 服务 (FastAPI)
- [ ] 关系图谱可视化
- [ ] 测试覆盖 > 70%
- [ ] 文档完善
- [ ] Docker 部署

**检查点**: 完整的系统可部署运行

---

## Git Worktree 策略

在 Milestone 3 完成后建立 worktree：

```bash
# 主分支: 稳定功能
git branch main

# 开发分支: 新功能开发
git worktree add ../TalentIntel-dev develop

# Bug 修复分支: 紧急修复
git worktree add ../TalentIntel-hotfix hotfix
```

**工作流**:
- `main`: 稳定版本，只有通过测试的代码
- `develop`: 功能开发，每日合并到 main
- `hotfix`: 紧急修复，直接基于 main

---

## 检查机制

### 每日检查清单
- [ ] 代码提交记录审查
- [ ] 功能完成情况对比计划
- [ ] 测试通过率
- [ ] 阻塞问题识别

### 里程碑检查清单
- [ ] 功能完整性验收
- [ ] 代码质量审查
- [ ] 文档同步更新
- [ ] 下一阶段计划调整

---

## 技术债务追踪

| 项目 | 严重程度 | 计划解决时间 |
|------|----------|-------------|
| 代理池管理 | 中 | Milestone 4 |
| 并发控制优化 | 中 | Milestone 5 |
| 测试覆盖补充 | 低 | Milestone 5 |

---

## 风险与应对

| 风险 | 概率 | 应对策略 |
|------|------|----------|
| LinkedIn 反爬升级 | 高 | 优先完成 Tier 1 API 方案 |
| GitHub API 限流 | 中 | 实现 ETag 缓存和退避策略 |
| 开发进度延迟 | 中 | 每 2 天检查，及时调整范围 |

---

**最后更新**: 2026-03-01
**当前进度**: Milestone 1 ✅ 完成 | Milestone 2 ✅ 完成 | 准备开始 Milestone 3
