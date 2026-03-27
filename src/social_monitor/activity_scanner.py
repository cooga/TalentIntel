#!/usr/bin/env python3
"""
TalentIntel Phase 2A - Activity Scanner
LinkedIn 动态扫描器

检测:
1. 最近动态 (posts, articles)
2. 职业成就信号 (论文、项目、获奖)
3. 情感倾向信号 (积极/消极情绪)
4. 互动模式分析
"""

import json
import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from playwright.async_api import async_playwright

LINKEDIN_PROFILE = "/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/profiles/linkedin_01"


@dataclass
class SocialActivity:
    """社交动态"""
    candidate_id: str
    activity_type: str  # post, article, like, comment, share
    content: str
    activity_date: str
    engagement: Dict  # likes, comments, shares 数量
    extracted_links: List[str]
    sentiment_score: float  # -1 to 1
    detected_signals: List[str]
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AchievementSignal:
    """成就信号"""
    candidate_id: str
    signal_type: str  # paper_published, patent_filed, project_launched, award_received
    description: str
    confidence: float
    evidence: str
    detected_at: str
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SentimentSignal:
    """情感信号"""
    candidate_id: str
    sentiment_type: str  # positive, negative, neutral
    intensity: float  # 0-1
    trigger_keywords: List[str]
    context: str
    detected_at: str
    
    def to_dict(self) -> dict:
        return asdict(self)


class ActivityScanner:
    """LinkedIn 动态扫描器"""
    
    def __init__(self, profile_path: str = LINKEDIN_PROFILE):
        self.profile_path = profile_path
        self.activities_dir = Path("/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/social_activities")
        self.activities_dir.mkdir(exist_ok=True)
    
    async def scan_candidate(self, browser, candidate: dict, days: int = 30) -> Dict:
        """
        扫描候选人动态
        
        Returns:
            {
                'activities': List[SocialActivity],
                'achievements': List[AchievementSignal],
                'sentiments': List[SentimentSignal],
                'summary': Dict
            }
        """
        candidate_id = candidate.get('linkedin_url', '')
        name = candidate.get('name', '')
        
        print(f"\n📱 扫描动态: {name}")
        
        # 1. 获取动态列表
        activities = await self._fetch_activities(browser, candidate_id, days)
        print(f"   获取到 {len(activities)} 条动态")
        
        # 2. 分析每条动态
        analyzed_activities = []
        for activity in activities:
            analyzed = self._analyze_activity(activity)
            analyzed_activities.append(analyzed)
        
        # 3. 检测成就信号
        achievements = self._detect_achievements(analyzed_activities, candidate_id)
        if achievements:
            print(f"   🏆 发现 {len(achievements)} 个成就信号")
        
        # 4. 检测情感信号
        sentiments = self._detect_sentiments(analyzed_activities, candidate_id)
        if sentiments:
            print(f"   💭 发现 {len(sentiments)} 个情感信号")
        
        # 5. 保存结果
        self._save_activities(candidate_id, analyzed_activities)
        
        # 6. 生成摘要
        summary = self._generate_summary(analyzed_activities, achievements, sentiments)
        
        return {
            'activities': [a.to_dict() for a in analyzed_activities],
            'achievements': [a.to_dict() for a in achievements],
            'sentiments': [s.to_dict() for s in sentiments],
            'summary': summary
        }
    
    async def _fetch_activities(self, browser, candidate_id: str, days: int) -> List[Dict]:
        """抓取候选人动态"""
        activities = []
        
        try:
            # 访问候选人主页的动态部分
            page = await browser.new_page()
            
            # LinkedIn 动态页面 URL 格式
            activity_url = f"{candidate_id}/recent-activity/all/"
            await page.goto(activity_url, timeout=30000)
            await asyncio.sleep(3)
            
            # 提取动态内容（简化版）
            # 注意：LinkedIn 动态页面需要滚动加载，这里简化处理
            content = await page.content()
            
            # 检测动态元素
            # LinkedIn 的动态通常在特定 class 的 div 中
            activity_selectors = [
                '[data-urn]',
                '[class*="feed-shared-update-v2"]',
                '[class*="social-details_social-activity"]'
            ]
            
            for selector in activity_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for elem in elements[:10]:  # 限制数量
                        text = await elem.inner_text()
                        if text and len(text) > 20:  # 过滤空内容
                            activities.append({
                                'content': text[:500],  # 限制长度
                                'type': 'post',
                                'date': datetime.now().isoformat()  # 简化处理
                            })
                except:
                    continue
            
            await page.close()
            
        except Exception as e:
            print(f"   ⚠️ 抓取动态失败: {e}")
        
        return activities
    
    def _analyze_activity(self, activity: Dict) -> SocialActivity:
        """分析单条动态"""
        content = activity.get('content', '')
        
        # 简单情感分析（基于关键词）
        sentiment_score = self._calculate_sentiment(content)
        
        # 提取链接
        links = self._extract_links(content)
        
        # 检测信号关键词
        detected_signals = self._detect_signals(content)
        
        return SocialActivity(
            candidate_id=activity.get('candidate_id', ''),
            activity_type=activity.get('type', 'post'),
            content=content,
            activity_date=activity.get('date', datetime.now().isoformat()),
            engagement={'likes': 0, 'comments': 0, 'shares': 0},  # 简化
            extracted_links=links,
            sentiment_score=sentiment_score,
            detected_signals=detected_signals
        )
    
    def _calculate_sentiment(self, text: str) -> float:
        """计算情感分数 -1 to 1"""
        text_lower = text.lower()
        
        # 积极关键词
        positive_words = [
            'excited', 'thrilled', 'honored', 'proud', 'delighted',
            '恭喜', '感谢', '开心', '优秀', '成功', 'launch', 'achievement',
            'milestone', 'breakthrough', 'innovation', 'proud to announce'
        ]
        
        # 消极关键词
        negative_words = [
            'frustrated', 'disappointed', 'tired', 'burnout', 'struggle',
            '困难', '累', '失望', '压力', '加班', 'unfortunately', 'regret',
            'layoff', 'fired', 'quit', 'leaving', 'goodbye'
        ]
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        # 计算分数
        total = pos_count + neg_count
        if total == 0:
            return 0.0
        
        return (pos_count - neg_count) / max(total, 1)
    
    def _extract_links(self, text: str) -> List[str]:
        """提取文本中的链接"""
        url_pattern = r'https?://[^\s<>"{}|\\^`[\]]+'
        return re.findall(url_pattern, text)
    
    def _detect_signals(self, text: str) -> List[str]:
        """检测信号关键词"""
        text_lower = text.lower()
        signals = []
        
        # 成就信号
        achievement_keywords = {
            'paper': ['paper', 'publication', 'arxiv', 'published', 'journal', 'conference'],
            'patent': ['patent', 'invention', 'intellectual property', 'filed'],
            'project': ['launched', 'released', 'shipped', 'deployed', 'product'],
            'award': ['award', 'recognition', 'honored', 'selected', 'winner'],
            'promotion': ['promoted', 'new role', 'new position', 'excited to share']
        }
        
        for signal_type, keywords in achievement_keywords.items():
            if any(kw in text_lower for kw in keywords):
                signals.append(f"potential_{signal_type}")
        
        return signals
    
    def _detect_achievements(self, activities: List[SocialActivity], candidate_id: str) -> List[AchievementSignal]:
        """检测成就信号"""
        achievements = []
        
        achievement_patterns = {
            'paper_published': [
                r'(new paper|our paper|published).{0,100}(arxiv|conference|journal)',
                r'(accepted|published).{0,50}(neurips|icml|iclr|cvpr|icc|globecom)'
            ],
            'patent_filed': [
                r'(patent|invention).{0,100}(filed|granted|approved)',
                r'(intellectual property|ip).{0,50}(submitted)'
            ],
            'project_launched': [
                r'(excited|thrilled).{0,50}(launch|announce|release|ship)',
                r'(new product|new feature|new version).{0,50}(available|released)'
            ],
            'award_received': [
                r'(honored|delighted|proud).{0,50}(award|recognition|selected)',
                r'(won|received).{0,30}(award|prize|recognition)'
            ]
        }
        
        for activity in activities:
            content = activity.content.lower()
            
            for signal_type, patterns in achievement_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        # 计算置信度
                        confidence = 0.7 + (0.1 * len(activity.detected_signals))
                        
                        achievements.append(AchievementSignal(
                            candidate_id=candidate_id,
                            signal_type=signal_type,
                            description=f"检测到{signal_type}相关动态",
                            confidence=min(confidence, 0.95),
                            evidence=content[:200],
                            detected_at=datetime.now().isoformat()
                        ))
                        break  # 避免重复
        
        return achievements
    
    def _detect_sentiments(self, activities: List[SocialActivity], candidate_id: str) -> List[SentimentSignal]:
        """检测情感信号"""
        sentiments = []
        
        # 消极信号关键词
        frustration_keywords = [
            'tired', 'burnout', 'exhausted', 'frustrated', 'disappointed',
            'struggling', 'difficult', 'challenging', 'regret', 'unfortunately',
            '加班', '累', '压力', '困难', '失望'
        ]
        
        # 离职相关
        departure_keywords = [
            'last day', 'goodbye', 'farewell', 'moving on', 'new chapter',
            '离职', '告别', '离开', '新起点'
        ]
        
        for activity in activities:
            content_lower = activity.content.lower()
            
            # 检测消极情感
            neg_keywords_found = [kw for kw in frustration_keywords if kw in content_lower]
            if neg_keywords_found and activity.sentiment_score < -0.3:
                sentiments.append(SentimentSignal(
                    candidate_id=candidate_id,
                    sentiment_type="negative_frustration",
                    intensity=abs(activity.sentiment_score),
                    trigger_keywords=neg_keywords_found,
                    context=activity.content[:150],
                    detected_at=datetime.now().isoformat()
                ))
            
            # 检测离职信号
            dep_keywords_found = [kw for kw in departure_keywords if kw in content_lower]
            if dep_keywords_found:
                sentiments.append(SentimentSignal(
                    candidate_id=candidate_id,
                    sentiment_type="potential_departure",
                    intensity=0.8,
                    trigger_keywords=dep_keywords_found,
                    context=activity.content[:150],
                    detected_at=datetime.now().isoformat()
                ))
        
        return sentiments
    
    def _generate_summary(self, activities: List[SocialActivity], 
                         achievements: List[AchievementSignal],
                         sentiments: List[SentimentSignal]) -> Dict:
        """生成摘要"""
        return {
            'total_activities': len(activities),
            'avg_sentiment': sum(a.sentiment_score for a in activities) / max(len(activities), 1),
            'achievement_signals': len(achievements),
            'sentiment_signals': len(sentiments),
            'negative_signals': sum(1 for s in sentiments if s.sentiment_type == "negative_frustration"),
            'departure_signals': sum(1 for s in sentiments if s.sentiment_type == "potential_departure"),
            'generated_at': datetime.now().isoformat()
        }
    
    def _save_activities(self, candidate_id: str, activities: List[SocialActivity]):
        """保存动态记录"""
        safe_id = candidate_id.replace('https://', '').replace('/', '_').replace('.', '_')[:50]
        activity_file = self.activities_dir / f"{safe_id}_activities.json"
        
        with open(activity_file, 'w', encoding='utf-8') as f:
            json.dump([a.to_dict() for a in activities], f, indent=2, ensure_ascii=False)


async def main():
    """测试 Activity Scanner"""
    
    print("="*80)
    print("🚀 TalentIntel Phase 2A - Activity Scanner")
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
    )[:2]
    
    print(f"\n测试候选人: {len(test_candidates)}位")
    
    # 启动浏览器
    scanner = ActivityScanner()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=LINKEDIN_PROFILE,
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        results = []
        
        for candidate in test_candidates:
            result = await scanner.scan_candidate(browser, candidate, days=30)
            results.append({
                'candidate': candidate['name'],
                **result
            })
        
        await browser.close()
    
    # 保存结果
    result_file = '/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/activity_scan_result.json'
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print("✅ 扫描完成")
    print(f"结果保存: {result_file}")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())
