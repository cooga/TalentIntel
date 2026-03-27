#!/usr/bin/env python3
"""
汇总本次搜索发现的候选人并导入系统
AMD、Marvell、Apple 华人 AI/ML 候选人
"""

import json
from datetime import datetime
from pathlib import Path

# 本次搜索发现的所有候选人
DISCOVERED_CANDIDATES = [
    # AMD
    {"name": "Xin Li", "title": "Machine Learning Software Engineer", "company": "AMD", "location": "Sunnyvale, California", "linkedin_url": "https://www.linkedin.com/in/xin-li-23b35735", "match_score": 0.82, "is_chinese": True, "chinese_surname": "Li"},
    {"name": "Andy Luo", "title": "Engineer", "company": "AMD", "location": "San Jose, California", "linkedin_url": "https://www.linkedin.com/in/andyluo77", "match_score": 0.78, "is_chinese": True, "chinese_surname": "Luo"},
    {"name": "David Kang", "title": "Senior ML Software Engineer", "company": "AMD", "location": "Austin, Texas", "linkedin_url": "https://www.linkedin.com/in/david-kang-081bba54", "match_score": 0.80, "is_chinese": True, "chinese_surname": "Kang"},
    {"name": "Ray Lin", "title": "AI Engineer", "company": "AMD", "location": "Santa Clara, California", "linkedin_url": "https://www.linkedin.com/in/ray-lin-76926a13a", "match_score": 0.83, "is_chinese": True, "chinese_surname": "Lin"},
    {"name": "Xinya Zhang", "title": "Engineer", "company": "AMD", "location": "Austin, Texas", "linkedin_url": "https://www.linkedin.com/in/xinya-zhang-93246857", "match_score": 0.75, "is_chinese": True, "chinese_surname": "Zhang"},
    {"name": "Peng Sun", "title": "Sr. Director of AI Software Engineering", "company": "AMD", "location": "Austin, Texas", "linkedin_url": "https://www.linkedin.com/in/pengsun86", "match_score": 0.88, "is_chinese": True, "chinese_surname": "Sun"},
    
    # Marvell
    {"name": "Xuehua Chen", "title": "Engineer", "company": "Marvell", "location": "Palo Alto, California", "linkedin_url": "https://www.linkedin.com/in/xuehua-chen-253a805", "match_score": 0.76, "is_chinese": True, "chinese_surname": "Chen"},
    {"name": "Jiani Huang", "title": "Engineer", "company": "Marvell", "location": "San Jose, California", "linkedin_url": "https://www.linkedin.com/in/jiani-huang-26a48359", "match_score": 0.77, "is_chinese": True, "chinese_surname": "Huang"},
    {"name": "Li Y.", "title": "Principal Engineer", "company": "Marvell", "location": "San Jose, California", "linkedin_url": "https://www.linkedin.com/in/li-y-4a217263", "match_score": 0.85, "is_chinese": True, "chinese_surname": "Li"},
    {"name": "Lily Wong", "title": "Engineer", "company": "Marvell", "location": "Campbell, California", "linkedin_url": "https://www.linkedin.com/in/lilyawong", "match_score": 0.74, "is_chinese": True, "chinese_surname": "Wong"},
    {"name": "Yuping Zhang", "title": "Engineer", "company": "Marvell", "location": "Santa Clara, California", "linkedin_url": "https://www.linkedin.com/in/yupingzhang", "match_score": 0.76, "is_chinese": True, "chinese_surname": "Zhang"},
    {"name": "Yao C.", "title": "Engineer", "company": "Marvell", "location": "San Francisco Bay Area", "linkedin_url": "https://www.linkedin.com/in/chouyao", "match_score": 0.73, "is_chinese": True, "chinese_surname": "Yao"},
    
    # Apple
    {"name": "Caron Zhang", "title": "Principal AI/ML Engineer", "company": "Apple", "location": "Cupertino, California", "linkedin_url": "https://www.linkedin.com/in/tianlucaronzhang", "match_score": 0.87, "is_chinese": True, "chinese_surname": "Zhang"},
    {"name": "YIFENG LIU", "title": "AI/ML Data Platform Engineer", "company": "Apple", "location": "Cupertino, California", "linkedin_url": "https://www.linkedin.com/in/yifeng-liu-b231b870", "match_score": 0.84, "is_chinese": True, "chinese_surname": "Liu"},
    {"name": "Joseph Cheng", "title": "ML Research, Responsible AI", "company": "Apple", "location": "Cupertino, California", "linkedin_url": "https://www.linkedin.com/in/josephyitancheng", "match_score": 0.86, "is_chinese": True, "chinese_surname": "Cheng"},
    {"name": "Hepeng Zhang", "title": "Machine Learning Engineer", "company": "Apple", "location": "Cupertino, California", "linkedin_url": "https://www.linkedin.com/in/hepengzhang", "match_score": 0.85, "is_chinese": True, "chinese_surname": "Zhang"},
    {"name": "Jiarui Lu", "title": "Foundation Models Engineer", "company": "Apple", "location": "Cupertino, California", "linkedin_url": "https://www.linkedin.com/in/jiarui-lu", "match_score": 0.83, "is_chinese": True, "chinese_surname": "Lu"},
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
    print("📥 导入新发现候选人")
    print("=" * 70)
    print(f"本次发现: {len(DISCOVERED_CANDIDATES)} 人\n")
    
    # 加载现有数据
    existing_data = load_existing_candidates()
    existing_urls = {c.get('linkedin_url', '').lower() for c in existing_data.get('candidates', [])}
    
    imported = []
    skipped = []
    
    for candidate in DISCOVERED_CANDIDATES:
        url = candidate.get('linkedin_url', '').lower()
        
        # 检查是否已存在
        if url in existing_urls:
            print(f"   ⏭️  已存在: {candidate['name']}")
            skipped.append(candidate)
            continue
        
        # 补充完整信息
        enriched = {
            **candidate,
            "verified": True,
            "verified_at": datetime.now().isoformat(),
            "source": "Google X-Ray Search 2026-03-24",
            "verification_method": "browser_automation"
        }
        
        existing_data['candidates'].append(enriched)
        existing_urls.add(url)
        imported.append(enriched)
        print(f"   ✅ 导入: {candidate['name']} ({candidate['company']}) - 匹配度: {candidate['match_score']}")
    
    # 更新计数
    existing_data['count'] = len(existing_data['candidates'])
    existing_data['timestamp'] = datetime.now().isoformat()
    
    # 保存
    save_candidates(existing_data)
    
    # 统计
    print("\n" + "=" * 70)
    print("📊 导入结果")
    print("=" * 70)
    print(f"   成功导入: {len(imported)} 人")
    print(f"   跳过重复: {len(skipped)} 人")
    print(f"   候选人库总数: {existing_data['count']} 人")
    
    # 公司分布
    from collections import Counter
    companies = Counter([c['company'] for c in imported])
    print("\n   新增候选人公司分布:")
    for company, count in companies.most_common():
        print(f"      {company}: {count} 人")
    
    # 保存发现的候选人
    output_dir = Path(__file__).parent.parent / "data" / "research"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    discovered_file = output_dir / f"DISCOVERED_CANDIDATES_20260324_220800.json"
    with open(discovered_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "imported": imported,
            "skipped": skipped,
            "stats": {
                "total_discovered": len(DISCOVERED_CANDIDATES),
                "imported": len(imported),
                "skipped": len(skipped)
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n   详细数据: {discovered_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()
