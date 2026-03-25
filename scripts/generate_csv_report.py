#!/usr/bin/env python3
"""
合并所有候选人数据并生成详细Excel表格
"""
import json
import glob
from datetime import datetime
import sys

# 读取所有候选人文件
candidates = []

# 读取ROUND2_DISCOVERED
with open('ROUND2_DISCOVERED_20260324_234710.json', 'r') as f:
    data = json.load(f)
    for c in data.get('imported', []):
        c['batch'] = 'Round 2'
        candidates.append(c)

# 读取DISCOVERED_CANDIDATES
with open('DISCOVERED_CANDIDATES_20260324_220800.json', 'r') as f:
    data = json.load(f)
    for c in data.get('imported', []):
        c['batch'] = 'Round 1'
        candidates.append(c)

# 读取其他文件
for fname in ['INTEL_CANDIDATES_20260324_215348.json', 'BROADCOM_CANDIDATES_20260324_215543.json']:
    try:
        with open(fname, 'r') as f:
            data = json.load(f)
            for c in data.get('imported', []):
                c['batch'] = fname.split('_')[0]
                candidates.append(c)
    except:
        pass

# 去重（基于LinkedIn URL）
seen = set()
unique_candidates = []
for c in candidates:
    url = c.get('linkedin_url', '')
    if url and url not in seen:
        seen.add(url)
        unique_candidates.append(c)

# 按匹配分数排序
unique_candidates.sort(key=lambda x: x.get('match_score', 0), reverse=True)

# 生成CSV内容
csv_lines = [
    '姓名,职位,公司,地点,匹配分数,优先级,华人,专业背景,LinkedIn链接,来源批次'
]

for c in unique_candidates:
    name = c.get('name', '').replace(',', ' ')
    title = c.get('title', '').replace(',', ' ')
    company = c.get('company', '').replace(',', ' ')
    location = c.get('location', '').replace(',', ' ')
    score = c.get('match_score', 0)
    priority = c.get('priority', 'P1')
    is_chinese = '是' if c.get('is_chinese') else '否'
    background = (c.get('background', '') or c.get('expertise', '')).replace(',', ' ').replace('\n', ' ')
    linkedin = c.get('linkedin_url', '')
    batch = c.get('batch', '')
    
    csv_lines.append(f'"{name}","{title}","{company}","{location}",{score},{priority},{is_chinese},"{background}","{linkedin}",{batch}')

# 保存CSV
csv_content = '\n'.join(csv_lines)
output_file = '/tmp/candidates_report_20260325.csv'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(csv_content)

print(f"✅ 生成成功！")
print(f"📊 总候选人数量: {len(unique_candidates)}")
print(f"📁 文件保存至: {output_file}")
print(f"\n📈 统计信息:")

# 统计
p0_count = sum(1 for c in unique_candidates if c.get('priority') == 'P0')
chinese_count = sum(1 for c in unique_candidates if c.get('is_chinese'))
avg_score = sum(c.get('match_score', 0) for c in unique_candidates) / len(unique_candidates) if unique_candidates else 0

print(f"  - P0 优先级: {p0_count} 人")
print(f"  - 华人候选人: {chinese_count} 人 ({chinese_count/len(unique_candidates)*100:.1f}%)")
print(f"  - 平均匹配分数: {avg_score:.2f}")

# 按公司统计
from collections import Counter
companies = Counter(c.get('company', 'Unknown') for c in unique_candidates)
print(f"\n🏢 公司分布:")
for company, count in companies.most_common(10):
    print(f"  - {company}: {count} 人")
