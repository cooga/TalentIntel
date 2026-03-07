#!/usr/bin/env python3
"""
北美大厂华人AI+无线通信专家检索脚本
使用X-Ray搜索技术 + Decodo住宅代理
"""
import asyncio
import aiohttp
from aiohttp import ClientTimeout
import yaml
import json
import re
from datetime import datetime
from pathlib import Path
import urllib.parse
import random

# ============ 配置 ============
# 加载Decodo代理
with open('config/proxies.yaml') as f:
    proxy_config = yaml.safe_load(f)
proxies = proxy_config['proxies']

# 北美大厂列表
BIG_TECH_COMPANIES = [
    "Google", "Meta", "NVIDIA", "Apple", "Microsoft", "Amazon",
    "Qualcomm", "Intel", "Broadcom", "Cisco", "Oracle", "IBM",
    "Tesla", "AMD", "Marvell", "Texas Instruments"
]

# 华人常见姓氏（拼音形式）
CHINESE_SURNAMES = [
    "chen", "wang", "li", "liu", "zhang", "lin", "yang", "wu", "zhou", "zhao",
    "huang", "xu", "sun", "hu", "zhu", "guo", "ma", "luo", "gao", "lin",
    "he", "zheng", "xie", "song", "tang", "xu", "deng", "feng", "han", "cao"
]

# X-Ray搜索策略
SEARCH_STRATEGIES = [
    {
        "name": "北美大厂AI+无线通用搜索",
        "query": 'site:linkedin.com/in ("Google" OR "Meta" OR "NVIDIA" OR "Apple" OR "Microsoft" OR "Amazon") ("AI" OR "machine learning" OR "deep learning") ("wireless" OR "5G" OR "communication")',
    },
    {
        "name": "通信大厂AI专家",
        "query": 'site:linkedin.com/in ("Qualcomm" OR "Intel" OR "Broadcom" OR "Cisco") ("AI" OR "ML" OR "machine learning") ("wireless" OR "MIMO" OR "OFDM")',
    },
    {
        "name": "研究员+无线AI",
        "query": 'site:linkedin.com/in ("Research Scientist" OR "Staff Engineer" OR "Principal Engineer") ("AI" OR "deep learning") ("wireless" OR "communication")',
    },
    {
        "name": "5G/6G AI专家",
        "query": 'site:linkedin.com/in ("5G" OR "6G") ("AI" OR "machine learning") engineer',
    },
    {
        "name": "MIMO深度学习专家",
        "query": 'site:linkedin.com/in ("MIMO" OR "beamforming") ("deep learning" OR "neural network")',
    },
    {
        "name": "NVIDIA无线AI",
        "query": 'site:linkedin.com/in "NVIDIA" ("wireless" OR "communication" OR "5G")',
    },
    {
        "name": "Apple无线ML",
        "query": 'site:linkedin.com/in "Apple" ("wireless" OR "RF" OR "baseband") ("ML" OR "AI")',
    },
    {
        "name": "Google无线研究",
        "query": 'site:linkedin.com/in "Google" ("wireless" OR "connectivity") researcher',
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}

# ============ 候选人评估类 ============
class CandidateEvaluator:
    """评估候选人匹配度"""
    
    AI_KEYWORDS = [
        "ai", "artificial intelligence", "machine learning", "deep learning", 
        "ml", "neural network", "neural", "federated learning", "transformer",
        "llm", "large language model", "reinforcement learning", "computer vision",
        "nlp", "natural language", "data science", "algorithm"
    ]
    
    WIRELESS_KEYWORDS = [
        "wireless", "5g", "6g", "mimo", "ofdm", "communication", "telecom",
        "radio", "signal", "channel", "antenna", "rf", "baseband", "phy",
        "beamforming", "modulation", "spectrum", "cellular", "lte", "wifi",
        "bluetooth", "sensing", "localization", "mmwave", "massive mimo"
    ]
    
    BIG_TECH_KEYWORDS = [
        "google", "meta", "facebook", "nvidia", "apple", "microsoft", 
        "amazon", "aws", "qualcomm", "intel", "broadcom", "cisco",
        "oracle", "ibm", "tesla", "amd", "marvell", "ti", "texas instruments"
    ]
    
    @classmethod
    def evaluate(cls, profile: dict) -> dict:
        """评估候选人匹配度"""
        text = f"{profile.get('name', '')} {profile.get('title', '')} {profile.get('snippet', '')}".lower()
        url = profile.get('url', '').lower()
        
        # AI评分
        ai_score = sum(2 if kw in text else 0 for kw in cls.AI_KEYWORDS)
        ai_score = min(ai_score / 6, 1.0)  # 归一化
        
        # 无线通信评分
        wireless_score = sum(2 if kw in text else 0 for kw in cls.WIRELESS_KEYWORDS)
        wireless_score = min(wireless_score / 6, 1.0)  # 归一化
        
        # 北美大厂评分
        bigtech_score = sum(1 if kw in url or kw in text else 0 for kw in cls.BIG_TECH_KEYWORDS)
        bigtech_score = min(bigtech_score / 2, 1.0)
        
        # 交叉领域奖励
        cross_bonus = 0.15 if (ai_score > 0.3 and wireless_score > 0.3) else 0
        
        # 综合匹配度
        match_score = (ai_score * 0.35 + wireless_score * 0.35 + bigtech_score * 0.15 + cross_bonus)
        match_score = min(match_score, 1.0)
        
        # 判断是否华人
        is_chinese = cls._is_chinese_name(profile.get('name', ''))
        
        return {
            "url": profile['url'],
            "name": profile['name'],
            "match_score": round(match_score, 2),
            "ai_score": round(ai_score, 2),
            "wireless_score": round(wireless_score, 2),
            "bigtech_score": round(bigtech_score, 2),
            "is_chinese": is_chinese,
            "priority": "high" if match_score >= 0.7 else "medium" if match_score >= 0.5 else "low"
        }
    
    @classmethod
    def _is_chinese_name(cls, name: str) -> bool:
        """判断是否为华人姓名"""
        if not name:
            return False
        name_lower = name.lower()
        # 检查姓氏匹配
        for surname in CHINESE_SURNAMES:
            if name_lower.startswith(surname + " ") or name_lower == surname:
                return True
        return False


# ============ 搜索执行器 ============
class LinkedInHunter:
    """LinkedIn人才检索器"""
    
    def __init__(self):
        self.proxy_index = 0
        self.candidates = []
        self.seen_urls = set()
        self.stats = {
            "strategies": 0,
            "pages_fetched": 0,
            "profiles_found": 0,
            "chinese_candidates": 0,
            "high_score_candidates": 0
        }
    
    def get_proxy(self) -> dict:
        """获取下一个代理"""
        proxy = proxies[self.proxy_index % len(proxies)]
        self.proxy_index += 1
        return proxy
    
    def build_proxy_url(self, proxy: dict) -> str:
        """构建代理URL"""
        return f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
    
    async def search_google(self, query: str, session: aiohttp.ClientSession, page: int = 0) -> list:
        """执行Google搜索"""
        start = page * 10
        params = urllib.parse.urlencode({"q": query, "start": start, "num": 10, "hl": "en"})
        url = f"https://www.google.com/search?{params}"
        
        proxy = self.get_proxy()
        proxy_url = self.build_proxy_url(proxy)
        
        try:
            timeout = ClientTimeout(total=25)
            async with session.get(url, proxy=proxy_url, ssl=False, timeout=timeout) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    return self.extract_profiles(html)
                elif resp.status == 429:
                    print(f"    ⚠️  429限制，等待...")
                    await asyncio.sleep(random.uniform(30, 60))
                    return []
                else:
                    return []
        except Exception as e:
            return []
    
    def extract_profiles(self, html: str) -> list:
        """从HTML中提取LinkedIn档案"""
        profiles = []
        
        # 匹配LinkedIn档案URL
        pattern = r'https?://(?:www\.)?linkedin\.com/in/[^"\s<>]+'
        urls = re.findall(pattern, html, re.IGNORECASE)
        
        for url in urls:
            # 清洗URL
            clean_url = re.sub(r'\?.*$', '', url)
            clean_url = re.sub(r'/$', '', clean_url)
            clean_url = clean_url.replace('http://', 'https://')
            
            if clean_url not in self.seen_urls and '/in/' in clean_url:
                self.seen_urls.add(clean_url)
                
                # 提取姓名
                name_match = re.search(r'/in/([^/]+)', clean_url)
                if name_match:
                    raw_name = name_match.group(1)
                    name = raw_name.replace('-', ' ').replace('_', ' ').title()
                    
                    # 提取标题片段（如果有）
                    snippet = self._extract_snippet(html, clean_url)
                    
                    profiles.append({
                        "url": clean_url,
                        "name": name,
                        "raw_name": raw_name,
                        "snippet": snippet
                    })
        
        return profiles
    
    def _extract_snippet(self, html: str, url: str) -> str:
        """提取搜索结果中的简介片段"""
        # 简化处理，返回空字符串
        return ""
    
    async def run_search(self, progress_callback=None):
        """执行完整搜索"""
        print("=" * 75)
        print("🎯 北美大厂华人AI+无线通信专家检索")
        print(f"策略数: {len(SEARCH_STRATEGIES)} | 代理数: {len(proxies)}")
        print("=" * 75)
        
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            for idx, strategy in enumerate(SEARCH_STRATEGIES):
                self.stats["strategies"] += 1
                print(f"\n📋 策略 {idx+1}/{len(SEARCH_STRATEGIES)}: {strategy['name']}")
                print(f"   查询: {strategy['query'][:60]}...")
                
                # 每个策略搜索2页
                for page in range(2):
                    print(f"   🔍 页 {page+1}...", end=" ")
                    
                    profiles = await self.search_google(strategy['query'], session, page)
                    self.stats["pages_fetched"] += 1
                    self.stats["profiles_found"] += len(profiles)
                    
                    print(f"找到 {len(profiles)} 个档案")
                    
                    # 评估候选人
                    for p in profiles:
                        evaluated = CandidateEvaluator.evaluate(p)
                        
                        if evaluated['is_chinese']:
                            self.stats["chinese_candidates"] += 1
                            if evaluated['match_score'] >= 0.7:
                                self.stats["high_score_candidates"] += 1
                                self.candidates.append(evaluated)
                                print(f"   ⭐ {evaluated['name']} - 匹配度: {evaluated['match_score']}")
                    
                    # 延时避免触发限制
                    await asyncio.sleep(random.uniform(8, 15))
                
                # 每完成一个策略报告进度
                if progress_callback:
                    progress_callback(self.stats, self.candidates)
        
        return self.candidates
    
    def save_results(self):
        """保存搜索结果"""
        output_dir = Path("data/findings/2026-03-04")
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")
        
        # 去重
        seen = set()
        unique_candidates = []
        for c in self.candidates:
            if c['url'] not in seen:
                seen.add(c['url'])
                unique_candidates.append(c)
        
        # 按匹配度排序
        unique_candidates.sort(key=lambda x: x['match_score'], reverse=True)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "candidate_count": len(unique_candidates),
            "candidates": unique_candidates
        }
        
        output_file = output_dir / f"chinese_talent_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return output_file, unique_candidates


# ============ 主函数 ============
async def main():
    hunter = LinkedInHunter()
    
    # 进度回调
    def report_progress(stats, candidates):
        high_score = [c for c in candidates if c['match_score'] >= 0.7]
        if len(high_score) % 5 == 0 and len(high_score) > 0:
            print(f"\n   📊 进度: 已找到 {len(high_score)} 位高分华人候选人")
    
    # 执行搜索
    await hunter.run_search(progress_callback=report_progress)
    
    # 保存结果
    output_file, candidates = hunter.save_results()
    
    # 打印报告
    print("\n" + "=" * 75)
    print("📊 检索完成报告")
    print("=" * 75)
    print(f"执行策略: {hunter.stats['strategies']}")
    print(f"获取页面: {hunter.stats['pages_fetched']}")
    print(f"发现档案: {hunter.stats['profiles_found']}")
    print(f"华人候选人: {hunter.stats['chinese_candidates']}")
    print(f"高分候选人(≥0.7): {len(candidates)}")
    print("-" * 75)
    
    if candidates:
        print("\n🏆 高分华人AI+无线通信专家:")
        for i, c in enumerate(candidates[:20], 1):
            print(f"{i:2d}. {c['name']:20s} | 匹配度: {c['match_score']:.2f} | {c['url'][:50]}...")
    
    print(f"\n💾 结果已保存: {output_file}")
    
    # 返回结果供外部调用
    return {
        "stats": hunter.stats,
        "candidates": candidates,
        "output_file": str(output_file)
    }


if __name__ == "__main__":
    result = asyncio.run(main())
