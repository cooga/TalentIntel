#!/usr/bin/env python3
"""
无线通信/EE 背景人才搜索
目标：20人，要求有无线通信背景或EE专业
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

proxies = config['proxies'][:5]  # 使用5个代理

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# 无线通信/EE 背景搜索URL - 多角度搜索
SEARCH_URLS = [
    # 华人无线通信专家
    "https://www.google.com/search?q=site:linkedin.com/in+wireless+communication+engineer+phd+chinese",
    "https://www.google.com/search?q=site:linkedin.com/in+5G+6G+researcher+electrical+engineering+chinese",
    "https://www.google.com/search?q=site:linkedin.com/in+MIMO+OFDM+signal+processing+researcher+chinese",
    "https://www.google.com/search?q=site:linkedin.com/in+RF+engineer+mmWave+chinese+qualcomm+broadcom",
    "https://www.google.com/search?q=site:linkedin.com/in+communication+theory+researcher+IEEE+chinese",
    # EE 专业背景
    "https://www.google.com/search?q=site:linkedin.com/in+electrical+engineering+phd+Stanford+MIT+Berkeley+chinese",
    "https://www.google.com/search?q=site:linkedin.com/in+EE+major+wireless+AI+researcher+chinese",
    "https://www.google.com/search?q=site:linkedin.com/in+telecommunication+engineer+chinese+North+America",
    # 顶级公司无线团队
    "https://www.google.com/search?q=site:linkedin.com/in+wireless+engineer+NVIDIA+AI+Aerial+chinese",
    "https://www.google.com/search?q=site:linkedin.com/in+radio+frequency+engineer+Apple+Google+chinese",
    "https://www.google.com/search?q=site:linkedin.com/in+baseband+engineer+MediaTek+Huawei+chinese",
    "https://www.google.com/search?q=site:linkedin.com/in+antenna+engineer+SpaceX+Starlink+chinese",
    # 学术界无线通信研究者
    "https://www.google.com/search?q=site:linkedin.com/in+wireless+communication+professor+chinese+university",
    "https://www.google.com/search?q=site:linkedin.com/in+communication+systems+researcher+chinese+lab",
]

async def fetch_search(url, proxy, session):
    """执行搜索"""
    proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
    
    try:
        timeout = ClientTimeout(total=25)
        async with session.get(url, proxy=proxy_url, ssl=False, timeout=timeout) as resp:
            if resp.status == 200:
                return await resp.text()
            return None
    except Exception as e:
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
                        'tian', 'dong', 'yuan', 'pan', 'yu', 'lu', 'jiang', 'cai', 'jia', 'ding', 'wei',
                        'shen', 'fang', 'jiang', 'tan', 'fan', 'jin', 'qian', 'kong', 'bai', 'shao']
    
    name_lower = name.lower()
    words = name_lower.split()
    
    # 排除常见非华人姓氏
    exclude = ['nguyen', 'park', 'kim', 'choi', 'singh', 'patel', 'gupta', 'kumar', 'tran', 'le', 'pham']
    if any(e in name_lower for e in exclude):
        return False
    
    return any(s in words for s in chinese_surnames)

def evaluate_wireless_profile(profile):
    """评估无线通信/EE背景候选人"""
    name = profile.get("name", "")
    name_lower = name.lower()
    url_lower = profile.get("url", "").lower()
    
    # 无线通信关键词
    wireless_kw = ["wireless", "5g", "6g", "communication", "mimo", "ofdm", "signal", 
                   "radio", "rf", "mmwave", "antenna", "modem", "baseband", "telecom",
                   "channel", "propagation", "spectrum", "cellular", "lte", "nr", "wifi",
                   "bluetooth", "satellite", "starlink", "gnss", "gps"]
    
    # EE 专业关键词
    ee_kw = ["electrical", "engineering", "ee", "electronics", "circuit", "ic", "chip",
             "semiconductor", "hardware", "embedded", "vlsi", "analog", "digital"]
    
    # 顶级机构/公司
    top_orgs = ["stanford", "mit", "berkeley", "cmu", "ucla", "usc", "uiuc", "gatech",
                "qualcomm", "broadcom", "nvidia", "apple", "google", "meta", "intel",
                "mediatek", "huawei", "ericsson", "nokia", "samsung", "cisco"]
    
    wireless_score = sum(1 for kw in wireless_kw if kw in name_lower or kw in url_lower)
    ee_score = sum(1 for kw in ee_kw if kw in name_lower or kw in url_lower)
    org_score = sum(1 for org in top_orgs if org in url_lower)
    
    # 基础分计算
    base_score = min(wireless_score, 5) * 0.15 + min(ee_score, 3) * 0.1 + min(org_score, 2) * 0.1
    
    # 交叉奖励：同时有无线和EE背景
    cross_bonus = 0.3 if (wireless_score > 0 and ee_score > 0) else 0
    
    match_score = min(base_score + cross_bonus, 1.0)
    
    # 判断是否有无线通信背景
    has_wireless_bg = wireless_score > 0
    has_ee_bg = ee_score > 0
    
    return {
        "url": profile["url"],
        "name": name,
        "match_score": round(match_score, 2),
        "wireless_indicators": int(wireless_score),
        "ee_indicators": int(ee_score),
        "top_org_indicators": int(org_score),
        "has_wireless_bg": has_wireless_bg,
        "has_ee_bg": has_ee_bg,
        "priority": "high" if match_score >= 0.6 else "medium" if match_score >= 0.4 else "low"
    }

async def main():
    print("=" * 70)
    print("🎯 TalentIntel - 无线通信/EE 背景人才搜索")
    print("=" * 70)
    print(f"搜索目标: 20人，要求有无线通信背景或EE专业")
    print(f"搜索时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    all_candidates = []
    seen_urls = set()
    
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        for i, search_url in enumerate(SEARCH_URLS):
            proxy = proxies[i % len(proxies)]
            
            print(f"\n[{i+1}/{len(SEARCH_URLS)}] 搜索中...")
            
            html = await fetch_search(search_url, proxy, session)
            
            if html:
                profiles = extract_linkedin_profiles(html)
                print(f"  ✅ 找到 {len(profiles)} 个档案")
                
                for p in profiles:
                    if p["url"] not in seen_urls:
                        seen_urls.add(p["url"])
                        evaluated = evaluate_wireless_profile(p)
                        # 只保留有无线或EE背景的候选人
                        if evaluated and (evaluated["has_wireless_bg"] or evaluated["has_ee_bg"]):
                            all_candidates.append(evaluated)
                            print(f"  📡 {evaluated['name']} - 无线:{evaluated['wireless_indicators']} EE:{evaluated['ee_indicators']} 分:{evaluated['match_score']}")
            else:
                print(f"  ⚠️  搜索失败")
            
            await asyncio.sleep(1.5)
    
    # 按分数排序
    all_candidates.sort(key=lambda x: x["match_score"], reverse=True)
    
    # 限制目标人数
    target_candidates = all_candidates[:20]
    
    # 统计
    wireless_only = [c for c in target_candidates if c["has_wireless_bg"] and not c["has_ee_bg"]]
    ee_only = [c for c in target_candidates if c["has_ee_bg"] and not c["has_wireless_bg"]]
    both = [c for c in target_candidates if c["has_wireless_bg"] and c["has_ee_bg"]]
    high_score = [c for c in target_candidates if c["match_score"] >= 0.6]
    
    # 保存结果
    output_dir = Path("data/findings/2026-03-08")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%H%M%S")
    
    result_file = output_dir / f"wireless_ee_candidates_{timestamp}.json"
    with open(result_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "target": "wireless_communication_ee_background",
            "target_count": 20,
            "found_candidates": len(target_candidates),
            "total_scanned": len(all_candidates),
            "statistics": {
                "wireless_only": len(wireless_only),
                "ee_only": len(ee_only),
                "both_bg": len(both),
                "high_score": len(high_score)
            },
            "candidates": target_candidates
        }, f, indent=2)
    
    # 同时生成 Markdown 报告
    md_file = output_dir / f"wireless_ee_candidates_{timestamp}.md"
    with open(md_file, "w") as f:
        f.write("# 无线通信/EE 背景人才搜索报告\n\n")
        f.write(f"**搜索时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**目标**: 20人，有无线通信背景或EE专业\n\n")
        f.write("## 统计概览\n\n")
        f.write(f"- **找到候选人**: {len(target_candidates)} 人\n")
        f.write(f"- **扫描档案总数**: {len(all_candidates)} 人\n")
        f.write(f"- **纯无线背景**: {len(wireless_only)} 人\n")
        f.write(f"- **纯EE背景**: {len(ee_only)} 人\n")
        f.write(f"- **双背景**: {len(both)} 人\n")
        f.write(f"- **高分候选人 (≥0.6)**: {len(high_score)} 人\n\n")
        f.write("## 候选人列表\n\n")
        for i, c in enumerate(target_candidates, 1):
            bg_type = ""
            if c["has_wireless_bg"] and c["has_ee_bg"]:
                bg_type = "[无线+EE]"
            elif c["has_wireless_bg"]:
                bg_type = "[无线]"
            else:
                bg_type = "[EE]"
            f.write(f"### {i}. {c['name']} {bg_type}\n\n")
            f.write(f"- **匹配分数**: {c['match_score']}\n")
            f.write(f"- **LinkedIn**: {c['url']}\n")
            f.write(f"- **无线指标**: {c['wireless_indicators']}\n")
            f.write(f"- **EE指标**: {c['ee_indicators']}\n")
            f.write(f"- **优先级**: {c['priority']}\n\n")
    
    # 报告
    print("\n" + "=" * 70)
    print("📊 搜索完成")
    print(f"找到候选人: {len(target_candidates)} / 20 目标")
    print(f"扫描档案总数: {len(all_candidates)}")
    print(f"结果保存: {result_file}")
    print(f"Markdown报告: {md_file}")
    print("=" * 70)
    
    print(f"\n📈 背景分布:")
    print(f"   纯无线背景: {len(wireless_only)} 人")
    print(f"   纯EE背景: {len(ee_only)} 人")
    print(f"   双背景: {len(both)} 人")
    print(f"   高分候选人: {len(high_score)} 人")
    
    if target_candidates:
        print("\n🏆 TOP 候选人:")
        for i, c in enumerate(target_candidates[:5], 1):
            bg = "无线+EE" if c["has_wireless_bg"] and c["has_ee_bg"] else "无线" if c["has_wireless_bg"] else "EE"
            print(f"{i}. {c['name']} ({bg}) - 分数: {c['match_score']}")
    else:
        print("\n⚠️ 本次搜索未找到符合条件的候选人")

if __name__ == "__main__":
    asyncio.run(main())
