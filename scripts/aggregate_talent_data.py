#!/usr/bin/env python3
"""
TalentIntel 数据汇总与进度报告生成器
整合所有候选人数据，生成进度报告
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import re


class TalentDataAggregator:
    """人才数据汇总器"""
    
    def __init__(self, base_dir: str = "/Users/cooga/.openclaw/workspace/Project/TalentIntel"):
        self.base_dir = Path(base_dir)
        self.findings_dir = self.base_dir / "data" / "findings"
        self.xray_dir = self.base_dir / "data" / "xray_campaigns"
        self.candidates = []
        self.target = 100  # 总目标：100个高分候选人
        self.chinese_target = 40  # 华人候选人目标：40人
        
    def load_all_candidates(self) -> List[Dict]:
        """加载所有候选人数据"""
        print("🔍 正在扫描候选人数据...")
        
        candidates = []
        
        # 1. 从 findings 目录加载
        if self.findings_dir.exists():
            for json_file in self.findings_dir.rglob("*.json"):
                if "summary" in json_file.name:
                    continue
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and "match_score" in data:
                            candidates.append({
                                **data,
                                "_source": json_file.name,
                                "_filepath": str(json_file)
                            })
                except Exception as e:
                    pass
        
        # 2. 去重（基于 URL）
        seen_urls = set()
        unique_candidates = []
        for c in candidates:
            url = c.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_candidates.append(c)
        
        self.candidates = unique_candidates
        print(f"✅ 已加载 {len(unique_candidates)} 个唯一候选人")
        return unique_candidates
    
    def categorize_candidates(self) -> Dict:
        """分类候选人"""
        high = []    # >= 0.7
        medium = []  # 0.5 - 0.7
        low = []     # < 0.5
        chinese_high = []  # 高分华人候选人
        
        for c in self.candidates:
            score = c.get("match_score", 0)
            is_chinese = c.get("is_chinese", False) or self._is_chinese_name(c.get("evaluation", {}).get("basic_info", {}).get("name", ""))
            
            if score >= 0.7:
                high.append(c)
                if is_chinese:
                    chinese_high.append(c)
            elif score >= 0.5:
                medium.append(c)
            else:
                low.append(c)
        
        return {
            "high": sorted(high, key=lambda x: x.get("match_score", 0), reverse=True),
            "medium": sorted(medium, key=lambda x: x.get("match_score", 0), reverse=True),
            "low": low,
            "chinese_high": chinese_high,
        }
    
    def _is_chinese_name(self, name: str) -> bool:
        """判断是否为华人姓名"""
        if not name:
            return False
        chinese_surnames = [
            'chen', 'wang', 'li', 'liu', 'zhang', 'zhao', 'lin', 'yang', 'wu', 'zhou',
            'huang', 'xu', 'sun', 'hu', 'ma', 'guo', 'he', 'zheng', 'xie', 'song',
            'tang', 'feng', 'deng', 'ye', 'cheng', 'cai', 'cao', 'jiang', 'jin',
            'luo', 'gao', 'zheng', 'xiao', 'han', 'wei', 'xue', 'yan', 'dong'
        ]
        name_lower = name.lower()
        for surname in chinese_surnames:
            if name_lower.startswith(surname + ' ') or f' {surname}' in name_lower:
                return True
        return False
    
    def generate_progress_report(self) -> str:
        """生成进度报告"""
        categorized = self.categorize_candidates()
        
        high_count = len(categorized["high"])
        medium_count = len(categorized["medium"])
        chinese_high_count = len(categorized["chinese_high"])
        total = len(self.candidates)
        progress_pct = (high_count / self.target * 100) if self.target > 0 else 0
        chinese_progress_pct = (chinese_high_count / self.chinese_target * 100) if self.chinese_target > 0 else 0
        
        report = f"""
{'='*80}
🎯 TALENTINTEL 人才检索进度报告
{'='*80}

📊 总体统计
  目标高分候选人: {self.target} 人
  当前高分候选人: {high_count} 人
  进度完成度: {progress_pct:.1f}%
  
🇨🇳 华人候选人统计
  目标华人候选人: {self.chinese_target} 人
  当前华人高分候选人: {chinese_high_count} 人
  华人进度完成度: {chinese_progress_pct:.1f}%
  
  候选人分布:
    🔥 高分 (≥0.7): {high_count} 人 (华人: {chinese_high_count} 人)
    ⭐ 中分 (0.5-0.7): {medium_count} 人
    ⚪ 低分 (<0.5): {len(categorized['low'])} 人
    ─────────────────
    总计: {total} 人

{'='*80}
🏆 高分候选人列表 (前20)
{'='*80}
"""
        
        for i, c in enumerate(categorized["high"][:20], 1):
            info = c.get("evaluation", {}).get("basic_info", {})
            ai = c.get("evaluation", {}).get("ai_expertise", {})
            wireless = c.get("evaluation", {}).get("wireless_expertise", {})
            
            name = info.get("name", "Unknown")
            role = info.get("current_role", "N/A")
            company = info.get("current_company", "N/A")
            location = info.get("location", "N/A")
            score = c.get("match_score", 0)
            
            ai_level = ai.get("level", "N/A")
            wireless_level = wireless.get("level", "N/A")
            
            report += f"""
[{i}] {name}
    分数: {score:.2f} | 职位: {role}
    公司: {company} | 地点: {location}
    AI能力: {ai_level} | Wireless能力: {wireless_level}
    链接: {c.get('url', 'N/A')}
"""
        
        report += f"""
{'='*80}
📋 搜索策略状态
{'='*80}
"""
        
        # 列出 XRay campaigns
        if self.xray_dir.exists():
            campaigns = list(self.xray_dir.glob("*.json"))
            report += f"\n已生成搜索 Campaigns: {len(campaigns)} 个\n"
            for c in campaigns[:5]:
                report += f"  • {c.name}\n"
        
        report += f"""
{'='*80}
🚀 下一步行动建议
{'='*80}

当前进度: {high_count}/{self.target} ({progress_pct:.1f}%)

"""
        
        if high_count < self.target or chinese_high_count < self.chinese_target:
            remaining_total = self.target - high_count
            remaining_chinese = self.chinese_target - chinese_high_count
            report += f"""
还需 {remaining_total} 个高分候选人、{remaining_chinese} 个华人候选人才能达到目标。

建议操作:
1. 使用生成的 XRay 搜索链接批量获取候选人
   文件: data/xray_campaigns/extended_links_*.html

2. 使用浏览器插件(Linkclump)批量提取 LinkedIn 链接

3. 运行批量评估:
   python3 scripts/batch_evaluate.py links.txt

4. 运行华人专项搜索:
   python3 scripts/chinese_talent_hunt.py

5. 如需自动化，考虑使用付费住宅代理

6. 搜索关键词组合:
   • "machine learning wireless"
   • "AI engineer 5G"
   • "wireless communication researcher"
   • "MIMO deep learning"
   • "6G AI"
   • "semantic communication"
"""
        else:
            report += """
✅ 目标已达成！

建议操作:
1. 整理高分候选人列表
2. 优先联系排名靠前的候选人
3. 准备 outreach 邮件模板
4. 建立候选人跟进系统
"""
        
        report += f"""
{'='*80}
报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}
"""
        
        return report
    
    def save_summary(self):
        """保存汇总数据"""
        categorized = self.categorize_candidates()
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "target": self.target,
            "chinese_target": self.chinese_target,
            "progress": {
                "high_score": len(categorized["high"]),
                "medium_score": len(categorized["medium"]),
                "low_score": len(categorized["low"]),
                "total": len(self.candidates),
                "progress_pct": round(len(categorized["high"]) / self.target * 100, 1),
                "chinese_high_score": len(categorized["chinese_high"]),
                "chinese_progress_pct": round(len(categorized["chinese_high"]) / self.chinese_target * 100, 1),
            },
            "high_score_candidates": categorized["high"],
            "chinese_high_candidates": categorized["chinese_high"],
            "medium_score_candidates": categorized["medium"][:20],  # 限制数量
        }
        
        # 保存 JSON
        summary_file = self.base_dir / "data" / "findings" / "aggregated_summary.json"
        summary_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"💾 汇总数据已保存: {summary_file}")
        
        # 保存 Markdown 报告
        report = self.generate_progress_report()
        report_file = self.base_dir / "TALENT_SEARCH_PROGRESS_REPORT.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"💾 进度报告已保存: {report_file}")
        
        return summary_file, report_file
    
    def run(self):
        """运行汇总"""
        print("="*80)
        print("🚀 TalentIntel 数据汇总")
        print("="*80)
        
        self.load_all_candidates()
        categorized = self.categorize_candidates()
        
        print(f"\n📊 候选人分类:")
        print(f"  🔥 高分 (≥0.7): {len(categorized['high'])} 人")
        print(f"  🇨🇳 华人高分: {len(categorized['chinese_high'])} 人")
        print(f"  ⭐ 中分 (0.5-0.7): {len(categorized['medium'])} 人")
        print(f"  ⚪ 低分 (<0.5): {len(categorized['low'])} 人")
        
        self.save_summary()
        
        print("\n" + "="*80)
        print("✅ 数据汇总完成!")
        print("="*80)
        
        # 打印报告预览
        print("\n" + self.generate_progress_report())
        
        return categorized


def main():
    """主函数"""
    aggregator = TalentDataAggregator()
    result = aggregator.run()
    
    # 返回关键统计
    high_count = len(result["high"])
    chinese_count = len(result["chinese_high"])
    print(f"\n🎯 RESULT: {high_count}/100 高分候选人, {chinese_count}/40 华人候选人")
    
    # ===== 刷新华人候选人整体报告 =====
    print("\n" + "="*80)
    print("🔄 正在刷新华人候选人整体报告...")
    print("="*80)
    try:
        import subprocess
        result_sub = subprocess.run(
            ["python3", "scripts/generate_chinese_report.py"],
            cwd=str(Path(__file__).parent.parent),
            capture_output=True,
            text=True
        )
        if result_sub.returncode == 0:
            print("✅ 华人候选人整体报告已刷新!")
            print("📄 报告位置: CHINESE_TALENT_OVERALL_REPORT.md")
        else:
            print(f"⚠️ 报告刷新遇到问题")
    except Exception as e:
        print(f"⚠️ 报告刷新失败: {e}")
    # ==================================
    
    return high_count, chinese_count


if __name__ == "__main__":
    high_count, chinese_count = main()
    exit(0 if high_count >= 100 else 1)
