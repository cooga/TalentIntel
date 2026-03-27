#!/usr/bin/env python3
"""
TalentIntel X-Ray 搜索执行器
使用 Google X-Ray 搜索 LinkedIn 公开档案
"""
import json
import time
from datetime import datetime
from pathlib import Path

print("=" * 80)
print("🌐 Google X-Ray 搜索 - 北美大厂华人人才")
print("=" * 80)
print()

# 搜索配置
searches = [
    {
        "name": "NVIDIA San Jose AI工程师",
        "url": "https://www.google.com/search?q=site%3Alinkedin.com%2Fin+%28%22NVIDIA%22%29+%28%22AI+Engineer%22+OR+%22Machine+Learning%22+OR+%22Deep+Learning%22%29+%28%22San+Jose%22+OR+%22CA%22%29",
        "company": "NVIDIA",
        "priority": "P0"
    },
    {
        "name": "Qualcomm San Diego 5G专家",
        "url": "https://www.google.com/search?q=site%3Alinkedin.com%2Fin+%28%22Qualcomm%22%29+%28%225G%22+OR+%226G%22+OR+%22Wireless%22%29+%28%22San+Diego%22+OR+%22CA%22%29",
        "company": "Qualcomm",
        "priority": "P0"
    },
    {
        "name": "SpaceX Starlink工程师",
        "url": "https://www.google.com/search?q=site%3Alinkedin.com%2Fin+%28%22SpaceX%22%29+%28%22Starlink%22+OR+%22Wireless%22+OR+%22Engineer%22%29+%28%22Hawthorne%22+OR+%22CA%22%29",
        "company": "SpaceX",
        "priority": "P0"
    },
    {
        "name": "Google AI无线通信",
        "url": "https://www.google.com/search?q=site%3Alinkedin.com%2Fin+%28%22Google%22%29+%28%22AI%22+OR+%22Wireless%22+OR+%225G%22%29+%28%22Mountain+View%22+OR+%22CA%22%29",
        "company": "Google",
        "priority": "P1"
    },
    {
        "name": "Meta AI网络连接",
        "url": "https://www.google.com/search?q=site%3Alinkedin.com%2Fin+%28%22Meta%22%29+%28%22AI%22+OR+%22Wireless%22+OR+%22Connectivity%22%29+%28%22Menlo+Park%22+OR+%22CA%22%29",
        "company": "Meta",
        "priority": "P1"
    }
]

# 华人姓氏
chinese_surnames = ['chen', 'wang', 'li', 'zhang', 'liu', 'lin', 'wu', 'zhou', 'huang', 'zhao', 'yang', 'xu', 'sun', 'zhu', 'ma', 'gao', 'guo', 'he', 'zheng', 'xie', 'han', 'tang', 'feng', 'cao', 'yuan', 'deng', 'xue', 'tian', 'pan', 'wei']

print(f"📋 搜索任务: {len(searches)} 个")
print()

# 生成搜索指南
print("=" * 80)
print("🔍 搜索执行指南")
print("=" * 80)
print()

for i, search in enumerate(searches, 1):
    print(f"【{i}】{search['name']} (优先级: {search['priority']})")
    print(f"    公司: {search['company']}")
    print(f"    URL: {search['url']}")
    print()
    print(f"    操作步骤:")
    print(f"    1. 复制上方URL到浏览器")
    print(f"    2. 查看搜索结果")
    print(f"    3. 提取 linkedin.com/in/xxx 链接")
    print(f"    4. 根据姓名筛选华人 (姓氏: {', '.join(chinese_surnames[:10])}...)")
    print(f"    5. 记录候选人信息")
    print()

# 保存搜索任务
output_dir = Path('data/xray_searches')
output_dir.mkdir(parents=True, exist_ok=True)

mission = {
    'timestamp': datetime.now().isoformat(),
    'researcher': 'Kobe Claw',
    'mission': '双轨搜索 - X-Ray 轨道',
    'searches': searches,
    'chinese_surnames': chinese_surnames,
    'instructions': {
        'step1': '访问Google搜索URL',
        'step2': '提取LinkedIn档案链接',
        'step3': '筛选华人候选人',
        'step4': '验证AI+无线背景',
        'step5': '录入人才库'
    }
}

with open(output_dir / 'xray_mission_20260322.json', 'w', encoding='utf-8') as f:
    json.dump(mission, f, ensure_ascii=False, indent=2)

print(f"✅ 搜索任务已保存: {output_dir}/xray_mission_20260322.json")
print()

print("=" * 80)
print("🎯 候选人识别标准")
print("=" * 80)
print()
print("1. 华人身份判断:")
print("   - 姓氏匹配 (Chen, Wang, Li, Zhang, Liu, Lin, Wu, Zhou等)")
print("   - 中文名或拼音名")
print("   - 教育背景(中国大学)或华人社区活动")
print()
print("2. 技术背景要求:")
print("   - AI/ML/DL 关键词")
print("   - Wireless/5G/6G/Communication 关键词")
print("   - 两者交叉优先")
print()
print("3. 目标公司:")
print("   - P0: NVIDIA, Qualcomm, SpaceX (立即联系)")
print("   - P1: Google, Meta (次要优先级)")
print()

print("=" * 80)
print("🚀 开始执行")
print("=" * 80)
print()
print("请逐个访问以下搜索链接，记录发现的候选人:")
print()
for i, search in enumerate(searches[:3], 1):
    print(f"{i}. {search['name']}")
    print(f"   {search['url']}")
    print()

print("=" * 80)
print("💡 提示")
print("=" * 80)
print()
print("- Google 可能有反爬，建议使用正常浏览速度")
print("- 每页10个结果，可翻页查看更多")
print("- 记录格式: 姓名 | 公司 | 职位 | LinkedIn URL | 是否华人")
print()
