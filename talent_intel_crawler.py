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
    source: str  # google_scholar / github / linkedin / arxiv_author / semanticscholar_author
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
        
        cached_data = self.cache.get(cache_key)
        if cached_data:
            print(f"[Cache Hit] Scholar profile: {scholar_url}")
            return TalentProfile(**cached_data)
        
        print(f"[Crawling] Scholar profile: {scholar_url}")
        
        async with SmartCrawler(profile_name=self.profile_name) as crawler:
            result = await crawler.crawl(
                url=scholar_url,
                wait_for="#gsc_prf_w",
                query="scholar citations research"
            )
            
            if not result["success"]:
                print(f"[Failed] {result.get('error', 'Unknown error')}")
                return None
            
            schema = TALENT_SCHEMAS["google_scholar"]
            extracted = await self.extractor.extract_with_schema(crawler.page, schema)
            
            profile = TalentProfile(
                source="google_scholar",
                name=extracted.get("name", "Unknown"),
                url=scholar_url,
                raw_data=extracted,
                extracted_at=datetime.now(),
                confidence=0.85 if extracted.get("name") else 0.5
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
    
    async def crawl_github_profile(self, github_url: str) -> Optional[TalentProfile]:
        """抓取 GitHub 个人主页"""
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
    
    async def crawl_arxiv_author(self, arxiv_url: str) -> Optional[TalentProfile]:
        """
        抓取 arXiv 作者主页
        
        Args:
            arxiv_url: 如 https://arxiv.org/a/author_id
        """
        cache_key = f"arxiv_author:{hash(arxiv_url)}"
        
        cached_data = self.cache.get(cache_key)
        if cached_data:
            print(f"[Cache Hit] arXiv author: {arxiv_url}")
            return TalentProfile(**cached_data)
        
        print(f"[Crawling] arXiv author: {arxiv_url}")
        
        async with SmartCrawler(profile_name=self.profile_name) as crawler:
            result = await crawler.crawl(
                url=arxiv_url,
                wait_for=".author-profile",
                query="arxiv author papers"
            )
            
            if not result["success"]:
                print(f"[Failed] {result.get('error', 'Unknown error')}")
                return None
            
            schema = TALENT_SCHEMAS["arxiv_author"]
            extracted = await self.extractor.extract_with_schema(crawler.page, schema)
            
            profile = TalentProfile(
                source="arxiv_author",
                name=extracted.get("name", "Unknown"),
                url=arxiv_url,
                raw_data=extracted,
                extracted_at=datetime.now(),
                confidence=0.85 if extracted.get("name") else 0.5
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
    
    async def crawl_arxiv_paper(self, arxiv_url: str) -> Optional[Dict[str, Any]]:
        """
        抓取 arXiv 论文详情
        
        Args:
            arxiv_url: 如 https://arxiv.org/abs/2301.xxxxx
        """
        cache_key = f"arxiv_paper:{hash(arxiv_url)}"
        
        cached_data = self.cache.get(cache_key)
        if cached_data:
            print(f"[Cache Hit] arXiv paper: {arxiv_url}")
            return cached_data
        
        print(f"[Crawling] arXiv paper: {arxiv_url}")
        
        async with SmartCrawler(profile_name=self.profile_name) as crawler:
            result = await crawler.crawl(
                url=arxiv_url,
                wait_for="#content-inner",
                query="arxiv paper abstract"
            )
            
            if not result["success"]:
                print(f"[Failed] {result.get('error', 'Unknown error')}")
                return None
            
            schema = TALENT_SCHEMAS["arxiv_paper"]
            extracted = await self.extractor.extract_with_schema(crawler.page, schema)
            
            if extracted.get("_success"):
                self.cache.set(cache_key, extracted, ttl=604800)
                return extracted
            
            return None
    
    async def crawl_semanticscholar_author(self, ss_url: str) -> Optional[TalentProfile]:
        """
        抓取 Semantic Scholar 作者主页
        
        Args:
            ss_url: 如 https://www.semanticscholar.org/author/xxx/xxxx
        """
        cache_key = f"semanticscholar_author:{hash(ss_url)}"
        
        cached_data = self.cache.get(cache_key)
        if cached_data:
            print(f"[Cache Hit] Semantic Scholar author: {ss_url}")
            return TalentProfile(**cached_data)
        
        print(f"[Crawling] Semantic Scholar author: {ss_url}")
        
        async with SmartCrawler(profile_name=self.profile_name) as crawler:
            result = await crawler.crawl(
                url=ss_url,
                wait_for="[data-test-id='author-page']",
                query="semantic scholar author citations"
            )
            
            if not result["success"]:
                print(f"[Failed] {result.get('error', 'Unknown error')}")
                return None
            
            schema = TALENT_SCHEMAS["semanticscholar_author"]
            extracted = await self.extractor.extract_with_schema(crawler.page, schema)
            
            profile = TalentProfile(
                source="semanticscholar_author",
                name=extracted.get("name", "Unknown"),
                url=ss_url,
                raw_data=extracted,
                extracted_at=datetime.now(),
                confidence=0.85 if extracted.get("name") else 0.5
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
    
    async def crawl_semanticscholar_paper(self, ss_url: str) -> Optional[Dict[str, Any]]:
        """
        抓取 Semantic Scholar 论文详情
        
        Args:
            ss_url: 如 https://www.semanticscholar.org/paper/xxx/xxxx
        """
        cache_key = f"semanticscholar_paper:{hash(ss_url)}"
        
        cached_data = self.cache.get(cache_key)
        if cached_data:
            print(f"[Cache Hit] Semantic Scholar paper: {ss_url}")
            return cached_data
        
        print(f"[Crawling] Semantic Scholar paper: {ss_url}")
        
        async with SmartCrawler(profile_name=self.profile_name) as crawler:
            result = await crawler.crawl(
                url=ss_url,
                wait_for="[data-test-id='paper-details']",
                query="semantic scholar paper"
            )
            
            if not result["success"]:
                print(f"[Failed] {result.get('error', 'Unknown error')}")
                return None
            
            schema = TALENT_SCHEMAS["semanticscholar_paper"]
            extracted = await self.extractor.extract_with_schema(crawler.page, schema)
            
            if extracted.get("_success"):
                self.cache.set(cache_key, extracted, ttl=604800)
                return extracted
            
            return None
    
    async def crawl_batch(self, urls: List[str], source_type: str) -> List[TalentProfile]:
        """
        批量抓取
        
        Args:
            urls: URL列表
            source_type: scholar / github / arxiv_author / semanticscholar_author
            
        Returns:
            TalentProfile 列表
        """
        results = []
        
        # 根据类型选择抓取函数
        crawl_func_map = {
            "scholar": self.crawl_scholar_profile,
            "github": self.crawl_github_profile,
            "arxiv_author": self.crawl_arxiv_author,
            "semanticscholar_author": self.crawl_semanticscholar_author
        }
        
        crawl_func = crawl_func_map.get(source_type)
        if not crawl_func:
            raise ValueError(f"Unknown source type: {source_type}. "
                           f"Supported: {list(crawl_func_map.keys())}")
        
        # 并发抓取（限制并发数）
        semaphore = asyncio.Semaphore(3)
        
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
    
    def crawl_arxiv_author(self, url: str) -> Optional[TalentProfile]:
        """同步抓取 arXiv 作者"""
        crawler = TalentIntelCrawler(self.profile_name)
        return asyncio.run(crawler.crawl_arxiv_author(url))
    
    def crawl_arxiv_paper(self, url: str) -> Optional[Dict[str, Any]]:
        """同步抓取 arXiv 论文"""
        crawler = TalentIntelCrawler(self.profile_name)
        return asyncio.run(crawler.crawl_arxiv_paper(url))
    
    def crawl_semanticscholar_author(self, url: str) -> Optional[TalentProfile]:
        """同步抓取 Semantic Scholar 作者"""
        crawler = TalentIntelCrawler(self.profile_name)
        return asyncio.run(crawler.crawl_semanticscholar_author(url))
    
    def crawl_semanticscholar_paper(self, url: str) -> Optional[Dict[str, Any]]:
        """同步抓取 Semantic Scholar 论文"""
        crawler = TalentIntelCrawler(self.profile_name)
        return asyncio.run(crawler.crawl_semanticscholar_paper(url))
    
    def crawl_batch(self, urls: List[str], source_type: str) -> List[TalentProfile]:
        """同步批量抓取"""
        crawler = TalentIntelCrawler(self.profile_name)
        return asyncio.run(crawler.crawl_batch(urls, source_type))


async def demo():
    """演示"""
    print("=" * 70)
    print(" TalentIntel Smart Crawler Demo")
    print("=" * 70)
    
    crawler = TalentIntelCrawler()
    
    print("\n支持的 Schema:")
    for name, schema in TALENT_SCHEMAS.items():
        print(f"  • {name}: {schema.name}")
    
    print("\n示例用法:")
    print("  from talent_intel_crawler import TalentIntelSync")
    print("  crawler = TalentIntelSync()")
    print("  profile = crawler.crawl_arxiv_author('https://arxiv.org/a/0000-0002-0000-0000')")
    print("  paper = crawler.crawl_semanticscholar_paper('https://www.semanticscholar.org/paper/xxx')")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo())
