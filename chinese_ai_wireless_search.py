#!/usr/bin/env python3
"""
华人 AI + 无线通信人才在线搜索
目标：补充15人缺口
搜索策略：Google Scholar + LinkedIn X-Ray + arXiv
"""
import asyncio
import aiohttp
from aiohttp import ClientTimeout
import json
import re
from datetime import datetime
from pathlib import Path

# 代理配置
PROXIES = [
    {"host": "gate.decodo.com", "port": 10000, "username": "user107515", "password": "xu8Jph4k"},
    {"host": "gate.decodo.com", "port": 10001, "username": "user107515", "password": "xu8Jph4k"},
    {"host": "gate.decodo.com", "port": 10002, "username": "user107515", "password": "xu8Jph4k"},
    {"host": "gate.decodo.com", "port": 10003, "username": "user107515", "password": "xu8Jph4k"},
    {"host": "gate.decodo.com", "port": 10004, "username": "user107515", "password": "xu8Jph4k"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# Google Scholar 搜索 URL - 针对 AI + 无线通信 + 华人学者
SCHOLAR_URLS = [
    # AI + 无线通信 + 华人学者
    "https://scholar.google.com/scholar?q=machine+learning+wireless+communication+author:chen+OR+author:wang+OR+author:liu+OR+author:zhang",
    "https://scholar.google.com/scholar?q=deep+learning+MIMO+channel+estimation+author:li+OR+author:yang+OR+author:huang",
    "https://scholar.google.com/scholar?q=AI+5G+6G+signal+processing+author:wu+OR+author:zhou+OR+author:xu",
    "https://scholar.google.com/scholar?q=neural+network+OFDM+beamforming+author:sun+OR+author:ma+OR+author:lin",
    "https://scholar.google.com/scholar?q=reinforcement+learning+wireless+networks+author:guo+OR+author:he+OR+author:zheng",
    # 顶会论文 + 华人作者
    "https://scholar.google.com/scholar?q=ICC+2024+AI+wireless+chinese+author",
    "https://scholar.google.com/scholar?q=Globecom+2024+machine+learning+wireless+author",
    "https://scholar.google.com/scholar?q=NeurIPS+2024+wireless+communication+author",
]

# LinkedIn X-Ray 搜索 URL
LINKEDIN_URLS = [
    # 北美顶级公司华人无线AI专家
    "https://www.google.com/search?q=site:linkedin.com/in+('wireless'+OR+'5G'+OR+'MIMO')+('AI'+OR+'machine+learning')+('research+scientist'+OR+'senior+engineer')+(chen+OR+wang+OR+liu+OR+zhang+OR+li)+('Google'+OR+'Meta'+OR+'Apple'+OR+'NVIDIA')",
    "https://www.google.com/search?q=site:linkedin.com/in+wireless+communication+AI+engineer+(yang+OR+huang+OR+zhao+OR+wu+OR+zhou)+(Qualcomm+OR+Broadcom+OR+Intel+OR+Samsung)",
    "https://www.google.com/search?q=site:linkedin.com/in+signal+processing+deep+learning+(xu+OR+sun+OR+ma+OR+lin+OR+guo)+(Stanford+OR+MIT+OR+Berkeley+OR+CMU)",
    "https://www.google.com/search?q=site:linkedin.com/in+RF+engineer+machine+learning+(he+OR+zheng+OR+xie+OR+song+OR+tang)+(North+America+OR+Canada)",
    "https://www.google.com/search?q=site:linkedin.com/in+antenna+AI+optimization+(deng+OR+han+OR+feng+OR+cao+OR+peng)+(PhD+OR+Researcher)",
]

async def fetch_with_proxy(url, proxy, session):
    """使用代理获取页面"""
    proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
    try:
        timeout = ClientTimeout(total=30)
        async with session.get(url, proxy=proxy_url, ssl=False, timeout=timeout) as resp:
            if resp.status == 200:
                return await resp.text()
            print(f"  ⚠️ HTTP {resp.status}")
            return None
    except Exception as e:
        return None

def extract_scholar_profiles(html):
    """从 Google Scholar 提取学者信息"""
    if not html:
        return []

    profiles = []

    # 匹配学者名字和机构
    # 模式: <div class="gs_ai_name"><a href="...">Name</a></div>
    name_pattern = r'<div class="gs_ai_name"><a[^>]*>([^<]+)</a></div>'
    names = re.findall(name_pattern, html)

    # 匹配机构
    aff_pattern = r'<div class="gs_ai_aff">([^<]+)</div>'
    affiliations = re.findall(aff_pattern, html)

    # 匹配研究兴趣
    int_pattern = r'<div class="gs_ai_int">([^<]+)</div>'
    interests = re.findall(int_pattern, html)

    for i, name in enumerate(names):
        profile = {
            "name": name.strip(),
            "source": "google_scholar",
            "url": "",
            "affiliation": affiliations[i] if i < len(affiliations) else "",
            "interests": interests[i] if i < len(interests) else ""
        }
        profiles.append(profile)

    return profiles

def extract_linkedin_profiles(html):
    """从搜索结果提取 LinkedIn 档案"""
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
                profiles.append({
                    "name": name,
                    "url": clean,
                    "source": "linkedin_xray"
                })

    return profiles

def is_chinese_name(name):
    """判断是否为华人姓名"""
    if not name:
        return False

    name_lower = name.lower()
    words = name_lower.split()

    chinese_surnames = [
        'wang', 'liu', 'li', 'zhang', 'chen', 'yang', 'huang', 'zhao', 'wu', 'zhou',
        'xu', 'sun', 'ma', 'zhu', 'hu', 'guo', 'lin', 'he', 'gao', 'zheng', 'liang',
        'xie', 'song', 'tang', 'deng', 'han', 'feng', 'cao', 'peng', 'zeng', 'xiao',
        'tian', 'dong', 'yuan', 'pan', 'yu', 'lu', 'jiang', 'cai', 'jia', 'ding', 'wei'
    ]

    exclude = ['nguyen', 'park', 'kim', 'choi', 'singh', 'patel', 'gupta', 'kumar',
               'tran', 'le', 'pham', 'truong', 'vo', 'vu']
    if any(e in name_lower for e in exclude):
        return False

    return any(s in words for s in chinese_surnames)

def evaluate_candidate(profile):
    """评估候选人匹配度"""
    name = profile.get("name", "")
    text = json.dumps(profile).lower()

    # AI 关键词
    ai_score = sum(1 for kw in ["ai", "machine learning", "deep learning", "neural", "reinforcement learning"] if kw in text)

    # 无线关键词
    wireless_score = sum(1 for kw in ["wireless", "5g", "6g", "mimo", "ofdm", "signal", "communication", "channel", "rf", "antenna"] if kw in text)

    # 经验关键词（推测资深程度）
    senior_indicators = ["professor", "senior", "lead", "principal", "director", "chief", "staff", "phd"]
    senior_score = sum(1 for kw in senior_indicators if kw in text)

    # 综合匹配分数
    match_score = min((ai_score + wireless_score) * 0.15 + senior_score * 0.1, 1.0)

    # 工作地点（推测）
    location = "Unknown"
    if any(x in text for x in ["stanford", "mit", "berkeley", "google", "meta", "nvidia", "san francisco", "california", "usa", "america"]):
        location = "North America"
    elif any(x in text for x in ["singapore", "taiwan", "hong kong"]):
        location = "Asia Pacific"
    elif any(x in text for x in ["london", "oxford", "cambridge", "eth", "germany", "france"]):
        location = "Europe"

    return {
        **profile,
        "match_score": round(match_score, 2),
        "ai_score": ai_score,
        "wireless_score": wireless_score,
        "senior_score": senior_score,
        "location_inferred": location,
        "has_3plus_years": senior_score >= 2  # 简单推断
    }

async def main():
    print("=" * 70)
    print("🔍 AI + 海外华人 + 无线背景人才在线搜索")
    print("=" * 70)
    print(f"目标：补充15人缺口")
    print(f"搜索时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    all_candidates = []

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        # 第一阶段：Google Scholar 搜索
        print("\n📚 阶段1: Google Scholar 学者搜索...")
        for i, url in enumerate(SCHOLAR_URLS):
            proxy = PROXIES[i % len(PROXIES)]
            print(f"\n[{i+1}/{len(SCHOLAR_URLS)}] 搜索...")

            html = await fetch_with_proxy(url, proxy, session)
            if html:
                profiles = extract_scholar_profiles(html)
                print(f"  ✅ 找到 {len(profiles)} 位学者")

                for p in profiles:
                    if is_chinese_name(p["name"]):
                        evaluated = evaluate_candidate(p)
                        if evaluated["match_score"] >= 0.3:
                            all_candidates.append(evaluated)
                            print(f"  ⭐ 华人候选人: {p['name']} (分数: {evaluated['match_score']})")
            else:
                print(f"  ⚠️ 搜索失败")

            await asyncio.sleep(2)

        # 第二阶段：LinkedIn X-Ray 搜索
        print("\n\n💼 阶段2: LinkedIn X-Ray 搜索...")
        for i, url in enumerate(LINKEDIN_URLS):
            proxy = PROXIES[i % len(PROXIES)]
            print(f"\n[{i+1}/{len(LINKEDIN_URLS)}] 搜索...")

            html = await fetch_with_proxy(url, proxy, session)
            if html:
                profiles = extract_linkedin_profiles(html)
                print(f"  ✅ 找到 {len(profiles)} 个档案")

                for p in profiles:
                    if is_chinese_name(p["name"]):
                        evaluated = evaluate_candidate(p)
                        if evaluated["match_score"] >= 0.3:
                            all_candidates.append(evaluated)
                            print(f"  ⭐ 华人候选人: {p['name']} (分数: {evaluated['match_score']})")
            else:
                print(f"  ⚠️ 搜索失败")

            await asyncio.sleep(2)

    # 去重
    seen_names = set()
    unique_candidates = []
    for c in all_candidates:
        name = c.get("name", "").lower()
        if name and name not in seen_names:
            seen_names.add(name)
            unique_candidates.append(c)

    # 按匹配分数排序
    unique_candidates.sort(key=lambda x: x["match_score"], reverse=True)

    # 取前20人
    final_candidates = unique_candidates[:20]

    # 统计
    with_3plus = [c for c in final_candidates if c.get("has_3plus_years")]
    north_america = [c for c in final_candidates if c.get("location_inferred") == "North America"]
    asia_pacific = [c for c in final_candidates if c.get("location_inferred") == "Asia Pacific"]

    print("\n" + "=" * 70)
    print("📊 搜索完成")
    print("=" * 70)
    print(f"总发现候选人: {len(all_candidates)}")
    print(f"去重后候选人: {len(unique_candidates)}")
    print(f"最终候选人: {len(final_candidates)}")
    print(f"3年以上经验: {len(with_3plus)} 人")
    print(f"北美地区: {len(north_america)} 人")
    print(f"亚太地区: {len(asia_pacific)} 人")

    # 保存结果
    output_dir = Path("data/findings/2026-03-08")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%H%M%S")

    result_file = output_dir / f"chinese_ai_wireless_search_{timestamp}.json"
    with open(result_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "search_target": "AI + 海外华人 + 无线背景",
            "target_count": 15,
            "found_candidates": len(final_candidates),
            "with_3plus_years": len(with_3plus),
            "by_region": {
                "north_america": len(north_america),
                "asia_pacific": len(asia_pacific),
                "other": len(final_candidates) - len(north_america) - len(asia_pacific)
            },
            "candidates": final_candidates
        }, f, indent=2)

    # 生成 Markdown
    md_file = output_dir / f"chinese_ai_wireless_search_{timestamp}.md"
    with open(md_file, "w") as f:
        f.write("# AI + 海外华人 + 无线背景人才搜索报告\n\n")
        f.write(f"**搜索时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**搜索目标**: 补充15人缺口\n\n")
        f.write("## 统计概览\n\n")
        f.write(f"- **找到候选人**: {len(final_candidates)} 人\n")
        f.write(f"- **3年以上经验**: {len(with_3plus)} 人\n")
        f.write(f"- **北美地区**: {len(north_america)} 人\n")
        f.write(f"- **亚太地区**: {len(asia_pacific)} 人\n\n")

        f.write("## ⭐ 候选人列表\n\n")
        for i, c in enumerate(final_candidates, 1):
            exp_badge = "⭐" if c.get("has_3plus_years") else ""
            f.write(f"### {i}. {c['name']} {exp_badge}\n\n")
            f.write(f"- **来源**: {c.get('source', 'unknown')}\n")
            f.write(f"- **机构/公司**: {c.get('affiliation', c.get('source', ''))}\n")
            f.write(f"- **推断地点**: {c.get('location_inferred', 'Unknown')}\n")
            f.write(f"- **匹配分数**: {c.get('match_score', 0)}\n")
            f.write(f"- **LinkedIn/URL**: {c.get('url', 'N/A')}\n")
            f.write(f"- **AI相关度**: {c.get('ai_score', 0)}\n")
            f.write(f"- **无线相关度**: {c.get('wireless_score', 0)}\n\n")

    print(f"\n✅ 结果已保存:")
    print(f"   JSON: {result_file}")
    print(f"   Markdown: {md_file}")

    print("\n🏆 TOP 候选人:")
    for i, c in enumerate(final_candidates[:10], 1):
        exp_badge = "⭐" if c.get("has_3plus_years") else ""
        print(f"{i}. {c['name']} {exp_badge} - 分数: {c['match_score']}")
        print(f"   地点: {c.get('location_inferred', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(main())
