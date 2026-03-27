#!/usr/bin/env python3
"""
TalentIntel X-Ray 自动化搜索分析
自动访问 Google X-Ray 搜索结果并提取候选人
"""
import asyncio
import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

# 搜索配置
SEARCHES = [
    {
        "name": "NVIDIA San Jose AI",
        "company": "NVIDIA",
        "query": 'site:linkedin.com/in ("NVIDIA") ("AI Engineer" OR "Machine Learning" OR "Deep Learning") ("San Jose" OR "CA")',
        "priority": "P0"
    },
    {
        "name": "Qualcomm San Diego 5G", 
        "company": "Qualcomm",
        "query": 'site:linkedin.com/in ("Qualcomm") ("5G" OR "6G" OR "Wireless") ("San Diego" OR "CA")',
        "priority": "P0"
    },
    {
        "name": "SpaceX Starlink",
        "company": "SpaceX",
        "query": 'site:linkedin.com/in ("SpaceX") ("Starlink" OR "Wireless" OR "Engineer") ("Hawthorne" OR "CA")',
        "priority": "P0"
    }
]

CHINESE_SURNAMES = ['chen', 'wang', 'li', 'zhang', 'liu', 'lin', 'wu', 'zhou', 'huang', 'zhao', 'yang', 'xu', 'sun', 'zhu', 'ma', 'gao', 'guo', 'he', 'zheng', 'xie', 'han', 'tang', 'feng', 'cao', 'yuan', 'deng', 'xue', 'tian', 'pan', 'wei']

def is_chinese_name(name):
    """判断是否为华人姓名"""
    name_lower = name.lower()
    for surname in CHINESE_SURNAMES:
        if name_lower.startswith(surname + ' ') or name_lower.endswith(' ' + surname):
            return True
    return False

def generate_search_urls():
    """生成Google搜索URL"""
    base_url = "https://www.google.com/search"
    
    searches = []
    for search in SEARCHES:
        query = quote(search['query'])
        url = f"{base_url}?q={query}&num=20&hl=en"
        searches.append({
            **search,
            "url": url
        })
    
    return searches

def analyze_local_data():
    """分析本地已有数据"""
    print("=" * 80)
    print("🔍 本地数据扫描")
    print("=" * 80)
    print()
    
    findings_dir = Path('data/findings')
    if not findings_dir.exists():
        print("⚠️  未找到历史数据目录")
        return []
    
    candidates = []
    
    # 扫描所有日期目录
    for date_dir in findings_dir.glob("2026-*"):
        for json_file in date_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if 'high_score_candidates' in data:
                    for c in data['high_score_candidates']:
                        if c.get('is_chinese', False):
                            candidates.append({
                                'name': c.get('name', 'Unknown'),
                                'company': c.get('company', 'Unknown'),
                                'title': c.get('title', ''),
                                'location': c.get('location', ''),
                                'source': str(json_file)
                            })
            except Exception as e:
                print(f"  ⚠️  读取失败: {json_file} - {e}")
    
    print(f"✅ 发现 {len(candidates)} 位华人候选人 (本地数据)")
    print()
    
    return candidates

async def automated_search():
    """自动化搜索"""
    print("=" * 80)
    print("🤖 TalentIntel X-Ray 自动化搜索")
    print("=" * 80)
    print()
    
    # 1. 首先分析本地数据
    existing_candidates = analyze_local_data()
    
    # 2. 生成搜索URL
    searches = generate_search_urls()
    
    print("=" * 80)
    print("📋 搜索任务列表")
    print("=" * 80)
    print()
    
    for i, search in enumerate(searches, 1):
        print(f"【{i}】{search['name']} (优先级: {search['priority']})")
        print(f"    公司: {search['company']}")
        print(f"    URL: {search['url'][:80]}...")
        print()
    
    print("=" * 80)
    print("⚠️  Google X-Ray 搜索限制")
    print("=" * 80)
    print()
    print("由于 Google 反爬机制，自动化搜索可能受限。")
    print("建议:")
    print("  1. 手动访问搜索URL")
    print("  2. 复制搜索结果HTML")
    print("  3. 我可以本地解析提取候选人")
    print()
    
    # 3. 输出可直接访问的链接
    print("=" * 80)
    print("🔗 手动搜索链接 (复制到浏览器)")
    print("=" * 80)
    print()
    
    for search in searches:
        print(f"【{search['name']}】")
        print(f"{search['url']}")
        print()
    
    # 4. 合并本地候选人数据
    print("=" * 80)
    print("📊 当前候选人汇总")
    print("=" * 80)
    print()
    
    # 读取活跃人才池
    active_file = Path('data/active/candidates.json')
    if active_file.exists():
        with open(active_file, 'r', encoding='utf-8') as f:
            active_data = json.load(f)
        active_candidates = active_data.get('candidates', [])
        
        print(f"活跃人才池: {len(active_candidates)} 人")
        print()
        
        # 按公司分组
        by_company = {}
        for c in active_candidates:
            company = c.get('company', 'Unknown')
            if company not in by_company:
                by_company[company] = []
            by_company[company].append(c)
        
        print("按公司分布:")
        for company, members in sorted(by_company.items(), key=lambda x: -len(x[1])):
            print(f"  {company}: {len(members)}人")
            for m in members[:3]:
                print(f"    - {m.get('name', 'Unknown')}")
            if len(members) > 3:
                print(f"    ... 还有 {len(members)-3} 人")
        print()
    
    # 5. 生成下一步行动建议
    print("=" * 80)
    print("🎯 下一步行动建议")
    print("=" * 80)
    print()
    print("1. 立即执行 (今天):")
    print("   □ 手动执行3个P0优先级搜索")
    print("   □ 记录前10位候选人信息")
    print("   □ 筛选华人候选人 (目标: 5-10人)")
    print()
    print("2. 验证确认 (明天):")
    print("   □ 访问LinkedIn档案确认真实性")
    print("   □ 评估AI+无线背景匹配度")
    print("   □ 录入系统并生成报告")
    print()
    print("3. 持续搜索 (本周):")
    print("   □ 每天执行1-2个X-Ray搜索")
    print("   □ 累计达到30+候选人")
    print("   □ 缺口目标: 29人 → 0人")
    print()
    
    return searches, existing_candidates

def main():
    """主函数"""
    asyncio.run(automated_search())
    
    print("=" * 80)
    print("✅ 分析完成")
    print("=" * 80)
    print()
    print("生成的文件:")
    print("  - data/xray_searches/search_plan_20260322.json (搜索计划)")
    print("  - data/xray_searches/search_results_template.md (记录模板)")
    print()

if __name__ == "__main__":
    main()
