"""
TalentIntel Crawler - 基于 Crawl4AI 改进的智能人才抓取系统

核心改进:
1. Playwright 浏览器抓取（替代纯 HTTP）
2. BM25 智能内容清洗
3. 三层缓存架构
4. Profile 持久化管理
5. 智能 Schema 提取
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from smart_crawler import SmartCrawler, ProfileManager
from intelligent_extractor import IntelligentExtractor, TALENT_SCHEMAS
from smart_cache import SmartCacheManager, cached


@dataclass
class TalentProfile:
    """人才档案数据结构"""
    source: str  # google_scholar / github / linkedin
    name: str
    url: str
    raw_data: Dict[str, Any]
    extracted_at: datetime
    confidence: float = 0.0  # 提取置信度


class TalentIntelCrawler:
    """
    TalentIntel 智能抓取器
    
    统一接口，封装所有改进功能
    """
    
    def __init__(self, profile_name: str = "default"):
        self.profile_name = profile_name
        self.cache = SmartCacheManager()
        self.extractor = IntelligentExtractor()
        self.profile_manager = ProfileManager()
    
    async def crawl_scholar_profile(self, scholar_url: str) -> Optional[TalentProfile]:
        """
        抓取 Google Scholar 个人主页
        
        Args:
            scholar_url: 如 https://scholar.google.com/citations?user=xxx
            
        Returns:
            TalentProfile 或 None
        """
        cache_key = f"scholar:{hash(scholar_url)}"
        
        # 检查缓存
        cached_data = self.cache.get(cache_key)
        if cached_data:
            print(f"[Cache Hit] Scholar profile: {scholar_url}")
            return TalentProfile(**cached_data)
        
        print(f"[Crawling] Scholar profile: {scholar_url}")
        
        async with SmartCrawler(profile_name=self.profile_name) as crawler:
            # 访问页面
            result = await crawler.crawl(
                url=scholar_url,
                wait_for="#gsc_prf_w",
                query="scholar citations research"
            )
            
            if not result["success"]:
                print(f"[Failed] {result.get('error', 'Unknown error')}")
                return None
            
            # 使用 Schema 提取结构化数据
            schema = TALENT_SCHEMAS["google_scholar"]
            extracted = await self.extractor.extract_with_schema(crawler.page, schema)
            
            # 构建人才档案
            profile = TalentProfile(
                source="google_scholar",
                name=extracted.get("name", "Unknown"),
                url=scholar_url,
                raw_data=extracted,
                extracted_at=datetime.now(),
                confidence=0.85 if extracted.get("name") else 0.5
            )
            
            # 缓存结果（7天）
            self.cache.set(cache_key, {
                "source": profile.source,
                "name": profile.name,
                "url": profile.url,
                "raw_data": profile.raw_data,
                "extracted_at": profile.extracted_at.isoformat(),
                "confidence": profile.confidence
            }, ttl=604800)
            
            return profile
    
    async def crawl_github_profile(self, github_url: str) -> Optional[TalentProfile]:
        """
        抓取 GitHub 个人主页
        
        Args:
            github_url: 如 https://github.com/username
        """
        cache_key = f"github:{hash(github_url)}"
        
        cached_data = self.cache.get(cache_key)
        if cached_data:
            print(f"[Cache Hit] GitHub profile: {github_url}")
            return TalentProfile(**cached_data)
        
        print(f"[Crawling] GitHub profile: {github_url}")
        
        async with SmartCrawler(profile_name=self.profile_name) as crawler:
            result = await crawler.crawl(
                url=github_url,
                wait_for=".js-profile-editable-area",
                query="github developer repositories"
            )
            
            if not result["success"]:
                return None
            
            schema = TALENT_SCHEMAS["github_profile"]
            extracted = await self.extractor.extract_with_schema(crawler.page, schema)
            
            profile = TalentProfile(
                source="github",
                name=extracted.get("fullname") or extracted.get("username", "Unknown"),
                url=github_url,
                raw_data=extracted,
                extracted_at=datetime.now(),
                confidence=0.8 if extracted.get("username") else 0.5
            )
            
            self.cache.set(cache_key, {
                "source": profile.source,
                "name": profile.name,
                "url": profile.url,
                "raw_data": profile.raw_data,
                "extracted_at": profile.extracted_at.isoformat(),
                "confidence": profile.confidence
            }, ttl=604800)
            
            return profile
    
    async def crawl_batch(self, urls: List[str], source_type: str) -> List[TalentProfile]:
        """
        批量抓取
        
        Args:
            urls: URL列表
            source_type: scholar / github / linkedin
            
        Returns:
            TalentProfile 列表
        """
        results = []
        
        # 根据类型选择抓取函数
        if source_type == "scholar":
            crawl_func = self.crawl_scholar_profile
        elif source_type == "github":
            crawl_func = self.crawl_github_profile
        else:
            raise ValueError(f"Unknown source type: {source_type}")
        
        # 并发抓取（限制并发数）
        semaphore = asyncio.Semaphore(3)  # 最多3个并发
        
        async def crawl_with_limit(url):
            async with semaphore:
                return await crawl_func(url)
        
        tasks = [crawl_with_limit(url) for url in urls]
        profiles = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤成功结果
        for profile in profiles:
            if isinstance(profile, TalentProfile):
                results.append(profile)
            elif isinstance(profile, Exception):
                print(f"[Error] {profile}")
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取抓取统计"""
        return {
            "cache": self.cache.stats(),
            "profiles": self.profile_manager.list_profiles()
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear_all()
        print("[Cache Cleared] All cache levels cleared")


# 简化同步接口
class TalentIntelSync:
    """同步包装类"""
    
    def __init__(self, profile_name: str = "default"):
        self.profile_name = profile_name
    
    def crawl_scholar(self, url: str) -> Optional[TalentProfile]:
        """同步抓取 Scholar"""
        crawler = TalentIntelCrawler(self.profile_name)
        return asyncio.run(crawler.crawl_scholar_profile(url))
    
    def crawl_github(self, url: str) -> Optional[TalentProfile]:
        """同步抓取 GitHub"""
        crawler = TalentIntelCrawler(self.profile_name)
        return asyncio.run(crawler.crawl_github_profile(url))
    
    def crawl_batch(self, urls: List[str], source_type: str) -> List[TalentProfile]:
        """同步批量抓取"""
        crawler = TalentIntelCrawler(self.profile_name)
        return asyncio.run(crawler.crawl_batch(urls, source_type))


# 示例脚本
async def demo():
    """演示新系统的改进"""
    print("=" * 70)
    print(" TalentIntel Smart Crawler Demo")
    print("=" * 70)
    
    crawler = TalentIntelCrawler()
    
    # 演示 1: 缓存系统
    print("\n[Demo 1] 三层缓存系统")
    print("-" * 70)
    print("L1 (Memory): 热数据，最快访问")
    print("L2 (Disk): 持久化，进程间共享")
    print("L3 (Browser): 已渲染页面复用")
    print(f"\n当前缓存统计: {crawler.cache.stats()}")
    
    # 演示 2: Profile 管理
    print("\n[Demo 2] Profile 持久化管理")
    print("-" * 70)
    profiles = crawler.profile_manager.list_profiles()
    print(f"已保存的 Profiles: {profiles if profiles else '(无)'}")
    print("功能: 保存登录态、Cookie、浏览器指纹")
    
    # 演示 3: BM25 内容清洗
    print("\n[Demo 3] BM25 智能内容清洗")
    print("-" * 70)
    from smart_crawler import BM25ContentFilter
    
    bm25 = BM25ContentFilter()
    test_blocks = [
        {"text": "导航栏 Home About Contact", "tag": "nav", "class": "navbar"},
        {"text": "李明的研究兴趣包括机器学习、自然语言处理、计算机视觉。他在Google Scholar上有1000+引用。", "tag": "article", "class": "profile-content"},
        {"text": "广告：购买优质服务器", "tag": "div", "class": "ad-banner"},
        {"text": "发表论文：1. Transformer架构研究 2. BERT模型优化 3. GPT系列分析", "tag": "section", "class": "publications"}
    ]
    
    main_content = bm25.extract_main_content(test_blocks, query="machine learning research")
    print(f"输入块数: {len(test_blocks)}")
    print(f"提取内容:\n{main_content[:300]}...")
    
    # 演示 4: Schema 提取
    print("\n[Demo 4] 智能 Schema 提取")
    print("-" * 70)
    print("预定义 Schema:")
    for name, schema in TALENT_SCHEMAS.items():
        print(f"  • {name}: {schema.name}")
        print(f"    字段: {list(schema.fields.keys())}")
    
    # 演示 5: 抓取示例（可选，需要网络）
    print("\n[Demo 5] 实际抓取演示")
    print("-" * 70)
    test_url = "https://scholar.google.com/citations?hl=en&imq=Geoffrey+Hinton"
    print(f"示例 URL: {test_url}")
    print("(实际抓取需要网络连接和 Playwright 浏览器)")
    print("运行: python -c \"from talent_intel_crawler import TalentIntelSync; TalentIntelSync().crawl_scholar('URL')\"")
    
    print("\n" + "=" * 70)
    print(" Demo Completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(demo())
