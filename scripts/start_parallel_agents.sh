#!/bin/bash
# 启动并行开发代理

PROJECT_DIR="/Users/cooga/.openclaw/workspace/Project"

echo "=== 启动 TalentIntel 并行开发代理 ==="
echo "时间: $(date)"
echo ""

# 1. 开发代理 - 在 TalentIntel-dev 开发 Milestone 2
echo "[1/3] 启动开发代理 (Developer) - Milestone 2..."
cd "$PROJECT_DIR/TalentIntel-dev"
claude --dangerously-skip-permissions -p "
你是 TalentIntel 项目的开发工程师。

## 任务
完成 Milestone 2：自动化监控和信号检测系统

## 详细任务文档
请阅读: tasks/milestone2.md

## 核心任务
1. 实现 MonitoringScheduler (APScheduler)
2. 实现 GitHubMonitor (事件监控)
3. 实现 BaselineLearner (基线学习)
4. 实现 TemporalAnalyzer (时间异常检测)
5. 实现 SignalService (信号管理)
6. 增强 CLI 命令

## 开发目录
/Users/cooga/.openclaw/workspace/Project/TalentIntel-dev
分支: develop

## 参考
- Milestone 1 代码已在当前目录
- docs/ARCHITECTURE.md 架构文档

## 输出
完成后提交代码到 develop 分支。
遇到阻塞问题立即停止并说明。
" &
echo "开发代理已启动 (PID: $!)"
echo ""

# 2. 测试代理 - 在 TalentIntel-test 测试功能
echo "[2/3] 启动测试代理 (Tester)..."
cd "$PROJECT_DIR/TalentIntel-test"
claude --dangerously-skip-permissions -p "
你是 TalentIntel 项目的测试工程师。

## 任务
测试 Milestone 1 功能，发现问题并记录

## 详细任务文档
请阅读: tasks/testing.md

## 核心任务
1. 安装项目: pip install -e .
2. 初始化: sentinel init
3. 添加测试实体: sentinel add <真实GitHub用户>
4. 测试所有 CLI 命令
5. 验证数据库操作
6. 测试 GitHub API 调用（如有token）
7. 记录问题到 test-reports/YYYYMMDD.md

## 测试目录
/Users/cooga/.openclaw/workspace/Project/TalentIntel-test
分支: test-branch

## 输出
- test-reports/YYYYMMDD.md - 问题报告
- 定期反馈问题给开发代理

遇到阻塞问题立即停止并说明。
" &
echo "测试代理已启动 (PID: $!)"
echo ""

# 3. 审查代理 - 代码质量监控
echo "[3/3] 启动审查代理 (Reviewer)..."
cd "$PROJECT_DIR/TalentIntel"
claude --dangerously-skip-permissions -p "
你是 TalentIntel 项目的代码审查员。

## 任务
监控代码质量，收集问题，总结经验

## 详细任务文档
请阅读: tasks/review.md

## 核心任务
1. 检查代码质量: mypy, ruff
2. 对照架构文档审查一致性
3. 每 30 分钟检查一次开发代理的提交
4. 记录问题到 reviews/review-YYYYMMDD.md
5. 创建 docs/BEST_PRACTICES.md
6. 创建 docs/LESSONS_LEARNED.md

## 审查目录
/Users/cooga/.openclaw/workspace/Project/TalentIntel
分支: main

## 监控范围
- TalentIntel-dev (开发分支)
- TalentIntel-test (测试分支)

## 输出
- reviews/review-YYYYMMDD.md
- docs/BEST_PRACTICES.md
- docs/LESSONS_LEARNED.md

持续运行，定期汇报发现。
" &
echo "审查代理已启动 (PID: $!)"
echo ""

echo "=== 所有代理已启动 ==="
echo "使用 'ps aux | grep claude' 查看进程"
echo "使用 './scripts/check_agents.sh' 检查状态"
