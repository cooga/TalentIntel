#!/usr/bin/env python3
"""
北美大厂华人AI+无线专家精确筛选
目标: 真正在北美工作的华人专家
"""
import json
from pathlib import Path
from datetime import datetime

# 精确定位的华人姓名特征（常见华人姓氏拼音）
CHINESE_SURNAMES = {
    'chen', 'wang', 'li', 'liu', 'zhang', 'zhao', 'yang', 'wu', 'zhou', 
    'huang', 'xu', 'sun', 'hu', 'ma', 'guo', 'he', 'zheng', 'xie', 'lin',
    'tang', 'deng', 'ye', 'cheng', 'cai', 'cao', 'dai', 'ding', 'dong', 
    'du', 'duan', 'fan', 'fang', 'fu', 'gao', 'ge', 'gong', 'guan', 'han',
    'hao', 'hong', 'hou', 'jiang', 'jin', 'kang', 'kong', 'lai', 'lan', 
    'lei', 'liang', 'liao', 'lu', 'luo', 'mao', 'meng', 'miao', 'ni', 
    'ning', 'pan', 'peng', 'qi', 'qian', 'qiao', 'qin', 'qiu', 'qu',
    'ren', 'rong', 'shao', 'shen', 'shi', 'song', 'su', 'tan', 'tao', 
    'tian', 'wan', 'wei', 'wen', 'weng', 'xia', 'xiang', 'xiao', 'xin', 
    'xing', 'xiong', 'xue', 'yan', 'yao', 'yi', 'yin', 'ying', 'you', 
    'yu', 'yuan', 'zeng', 'zhan', 'zhuang', 'zhuo', 'zong', 'zu', 'zuo'
}

# 北美地区关键词
NORTH_AMERICA = ['united states', 'usa', 'california', 'ca', 'texas', 'tx', 
                 'new york', 'ny', 'washington', 'wa', 'massachusetts', 'ma',
                 'illinois', 'il', 'colorado', 'co', 'north carolina', 'nc',
                 'oregon', 'or', 'arizona', 'az', 'florida', 'fl', 'georgia', 'ga',
                 'canada', 'toronto', 'vancouver', 'montreal', 'ottawa',
                 'palo alto', 'san francisco', 'san jose', 'seattle', 'austin',
                 'boston', 'new york city', 'mountain view', 'sunnyvale', 'cupertino',
                 'santa clara', 'menlo park', 'redmond', 'bellevue', 'san diego']

# 北美大厂
BIG_TECH = ['google', 'meta', 'facebook', 'nvidia', 'apple', 'microsoft', 'amazon', 
            'aws', 'qualcomm', 'intel', 'broadcom', 'cisco', 'amd', 'tesla', 
            'oracle', 'ibm', 'marvell', 'texas instruments', 'ericsson', 'samsung']

def is_chinese_name(name):
    """精确判断是否为华人姓名"""
    if not name or name == 'N/A':
        return False
    
    name_lower = name.lower()
    # 将名字拆分为单词
    words = name_lower.replace('.', ' ').replace('-', ' ').split()
    
    # 检查姓氏是否匹配（通常是第一个或最后一个单词）
    for word in words:
        if word in CHINESE_SURNAMES:
            return True
    
    return False

def is_north_america(location):
    """判断是否北美地区"""
    if not location:
        return False
    location_lower = location.lower()
    return any(loc in location_lower for loc in NORTH_AMERICA)

def extract_company(text):
    """提取公司信息"""
    if not text:
        return 'Unknown'
    text_lower = text.lower()
    for company in BIG_TECH:
        if company in text_lower:
            return company.title()
    return text.split(',')[0] if ',' in text else text

def load_and_filter_candidates(filepath):
    """加载并精确筛选候选人"""
    with open(filepath) as f:
        data = json.load(f)
    
    candidates = data.get('candidates', [])
    chinese_na_candidates = []
    
    for c in candidates:
        name = c.get('name', '')
        evaluation = c.get('evaluation', {})
        basic_info = evaluation.get('basic_info', {})
        location = basic_info.get('location', '')
        company = basic_info.get('current_company', '')
        
        # 筛选条件:
        # 1. 华人姓名
        # 2. 在北美工作
        # 3. 高匹配度 (≥0.7)
        if is_chinese_name(name) and is_north_america(location):
            if c.get('match_score', 0) >= 0.7:
                chinese_na_candidates.append({
                    'name': name,
                    'url': c.get('url', ''),
                    'match_score': c.get('match_score', 0),
                    'company': company,
                    'role': basic_info.get('current_role', ''),
                    'location': location,
                    'ai_domains': evaluation.get('ai_expertise', {}).get('domains', []),
                    'wireless_domains': evaluation.get('wireless_expertise', {}).get('domains', []),
                    'evaluation': evaluation
                })
    
    return chinese_na_candidates

def generate_report(candidates):
    """生成详细报告"""
    candidates = sorted(candidates, key=lambda x: x['match_score'], reverse=True)
    
    lines = []
    lines.append("=" * 85)
    lines.append("🇺🇸 北美大厂华人AI+无线通信专家检索报告")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 85)
    lines.append("")
    
    # 统计
    lines.append("📊 统计摘要")
    lines.append("-" * 85)
    lines.append(f"符合条件的候选人: {len(candidates)}")
    
    # 公司分布
    company_dist = {}
    for c in candidates:
        comp = c.get('company', 'Unknown')
        company_dist[comp] = company_dist.get(comp, 0) + 1
    
    lines.append("\n🏢 公司分布")
    lines.append("-" * 85)
    for comp, count in sorted(company_dist.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"  {comp}: {count}人")
    
    # 地点分布
    location_dist = {}
    for c in candidates:
        loc = c.get('location', 'Unknown')
        # 简化地点名称
        loc_short = loc.split(',')[0] if ',' in loc else loc
        location_dist[loc_short] = location_dist.get(loc_short, 0) + 1
    
    lines.append("\n🌎 地点分布")
    lines.append("-" * 85)
    for loc, count in sorted(location_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
        lines.append(f"  {loc}: {count}人")
    
    # 详细列表
    lines.append("\n" + "=" * 85)
    lines.append("🏆 候选人详细列表 (按匹配度排序)")
    lines.append("=" * 85)
    lines.append("")
    
    for i, c in enumerate(candidates, 1):
        lines.append(f"【{i}】{c['name']}")
        lines.append(f"  ⭐ 匹配度: {c['match_score']:.2f}")
        lines.append(f"  🏢 公司: {c['company']}")
        lines.append(f"  💼 职位: {c['role']}")
        lines.append(f"  📍 地点: {c['location']}")
        lines.append(f"  🔗 LinkedIn: {c['url']}")
        
        if c['ai_domains']:
            lines.append(f"  🤖 AI专长: {', '.join(c['ai_domains'])}")
        if c['wireless_domains']:
            lines.append(f"  📡 无线专长: {', '.join(c['wireless_domains'])}")
        
        lines.append("")
    
    return '\n'.join(lines)

def main():
    input_file = Path("data/findings/2026-03-04/candidates_batch_144525.json")
    
    if not input_file.exists():
        print(f"❌ 找不到文件: {input_file}")
        return
    
    print("🔍 筛选北美大厂华人AI+无线专家...")
    print("-" * 60)
    
    candidates = load_and_filter_candidates(input_file)
    
    print(f"✅ 找到 {len(candidates)} 位符合条件的候选人")
    
    if not candidates:
        print("\n⚠️ 没有找到符合条件的候选人")
        print("建议: 扩展搜索范围或调整筛选条件")
        return
    
    # 生成报告
    report = generate_report(candidates)
    
    # 保存报告
    output_dir = Path("data/findings/2026-03-04")
    timestamp = datetime.now().strftime("%H%M%S")
    
    report_file = output_dir / f"NA_chinese_talent_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 保存JSON
    json_file = output_dir / f"NA_chinese_talent_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "count": len(candidates),
            "candidates": candidates
        }, f, ensure_ascii=False, indent=2)
    
    # 打印报告
    print("\n" + report)
    
    print(f"\n💾 报告已保存: {report_file}")
    print(f"💾 数据已保存: {json_file}")

if __name__ == "__main__":
    main()
