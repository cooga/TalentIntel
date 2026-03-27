"""
Google X-Ray Search 批量链接生成器 + 自动化评估

工作流程:
1. 生成多个 Google X-Ray 搜索链接
2. 用户使用浏览器打开这些链接
3. 使用 Linkclump 或其他工具批量复制 LinkedIn 链接
4. 将链接粘贴到本工具，自动批量评估
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import urllib.parse
import webbrowser


class XRayLinkGenerator:
    """Google X-Ray 搜索链接生成器"""
    
    def __init__(self):
        self.base_url = "https://www.google.com/search"
    
    def build_query(
        self,
        companies: List[str],
        titles: List[str],
        skills: List[str],
        locations: List[str],
        exclude: List[str] = None
    ) -> str:
        """构建搜索查询"""
        parts = ["site:linkedin.com/in"]
        
        if companies:
            companies_q = " OR ".join([f'"{c}"' for c in companies])
            parts.append(f"({companies_q})")
        
        if titles:
            titles_q = " OR ".join([f'"{t}"' for t in titles])
            parts.append(f"({titles_q})")
        
        if skills:
            skills_q = " OR ".join([f'"{s}"' for s in skills])
            parts.append(f"({skills_q})")
        
        if locations:
            locations_q = " OR ".join([f'"{l}"' for l in locations])
            parts.append(f"({locations_q})")
        
        if exclude:
            for ex in exclude:
                parts.append(f'-"{ex}"')
        
        return " ".join(parts)
    
    def generate_paginated_links(
        self,
        query: str,
        num_pages: int = 5
    ) -> List[Dict]:
        """生成分页搜索链接"""
        links = []
        
        for page in range(num_pages):
            start = page * 10
            params = {
                "q": query,
                "start": start,
                "num": 10,
            }
            url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
            
            links.append({
                "page": page + 1,
                "url": url,
                "range": f"{start+1}-{start+10}",
            })
        
        return links


class TalentDiscoveryPipeline:
    """人才发现流程管理"""
    
    # 预配置的搜索策略
    STRATEGIES = {
        "na_ai_wireless": {
            "name": "北美 AI+无线工程师",
            "companies": ["Qualcomm", "NVIDIA", "Intel", "Samsung", "Apple", "Meta"],
            "titles": ["AI Engineer", "Wireless Engineer", "Research Scientist", "ML Engineer"],
            "skills": ["5G", "Deep Learning", "MIMO", "Wireless Communication"],
            "locations": ["United States", "Canada"],
            "exclude": ["recruiter", "HR", "sales"],
        },
        "china_wireless": {
            "name": "华系通信算法专家",
            "companies": ["Huawei", "ZTE", "HiSilicon", "OPPO", "vivo", "Xiaomi"],
            "titles": ["算法工程师", "通信算法", "Research Engineer", "Senior Engineer"],
            "skills": ["5G", "MIMO", "OFDM", "信道估计", "信号处理"],
            "locations": ["China", "Singapore"],
            "exclude": [],
        },
        "eu_research": {
            "name": "欧洲无线研究机构",
            "companies": ["Ericsson", "Nokia", "Bell Labs", "InterDigital", "Keysight"],
            "titles": ["Research Scientist", "Wireless Researcher", "Principal Engineer"],
            "skills": ["6G", "Machine Learning", "Wireless Communication", "mmWave"],
            "locations": ["Sweden", "Finland", "Germany", "UK", "France"],
            "exclude": [],
        },
        "apac_talent": {
            "name": "亚太无线AI人才",
            "companies": ["MediaTek", "Samsung", "Sony", "NEC", "NTT"],
            "titles": ["Engineer", "Scientist", "Researcher", "Developer"],
            "skills": ["AI", "5G", "Machine Learning", "Communication"],
            "locations": ["Singapore", "Japan", "South Korea", "Australia"],
            "exclude": [],
        },
    }
    
    def __init__(self, output_dir: str = "data/xray_campaigns"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.link_gen = XRayLinkGenerator()
    
    def generate_all_strategies(self) -> Dict:
        """生成所有策略的搜索链接"""
        results = {}
        
        for strategy_id, config in self.STRATEGIES.items():
            print(f"\n🎯 策略: {config['name']}")
            
            # 构建查询
            query = self.link_gen.build_query(
                companies=config["companies"],
                titles=config["titles"],
                skills=config["skills"],
                locations=config["locations"],
                exclude=config.get("exclude", []),
            )
            
            # 生成链接
            links = self.link_gen.generate_paginated_links(query, num_pages=5)
            
            results[strategy_id] = {
                "name": config["name"],
                "query": query,
                "links": links,
            }
            
            print(f"   查询: {query[:80]}...")
            print(f"   生成 {len(links)} 个搜索链接")
        
        return results
    
    def save_campaign(self, results: Dict, campaign_name: str = None):
        """保存营销活动"""
        if not campaign_name:
            campaign_name = f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        output_file = self.output_dir / f"{campaign_name}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "campaign_name": campaign_name,
                "created_at": datetime.now().isoformat(),
                "strategies": results,
                "total_links": sum(len(s["links"]) for s in results.values()),
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 营销活动已保存: {output_file}")
        return output_file
    
    def open_links_batch(self, results: Dict, strategy_id: str = None, max_links: int = 3):
        """批量打开链接（浏览器）"""
        if strategy_id and strategy_id in results:
            strategies = {strategy_id: results[strategy_id]}
        else:
            strategies = results
        
        opened = 0
        for sid, strategy in strategies.items():
            print(f"\n🚀 打开策略: {strategy['name']}")
            
            for link in strategy["links"][:max_links]:
                if opened >= max_links:
                    break
                
                print(f"   打开: 第 {link['page']} 页")
                webbrowser.open(link["url"])
                opened += 1
                
                # 延时避免浏览器过载
                import time
                time.sleep(1)
        
        print(f"\n✅ 已打开 {opened} 个链接")
        print("\n💡 提示: 使用 Linkclump 或 Multi-Link Paste 浏览器插件批量提取 LinkedIn 链接")
    
    def generate_html_report(self, results: Dict, output_file: str = None):
        """生成 HTML 报告（方便点击）"""
        if not output_file:
            output_file = self.output_dir / f"xray_links_{datetime.now().strftime('%Y%m%d')}.html"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TalentIntel X-Ray Search Links</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #0077b5; padding-bottom: 10px; }}
        h2 {{ color: #0077b5; margin-top: 30px; }}
        .strategy {{ background: #f5f5f5; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .query {{ background: #fff; padding: 10px; border-left: 3px solid #0077b5; font-family: monospace; font-size: 12px; word-break: break-all; }}
        .links {{ margin-top: 10px; }}
        .link {{ display: inline-block; margin: 5px; padding: 8px 15px; background: #0077b5; color: white; text-decoration: none; border-radius: 4px; font-size: 14px; }}
        .link:hover {{ background: #005885; }}
        .tips {{ background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .tips h3 {{ margin-top: 0; color: #856404; }}
    </style>
</head>
<body>
    <h1>🎯 TalentIntel X-Ray Search Links</h1>
    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="tips">
        <h3>📖 使用说明</h3>
        <ol>
            <li>点击下方的搜索链接，在浏览器中打开 Google 搜索结果</li>
            <li>安装浏览器插件: <a href="https://chrome.google.com/webstore/detail/linkclump/gpmkpgdbdhciadajoafejkkbpbcfjmfg" target="_blank">Linkclump (Chrome)</a> 或 <a href="https://addons.mozilla.org/en-US/firefox/addon/multilinkpaste/" target="_blank">Multi-Link Paste (Firefox)</a></li>
            <li>框选搜索结果中的所有 LinkedIn 链接，批量复制</li>
            <li>将链接粘贴到 TalentIntel 评估工具中进行批量分析</li>
        </ol>
    </div>
"""
        
        for sid, strategy in results.items():
            html_content += f"""
    <div class="strategy">
        <h2>{strategy['name']}</h2>
        <div class="query">{strategy['query']}</div>
        <div class="links">
"""
            for link in strategy["links"]:
                html_content += f'            <a class="link" href="{link["url"]}" target="_blank">第 {link["page"]} 页 ({link["range"]})</a>\n'
            
            html_content += "        </div>\n    </div>\n"
        
        html_content += """
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n📄 HTML 报告已生成: {output_file}")
        return output_file


def main():
    """主函数"""
    print("=" * 70)
    print("🎯 TalentIntel X-Ray Search - 批量链接生成器")
    print("=" * 70)
    
    pipeline = TalentDiscoveryPipeline()
    
    # 生成所有策略
    print("\n📋 正在生成搜索策略...")
    results = pipeline.generate_all_strategies()
    
    # 保存配置
    campaign_file = pipeline.save_campaign(results)
    
    # 生成 HTML 报告
    html_file = pipeline.generate_html_report(results)
    
    # 询问是否打开链接
    print("\n" + "=" * 70)
    print("✅ 生成完成!")
    print(f"   JSON 配置: {campaign_file}")
    print(f"   HTML 报告: {html_file}")
    print("=" * 70)
    
    print("\n🚀 下一步:")
    print("   1. 用浏览器打开 HTML 报告")
    print("   2. 点击搜索链接查看 Google 结果")
    print("   3. 安装 Linkclump 插件批量提取 LinkedIn 链接")
    print("   4. 使用 scripts/batch_evaluate.py 批量评估")
    
    # 可选：自动打开 HTML
    try:
        response = input("\n是否现在打开 HTML 报告? (y/n): ").strip().lower()
        if response == 'y':
            webbrowser.open(f"file://{html_file.absolute()}")
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
