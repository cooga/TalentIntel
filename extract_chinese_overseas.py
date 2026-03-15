#!/usr/bin/env python3
"""
从 chinese_talent 文件中提取 AI + 海外华人 + 无线背景候选人
"""
import json
from pathlib import Path
from datetime import datetime

def is_chinese_name(name):
    """判断是否为华人姓名"""
    if not name:
        return False

    name_lower = name.lower()
    words = name_lower.split()

    chinese_surnames = [
        'wang', 'liu', 'li', 'zhang', 'chen', 'yang', 'huang', 'zhao', 'wu', 'zhou',
        'xu', 'sun', 'ma', 'zhu', 'hu', 'guo', 'lin', 'he', 'gao', 'zheng', 'liang',
        'xie', 'song', 'tang', 'deng', 'han', 'feng', 'cao', 'peng', 'zeng', 'xiao',
        'tian', 'dong', 'yuan', 'pan', 'yu', 'lu', 'jiang', 'cai', 'jia', 'ding', 'wei',
        'shen', 'fang', 'tan', 'fan', 'jin', 'qian', 'kong', 'bai', 'shao', 'ma'
    ]

    exclude = ['nguyen', 'park', 'kim', 'choi', 'singh', 'patel', 'gupta', 'kumar',
               'tran', 'le', 'pham', 'truong', 'vo', 'vu', 'ngo', 'hoang']
    if any(e in name_lower for e in exclude):
        return False

    return any(s in words for s in chinese_surnames)

def is_overseas(location):
    """判断是否在海外（非中国大陆）"""
    if not location:
        return True  # 默认认为是海外

    china_keywords = ['china', 'beijing', 'shanghai', 'shenzhen', 'guangzhou', 'hangzhou',
                      'beijing', 'mainland', '中国', '北京', '上海', '深圳', '广州', '杭州']
    location_lower = location.lower()

    return not any(kw in location_lower for kw in china_keywords)

def main():
    base_dir = Path("data/findings")

    # 加载所有候选人文件
    all_candidates = []

    # 从 chinese_talent_161829.json 加载
    file1 = base_dir / "2026-03-04" / "chinese_talent_161829.json"
    if file1.exists():
        with open(file1) as f:
            data = json.load(f)
            all_candidates.extend(data.get("candidates", []))

    # 从 NA_chinese_talent_161937.json 加载
    file2 = base_dir / "2026-03-04" / "NA_chinese_talent_161937.json"
    if file2.exists():
        with open(file2) as f:
            data = json.load(f)
            all_candidates.extend(data.get("candidates", []))

    print(f"📊 加载候选人总数: {len(all_candidates)}")

    # 筛选华人 + 海外 + AI + 无线
    qualified = []
    for c in all_candidates:
        name = c.get("name", "")
        location = c.get("location", "") or c.get("evaluation", {}).get("basic_info", {}).get("location", "")

        if is_chinese_name(name) and is_overseas(location):
            # 获取详细信息
            evaluation = c.get("evaluation", {})
            basic_info = evaluation.get("basic_info", {})

            qualified.append({
                "name": name,
                "url": c.get("url", ""),
                "current_role": basic_info.get("current_role", c.get("role", "")),
                "current_company": basic_info.get("current_company", c.get("company", "")),
                "location": location,
                "match_score": c.get("match_score", 0),
                "ai_domains": c.get("ai_domains", evaluation.get("ai_expertise", {}).get("domains", [])),
                "wireless_domains": c.get("wireless_domains", evaluation.get("wireless_expertise", {}).get("domains", [])),
                "is_overseas": True
            })

    # 按匹配分数排序
    qualified.sort(key=lambda x: x["match_score"], reverse=True)

    # 限制20人
    final = qualified[:20]

    # 按地区统计
    us_candidates = [c for c in final if 'ca' in c.get('location', '').lower() or 'us' in c.get('location', '').lower() or 'america' in c.get('location', '').lower()]
    asia_candidates = [c for c in final if any(x in c.get('location', '').lower() for x in ['singapore', 'taiwan', 'korea', 'japan', 'hong kong'])]
    europe_candidates = [c for c in final if any(x in c.get('location', '').lower() for x in ['uk', 'germany', 'france', 'sweden', 'switzerland', 'spain', 'italy', 'israel'])]

    print(f"\n🇨🇳 AI + 海外华人 + 无线背景候选人: {len(final)} 人")
    print(f"   - 北美: {len(us_candidates)} 人")
    print(f"   - 亚太: {len(asia_candidates)} 人")
    print(f"   - 欧洲: {len(europe_candidates)} 人")

    # 保存结果
    output_dir = base_dir / "2026-03-08"
    output_dir.mkdir(parents=True, exist_ok=True)

    result_file = output_dir / "chinese_overseas_ai_wireless.json"
    with open(result_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "target": "AI + 海外华人 + 无线背景",
            "target_count": 20,
            "found_candidates": len(final),
            "by_region": {
                "north_america": len(us_candidates),
                "asia_pacific": len(asia_candidates),
                "europe": len(europe_candidates)
            },
            "candidates": final
        }, f, indent=2)

    # 生成 Markdown 报告
    md_file = output_dir / "chinese_overseas_ai_wireless.md"
    with open(md_file, "w") as f:
        f.write("# AI + 海外华人 + 无线背景人才报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**筛选条件**: AI + 海外华人 + 无线通信背景\n\n")
        f.write(f"**目标人数**: 20人\n\n")
        f.write("## 统计概览\n\n")
        f.write(f"- **找到候选人**: {len(final)} 人\n")
        f.write(f"- **北美地区**: {len(us_candidates)} 人\n")
        f.write(f"- **亚太地区**: {len(asia_candidates)} 人\n")
        f.write(f"- **欧洲地区**: {len(europe_candidates)} 人\n\n")

        f.write("## ⭐ 候选人列表\n\n")
        for i, c in enumerate(final, 1):
            f.write(f"### {i}. {c['name']}\n\n")
            f.write(f"- **当前职位**: {c['current_role']}\n")
            f.write(f"- **公司/机构**: {c['current_company']}\n")
            f.write(f"- **地点**: {c['location']}\n")
            f.write(f"- **匹配分数**: {c['match_score']}\n")
            f.write(f"- **LinkedIn**: {c['url']}\n")

            if c.get('ai_domains'):
                f.write(f"- **AI 专长**: {', '.join(c['ai_domains'])}\n")
            if c.get('wireless_domains'):
                f.write(f"- **无线专长**: {', '.join(c['wireless_domains'])}\n")

            # 工作年限评估
            role_lower = c.get('current_role', '').lower()
            if any(k in role_lower for k in ['professor', 'director', 'principal', 'chief', 'senior']):
                f.write(f"- **经验评估**: 资深 (5年+) ⭐⭐⭐\n")
            elif any(k in role_lower for k in ['staff', 'lead', 'manager']):
                f.write(f"- **经验评估**: 中等 (3-5年) ⭐⭐\n")
            else:
                f.write(f"- **经验评估**: 初级 (1-3年) ⭐\n")

            f.write("\n")

    print(f"\n✅ 结果已保存:")
    print(f"   JSON: {result_file}")
    print(f"   Markdown: {md_file}")

    print("\n🏆 候选人列表:")
    for i, c in enumerate(final, 1):
        role_lower = c.get('current_role', '').lower()
        exp_badge = "⭐⭐⭐" if any(k in role_lower for k in ['professor', 'director', 'principal', 'chief']) else "⭐⭐" if any(k in role_lower for k in ['staff', 'lead', 'manager']) else "⭐"
        print(f"{i}. {c['name']} {exp_badge}")
        print(f"   {c['current_role']} @ {c['current_company']}")
        print(f"   地点: {c['location']} | 分数: {c['match_score']}")

    return len(final)

if __name__ == "__main__":
    count = main()
