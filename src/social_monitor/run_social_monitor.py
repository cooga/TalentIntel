#!/usr/bin/env python3
"""
TalentIntel Phase 2A - Social Monitor Entry Point
社交监控启动器

功能:
1. Profile Tracker - 档案变化追踪
2. Activity Scanner - 动态扫描
3. 结果汇总与通知

Usage:
    python3 run_social_monitor.py [--mode daily|full] [--limit N]
"""

import json
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

from profile_tracker import ProfileTracker
from activity_scanner import ActivityScanner

LINKEDIN_PROFILE = "/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/profiles/linkedin_01"


class SocialMonitor:
    """社交监控主控"""
    
    def __init__(self):
        self.profile_tracker = ProfileTracker()
        self.activity_scanner = ActivityScanner()
        self.results_dir = Path("/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/monitor_results")
        self.results_dir.mkdir(exist_ok=True)
    
    async def run(self, mode: str = "daily", limit: int = 10):
        """
        运行社交监控
        
        Args:
            mode: daily (只监控变化) / full (完整扫描)
            limit: 处理的候选人数量
        """
        print("="*80)
        print(f"🚀 TalentIntel Phase 2A - Social Monitor")
        print(f"模式: {mode} | 限额: {limit}人")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # 加载候选人
        candidates = self._load_candidates()
        
        if not candidates:
            print("❌ 没有符合条件的候选人")
            return
        
        print(f"\n📊 候选人池: {len(candidates)}人")
        
        # 选择监控对象
        if mode == "daily":
            # 每日模式：优先监控高分候选人
            monitor_targets = sorted(
                candidates,
                key=lambda x: (-x.get('match_score', 0), x.get('last_checked', ''))
            )[:limit]
        else:
            # 完整模式：随机选择
            monitor_targets = candidates[:limit]
        
        print(f"监控目标: {len(monitor_targets)}人")
        for i, c in enumerate(monitor_targets, 1):
            print(f"  {i}. {c['name']} ({c.get('company', 'N/A')}) - 匹配度: {c.get('match_score', 0):.2f}")
        
        # 启动监控
        all_results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=LINKEDIN_PROFILE,
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            for i, candidate in enumerate(monitor_targets, 1):
                print(f"\n{'='*80}")
                print(f"[{i}/{len(monitor_targets)}] {candidate['name']}")
                print(f"{'='*80}")
                
                result = await self._monitor_single(browser, candidate, mode)
                all_results.append(result)
                
                # 更新检查时间
                self._update_last_checked(candidate['linkedin_url'])
            
            await browser.close()
        
        # 生成报告
        report = self._generate_report(all_results)
        
        # 保存结果
        self._save_results(report)
        
        # 发送通知（如果有重要信号）
        await self._send_notifications(report)
        
        return report
    
    async def _monitor_single(self, browser, candidate: dict, mode: str) -> dict:
        """监控单个候选人"""
        result = {
            'candidate_id': candidate.get('linkedin_url', ''),
            'name': candidate['name'],
            'timestamp': datetime.now().isoformat(),
            'profile_result': None,
            'activity_result': None,
            'hot_signals': []
        }
        
        # 1. Profile Tracker
        try:
            snapshot, delta, signals = await self.profile_tracker.track_candidate(
                browser, candidate
            )
            
            result['profile_result'] = {
                'has_snapshot': snapshot is not None,
                'has_changes': delta is not None,
                'changes': delta.to_dict() if delta else None,
                'signals': [s.to_dict() for s in signals]
            }
            
            # 收集热信号
            for signal in signals:
                if signal.signal_type in ['open_to_work', 'company_change', 'promotion']:
                    result['hot_signals'].append({
                        'type': signal.signal_type,
                        'confidence': signal.confidence,
                        'evidence': signal.evidence
                    })
            
        except Exception as e:
            print(f"   ❌ Profile Tracker 错误: {e}")
            result['profile_result'] = {'error': str(e)}
        
        # 2. Activity Scanner（完整模式才运行）
        if mode == "full":
            try:
                activity_result = await self.activity_scanner.scan_candidate(
                    browser, candidate, days=30
                )
                result['activity_result'] = activity_result
                
                # 收集热信号
                for achievement in activity_result.get('achievements', []):
                    if achievement['confidence'] > 0.8:
                        result['hot_signals'].append({
                            'type': achievement['signal_type'],
                            'confidence': achievement['confidence'],
                            'evidence': achievement['evidence']
                        })
                
            except Exception as e:
                print(f"   ❌ Activity Scanner 错误: {e}")
                result['activity_result'] = {'error': str(e)}
        
        # 3. 信号总结
        if result['hot_signals']:
            print(f"\n   🔥 热信号 ({len(result['hot_signals'])}个):")
            for sig in result['hot_signals']:
                print(f"      - {sig['type']}: {sig['evidence'][:60]}...")
        
        return result
    
    def _load_candidates(self) -> list:
        """加载候选人"""
        db_path = '/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/clean_candidates_db.json'
        
        try:
            with open(db_path, 'r') as f:
                db = json.load(f)
            
            candidates = db.get('candidates', [])
            
            # 只监控已验证的候选人
            verified = [c for c in candidates if c.get('verified') == True]
            
            return verified
            
        except Exception as e:
            print(f"❌ 加载候选人失败: {e}")
            return []
    
    def _update_last_checked(self, linkedin_url: str):
        """更新最后检查时间"""
        db_path = '/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/clean_candidates_db.json'
        
        try:
            with open(db_path, 'r') as f:
                db = json.load(f)
            
            for c in db.get('candidates', []):
                if c.get('linkedin_url') == linkedin_url:
                    c['last_checked'] = datetime.now().isoformat()
                    break
            
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(db, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ 更新检查时间失败: {e}")
    
    def _generate_report(self, results: list) -> dict:
        """生成监控报告"""
        total = len(results)
        
        # 统计信号
        all_hot_signals = []
        profile_changes = 0
        open_to_work_count = 0
        company_changes = 0
        
        for r in results:
            if r.get('hot_signals'):
                all_hot_signals.extend(r['hot_signals'])
            
            profile_result = r.get('profile_result', {})
            if profile_result and profile_result.get('has_changes'):
                profile_changes += 1
            
            for sig in r.get('hot_signals', []):
                if sig['type'] == 'open_to_work':
                    open_to_work_count += 1
                elif sig['type'] == 'company_change':
                    company_changes += 1
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_monitored': total,
                'profile_changes': profile_changes,
                'hot_signals': len(all_hot_signals),
                'open_to_work': open_to_work_count,
                'company_changes': company_changes
            },
            'hot_leads': [
                {
                    'name': r['name'],
                    'signals': r['hot_signals']
                }
                for r in results if r.get('hot_signals')
            ],
            'details': results
        }
        
        return report
    
    def _save_results(self, report: dict):
        """保存结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = self.results_dir / f"monitor_report_{timestamp}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*80}")
        print(f"💾 报告已保存: {result_file}")
        print(f"{'='*80}")
    
    async def _send_notifications(self, report: dict):
        """发送通知（如果有重要信号）"""
        hot_leads = report.get('hot_leads', [])
        
        if not hot_leads:
            print("\n📭 无重要信号，跳过通知")
            return
        
        print(f"\n🔔 发送通知 ({len(hot_leads)}个热线索)")
        
        # TODO: 集成 Discord Webhook
        # 这里简化处理，只打印通知内容
        
        for lead in hot_leads[:5]:  # 最多5个
            print(f"\n🎯 {lead['name']}")
            for sig in lead['signals']:
                print(f"   - {sig['type']} (置信度: {sig['confidence']:.2f})")


def main():
    parser = argparse.ArgumentParser(description='TalentIntel Social Monitor')
    parser.add_argument('--mode', choices=['daily', 'full'], default='daily',
                       help='监控模式: daily (每日检查) / full (完整扫描)')
    parser.add_argument('--limit', type=int, default=10,
                       help='处理的候选人数量')
    
    args = parser.parse_args()
    
    monitor = SocialMonitor()
    asyncio.run(monitor.run(mode=args.mode, limit=args.limit))


if __name__ == "__main__":
    main()
