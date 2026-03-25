#!/usr/bin/env python3
"""
生成清理后的真实候选人数据集（排除模拟数据）
"""
import json
import csv
from collections import Counter
from datetime import datetime

BASE_DIR = "/Users/cooga/.openclaw/workspace/Project/TalentIntel"

# 加载统一数据库
with open(f"{BASE_DIR}/data/unified_candidates_db.json", 'r') as f:
    db = json.load(f)

# 过滤条件：排除模拟数据
def is_real_candidate(c):
    """判断是否为真实候选人"""
    url = c.get('linkedin_url', '')
    source = c.get('source', '')
    score = c.get('match_score', 0)
    
    # 排除明显的模拟URL模式
    fake_patterns = ['-signal', '-nvidia', '-genai', '-mimo', '-wireless', '-6g', '-quantum', '-comm', '-satellite', '-phd', 'in/cwang-', 'in/jamesli-', 'in/alexzhang-', 'in/robertliu-', 'in/emilychen-', 'in/junwang-', 'in/xianbinwang', 'in/amyl-', 'in/danielwu-', 'in/jpark-', 'in/lzhang-', 'in/mwu-', 'in/schen-']
    
    for pattern in fake_patterns:
        if pattern in url:
            return False
    
    # 排除明确标记为模拟的
    if 'simulated' in source.lower():
        return False
    
    # 排除linkedin.com/in/xxx-xxx 格式（通常是人名，模拟数据用描述性后缀）
    if '/in/' in url:
        parts = url.split('/in/')[-1].rstrip('/').split('-')
        # 如果URL部分包含技术词汇，可能是模拟数据
        tech_words = ['signal', 'wireless', 'quantum', 'satellite', 'phd', 'genai', 'mimo', '6g', '5g', 'ml', 'ai']
        for part in parts:
            if part.lower() in tech_words:
                return False
    
    return True

# 过滤真实候选人
real_candidates = [c for c in db['candidates'] if is_real_candidate(c)]

print("🧹 数据清理报告")
print("=" * 60)
print(f"原始数据: {len(db['candidates'])} 人")
print(f"移除模拟数据: {len(db['candidates']) - len(real_candidates)} 人")
print(f"✅ 真实候选人: {len(real_candidates)} 人")

# 统计
chinese_count = sum(1 for c in real_candidates if c.get('is_chinese'))
verified_count = sum(1 for c in real_candidates if c.get('verified'))
p0_count = sum(1 for c in real_candidates if c.get('priority') == 'P0')

print(f"\n📊 清理后统计:")
print(f"  - 华人: {chinese_count} 人 ({chinese_count/len(real_candidates)*100:.1f}%)")
print(f"  - 已验证: {verified_count} 人 ({verified_count/len(real_candidates)*100:.1f}%)")
print(f"  - P0优先级: {p0_count} 人")

# 公司分布
companies = Counter(c.get('company', 'Unknown') for c in real_candidates if c.get('company'))
print(f"\n🏢 公司分布 (Top 10):")
for company, count in companies.most_common(10):
    print(f"  - {company}: {count} 人")

# 保存清理后的数据
clean_db = {
    'timestamp': datetime.now().isoformat(),
    'total_candidates': len(real_candidates),
    'chinese_count': chinese_count,
    'verified_count': verified_count,
    'p0_count': p0_count,
    'note': 'Cleaned dataset - excludes simulated candidates',
    'candidates': real_candidates
}

output_json = f"{BASE_DIR}/data/clean_candidates_db.json"
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(clean_db, f, indent=2, ensure_ascii=False)

print(f"\n💾 清理后数据已保存:")
print(f"  📁 {output_json}")

# 生成清理后的CSV
csv_output = "/tmp/clean_candidates_report_20260325.csv"
csv_lines = ['姓名,职位,公司,地点,匹配分数,优先级,华人,中文姓氏,专业背景,LinkedIn链接,数据来源,已验证']

for c in real_candidates:
    name = c.get('name', '').replace(',', ' ')
    title = c.get('title', '').replace(',', ' ')
    company = c.get('company', '').replace(',', ' ')
    location = c.get('location', '').replace(',', ' ')
    score = c.get('match_score', 0)
    priority = c.get('priority', '')
    is_chinese = '是' if c.get('is_chinese') else '否'
    surname = c.get('chinese_surname', '')
    background = c.get('background', '').replace(',', ' ').replace('\n', ' ')[:200]
    linkedin = c.get('linkedin_url', '')
    source = c.get('source', '').replace(',', ' ')
    verified = '是' if c.get('verified') else '否'
    
    csv_lines.append(f'"{name}","{title}","{company}","{location}",{score},{priority},{is_chinese},{surname},"{background}","{linkedin}","{source}",{verified}')

with open(csv_output, 'w', encoding='utf-8') as f:
    f.write('\n'.join(csv_lines))

print(f"  📊 CSV报告: {csv_output}")

# 显示Top 10真实高分候选人
print("\n⭐ Top 10 真实高分候选人:")
print("-" * 100)
real_candidates_sorted = sorted(real_candidates, key=lambda x: x.get('match_score', 0), reverse=True)
for i, c in enumerate(real_candidates_sorted[:10], 1):
    name = c.get('name', '')[:25]
    company = c.get('company', '')[:20]
    score = c.get('match_score', 0)
    priority = c.get('priority', 'P?')
    verified = '✓' if c.get('verified') else ' '
    print(f"{i:2}. {verified} {name:25} | {company:20} | 匹配度:{score:.2f} | {priority}")

# SpaceX详细列表
print("\n🚀 SpaceX 候选人列表 (8人):")
print("-" * 100)
spacex_list = [c for c in real_candidates if c.get('company', '').lower() == 'spacex' or 'spacex' in c.get('source', '').lower()]
for c in sorted(spacex_list, key=lambda x: x.get('match_score', 0), reverse=True):
    chinese_mark = '🇨🇳' if c.get('is_chinese') else '  '
    print(f"  {chinese_mark} {c['name']:30} | {c['title'][:35]:35} | 匹配度:{c.get('match_score', 0):.2f}")

print("\n✅ 数据清理完成!")
