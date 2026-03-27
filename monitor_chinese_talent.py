#!/usr/bin/env python3
"""
TalentIntel Monitor - 华人人才持续监控器
每小时运行一次，直到连续3次无新华人候选人为止
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

# 配置
TALENT_INTEL_DIR = os.path.expanduser("~/.openclaw/workspace/Project/TalentIntel")
DATA_DIR = os.path.join(TALENT_INTEL_DIR, "data/daily")
STATE_FILE = os.path.join(TALENT_INTEL_DIR, ".monitor_state.json")

# 连续无新发现次数阈值
EMPTY_THRESHOLD = 3

def load_state():
    """加载监控状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        "run_count": 0,
        "empty_count": 0,
        "total_chinese_found": 0,
        "last_run": None,
        "known_chinese": [],
        "start_time": datetime.now().isoformat()
    }

def save_state(state):
    """保存监控状态"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_today_dir():
    """获取今日数据目录"""
    today = datetime.now().strftime('%Y-%m-%d')
    return os.path.join(DATA_DIR, today)

def count_chinese_candidates():
    """统计今日华人候选人数量"""
    today_dir = get_today_dir()
    if not os.path.exists(today_dir):
        return 0, []
    
    chinese_list = []
    
    # 读取talents_final.json
    final_file = os.path.join(today_dir, "talents_final.json")
    if os.path.exists(final_file):
        try:
            with open(final_file, 'r') as f:
                data = json.load(f)
                for candidate in data:
                    if candidate.get('is_chinese') or candidate.get('华人'):
                        name = candidate.get('name', 'Unknown')
                        chinese_list.append(name)
        except:
            pass
    
    # 也检查report文件
    report_file = os.path.join(today_dir, "FINAL_REPORT.md")
    if os.path.exists(report_file):
        try:
            with open(report_file, 'r') as f:
                content = f.read()
                # 简单统计华人部分
                if "华人候选人" in content:
                    pass
        except:
            pass
    
    return len(chinese_list), chinese_list

def run_talent_search():
    """运行TalentIntel检索"""
    print(f"\n{'='*70}")
    print(f"🚀 第 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 轮检索启动")
    print('='*70)
    
    os.chdir(TALENT_INTEL_DIR)
    
    # 运行bigtech挖掘器
    try:
        result = subprocess.run(
            [sys.executable, "scripts/bigtech_talent_miner.py"],
            capture_output=True,
            text=True,
            timeout=600
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.TimeoutExpired:
        print("❌ 检索超时")
        return False
    except Exception as e:
        print(f"❌ 检索失败: {e}")
        return False

def send_notification(title, message):
    """发送通知"""
    print(f"\n🔔 {title}")
    print(f"   {message}")
    
    # 如果系统支持，发送桌面通知
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}"'
        ], check=False)
    except:
        pass

def main():
    """主函数"""
    print("="*70)
    print("🎯 TalentIntel 华人人才持续监控系统")
    print("="*70)
    print(f"监控间隔: 1小时")
    print(f"停止条件: 连续{EMPTY_THRESHOLD}次无新华人候选人")
    print(f"数据目录: {DATA_DIR}")
    print("="*70)
    
    state = load_state()
    
    print(f"\n📊 当前状态:")
    print(f"   已运行次数: {state['run_count']}")
    print(f"   连续无新发现: {state['empty_count']}/{EMPTY_THRESHOLD}")
    print(f"   累计华人候选人: {state['total_chinese_found']}")
    
    while state['empty_count'] < EMPTY_THRESHOLD:
        # 运行检索
        state['run_count'] += 1
        state['last_run'] = datetime.now().isoformat()
        
        success = run_talent_search()
        
        if success:
            # 统计结果
            current_chinese, names = count_chinese_candidates()
            
            # 找出新发现的华人
            new_chinese = [name for name in names if name not in state['known_chinese']]
            
            if new_chinese:
                # 有新发现
                print(f"\n✅ 发现 {len(new_chinese)} 位新华人候选人!")
                for name in new_chinese:
                    print(f"   - {name}")
                
                state['total_chinese_found'] += len(new_chinese)
                state['known_chinese'].extend(new_chinese)
                state['empty_count'] = 0
                
                send_notification(
                    "TalentIntel: 新发现",
                    f"发现 {len(new_chinese)} 位新华人候选人，累计 {state['total_chinese_found']} 人"
                )
            else:
                # 无新发现
                state['empty_count'] += 1
                print(f"\n⚠️  本轮无新华人候选人 (连续 {state['empty_count']}/{EMPTY_THRESHOLD} 次)")
                
                if state['empty_count'] >= EMPTY_THRESHOLD:
                    send_notification(
                        "TalentIntel: 监控完成",
                        f"连续{EMPTY_THRESHOLD}次无新发现，监控结束。累计发现 {state['total_chinese_found']} 位华人候选人"
                    )
        
        # 保存状态
        save_state(state)
        
        # 检查是否达到停止条件
        if state['empty_count'] >= EMPTY_THRESHOLD:
            print(f"\n{'='*70}")
            print("🎉 监控完成!")
            print('='*70)
            print(f"总运行次数: {state['run_count']}")
            print(f"累计华人候选人: {state['total_chinese_found']}")
            print(f"开始时间: {state['start_time']}")
            print(f"结束时间: {datetime.now().isoformat()}")
            print('='*70)
            break
        
        # 等待1小时
        next_run = datetime.now().timestamp() + 3600
        print(f"\n⏳ 下次检索: {datetime.fromtimestamp(next_run).strftime('%H:%M:%S')}")
        print(f"   (等待1小时...)")
        
        try:
            time.sleep(3600)  # 1小时 = 3600秒
        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断监控")
            save_state(state)
            print(f"状态已保存，可稍后继续")
            break

if __name__ == '__main__':
    main()
