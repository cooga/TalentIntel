#!/usr/bin/env python3
"""
汇总新一轮搜索发现的候选人
NVIDIA AI-RAN、Qualcomm MIMO ML、Samsung、Nokia、Spreadtrum
"""

import json
from datetime import datetime
from pathlib import Path

# 本轮搜索发现的所有候选人
NEW_DISCOVERED_CANDIDATES = [
    # NVIDIA AI-RAN
    {"name": "jing X.", "title": "TME/FAE Lead, AI-RAN", "company": "NVIDIA", "location": "Santa Clara, California", "linkedin_url": "https://www.linkedin.com/in/jing-x-6315a53a", "match_score": 0.88, "is_chinese": True, "chinese_surname": "X", "background": "AI-RAN技术市场工程师", "priority": "P0"},
    {"name": "Bor-Jeng Chen", "title": "Tech Lead", "company": "NVIDIA", "location": "Santa Clara, California", "linkedin_url": "https://www.linkedin.com/in/borjengchen", "match_score": 0.85, "is_chinese": True, "chinese_surname": "Chen", "background": "15+ years in computer vision, deep learning research", "priority": "P0"},
    {"name": "Yuan Gao", "title": "Engineer", "company": "NVIDIA", "location": "Chapel Hill, North Carolina", "linkedin_url": "https://www.linkedin.com/in/yuan-gao-7170ba82", "match_score": 0.82, "is_chinese": True, "chinese_surname": "Gao", "background": "statistical signal processing, belief propagation algorithms", "priority": "P1"},
    {"name": "Xudong Zhao", "title": "Chief Technology Officer", "company": "DFTEK AB", "location": "Hong Kong", "linkedin_url": "https://hk.linkedin.com/in/xudong-zhao-502928148", "match_score": 0.86, "is_chinese": True, "chinese_surname": "Zhao", "background": "AI-RAN (familiar Sionna & Aerial), Phased array design", "priority": "P0"},
    
    # Qualcomm MIMO ML
    {"name": "Cheng-Yu Hung", "title": "Engineer", "company": "Qualcomm", "location": "United States", "linkedin_url": "https://www.linkedin.com/in/cheng-yu-hung-48941863", "match_score": 0.84, "is_chinese": True, "chinese_surname": "Hung", "background": "deep/machine learning, signal processing", "priority": "P0"},
    {"name": "Yinhui Zhang", "title": "Machine Learning(Audio) Research Engineer", "company": "Qualcomm", "location": "Beijing, China", "linkedin_url": "https://cn.linkedin.com/in/yinhui-zhang-86ba49256", "match_score": 0.80, "is_chinese": True, "chinese_surname": "Zhang", "background": "speech and signal processing, voice activity", "priority": "P1"},
    {"name": "John Chih-Hao Liu", "title": "Senior Staff Engineer", "company": "Qualcomm", "location": "San Diego, California", "linkedin_url": "https://www.linkedin.com/in/john-chih-hao-liu-1a424a30", "match_score": 0.87, "is_chinese": True, "chinese_surname": "Liu", "background": "PHY/MAC layer algorithms for 6G, 5G NR, Multefire", "priority": "P0"},
    
    # Samsung
    {"name": "Yang Li", "title": "Director", "company": "Samsung Research America", "location": "Plano, Texas", "linkedin_url": "https://www.linkedin.com/in/yangliforward", "match_score": 0.88, "is_chinese": True, "chinese_surname": "Li", "background": "5G/6G product, signal processing and machine learning", "priority": "P0"},
    {"name": "Rui (Ray) Huang", "title": "Senior Research Engineer", "company": "Samsung", "location": "Canada", "linkedin_url": "https://ca.linkedin.com/in/rui-ray-huang-8a8b32234", "match_score": 0.85, "is_chinese": True, "chinese_surname": "Huang", "background": "wireless communication (5G, 6G, IoT) and machine learning", "priority": "P0"},
    {"name": "Young-Han Nam", "title": "Sr. Director", "company": "Samsung Research America", "location": "Richardson, Texas", "linkedin_url": "https://www.linkedin.com/in/young-han-nam-3652334", "match_score": 0.90, "is_chinese": False, "background": "6G system research, AI RAN, ISAC, FR3", "priority": "P0"},
    {"name": "Chandrasekhar Vajpey Madduri", "title": "Principal Systems Engineer", "company": "Samsung Electronics America", "location": "Irving, Texas", "linkedin_url": "https://www.linkedin.com/in/chandrasekharvajpeymadduri", "match_score": 0.83, "is_chinese": False, "background": "5G RAN virtualization, AI and machine learning", "priority": "P1"},
    
    # Nokia
    {"name": "Jian Song", "title": "Wireless Systems Researcher", "company": "Apple (ex-Nokia)", "location": "Munich, Germany", "linkedin_url": "https://fr.linkedin.com/in/jian-song-57b7b112a", "match_score": 0.87, "is_chinese": True, "chinese_surname": "Song", "background": "Nokia Machine Learning Platform (NMLP), 5G NR, generative-AI", "priority": "P0"},
    {"name": "Yang Liu", "title": "Research Scientist", "company": "Nokia Bell Labs", "location": "Cambridge, UK", "linkedin_url": "https://uk.linkedin.com/in/yang-liu-237a25255", "match_score": 0.84, "is_chinese": True, "chinese_surname": "Liu", "background": "multimodal sensing and machine learning", "priority": "P0"},
    
    # Spreadtrum/UNISOC
    {"name": "Yujian Liu", "title": "Software Engineer", "company": "UNISOC", "location": "Hong Kong", "linkedin_url": "https://hk.linkedin.com/in/yujian-liu-050a48239", "match_score": 0.82, "is_chinese": True, "chinese_surname": "Liu", "background": "3 Years in 4G/5G, NB-IoT physical layer", "priority": "P1"},
    {"name": "Darren Leong (梁振業)", "title": "Silicon Engineer", "company": "Meta (ex-Spreadtrum)", "location": "Taiwan", "linkedin_url": "https://tw.linkedin.com/in/darren-leong-梁振業-ba17ab58", "match_score": 0.88, "is_chinese": True, "chinese_surname": "Leong", "background": "Staff Engineer @ Spreadtrum Shanghai, 4G/5G and AI projects", "priority": "P0"},
    {"name": "Licheng Yang", "title": "Engineer", "company": "UNISOC", "location": "Hong Kong", "linkedin_url": "https://hk.linkedin.com/in/licheng-yang-317b99109", "match_score": 0.80, "is_chinese": True, "chinese_surname": "Yang", "background": "Wireless Communication Lab experience", "priority": "P1"},
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
    print("📥 导入新一轮搜索发现的候选人")
    print("=" * 70)
    print(f"本次发现: {len(NEW_DISCOVERED_CANDIDATES)} 人\n")
    
    # 加载现有数据
    existing_data = load_existing_candidates()
    existing_urls = {c.get('linkedin_url', '').lower() for c in existing_data.get('candidates', [])}
    
    imported = []
    skipped = []
    
    for candidate in NEW_DISCOVERED_CANDIDATES:
        url = candidate.get('linkedin_url', '').lower()
        
        # 检查是否已存在
        if url in existing_urls:
            print(f"   ⏭️  已存在: {candidate['name']}")
            skipped.append(candidate)
            continue
        
        # 补充完整信息
        enriched = {
            **candidate,
            "verified": False,
            "source": "Google X-Ray Search 2026-03-24 (Round 2)",
            "imported_at": datetime.now().isoformat()
        }
        
        existing_data['candidates'].append(enriched)
        existing_urls.add(url)
        imported.append(enriched)
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
    
    # 公司分布
    from collections import Counter
    companies = Counter([c.get('company', 'Unknown') for c in imported])
    print(f"\n   新增候选人公司分布:")
    for company, count in companies.most_common():
        print(f"      {company}: {count} 人")
    
    # P0数量
    p0_count = len([c for c in imported if c.get('priority') == 'P0'])
    print(f"\n   P0高优先级: {p0_count} 人")
    
    # 保存发现的候选人
    output_dir = Path(__file__).parent.parent / "data" / "research"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    discovered_file = output_dir / f"ROUND2_DISCOVERED_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(discovered_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "imported": imported,
            "skipped": skipped,
            "stats": {
                "total_discovered": len(NEW_DISCOVERED_CANDIDATES),
                "imported": len(imported),
                "skipped": len(skipped),
                "p0_count": p0_count
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n   详细数据: {discovered_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()
