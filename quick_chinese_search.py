#!/usr/bin/env python3
"""
快速华人候选人补充搜索 - 修复版
针对北美华人专家进行快速搜索
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

proxies = config['proxies'][:3]  # 只用前3个代理，减少时间

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# 专门针对北美华人的搜索URL
SEARCH_URLS = [
    # Google搜索 - 北美华人AI+无线专家
    "https://www.google.com/search?q=site:linkedin.com/in+chinese+professor+machine+learning+wireless+Stanford+MIT+Berkeley",
    "https://www.google.com/search?q=site:linkedin.com/in+chinese+researcher+AI+5G+NVIDIA+Google+Meta",
    "https://www.google.com/search?q=site:linkedin.com/in+chinese+engineer+deep+learning+MIMO+Qualcomm+Broadcom",
    "https://www.google.com/search?q=site:linkedin.com/in+chinese+scientist+wireless+communication+CMU+UCLA+USC",
]

async def fetch_search(url, proxy, session):
    """执行搜索"""
    proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
    
    try:
        timeout = ClientTimeout(total=20)
        async with session.get(url, proxy=proxy_url, ssl=False, timeout=timeout) as resp:
            if resp.status == 200:
                return await resp.text()
            return None
    except Exception:
        return None

def extract_linkedin_profiles(html):
    """提取LinkedIn档案"""
    if not html:
        return []
    
    profiles = []
    pattern = r'https?://(?:www\.)?linkedin\.com/in/[^"\s<>]+'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    seen = set()
    for url in matches:
        clean = re.sub(r'\?.*$', '', url)
        clean = re.sub(r'/$', '', clean)
        clean = clean.replace('http://', 'https://')
        
        if clean not in seen and '/in/' in clean:
            seen.add(clean)
            name_match = re.search(r'/in/([^/]+)', clean)
            if name_match:
                raw_name = name_match.group(1)
                name = raw_name.replace('-', ' ').replace('_', ' ').title()
                profiles.append({"url": clean, "name": name})
    
    return profiles

def is_chinese_name(name):
    """判断是否为华人姓名"""
    chinese_surnames = ['wang', 'liu', 'li', 'zhang', 'chen', 'yang', 'huang', 'zhao', 'wu', 'zhou', 
                        'xu', 'sun', 'ma', 'zhu', 'hu', 'guo', 'lin', 'he', 'gao', 'zheng', 'liang',
                        'xie', 'song', 'tang', 'deng', 'han', 'feng', 'cao', 'peng', 'zeng', 'xiao',
                        'tian', 'dong', 'yuan', 'pan', 'yu', 'lu', 'jiang', 'cai', 'jia', 'ding', 'wei']
    
    name_lower = name.lower()
    words = name_lower.split()
    
    # 排除常见非华人姓氏
    exclude = ['nguyen', 'park', 'kim', 'choi', 'singh', 'patel', 'gupta', 'kumar']
    if any(e in name_lower for e in exclude):
        return False
    
    return any(s in words for s in chinese_surnames)

def evaluate_profile(profile):
    """评估候选人"""
    name = profile.get("name", "")
    name_lower = name.lower()
    
    # 必须是华人
    if not is_chinese_name(name):
        return None
    
    # 评分逻辑
    ai_kw = ["ai", "ml", "machine learning", "deep learning", "neural", "research scientist", 
             "data scientist", "algorithm", "artificial intelligence"]
    wireless_kw = ["wireless", "5g", "6g", "communication", "signal", "mimo", 
                   "ofdm", "radio", "network", "telecom", "channel", "antenna", "modem"]
    
    ai_score = sum(1 for kw in ai_kw if kw in name_lower)
    wireless_score = sum(1 for kw in wireless_kw if kw in name_lower)
    
    # 通过名字推断背景（LinkedIn URL中的关键词）
    url_lower = profile.get("url", "").lower()
    ai_score += sum(1 for kw in ai_kw if kw in url_lower) * 0.5
    wireless_score += sum(1 for kw in wireless_kw if kw in url_lower) * 0.5
    
    # 基础分 + 交叉奖励
    base_score = min(ai_score, 3) * 0.2 + min(wireless_score, 3) * 0.2
    cross_bonus = 0.4 if (ai_score > 0 and wireless_score > 0) else 0
    match_score = min(base_score + cross_bonus, 1.0)
    
    return {
        "url": profile["url"],
        "name": name,
        "match_score": round(match_score, 2),
        "ai_indicators": int(ai_score),
        "wireless_indicators": int(wireless_score),
        "priority": "high" if match_score >= 0.75 else "medium" if match_score >= 0.5 else "low"
    }

async def main():
    print("=" * 70)
    print("🎯 TalentIntel - 北美华人专家快速搜索")
    print("=" * 70)
    print(f"搜索目标: 补充2位高分华人候选人 (≥0.75)")
    print(f"当前进度: 8/10 人")
    print("=" * 70)
    
    all_profiles = []
    high_score_candidates = []
    
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        for i, search_url in enumerate(SEARCH_URLS):
            proxy = proxies[i % len(proxies)]
            
            print(f"\n[{i+1}/{len(SEARCH_URLS)}] 搜索中...")
            
            html = await fetch_search(search_url, proxy, session)
            
            if html:
                profiles = extract_linkedin_profiles(html)
                print(f"  ✅ 找到 {len(profiles)} 个档案")
                
                for p in profiles:
                    evaluated = evaluate_profile(p)
                    if evaluated and evaluated["match_score"] >= 0.75:
                        # 检查是否已存在
                        all_profiles.append(evaluated)
                        high_score_candidates.append(evaluated)
                        print(f"  ⭐ 华人候选人: {evaluated['name']} - {evaluated['match_score']}")
            else:
                print(f"  ⚠️  搜索失败")
            
            await asyncio.sleep(2)  # 减少延迟
    
    # 去重
    seen_urls = set()
    unique_candidates = []
    for c in high_score_candidates:
        if c["url"] not in seen_urls:
            seen_urls.add(c["url"])
            unique_candidates.append(c)
    
    # 保存结果
    output_dir = Path("data/findings/2026-03-05")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%H%M%S")
    
    result_file = output_dir / f"chinese_candidates_{timestamp}.json"
    with open(result_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "target": "chinese_north_america",
            "min_score": 0.75,
            "found_candidates": len(unique_candidates),
            "candidates": unique_candidates
        }, f, indent=2)
    
    # 报告
    print("\n" + "=" * 70)
    print("📊 搜索完成")
    print(f"找到华人候选人: {len(unique_candidates)} 人")
    print(f"结果保存: {result_file}")
    print("=" * 70)
    
    if unique_candidates:
        print("\n🏆 高分华人候选人:")
        for i, c in enumerate(unique_candidates, 1):
            print(f"{i}. {c['name']} - 分数: {c['match_score']}")
            print(f"   {c['url']}")
    else:
        print("\n⚠️ 本次搜索未找到符合条件的新候选人")
        print("建议: 尝试调整搜索关键词或增加搜索页面")

if __name__ == "__main__":
    asyncio.run(main())
