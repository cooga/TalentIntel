"""
TalentIntel - Smart Talent Intelligence System

基于 Crawl4AI 架构改进的智能人才抓取系统

核心模块:
- smart_crawler: 浏览器爬虫，具备反检测能力
- intelligent_extractor: 智能内容提取
- smart_cache: 三层缓存管理
- talent_intel_crawler: 统一接口封装

使用示例:
    from talent_intel_crawler import TalentIntelSync
    
    crawler = TalentIntelSync()
    profile = crawler.crawl_scholar("https://scholar.google.com/...")
"""

__version__ = "2.0.0"

from .smart_crawler import (
    SmartCrawler,
    BM25ContentFilter,
    ProfileManager,
    CrawlProfile
)

from .intelligent_extractor import (
    IntelligentExtractor,
    ExtractionSchema,
    TALENT_SCHEMAS,
    extract_emails,
    extract_urls,
    extract_phone_numbers
)

from .smart_cache import (
    SmartCacheManager,
    MemoryCache,
    DiskCache,
    cached
)

from .talent_intel_crawler import (
    TalentIntelCrawler,
    TalentIntelSync,
    TalentProfile
)

__all__ = [
    # 核心爬虫
    "SmartCrawler",
    "BM25ContentFilter",
    "ProfileManager",
    "CrawlProfile",
    
    # 内容提取
    "IntelligentExtractor",
    "ExtractionSchema",
    "TALENT_SCHEMAS",
    "extract_emails",
    "extract_urls",
    "extract_phone_numbers",
    
    # 缓存
    "SmartCacheManager",
    "MemoryCache",
    "DiskCache",
    "cached",
    
    # 统一接口
    "TalentIntelCrawler",
    "TalentIntelSync",
    "TalentProfile"
]
