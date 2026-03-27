#!/usr/bin/env python3
"""
TalentIntel Coordinator - 人才情报协调器
数字研究员主控程序，协调多数据源，触发人工介入
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class TalentProfile:
    """统一人才档案"""
    # 身份
    name: str
    source: str  # github/arxiv/semantic_scholar/linkedin
    source_id: str  # 平台唯一ID
    
    # 专业领域
    ai_score: float  # AI能力评分 0-1
    wireless_score: float  # 无线通信能力评分 0-1
    match_score: float  # 综合匹配分数
    
    # 联系信息
    email: str = ""
    homepage: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    
    # 元数据
    location: str = ""
    company: str = ""
    affiliations: List[str] = None
    
    # 证据
    evidence: Dict = None  # 支持评分的证据
    
    # 状态
    status: str = "auto_discovered"  # auto_discovered / human_verified / contacted
    verification_notes: str = ""
    
    def __post_init__(self):
        if self.affiliations is None:
            self.affiliations = []
        if self.evidence is None:
            self.evidence = {}


class TalentIntelCoordinator:
    """人才情报协调器"""
    
    # 人工介入触发阈值
    HIGH_SCORE_THRESHOLD = 0.8  # ≥0.8分需要人工验证
    DAILY_MANUAL_LIMIT = 3  # 每日最多3人需要人工介入
    
    def __init__(self, data_dir: str = "data/daily"):
        self.data_dir = data_dir
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.daily_dir = f"{data_dir}/{self.today}"
        os.makedirs(self.daily_dir, exist_ok=True)
        
        # 今日人工介入计数
        self.manual_count = 0
    
    def run_github_phase(self) -> List[TalentProfile]:
        """Phase 1: GitHub自动挖掘"""
        print("\n" + "="*70)
        print("🚀 Phase 1: GitHub开发者挖掘 (全自动)")
        print("="*70)
        
        # 运行GitHub挖掘脚本
        output_file = f"{self.daily_dir}/github_raw.json"
        
        try:
            result = subprocess.run([
                sys.executable,
                "scripts/github_talent_miner.py",
                "--output", output_file,
                "--min-score", "0.3"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"❌ GitHub挖掘失败: {result.stderr}")
                return []
            
            # 读取结果
            with open(output_file, 'r') as f:
                github_data = json.load(f)
            
            # 转换为统一格式
            profiles = []
            for item in github_data:
                profile = TalentProfile(
                    name=item.get('name') or item.get('username'),
                    source='github',
                    source_id=item.get('username'),
                    ai_score=min(len(item.get('ai_repos', [])) / 3, 1.0),
                    wireless_score=min(len(item.get('wireless_repos', [])) / 3, 1.0),
                    match_score=item.get('match_score', 0),
                    email=item.get('email', ''),
                    homepage=item.get('blog', ''),
                    github_url=f"https://github.com/{item.get('username')}",
                    location=item.get('location', ''),
                    company=item.get('company', ''),
                    evidence={
                        'ai_repos': item.get('ai_repos', []),
                        'wireless_repos': item.get('wireless_repos', []),
                        'followers': item.get('followers', 0),
                        'repos_count': item.get('repos_count', 0)
                    }
                )
                profiles.append(profile)
            
            print(f"✅ GitHub挖掘完成: {len(profiles)} 人")
            return profiles
            
        except Exception as e:
            print(f"❌ GitHub挖掘异常: {e}")
            return []
    
    def run_academic_phase(self) -> List[TalentProfile]:
        """Phase 2: 学术数据库挖掘"""
        print("\n" + "="*70)
        print("🎓 Phase 2: 学术数据库挖掘 (全自动)")
        print("="*70)
        
        output_file = f"{self.daily_dir}/academic_raw.json"
        
        try:
            result = subprocess.run([
                sys.executable,
                "scripts/academic_talent_miner.py",
                "--output", output_file
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                print(f"❌ 学术挖掘失败: {result.stderr}")
                return []
            
            # 读取结果
            with open(output_file, 'r') as f:
                academic_data = json.load(f)
            
            # 转换为统一格式
            profiles = []
            for item in academic_data.get('semantic_scholar_profiles', []):
                profile = TalentProfile(
                    name=item.get('name'),
                    source='semantic_scholar',
                    source_id=item.get('name'),  # Semantic Scholar没有唯一ID
                    ai_score=min(len(item.get('ai_papers', [])) / 5, 1.0),
                    wireless_score=min(len(item.get('wireless_papers', [])) / 5, 1.0),
                    match_score=item.get('match_score', 0),
                    homepage=item.get('homepage', ''),
                    affiliations=item.get('affiliations', []),
                    company=item.get('affiliations', [''])[0] if item.get('affiliations') else '',
                    evidence={
                        'ai_papers': item.get('ai_papers', []),
                        'wireless_papers': item.get('wireless_papers', []),
                        'h_index': item.get('h_index', 0),
                        'citations': item.get('citations', 0),
                        'total_papers': len(item.get('papers', []))
                    }
                )
                profiles.append(profile)
            
            print(f"✅ 学术挖掘完成: {len(profiles)} 人")
            return profiles
            
        except Exception as e:
            print(f"❌ 学术挖掘异常: {e}")
            return []
    
    def merge_and_dedup(self, github_profiles: List[TalentProfile],
                       academic_profiles: List[TalentProfile]) -> List[TalentProfile]:
        """合并并去重"""
        print("\n" + "="*70)
        print("🔄 数据合并与去重")
        print("="*70)
        
        all_profiles = github_profiles + academic_profiles
        
        # 基于姓名去重（简化版，实际可用更复杂的匹配算法）
        seen_names = {}
        unique_profiles = []
        
        for profile in all_profiles:
            name_key = profile.name.lower().replace(' ', '')
            
            if name_key in seen_names:
                # 合并信息
                existing = seen_names[name_key]
                # 取最高分数
                existing.match_score = max(existing.match_score, profile.match_score)
                existing.ai_score = max(existing.ai_score, profile.ai_score)
                existing.wireless_score = max(existing.wireless_score, profile.wireless_score)
                # 合并证据
                existing.evidence.update(profile.evidence)
                # 补充来源
                if profile.source not in existing.source:
                    existing.source += f"+{profile.source}"
            else:
                seen_names[name_key] = profile
                unique_profiles.append(profile)
        
        # 排序
        unique_profiles.sort(key=lambda x: x.match_score, reverse=True)
        
        print(f"✅ 合并完成: {len(github_profiles)} GitHub + {len(academic_profiles)} 学术 = {len(unique_profiles)} 唯一")
        return unique_profiles
    
    def trigger_human_verification(self, profile: TalentProfile) -> bool:
        """
        触发人工验证
        返回: 是否成功完成验证
        """
        if self.manual_count >= self.DAILY_MANUAL_LIMIT:
            print(f"   ⚠️  今日人工验证配额已满 ({self.DAILY_MANUAL_LIMIT}人)")
            return False
        
        print(f"\n" + "="*70)
        print(f"👤 需要人工验证: {profile.name}")
        print(f"   匹配分数: {profile.match_score:.2f}")
        print(f"   来源: {profile.source}")
        print(f"   证据: {json.dumps(profile.evidence, indent=2)[:200]}...")
        print("="*70)
        
        # 生成验证任务文件
        task_file = f"{self.daily_dir}/verify_{profile.name.replace(' ', '_')}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(profile), f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 验证任务已创建: {task_file}")
        print("\n请人工执行以下验证:")
        print(f"  1. 搜索 LinkedIn: {profile.name}")
        print(f"  2. 验证身份和职业信息")
        print(f"  3. 获取 LinkedIn URL")
        print(f"  4. 更新任务文件中的 linkedin_url 和 status")
        
        self.manual_count += 1
        
        # 注意：这里只是创建任务，实际验证需要人工完成后更新文件
        return True
    
    def run_verification_phase(self, profiles: List[TalentProfile]) -> List[TalentProfile]:
        """Phase 3: 人工验证（低频介入）"""
        print("\n" + "="*70)
        print("👁️  Phase 3: 高分候选人验证 (人工介入)")
        print("="*70)
        
        # 筛选高分候选人
        high_score = [p for p in profiles if p.match_score >= self.HIGH_SCORE_THRESHOLD]
        
        print(f"发现 {len(high_score)} 位高分候选人 (≥{self.HIGH_SCORE_THRESHOLD})")
        print(f"今日人工验证配额: {self.DAILY_MANUAL_LIMIT}人")
        
        verified_count = 0
        for profile in high_score[:self.DAILY_MANUAL_LIMIT]:
            if self.trigger_human_verification(profile):
                profile.status = "pending_verification"
                verified_count += 1
        
        print(f"\n✅ 已创建 {verified_count} 个人工验证任务")
        return profiles
    
    def generate_daily_report(self, profiles: List[TalentProfile]):
        """生成每日报告"""
        report_file = f"{self.daily_dir}/report.md"
        
        auto_discovered = [p for p in profiles if p.status == "auto_discovered"]
        pending = [p for p in profiles if p.status == "pending_verification"]
        high_score = [p for p in profiles if p.match_score >= 0.7]
        
        lines = [
            f"# 人才情报日报 - {self.today}",
            f"\n## 数据概览",
            f"- **总发现**: {len(profiles)} 人",
            f"- **自动发现**: {len(auto_discovered)} 人",
            f"- **待人工验证**: {len(pending)} 人",
            f"- **高分候选人**: {len(high_score)} 人 (≥0.7)",
            "\n## 数据源分布",
        ]
        
        # 统计来源
        source_counts = {}
        for p in profiles:
            source_counts[p.source] = source_counts.get(p.source, 0) + 1
        
        for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
            lines.append(f"- {source}: {count} 人")
        
        # 高分候选人详情
        lines.extend([
            "\n## 高分候选人 (Top 20)",
            ""
        ])
        
        for i, p in enumerate(high_score[:20], 1):
            lines.extend([
                f"### {i}. {p.name}",
                f"- **匹配分数**: {p.match_score:.2f} (AI: {p.ai_score:.2f}, Wireless: {p.wireless_score:.2f})",
                f"- **来源**: {p.source}",
                f"- **地点**: {p.location}",
                f"- **公司/机构**: {p.company or ', '.join(p.affiliations[:1])}",
            ])
            
            if p.github_url:
                lines.append(f"- **GitHub**: {p.github_url}")
            if p.homepage:
                lines.append(f"- **主页**: {p.homepage}")
            
            lines.append(f"- **状态**: {p.status}")
            
            # 证据
            if p.evidence:
                lines.append(f"- **证据**: {len(p.evidence)} 项")
            
            lines.append("")
        
        # 待验证任务
        if pending:
            lines.extend([
                "\n## 待人工验证任务",
                ""
            ])
            for p in pending:
                lines.append(f"- [ ] {p.name} (分数: {p.match_score:.2f})")
        
        # 写入报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"\n📝 日报已生成: {report_file}")
    
    def export_final_data(self, profiles: List[TalentProfile]):
        """导出最终数据"""
        output_file = f"{self.daily_dir}/talents_final.json"
        
        data = [asdict(p) for p in profiles]
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 最终数据已导出: {output_file}")
    
    def run_daily_pipeline(self):
        """运行每日完整流程"""
        print("\n" + "="*70)
        print(f"🤖 TalentIntel 数字研究员启动 - {self.today}")
        print("="*70)
        print("模式: 全自动发现 + 低频人工验证")
        
        # Phase 1: GitHub挖掘
        github_profiles = self.run_github_phase()
        
        # Phase 2: 学术挖掘
        academic_profiles = self.run_academic_phase()
        
        # 合并去重
        all_profiles = self.merge_and_dedup(github_profiles, academic_profiles)
        
        # Phase 3: 人工验证触发（低频）
        all_profiles = self.run_verification_phase(all_profiles)
        
        # 生成报告
        self.generate_daily_report(all_profiles)
        
        # 导出数据
        self.export_final_data(all_profiles)
        
        # 总结
        print("\n" + "="*70)
        print("📊 每日任务完成")
        print("="*70)
        print(f"总发现: {len(all_profiles)} 人")
        print(f"高分(≥0.7): {len([p for p in all_profiles if p.match_score >= 0.7])} 人")
        print(f"待验证: {len([p for p in all_profiles if p.status == 'pending_verification'])} 人")
        print(f"人工介入: {self.manual_count}/{self.DAILY_MANUAL_LIMIT} 人")
        print("="*70)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TalentIntel 人才情报协调器')
    parser.add_argument('--data-dir', default='data/daily',
                       help='数据目录')
    parser.add_argument('--phase', choices=['all', 'github', 'academic', 'verify'],
                       default='all', help='执行阶段')
    
    args = parser.parse_args()
    
    coordinator = TalentIntelCoordinator(data_dir=args.data_dir)
    
    if args.phase == 'all':
        coordinator.run_daily_pipeline()
    elif args.phase == 'github':
        profiles = coordinator.run_github_phase()
        coordinator.export_final_data(profiles)
    elif args.phase == 'academic':
        profiles = coordinator.run_academic_phase()
        coordinator.export_final_data(profiles)
    elif args.phase == 'verify':
        # 读取现有数据并触发验证
        daily_file = f"{coordinator.daily_dir}/talents_final.json"
        if os.path.exists(daily_file):
            with open(daily_file, 'r') as f:
                data = json.load(f)
            profiles = [TalentProfile(**item) for item in data]
            coordinator.run_verification_phase(profiles)
        else:
            print("❌ 未找到今日数据文件，请先运行完整流程")


if __name__ == '__main__':
    main()
