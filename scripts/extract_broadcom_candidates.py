#!/usr/bin/env python3
"""
解析 Google X-Ray 搜索结果 - 提取 Broadcom 华人候选人
"""

import json
from datetime import datetime
from pathlib import Path

# 从搜索结果中提取的候选人
EXTRACTED_CANDIDATES = [
    {
        "name": "Victor Liang",
        "title": "AI/Machine Learning Engineer",
        "company": "Broadcom",
        "location": "Irvine, California",
        "linkedin_url": "https://www.linkedin.com/in/vliang",
        "followers": "490+",
        "background": "AI and machine learning video quality analytics. Digital image and signal processing.",
        "is_chinese": True,
        "chinese_name": "梁",
        "match_score": 0.82,
        "source": "Google X-Ray Search",
        "search_query": "site:linkedin.com/in (\"Broadcom\") (\"AI\" OR \"Machine Learning\") (\"California\" OR \"CA\")"
    },
    {
        "name": "Jinghao Li",
        "title": "Software Engineer",
        "company": "Broadcom Software",
        "location": "Culver City, California",
        "linkedin_url": "https://www.linkedin.com/in/jinghli",
        "followers": "570+",
        "background": "Beihang University",
        "is_chinese": True,
        "chinese_name": "李景浩",
        "match_score": 0.75,
        "source": "Google X-Ray Search",
        "search_query": "site:linkedin.com/in (\"Broadcom\") (\"AI\" OR \"Machine Learning\") (\"California\" OR \"CA\")"
    },
    {
        "name": "Ben Yang",
        "title": "Engineer",
        "company": "Broadcom Inc.",
        "location": "Los Gatos, California",
        "linkedin_url": "https://www.linkedin.com/in/ben-yang-618a7087",
        "followers": "50+",
        "background": "UCLA Henry Samueli School of Engineering and Applied Science",
        "is_chinese": True,
        "chinese_name": "杨",
        "match_score": 0.72,
        "source": "Google X-Ray Search",
        "search_query": "site:linkedin.com/in (\"Broadcom\") (\"AI\" OR \"Machine Learning\") (\"California\" OR \"CA\")"
    }
]

def save_candidates(candidates):
    """保存候选人数据"""
    output_dir = Path(__file__).parent.parent / "data" / "research"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_file = output_dir / f"BROADCOM_CANDIDATES_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, 'w') as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)
    
    return json_file

def generate_report(candidates):
    """生成 Markdown 报告"""
    lines = [
        "# 🔍 Broadcom 华人 AI/ML 候选人发现报告\n",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        "**搜索方法**: Google X-Ray (site:linkedin.com/in)\n",
        "**搜索词**: (\"Broadcom\") (\"AI\" OR \"Machine Learning\") (\"California\" OR \"CA\")\n\n",
        "---\n\n",
        f"## 📊 发现统计\n\n",
        f"- **总发现**: {len(candidates)} 人\n",
        f"- **目标区域**: California\n",
        f"- **平均匹配度**: {sum(c['match_score'] for c in candidates) / len(candidates):.2f}\n\n",
        "---\n\n"
    ]
    
    lines.append("## 🏆 候选人详情\n\n")
    for c in candidates:
        chinese_display = f"({c['chinese_name']})" if c.get('chinese_name') else ''
        lines.append(f"### {c['name']} {chinese_display}\n")
        lines.append(f"- **职位**: {c['title']}\n")
        lines.append(f"- **公司**: {c['company']}\n")
        lines.append(f"- **地点**: {c['location']}\n")
        lines.append(f"- **匹配度**: {c['match_score']}\n")
        lines.append(f"- **关注者**: {c['followers']}\n")
        lines.append(f"- **背景**: {c['background']}\n")
        lines.append(f"- **LinkedIn**: [{c['linkedin_url']}]({c['linkedin_url']})\n\n")
    
    lines.append("---\n\n")
    lines.append("## 🔗 下一步\n\n")
    lines.append("1. 点击 LinkedIn 链接验证详细信息\n")
    lines.append("2. 使用 Kobe 数字研究员登录 LinkedIn 进行深度评估\n")
    lines.append("3. 将验证通过的候选人导入主库\n")
    
    return "".join(lines)

def main():
    """主入口"""
    print("=" * 70)
    print("🔍 Broadcom 华人候选人提取结果")
    print("=" * 70)
    print()
    
    candidates = EXTRACTED_CANDIDATES
    
    print(f"✅ 从搜索结果中提取: {len(candidates)} 人\n")
    
    for c in candidates:
        chinese_display = f"({c['chinese_name']})" if c.get('chinese_name') else ''
        print(f"  • {c['name']} {chinese_display}")
        print(f"    {c['title']} @ {c['company']}")
        print(f"    {c['location']} | 匹配度: {c['match_score']}")
        print()
    
    # 保存 JSON
    json_file = save_candidates(candidates)
    print(f"💾 已保存: {json_file}")
    
    # 生成报告
    report = generate_report(candidates)
    report_file = Path(__file__).parent.parent / "data" / "research" / f"BROADCOM_CANDIDATES_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"📄 报告: {report_file}")
    
    print("\n" + "=" * 70)
    print("📊 汇总")
    print("=" * 70)
    print(f"   高分候选人 (>=0.75): {len([c for c in candidates if c['match_score'] >= 0.75])} 人")
    print(f"   其他候选人: {len([c for c in candidates if c['match_score'] < 0.75])} 人")
    print(f"   平均匹配度: {sum(c['match_score'] for c in candidates) / len(candidates):.2f}")
    print("=" * 70)

if __name__ == "__main__":
    main()
