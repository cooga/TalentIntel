#!/usr/bin/env python3
"""
快速华人AI+无线专家检索 - 轻量版
"""
import asyncio
import aiohttp
from aiohttp import ClientTimeout
import yaml
import json
import re
from datetime import datetime
from pathlib import Path

# 加载代理配置
with open('config/proxies.yaml') as f:
    config = yaml.safe_load(f)
proxies = config['proxies']

# 华人姓氏
CHINESE_NAMES = ["chen", "wang", "li", "liu", "zhang", "lin", "yang", "wu", "zhou", "zhao", 
                 "huang", "xu", "sun", "hu", "ma", "guo", "he", "zheng", "xie"]

# 核心搜索查询
SEARCH_QUERIES = [
    ('site:linkedin.com/in "NVIDIA" "wireless" "AI"', "NVIDIA无线AI"),
    ('site:linkedin.com/in "Qualcomm" "AI" "5G"', "Qualcomm AI+5G"),
    ('site:linkedin.com/in "Google" "wireless" "machine learning"', "Google无线ML"),
    ('site:linkedin.com/in "Apple" "wireless" "deep learning"', "Apple无线深度学习"),
    ('site:linkedin.com/in "Meta" "AI" "communication"', "Meta AI通信"),
    ('site:linkedin.com/in "Microsoft" "wireless" "AI"', "Microsoft无线AI"),
    ('site:linkedin.com/in "Intel" "AI" "5G"', "Intel AI+5G"),
    ('site:linkedin.com/in "Broadcom" "machine learning"', "Broadcom ML"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def is_chinese_name(name):
    name_lower = name.lower()
    return any(name_lower.startswith(s + " ") or name_lower == s for s in CHINESE_NAMES)

def evaluate_profile(name, url):
    text = name.lower()
    ai_terms = ["ai", "ml", "machine learning", "deep learning", "research", "scientist"]
    wireless_terms = ["wireless", "5g", "6g", "communication", "mimo", "signal", "network"]
    
    ai_score = sum(0.2 for t in ai_terms if t in text)
    wireless_score = sum(0.2 for t in wireless_terms if t in text)
    cross_bonus = 0.3 if ai_score > 0 and wireless_score > 0 else 0
    
    match_score = min(ai_score + wireless_score + cross_bonus, 1.0)
    return round(match_score, 2)

async def search_single(query, label, proxy, session):
    """执行单个搜索"""
    proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=10"
    
    try:
        timeout = ClientTimeout(total=20)
        async with session.get(url, proxy=proxy_url, ssl=False, timeout=timeout) as resp:
            if resp.status == 200:
                html = await resp.text()
                return extract_profiles(html, label)
    except Exception as e:
        pass
    return []

def extract_profiles(html, source):
    """提取档案"""
    profiles = []
    pattern = r'https?://(?:www\.)?linkedin\.com/in/([^"\s<>]+)'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    seen = set()
    for match in matches:
        clean = re.sub(r'\?.*$', '', match)
        if clean not in seen:
            seen.add(clean)
            name = clean.replace('-', ' ').replace('_', ' ').title()
            profiles.append({"name": name, "url": f"https://linkedin.com/in/{clean}", "source": source})
    return profiles

async def main():
    print("=" * 70)
    print("🎯 快速华人AI+无线专家检索")
    print("=" * 70)
    
    all_profiles = []
    chinese_candidates = []
    
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        for i, (query, label) in enumerate(SEARCH_QUERIES):
            proxy = proxies[i % len(proxies)]
            print(f"\n[{i+1}/{len(SEARCH_QUERIES)}] {label}")
            
            profiles = await search_single(query, label, proxy, session)
            all_profiles.extend(profiles)
            
            for p in profiles:
                if is_chinese_name(p['name']):
                    p['match_score'] = evaluate_profile(p['name'], p['url'])
                    chinese_candidates.append(p)
                    print(f"  ⭐ {p['name']} (匹配度: {p['match_score']})")
            
            await asyncio.sleep(3)
    
    # 去重
    seen = set()
    unique = []
    for c in chinese_candidates:
        if c['url'] not in seen and c['match_score'] >= 0.5:
            seen.add(c['url'])
            unique.append(c)
    
    unique.sort(key=lambda x: x['match_score'], reverse=True)
    
    # 保存
    output_dir = Path("data/findings/2026-03-04")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%H%M%S")
    
    output_file = output_dir / f"quick_chinese_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_profiles": len(all_profiles),
            "chinese_candidates": len(unique),
            "candidates": unique
        }, f, indent=2)
    
    print("\n" + "=" * 70)
    print(f"📊 完成! 总档案: {len(all_profiles)} | 华人候选人: {len(unique)}")
    print("=" * 70)
    
    if unique:
        print("\n🏆 高分候选人:")
        for i, c in enumerate(unique[:15], 1):
            print(f"{i:2d}. {c['name']:20s} | {c['match_score']:.2f} | {c['source']}")
    
    print(f"\n💾 结果: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
