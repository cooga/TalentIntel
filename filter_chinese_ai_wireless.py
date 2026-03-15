#!/usr/bin/env python3
"""
AI + 海外华人 + 无线背景人才筛选
目标：20人，工作3年以上加分
"""
import json
from pathlib import Path
from datetime import datetime
import re

# 无线通信关键词
wireless_keywords = [
    "wireless", "5g", "6g", "communication", "mimo", "ofdm", "signal",
    "radio", "rf", "mmwave", "antenna", "modem", "baseband", "telecom",
    "channel", "propagation", "spectrum", "cellular", "lte", "nr", "wifi",
    "bluetooth", "satellite", "starlink", "gnss", "gps", "sensing"
]

# AI关键词
ai_keywords = [
    "ai", "machine learning", "deep learning", "neural", "artificial intelligence",
    "ml", "data scientist", "algorithm", "research scientist", "llm", "genai"
]

def has_wireless_background(candidate):
    """检查是否有无线通信背景"""
    text = json.dumps(candidate).lower()
    return any(kw in text for kw in wireless_keywords)

def has_ai_background(candidate):
    """检查是否有AI背景"""
    text = json.dumps(candidate).lower()
    return any(kw in text for kw in ai_keywords)

def is_chinese_name(name):
    """判断是否为华人姓名 - 增强版"""
    if not name:
        return False

    name_lower = name.lower()
    words = name_lower.split()

    # 常见华人姓氏（拼音）
    chinese_surnames = [
        'wang', 'liu', 'li', 'zhang', 'chen', 'yang', 'huang', 'zhao', 'wu', 'zhou',
        'xu', 'sun', 'ma', 'zhu', 'hu', 'guo', 'lin', 'he', 'gao', 'zheng', 'liang',
        'xie', 'song', 'tang', 'deng', 'han', 'feng', 'cao', 'peng', 'zeng', 'xiao',
        'tian', 'dong', 'yuan', 'pan', 'yu', 'lu', 'jiang', 'cai', 'jia', 'ding', 'wei',
        'shen', 'fang', 'jiang', 'tan', 'fan', 'jin', 'qian', 'kong', 'bai', 'shao',
        'qin', 'zou', 'xiong', 'meng', 'hao', 'gong', 'bai', 'wan', 'duan', 'lai',
        'yin', 'shi', 'long', 'wan', 'gu', 'kang', 'mao', 'qiu', 'shao', 'wu'
    ]

    # 排除常见非华人姓氏
    exclude = ['nguyen', 'park', 'kim', 'choi', 'singh', 'patel', 'gupta', 'kumar',
               'tran', 'le', 'pham', 'truong', 'vo', 'vu', 'ngo', 'hoang']
    if any(e in name_lower for e in exclude):
        return False

    # 检查是否包含华人姓氏
    has_chinese_surname = any(s in words for s in chinese_surnames)

    # 检查是否包含中文特征（如"Dr. "后面跟着的拼音组合）
    # 如 "Wang Wei", "Li Ming" 等常见组合
    if len(words) >= 2:
        first_word = words[0]
        if first_word in chinese_surnames:
            return True

    return has_chinese_surname

def estimate_experience_years(experience_list):
    """估算工作年限"""
    if not experience_list:
        return 0

    total_years = 0
    for exp in experience_list:
        text = exp.get("text", "")

        # 匹配 "X yrs Y mos" 格式
        year_match = re.search(r'(\d+)\s*yrs?', text, re.IGNORECASE)
        month_match = re.search(r'(\d+)\s*mos?', text, re.IGNORECASE)

        years = int(year_match.group(1)) if year_match else 0
        months = int(month_match.group(1)) if month_match else 0

        total_years += years + months / 12

    return round(total_years, 1)

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

    # 筛选 AI + 华人 + 无线背景
    qualified_candidates = []

    for c in high_score_candidates:
        profile = c.get("profile", {})
        name = profile.get("name", "")
        evaluation = c.get("evaluation", {})
        experience = profile.get("experience", [])

        # 检查华人姓名
        is_chinese = is_chinese_name(name)

        # 检查AI和无线背景
        has_wireless = has_wireless_background(c)
        has_ai = has_ai_background(c)

        if is_chinese and has_wireless and has_ai:
            # 计算工作年限
            exp_years = estimate_experience_years(experience)

            qualified_candidates.append({
                "name": name,
                "url": c.get("url", ""),
                "current_role": evaluation.get("basic_info", {}).get("current_role", ""),
                "current_company": evaluation.get("basic_info", {}).get("current_company", ""),
                "location": evaluation.get("basic_info", {}).get("location", ""),
                "education": evaluation.get("basic_info", {}).get("education", ""),
                "match_score": c.get("match_score", 0),
                "experience_years": exp_years,
                "has_3plus_years": exp_years >= 3,
                "wireless_expertise": evaluation.get("wireless_expertise", {}),
                "ai_expertise": evaluation.get("ai_expertise", {}),
                "experience_snippet": experience[:2] if experience else []
            })

    # 按工作年限和匹配分数排序（3年以上优先，然后按分数）
    qualified_candidates.sort(key=lambda x: (x["has_3plus_years"], x["match_score"]), reverse=True)

    # 取前20人
    final_candidates = qualified_candidates[:20]

    # 统计
    with_3plus = [c for c in final_candidates if c["has_3plus_years"]]
    less_than_3 = [c for c in final_candidates if not c["has_3plus_years"]]

    print(f"\n🇨🇳 AI + 海外华人 + 无线背景候选人: {len(final_candidates)} / 20 目标")
    print(f"   - 3年以上经验: {len(with_3plus)} 人 ⭐")
    print(f"   - 少于3年: {len(less_than_3)} 人")

    # 保存结果
    output_dir = Path("data/findings/2026-03-08")
    output_dir.mkdir(parents=True, exist_ok=True)

    result_file = output_dir / "chinese_ai_wireless_candidates.json"
    with open(result_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "target": "AI + 海外华人 + 无线背景",
            "target_count": 20,
            "found_candidates": len(final_candidates),
            "with_3plus_years": len(with_3plus),
            "less_than_3_years": len(less_than_3),
            "candidates": final_candidates
        }, f, indent=2)

    # 生成 Markdown 报告
    md_file = output_dir / "chinese_ai_wireless_candidates.md"
    with open(md_file, "w") as f:
        f.write("# AI + 海外华人 + 无线背景人才报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**筛选条件**: AI + 海外华人 + 无线通信背景\n\n")
        f.write(f"**目标人数**: 20人\n\n")
        f.write("## 统计概览\n\n")
        f.write(f"- **找到候选人**: {len(final_candidates)} 人\n")
        f.write(f"- **3年以上经验**: {len(with_3plus)} 人 ⭐\n")
        f.write(f"- **少于3年经验**: {len(less_than_3)} 人\n\n")

        if with_3plus:
            f.write("## ⭐ 3年以上经验候选人\n\n")
            for i, c in enumerate(with_3plus, 1):
                f.write(f"### {i}. {c['name']}\n\n")
                f.write(f"- **当前职位**: {c['current_role']}\n")
                f.write(f"- **公司**: {c['current_company']}\n")
                f.write(f"- **地点**: {c['location']}\n")
                f.write(f"- **教育背景**: {c['education']}\n")
                f.write(f"- **估算工作年限**: {c['experience_years']} 年\n")
                f.write(f"- **匹配分数**: {c['match_score']}\n")
                f.write(f"- **LinkedIn**: {c['url']}\n")

                # AI 专长
                ai_exp = c.get('ai_expertise', {})
                if ai_exp:
                    f.write(f"- **AI 专长**: {', '.join(ai_exp.get('domains', []))}\n")

                # 无线专长
                wireless_exp = c.get('wireless_expertise', {})
                if wireless_exp:
                    f.write(f"- **无线专长**: {', '.join(wireless_exp.get('domains', []))}\n")

                f.write("\n")

        if less_than_3:
            f.write("## 📌 少于3年经验候选人\n\n")
            for i, c in enumerate(less_than_3, 1):
                f.write(f"### {i}. {c['name']}\n\n")
                f.write(f"- **当前职位**: {c['current_role']}\n")
                f.write(f"- **公司**: {c['current_company']}\n")
                f.write(f"- **地点**: {c['location']}\n")
                f.write(f"- **教育背景**: {c['education']}\n")
                f.write(f"- **估算工作年限**: {c['experience_years']} 年\n")
                f.write(f"- **匹配分数**: {c['match_score']}\n")
                f.write(f"- **LinkedIn**: {c['url']}\n\n")

    print(f"\n✅ 结果已保存:")
    print(f"   JSON: {result_file}")
    print(f"   Markdown: {md_file}")

    # 显示候选人列表
    print("\n🏆 候选人列表:")
    for i, c in enumerate(final_candidates, 1):
        exp_badge = "⭐" if c["has_3plus_years"] else ""
        print(f"{i}. {c['name']} {exp_badge}")
        print(f"   {c['current_role']} @ {c['current_company']}")
        print(f"   年限: {c['experience_years']}年 | 分数: {c['match_score']}")

    # 如果不足20人，提示需要补充搜索
    if len(final_candidates) < 20:
        print(f"\n⚠️ 距离目标 20 人还差 {20 - len(final_candidates)} 人")
        print("建议启动华人候选人专项搜索")

    return len(final_candidates)

if __name__ == "__main__":
    count = main()
