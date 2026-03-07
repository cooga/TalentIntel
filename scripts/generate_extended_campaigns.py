#!/usr/bin/env python3
"""
多策略 XRay 搜索链接生成器
生成大量针对不同关键词组合的搜索链接
"""

import json
import urllib.parse
from datetime import datetime
from pathlib import Path

# 扩展搜索策略 - 多关键词组合
EXTENDED_STRATEGIES = [
    # 策略组1: ML + Wireless 组合
    {
        "id": "ml_wireless_us",
        "name": "北美 ML+Wireless 人才",
        "companies": ["Qualcomm", "NVIDIA", "Intel", "Samsung", "Apple", "Meta", "Google"],
        "titles": ["Machine Learning Engineer", "Wireless Engineer", "AI Researcher", "Research Scientist"],
        "skills": ["machine learning", "wireless communication", "deep learning", "5G"],
        "locations": ["United States", "Canada"],
    },
    {
        "id": "ai_5g_engineer",
        "name": "AI+5G 工程师",
        "companies": ["Huawei", "Ericsson", "Nokia", "ZTE", "Cisco"],
        "titles": ["AI Engineer", "5G Engineer", "Algorithm Engineer", "Research Engineer"],
        "skills": ["AI", "5G", "deep learning", "MIMO", "OFDM"],
        "locations": ["China", "Singapore", "United States"],
    },
    {
        "id": "wireless_researcher_eu",
        "name": "欧洲无线通信研究员",
        "companies": ["Ericsson", "Nokia", "Bell Labs", "InterDigital", "Keysight", "Siemens"],
        "titles": ["Research Scientist", "Wireless Researcher", "Principal Engineer"],
        "skills": ["wireless communication", "6G", "machine learning", "signal processing"],
        "locations": ["Sweden", "Finland", "Germany", "UK", "France", "Netherlands"],
    },
    {
        "id": "mimo_dl_expert",
        "name": "MIMO+深度学习专家",
        "companies": ["Qualcomm", "Samsung", "Huawei", "MediaTek", "Intel"],
        "titles": ["Engineer", "Scientist", "Researcher", "Architect"],
        "skills": ["MIMO", "deep learning", "neural network", "channel estimation"],
        "locations": ["United States", "South Korea", "China", "Taiwan"],
    },
    {
        "id": "signal_processing_ml",
        "name": "信号处理+机器学习",
        "companies": ["Qualcomm", "Apple", "Broadcom", "Intel", "Texas Instruments"],
        "titles": ["Signal Processing Engineer", "ML Engineer", "Algorithm Developer"],
        "skills": ["signal processing", "machine learning", "wireless", "PHY layer"],
        "locations": ["United States", "Canada", "UK"],
    },
    # 策略组2: 学术研究机构
    {
        "id": "academic_researcher",
        "name": "学术机构无线AI研究员",
        "companies": ["MIT", "Stanford", "Berkeley", "CMU", "Caltech", "ETH Zurich", "Imperial College"],
        "titles": ["PhD", "Postdoc", "Researcher", "Professor", "Fellow"],
        "skills": ["wireless", "AI", "machine learning", "communication"],
        "locations": ["United States", "Switzerland", "UK", "Germany"],
    },
    {
        "id": "wireless_phd",
        "name": "无线通信博士人才",
        "companies": ["Stanford", "MIT", "UC Berkeley", "Georgia Tech", "Purdue", "UIUC"],
        "titles": ["PhD Candidate", "PhD Student", "Research Assistant"],
        "skills": ["wireless communication", "5G", "6G", "machine learning", "MIMO"],
        "locations": ["United States", "Canada"],
    },
    # 策略组3: 亚太地区
    {
        "id": "apac_wireless_ai",
        "name": "亚太无线AI人才",
        "companies": ["MediaTek", "Samsung", "Sony", "Huawei", "NEC", "NTT", "Rakuten"],
        "titles": ["Engineer", "Scientist", "Researcher", "Developer"],
        "skills": ["AI", "5G", "machine learning", "wireless"],
        "locations": ["Singapore", "Japan", "South Korea", "Australia", "Taiwan"],
    },
    {
        "id": "singapore_talent",
        "name": "新加坡无线通信人才",
        "companies": ["Qualcomm", "MediaTek", "Huawei", "Ericsson", "Nokia", "Singtel"],
        "titles": ["Engineer", "Researcher", "Scientist", "Architect"],
        "skills": ["wireless communication", "5G", "AI", "deep learning"],
        "locations": ["Singapore"],
    },
    # 策略组4: 特定技术方向
    {
        "id": "federated_learning",
        "name": "联邦学习+无线",
        "companies": ["Google", "Apple", "Qualcomm", "Samsung", "Huawei"],
        "titles": ["Research Scientist", "ML Engineer", "AI Researcher"],
        "skills": ["federated learning", "wireless", "edge computing", "distributed ML"],
        "locations": ["United States", "Switzerland", "UK"],
    },
    {
        "id": "beamforming_dl",
        "name": "波束成形+深度学习",
        "companies": ["Qualcomm", "Samsung", "Huawei", "Ericsson", "Nokia"],
        "titles": ["Engineer", "Scientist", "Researcher"],
        "skills": ["beamforming", "deep learning", "mmWave", "massive MIMO"],
        "locations": ["United States", "South Korea", "Sweden", "Finland"],
    },
    {
        "id": "channel_estimation",
        "name": "信道估计+AI",
        "companies": ["Qualcomm", "Huawei", "Samsung", "MediaTek", "Intel"],
        "titles": ["Algorithm Engineer", "Research Engineer", "Scientist"],
        "skills": ["channel estimation", "machine learning", "deep learning", "OFDM"],
        "locations": ["United States", "China", "South Korea"],
    },
    {
        "id": "semantic_communication",
        "name": "语义通信专家",
        "companies": ["Huawei", "Qualcomm", "Samsung", "Nokia", "Ericsson"],
        "titles": ["Researcher", "Scientist", "Engineer"],
        "skills": ["semantic communication", "deep learning", "6G", "AI"],
        "locations": ["China", "United States", "Europe"],
    },
    # 策略组5: 工业界专家
    {
        "id": "senior_wireless_expert",
        "name": "资深无线通信专家",
        "companies": ["Qualcomm", "Huawei", "Ericsson", "Nokia", "Samsung", "Apple"],
        "titles": ["Senior Engineer", "Staff Engineer", "Principal Engineer", "Distinguished Engineer"],
        "skills": ["wireless communication", "5G", "system design", "architecture"],
        "locations": ["United States", "Sweden", "Finland", "China"],
    },
    {
        "id": "phy_layer_expert",
        "name": "物理层算法专家",
        "companies": ["Qualcomm", "MediaTek", "Huawei", "Intel", "Samsung"],
        "titles": ["PHY Engineer", "Algorithm Engineer", "System Engineer"],
        "skills": ["PHY layer", "signal processing", "modulation", "coding"],
        "locations": ["United States", "Taiwan", "China", "South Korea"],
    },
]


def build_search_query(strategy: dict) -> str:
    """构建搜索查询"""
    parts = ["site:linkedin.com/in"]
    
    if strategy.get("companies"):
        companies_q = " OR ".join([f'"{c}"' for c in strategy["companies"]])
        parts.append(f"({companies_q})")
    
    if strategy.get("titles"):
        titles_q = " OR ".join([f'"{t}"' for t in strategy["titles"]])
        parts.append(f"({titles_q})")
    
    if strategy.get("skills"):
        skills_q = " OR ".join([f'"{s}"' for s in strategy["skills"]])
        parts.append(f"({skills_q})")
    
    if strategy.get("locations"):
        locations_q = " OR ".join([f'"{l}"' for l in strategy["locations"]])
        parts.append(f"({locations_q})")
    
    return " ".join(parts)


def generate_paginated_links(query: str, num_pages: int = 5) -> list:
    """生成分页链接"""
    base_url = "https://www.google.com/search"
    links = []
    
    for page in range(num_pages):
        start = page * 10
        params = {
            "q": query,
            "start": start,
            "num": 10,
        }
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        links.append({
            "page": page + 1,
            "url": url,
            "range": f"{start+1}-{start+10}",
        })
    
    return links


def generate_html_report(all_strategies: list, output_file: Path):
    """生成 HTML 报告"""
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TalentIntel Extended X-Ray Search - 50 Candidates Target</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1400px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; border-bottom: 3px solid #0077b5; padding-bottom: 10px; }}
        h2 {{ color: #0077b5; margin-top: 30px; background: white; padding: 10px; border-radius: 8px; }}
        .strategy {{ background: white; padding: 15px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .query {{ background: #f8f9fa; padding: 10px; border-left: 3px solid #0077b5; font-family: monospace; font-size: 11px; word-break: break-all; margin: 10px 0; }}
        .links {{ margin-top: 10px; display: flex; flex-wrap: wrap; gap: 5px; }}
        .link {{ display: inline-block; padding: 6px 12px; background: #0077b5; color: white; text-decoration: none; border-radius: 4px; font-size: 12px; }}
        .link:hover {{ background: #005885; }}
        .tips {{ background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #ffc107; }}
        .tips h3 {{ margin-top: 0; color: #856404; }}
        .stats {{ background: #d4edda; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 15px; }}
    </style>
</head>
<body>
    <h1>🎯 TalentIntel Extended X-Ray Search</h1>
    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 目标: 50个高分候选人</p>
    
    <div class="stats">
        <h3>📊 统计</h3>
        <p>搜索策略数: {len(all_strategies)}</p>
        <p>总搜索链接: {len(all_strategies) * 5}</p>
        <p>预计可覆盖候选人: 500+</p>
    </div>
    
    <div class="tips">
        <h3>📖 批量操作指南</h3>
        <ol>
            <li>安装浏览器插件: <a href="https://chrome.google.com/webstore/detail/linkclump/gpmkpgdbdhciadajoafejkkbpbcfjmfg" target="_blank">Linkclump (Chrome)</a></li>
            <li>点击每个策略的搜索链接，在浏览器中打开 Google 结果</li>
            <li>使用 Linkclump 框选并复制所有 LinkedIn 链接</li>
            <li>将链接保存到文本文件，每行一个 URL</li>
            <li>运行: <code>python3 scripts/batch_evaluate.py links.txt</code></li>
        </ol>
    </div>
    
    <div class="grid">
"""
    
    for strategy in all_strategies:
        html_content += f"""
    <div class="strategy">
        <h3>{strategy['name']}</h3>
        <div class="query">{strategy['query']}</div>
        <div class="links">
"""
        for link in strategy['links']:
            html_content += f'            <a class="link" href="{link["url"]}" target="_blank">第{link["page"]}页</a>\n'
        
        html_content += "        </div>\n    </div>\n"
    
    html_content += """
    </div>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"📄 HTML 报告已生成: {output_file}")
    return output_file


def main():
    """主函数"""
    print("=" * 70)
    print("🎯 Extended X-Ray Search - 扩展搜索策略生成")
    print("=" * 70)
    
    output_dir = Path("data/xray_campaigns")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 处理所有策略
    all_strategies = []
    
    print(f"\n📋 正在生成 {len(EXTENDED_STRATEGIES)} 个搜索策略...\n")
    
    for strategy in EXTENDED_STRATEGIES:
        print(f"🔍 {strategy['name']}")
        
        query = build_search_query(strategy)
        links = generate_paginated_links(query, num_pages=5)
        
        all_strategies.append({
            "id": strategy['id'],
            "name": strategy['name'],
            "query": query,
            "links": links,
        })
        
        print(f"   查询: {query[:70]}...")
        print(f"   链接: {len(links)} 个")
    
    # 保存 JSON 配置
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_file = output_dir / f"extended_campaign_{timestamp}.json"
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "campaign_name": "extended_50_candidates",
            "created_at": datetime.now().isoformat(),
            "target": 50,
            "strategies": all_strategies,
            "total_links": len(all_strategies) * 5,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 JSON 配置已保存: {json_file}")
    
    # 生成 HTML 报告
    html_file = output_dir / f"extended_links_{timestamp}.html"
    generate_html_report(all_strategies, html_file)
    
    print("\n" + "=" * 70)
    print("✅ 扩展搜索策略生成完成!")
    print(f"   总策略数: {len(all_strategies)}")
    print(f"   总搜索链接: {len(all_strategies) * 5}")
    print(f"   JSON: {json_file}")
    print(f"   HTML: {html_file}")
    print("=" * 70)
    
    print("\n🚀 下一步操作:")
    print("   1. 用浏览器打开 HTML 报告")
    print("   2. 逐个点击搜索链接，批量提取 LinkedIn 档案 URL")
    print("   3. 使用 batch_evaluate.py 批量评估")
    print("   4. 目标: 收集50个≥0.7分的高分候选人")


if __name__ == "__main__":
    main()
