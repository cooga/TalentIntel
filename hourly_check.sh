#!/bin/bash
#
# TalentIntel 每小时华人人才监控脚本
# 添加到crontab: 0 * * * * /Users/cooga/.openclaw/workspace/Project/TalentIntel/hourly_check.sh
#

TALENT_INTEL_DIR="/Users/cooga/.openclaw/workspace/Project/TalentIntel"
LOG_FILE="$TALENT_INTEL_DIR/monitor.log"
STATE_FILE="$TALENT_INTEL_DIR/.monitor_state.json"
DATA_DIR="$TALENT_INTEL_DIR/data/daily"

# 记录日志
echo "========================================" >> "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') - 监控运行" >> "$LOG_FILE"

cd "$TALENT_INTEL_DIR" || exit 1

# 初始化状态文件
if [ ! -f "$STATE_FILE" ]; then
    echo '{"run_count":0,"empty_count":0,"total_chinese":5,"known_names":["Wei C.","Jenny Chu","Wai San Wong","Yaxiong Xie","Xianbin Wang"],"last_run":""}' > "$STATE_FILE"
fi

# 读取当前状态
RUN_COUNT=$(python3 -c "import json; print(json.load(open('$STATE_FILE'))['run_count'])")
EMPTY_COUNT=$(python3 -c "import json; print(json.load(open('$STATE_FILE'))['empty_count'])")
TOTAL_CHINESE=$(python3 -c "import json; print(json.load(open('$STATE_FILE'))['total_chinese'])")

RUN_COUNT=$((RUN_COUNT + 1))
echo "第 $RUN_COUNT 轮检索" >> "$LOG_FILE"

# 运行一轮bigtech挖掘
echo "正在运行bigtech_talent_miner.py..." >> "$LOG_FILE"
python3 scripts/bigtech_talent_miner.py >> "$LOG_FILE" 2>&1 &
PID=$!
sleep 600
kill $PID 2>/dev/null || true
wait $PID 2>/dev/null || true

# 统计今日华人候选人
TODAY=$(date +%Y-%m-%d)
REPORT_FILE="$DATA_DIR/$TODAY/FINAL_REPORT.md"

if [ -f "$REPORT_FILE" ]; then
    # 从报告中统计华人数量
    CURRENT_CHINESE=$(grep -c "确认华人" "$REPORT_FILE" 2>/dev/null || echo "0")
    echo "当前报告中华人数量: $CURRENT_CHINESE" >> "$LOG_FILE"
else
    echo "今日报告不存在" >> "$LOG_FILE"
    CURRENT_CHINESE=$TOTAL_CHINESE
fi

# 判断是否发现新的华人
if [ "$CURRENT_CHINESE" -gt "$TOTAL_CHINESE" ]; then
    NEW_FOUND=$((CURRENT_CHINESE - TOTAL_CHINESE))
    echo "✅ 发现 $NEW_FOUND 位新华人候选人!" >> "$LOG_FILE"
    
    # 发送通知
    osascript -e "display notification \"发现 $NEW_FOUND 位新华人候选人\" with title \"TalentIntel监控\"" 2>/dev/null || true
    
    # 重置empty计数
    EMPTY_COUNT=0
    TOTAL_CHINESE=$CURRENT_CHINESE
else
    echo "⚠️ 本轮无新华人候选人" >> "$LOG_FILE"
    EMPTY_COUNT=$((EMPTY_COUNT + 1))
fi

echo "连续无新发现: $EMPTY_COUNT/3" >> "$LOG_FILE"

# 更新状态文件
python3 -c "
import json
state = {
    'run_count': $RUN_COUNT,
    'empty_count': $EMPTY_COUNT,
    'total_chinese': $TOTAL_CHINESE,
    'last_run': '$(date -Iseconds)',
    'status': 'running'
}
with open('$STATE_FILE', 'w') as f:
    json.dump(state, f, indent=2)
"

# 检查是否达到停止条件
if [ "$EMPTY_COUNT" -ge 3 ]; then
    echo "🎉 连续3次无新发现，监控完成!" >> "$LOG_FILE"
    osascript -e "display notification \"华人人才监控完成，累计发现 $TOTAL_CHINESE 人\" with title \"TalentIntel完成\"" 2>/dev/null || true
    
    # 禁用cron任务
    crontab -l | grep -v "hourly_check.sh" | crontab -
    echo "已自动停止定时任务" >> "$LOG_FILE"
fi

echo "========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
