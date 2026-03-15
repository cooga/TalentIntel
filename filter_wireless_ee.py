#!/usr/bin/env python3
"""
从现有TalentIntel数据中筛选无线通信/EE背景人才
"""
import json
from pathlib import Path
from datetime import datetime

# 无线通信关键词
wireless_keywords = [
    "wireless", "5g", "6g", "communication", "mimo", "ofdm", "signal",
    "radio", "rf", "mmwave", "antenna", "modem", "baseband", "telecom",
    "channel", "propagation", "spectrum", "cellular", "lte", "nr", "wifi",
    "bluetooth", "satellite", "starlink", "gnss", "gps", "sensing"
]

# EE 专业关键词
ee_keywords = [
    "electrical", "electronics", "ee", "circuit", "ic", "chip",
    "semiconductor", "hardware", "embedded", "vlsi", "analog", "digital",
    "electrical engineering", "electronic engineering"
]

def has_wireless_background(candidate):
    """检查是否有无线通信背景"""
    text = json.dumps(candidate).lower()
    return any(kw in text for kw in wireless_keywords)

def has_ee_background(candidate):
    """检查是否有EE背景"""
    text = json.dumps(candidate).lower()
    return any(kw in text for kw in ee_keywords)

def is_chinese_name(name):
    """判断是否为华人姓名"""
    if not name:
        return False
    chinese_surnames = ['wang', 'liu', 'li', 'zhang', 'chen', 'yang', 'huang', 'zhao', 'wu', 'zhou',
                        'xu', 'sun', 'ma', 'zhu', 'hu', 'guo', 'lin', 'he', 'gao', 'zheng', 'liang',
                        'xie', 'song', 'tang', 'deng', 'han', 'feng', 'cao', 'peng', 'zeng', 'xiao',
                        'tian', 'dong', 'yuan', 'pan', 'yu', 'lu', 'jiang', 'cai', 'jia', 'ding', 'wei']
    name_lower = name.lower()
    words = name_lower.split()

    # 排除常见非华人姓氏
    exclude = ['nguyen', 'park', 'kim', 'choi', 'singh', 'patel', 'gupta', 'kumar']
    if any(e in name_lower for e in exclude):
        return False

    return any(s in words for s in chinese_surnames)

def main():
    # 加载 aggregated_summary.json
    summary_path = Path("data/findings/aggregated_summary.json")
    if not summary_path.exists():
        print("❌ 找不到 aggregated_summary.json")
        return

    with open(summary_path) as f:
        data = json.load(f)

    high_score_candidates = data.get("high_score_candidates", [])
    print(f"📊 高分候选人总数: {len(high_score_candidates)}")

    # 筛选有无线/EE背景的候选人
    wireless_candidates = []
    for c in high_score_candidates:
        profile = c.get("profile", {})
        name = profile.get("name", "")
        evaluation = c.get("evaluation", {})

        has_wireless = has_wireless_background(c)
        has_ee = has_ee_background(c)

        if has_wireless or has_ee:
            wireless_candidates.append({
                "name": name,
                "url": c.get("url", ""),
                "current_role": evaluation.get("basic_info", {}).get("current_role", ""),
                "current_company": evaluation.get("basic_info", {}).get("current_company", ""),
                "has_wireless_bg": has_wireless,
                "has_ee_bg": has_ee,
                "match_score": c.get("match_score", 0),
                "is_chinese": is_chinese_name(name),
                "wireless_expertise": evaluation.get("wireless_expertise", {}),
                "ai_expertise": evaluation.get("ai_expertise", {})
            })

    # 按分数排序
    wireless_candidates.sort(key=lambda x: x["match_score"], reverse=True)

    # 统计
    chinese_candidates = [c for c in wireless_candidates if c["is_chinese"]]
    wireless_only = [c for c in wireless_candidates if c["has_wireless_bg"] and not c["has_ee_bg"]]
    ee_only = [c for c in wireless_candidates if c["has_ee_bg"] and not c["has_wireless_bg"]]
    both_bg = [c for c in wireless_candidates if c["has_wireless_bg"] and c["has_ee_bg"]]

    print(f"\n📡 无线通信/EE背景候选人: {len(wireless_candidates)} 人")
    print(f"   - 华人候选人: {len(chinese_candidates)} 人")
    print(f"   - 纯无线背景: {len(wireless_only)} 人")
    print(f"   - 纯EE背景: {len(ee_only)} 人")
    print(f"   - 双背景: {len(both_bg)} 人")

    # 保存结果
    output_dir = Path("data/findings/2026-03-08")
    output_dir.mkdir(parents=True, exist_ok=True)

    result_file = output_dir / "wireless_ee_from_existing.json"
    with open(result_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "source": "existing_database",
            "total_found": len(wireless_candidates),
            "chinese_count": len(chinese_candidates),
            "statistics": {
                "wireless_only": len(wireless_only),
                "ee_only": len(ee_only),
                "both_bg": len(both_bg)
            },
            "candidates": wireless_candidates[:25]  # 取前25人
        }, f, indent=2)

    # 生成 Markdown 报告
    md_file = output_dir / "wireless_ee_from_existing.md"
    with open(md_file, "w") as f:
        f.write("# 无线通信/EE 背景人才报告 (基于现有数据)\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**数据来源**: TalentIntel 现有数据库\n\n")
        f.write("## 统计概览\n\n")
        f.write(f"- **总候选人**: {len(wireless_candidates)} 人\n")
        f.write(f"- **华人候选人**: {len(chinese_candidates)} 人\n")
        f.write(f"- **纯无线背景**: {len(wireless_only)} 人\n")
        f.write(f"- **纯EE背景**: {len(ee_only)} 人\n")
        f.write(f"- **双背景**: {len(both_bg)} 人\n\n")

        f.write("## 候选人列表 (TOP 20)\n\n")
        for i, c in enumerate(wireless_candidates[:20], 1):
            bg_type = ""
            if c["has_wireless_bg"] and c["has_ee_bg"]:
                bg_type = "[无线+EE]"
            elif c["has_wireless_bg"]:
                bg_type = "[无线]"
            else:
                bg_type = "[EE]"

            chinese_tag = "🇨🇳 " if c["is_chinese"] else ""

            f.write(f"### {i}. {chinese_tag}{c['name']} {bg_type}\n\n")
            f.write(f"- **当前职位**: {c['current_role']}\n")
            f.write(f"- **公司**: {c['current_company']}\n")
            f.write(f"- **匹配分数**: {c['match_score']}\n")
            f.write(f"- **LinkedIn**: {c['url']}\n")
            f.write(f"- **无线背景**: {'✅' if c['has_wireless_bg'] else '❌'}\n")
            f.write(f"- **EE背景**: {'✅' if c['has_ee_bg'] else '❌'}\n\n")

    print(f"\n✅ 结果已保存:")
    print(f"   JSON: {result_file}")
    print(f"   Markdown: {md_file}")

    # 显示 TOP 10
    print("\n🏆 TOP 10 候选人:")
    for i, c in enumerate(wireless_candidates[:10], 1):
        bg = "无线+EE" if c["has_wireless_bg"] and c["has_ee_bg"] else "无线" if c["has_wireless_bg"] else "EE"
        chinese = "🇨🇳" if c["is_chinese"] else ""
        print(f"{i}. {chinese} {c['name']} ({bg}) - {c['current_company']} - 分数: {c['match_score']}")

    return len(wireless_candidates)

if __name__ == "__main__":
    count = main()
    print(f"\n📌 现有数据库中找到 {count} 位无线通信/EE背景候选人")
    if count < 20:
        print(f"⚠️ 距离目标 20 人还差 {20 - count} 人，建议启动补充搜索")
