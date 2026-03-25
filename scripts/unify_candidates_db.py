#!/usr/bin/env python3
"""
遍历所有数据目录，生成完整可靠的候选人数据集
排除: archive, profiles, cache, BrowserMetrics等浏览器数据
"""
import json
import os
import glob
from collections import defaultdict
from datetime import datetime

BASE_DIR = "/Users/cooga/.openclaw/workspace/Project/TalentIntel"
OUTPUT_FILE = "/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/unified_candidates_db.json"
CSV_OUTPUT = "/tmp/unified_candidates_report_20260325.csv"

# 排除的目录模式
EXCLUDE_PATTERNS = [
    'archive',
    'profiles',
    'Cache',
    'BrowserMetrics',
    'chrome',
    'leveldb',
    'Default',  # Chrome profile data
    'Blob',
    'blob_storage',
]

# 收集所有候选人
candidates_by_url = {}
data_sources = defaultdict(int)

def is_valid_json_file(filepath):
    """检查是否是有效的数据文件（非浏览器缓存等）"""
    path_lower = filepath.lower()
    for pattern in EXCLUDE_PATTERNS:
        if pattern.lower() in path_lower:
            return False
    return True

def extract_candidates_from_json(filepath):
    """从JSON文件中提取候选人列表"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ⚠️ 无法解析 {filepath}: {e}")
        return []
    
    candidates = []
    
    # 处理各种可能的JSON结构
    if isinstance(data, dict):
        # 结构1: { "candidates": [...] }
        if 'candidates' in data and isinstance(data['candidates'], list):
            candidates.extend(data['candidates'])
        # 结构2: { "imported": [...] }
        if 'imported' in data and isinstance(data['imported'], list):
            candidates.extend(data['imported'])
        # 结构3: { "chinese_candidates": [...] }
        if 'chinese_candidates' in data and isinstance(data['chinese_candidates'], list):
            candidates.extend(data['chinese_candidates'])
        # 结构4: 单个候选人对象
        if 'name' in data and 'linkedin_url' in data:
            candidates.append(data)
    elif isinstance(data, list):
        # 结构5: 直接是列表
        for item in data:
            if isinstance(item, dict) and 'name' in item:
                candidates.append(item)
    
    return candidates

def normalize_candidate(candidate, source_file):
    """标准化候选人数据格式"""
    if not isinstance(candidate, dict):
        return None
    
    # 必须有name和linkedin_url
    name = candidate.get('name', '').strip()
    linkedin_url = candidate.get('linkedin_url', candidate.get('url', '')).strip()
    
    if not name or not linkedin_url:
        return None
    
    # 标准化URL（移除跟踪参数）
    if '?' in linkedin_url:
        linkedin_url = linkedin_url.split('?')[0]
    
    # 提取source信息
    source = candidate.get('source', '')
    if not source:
        # 从文件路径推断
        if 'spacex' in source_file.lower():
            source = 'SpaceX X-Ray Search'
        elif 'research' in source_file.lower():
            source = 'Research X-Ray'
        elif 'xray' in source_file.lower():
            source = 'X-Ray Search'
        elif 'active' in source_file.lower():
            source = 'Active Pool'
        elif 'phase2' in source_file.lower():
            source = 'Phase 2'
        else:
            source = 'Unknown'
    
    return {
        'name': name,
        'title': candidate.get('title', candidate.get('headline', '')).strip(),
        'company': candidate.get('company', '').strip(),
        'location': candidate.get('location', '').strip(),
        'linkedin_url': linkedin_url,
        'match_score': float(candidate.get('match_score', candidate.get('score', 0)) or 0),
        'is_chinese': candidate.get('is_chinese', candidate.get('chinese', True)),
        'chinese_surname': candidate.get('chinese_surname', ''),
        'priority': candidate.get('priority', ''),
        'background': (candidate.get('background', '') or candidate.get('notes', '') or candidate.get('expertise', '')).strip(),
        'verified': candidate.get('verified', False),
        'verification_method': candidate.get('verification_method', ''),
        'source': source,
        'source_file': source_file,
        'imported_at': candidate.get('imported_at', candidate.get('timestamp', '')),
        'email': candidate.get('email', ''),
        'phone': candidate.get('phone', ''),
    }

print("🔍 扫描数据目录...")
print("=" * 60)

# 查找所有JSON文件
data_dir = os.path.join(BASE_DIR, 'data')
all_json_files = []

for root, dirs, files in os.walk(data_dir):
    # 跳过排除的目录
    dirs[:] = [d for d in dirs if not any(p.lower() in d.lower() for p in EXCLUDE_PATTERNS)]
    
    for file in files:
        if file.endswith('.json'):
            filepath = os.path.join(root, file)
            if is_valid_json_file(filepath):
                all_json_files.append(filepath)

print(f"找到 {len(all_json_files)} 个候选JSON文件\n")

# 处理每个文件
for filepath in sorted(all_json_files):
    rel_path = os.path.relpath(filepath, BASE_DIR)
    raw_candidates = extract_candidates_from_json(filepath)
    
    if raw_candidates:
        print(f"📄 {rel_path}: {len(raw_candidates)} 人")
        
        for candidate in raw_candidates:
            normalized = normalize_candidate(candidate, rel_path)
            if normalized:
                url = normalized['linkedin_url']
                
                # 去重：如果URL已存在，保留评分更高的
                if url in candidates_by_url:
                    existing = candidates_by_url[url]
                    if normalized['match_score'] > existing['match_score']:
                        print(f"   🔄 更新: {normalized['name']} (评分 {existing['match_score']} → {normalized['match_score']})")
                        candidates_by_url[url] = normalized
                else:
                    candidates_by_url[url] = normalized

print("\n" + "=" * 60)

# 转换为列表并排序
candidates_list = list(candidates_by_url.values())
candidates_list.sort(key=lambda x: x['match_score'], reverse=True)

# 统计信息
print("📊 数据合并统计:")
print(f"  总候选人: {len(candidates_list)}")

chinese_count = sum(1 for c in candidates_list if c.get('is_chinese'))
print(f"  华人候选人: {chinese_count} ({chinese_count/len(candidates_list)*100:.1f}%)")

verified_count = sum(1 for c in candidates_list if c.get('verified'))
print(f"  已验证: {verified_count} ({verified_count/len(candidates_list)*100:.1f}%)")

p0_count = sum(1 for c in candidates_list if c.get('priority') == 'P0')
print(f"  P0优先级: {p0_count}")

# 按公司统计
from collections import Counter
companies = Counter(c.get('company', 'Unknown') for c in candidates_list if c.get('company'))
print(f"\n🏢 Top 10 公司分布:")
for company, count in companies.most_common(10):
    print(f"  - {company}: {count} 人")

# 按source统计
sources = Counter(c.get('source', 'Unknown') for c in candidates_list)
print(f"\n📁 数据来源分布:")
for source, count in sources.most_common():
    print(f"  - {source}: {count} 人")

# 保存统一数据库
unified_db = {
    'timestamp': datetime.now().isoformat(),
    'total_candidates': len(candidates_list),
    'chinese_count': chinese_count,
    'verified_count': verified_count,
    'p0_count': p0_count,
    'candidates': candidates_list
}

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(unified_db, f, indent=2, ensure_ascii=False)

print(f"\n💾 统一数据库已保存:")
print(f"  📁 {OUTPUT_FILE}")
print(f"  📝 共 {len(candidates_list)} 人")

# 生成CSV
csv_lines = [
    '姓名,职位,公司,地点,匹配分数,优先级,华人,中文姓氏,专业背景,LinkedIn链接,数据来源,已验证'
]

for c in candidates_list:
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

csv_content = '\n'.join(csv_lines)
with open(CSV_OUTPUT, 'w', encoding='utf-8') as f:
    f.write(csv_content)

print(f"  📊 CSV报告已保存: {CSV_OUTPUT}")

# 显示前10名高分候选人
print("\n⭐ Top 10 高分候选人:")
print("-" * 100)
for i, c in enumerate(candidates_list[:10], 1):
    name = c.get('name', '')[:25]
    company = c.get('company', '')[:20]
    score = c.get('match_score', 0)
    priority = c.get('priority', 'P?')
    print(f"{i:2}. {name:25} | {company:20} | 匹配度:{score:.2f} | {priority}")

print("\n✅ 完成!")
