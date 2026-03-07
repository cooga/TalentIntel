#!/usr/bin/env python3
"""
使用Decodo住宅代理执行XRay搜索
"""
import asyncio
import aiohttp
from aiohttp import ClientTimeout
import yaml
import json
import re
from datetime import datetime
from pathlib import Path
import sys

# 加载配置
with open('config/proxies.yaml') as f:
    config = yaml.safe_load(f)

proxies = config['proxies']

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

async def fetch_search(url, proxy, session):
    """执行搜索"""
    proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
    
    try:
        timeout = ClientTimeout(total=25)
        async with session.get(url, proxy=proxy_url, ssl=False, timeout=timeout, allow_redirects=True) as resp:
            if resp.status == 200:
                return await resp.text()
            elif resp.status == 429:
                print(f"    ⚠️  429限制")
                return None
            else:
                return None
    except Exception as e:
        return None

def extract_linkedin_profiles(html):
    """提取LinkedIn档案"""
    if not html:
        return []
    
    profiles = []
    # 匹配LinkedIn个人档案URL
    pattern = r'https?://(?:www\.)?linkedin\.com/in/[^"\s<>]+'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    seen = set()
    for url in matches:
        # 清洗URL
        clean = re.sub(r'\?.*$', '', url)
        clean = re.sub(r'/$', '', clean)
        clean = clean.replace('http://', 'https://')
        
        if clean not in seen and '/in/' in clean:
            seen.add(clean)
            # 提取姓名
            name_match = re.search(r'/in/([^/]+)', clean)
            if name_match:
                raw_name = name_match.group(1)
                name = raw_name.replace('-', ' ').replace('_', ' ').title()
                profiles.append({"url": clean, "name": name, "raw": raw_name})
    
    return profiles

def evaluate_profile(profile, strategy_name):
    """评估候选人"""
    name = profile.get("name", "").lower()
    raw = profile.get("raw", "").lower()
    combined = f"{name} {raw} {strategy_name}".lower()
    
    ai_kw = ["ai", "ml", "machine", "learning", "deep", "neural", "research", 
             "scientist", "data", "algorithm", "artificial", "intelligence"]
    wireless_kw = ["wireless", "5g", "6g", "communication", "signal", "mimo", 
                   "ofdm", "radio", "network", "telecom", "channel", "antenna"]
    
    ai_score = sum(1 for kw in ai_kw if kw in combined)
    wireless_score = sum(1 for kw in wireless_kw if kw in combined)
    
    # 交叉领域奖励
    cross_bonus = 0.25 if (ai_score > 0 and wireless_score > 0) else 0
    base_score = (min(ai_score, 4) * 0.15 + min(wireless_score, 4) * 0.15)
    match_score = min(base_score + cross_bonus, 1.0)
    
    return {
        "url": profile["url"],
        "name": profile["name"],
        "match_score": round(match_score, 2),
        "ai_indicators": ai_score,
        "wireless_indicators": wireless_score,
        "source_strategy": strategy_name,
        "priority": "high" if match_score >= 0.7 else "medium" if match_score >= 0.5 else "low"
    }

async def main():
    print("=" * 70)
    print("🎯 TalentIntel - Decodo住宅代理XRay搜索")
    print("=" * 70)
    
    # 加载campaign
    with open('data/xray_campaigns/campaign_20260304_094042.json') as f:
        campaign = json.load(f)
    
    all_profiles = []
    high_score_candidates = []
    proxy_idx = 0
    
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        for strategy_name, strategy in campaign["strategies"].items():
            print(f"\n📋 策略: {strategy['name']}")
            
            for link_info in strategy["links"]:
                search_url = link_info["url"]
                page = link_info["page"]
                
                # 轮换代理
                proxy = proxies[proxy_idx % len(proxies)]
                proxy_idx += 1
                
                print(f"  🔍 页 {page} - 代理 {proxy['host']}:{proxy['port']}")
                
                html = await fetch_search(search_url, proxy, session)
                
                if html:
                    profiles = extract_linkedin_profiles(html)
                    print(f"    ✅ 找到 {len(profiles)} 个档案")
                    
                    for p in profiles:
                        evaluated = evaluate_profile(p, strategy_name)
                        all_profiles.append(evaluated)
                        
                        if evaluated["match_score"] >= 0.7:
                            high_score_candidates.append(evaluated)
                            print(f"    ⭐ {evaluated['name']} - {evaluated['match_score']}")
                else:
                    print(f"    ❌ 获取失败")
                
                # 延时
                await asyncio.sleep(3)
    
    # 去重
    seen_urls = set()
    unique_candidates = []
    for c in high_score_candidates:
        if c["url"] not in seen_urls:
            seen_urls.add(c["url"])
            unique_candidates.append(c)
    
    # 保存结果
    output_dir = Path("data/findings/2026-03-04")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%H%M%S")
    
    result_file = output_dir / f"xray_results_{timestamp}.json"
    with open(result_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_profiles": len(all_profiles),
            "high_score_count": len(unique_candidates),
            "candidates": unique_candidates
        }, f, indent=2)
    
    # 报告
    print("\n" + "=" * 70)
    print("📊 搜索完成")
    print(f"总档案: {len(all_profiles)} | 高分候选人: {len(unique_candidates)}")
    print("=" * 70)
    
    if unique_candidates:
        print("\n🏆 高分候选人:")
        for i, c in enumerate(unique_candidates[:15], 1):
            print(f"{i}. {c['name']} - {c['match_score']} - {c['url'][:45]}")
    
    print(f"\n💾 结果已保存: {result_file}")

if __name__ == "__main__":
    asyncio.run(main())
