"""
Google X-Ray Search for LinkedIn Talent Discovery
通过 Google 搜索公开索引的 LinkedIn 档案，绕过平台限制

原理:
- LinkedIn 公开档案允许 Google 收录
- site:linkedin.com/in 限定搜索范围
- Boolean 语法精准定位目标人群

优势:
- 无需 LinkedIn 账号
- 无反爬风险
- 可批量获取档案链接
- 完全合法合规
"""

import asyncio
import json
import re
import urllib.parse
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import aiohttp


@dataclass
class XRaySearchConfig:
    """X-Ray 搜索配置"""
    # 目标公司
    target_companies: List[str]
    # 职位关键词
    title_keywords: List[str]
    # 技能关键词
    skill_keywords: List[str]
    # 地区
    locations: List[str]
    # 排除关键词
    exclude_keywords: List[str]


class LinkedInXRaySearcher:
    """LinkedIn X-Ray 搜索引擎"""
    
    def __init__(self):
        self.base_url = "https://www.google.com/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    def build_search_query(self, config: XRaySearchConfig) -> str:
        """
        构建 Google X-Ray 搜索查询
        
        语法示例:
        site:linkedin.com/in (华为 OR 高通 OR 爱立信) (AI工程师 OR 算法专家) (无线通信 OR 5G)
        """
        parts = ["site:linkedin.com/in"]
        
        # 公司条件
        if config.target_companies:
            companies = " OR ".join([f'"{c}"' for c in config.target_companies])
            parts.append(f"({companies})")
        
        # 职位条件
        if config.title_keywords:
            titles = " OR ".join([f'"{t}"' for t in config.title_keywords])
            parts.append(f"({titles})")
        
        # 技能条件
        if config.skill_keywords:
            skills = " OR ".join([f'"{s}"' for s in config.skill_keywords])
            parts.append(f"({skills})")
        
        # 地区条件
        if config.locations:
            locations = " OR ".join([f'"{l}"' for l in config.locations])
            parts.append(f"({locations})")
        
        # 排除条件
        for exclude in config.exclude_keywords:
            parts.append(f'-"{exclude}"')
        
        return " ".join(parts)
    
    def generate_search_urls(self, config: XRaySearchConfig, num_results: int = 100) -> List[str]:
        """
        生成多个搜索 URL（分页）
        
        Google 每页约 10 个结果，需要多次搜索获取更多
        """
        query = self.build_search_query(config)
        urls = []
        
        # Google 分页：start=0, 10, 20, 30...
        for start in range(0, min(num_results, 100), 10):
            params = {
                "q": query,
                "start": start,
                "num": 10,
                "hl": "zh-CN"  # 中文界面，可根据需要调整
            }
            url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
            urls.append(url)
        
        return urls
    
    def extract_linkedin_urls(self, html_content: str) -> List[Dict]:
        """
        从 Google 搜索结果中提取 LinkedIn 档案链接
        
        返回格式:
        [
            {
                "url": "https://www.linkedin.com/in/username/",
                "title": "姓名 - 职位",
                "snippet": "简介片段..."
            }
        ]
        """
        profiles = []
        
        # 匹配 LinkedIn 档案链接
        # Google 搜索结果中的链接格式
        pattern = r'https://[^"\s<>]*linkedin\.com/in/[^"\s<>]+'
        urls = re.findall(pattern, html_content)
        
        # 去重并清洗
        seen = set()
        for url in urls:
            # 去除追踪参数
            clean_url = re.sub(r'\?.*$', '', url)
            if clean_url not in seen and '/in/' in clean_url:
                seen.add(clean_url)
                profiles.append({
                    "url": clean_url,
                    "name": self._extract_name_from_url(clean_url),
                    "discovered_at": datetime.now().isoformat()
                })
        
        return profiles
    
    def _extract_name_from_url(self, url: str) -> str:
        """从 LinkedIn URL 中提取姓名"""
        match = re.search(r'/in/([^/\?]+)', url)
        if match:
            # 将 username 转换为可读姓名（粗略）
            username = match.group(1)
            # 替换连字符为空格，首字母大写
            name = username.replace('-', ' ').replace('_', ' ').title()
            return name
        return "Unknown"
    
    async def search(self, config: XRaySearchConfig, max_results: int = 50) -> List[Dict]:
        """
        执行 X-Ray 搜索
        
        注意：这里生成的是搜索链接，实际抓取需要处理 Google 反爬
        建议：
        1. 手动在浏览器中打开链接查看
        2. 使用代理池轮换 IP
        3. 添加延时避免触发限制
        """
        urls = self.generate_search_urls(config, max_results)
        all_profiles = []
        
        print(f"🔍 生成 {len(urls)} 个搜索链接")
        print(f"📝 搜索查询: {self.build_search_query(config)}")
        print()
        
        # 显示前3个搜索链接作为示例
        for i, url in enumerate(urls[:3], 1):
            print(f"🔗 搜索链接 {i}: {url}")
        
        print()
        print("⚠️  提示: Google 搜索有反爬限制，建议:")
        print("   1. 手动在浏览器中打开上述链接")
        print("   2. 或使用代理池 + 延时进行自动化")
        print()
        
        return urls


class TalentMiningConfig:
    """
    产业挖掘配置
    针对特定公司 + 职位 + 技能组合
    """
    
    # 目标公司：通信/AI大厂
    WIRELESS_COMPANIES = [
        "Huawei", "Qualcomm", "Ericsson", "Nokia", "Samsung",
        "NVIDIA", "Intel", "MediaTek", "ZTE", "Cisco",
        "Bell Labs", "InterDigital", "Keysight"
    ]
    
    # AI + Wireless 交叉职位
    TARGET_TITLES = [
        "AI Engineer", "Machine Learning Engineer", "Research Scientist",
        "算法工程师", "Wireless Engineer", "5G Engineer",
        "Deep Learning Engineer", "通信算法工程师", "AI Researcher"
    ]
    
    # 核心技术关键词
    SKILL_KEYWORDS = [
        "5G", "6G", "MIMO", "OFDM", "无线通信",
        "Deep Learning", "Machine Learning", "AI",
        "信道估计", "信号处理", "PHY Layer"
    ]
    
    # 目标地区
    LOCATIONS = [
        "United States", "Canada", "Singapore", "Germany",
        "Sweden", "Finland", "UK", "China"
    ]


def generate_hunting_queries() -> List[Dict]:
    """
    生成多个猎头搜索查询（不同组合）
    
    针对不同的公司-职位-技能组合，生成专门的搜索策略
    """
    queries = []
    
    # 策略1: 大厂 AI 无线工程师（美国）
    queries.append({
        "name": "北美大厂 AI+无线工程师",
        "config": XRaySearchConfig(
            target_companies=["Qualcomm", "NVIDIA", "Intel", "Samsung"],
            title_keywords=["AI Engineer", "Wireless Engineer", "Research Scientist"],
            skill_keywords=["5G", "Deep Learning", "MIMO"],
            locations=["United States", "Canada"],
            exclude_keywords=["recruiter", "HR", "sales"]
        )
    })
    
    # 策略2: 华为/中兴 通信算法专家
    queries.append({
        "name": "华系通信算法专家",
        "config": XRaySearchConfig(
            target_companies=["Huawei", "ZTE", "HiSilicon"],
            title_keywords=["算法工程师", "通信算法", "Research Engineer"],
            skill_keywords=["5G", "MIMO", "OFDM", "信道估计"],
            locations=["China", "Singapore", "Germany"],
            exclude_keywords=[]
        )
    })
    
    # 策略3: 欧洲无线通信研究机构
    queries.append({
        "name": "欧洲无线研究机构",
        "config": XRaySearchConfig(
            target_companies=["Ericsson", "Nokia", "Bell Labs", "InterDigital"],
            title_keywords=["Research Scientist", "Wireless Researcher", "AI Researcher"],
            skill_keywords=["6G", "Machine Learning", "Wireless Communication"],
            locations=["Sweden", "Finland", "Germany", "UK"],
            exclude_keywords=[]
        )
    })
    
    # 策略4: 新加坡/东南亚无线AI人才
    queries.append({
        "name": "新加坡无线AI人才",
        "config": XRaySearchConfig(
            target_companies=["Qualcomm", "MediaTek", "Huawei", "Samsung"],
            title_keywords=["Engineer", "Scientist", "Researcher"],
            skill_keywords=["AI", "5G", "Machine Learning"],
            locations=["Singapore"],
            exclude_keywords=[]
        )
    })
    
    return queries


async def main():
    """主函数：演示 X-Ray 搜索"""
    
    print("=" * 70)
    print("🎯 LinkedIn X-Ray Search - 产业人才挖掘")
    print("=" * 70)
    print()
    
    searcher = LinkedInXRaySearcher()
    
    # 获取所有搜索策略
    strategies = generate_hunting_queries()
    
    print(f"📋 已配置 {len(strategies)} 个搜索策略:\n")
    for i, strategy in enumerate(strategies, 1):
        print(f"{i}. {strategy['name']}")
    print()
    print("-" * 70)
    
    # 执行第一个策略作为演示
    demo_strategy = strategies[0]
    print(f"\n🚀 演示策略: {demo_strategy['name']}\n")
    
    urls = await searcher.search(demo_strategy['config'], max_results=30)
    
    # 保存结果
    result = {
        "strategy": demo_strategy['name'],
        "query": searcher.build_search_query(demo_strategy['config']),
        "search_urls": urls,
        "generated_at": datetime.now().isoformat()
    }
    
    output_file = f"xray_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 搜索配置已保存: {output_file}")
    print()
    print("=" * 70)
    print("下一步建议:")
    print("1. 手动在浏览器中打开上述 Google 搜索链接")
    print("2. 收集 LinkedIn 档案 URL")
    print("3. 使用 TalentIntel 数字研究员逐个深入评估")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
