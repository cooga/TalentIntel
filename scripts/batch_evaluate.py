"""
批量人才评估工具
读取 LinkedIn 链接列表，使用数字研究员批量评估
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from platforms.linkedin_v2 import LinkedInResearcherV2


class BatchTalentEvaluator:
    """批量人才评估器"""
    
    def __init__(self, links_file: str = None):
        self.links_file = links_file
        self.results = []
        self.high_matches = []
    
    def load_links(self, file_path: str = None) -> List[str]:
        """
        加载链接列表
        
        支持格式:
        - 每行一个 URL 的文本文件
        - JSON 文件（包含 url 字段的数组）
        """
        file_path = file_path or self.links_file
        
        if not file_path:
            raise ValueError("请提供链接文件路径")
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 检测文件类型
        if path.suffix == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [item["url"] if isinstance(item, dict) else item for item in data]
                elif isinstance(data, dict) and "profiles" in data:
                    return [p["url"] for p in data["profiles"]]
        else:
            # 文本文件，每行一个链接
            with open(path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip() and 'linkedin.com/in/' in line]
    
    async def evaluate_batch(
        self,
        links: List[str],
        min_score: float = 0.5,
        max_profiles: int = 10,
    ) -> List[Dict]:
        """
        批量评估人才
        
        Args:
            links: LinkedIn 档案链接列表
            min_score: 最低匹配分数
            max_profiles: 最大评估数量
        """
        researcher = LinkedInResearcherV2()
        
        try:
            # 启动浏览器
            print("🚀 启动浏览器...")
            await researcher.start(headless=False)
            
            # 检查登录
            if not await researcher.ensure_login():
                print("❌ 登录失败")
                return []
            
            print(f"✅ 已登录，准备评估 {min(len(links), max_profiles)} 个人才档案\n")
            
            results = []
            high_matches = []
            
            for i, url in enumerate(links[:max_profiles], 1):
                print(f"\n{'='*60}")
                print(f"🔍 [{i}/{min(len(links), max_profiles)}] 评估: {url}")
                print('='*60)
                
                try:
                    # 查看档案
                    result = await researcher.view_profile(url)
                    
                    if result:
                        match_score = result.get("match_score", 0)
                        
                        if match_score >= min_score:
                            print(f"\n✅ 匹配成功! 分数: {match_score:.2f}")
                            results.append(result)
                            
                            if match_score >= 0.7:
                                high_matches.append(result)
                        else:
                            print(f"\n⏭️  匹配度不足 ({match_score:.2f} < {min_score})，跳过")
                    else:
                        print("\n❌ 无法评估此档案")
                
                except Exception as e:
                    print(f"\n❌ 评估出错: {e}")
                
                # 档案间休息（如果不是最后一个）
                if i < min(len(links), max_profiles):
                    import random
                    delay = random.uniform(30, 60)
                    print(f"\n⏳ 休息 {delay:.1f} 秒...")
                    await asyncio.sleep(delay)
            
            # 保存结果
            self.results = results
            self.high_matches = high_matches
            
            return results
            
        finally:
            await researcher.shutdown()
    
    def save_results(self, output_dir: str = "data/batch_evaluations"):
        """保存评估结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存所有结果
        all_results_file = output_path / f"batch_results_{timestamp}.json"
        with open(all_results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "evaluated_at": datetime.now().isoformat(),
                "total_evaluated": len(self.results) + len([r for r in self.results if r["match_score"] < 0.5]),
                "high_matches": len(self.high_matches),
                "medium_matches": len([r for r in self.results if 0.5 <= r["match_score"] < 0.7]),
                "profiles": self.results,
            }, f, ensure_ascii=False, indent=2)
        
        # 保存高匹配人才（单独文件）
        if self.high_matches:
            high_match_file = output_path / f"high_matches_{timestamp}.json"
            with open(high_match_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "evaluated_at": datetime.now().isoformat(),
                    "count": len(self.high_matches),
                    "profiles": self.high_matches,
                }, f, ensure_ascii=False, indent=2)
        
        # 生成 Markdown 报告
        report_file = output_path / f"batch_report_{timestamp}.md"
        self.generate_markdown_report(report_file)
        
        print(f"\n💾 结果已保存:")
        print(f"   所有结果: {all_results_file}")
        if self.high_matches:
            print(f"   高匹配人才: {high_match_file}")
        print(f"   报告: {report_file}")
        
        return all_results_file
    
    def generate_markdown_report(self, output_file: Path):
        """生成 Markdown 报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# 批量人才评估报告\n\n")
            f.write(f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 统计
            f.write(f"## 统计\n\n")
            f.write(f"- 总评估人数: {len(self.results)}\n")
            f.write(f"- 高匹配 (≥0.7): {len(self.high_matches)}\n")
            f.write(f"- 中匹配 (0.5-0.7): {len([r for r in self.results if 0.5 <= r['match_score'] < 0.7])}\n\n")
            
            # 高匹配人才
            if self.high_matches:
                f.write(f"## 🏆 高匹配人才 (≥0.7)\n\n")
                for i, profile in enumerate(self.high_matches, 1):
                    eval_data = profile.get("evaluation", {})
                    f.write(f"### {i}. {eval_data.get('basic_info', {}).get('name', 'Unknown')}\n\n")
                    f.write(f"- **匹配分数**: {profile.get('match_score', 0):.2f}\n")
                    f.write(f"- **职位**: {eval_data.get('basic_info', {}).get('current_role', 'N/A')}\n")
                    f.write(f"- **公司**: {eval_data.get('basic_info', {}).get('current_company', 'N/A')}\n")
                    f.write(f"- **地点**: {eval_data.get('basic_info', {}).get('location', 'N/A')}\n")
                    f.write(f"- **档案**: {profile.get('url', 'N/A')}\n\n")
                    
                    if 'ai_expertise' in eval_data:
                        f.write(f"**AI能力**: {eval_data['ai_expertise'].get('level', 'N/A')}\n")
                    if 'wireless_expertise' in eval_data:
                        f.write(f"**Wireless能力**: {eval_data['wireless_expertise'].get('level', 'N/A')}\n")
                    
                    f.write(f"\n**匹配理由**:\n")
                    for reason in eval_data.get('match_reasons', []):
                        f.write(f"- {reason}\n")
                    
                    f.write(f"\n---\n\n")
            
            # 其他匹配人才
            other_matches = [r for r in self.results if r.get("match_score", 0) < 0.7]
            if other_matches:
                f.write(f"## ⭐ 其他匹配人才 (0.5-0.7)\n\n")
                for profile in other_matches:
                    eval_data = profile.get("evaluation", {})
                    name = eval_data.get('basic_info', {}).get('name', 'Unknown')
                    score = profile.get("match_score", 0)
                    url = profile.get("url", "N/A")
                    f.write(f"- **{name}** | 分数: {score:.2f} | [档案]({url})\n")
                
                f.write("\n")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="批量人才评估工具")
    parser.add_argument("links_file", help="包含 LinkedIn 链接的文件路径")
    parser.add_argument("--min-score", type=float, default=0.5, help="最低匹配分数 (默认: 0.5)")
    parser.add_argument("--max-profiles", type=int, default=10, help="最大评估数量 (默认: 10)")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🎯 TalentIntel - 批量人才评估")
    print("=" * 70)
    
    evaluator = BatchTalentEvaluator(args.links_file)
    
    try:
        # 加载链接
        print(f"\n📂 加载链接: {args.links_file}")
        links = evaluator.load_links()
        print(f"   找到 {len(links)} 个有效链接")
        
        if not links:
            print("❌ 没有找到有效的 LinkedIn 链接")
            return
        
        # 批量评估
        results = await evaluator.evaluate_batch(
            links,
            min_score=args.min_score,
            max_profiles=args.max_profiles,
        )
        
        # 打印摘要
        print("\n" + "=" * 70)
        print("📊 评估完成!")
        print(f"   高匹配 (≥0.7): {len(evaluator.high_matches)}")
        print(f"   中匹配 (0.5-0.7): {len([r for r in results if 0.5 <= r['match_score'] < 0.7])}")
        print("=" * 70)
        
        # 保存结果
        evaluator.save_results()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
