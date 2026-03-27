#!/usr/bin/env python3
"""
TalentIntel Phase 2 PoC - 使用Kimi Web Search的真实数据验证
只使用Kimi $web_search获取真实数据，禁止模拟
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# 导入Kimi Web Search
from kimi_web_search import KimiWebSearcher, KimiSearchResult


@dataclass
class SocialActivity:
    """社交活动 - 仅真实数据"""
    id: str
    platform: str
    activity_type: str
    content: str
    timestamp: datetime
    url: str
    verified: bool = False
    source: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "platform": self.platform,
            "activity_type": self.activity_type,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "url": self.url,
            "verified": self.verified,
            "source": self.source,
        }


@dataclass
class CandidateProfile:
    """候选人档案 - 仅已验证信息"""
    id: str
    name: str
    company: str
    title: str
    location: str
    linkedin_url: str
    linkedin_verified: bool = False
    x_url: Optional[str] = None
    x_verified: bool = False
    github_url: Optional[str] = None
    github_verified: bool = False
    activities: List[SocialActivity] = field(default_factory=list)
    search_results: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "company": self.company,
            "title": self.title,
            "location": self.location,
            "linkedin_url": self.linkedin_url,
            "linkedin_verified": self.linkedin_verified,
            "x_url": self.x_url,
            "x_verified": self.x_verified,
            "github_url": self.github_url,
            "github_verified": self.github_verified,
            "activities_count": len(self.activities),
            "activities": [a.to_dict() for a in self.activities],
            "search_results": self.search_results,
        }


class RealDataCollector:
    """真实数据收集器 - 使用Kimi Web Search"""
    
    def __init__(self):
        self.searcher = KimiWebSearcher()
        self.collected_data = {}
    
    def search_social_accounts(self, candidate: CandidateProfile) -> Dict:
        """搜索候选人的社交媒体账号"""
        results = {
            "linkedin": [],
            "x": [],
            "github": [],
            "others": []
        }
        
        name = candidate.name
        company = candidate.company
        
        print(f"\n🔍 搜索 {name} 的社交媒体账号...")
        print(f"   公司: {company}")
        
        # 1. 搜索 X/Twitter
        print("\n   [1/3] 搜索 X/Twitter...")
        x_query = f'"{name}" {company} (x.com OR twitter.com) profile'
        x_results = self.searcher.search(x_query, count=5)
        
        if x_results:
            # 过滤个人主页
            x_profiles = [
                r for r in x_results 
                if '/status/' not in r.url and '/tweet/' not in r.url
            ]
            results["x"] = [r.to_dict() for r in x_profiles]
            
            if x_profiles:
                candidate.x_url = x_profiles[0].url
                candidate.x_verified = True
                print(f"   ✅ 找到 X: {candidate.x_url}")
            else:
                print(f"   ⚠️  找到X相关内容但无法确认个人主页")
        else:
            print(f"   ❌ 未找到 X 账号")
        
        # 2. 搜索 GitHub
        print("\n   [2/3] 搜索 GitHub...")
        gh_query = f'"{name}" {company} github.com'
        gh_results = self.searcher.search(gh_query, count=5)
        
        if gh_results:
            # 过滤个人主页
            gh_profiles = [
                r for r in gh_results 
                if 'github.com' in r.url 
                and '/blob/' not in r.url 
                and '/issues/' not in r.url
                and '/pull/' not in r.url
            ]
            results["github"] = [r.to_dict() for r in gh_profiles]
            
            if gh_profiles:
                candidate.github_url = gh_profiles[0].url
                candidate.github_verified = True
                print(f"   ✅ 找到 GitHub: {candidate.github_url}")
            else:
                print(f"   ⚠️  找到GitHub相关内容但无法确认个人主页")
        else:
            print(f"   ❌ 未找到 GitHub 账号")
        
        # 3. 搜索 LinkedIn（验证档案）
        print("\n   [3/3] 验证 LinkedIn...")
        if candidate.linkedin_url:
            li_query = f'{name} {company} linkedin.com/in/'
            li_results = self.searcher.search(li_query, count=3)
            
            if li_results:
                results["linkedin"] = [r.to_dict() for r in li_results]
                # 检查是否包含提供的URL
                found = any(candidate.linkedin_url in r.url for r in li_results)
                candidate.linkedin_verified = found
                print(f"   {'✅' if found else '⚠️'} LinkedIn 验证{'成功' if found else '需要人工确认'}")
            else:
                print(f"   ⚠️  LinkedIn 验证无结果")
        
        candidate.search_results = results
        return results
    
    def search_professional_info(self, candidate: CandidateProfile) -> Dict:
        """搜索职业相关信息"""
        print(f"\n📚 搜索 {candidate.name} 的职业信息...")
        
        results = {}
        
        # 搜索论文/学术
        print("\n   搜索学术论文...")
        paper_query = f'"{candidate.name}" "{candidate.company}" paper research'
        paper_results = self.searcher.search(paper_query, count=5)
        results["papers"] = [r.to_dict() for r in paper_results] if paper_results else []
        print(f"   找到 {len(results['papers'])} 条相关结果")
        
        # 搜索专利
        print("\n   搜索专利...")
        patent_query = f'"{candidate.name}" "{candidate.company}" patent'
        patent_results = self.searcher.search(patent_query, count=3)
        results["patents"] = [r.to_dict() for r in patent_results] if patent_results else []
        print(f"   找到 {len(results['patents'])} 条相关结果")
        
        return results
    
    def get_search_stats(self) -> Dict:
        """获取搜索统计"""
        return self.searcher.get_stats()


async def run_kimi_poc():
    """运行使用Kimi Web Search的PoC"""
    
    print("=" * 70)
    print("🚀 TalentIntel Phase 2 PoC - Kimi Web Search版")
    print("⚠️  只使用真实搜索数据，禁止模拟")
    print("=" * 70)
    
    # 检查API Key
    if not os.getenv("MOONSHOT_API_KEY"):
        print("\n❌ 错误: MOONSHOT_API_KEY 环境变量未设置")
        print("\n请设置环境变量:")
        print("   export MOONSHOT_API_KEY='your-api-key'")
        print("\n获取API Key: https://platform.moonshot.cn/")
        return None
    
    # 创建候选人
    candidate = CandidateProfile(
        id="zhican_chen_001",
        name="Zhican(West) Chen",
        company="NVIDIA",
        title="Senior Software Engineer",
        location="Santa Clara, California",
        linkedin_url="https://linkedin.com/in/zhican-west-chen-7213b4b4",
    )
    
    print(f"\n👤 候选人: {candidate.name}")
    print(f"   公司: {candidate.company}")
    print(f"   职位: {candidate.title}")
    
    # 创建数据收集器
    collector = RealDataCollector()
    
    # 执行搜索
    print("\n" + "-" * 70)
    print("🔍 开始社交账号搜索")
    print("-" * 70)
    
    social_results = collector.search_social_accounts(candidate)
    
    # 搜索职业信息
    print("\n" + "-" * 70)
    print("📚 开始职业信息搜索")
    print("-" * 70)
    
    professional_results = collector.search_professional_info(candidate)
    
    # 显示结果
    print("\n" + "=" * 70)
    print("📊 搜索结果总结")
    print("=" * 70)
    
    verified_count = sum([
        candidate.linkedin_verified,
        candidate.x_verified,
        candidate.github_verified
    ])
    
    print(f"\n✅ 已验证平台: {verified_count}/3")
    print(f"   • LinkedIn: {'✅' if candidate.linkedin_verified else '❌'} {candidate.linkedin_url}")
    print(f"   • X/Twitter: {'✅' if candidate.x_verified else '❌'} {candidate.x_url or '未找到'}")
    print(f"   • GitHub: {'✅' if candidate.github_verified else '❌'} {candidate.github_url or '未找到'}")
    
    # 显示找到的账号详情
    if candidate.x_verified and candidate.x_url:
        print(f"\n🐦 X/Twitter 详情:")
        for result in social_results.get("x", [])[:2]:
            print(f"   • {result.get('title', 'N/A')}")
            print(f"     {result.get('url', 'N/A')}")
    
    if candidate.github_verified and candidate.github_url:
        print(f"\n🐙 GitHub 详情:")
        for result in social_results.get("github", [])[:2]:
            print(f"   • {result.get('title', 'N/A')}")
            print(f"     {result.get('url', 'N/A')}")
    
    # 显示搜索统计
    stats = collector.get_search_stats()
    print("\n" + "-" * 70)
    print("💰 搜索费用统计")
    print("-" * 70)
    print(f"   搜索次数: {stats['search_count']}")
    print(f"   Tokens消耗: {stats['total_tokens']}")
    print(f"   总费用: ￥{stats['estimated_cost']:.2f}")
    print(f"   单价: ￥0.03/次")
    
    # 生成报告
    report = {
        "poc_name": "TalentIntel Phase 2 PoC - Kimi Web Search",
        "timestamp": datetime.now().isoformat(),
        "candidate": candidate.to_dict(),
        "professional_info": professional_results,
        "verification_status": {
            "linkedin": candidate.linkedin_verified,
            "x": candidate.x_verified,
            "github": candidate.github_verified,
            "total_verified": verified_count,
            "total_attempted": 3
        },
        "search_stats": stats,
        "data_source": "Kimi Web Search (builtin_function.$web_search)",
        "note": "本报告所有数据来自Kimi实时搜索，不包含任何模拟数据"
    }
    
    # 保存报告
    report_path = "/Users/cooga/.openclaw/workspace/Project/TalentIntel/poc/kimi_verification_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 完整报告已保存: {report_path}")
    
    print("\n" + "=" * 70)
    print("✅ Kimi Web Search PoC 完成!")
    print("=" * 70)
    
    return candidate


if __name__ == "__main__":
    try:
        candidate = asyncio.run(run_kimi_poc())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
