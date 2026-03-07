#!/usr/bin/env python3
"""
Bright Data SERP API 搜索模块 - URL参数认证版
"""
import asyncio
import aiohttp
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

# Bright Data SERP API 配置
BRIGHTDATA_API_URL = "https://api.brightdata.com/request"
BRIGHTDATA_TOKEN = "b80e2a1d-fc62-4a98-9bab-5acc0b290aaf"
BRIGHTDATA_ZONE = "openclaw"

# 专门针对北美华人的搜索关键词
SEARCH_QUERIES = [
    "site:linkedin.com/in chinese professor machine learning wireless Stanford MIT Berkeley",
    "site:linkedin.com/in chinese researcher AI 5G NVIDIA Google Meta Apple",
    "site:linkedin.com/in chinese engineer deep learning MIMO Qualcomm Broadcom Intel",
    "site:linkedin.com/in chinese scientist wireless communication CMU UCLA USC Columbia",
    "site:linkedin.com/in chinese postdoc neural network physical layer Bell Labs",
]


def is_chinese_name(name):
    """判断是否为华人姓名"""
    chinese_surnames = ['wang', 'liu', 'li', 'zhang', 'chen', 'yang', 'huang', 'zhao', 'wu', 'zhou',
                        'xu', 'sun', 'ma', 'zhu', 'hu', 'guo', 'lin', 'he', 'gao', 'zheng', 'liang',
                        'xie', 'song', 'tang', 'deng', 'han', 'feng', 'cao', 'peng', 'zeng', 'xiao',
                        'tian', 'dong', 'yuan', 'pan', 'yu', 'lu', 'jiang', 'cai', 'jia', 'ding', 'wei']

    name_lower = name.lower()
    words = name_lower.split()

    exclude = ['nguyen', 'park', 'kim', 'choi', 'singh', 'patel', 'gupta', 'kumar']
    if any(e in name_lower for e in exclude):
        return False

    return any(s in words for s in chinese_surnames)


def extract_linkedin_profiles(html_content):
    """从HTML中提取LinkedIn档案链接"""
    if not html_content:
        return []

    profiles = []
    pattern = r'https?://(?:www\.)?linkedin\.com/in/[^"\s<>]+'
    matches = re.findall(pattern, html_content, re.IGNORECASE)

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


def evaluate_profile(profile):
    """评估候选人匹配度"""
    name = profile.get("name", "")
    name_lower = name.lower()
    url_lower = profile.get("url", "").lower()

    if not is_chinese_name(name):
        return None

    ai_keywords = ["ai", "ml", "machine learning", "deep learning", "neural", "research scientist",
                   "data scientist", "algorithm", "artificial intelligence", "researcher"]
    ai_score = sum(2 for kw in ai_keywords if kw in name_lower or kw in url_lower)

    wireless_keywords = ["wireless", "5g", "6g", "communication", "signal", "mimo",
                         "ofdm", "radio", "network", "telecom", "channel", "antenna", "modem", "physical layer"]
    wireless_score = sum(2 for kw in wireless_keywords if kw in name_lower or kw in url_lower)

    top_institutions = ["stanford", "mit", "berkeley", "cmu", "google", "nvidia", "apple", "meta", "qualcomm", "intel"]
    bonus = sum(0.3 for inst in top_institutions if inst in url_lower)

    base_score = min(ai_score * 0.15 + wireless_score * 0.15 + bonus, 0.8)
    cross_bonus = 0.2 if (ai_score > 0 and wireless_score > 0) else 0
    match_score = min(base_score + cross_bonus, 1.0)

    return {
        "url": profile["url"],
        "name": profile["name"],
        "match_score": round(match_score, 2),
        "ai_indicators": ai_score,
        "wireless_indicators": wireless_score,
        "priority": "high" if match_score >= 0.75 else "medium" if match_score >= 0.6 else "low"
    }


async def search_with_brightdata(query, session):
    """使用Bright Data SERP API - URL参数认证"""
    search_url = f"https://www.google.com/search?q={quote(query)}"
    
    # URL参数方式传递认证信息
    api_url = f"{BRIGHTDATA_API_URL}?zone={BRIGHTDATA_ZONE}&api_key={BRIGHTDATA_TOKEN}"
    
    payload = {
        "url": search_url,
        "format": "raw"
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        async with session.post(api_url, headers=headers, json=payload, timeout=60) as resp:
            if resp.status == 200:
                result = await resp.json()
                html = result.get('body', result.get('html', ''))
                return html
            else:
                error_text = await resp.text()
                print(f"    ❌ API错误: {resp.status} - {error_text[:150]}")
                return None
    except Exception as e:
        print(f"    ❌ 请求异常: {e}")
        return None


async def main():
    print("=" * 70)
    print("🎯 Bright Data SERP API - URL参数认证版")
    print("=" * 70)

    all_profiles = []
    high_score_candidates = []

    async with aiohttp.ClientSession() as session:
        for i, query in enumerate(SEARCH_QUERIES):
            print(f"\n[{i+1}/{len(SEARCH_QUERIES)}] {query[:45]}...")

            html = await search_with_brightdata(query, session)

            if html:
                profiles = extract_linkedin_profiles(html)
                print(f"  ✅ {len(profiles)} 个档案")

                for p in profiles:
                    evaluated = evaluate_profile(p)
                    if evaluated and evaluated["match_score"] >= 0.75:
                        all_profiles.append(evaluated)
                        high_score_candidates.append(evaluated)
                        print(f"  ⭐ {evaluated['name']} - {evaluated['match_score']}")
            else:
                print(f"  ⚠️  失败")

            await asyncio.sleep(3)

    # 去重
    seen_urls = set()
    unique_candidates = []
    for c in high_score_candidates:
        if c["url"] not in seen_urls:
            seen_urls.add(c["url"])
            unique_candidates.append(c)

    # 保存
    output_dir = Path("data/findings/2026-03-05")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%H%M%S")

    result_file = output_dir / f"brightdata_chinese_{timestamp}.json"
    with open(result_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "api": "brightdata_serp_v2",
            "found_candidates": len(unique_candidates),
            "candidates": unique_candidates
        }, f, indent=2)

    print("\n" + "=" * 70)
    print(f"📊 完成: {len(unique_candidates)} 位高分华人候选人")
    print(f"💾 保存: {result_file}")
    print("=" * 70)

    if unique_candidates:
        print("\n🏆 候选人:")
        for i, c in enumerate(unique_candidates, 1):
            print(f"{i}. {c['name']} - {c['match_score']}")
    else:
        print("\n⚠️ 未找到新候选人")


if __name__ == "__main__":
    asyncio.run(main())
