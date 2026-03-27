#!/usr/bin/env python3
"""
学术渠道人才搜索
通过 Google Scholar 搜索 AI+无线通信领域的华人研究者
无需 CAPTCHA，直接获取论文作者信息
"""
import json
from datetime import datetime
from pathlib import Path

print("=" * 80)
print("📚 学术渠道人才搜索 - Google Scholar")
print("=" * 80)
print()

# 搜索配置
search_queries = [
    {
        "name": "无线通信 + 深度学习",
        "query": "wireless communication deep learning",
        "keywords": ["wireless", "deep learning", "neural network", "5G", "MIMO"]
    },
    {
        "name": "AI + 信号处理",
        "query": "machine learning signal processing",
        "keywords": ["machine learning", "signal processing", "OFDM", "beamforming"]
    },
    {
        "name": "联邦学习 + 无线",
        "query": "federated learning wireless",
        "keywords": ["federated learning", "wireless", "edge computing", "IoT"]
    },
    {
        "name": "语义通信 + AI",
        "query": "semantic communication AI",
        "keywords": ["semantic communication", "deep learning", "6G"]
    }
]

target_conferences = [
    "IEEE ICC", "IEEE Globecom", "IEEE INFOCOM", 
    "MobiCom", "MobiHoc", "NeurIPS", "ICML", "CVPR"
]

print("📋 搜索策略")
print("=" * 80)
print()

for i, search in enumerate(search_queries, 1):
    print(f"【{i}】{search['name']}")
    print(f"    Google Scholar: https://scholar.google.com/scholar?q={search['query'].replace(' ', '+')}")
    print(f"    关键词: {', '.join(search['keywords'])}")
    print()

print("=" * 80)
print("🎯 目标会议")
print("=" * 80)
print()
print(', '.join(target_conferences))
print()

print("=" * 80)
print("🔍 作者识别策略")
print("=" * 80)
print()
print("1. 搜索论文 (Google Scholar)")
print("2. 查看作者列表")
print("3. 根据姓名识别华人 (Chen, Wang, Li, Zhang, Liu等)")
print("4. 查看作者单位 (目标公司: NVIDIA, Google, Qualcomm等)")
print("5. 获取邮箱 (部分论文提供)")
print()

# 生成可直接访问的链接
print("=" * 80)
print("🔗 学术搜索链接 (复制到浏览器)")
print("=" * 80)
print()

for search in search_queries:
    url = f"https://scholar.google.com/scholar?q={search['query'].replace(' ', '+')}&hl=en&as_sdt=0%2C5&as_ylo=2023"
    print(f"【{search['name']}】")
    print(url)
    print()

# 保存搜索计划
output_dir = Path('data/academic_search')
output_dir.mkdir(parents=True, exist_ok=True)

plan = {
    'timestamp': datetime.now().isoformat(),
    'strategy': '学术渠道挖掘',
    'searches': search_queries,
    'target_conferences': target_conferences,
    'chinese_surnames': ['Chen', 'Wang', 'Li', 'Zhang', 'Liu', 'Lin', 'Wu', 'Zhou', 'Huang', 'Zhao', 'Yang', 'Xu', 'Sun', 'Zhu', 'Ma', 'Gao', 'Guo', 'He', 'Zheng', 'Xie', 'Han', 'Tang', 'Feng', 'Cao', 'Yuan', 'Deng', 'Xue', 'Tian', 'Pan', 'Wei'],
    'target_companies': ['NVIDIA', 'Google', 'Meta', 'Qualcomm', 'Intel', 'Apple', 'Samsung', 'Ericsson', 'Nokia'],
    'instructions': {
        'step1': '访问 Google Scholar 搜索链接',
        'step2': '筛选 2023-2024 年论文',
        'step3': '查看作者姓名识别华人',
        'step4': '检查作者单位是否为目标公司',
        'step5': '记录作者信息和联系方式'
    }
}

with open(output_dir / 'academic_search_plan.json', 'w', encoding='utf-8') as f:
    json.dump(plan, f, ensure_ascii=False, indent=2)

print(f"✅ 搜索计划已保存: {output_dir}/academic_search_plan.json")
print()

print("=" * 80)
print("💡 优势")
print("=" * 80)
print()
print("✅ 无需 CAPTCHA 验证")
print("✅ 信息真实可靠 (论文可查)")
print("✅ 可直接获取邮箱 (部分论文)")
print("✅ 适合发现学术界转工业界人才")
print("✅ 可以追踪特定研究领域")
print()

print("=" * 80)
print("📊 预期成果")
print("=" * 80)
print()
print("每个搜索可发现: 5-10 位华人研究者")
print("总计预期: 20-40 位潜在候选人")
print()
