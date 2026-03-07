"""
X-Ray LinkedIn Search - 整合版

使用 Google X-Ray 搜索技术获取 LinkedIn 人才信息
整合到 Smart Crawler 系统，使用新的缓存和 Profile 管理

X-Ray 搜索原理:
site:linkedin.com/in + 关键词 = Google 索引的公开 LinkedIn 页面
"""

import asyncio
import re
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote
import yaml

from smart_cache import SmartCacheManager
from intelligent_extractor import extract_emails


@dataclass
class LinkedInProfile:
    """LinkedIn 人才档案"""
    url: str
    name: str
    raw_slug: str
    match_score: float
    ai_indicators: int
    wireless_indicators: int
    source_query: str
    discovered_at: datetime
    
    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "name": self.name,
            "raw_slug": self.raw_slug,
            "match_score": self.match_score,
            "ai_indicators": self.ai_indicators,
            "wireless_indicators": self.wireless_indicators,
            "source_query": self.source_query,
            "discovered_at": self.discovered_at.isoformat()
        }


class XRayLinkedInSearcher:
    """
    X-Ray LinkedIn 搜索器
    
    使用 Google X-Ray 技术搜索 LinkedIn 人才
    特点:
    - 不需要 LinkedIn 账号
    - 合规安全 (只抓取 Google 公开索引)
    - 可批量获取人才链接
    """
    
    # 人才画像关键词组合
    DEFAULT_QUERIES = [
        # 华人学者 - AI + 无线通信
        "site:linkedin.com/in chinese professor machine learning wireless communication",
        "site:linkedin.com/in chinese researcher AI 5G 6G deep learning",
        "site:linkedin.com/in chinese scientist neural network signal processing",
        
        # 北美大厂华人工程师
        "site:linkedin.com/in chinese engineer NVIDIA Google Meta Apple wireless",
        "site:linkedin.com/in chinese researcher Qualcomm Broadcom Intel 5G",
        "site:linkedin.com/in chinese engineer Bell Labs Samsung Huawei AI",
        
        # 顶尖学校华人
        "site:linkedin.com/in phd Stanford MIT Berkeley CMU wireless AI",
        "site:linkedin.com/in postdoc UCLA USC Columbia NYU machine learning",
        "site:linkedin.com/in researcher Caltech Princeton Harvard communication",
        
        # 特定领域专家
        "site:linkedin.com/in expert MIMO OFDM channel estimation deep learning",
        "site:linkedin.com/in specialist semantic communication AI native",
        "site:linkedin.com/in researcher RIS IRS smart surface wireless",
        
        # 产业界专家
        "site:linkedin.com/in director AI research wireless communication",
        "site:linkedin.com/in principal scientist 5G 6G machine learning",
        "site:linkedin.com/in chief engineer radio access network AI",
    ]
    
    def __init__(self, proxy_config_path: str = "config/proxies.yaml"):
        self.cache = SmartCacheManager()
        self.proxy_config_path = proxy_config_path
        self.proxies = self._load_proxies()
        
        # 去重集合
        self.discovered_urls: Set[str] = set()
        self.discovered_profiles: List[LinkedInProfile] = []
    
    def _load_proxies(self) -> List[Dict]:
        """加载代理配置"""
        try:
            with open(self.proxy_config_path) as f:
                config = yaml.safe_load(f)
                return config.get('proxies', [])
        except Exception as e:
            print(f"⚠️  代理配置加载失败: {e}")
            return []
    
    def _extract_linkedin_profiles(self, html: str, query: str) -> List[LinkedInProfile]:
        """
        从 Google 搜索结果 HTML 中提取 LinkedIn 档案
        
        Args:
            html: Google 搜索结果页面 HTML
            query: 搜索查询词
            
        Returns:
            LinkedInProfile 列表
        """
        if not html:
            return []
        
        profiles = []
        # 匹配 LinkedIn 个人档案 URL
        pattern = r'https?://(?:www\.)?linkedin\.com/in/[^"\s<>]+'
        matches = re.findall(pattern, html, re.IGNORECASE)
        
        seen = set()
        for url in matches:
            # 清洗 URL
            clean_url = re.sub(r'\?.*$', '', url)  # 移除查询参数
            clean_url = re.sub(r'/$', '', clean_url)  # 移除末尾斜杠
            clean_url = clean_url.replace('http://', 'https://')
            
            if clean_url in seen or '/in/' not in clean_url:
                continue
            
            seen.add(clean_url)
            
            # 提取姓名
            name_match = re.search(r'/in/([^/]+)', clean_url)
            if name_match:
                raw_slug = name_match.group(1)
                name = raw_slug.replace('-', ' ').replace('_', ' ').title()
                
                # 评估匹配度
                evaluation = self._evaluate_profile(name, raw_slug, query)
                
                profile = LinkedInProfile(
                    url=clean_url,
                    name=name,
                    raw_slug=raw_slug,
                    match_score=evaluation["match_score"],
                    ai_indicators=evaluation["ai_indicators"],
                    wireless_indicators=evaluation["wireless_indicators"],
                    source_query=query,
                    discovered_at=datetime.now()
                )
                
                profiles.append(profile)
        
        return profiles
    
    def _evaluate_profile(self, name: str, raw_slug: str, query: str) -> Dict[str, Any]:
        """
        评估候选人与目标画像的匹配度
        
        Args:
            name: 姓名
            raw_slug: URL slug
            query: 搜索查询词
            
        Returns:
            评估结果字典
        """
        combined = f"{name} {raw_slug} {query}".lower()
        
        # AI 相关关键词
        ai_keywords = [
            "ai", "ml", "machine", "learning", "deep", "neural", "research",
            "scientist", "data", "algorithm", "artificial", "intelligence",
            "nlp", "cv", "computer vision", "llm", "transformer"
        ]
        
        # 无线通信关键词
        wireless_keywords = [
            "wireless", "5g", "6g", "communication", "signal", "mimo",
            "ofdm", "radio", "network", "telecom", "channel", "antenna",
            "phy", "physical", "layer", "rf", "mmwave", "spectrum"
        ]
        
        # 计算得分
        ai_score = sum(1 for kw in ai_keywords if kw in combined)
        wireless_score = sum(1 for kw in wireless_keywords if kw in combined)
        
        # 交叉领域奖励
        cross_bonus = 0.25 if (ai_score > 0 and wireless_score > 0) else 0
        base_score = (min(ai_score, 4) * 0.15 + min(wireless_score, 4) * 0.15)
        match_score = min(base_score + cross_bonus, 1.0)
        
        return {
            "match_score": round(match_score, 2),
            "ai_indicators": ai_score,
            "wireless_indicators": wireless_score,
            "priority": "high" if match_score >= 0.7 else "medium" if match_score >= 0.5 else "low"
        }
    
    async def search_with_proxy(self, query: str, proxy: Dict) -> Optional[str]:
        """
        使用代理执行 Google 搜索
        
        Args:
            query: 搜索查询
            proxy: 代理配置
            
        Returns:
            HTML 内容或 None
        """
        import aiohttp
        from aiohttp import ClientTimeout
        
        proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        # 构建 Google 搜索 URL
        encoded_query = quote(query)
        search_url = f"https://www.google.com/search?q={encoded_query}&num=50"
        
        try:
            timeout = ClientTimeout(total=25)
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    search_url, 
                    proxy=proxy_url, 
                    ssl=False, 
                    timeout=timeout,
                    allow_redirects=True
                ) as resp:
                    if resp.status == 200:
                        return await resp.text()
                    elif resp.status == 429:
                        print(f"    ⚠️  429 限制，需要更换代理")
                        return None
                    else:
                        print(f"    ⚠️  HTTP {resp.status}")
                        return None
        except Exception as e:
            print(f"    ⚠️  请求异常: {str(e)[:50]}")
            return None
    
    async def search_single_query(self, query: str, max_results: int = 20) -> List[LinkedInProfile]:
        """
        执行单个查询的 X-Ray 搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            LinkedInProfile 列表
        """
        cache_key = f"xray:{hash(query)}"
        
        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            print(f"  [Cache Hit] {query[:50]}...")
            return [LinkedInProfile(**p) for p in cached]
        
        print(f"  [Searching] {query[:60]}...")
        
        all_profiles = []
        
        # 轮流使用代理
        for i, proxy in enumerate(self.proxies):
            if len(all_profiles) >= max_results:
                break
            
            html = await self.search_with_proxy(query, proxy)
            
            if html:
                profiles = self._extract_linkedin_profiles(html, query)
                
                # 去重
                new_profiles = [
                    p for p in profiles 
                    if p.url not in self.discovered_urls
                ]
                
                for p in new_profiles:
                    self.discovered_urls.add(p.url)
                    all_profiles.append(p)
                
                print(f"    ✅ Proxy {i+1}: 找到 {len(profiles)} 个，新增 {len(new_profiles)} 个")
                
                # 如果找到足够结果，提前结束
                if len(all_profiles) >= max_results:
                    break
            else:
                print(f"    ❌ Proxy {i+1}: 失败")
            
            # 延迟避免被封
            await asyncio.sleep(2)
        
        # 缓存结果 (24小时)
        if all_profiles:
            self.cache.set(
                cache_key, 
                [p.to_dict() for p in all_profiles], 
                ttl=86400
            )
        
        return all_profiles[:max_results]
    
    async def search_all(
        self, 
        queries: List[str] = None,
        max_results_per_query: int = 20,
        min_match_score: float = 0.3
    ) -> List[LinkedInProfile]:
        """
        执行所有查询的 X-Ray 搜索
        
        Args:
            queries: 自定义查询列表，默认使用 DEFAULT_QUERIES
            max_results_per_query: 每个查询最大结果数
            min_match_score: 最低匹配分数过滤
            
        Returns:
            所有发现的 LinkedInProfile（已去重排序）
        """
        if queries is None:
            queries = self.DEFAULT_QUERIES
        
        print("=" * 80)
        print("🔍 X-Ray LinkedIn 人才搜索")
        print("=" * 80)
        print(f"查询数量: {len(queries)}")
        print(f"代理数量: {len(self.proxies)}")
        print()
        
        all_profiles = []
        
        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] 执行查询...")
            profiles = await self.search_single_query(query, max_results_per_query)
            all_profiles.extend(profiles)
            print()
        
        # 过滤低分结果
        filtered = [p for p in all_profiles if p.match_score >= min_match_score]
        
        # 按匹配分数排序
        sorted_profiles = sorted(filtered, key=lambda x: x.match_score, reverse=True)
        
        print("=" * 80)
        print(f"📊 搜索结果汇总")
        print("=" * 80)
        print(f"总发现: {len(all_profiles)} 个档案")
        print(f"通过过滤 (≥{min_match_score}分): {len(sorted_profiles)} 个档案")
        print()
        
        # 按优先级分组
        high = sum(1 for p in sorted_profiles if p.match_score >= 0.7)
        medium = sum(1 for p in sorted_profiles if 0.5 <= p.match_score < 0.7)
        low = sum(1 for p in sorted_profiles if p.match_score < 0.5)
        
        print(f"优先级分布:")
        print(f"  🔴 High (≥0.7): {high} 个")
        print(f"  🟡 Medium (0.5-0.7): {medium} 个")
        print(f"  🟢 Low (<0.5): {low} 个")
        print()
        
        return sorted_profiles
    
    def export_to_markdown(
        self, 
        profiles: List[LinkedInProfile], 
        output_path: str = "output/xray_linkedin_results.md"
    ):
        """导出结果为 Markdown"""
        from pathlib import Path
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# X-Ray LinkedIn 人才搜索结果\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"总计发现: {len(profiles)} 个高匹配度档案\n\n")
            
            # 高分优先
            f.write("## 🔴 高优先级 (匹配度 ≥ 0.7)\n\n")
            for p in profiles:
                if p.match_score >= 0.7:
                    f.write(f"### {p.name}\n")
                    f.write(f"- **LinkedIn**: [{p.url}]({p.url})\n")
                    f.write(f"- **匹配度**: {p.match_score}\n")
                    f.write(f"- **AI指标**: {p.ai_indicators}, **无线指标**: {p.wireless_indicators}\n")
                    f.write(f"- **来源查询**: `{p.source_query}`\n\n")
            
            # 中分
            f.write("## 🟡 中优先级 (匹配度 0.5-0.7)\n\n")
            for p in profiles:
                if 0.5 <= p.match_score < 0.7:
                    f.write(f"- **{p.name}** | [链接]({p.url}) | 匹配度: {p.match_score}\n")
            
            f.write("\n")
        
        print(f"💾 结果已导出: {output_path}")


# 同步包装函数
def search_linkedin_xray(
    queries: List[str] = None,
    max_results_per_query: int = 20,
    min_match_score: float = 0.3,
    proxy_config_path: str = "config/proxies.yaml"
) -> List[LinkedInProfile]:
    """同步接口执行 X-Ray 搜索"""
    searcher = XRayLinkedInSearcher(proxy_config_path)
    return asyncio.run(searcher.search_all(queries, max_results_per_query, min_match_score))


# 测试
if __name__ == "__main__":
    print("=" * 80)
    print(" X-Ray LinkedIn Searcher - 测试模式")
    print("=" * 80)
    print()
    
    # 显示默认查询
    print("默认查询列表:")
    for i, q in enumerate(XRayLinkedInSearcher.DEFAULT_QUERIES, 1):
        print(f"  {i}. {q}")
    print()
    
    # 测试评估函数
    print("测试人才评估:")
    searcher = XRayLinkedInSearcher()
    
    test_cases = [
        ("Zhang Wei", "zhang-wei-ml-engineer", "site:linkedin.com/in machine learning"),
        ("Li Hua", "li-hua-wireless-researcher", "site:linkedin.com/in wireless communication"),
        ("Wang Ming", "wang-ming-ai-5g-expert", "site:linkedin.com/in AI 5G"),
    ]
    
    for name, slug, query in test_cases:
        result = searcher._evaluate_profile(name, slug, query)
        print(f"  {name}: 匹配度 {result['match_score']}, AI: {result['ai_indicators']}, Wireless: {result['wireless_indicators']}")
    
    print()
    print("运行完整搜索需要配置代理 (config/proxies.yaml)")
    print("示例用法:")
    print("  from xray_linkedin_searcher import search_linkedin_xray")
    print("  profiles = search_linkedin_xray(max_results_per_query=10)")
