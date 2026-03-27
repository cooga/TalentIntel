"""
TalentIntel Phase 2 PoC - 多平台社交监控核心模块
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import json
import asyncio

class PlatformType(Enum):
    LINKEDIN = "linkedin"
    X = "x"  # Twitter
    GITHUB = "github"
    SCHOLAR = "google_scholar"
    FACEBOOK = "facebook"

class ActivityType(Enum):
    POST = "post"
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    JOB_CHANGE = "job_change"
    CONNECTION = "connection"
    REPO_CREATED = "repo_created"
    REPO_STARRED = "repo_starred"
    PAPER_PUBLISHED = "paper_published"
    PROFILE_UPDATE = "profile_update"

@dataclass
class SocialActivity:
    """社交活动数据模型"""
    id: str
    platform: PlatformType
    activity_type: ActivityType
    content: str
    timestamp: datetime
    url: str
    engagement: Dict[str, int] = field(default_factory=dict)  # likes, comments, shares
    raw_data: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "platform": self.platform.value,
            "activity_type": self.activity_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "url": self.url,
            "engagement": self.engagement,
        }

@dataclass
class CandidateProfile:
    """候选人档案模型"""
    id: str
    name: str
    company: str
    title: str
    location: str
    linkedin_url: str
    x_url: Optional[str] = None
    github_url: Optional[str] = None
    scholar_url: Optional[str] = None
    activities: List[SocialActivity] = field(default_factory=list)
    connections: List[str] = field(default_factory=list)
    
    def add_activity(self, activity: SocialActivity):
        self.activities.append(activity)
        # 按时间排序
        self.activities.sort(key=lambda x: x.timestamp, reverse=True)
    
    def get_recent_activities(self, days: int = 30) -> List[SocialActivity]:
        cutoff = datetime.now() - timedelta(days=days)
        return [a for a in self.activities if a.timestamp > cutoff]

@dataclass
class OpportunitySignal:
    """机会信号模型"""
    signal_type: str  # job_change, sentiment_negative, network_expansion, etc.
    confidence: float  # 0-1
    description: str
    source_activity: SocialActivity
    detected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "signal_type": self.signal_type,
            "confidence": self.confidence,
            "description": self.description,
            "source_activity": self.source_activity.to_dict(),
            "detected_at": self.detected_at.isoformat(),
        }

class PlatformAdapter(ABC):
    """平台适配器基类"""
    
    def __init__(self, platform: PlatformType):
        self.platform = platform
        self.rate_limiter = RateLimiter()
    
    @abstractmethod
    async def fetch_profile(self, identifier: str) -> Dict:
        """获取用户档案"""
        pass
    
    @abstractmethod
    async def fetch_activities(self, identifier: str, limit: int = 50) -> List[SocialActivity]:
        """获取用户活动"""
        pass
    
    @abstractmethod
    async def fetch_connections(self, identifier: str) -> List[str]:
        """获取用户连接（如平台支持）"""
        pass
    
    async def safe_request(self, url: str) -> Optional[str]:
        """带限流的请求"""
        await self.rate_limiter.wait()
        # 实际实现中使用 aiohttp 或 playwright
        return None

class RateLimiter:
    """简单的速率限制器"""
    def __init__(self, min_delay: float = 2.0, max_delay: float = 5.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request = None
    
    async def wait(self):
        import random
        delay = random.uniform(self.min_delay, self.max_delay)
        if self.last_request:
            elapsed = (datetime.now() - self.last_request).total_seconds()
            if elapsed < delay:
                await asyncio.sleep(delay - elapsed)
        self.last_request = datetime.now()

class LinkedInAdapter(PlatformAdapter):
    """LinkedIn 平台适配器"""
    
    def __init__(self):
        super().__init__(PlatformType.LINKEDIN)
    
    async def fetch_profile(self, linkedin_url: str) -> Dict:
        """从LinkedIn获取档案"""
        # PoC阶段使用模拟数据或浏览器自动化
        return {
            "name": "Zhican(West) Chen",
            "title": "Senior Software Engineer",
            "company": "NVIDIA",
            "location": "Santa Clara, California",
            "connections": 1200,
        }
    
    async def fetch_activities(self, linkedin_url: str, limit: int = 50) -> List[SocialActivity]:
        """获取LinkedIn活动"""
        # 模拟活动数据
        activities = [
            SocialActivity(
                id="li_001",
                platform=PlatformType.LINKEDIN,
                activity_type=ActivityType.POST,
                content="Excited to share our latest work on AI-RAN optimization at NVIDIA! \
                        We've achieved 30% latency reduction using neural network-based scheduling.",
                timestamp=datetime(2026, 3, 15, 10, 30),
                url=f"{linkedin_url}/activity/001",
                engagement={"likes": 156, "comments": 23, "shares": 12}
            ),
            SocialActivity(
                id="li_002",
                platform=PlatformType.LINKEDIN,
                activity_type=ActivityType.COMMENT,
                content="Great point about massive MIMO beamforming! We've seen similar results \
                        in our AI-RAN research.",
                timestamp=datetime(2026, 3, 10, 14, 20),
                url=f"{linkedin_url}/activity/002",
                engagement={"likes": 45, "comments": 8}
            ),
        ]
        return activities[:limit]
    
    async def fetch_connections(self, linkedin_url: str) -> List[str]:
        """获取LinkedIn连接"""
        # 模拟共同连接
        return [
            "https://linkedin.com/in/nvidia-engineer-1",
            "https://linkedin.com/in/nvidia-engineer-2",
            "https://linkedin.com/in/rice-alumni-1",
        ]

class XAdapter(PlatformAdapter):
    """X (Twitter) 平台适配器"""
    
    def __init__(self):
        super().__init__(PlatformType.X)
    
    async def fetch_profile(self, x_handle: str) -> Dict:
        """从X获取档案"""
        return {
            "handle": x_handle,
            "name": "Zhican Chen",
            "bio": "AI researcher @NVIDIA | PhD @Rice | Wireless AI, 6G, MIMO",
            "followers": 3500,
            "following": 800,
        }
    
    async def fetch_activities(self, x_handle: str, limit: int = 50) -> List[SocialActivity]:
        """获取X推文"""
        activities = [
            SocialActivity(
                id="x_001",
                platform=PlatformType.X,
                activity_type=ActivityType.POST,
                content="Just published our paper on 'Neural Scheduling for 5G RAN' at IEEE TCOM! \
                        Key insight: learned schedulers can adapt to traffic patterns better than heuristic ones. \
                        #AI #5G #Wireless",
                timestamp=datetime(2026, 3, 20, 9, 15),
                url=f"https://x.com/{x_handle}/status/001",
                engagement={"likes": 89, "comments": 12, "retweets": 34}
            ),
            SocialActivity(
                id="x_002",
                platform=PlatformType.X,
                activity_type=ActivityType.LIKE,
                content="Liked: 'Open RAN is the future of wireless infrastructure' by @wireless_expert",
                timestamp=datetime(2026, 3, 18, 16, 45),
                url=f"https://x.com/wireless_expert/status/002",
            ),
            SocialActivity(
                id="x_003",
                platform=PlatformType.X,
                activity_type=ActivityType.POST,
                content="Frustrated with the current state of wireless research funding. \
                        So much potential but slow to deploy. Time for a change?",
                timestamp=datetime(2026, 3, 12, 11, 30),
                url=f"https://x.com/{x_handle}/status/003",
                engagement={"likes": 234, "comments": 56}
            ),
        ]
        return activities[:limit]
    
    async def fetch_connections(self, x_handle: str) -> List[str]:
        """X平台不直接提供连接，通过互动推断"""
        return []

class GitHubAdapter(PlatformAdapter):
    """GitHub 平台适配器"""
    
    def __init__(self):
        super().__init__(PlatformType.GITHUB)
    
    async def fetch_profile(self, github_username: str) -> Dict:
        """从GitHub获取档案"""
        return {
            "username": github_username,
            "name": "Zhican Chen",
            "bio": "AI researcher focusing on wireless communication optimization",
            "public_repos": 15,
            "followers": 280,
            "following": 45,
        }
    
    async def fetch_activities(self, github_username: str, limit: int = 50) -> List[SocialActivity]:
        """获取GitHub活动"""
        activities = [
            SocialActivity(
                id="gh_001",
                platform=PlatformType.GITHUB,
                activity_type=ActivityType.REPO_CREATED,
                content="Created repository: ai-ran-simulator - AI-powered 5G RAN simulation framework",
                timestamp=datetime(2026, 2, 28, 8, 0),
                url=f"https://github.com/{github_username}/ai-ran-simulator",
                engagement={"stars": 127, "forks": 34}
            ),
            SocialActivity(
                id="gh_002",
                platform=PlatformType.GITHUB,
                activity_type=ActivityType.REPO_STARRED,
                content="Starred: sionna - NVIDIA's GPU-accelerated 5G/6G link-level simulator",
                timestamp=datetime(2026, 3, 5, 14, 20),
                url="https://github.com/NVIDIA/sionna",
            ),
            SocialActivity(
                id="gh_003",
                platform=PlatformType.GITHUB,
                activity_type=ActivityType.POST,  # Commit/push
                content="Pushed 5 commits to ai-ran-simulator: \
                        Implemented neural scheduler with transformer architecture",
                timestamp=datetime(2026, 3, 18, 10, 0),
                url=f"https://github.com/{github_username}/ai-ran-simulator/commits",
            ),
        ]
        return activities[:limit]
    
    async def fetch_connections(self, github_username: str) -> List[str]:
        """通过共同贡献推断连接"""
        return [
            "https://github.com/nvidia-researcher-1",
            "https://github.com/wireless-ai-contributor",
        ]

class OpportunityDetector:
    """机会信号检测器"""
    
    SIGNAL_PATTERNS = {
        "job_change": [
            "excited to announce.*new (role|position|opportunity)",
            "starting.*(new job|new role|new position)",
            "#OpenToWork|open to (new opportunities|work)",
            "last day at|farewell to|saying goodbye to.*team",
        ],
        "sentiment_negative": [
            "frustrated with|tired of|burned out|stuck in",
            "looking for.*change|ready for.*new challenge",
            "time for a change",
        ],
        "network_expansion": [
            "thrilled to connect|great to meet",
        ],
        "achievement": [
            "published.*paper|accepted.*conference",
            "grateful.*award|honored.*recognition",
        ],
    }
    
    def __init__(self):
        import re
        self.patterns = {
            signal: [re.compile(p, re.IGNORECASE) for p in patterns]
            for signal, patterns in self.SIGNAL_PATTERNS.items()
        }
    
    def detect(self, activity: SocialActivity) -> List[OpportunitySignal]:
        """检测活动中的机会信号"""
        signals = []
        content = activity.content.lower()
        
        for signal_type, patterns in self.patterns.items():
            for pattern in patterns:
                if pattern.search(content):
                    confidence = self._calculate_confidence(activity, signal_type)
                    signals.append(OpportunitySignal(
                        signal_type=signal_type,
                        confidence=confidence,
                        description=f"Detected '{signal_type}' signal in {activity.platform.value} activity",
                        source_activity=activity
                    ))
                    break  # 每个类型只报告一次
        
        return signals
    
    def _calculate_confidence(self, activity: SocialActivity, signal_type: str) -> float:
        """计算信号置信度"""
        base_confidence = 0.7
        
        # 根据平台调整
        if activity.platform == PlatformType.LINKEDIN:
            base_confidence += 0.1  # LinkedIn职业信号更可靠
        
        # 根据互动量调整
        engagement = sum(activity.engagement.values())
        if engagement > 100:
            base_confidence += 0.1
        
        # 根据内容长度调整
        if len(activity.content) > 200:
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)

class SocialMonitorService:
    """社交监控服务 - PoC核心"""
    
    def __init__(self):
        self.adapters = {
            PlatformType.LINKEDIN: LinkedInAdapter(),
            PlatformType.X: XAdapter(),
            PlatformType.GITHUB: GitHubAdapter(),
        }
        self.detector = OpportunityDetector()
        self.candidates: Dict[str, CandidateProfile] = {}
    
    async def monitor_candidate(self, candidate: CandidateProfile) -> Dict:
        """监控单个候选人所有平台"""
        results = {
            "candidate": candidate.name,
            "platforms": {},
            "signals": [],
            "activities": [],
        }
        
        # LinkedIn
        if candidate.linkedin_url:
            try:
                li_adapter = self.adapters[PlatformType.LINKEDIN]
                profile = await li_adapter.fetch_profile(candidate.linkedin_url)
                activities = await li_adapter.fetch_activities(candidate.linkedin_url)
                
                results["platforms"]["linkedin"] = {
                    "profile": profile,
                    "activity_count": len(activities)
                }
                
                for activity in activities:
                    candidate.add_activity(activity)
                    signals = self.detector.detect(activity)
                    results["signals"].extend([s.to_dict() for s in signals])
                    results["activities"].append(activity.to_dict())
                    
            except Exception as e:
                results["platforms"]["linkedin"] = {"error": str(e)}
        
        # X (尝试推断用户名)
        x_handle = self._infer_x_handle(candidate)
        if x_handle:
            try:
                x_adapter = self.adapters[PlatformType.X]
                profile = await x_adapter.fetch_profile(x_handle)
                activities = await x_adapter.fetch_activities(x_handle)
                
                results["platforms"]["x"] = {
                    "profile": profile,
                    "activity_count": len(activities)
                }
                
                for activity in activities:
                    candidate.add_activity(activity)
                    signals = self.detector.detect(activity)
                    results["signals"].extend([s.to_dict() for s in signals])
                    results["activities"].append(activity.to_dict())
                    
            except Exception as e:
                results["platforms"]["x"] = {"error": str(e)}
        
        # GitHub (尝试推断用户名)
        github_username = self._infer_github_username(candidate)
        if github_username:
            try:
                gh_adapter = self.adapters[PlatformType.GITHUB]
                profile = await gh_adapter.fetch_profile(github_username)
                activities = await gh_adapter.fetch_activities(github_username)
                
                results["platforms"]["github"] = {
                    "profile": profile,
                    "activity_count": len(activities)
                }
                
                for activity in activities:
                    candidate.add_activity(activity)
                    signals = self.detector.detect(activity)
                    results["signals"].extend([s.to_dict() for s in signals])
                    results["activities"].append(activity.to_dict())
                    
            except Exception as e:
                results["platforms"]["github"] = {"error": str(e)}
        
        return results
    
    def _infer_x_handle(self, candidate: CandidateProfile) -> Optional[str]:
        """从候选人信息推断X账号"""
        # PoC: 使用姓名推断
        if "zhican" in candidate.name.lower():
            return "zhican_chen"
        return None
    
    def _infer_github_username(self, candidate: CandidateProfile) -> Optional[str]:
        """从候选人信息推断GitHub用户名"""
        # PoC: 使用姓名推断
        if "zhican" in candidate.name.lower():
            return "zhichen-nvidia"
        return None
    
    def calculate_opportunity_score(self, candidate: CandidateProfile) -> Dict:
        """计算候选人机会评分"""
        recent_activities = candidate.get_recent_activities(days=30)
        
        # 统计信号
        signals_by_type = {}
        for activity in recent_activities:
            signals = self.detector.detect(activity)
            for signal in signals:
                if signal.signal_type not in signals_by_type:
                    signals_by_type[signal.signal_type] = []
                signals_by_type[signal.signal_type].append(signal)
        
        # 计算评分
        score = 0
        breakdown = {}
        
        if "job_change" in signals_by_type:
            score += 35
            breakdown["job_change"] = 35
        
        if "sentiment_negative" in signals_by_type:
            score += 25
            breakdown["sentiment_negative"] = 25
        
        # 活跃度评分
        activity_score = min(len(recent_activities) * 2, 15)
        score += activity_score
        breakdown["activity"] = activity_score
        
        # 多平台存在
        platforms = set(a.platform for a in recent_activities)
        platform_score = len(platforms) * 5
        score += platform_score
        breakdown["multi_platform"] = platform_score
        
        return {
            "total_score": score,
            "max_score": 100,
            "breakdown": breakdown,
            "signals_detected": list(signals_by_type.keys()),
            "signal_count": sum(len(s) for s in signals_by_type.values()),
            "platforms_active": [p.value for p in platforms],
        }

# 从 datetime import timedelta
from datetime import timedelta

async def run_poc():
    """运行PoC验证"""
    print("=" * 60)
    print("TalentIntel Phase 2 PoC - 多平台社交监控")
    print("=" * 60)
    
    # 创建候选人
    candidate = CandidateProfile(
        id="zhican_chen_001",
        name="Zhican(West) Chen",
        company="NVIDIA",
        title="Senior Software Engineer",
        location="Santa Clara, California",
        linkedin_url="https://linkedin.com/in/zhican-west-chen-7213b4b4",
        x_url="https://x.com/zhican_chen",
        github_url="https://github.com/zhichen-nvidia",
    )
    
    # 初始化服务
    service = SocialMonitorService()
    
    # 执行监控
    print(f"\n🔍 监控候选人: {candidate.name}")
    print(f"   公司: {candidate.company}")
    print(f"   职位: {candidate.title}")
    print()
    
    results = await service.monitor_candidate(candidate)
    
    # 输出结果
    print("📊 平台监控结果:")
    print("-" * 40)
    for platform, data in results["platforms"].items():
        if "error" in data:
            print(f"  ❌ {platform}: {data['error']}")
        else:
            print(f"  ✅ {platform}: {data.get('activity_count', 0)} 条活动")
    
    print("\n🔔 检测到的机会信号:")
    print("-" * 40)
    if results["signals"]:
        for signal in results["signals"]:
            confidence = signal["confidence"]
            signal_type = signal["signal_type"]
            platform = signal["source_activity"]["platform"]
            print(f"  [{platform}] {signal_type}: {confidence:.0%} 置信度")
            print(f"    → {signal['description']}")
    else:
        print("  未检测到明显机会信号")
    
    print("\n📈 机会评分:")
    print("-" * 40)
    score_result = service.calculate_opportunity_score(candidate)
    print(f"  总分: {score_result['total_score']}/{score_result['max_score']}")
    print(f"  活跃平台: {', '.join(score_result['platforms_active'])}")
    print(f"  检测信号: {score_result['signal_count']} 个")
    print("\n  评分详情:")
    for key, value in score_result['breakdown'].items():
        print(f"    • {key}: +{value} 分")
    
    print("\n📝 最新活动:")
    print("-" * 40)
    for activity in sorted(candidate.activities, key=lambda x: x.timestamp, reverse=True)[:3]:
        print(f"  [{activity.platform.value}] {activity.activity_type.value}")
        print(f"    {activity.content[:100]}...")
        print(f"    {activity.timestamp.strftime('%Y-%m-%d %H:%M')}")
        print()
    
    print("=" * 60)
    print("PoC 验证完成")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    asyncio.run(run_poc())
