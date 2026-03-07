#!/usr/bin/env python3
"""
扩展X-Ray搜索 - 多策略并行检索
目标: 获取更多北美大厂华人AI+无线专家
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

# 扩展搜索策略
SEARCH_STRATEGIES = [
    # 北美大厂策略
    ('site:linkedin.com/in "NVIDIA" "AI" "wireless" "United States"', "NVIDIA美国AI无线"),
    ('site:linkedin.com/in "Google" "machine learning" "communication" "California"', "Google加州ML通信"),
    ('site:linkedin.com/in "Meta" "AI" "wireless" OR "connectivity"', "Meta AI无线"),
    ('site:linkedin.com/in "Apple" "wireless" "machine learning" "Cupertino"', "Apple无线ML"),
    ('site:linkedin.com/in "Microsoft" "AI" "5G" OR "wireless"', "Microsoft AI无线"),
    ('site:linkedin.com/in "Amazon" "AWS" "wireless" "machine learning"', "Amazon无线ML"),
    ('site:linkedin.com/in "Qualcomm" "AI" "San Diego"', "Qualcomm AI圣地亚哥"),
    ('site:linkedin.com/in "Intel" "AI" "wireless" "Oregon"', "Intel AI无线"),
    ('site:linkedin.com/in "Broadcom" "machine learning" "California"', "Broadcom ML加州"),
    
    # 职位+技能组合
    ('site:linkedin.com/in "Research Scientist" "deep learning" "MIMO" "United States"', "美国研究员MIMO深度学习"),
    ('site:linkedin.com/in "Staff Engineer" "AI" "5G"', "Staff工程师AI 5G"),
    ('site:linkedin.com/in "Principal Engineer" "wireless" "neural network"', "Principal工程师无线神经网络"),
    ('site:linkedin.com/in "Senior Engineer" "federated learning" "wireless"', "高级工程师联邦学习无线"),
    
    # 技术方向
    ('site:linkedin.com/in "beamforming" "deep learning" "United States"', "波束成形深度学习美国"),
    ('site:linkedin.com/in "OFDM" "machine learning" "United States"', "OFDM ML美国"),
    ('site:linkedin.com/in "channel estimation" "neural network" "United States"', "信道估计神经网络美国"),
    ('site:linkedin.com/in "semantic communication" "AI" "United States"', "语义通信AI美国"),
    
    # 学术+产业
    ('site:linkedin.com/in "PhD" "Stanford" "wireless" "AI"', "斯坦福博士无线AI"),
    ('site:linkedin.com/in "PhD" "MIT" "wireless" "machine learning"', "MIT博士无线ML"),
    ('site:linkedin.com/in "PhD" "Berkeley" "communication" "AI"', "伯克利博士通信AI"),
]

# 华人姓氏
CHINESE_NAMES = ['chen', 'wang', 'li', 'liu', 'zhang', 'lin', 'yang', 'wu', 'zhou', 'zhao', 
                 'huang', 'xu', 'sun', 'hu', 'ma', 'guo', 'he', 'zheng', 'xie', 'song']

# 北美地区
NORTH_AMERICA = ['united states', 'usa', 'california', 'ca', 'texas', 'tx', 'new york', 'ny',
                 'washington', 'wa', 'massachusetts', 'ma', 'illinois', 'il', 'colorado', 'co',
                 'oregon', 'or', 'arizona', 'az', 'florida', 'fl', 'georgia', 'ga', 'canada',
                 'palo alto', 'san francisco', 'seattle', 'austin', 'boston', 'mountain view',
                 'sunnyvale', 'cupertino', 'santa clara', 'menlo park', 'redmond', 'bellevue',
                 'san diego', 'plano']

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def is_chinese_name(name):
    name_lower = name.lower()
    return any(s in name_lower for s in CHINESE_NAMES)

def is_north_america(location):
    if not location:
        return False
    location_lower = location.lower()
    return any(loc in location_lower for loc in NORTH_AMERICA)

def evaluate_profile(name, title, location):
    text = f"{name} {title}".lower()
    
    ai_score = 0
    wireless_score = 0
    
    ai_keywords = ['ai', 'machine learning', 'deep learning', 'ml', 'neural', 'research scientist']
    wireless_keywords = ['wireless', '5g', '6g', 'communication', 'mimo', 'signal', 'ofdm']
    
    for kw in ai_keywords:
        if kw in text:
            ai_score += 0.15
    for kw in wireless_keywords:
        if kw in text:
            wireless_score += 0.15
    
    # 北美奖励
    na_bonus = 0.2 if is_north_america(location) else 0
    
    match_score = min(ai_score + wireless_score + na_bonus, 1.0)
    return round(match_score, 2)

async def search_single(query, label, proxy, session):
    """执行单个搜索"""
    proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=10"
    
    try:
        timeout = ClientTimeout(total=25)
        async with session.get(url, proxy=proxy_url, ssl=False, timeout=timeout) as resp:
            if resp.status == 200:
                html = await resp.text()
                profiles = extract_profiles(html)
                return label, profiles
    except Exception as e:
        pass
    return label, []

def extract_profiles(html):
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
            profiles.append({"name": name, "url": f"https://linkedin.com/in/{clean}"})
    return profiles

async def main():
    print("=" * 75)
    print("🎯 扩展检索 - 北美大厂华人AI+无线专家")
    print(f"搜索策略: {len(SEARCH_STRATEGIES)}个 | 代理: {len(proxies)}个")
    print("=" * 75)
    
    all_profiles = []
    chinese_na_candidates = []
    
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        for i, (query, label) in enumerate(SEARCH_STRATEGIES):
            proxy = proxies[i % len(proxies)]
            print(f"\n[{i+1}/{len(SEARCH_STRATEGIES)}] {label}")
            
            label, profiles = await search_single(query, label, proxy, session)
            
            for p in profiles:
                all_profiles.append(p)
                
                if is_chinese_name(p['name']):
                    score = evaluate_profile(p['name'], '', '')
                    if score >= 0.5:
                        p['match_score'] = score
                        p['source'] = label
                        chinese_na_candidates.append(p)
                        print(f"  ⭐ {p['name']} (匹配度: {score})")
            
            if profiles:
                print(f"   找到 {len(profiles)} 个档案")
            
            await asyncio.sleep(5)
            
            # 每5个策略报告一次
            if (i + 1) % 5 == 0:
                print(f"\n   📊 进度: 已找到 {len(chinese_na_candidates)} 位华人候选人")
    
    # 去重
    seen = set()
    unique = []
    for c in chinese_na_candidates:
        if c['url'] not in seen:
            seen.add(c['url'])
            unique.append(c)
    
    unique.sort(key=lambda x: x['match_score'], reverse=True)
    
    # 保存
    output_dir = Path("data/findings/2026-03-04")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%H%M%S")
    
    output_file = output_dir / f"extended_chinese_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_profiles": len(all_profiles),
            "chinese_candidates": len(unique),
            "candidates": unique
        }, f, indent=2)
    
    print("\n" + "=" * 75)
    print(f"📊 完成! 总档案: {len(all_profiles)} | 华人候选人: {len(unique)}")
    print("=" * 75)
    
    if unique:
        print("\n🏆 高分候选人:")
        for i, c in enumerate(unique[:20], 1):
            print(f"{i:2d}. {c['name']:25s} | {c['match_score']:.2f} | {c['source'][:30]}")
    
    print(f"\n💾 结果: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
