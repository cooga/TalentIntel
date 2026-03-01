#!/bin/bash
# 并行代理状态检查脚本

echo "=== TalentIntel 并行开发代理状态 ==="
echo "时间: $(date)"
echo ""

PROJECT_BASE="/Users/cooga/.openclaw/workspace/Project"

# 检查 Claude Code 进程
echo "【代理进程状态】"
CLAUDE_PIDS=$(pgrep -f "claude.*TalentIntel" | wc -l)
echo "运行中的 Claude 进程数: $CLAUDE_PIDS"
ps aux | grep "claude.*TalentIntel" | grep -v grep | awk '{print "  PID: " $2 " - " $11 " " $12}'
echo ""

# 检查各个 worktree
echo "【Worktree 状态】"
cd "$PROJECT_BASE/TalentIntel"
git worktree list
echo ""

# 检查开发分支最新提交
echo "【开发分支 (TalentIntel-dev) 最新提交】"
cd "$PROJECT_BASE/TalentIntel-dev"
git log --oneline -3 2>/dev/null || echo "  无法获取"
echo ""

# 检查测试分支
echo "【测试分支 (TalentIntel-test) 最新提交】"
cd "$PROJECT_BASE/TalentIntel-test"
git log --oneline -3 2>/dev/null || echo "  无法获取"
echo ""

# 检查测试报告
echo "【测试报告】"
if [ -d "$PROJECT_BASE/TalentIntel-test/test-reports" ]; then
    ls -la "$PROJECT_BASE/TalentIntel-test/test-reports/" 2>/dev/null
else
    echo "  暂无测试报告"
fi
echo ""

# 检查审查报告
echo "【审查报告】"
if [ -d "$PROJECT_BASE/TalentIntel/reviews" ]; then
    ls -la "$PROJECT_BASE/TalentIntel/reviews/" 2>/dev/null
else
    echo "  暂无审查报告"
fi
echo ""

# 检查最佳实践文档
echo "【文档更新】"
if [ -f "$PROJECT_BASE/TalentIntel/docs/BEST_PRACTICES.md" ]; then
    echo "  ✅ BEST_PRACTICES.md 已创建"
else
    echo "  ⏳ BEST_PRACTICES.md 待创建"
fi

if [ -f "$PROJECT_BASE/TalentIntel/docs/LESSONS_LEARNED.md" ]; then
    echo "  ✅ LESSONS_LEARNED.md 已创建"
else
    echo "  ⏳ LESSONS_LEARNED.md 待创建"
fi
echo ""

# 统计代码变更
echo "【代码统计 - 开发分支】"
cd "$PROJECT_BASE/TalentIntel-dev"
find src -name "*.py" 2>/dev/null | wc -l | xargs echo "  Python 文件数:"
find src -name "*.py" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print "  代码行数: " $1}'
echo ""

echo "=== 检查完成 ==="
