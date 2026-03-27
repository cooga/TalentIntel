#!/usr/bin/env python3
"""
TalentIntel Phase 2A - Profile Tracker
LinkedIn 档案变化追踪器

检测:
1. 职位变动 (position changes)
2. 公司变动 (company changes)
3. 求职信号 (open to work, job seeking preferences)
4. 档案更新频率 (profile update frequency)
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from playwright.async_api import async_playwright

# LinkedIn Profile 路径
LINKEDIN_PROFILE = "/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/profiles/linkedin_01"


@dataclass
class ProfileSnapshot:
    """档案快照"""
    candidate_id: str
    name: str
    headline: str
    current_company: str
    current_title: str
    location: str
    open_to_work: bool
    skills: List[str]
    summary: str
    captured_at: str
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProfileDelta:
    """档案变化"""
    candidate_id: str
    changed_fields: List[str]
    old_values: Dict
    new_values: Dict
    detected_at: str
    significance: str  # high / medium / low
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class JobSeekingSignal:
    """求职信号"""
    candidate_id: str
    signal_type: str  # open_to_work, position_change, frequent_updates, etc.
    confidence: float  # 0-1
    evidence: str
    detected_at: str
    
    def to_dict(self) -> dict:
        return asdict(self)


class ProfileTracker:
    """LinkedIn 档案追踪器"""
    
    def __init__(self, profile_path: str = LINKEDIN_PROFILE):
        self.profile_path = profile_path
        self.snapshot_dir = Path("/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/snapshots")
        self.snapshot_dir.mkdir(exist_ok=True)
    
    async def track_candidate(self, browser, candidate: dict) -> Tuple[Optional[ProfileSnapshot], Optional[ProfileDelta], List[JobSeekingSignal]]:
        """
        追踪单个候选人的档案变化
        
        Returns:
            (新快照, 变化, 求职信号列表)
        """
        candidate_id = candidate.get('linkedin_url', '')
        name = candidate.get('name', '')
        
        print(f"\n🔍 追踪: {name}")
        
        # 1. 获取当前档案
        new_snapshot = await self._capture_profile(browser, candidate)
        if not new_snapshot:
            print(f"   ❌ 无法获取档案")
            return None, None, []
        
        print(f"   ✅ 档案获取成功")
        print(f"   📍 当前: {new_snapshot.current_company} | {new_snapshot.current_title}")
        
        # 2. 加载历史快照
        old_snapshot = self._load_last_snapshot(candidate_id)
        
        # 3. 检测变化
        delta = None
        if old_snapshot:
            delta = self._detect_changes(old_snapshot, new_snapshot)
            if delta:
                print(f"   ⚠️ 检测到变化: {', '.join(delta.changed_fields)}")
        
        # 4. 检测求职信号
        signals = self._detect_job_seeking_signals(new_snapshot, old_snapshot)
        if signals:
            print(f"   🎯 发现 {len(signals)} 个求职信号:")
            for s in signals:
                print(f"      - {s.signal_type} (置信度: {s.confidence:.2f})")
        
        # 5. 保存新快照
        self._save_snapshot(new_snapshot)
        
        return new_snapshot, delta, signals
    
    async def _capture_profile(self, browser, candidate: dict) -> Optional[ProfileSnapshot]:
        """抓取候选人 LinkedIn 档案"""
        linkedin_url = candidate.get('linkedin_url', '')
        
        if not linkedin_url:
            return None
        
        try:
            page = await browser.new_page()
            await page.goto(linkedin_url, timeout=30000)
            await asyncio.sleep(3)  # 等待页面加载
            
            # 提取基本信息
            name = await self._extract_text(page, 'h1') or candidate.get('name', '')
            headline = await self._extract_text(page, '[class*="headline"]') or ""
            
            # 提取当前职位
            current_title = "Unknown"
            current_company = "Unknown"
            
            # 尝试从 headline 解析
            if ' at ' in headline:
                parts = headline.split(' at ')
                current_title = parts[0].strip()
                current_company = parts[1].strip()
            
            # 提取位置
            location = await self._extract_text(page, '[class*="location"]') or ""
            
            # 检测 Open to work
            open_to_work = await self._detect_open_to_work(page)
            
            # 提取技能（简化版）
            skills = []
            
            await page.close()
            
            return ProfileSnapshot(
                candidate_id=linkedin_url,
                name=name,
                headline=headline,
                current_company=current_company,
                current_title=current_title,
                location=location,
                open_to_work=open_to_work,
                skills=skills,
                summary="",
                captured_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            print(f"   ❌ 抓取错误: {e}")
            return None
    
    async def _extract_text(self, page, selector: str) -> str:
        """从页面提取文本"""
        try:
            elem = await page.query_selector(selector)
            if elem:
                return await elem.inner_text()
        except:
            pass
        return ""
    
    async def _detect_open_to_work(self, page) -> bool:
        """检测是否开启 Open to work"""
        try:
            # 检查页面内容是否包含 "Open to work" 标识
            content = await page.content()
            indicators = [
                "Open to work",
                "#OpenToWork",
                "Looking for new opportunities",
                "Actively looking"
            ]
            return any(ind.lower() in content.lower() for ind in indicators)
        except:
            return False
    
    def _load_last_snapshot(self, candidate_id: str) -> Optional[ProfileSnapshot]:
        """加载上次快照"""
        snapshot_file = self.snapshot_dir / f"{self._sanitize_id(candidate_id)}.json"
        
        if not snapshot_file.exists():
            return None
        
        try:
            with open(snapshot_file, 'r') as f:
                data = json.load(f)
                # 加载最后一个快照
                if data and len(data) > 0:
                    last = data[-1]
                    return ProfileSnapshot(**last)
        except Exception as e:
            print(f"   ⚠️ 加载快照失败: {e}")
        
        return None
    
    def _save_snapshot(self, snapshot: ProfileSnapshot):
        """保存快照"""
        snapshot_file = self.snapshot_dir / f"{self._sanitize_id(snapshot.candidate_id)}.json"
        
        snapshots = []
        if snapshot_file.exists():
            try:
                with open(snapshot_file, 'r') as f:
                    snapshots = json.load(f)
            except:
                pass
        
        # 限制历史记录数量（保留最近10个）
        snapshots.append(snapshot.to_dict())
        snapshots = snapshots[-10:]
        
        with open(snapshot_file, 'w') as f:
            json.dump(snapshots, f, indent=2, ensure_ascii=False)
    
    def _detect_changes(self, old: ProfileSnapshot, new: ProfileSnapshot) -> Optional[ProfileDelta]:
        """检测档案变化"""
        changed_fields = []
        old_values = {}
        new_values = {}
        
        # 检查各个字段
        fields_to_check = [
            ('current_company', '公司'),
            ('current_title', '职位'),
            ('headline', '标题'),
            ('location', '位置'),
            ('open_to_work', '求职状态')
        ]
        
        for field, label in fields_to_check:
            old_val = getattr(old, field)
            new_val = getattr(new, field)
            
            if old_val != new_val:
                changed_fields.append(label)
                old_values[field] = old_val
                new_values[field] = new_val
        
        if not changed_fields:
            return None
        
        # 计算重要性
        significance = "low"
        if '公司' in changed_fields or '职位' in changed_fields:
            significance = "high"
        elif '求职状态' in changed_fields:
            significance = "high"
        elif '标题' in changed_fields:
            significance = "medium"
        
        return ProfileDelta(
            candidate_id=new.candidate_id,
            changed_fields=changed_fields,
            old_values=old_values,
            new_values=new_values,
            detected_at=datetime.now().isoformat(),
            significance=significance
        )
    
    def _detect_job_seeking_signals(self, new: ProfileSnapshot, old: Optional[ProfileSnapshot]) -> List[JobSeekingSignal]:
        """检测求职信号"""
        signals = []
        
        # 信号1: Open to work
        if new.open_to_work:
            signals.append(JobSeekingSignal(
                candidate_id=new.candidate_id,
                signal_type="open_to_work",
                confidence=0.95,
                evidence=f"{new.name} 已开启 Open to work 状态",
                detected_at=datetime.now().isoformat()
            ))
        
        # 信号2: 职位变动（如果有旧数据）
        if old:
            if new.current_company != old.current_company:
                signals.append(JobSeekingSignal(
                    candidate_id=new.candidate_id,
                    signal_type="company_change",
                    confidence=0.90,
                    evidence=f"公司变动: {old.current_company} → {new.current_company}",
                    detected_at=datetime.now().isoformat()
                ))
            
            if new.current_title != old.current_title:
                # 判断是否升职或降职
                title_keywords = ['senior', 'staff', 'principal', 'lead', 'director', 'manager']
                old_level = sum(1 for kw in title_keywords if kw in old.current_title.lower())
                new_level = sum(1 for kw in title_keywords if kw in new.current_title.lower())
                
                if new_level > old_level:
                    signal_type = "promotion"
                    evidence = f"升职: {old.current_title} → {new.current_title}"
                elif new_level < old_level:
                    signal_type = "demotion"
                    evidence = f"职位变动: {old.current_title} → {new.current_title}"
                else:
                    signal_type = "title_change"
                    evidence = f"职位变动: {old.current_title} → {new.current_title}"
                
                signals.append(JobSeekingSignal(
                    candidate_id=new.candidate_id,
                    signal_type=signal_type,
                    confidence=0.85,
                    evidence=evidence,
                    detected_at=datetime.now().isoformat()
                ))
        
        return signals
    
    def _sanitize_id(self, candidate_id: str) -> str:
        """清理ID用于文件名"""
        return candidate_id.replace('https://', '').replace('/', '_').replace('.', '_')[:50]


async def main():
    """测试 Profile Tracker"""
    
    print("="*80)
    print("🚀 TalentIntel Phase 2A - Profile Tracker")
    print("="*80)
    
    # 加载候选人
    db_path = '/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/clean_candidates_db.json'
    with open(db_path, 'r') as f:
        db = json.load(f)
    
    candidates = db.get('candidates', [])
    
    # 选择高分候选人进行测试
    test_candidates = sorted(
        [c for c in candidates if c.get('verified') == True],
        key=lambda x: -x.get('match_score', 0)
    )[:3]
    
    print(f"\n测试候选人: {len(test_candidates)}位")
    
    # 启动浏览器
    tracker = ProfileTracker()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=LINKEDIN_PROFILE,
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        results = []
        
        for candidate in test_candidates:
            snapshot, delta, signals = await tracker.track_candidate(browser, candidate)
            results.append({
                'candidate': candidate['name'],
                'snapshot': snapshot.to_dict() if snapshot else None,
                'delta': delta.to_dict() if delta else None,
                'signals': [s.to_dict() for s in signals]
            })
        
        await browser.close()
    
    # 保存结果
    result_file = '/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/profile_tracking_result.json'
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print("✅ 追踪完成")
    print(f"结果保存: {result_file}")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())
