#!/usr/bin/env python3
"""
华人AI+无线专家筛选和报告脚本
从现有数据中筛选并生成详细报告
"""
import json
from pathlib import Path
from datetime import datetime

# 常见华人姓氏（拼音）
CHINESE_SURNAMES = [
    'chen', 'wang', 'li', 'liu', 'zhang', 'zhao', 'lin', 'yang', 'wu', 'zhou', 
    'huang', 'xu', 'sun', 'hu', 'ma', 'guo', 'he', 'zheng', 'xie', 'song', 
    'tang', 'feng', 'deng', 'ye', 'cheng', 'cai', 'cao', 'chao', 'chai', 'chan',
    'dai', 'ding', 'dong', 'du', 'duan', 'fan', 'fang', 'fu', 'gao', 'ge',
    'gong', 'gu', 'guan', 'han', 'hang', 'hao', 'hong', 'hou', 'hua', 'hui',
    'jiang', 'jin', 'kang', 'kong', 'lai', 'lan', 'lei', 'liang', 'liao', 'lian',
    'lu', 'luo', 'lü', 'lv', 'mao', 'meng', 'miao', 'min', 'ni', 'ning',
    'ou', 'pan', 'peng', 'piao', 'qi', 'qian', 'qiao', 'qin', 'qiu', 'qu',
    'quan', 'ran', 'rao', 'ren', 'rong', 'ruan', 'shao', 'shen', 'shi', 'shu',
    'shui', 'si', 'su', 'sun', 'tai', 'tan', 'tao', 'tian', 'wan', 'wei',
    'wen', 'weng', 'xia', 'xiang', 'xiao', 'xin', 'xing', 'xiong', 'xiu', 'xue',
    'yan', 'yang', 'yao', 'ye', 'yi', 'yin', 'ying', 'yong', 'you', 'yu',
    'yuan', 'yue', 'yun', 'zang', 'zeng', 'zha', 'zhai', 'zhan', 'zhang', 'zhao',
    'zhe', 'zhen', 'zheng', 'zhi', 'zhong', 'zhou', 'zhu', 'zhuang', 'zhuo', 'zong',
    'zu', 'zuo'
]

# 北美大厂
BIG_TECH = ['google', 'meta', 'facebook', 'nvidia', 'apple', 'microsoft', 'amazon', 
            'qualcomm', 'intel', 'broadcom', 'cisco', 'amd', 'tesla', 'oracle', 'ibm',
            'samsung', 'marvell', 'ti', 'texas instruments', 'ericsson', 'nokia']

def is_chinese_name(name):
    """判断是否为华人姓名"""
    if not name:
        return False
    name_lower = name.lower()
    # 检查是否包含华人姓氏作为独立单词
    for surname in CHINESE_SURNAMES:
        # 检查姓氏是否作为单词边界出现
        if f' {surname}' in name_lower or name_lower.startswith(surname + ' '):
            return True
    return False

def extract_from_bigtech(text):
    """提取大厂名称"""
    text_lower = text.lower()
    found = []
    for company in BIG_TECH:
        if company in text_lower:
            found.append(company.title())
    return list(set(found))

def load_candidates(filepath):
    """加载候选人数据"""
    with open(filepath) as f:
        data = json.load(f)
    return data.get('candidates', [])

def filter_chinese_candidates(candidates):
    """筛选华人候选人"""
    chinese = []
    for c in candidates:
        name = c.get('name', '')
        if is_chinese_name(name):
            chinese.append(c)
    return chinese

def generate_report(candidates, output_file):
    """生成详细报告"""
    # 按匹配度排序
    candidates = sorted(candidates, key=lambda x: x.get('match_score', 0), reverse=True)
    
    report = []
    report.append("=" * 80)
    report.append("北美大厂华人AI+无线通信专家检索报告")
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    report.append("")
    report.append(f"📊 统计摘要")
    report.append("-" * 80)
    report.append(f"候选人总数: {len(candidates)}")
    
    high_score = [c for c in candidates if c.get('match_score', 0) >= 0.7]
    medium_score = [c for c in candidates if 0.5 <= c.get('match_score', 0) < 0.7]
    
    report.append(f"高匹配度(≥0.7): {len(high_score)}")
    report.append(f"中匹配度(0.5-0.7): {len(medium_score)}")
    report.append("")
    
    # 按公司分布
    company_dist = {}
    for c in candidates:
        eval_data = c.get('evaluation', {})
        company = eval_data.get('basic_info', {}).get('current_company', 'Unknown')
        company_dist[company] = company_dist.get(company, 0) + 1
    
    report.append("🏢 公司分布")
    report.append("-" * 80)
    for company, count in sorted(company_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
        report.append(f"  {company}: {count}")
    report.append("")
    
    # 详细列表
    report.append("🏆 候选人详细列表")
    report.append("-" * 80)
    report.append("")
    
    for i, c in enumerate(candidates, 1):
        name = c.get('name', 'N/A')
        url = c.get('url', 'N/A')
        score = c.get('match_score', 0)
        priority = c.get('priority', 'low')
        eval_data = c.get('evaluation', {})
        basic = eval_data.get('basic_info', {})
        
        report.append(f"【{i}】{name}")
        report.append(f"  匹配度: {score:.2f} | 优先级: {priority.upper()}")
        report.append(f"  LinkedIn: {url}")
        report.append(f"  职位: {basic.get('current_role', 'N/A')}")
        report.append(f"  公司: {basic.get('current_company', 'N/A')}")
        report.append(f"  地点: {basic.get('location', 'N/A')}")
        
        # AI专长
        ai_exp = eval_data.get('ai_expertise', {})
        if ai_exp:
            report.append(f"  AI专长: {', '.join(ai_exp.get('domains', []))}")
        
        # 无线专长
        wireless_exp = eval_data.get('wireless_expertise', {})
        if wireless_exp:
            report.append(f"  无线专长: {', '.join(wireless_exp.get('domains', []))}")
        
        report.append("")
    
    # 保存报告
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    return '\n'.join(report)

def main():
    # 输入文件
    input_file = Path("data/findings/2026-03-04/candidates_batch_144525.json")
    
    if not input_file.exists():
        print(f"❌ 找不到文件: {input_file}")
        return
    
    # 加载数据
    print("📂 加载候选人数据...")
    candidates = load_candidates(input_file)
    print(f"   总计: {len(candidates)} 位候选人")
    
    # 筛选华人
    print("🔍 筛选华人候选人...")
    chinese_candidates = filter_chinese_candidates(candidates)
    print(f"   找到: {len(chinese_candidates)} 位华人候选人")
    
    # 生成报告
    output_dir = Path("data/findings/2026-03-04")
    output_file = output_dir / f"chinese_talent_report_{datetime.now().strftime('%H%M%S')}.txt"
    
    print("📝 生成报告...")
    report = generate_report(chinese_candidates, output_file)
    
    # 同时保存JSON
    json_file = output_dir / f"chinese_talent_{datetime.now().strftime('%H%M%S')}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "count": len(chinese_candidates),
            "candidates": chinese_candidates
        }, f, ensure_ascii=False, indent=2)
    
    # 打印摘要
    print("\n" + "=" * 80)
    print(report[:3000])  # 打印前3000字符
    print("...")
    print(f"\n💾 完整报告已保存: {output_file}")
    print(f"💾 JSON数据已保存: {json_file}")

if __name__ == "__main__":
    main()
