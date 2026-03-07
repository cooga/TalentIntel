#!/usr/bin/env python3
"""
快速人才检索脚本 - 使用Decodo住宅代理
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
import sys

# 加载代理配置
with open('config/proxies.yaml') as f:
    config = yaml.safe_load(f)

# 使用多个代理轮换
proxies = config['proxies'][:4]  # 使用美/英/德/日代理

SEARCH_KEYWORDS = [
    "machine learning wireless",
    "AI engineer 5G", 
    "deep learning MIMO",
    "6G artificial intelligence",
    "wireless sensing AI",
    "federated learning wireless",
    "OFDM machine learning",
    "beamforming deep learning",
    "channel estimation neural",
    "semantic communication"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

class TalentHunter:
    def __init__(self):
        self.proxy_index = 0
        self.stats = {"searches": 0, "profiles": 0, "high_score": 0}
        self.candidates = []
        self.seen_urls = set()
        
    def get_proxy(self):
        p = proxies[self.proxy_index % len(proxies)]
        self.proxy_index += 1
        return f"http://{p['username']}:{p['password']}@{p['host']}:{p['port']}"
    
    def evaluate_profile(self, name, url, keyword):
        text = f"{name} {keyword}".lower()
        
        ai_keywords = ["machine learning", "deep learning", "ai", "artificial intelligence", 
                      "neural", "federated", "transformer", "llm"]
        wireless_keywords = ["wireless", "5g", "6g", "mimo", "ofdm", "communication",
                           "sensing", "beamforming", "signal", "telecom", 
                           "cellular", "radio", "channel", "semantic"]
        
        ai_score = sum(1 for kw in ai_keywords if kw in text)
        wireless_score = sum(1 for kw in wireless_keywords if kw in text)
        
        ai_norm = min(ai_score / 2, 1.0)
        wireless_norm = min(wireless_score / 2, 1.0)
        cross_bonus = 0.3 if (ai_score >= 1 and wireless_score >= 1) else 0
        
        match_score = (ai_norm * 0.4 + wireless_norm * 0.4 + cross_bonus)
        match_score = min(match_score, 1.0)
        
        return {
            "name": name,
            "url": url,
            "keyword": keyword,
            "match_score": round(match_score, 2),
            "ai_score": ai_score,
            "wireless_score": wireless_score,
            "priority": "high" if match_score >= 0.7 else "medium" if match_score >= 0.5 else "low"
        }
    
    async def search_google(self, keyword, session):
        query = f'site:linkedin.com/in "{keyword}"'
        params = urllib.parse.urlencode({"q": query, "num": 20})
        url = f"https://www.google.com/search?{params}"
        
        proxy_url = self.get_proxy()
        
        try:
            timeout = ClientTimeout(total=20)
            async with session.get(url, proxy=proxy_url, ssl=False, timeout=timeout) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    return self.extract_profiles(html, keyword)
                elif resp.status == 429:
                    print(f"  ⚠️  触发限制(429)，等待...")
                    await asyncio.sleep(random.uniform(30, 60))
                    return []
                else:
                    return []
        except Exception as e:
            return []
    
    def extract_profiles(self, html, keyword):
        profiles = []
        pattern = r'https://[^"\s<>]*linkedin\.com/in/[^"\s<>]+'
        urls = re.findall(pattern, html, re.IGNORECASE)
        
        seen = set()
        for url in urls:
            clean_url = re.sub(r'\?.*$', '', url)
            clean_url = re.sub(r'/$', '', clean_url)
            
            if clean_url not in seen and '/in/' in clean_url and clean_url not in self.seen_urls:
                seen.add(clean_url)
                self.seen_urls.add(clean_url)
                
                name_match = re.search(r'/in/([^/]+)', clean_url)
                name = name_match.group(1).replace('-', ' ').replace('_', ' ').title() if name_match else "Unknown"
                profiles.append({"url": clean_url, "name": name, "keyword": keyword})
        
        return profiles
    
    async def run_hunt(self):
        print("=" * 70)
        print("🎯 TalentIntel - LinkedIn人才检索")
        print(f"关键词: {len(SEARCH_KEYWORDS)}个 | 代理: {len(proxies)}个")
        print("=" * 70)
        
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            for i, keyword in enumerate(SEARCH_KEYWORDS):
                print(f"\n[{i+1}/{len(SEARCH_KEYWORDS)}] 搜索: {keyword}")
                
                profiles = await self.search_google(keyword, session)
                self.stats["searches"] += 1
                self.stats["profiles"] += len(profiles)
                
                print(f"   找到 {len(profiles)} 个档案", end="")
                
                for p in profiles:
                    result = self.evaluate_profile(p["name"], p["url"], keyword)
                    if result["match_score"] >= 0.7:
                        self.candidates.append(result)
                        self.stats["high_score"] += 1
                        print(f"\n   ⭐ {result['name']} ({result['match_score']})")
                
                print()  # 换行
                await asyncio.sleep(random.uniform(5, 12))
        
        return self.candidates

if __name__ == "__main__":
    hunter = TalentHunter()
    results = asyncio.run(hunter.run_hunt())
    
    # 去重
    unique = []
    seen = set()
    for c in results:
        if c["url"] not in seen:
            seen.add(c["url"])
            unique.append(c)
    
    # 保存
    output_dir = Path("data/findings/2026-03-04")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%H%M%S")
    
    with open(output_dir / f"batch_{timestamp}.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "stats": hunter.stats,
            "candidates": unique
        }, f, indent=2)
    
    print("\n" + "=" * 70)
    print("📊 检索完成")
    print(f"搜索: {hunter.stats['searches']} | 档案: {hunter.stats['profiles']} | 高分: {len(unique)}")
    print("=" * 70)
