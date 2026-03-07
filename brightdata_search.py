#!/usr/bin/env python3
"""
Bright Data SERP API 搜索模块
用于替代Google爬虫，稳定获取搜索结果
"""
import asyncio
import aiohttp
import json
import re
from datetime import datetime
from pathlib import Path

# Bright Data SERP API 配置 - 使用 Scraping Browser 格式
BRIGHTDATA_API_TOKEN = "b80e2a1d-fc62-4a98-9bab-5acc0b290aaf"
BRIGHTDATA_ZONE = "openclaw"

# 尝试使用代理方式连接
BRIGHTDATA_PROXY_HOST = "brd.superproxy.io"
BRIGHTDATA_PROXY_PORT = 22225

def get_proxy_url():
    """获取Bright Data代理URL"""
    return f"http://brd-customer-hl-{BRIGHTDATA_ZONE}-zone-{BRIGHTDATA_ZONE}:{BRIGHTDATA_API_TOKEN}@{BRIGHTDATA_PROXY_HOST}:{BRIGHTDATA_PROXY_PORT}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

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

    # 排除常见非华人姓氏
    exclude = ['nguyen', 'park', 'kim', 'choi', 'singh', 'patel', 'gupta', 'kumar']
    if any(e in name_lower for e in exclude):
        return False

    return any(s in words for s in chinese_surnames)


def extract_linkedin_profiles(html_content):
    """从HTML中提取LinkedIn档案链接"""
    if not html_content:
        return []

    profiles = []
    # 匹配LinkedIn个人档案URL
    pattern = r'https?://(?:www\.)?linkedin\.com/in/[^"\s<>]+'
    matches = re.findall(pattern, html_content, re.IGNORECASE)

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
                profiles.append({"url": clean, "name": name})

    return profiles


def evaluate_profile(profile):
    """评估候选人匹配度"""
    name = profile.get("name", "")
    name_lower = name.lower()
    url_lower = profile.get("url", "").lower()

    # 必须是华人
    if not is_chinese_name(name):
        return None

    # AI关键词评分
    ai_keywords = ["ai", "ml", "machine learning", "deep learning", "neural", "research scientist",
                   "data scientist", "algorithm", "artificial intelligence", "researcher"]
    ai_score = sum(2 for kw in ai_keywords if kw in name_lower or kw in url_lower)

    # 无线通信关键词评分
    wireless_keywords = ["wireless", "5g", "6g", "communication", "signal", "mimo",
                         "ofdm", "radio", "network", "telecom", "channel", "antenna", "modem", "physical layer"]
    wireless_score = sum(2 for kw in wireless_keywords if kw in name_lower or kw in url_lower)

    # 公司/学校加分
    top_institutions = ["stanford", "mit", "berkeley", "cmu", "google", "nvidia", "apple", "meta", "qualcomm", "intel"]
    bonus = sum(0.3 for inst in top_institutions if inst in url_lower)

    # 计算总分
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
    """使用Bright Data SERP API进行搜索"""
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    
    # 尝试多种可能的API端点格式
    api_endpoints = [
        # 格式1: /serp
        f"https://api.brightdata.com/serp/req?zone={BRIGHTDATA_ZONE}&api_token={BRIGHTDATA_API_TOKEN}&url={url}",
        # 格式2: /request
        f"https://api.brightdata.com/request?zone={BRIGHTDATA_ZONE}&api_token={BRIGHTDATA_API_TOKEN}&url={url}",
    ]
    
    for api_url in api_endpoints:
        try:
            print(f"  尝试: {api_url[:80]}...")
            headers = {
                "Content-Type": "application/json"
            }
            
            async with session.get(api_url, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    html = result.get('body', result.get('html', result.get('results', '')))
                    print(f"    ✅ 成功!")
                    return html
                else:
                    error_text = await resp.text()
                    print(f"    ❌ 状态码: {resp.status}")
        except Exception as e:
            print(f"    ❌ 异常: {e}")
    
    return None


async def main():
    print("=" * 70)
    print("🎯 TalentIntel - Bright Data SERP API 搜索")
    print("=" * 70)
    print(f"搜索目标: 补充高分华人候选人 (≥0.75)")
    print(f"当前进度: 8/10 人")
    print(f"API Zone: {BRIGHTDATA_ZONE}")
    print("=" * 70)

    all_profiles = []
    high_score_candidates = []

    async with aiohttp.ClientSession() as session:
        for i, query in enumerate(SEARCH_QUERIES):
            print(f"\n[{i+1}/{len(SEARCH_QUERIES)}] 搜索: {query[:50]}...")

            html = await search_with_brightdata(query, session)

            if html:
                profiles = extract_linkedin_profiles(html)
                print(f"  ✅ 找到 {len(profiles)} 个档案")

                for p in profiles:
                    evaluated = evaluate_profile(p)
                    if evaluated and evaluated["match_score"] >= 0.75:
                        # 检查是否已存在
                        all_profiles.append(evaluated)
                        high_score_candidates.append(evaluated)
                        print(f"  ⭐ 高分华人: {evaluated['name']} - {evaluated['match_score']}")
            else:
                print(f"  ⚠️  搜索失败或无结果")

            # Bright Data建议间隔
            await asyncio.sleep(2)

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

    result_file = output_dir / f"brightdata_chinese_{timestamp}.json"
    with open(result_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "api": "brightdata_serp",
            "target": "chinese_north_america",
            "min_score": 0.75,
            "found_candidates": len(unique_candidates),
            "candidates": unique_candidates
        }, f, indent=2)

    # 报告
    print("\n" + "=" * 70)
    print("📊 搜索完成")
    print(f"找到高分华人候选人: {len(unique_candidates)} 人")
    print(f"结果保存: {result_file}")
    print("=" * 70)

    if unique_candidates:
        print("\n🏆 候选人列表:")
        for i, c in enumerate(unique_candidates, 1):
            print(f"{i}. {c['name']} - 分数: {c['match_score']}")
            print(f"   {c['url']}")
    else:
        print("\n⚠️ 本次搜索未找到符合条件的新候选人")
        print("建议: 尝试调整搜索关键词或降低分数阈值")


if __name__ == "__main__":
    asyncio.run(main())
