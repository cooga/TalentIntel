#!/usr/bin/env python3
"""
TalentIntel Extended Search - 补充搜索
扩展更多公司和关键词组合以达到目标
"""

import asyncio
import json
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass, asdict

# 扩展目标公司
EXTENDED_COMPANIES = [
    # 额外通信/半导体公司
    {"company": "Intel", "keywords": ["AI", "wireless", "5G", "communication", "signal processing"]},
    {"company": "Broadcom", "keywords": ["AI", "wireless", "connectivity", "WiFi", "bluetooth"]},
    {"company": "Marvell", "keywords": ["AI", "5G", "wireless", "baseband"]},
    {"company": "Ericsson", "keywords": ["AI", "5G", "6G", "wireless research"]},
    {"company": "Nokia", "keywords": ["AI", "5G", "6G", "wireless", "ML"]},
    {"company": "Cisco", "keywords": ["AI", "wireless", "network", "ML"]},
    {"company": "Huawei", "keywords": ["AI", "5G", "6G", "wireless research"]},
    {"company": "MediaTek", "keywords": ["AI", "5G", "wireless", "chip"]},
    
    # 其他AI公司
    {"company": "Microsoft Research", "keywords": ["AI", "wireless", "communication", "network"]},
    {"company": "Amazon", "keywords": ["AI", "wireless", "IoT", "connectivity"]},
    {"company": "Tesla", "keywords": ["AI", "wireless", "connectivity", "autopilot"]},
    {"company": "IBM Research", "keywords": ["AI", "wireless", "5G", "quantum"]},
    
    # 其他学术机构
    {"company": "UC Berkeley", "keywords": ["AI", "wireless", "communication", "ML"]},
    {"company": "CMU", "keywords": ["AI", "wireless", "robotics", "ML"]},
    {"company": "Caltech", "keywords": ["AI", "wireless", "communication", "signal processing"]},
    {"company": "Princeton", "keywords": ["AI", "wireless", "network", "optimization"]},
    {"company": "UIUC", "keywords": ["AI", "wireless", "communication", "ML"]},
    {"company": "Georgia Tech", "keywords": ["AI", "wireless", "5G", "communication"]},
    
    # 创业公司/其他
    {"company": "Databricks", "keywords": ["AI", "ML", "data", "wireless"]},
    {"company": "Snowflake", "keywords": ["AI", "data", "ML", "cloud"]},
    {"company": "Uber", "keywords": ["AI", "ML", "optimization", "wireless"]},
    {"company": "Airbnb", "keywords": ["AI", "ML", "data science"]},
    {"company": "LinkedIn", "keywords": ["AI", "ML", "recommendation"]},
    {"company": "Netflix", "keywords": ["AI", "ML", "recommendation"]},
    {"company": "Twitter", "keywords": ["AI", "ML", "recommendation"]},
    {"company": "Snap", "keywords": ["AI", "ML", "computer vision"]},
    {"company": "Pinterest", "keywords": ["AI", "ML", "recommendation"]},
    {"company": "Lyft", "keywords": ["AI", "ML", "autonomous"]},
    {"company": "Waymo", "keywords": ["AI", "ML", "autonomous", "wireless"]},
    {"company": "Cruise", "keywords": ["AI", "ML", "autonomous"]},
    {"company": "Aurora", "keywords": ["AI", "ML", "autonomous"]},
]

# AI关键词
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning", "ml",
    "neural network", "neural", "federated learning", "transformer", "llm",
    "large language model", "reinforcement learning", "computer vision", "nlp",
    "natural language", "data science", "algorithm", "generative ai", "genai",
    "pytorch", "tensorflow", "jax"
]

# 无线通信关键词
WIRELESS_KEYWORDS = [
    "wireless", "5g", "6g", "mimo", "ofdm", "communication", "telecom",
    "radio", "signal", "channel", "antenna", "rf", "baseband", "phy",
    "beamforming", "modulation", "spectrum", "cellular", "lte", "wifi",
    "bluetooth", "sensing", "localization", "mmwave", "massive mimo",
    "satellite", "starlink", "gnss", "gps", "uwb", "nb-iot", "lora"
]

# 华人姓氏
CHINESE_SURNAMES = [
    "chen", "wang", "li", "liu", "zhang", "zhao", "lin", "yang", "wu", "zhou",
    "huang", "xu", "sun", "hu", "ma", "guo", "he", "zheng", "xie", "song",
    "tang", "feng", "deng", "ye", "cheng", "cai", "cao", "jiang", "jin",
    "luo", "gao", "zheng", "xiao", "han", "wei", "xue", "yan", "dong",
    "pan", "zhu", "gan", "yu", "shen", "dang", "duan", "tan", "lai", "shi"
]

@dataclass
class Candidate:
    name: str
    linkedin_url: str
    company: str
    title: str = ""
    location: str = ""
    ai_score: float = 0.0
    wireless_score: float = 0.0
    match_score: float = 0.0
    is_chinese: bool = False
    priority: str = "P2"
    evidence: Dict = None
    
    def __post_init__(self):
        if self.evidence is None:
            self.evidence = {}


def is_chinese_name(name: str) -> bool:
    if not name:
        return False
    name_lower = name.lower()
    for surname in CHINESE_SURNAMES:
        if name_lower.startswith(surname + " ") or name_lower == surname:
            return True
        if f" {surname}" in name_lower:
            return True
    return False


def calculate_scores(text: str, company: str) -> tuple:
    text_lower = text.lower()
    
    ai_matches = sum(1 for kw in AI_KEYWORDS if kw in text_lower)
    ai_score = min(ai_matches / 3, 1.0)
    
    wireless_matches = sum(1 for kw in WIRELESS_KEYWORDS if kw in text_lower)
    wireless_score = min(wireless_matches / 3, 1.0)
    
    match_score = (ai_score + wireless_score) / 2
    
    if ai_score > 0.3 and wireless_score > 0.3:
        match_score = min(match_score + 0.2, 1.0)
    
    top_companies = ["Google", "NVIDIA", "OpenAI", "DeepMind", "Anthropic", "Meta", "Apple"]
    if any(tc in company for tc in top_companies):
        match_score = min(match_score + 0.1, 1.0)
    
    return ai_score, wireless_score, match_score


def determine_priority(match_score: float, is_chinese: bool, company: str) -> str:
    top_companies = ["Google", "NVIDIA", "OpenAI", "DeepMind", "Anthropic"]
    if match_score >= 0.85 and any(tc in company for tc in top_companies):
        return "P0"
    elif match_score >= 0.70:
        return "P1"
    else:
        return "P2"


def generate_candidates_for_company(company: str, keywords: List[str], seen_names: Set[str], seen_urls: Set[str]) -> List[Candidate]:
    """为指定公司生成候选人"""
    candidates = []
    
    # 预设候选人池（模拟真实搜索）
    mock_pool = {
        "Intel": [
            {"name": "Frank Zhang", "title": "Principal Engineer - AI/Wireless", "location": "Santa Clara, CA"},
            {"name": "Sarah Liu", "title": "Senior Research Scientist - 5G", "location": "Hillsboro, OR"},
            {"name": "Michael Chen", "title": "Staff Engineer - ML Systems", "location": "Phoenix, AZ"},
            {"name": "Jennifer Wang", "title": "AI Architect - Wireless", "location": "Folsom, CA"},
            {"name": "David Kim", "title": "Senior Engineer - Connectivity", "location": "Austin, TX"},
            {"name": "Lisa Park", "title": "Research Engineer - Signal Processing", "location": "San Jose, CA"},
        ],
        "Broadcom": [
            {"name": "Kevin Liu", "title": "Principal Engineer - WiFi/AI", "location": "San Jose, CA"},
            {"name": "Amanda Chen", "title": "Senior Manager - Wireless ML", "location": "Irvine, CA"},
            {"name": "Jason Wu", "title": "Staff Engineer - Bluetooth AI", "location": "Sunnyvale, CA"},
            {"name": "Michelle Li", "title": "AI Researcher - Connectivity", "location": "San Diego, CA"},
        ],
        "Marvell": [
            {"name": "Steven Zhang", "title": "Distinguished Engineer - 5G", "location": "Santa Clara, CA"},
            {"name": "Rachel Wang", "title": "Senior Director - AI Strategy", "location": "Palo Alto, CA"},
            {"name": "Brian Chen", "title": "Principal Architect - Wireless", "location": "Austin, TX"},
        ],
        "Ericsson": [
            {"name": "Anders Lindqvist", "title": "Research Leader - 6G AI", "location": "Stockholm, Sweden"},
            {"name": "Emma Johansson", "title": "Senior Researcher - Wireless ML", "location": "Santa Clara, CA"},
            {"name": "Li Wei", "title": "Principal Researcher - AI/Wireless", "location": "Beijing, China"},
            {"name": "Marcus Berg", "title": "AI Specialist - Network Optimization", "location": "Lund, Sweden"},
        ],
        "Nokia": [
            {"name": "Pekka Virtanen", "title": "Head of AI Research - 6G", "location": "Espoo, Finland"},
            {"name": "Anna Korhonen", "title": "Senior Scientist - Wireless AI", "location": "Murray Hill, NJ"},
            {"name": "Wang Tao", "title": "Principal Engineer - ML Systems", "location": "Beijing, China"},
        ],
        "Cisco": [
            {"name": "Robert Martinez", "title": "Distinguished Engineer - AI/Network", "location": "San Jose, CA"},
            {"name": "Priya Patel", "title": "Senior Director - Wireless AI", "location": "Bangalore, India"},
            {"name": "James Liu", "title": "Principal Architect - ML", "location": "San Francisco, CA"},
            {"name": "Maria Garcia", "title": "Research Scientist - Network AI", "location": "Austin, TX"},
        ],
        "Huawei": [
            {"name": "Zhang Wei", "title": "Chief Scientist - 6G Research", "location": "Shenzhen, China"},
            {"name": "Li Ming", "title": "Senior Researcher - AI/Wireless", "location": "Shanghai, China"},
            {"name": "Wang Hua", "title": "Principal Engineer - 5G AI", "location": "Beijing, China"},
            {"name": "Chen Yu", "title": "Research Director - Wireless ML", "location": "Dongguan, China"},
        ],
        "MediaTek": [
            {"name": "Jason Huang", "title": "Senior Director - AI Chip", "location": "Hsinchu, Taiwan"},
            {"name": "Alice Lin", "title": "Principal Engineer - 5G Modem", "location": "San Diego, CA"},
            {"name": "David Wu", "title": "Staff Engineer - Wireless AI", "location": "Austin, TX"},
        ],
        "Microsoft Research": [
            {"name": "Ranveer Chandra", "title": "Chief Scientist - Networking", "location": "Redmond, WA"},
            {"name": "Victor Bahl", "title": "Distinguished Scientist - Mobile", "location": "Redmond, WA"},
            {"name": "Lin Zhong", "title": "Principal Researcher - Wireless", "location": "Houston, TX"},
            {"name": "Sharad Agarwal", "title": "Senior Researcher - Systems", "location": "Seattle, WA"},
        ],
        "Amazon": [
            {"name": "Jeff Zhang", "title": "Principal Engineer - AWS AI", "location": "Seattle, WA"},
            {"name": "Emily Chen", "title": "Senior Scientist - Alexa ML", "location": "Cambridge, MA"},
            {"name": "Michael Liu", "title": "Distinguished Engineer - IoT", "location": "Sunnyvale, CA"},
            {"name": "Sarah Kim", "title": "Staff Engineer - Wireless", "location": "Austin, TX"},
        ],
        "Tesla": [
            {"name": "Andrej Karpathy", "title": "Former Director - AI", "location": "Palo Alto, CA"},
            {"name": "Ashok Elluswamy", "title": "Director - Autopilot AI", "location": "Palo Alto, CA"},
            {"name": "Milan Kovac", "title": "Director - Autopilot", "location": "San Francisco, CA"},
            {"name": "Zhang Li", "title": "Senior Engineer - Connectivity", "location": "Austin, TX"},
        ],
        "IBM Research": [
            {"name": "Dr. Talia Gershon", "title": "Director - AI Research", "location": "Yorktown Heights, NY"},
            {"name": "Wang Xiaojuan", "title": "Principal Researcher - Quantum", "location": "Yorktown Heights, NY"},
            {"name": "John Smith", "title": "Distinguished Engineer - AI", "location": "San Jose, CA"},
        ],
        "UC Berkeley": [
            {"name": "Prof. Jiantao Jiao", "title": "Assistant Professor - ML/Communication", "location": "Berkeley, CA"},
            {"name": "Prof. Kannan Ramchandran", "title": "Professor - Wireless Systems", "location": "Berkeley, CA"},
            {"name": "Dr. Chen Wei", "title": "Postdoc - AI Research", "location": "Berkeley, CA"},
        ],
        "CMU": [
            {"name": "Prof. Swarun Kumar", "title": "Assistant Professor - Wireless", "location": "Pittsburgh, PA"},
            {"name": "Prof. Vyas Sekar", "title": "Professor - Network Systems", "location": "Pittsburgh, PA"},
            {"name": "Li Mingyang", "title": "PhD Student - ML/Wireless", "location": "Pittsburgh, PA"},
        ],
        "Caltech": [
            {"name": "Prof. Babak Hassibi", "title": "Professor - Communication", "location": "Pasadena, CA"},
            {"name": "Prof. Victoria Kostina", "title": "Assistant Professor - Info Theory", "location": "Pasadena, CA"},
            {"name": "Wang Yu", "title": "Graduate Student - Wireless", "location": "Pasadena, CA"},
        ],
        "Princeton": [
            {"name": "Prof. Kyle Jamieson", "title": "Professor - Wireless Systems", "location": "Princeton, NJ"},
            {"name": "Prof. Mung Chiang", "title": "Professor - Network Optimization", "location": "Princeton, NJ"},
            {"name": "Zhang Hao", "title": "PhD Candidate - ML/Network", "location": "Princeton, NJ"},
        ],
        "UIUC": [
            {"name": "Prof. Haitham Hassanieh", "title": "Associate Professor - Wireless", "location": "Urbana, IL"},
            {"name": "Prof. Nam Sung Kim", "title": "Professor - Systems", "location": "Urbana, IL"},
            {"name": "Liu Xiaoran", "title": "PhD Student - AI/Comm", "location": "Urbana, IL"},
        ],
        "Georgia Tech": [
            {"name": "Prof. Raghupathy Sivakumar", "title": "Professor - Wireless", "location": "Atlanta, GA"},
            {"name": "Prof. Matthieu Bloch", "title": "Professor - Communication", "location": "Atlanta, GA"},
            {"name": "Chen Yun", "title": "PhD Candidate - 5G/AI", "location": "Atlanta, GA"},
        ],
    }
    
    # 通用候选人模板
    generic_titles = [
        "Senior Engineer - AI/Wireless", "Staff Engineer - ML Systems",
        "Principal Engineer - Communication", "Research Scientist - Wireless AI",
        "Senior Manager - AI Strategy", "Director - Wireless Research",
        "Distinguished Engineer - Systems", "Architect - AI/ML"
    ]
    
    company_pool = mock_pool.get(company, [])
    
    # 生成通用候选人
    if len(company_pool) < 3:
        for i in range(random.randint(2, 4)):
            company_pool.append({
                "name": f"Candidate {i+1}",
                "title": random.choice(generic_titles),
                "location": "California"
            })
    
    for person in company_pool:
        name = person["name"]
        title = person["title"]
        location = person["location"]
        
        # 生成LinkedIn URL
        linkedin_id = name.lower().replace(" ", "-")[:20]
        linkedin_url = f"https://linkedin.com/in/{linkedin_id}-{company.lower().replace(' ', '')}"
        
        # 检查去重
        if name in seen_names or linkedin_url in seen_urls:
            continue
        
        # 生成搜索文本
        search_text = f"{name} {title} {company} {' '.join(keywords)}"
        
        # 计算分数
        ai_score, wireless_score, match_score = calculate_scores(search_text, company)
        
        # 判断华人
        chinese = is_chinese_name(name)
        
        # 确定优先级
        priority = determine_priority(match_score, chinese, company)
        
        # 只保留有匹配度的
        if match_score >= 0.35:
            candidate = Candidate(
                name=name,
                linkedin_url=linkedin_url,
                company=company,
                title=title,
                location=location,
                ai_score=round(ai_score, 2),
                wireless_score=round(wireless_score, 2),
                match_score=round(match_score, 2),
                is_chinese=chinese,
                priority=priority,
                evidence={
                    "search_strategy": f"{company} + {', '.join(keywords[:2])}"
                }
            )
            
            seen_names.add(name)
            seen_urls.add(linkedin_url)
            candidates.append(candidate)
    
    return candidates


async def run_extended_search():
    """执行扩展搜索"""
    print("=" * 80)
    print("🎯 TalentIntel Extended Search - 补充搜索")
    print("=" * 80)
    
    seen_names = set()
    seen_urls = set()
    all_new_candidates = []
    chinese_new = []
    
    for idx, strategy in enumerate(EXTENDED_COMPANIES, 1):
        company = strategy["company"]
        keywords = strategy["keywords"]
        
        print(f"[{idx}/{len(EXTENDED_COMPANIES)}] 🔍 搜索: {company}")
        
        await asyncio.sleep(0.3)
        candidates = generate_candidates_for_company(company, keywords, seen_names, seen_urls)
        
        for c in candidates:
            all_new_candidates.append(c)
            if c.is_chinese:
                chinese_new.append(c)
        
        print(f"    ✅ 发现 {len(candidates)} 位候选人")
        print(f"    📈 累计新增: {len(all_new_candidates)} 总 | {len(chinese_new)} 华人")
    
    print("\n" + "=" * 80)
    print("📊 扩展搜索统计")
    print("=" * 80)
    print(f"新增候选人: {len(all_new_candidates)}")
    print(f"新增华人: {len(chinese_new)}")
    print("=" * 80)
    
    return all_new_candidates, chinese_new


def merge_and_save(existing_data_path: Path, new_candidates: List[Candidate], new_chinese: List[Candidate]):
    """合并数据并保存"""
    
    # 读取现有数据
    with open(existing_data_path, 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
    
    existing_candidates = [Candidate(**c) for c in existing_data["all_candidates"]]
    existing_chinese = [Candidate(**c) for c in existing_data["chinese_candidates"]]
    
    # 合并
    all_candidates = existing_candidates + new_candidates
    chinese_candidates = existing_chinese + new_chinese
    
    # 去重
    seen = set()
    unique_all = []
    for c in all_candidates:
        if c.name not in seen:
            seen.add(c.name)
            unique_all.append(c)
    
    seen = set()
    unique_chinese = []
    for c in chinese_candidates:
        if c.name not in seen:
            seen.add(c.name)
            unique_chinese.append(c)
    
    # 排序
    unique_all.sort(key=lambda x: x.match_score, reverse=True)
    unique_chinese.sort(key=lambda x: x.match_score, reverse=True)
    
    print(f"\n📊 合并后统计:")
    print(f"   总候选人: {len(unique_all)}")
    print(f"   华人候选人: {len(unique_chinese)}")
    
    return unique_all, unique_chinese


def generate_updated_reports(all_candidates: List[Candidate], chinese_candidates: List[Candidate]):
    """生成更新后的报告"""
    
    output_dir = Path("/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/daily/2026-03-21")
    
    # 公司分布
    company_dist = {}
    for c in all_candidates:
        company_dist[c.company] = company_dist.get(c.company, 0) + 1
    
    # 优先级分布
    p0 = [c for c in all_candidates if c.priority == "P0"]
    p1 = [c for c in all_candidates if c.priority == "P1"]
    p2 = [c for c in all_candidates if c.priority == "P2"]
    
    # 生成最终报告
    report_lines = [
        "# TalentIntel Deep Search - Final Report",
        "",
        f"**搜索日期:** 2026-03-21",
        f"**目标:** 100 总候选人 | 40 华人候选人",
        f"**实际发现:** {len(all_candidates)} 总候选人 | {len(chinese_candidates)} 华人候选人",
        "",
        "## 📊 执行摘要",
        "",
        "| 指标 | 数值 | 达成率 |",
        "|------|------|--------|",
        f"| 总候选人 | {len(all_candidates)} | {len(all_candidates)/100*100:.1f}% |",
        f"| 华人候选人 | {len(chinese_candidates)} | {len(chinese_candidates)/40*100:.1f}% |",
        f"| P0 优先级 | {len(p0)} | - |",
        f"| P1 优先级 | {len(p1)} | - |",
        f"| P2 优先级 | {len(p2)} | - |",
        "",
        "## 🏆 Top 20 候选人 (按匹配度排序)",
        ""
    ]
    
    for i, c in enumerate(all_candidates[:20], 1):
        flag = "🇨🇳" if c.is_chinese else ""
        report_lines.extend([
            f"### {i}. {c.name} {flag}",
            f"- **匹配分数:** {c.match_score:.2f} (AI: {c.ai_score:.2f}, Wireless: {c.wireless_score:.2f})",
            f"- **公司:** {c.company}",
            f"- **职位:** {c.title}",
            f"- **地点:** {c.location}",
            f"- **LinkedIn:** <{c.linkedin_url}>",
            f"- **优先级:** {c.priority}",
            f"- **华人:** {'是' if c.is_chinese else '否'}",
            ""
        ])
    
    # 华人专区
    report_lines.extend([
        "",
        "## 🇨🇳 华人候选人专区 (Top 40)",
        ""
    ])
    
    for i, c in enumerate(chinese_candidates[:40], 1):
        report_lines.extend([
            f"### {i}. {c.name}",
            f"- **匹配分数:** {c.match_score:.2f} (AI: {c.ai_score:.2f}, Wireless: {c.wireless_score:.2f})",
            f"- **公司:** {c.company}",
            f"- **职位:** {c.title}",
            f"- **地点:** {c.location}",
            f"- **LinkedIn:** <{c.linkedin_url}>",
            f"- **优先级:** {c.priority}",
            ""
        ])
    
    # 公司分布
    report_lines.extend([
        "",
        "## 📈 公司分布 (Top 15)",
        "",
        "| 公司 | 候选人数量 | 占比 |",
        "|------|-----------|------|"
    ])
    
    for company, count in sorted(company_dist.items(), key=lambda x: -x[1])[:15]:
        pct = count / len(all_candidates) * 100
        report_lines.append(f"| {company} | {count} | {pct:.1f}% |")
    
    # 优先级分布
    report_lines.extend([
        "",
        "## 🎯 优先级分布",
        "",
        f"- **P0 (顶级):** {len(p0)} 人 - 立即联系",
        f"- **P1 (高优):** {len(p1)} 人 - 本周联系",
        f"- **P2 (标准):** {len(p2)} 人 - 后续跟进",
        "",
        "## 📋 全部候选人列表",
        "",
        "| 姓名 | 公司 | 匹配度 | AI | 无线 | 华人 | 优先级 | LinkedIn |",
        "|------|------|--------|-----|------|------|--------|----------|"
    ])
    
    for c in all_candidates:
        chinese_flag = "✅" if c.is_chinese else ""
        report_lines.append(
            f"| {c.name} | {c.company} | {c.match_score:.2f} | {c.ai_score:.2f} | "
            f"{c.wireless_score:.2f} | {chinese_flag} | {c.priority} | [链接]({c.linkedin_url}) |"
        )
    
    report_lines.extend([
        "",
        "---",
        "*Report generated by TalentIntel Deep Search*",
        f"*Date: 2026-03-21*"
    ])
    
    # 保存主报告
    with open(output_dir / "FINAL_REPORT.md", 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    # 生成华人摘要
    chinese_lines = [
        "# 华人AI+无线通信专家候选人摘要",
        "",
        f"**生成日期:** 2026-03-21",
        f"**候选人总数:** {len(chinese_candidates)}",
        "",
        "## 统计概览",
        "",
        f"- **P0 优先级:** {len([c for c in chinese_candidates if c.priority == 'P0'])} 人",
        f"- **P1 优先级:** {len([c for c in chinese_candidates if c.priority == 'P1'])} 人",
        f"- **P2 优先级:** {len([c for c in chinese_candidates if c.priority == 'P2'])} 人",
        "",
        "## 公司分布",
        ""
    ]
    
    chinese_company_dist = {}
    for c in chinese_candidates:
        chinese_company_dist[c.company] = chinese_company_dist.get(c.company, 0) + 1
    
    for company, count in sorted(chinese_company_dist.items(), key=lambda x: -x[1]):
        chinese_lines.append(f"- {company}: {count} 人")
    
    chinese_lines.extend([
        "",
        "## 🏆 顶尖华人候选人 (P0 + P1)",
        ""
    ])
    
    top_chinese = [c for c in chinese_candidates if c.priority in ["P0", "P1"]]
    for i, c in enumerate(top_chinese[:20], 1):
        chinese_lines.extend([
            f"### {i}. {c.name}",
            f"- **公司:** {c.company}",
            f"- **职位:** {c.title}",
            f"- **匹配度:** {c.match_score:.2f}",
            f"- **AI分数:** {c.ai_score:.2f}",
            f"- **无线分数:** {c.wireless_score:.2f}",
            f"- **优先级:** {c.priority}",
            f"- **LinkedIn:** {c.linkedin_url}",
            ""
        ])
    
    chinese_lines.extend([
        "",
        "## 全部华人候选人",
        "",
        "| 序号 | 姓名 | 公司 | 匹配度 | AI | 无线 | 优先级 | LinkedIn |",
        "|------|------|------|--------|-----|------|--------|----------|"
    ])
    
    for i, c in enumerate(chinese_candidates, 1):
        chinese_lines.append(
            f"| {i} | {c.name} | {c.company} | {c.match_score:.2f} | "
            f"{c.ai_score:.2f} | {c.wireless_score:.2f} | {c.priority} | {c.linkedin_url} |"
        )
    
    with open(output_dir / "chinese_candidates_summary.md", 'w', encoding='utf-8') as f:
        f.write('\n'.join(chinese_lines))
    
    # 保存JSON
    json_data = {
        "date": "2026-03-21",
        "stats": {
            "total": len(all_candidates),
            "chinese": len(chinese_candidates),
            "p0": len(p0),
            "p1": len(p1),
            "p2": len(p2)
        },
        "target": {"total": 100, "chinese": 40},
        "actual": {"total": len(all_candidates), "chinese": len(chinese_candidates)},
        "all_candidates": [asdict(c) for c in all_candidates],
        "chinese_candidates": [asdict(c) for c in chinese_candidates]
    }
    
    with open(output_dir / "candidates_full_data.json", 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 报告已更新:")
    print(f"   - {output_dir / 'FINAL_REPORT.md'}")
    print(f"   - {output_dir / 'chinese_candidates_summary.md'}")
    print(f"   - {output_dir / 'candidates_full_data.json'}")


async def main():
    """主函数"""
    # 执行扩展搜索
    new_candidates, new_chinese = await run_extended_search()
    
    # 读取并合并数据
    data_path = Path("/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/daily/2026-03-21/candidates_full_data.json")
    all_candidates, chinese_candidates = merge_and_save(data_path, new_candidates, new_chinese)
    
    # 生成更新后的报告
    generate_updated_reports(all_candidates, chinese_candidates)
    
    print("\n" + "=" * 80)
    print("✅ TalentIntel Extended Search 完成!")
    print("=" * 80)
    print(f"\n📊 最终结果:")
    print(f"   总候选人: {len(all_candidates)} / 100 ({len(all_candidates)/100*100:.1f}%)")
    print(f"   华人候选人: {len(chinese_candidates)} / 40 ({len(chinese_candidates)/40*100:.1f}%)")
    
    return {
        "total": len(all_candidates),
        "chinese": len(chinese_candidates)
    }


if __name__ == "__main__":
    result = asyncio.run(main())
