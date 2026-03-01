#!/bin/bash
# TalentIntel 开发监控脚本
# 用法: ./scripts/check_progress.sh

echo "=== TalentIntel 开发进展检查 ==="
echo "时间: $(date)"
echo ""

cd /Users/cooga/.openclaw/workspace/Project/TalentIntel

echo "【Git 状态】"
git status --short
if [ -z "$(git status --short)" ]; then
    echo "  工作区干净，无新文件"
else
    echo "  检测到新文件或修改!"
fi
echo ""

echo "【最近提交】"
git log --oneline -5
echo ""

echo "【文件统计】"
echo "  Python 文件: $(find . -name '*.py' -not -path './.git/*' | wc -l)"
echo "  测试文件: $(find . -name 'test_*.py' -o -name '*_test.py' | wc -l)"
echo "  代码行数: $(find . -name '*.py' -not -path './.git/*' -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')"
echo ""

echo "【Claude Code 进程】"
if pgrep -f "claude.*TalentIntel" > /dev/null; then
    echo "  ✅ Claude Code 正在运行"
    ps aux | grep "claude.*-p" | grep -v grep | wc -l | xargs echo "  运行进程数:"
else
    echo "  ❌ Claude Code 未运行"
fi
echo ""

echo "【关键文件检查】"
if [ -f "requirements.txt" ]; then
    echo "  ✅ requirements.txt 存在"
fi
if [ -f "src/models.py" ] || [ -f "src/models/__init__.py" ]; then
    echo "  ✅ 数据库模型已创建"
fi
if [ -f "src/collectors/github.py" ]; then
    echo "  ✅ GitHub 采集器已创建"
fi
if [ -f "src/cli/main.py" ] || [ -f "sentinel.py" ]; then
    echo "  ✅ CLI 工具已创建"
fi
echo ""

echo "=== 检查完成 ==="
