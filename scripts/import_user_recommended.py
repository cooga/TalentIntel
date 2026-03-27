#!/usr/bin/env python3
"""
导入用户推荐的16位候选人
基于Excel数据导入TalentIntel库
"""

import json
from datetime import datetime
from pathlib import Path

# 用户推荐的16位新候选人（从Excel提取）
USER_RECOMMENDED_CANDIDATES = [
    {
        "name": "Rui Li",
        "title": "Researcher",
        "company": "University of Cambridge",
        "location": "UK",
        "linkedin_url": "https://uk.linkedin.com/in/ruihuili",
        "email": "ruili.cambridge@gmail.com",
        "match_score": 0.90,
        "is_chinese": True,
        "chinese_surname": "Li",
        "background": "边缘AI优化（LLM防抖、分布式训练）、AI模型压缩",
        "reason": "学术方向匹配，有工程经验",
        "experience_years": None,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P0",
        "website": "https://ruihuili.github.io/"
    },
    {
        "name": "Hao-Hsuan Chang",
        "title": "Researcher",
        "company": "Virginia Tech",
        "location": "United States",
        "linkedin_url": "https://www.linkedin.com/in/hao-hsuan-chang-8862b7170/en",
        "email": "haohsuan@vt.edu",
        "match_score": 0.85,
        "is_chinese": True,
        "chinese_surname": "Chang",
        "background": "开发低计算复杂度嵌入式通信算法模型",
        "reason": "台湾人，学术方向匹配，有工程经验",
        "experience_years": None,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P0",
        "website": "https://haohsuan2918.github.io/"
    },
    {
        "name": "Qiang Fu",
        "title": "Researcher",
        "company": "University of Alabama",
        "location": "United States",
        "linkedin_url": "https://www.linkedin.com/in/qiangfu4",
        "email": "qfu4@crimson.ua.edu",
        "match_score": 0.85,
        "is_chinese": True,
        "chinese_surname": "Fu",
        "background": "强化学习和AI项目经验，参与过无线通信的项目，有EE背景",
        "reason": "9年AI+信号处理经验",
        "experience_years": 9,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P0"
    },
    {
        "name": "Li Li",
        "title": "Researcher/Engineer",
        "company": "Unknown",
        "location": "UK",
        "linkedin_url": "https://uk.linkedin.com/in/li-li-isac-ai",
        "email": "lilishef@hotmail.com",
        "match_score": 0.88,
        "is_chinese": True,
        "chinese_surname": "Li",
        "background": "多年无线工作经验，参与过AI+无线项目",
        "reason": "20年工作经验，有AI和通信背景，带过项目",
        "experience_years": 20,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P0"
    },
    {
        "name": "Zhican(West) Chen",
        "title": "AI-RAN Engineer",
        "company": "NVIDIA",
        "location": "United States",
        "linkedin_url": "https://www.linkedin.com/in/zhican-west-chen-7213b4b4",
        "email": "zc38@rice.edu",
        "match_score": 0.92,
        "is_chinese": True,
        "chinese_surname": "Chen",
        "background": "参与NV AI-RAN项目开发和算法设计",
        "reason": "NV AI-RAN - 核心匹配！",
        "experience_years": None,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P0",
        "tags": ["AI-RAN", "NVIDIA", "5G", "O-RAN"]
    },
    {
        "name": "Po-Han Huang",
        "title": "Inference Acceleration Engineer",
        "company": "Unknown",
        "location": "United States",
        "linkedin_url": "https://www.linkedin.com/in/phuang17",
        "email": None,
        "match_score": 0.80,
        "is_chinese": True,
        "chinese_surname": "Huang",
        "background": "模型加速",
        "reason": "推理加速，台湾人",
        "experience_years": None,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P1",
        "website": "https://phuang17.github.io/"
    },
    {
        "name": "Calvin Chung-Shue Chen",
        "title": "AI Communication Engineer",
        "company": "Nokia",
        "location": "France",
        "linkedin_url": "https://fr.linkedin.com/in/calvin-chung-shue-chen-2700346",
        "email": None,
        "match_score": 0.85,
        "is_chinese": True,
        "chinese_surname": "Chen",
        "background": "诺基亚工作经验，最近4年从事AI通信工作",
        "reason": "香港人，诺基亚，20年工作经验",
        "experience_years": 20,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P0"
    },
    {
        "name": "Tingwu Wang",
        "title": "Embodied AI Researcher",
        "company": "NVIDIA",
        "location": "United States",
        "linkedin_url": "https://www.linkedin.com/in/tingwu-wang-3a592baa",
        "email": "wilsonwanguoft@gmail.com",
        "match_score": 0.82,
        "is_chinese": True,
        "chinese_surname": "Wang",
        "background": "具身智能",
        "reason": "机器人、NV",
        "experience_years": None,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P1",
        "website": "https://tingwuwang.github.io/"
    },
    {
        "name": "Yudi Huang",
        "title": "Aerial Software Developer",
        "company": "NVIDIA",
        "location": "United States",
        "linkedin_url": "https://www.linkedin.com/in/yudi-huang-166087164",
        "email": None,
        "match_score": 0.78,
        "is_chinese": True,
        "chinese_surname": "Huang",
        "background": "英伟达，Aerial软件开发，通信背景",
        "reason": "Aerial软件开发，通信背景，工作时间2年，较短",
        "experience_years": 2,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P2",
        "tags": ["Aerial", "5G", "CUDA"]
    },
    {
        "name": "George Zhou",
        "title": "Engineering Leader",
        "company": "Multiple (Samsung/Intel/Qualcomm/Broadcom)",
        "location": "United States",
        "linkedin_url": "https://www.linkedin.com/in/george-zhou-422bb822",
        "email": None,
        "match_score": 0.90,
        "is_chinese": True,
        "chinese_surname": "Zhou",
        "background": "背景匹配，工作经验丰富(25年)，在多家通信企业工作，三星、英特尔、高通、博通",
        "reason": "软硬件、AI背景，25年工作经验",
        "experience_years": 25,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P0",
        "tags": ["Samsung", "Intel", "Qualcomm", "Broadcom", "5G"]
    },
    {
        "name": "Yejing Fan",
        "title": "Postdoc Researcher",
        "company": "University of Leeds",
        "location": "UK",
        "linkedin_url": "https://uk.linkedin.com/in/yejing-fan-417091195",
        "email": "el17yf@leeds.ac.uk",
        "match_score": 0.75,
        "is_chinese": True,
        "chinese_surname": "Fan",
        "background": "AI4无线博士后，利兹大学",
        "reason": "博后，AI4WIRELESS",
        "experience_years": None,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P1",
        "website": "https://eps.leeds.ac.uk/electronic-engineering/pgr/9360/yejing-fan"
    },
    {
        "name": "Zengli Yang",
        "title": "AI Engineer",
        "company": "Unknown",
        "location": "United States",
        "linkedin_url": "https://www.linkedin.com/in/zengli-yang",
        "email": None,
        "match_score": 0.78,
        "is_chinese": True,
        "chinese_surname": "Yang",
        "background": "10年工作经验，通信转AI",
        "reason": "AI项目多，有通信背景",
        "experience_years": 10,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P1"
    },
    {
        "name": "Fujuan Guo",
        "title": "Wireless Communication Algorithm Engineer",
        "company": "Qualcomm",
        "location": "United States",
        "linkedin_url": "https://www.linkedin.com/in/fujuan-guo-a434ba88",
        "email": None,
        "match_score": 0.88,
        "is_chinese": True,
        "chinese_surname": "Guo",
        "background": "高通无线通信算法和软件工程，MIMO channel estimation based on machine learning approach",
        "reason": "高通，有用到机器学习",
        "experience_years": None,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P0",
        "tags": ["MIMO", "channel estimation", "Qualcomm", "5G"]
    },
    {
        "name": "Tianyang Bai",
        "title": "Wireless Engineer",
        "company": "Google",
        "location": "United States",
        "linkedin_url": "https://www.linkedin.com/in/tianyang-bai-183b4056",
        "email": None,
        "match_score": 0.80,
        "is_chinese": True,
        "chinese_surname": "Bai",
        "background": "高通无线到谷歌无线，20年经验",
        "reason": "缺少信息，谷歌",
        "experience_years": 20,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P0"
    },
    {
        "name": "Chunlin Yang",
        "title": "Wireless Modem Engineer",
        "company": "Multiple (Nokia/Intel/Samsung)",
        "location": "United States",
        "linkedin_url": "https://www.linkedin.com/in/chunlinyang",
        "email": None,
        "match_score": 0.87,
        "is_chinese": True,
        "chinese_surname": "Yang",
        "background": "5G and 4G wireless modem baseband L1/PHY SW/FW design, algorithm, architecture",
        "reason": "20年，有AI经验，诺基亚、英特尔、三星",
        "experience_years": 20,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P0",
        "tags": ["5G", "4G", "L1", "PHY", "modem", "Nokia", "Intel", "Samsung"]
    },
    {
        "name": "An Chen",
        "title": "Vice President",
        "company": "Qualcomm",
        "location": "United States",
        "linkedin_url": "https://www.linkedin.com/in/an-chen-2400762",
        "email": None,
        "match_score": 0.90,
        "is_chinese": True,
        "chinese_surname": "Chen",
        "background": "高通副总裁",
        "reason": "20+工作经验",
        "experience_years": 20,
        "source": "User Recommended (Excel)",
        "verified": False,
        "priority": "P0",
        "tags": ["VP", "Qualcomm", "executive"]
    }
]

def load_existing_candidates():
    """加载现有候选人库"""
    candidates_file = Path(__file__).parent.parent / "data" / "active" / "candidates.json"
    if candidates_file.exists():
        with open(candidates_file) as f:
            return json.load(f)
    return {"timestamp": datetime.now().isoformat(), "count": 0, "candidates": []}

def save_candidates(data):
    """保存候选人数据"""
    candidates_file = Path(__file__).parent.parent / "data" / "active" / "candidates.json"
    candidates_file.parent.mkdir(parents=True, exist_ok=True)
    with open(candidates_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print("=" * 70)
    print("📥 导入用户推荐的候选人")
    print("=" * 70)
    print(f"本次导入: {len(USER_RECOMMENDED_CANDIDATES)} 人\n")
    
    # 加载现有数据
    existing_data = load_existing_candidates()
    existing_urls = {c.get('linkedin_url', '').lower() for c in existing_data.get('candidates', [])}
    
    imported = []
    skipped = []
    
    for candidate in USER_RECOMMENDED_CANDIDATES:
        url = candidate.get('linkedin_url', '').lower()
        
        # 检查是否已存在
        if url in existing_urls:
            print(f"   ⏭️  已存在: {candidate['name']}")
            skipped.append(candidate)
            continue
        
        # 添加到库
        candidate['imported_at'] = datetime.now().isoformat()
        existing_data['candidates'].append(candidate)
        existing_urls.add(url)
        imported.append(candidate)
        print(f"   ✅ 导入: {candidate['name']} ({candidate['company']}) - 优先级: {candidate['priority']}")
    
    # 更新计数
    existing_data['count'] = len(existing_data['candidates'])
    existing_data['timestamp'] = datetime.now().isoformat()
    
    # 保存
    save_candidates(existing_data)
    
    print("\n" + "=" * 70)
    print("📊 导入结果")
    print("=" * 70)
    print(f"   成功导入: {len(imported)} 人")
    print(f"   跳过重复: {len(skipped)} 人")
    print(f"   候选人库总数: {existing_data['count']} 人")
    
    # 优先级分布
    p0_count = len([c for c in imported if c.get('priority') == 'P0'])
    p1_count = len([c for c in imported if c.get('priority') == 'P1'])
    p2_count = len([c for c in imported if c.get('priority') == 'P2'])
    
    print(f"\n   优先级分布:")
    print(f"      P0 (高优先级): {p0_count} 人")
    print(f"      P1 (中优先级): {p1_count} 人")
    print(f"      P2 (低优先级): {p2_count} 人")
    
    # 公司分布
    from collections import Counter
    companies = Counter([c.get('company', 'Unknown') for c in imported])
    print(f"\n   公司分布:")
    for company, count in companies.most_common():
        print(f"      {company}: {count} 人")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
