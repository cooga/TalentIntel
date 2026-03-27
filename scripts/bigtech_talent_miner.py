#!/usr/bin/env python3
"""
BigTech Talent Miner - 北美大厂人才挖掘器
专门搜索Google、NVIDIA、Samsung、Nokia等公司的AI+无线通信人才
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class BigTechProfile:
    """大厂人才档案"""
    name: str
    username: str
    company: str  # 当前公司
    location: str
    bio: str
    email: str
    blog: str
    
    # AI技能
    ai_repos: List[str]
    wireless_repos: List[str]
    
    # 评分
    ai_score: float
    wireless_score: float
    match_score: float
    
    # 链接
    github_url: str
    linkedin_url: str = ""
    
    # 验证状态
    is_chinese: bool = False
    company_verified: bool = False

class BigTechTalentMiner:
    """大厂人才挖掘器"""
    
    # 目标北美大厂
    TARGET_COMPANIES = [
        'Google', 'NVIDIA', 'Nvidia',
        'Samsung', 'Samsung Research',
        'Nokia', 'Nokia Bell Labs',
        'SpaceX', 'Tesla',
        'Qualcomm', 'Intel', 'AMD',
        'Meta', 'Amazon', 'Apple',
        'Ericsson', 'Huawei', 'ZTE'
    ]
    
    # 地点聚焦北美
    LOCATIONS = [
        'California', 'Seattle', 'New York', 'Boston', 'Texas',
        'Toronto', 'Vancouver', 'Montreal',
        'London', 'Cambridge'
    ]
    
    AI_KEYWORDS = [
        'machine learning', 'deep learning', 'neural network',
        'pytorch', 'tensorflow', 'AI', 'ML', 'federated learning',
        'reinforcement learning', 'LLM', 'generative AI'
    ]
    
    WIRELESS_KEYWORDS = [
        'wireless', '5G', '6G', 'MIMO', 'OFDM', 'beamforming',
        'channel estimation', 'signal processing', 'communication',
        'RF', 'mmWave', 'satellite', 'WiFi', 'LTE', 'NR',
        'radio', 'antenna', 'propagation'
    ]
    
    # 华人姓氏
    CHINESE_SURNAMES = ['zhang', 'li', 'wang', 'liu', 'chen', 'yang', 
                       'zhao', 'huang', 'zhou', 'wu', 'xu', 'sun', 'hu',
                       'zhu', 'gao', 'lin', 'he', 'guo', 'ma', 'luo',
                       'liang', 'song', 'zheng', 'xie', 'han', 'tang',
                       'feng', 'yu', 'dong', 'xiao', 'cheng', 'cao',
                       'yuan', 'deng', 'xue', 'tian', 'pan', 'wei', 'jiang']
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {'Accept': 'application/vnd.github.v3+json'}
        if token:
            self.headers['Authorization'] = f'token {token}'
    
    def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """发送GitHub API请求"""
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 403:
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            wait_time = max(reset_time - int(time.time()), 0) + 1
            print(f"⏳ 速率限制，等待 {wait_time} 秒...")
            time.sleep(wait_time)
            return self._request(endpoint, params)
        
        response.raise_for_status()
        return response.json()
    
    def search_by_company(self, company: str, location: str = None) -> List[Dict]:
        """
        按公司搜索GitHub用户
        """
        query = f'"{company}" in:company'
        if location:
            query += f' location:{location}'
        
        print(f"🔍 搜索 {company} 员工" + (f" @ {location}" if location else ""))
        
        all_users = []
        page = 1
        per_page = 100
        
        while page <= 5:  # 最多500个结果
            params = {
                'q': query,
                'per_page': per_page,
                'page': page
            }
            
            try:
                result = self._request('/search/users', params)
                users = result.get('items', [])
                
                if not users:
                    break
                
                all_users.extend(users)
                print(f"  获取第 {page} 页，累计 {len(all_users)} 人")
                
                if len(users) < per_page:
                    break
                
                page += 1
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ 搜索失败: {e}")
                break
        
        return all_users
    
    def get_user_details(self, username: str) -> Optional[BigTechProfile]:
        """获取用户详细信息"""
        try:
            user = self._request(f'/users/{username}')
            repos = self._request(f'/users/{username}/repos', {'per_page': 100})
            
            # 分析仓库
            ai_repos = []
            wireless_repos = []
            
            for repo in repos:
                repo_name = repo.get('name', '').lower()
                repo_desc = repo.get('description', '') or ''
                topics = repo.get('topics', [])
                repo_text = f"{repo_name} {repo_desc} {' '.join(topics)}".lower()
                
                if any(kw in repo_text for kw in self.AI_KEYWORDS):
                    ai_repos.append(repo['name'])
                
                if any(kw in repo_text for kw in self.WIRELESS_KEYWORDS):
                    wireless_repos.append(repo['name'])
            
            # 计算分数
            ai_score = min(len(ai_repos) / 3, 1.0)
            wireless_score = min(len(wireless_repos) / 3, 1.0)
            match_score = (ai_score + wireless_score) / 2
            
            # 双领域加分
            if ai_repos and wireless_repos:
                match_score = min(match_score + 0.2, 1.0)
            
            # 华人识别
            name_lower = (user.get('name') or '').lower()
            username_lower = user.get('login', '').lower()
            is_chinese = any(surname in name_lower.split() or surname in username_lower 
                            for surname in self.CHINESE_SURNAMES)
            
            if is_chinese and match_score > 0:
                match_score = min(match_score + 0.1, 1.0)
            
            return BigTechProfile(
                name=user.get('name') or username,
                username=username,
                company=user.get('company', ''),
                location=user.get('location', ''),
                bio=user.get('bio', ''),
                email=user.get('email', ''),
                blog=user.get('blog', ''),
                ai_repos=ai_repos,
                wireless_repos=wireless_repos,
                ai_score=ai_score,
                wireless_score=wireless_score,
                match_score=match_score,
                github_url=f"https://github.com/{username}",
                is_chinese=is_chinese
            )
            
        except Exception as e:
            print(f"❌ 获取用户 {username} 详情失败: {e}")
            return None
    
    def find_bigtech_talent(self) -> List[BigTechProfile]:
        """
        搜索所有目标大厂的人才
        """
        print("\n" + "="*70)
        print("🎯 北美大厂AI+无线通信人才挖掘")
        print("="*70)
        print(f"目标公司: {', '.join(self.TARGET_COMPANIES[:8])}")
        print(f"目标地点: {', '.join(self.LOCATIONS[:5])}")
        print("="*70)
        
        all_candidates = []
        seen_users = set()
        
        for company in self.TARGET_COMPANIES:
            print(f"\n{'='*70}")
            print(f"🏢 搜索: {company}")
            print('='*70)
            
            # 搜索该公司的用户
            for location in self.LOCATIONS[:3]:  # 前3个地点
                users = self.search_by_company(company, location)
                
                for user in users:
                    username = user['login']
                    if username in seen_users:
                        continue
                    seen_users.add(username)
                    
                    profile = self.get_user_details(username)
                    if profile and (profile.ai_repos or profile.wireless_repos):
                        all_candidates.append(profile)
                        
                        print(f"\n👤 {profile.name or username}")
                        print(f"   公司: {profile.company}")
                        print(f"   地点: {profile.location}")
                        print(f"   AI仓库: {len(profile.ai_repos)}个")
                        print(f"   无线仓库: {len(profile.wireless_repos)}个")
                        print(f"   匹配分数: {profile.match_score:.2f}")
                        
                        if profile.is_chinese:
                            print(f"   🏮 华人")
                        
                        if profile.match_score >= 0.5:
                            print(f"   ⭐ 高分候选人!")
                
                time.sleep(3)  # 地点间延迟
            
            time.sleep(5)  # 公司间延迟
        
        # 排序
        all_candidates.sort(key=lambda x: x.match_score, reverse=True)
        return all_candidates
    
    def generate_report(self, candidates: List[BigTechProfile]) -> str:
        """生成报告"""
        lines = [
            "# 北美大厂AI+无线通信人才报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"数据来源: GitHub",
            f"候选人总数: {len(candidates)}",
            "\n## 高分华人候选人 (匹配度≥0.5)",
            ""
        ]
        
        chinese_high = [c for c in candidates if c.is_chinese and c.match_score >= 0.5]
        
        for i, c in enumerate(chinese_high[:20], 1):
            lines.extend([
                f"### {i}. {c.name}",
                f"- **匹配分数**: {c.match_score:.2f}",
                f"- **公司**: {c.company}",
                f"- **地点**: {c.location}",
                f"- **GitHub**: {c.github_url}",
                f"- **AI仓库**: {', '.join(c.ai_repos[:3])}",
                f"- **无线仓库**: {', '.join(c.wireless_repos[:3])}",
                ""
            ])
        
        # 按公司分组
        lines.extend(["\n## 按公司分布", ""])
        company_groups = {}
        for c in candidates:
            comp = c.company.strip() if c.company else 'Unknown'
            if comp not in company_groups:
                company_groups[comp] = []
            company_groups[comp].append(c)
        
        for comp, members in sorted(company_groups.items(), key=lambda x: -len(x[1]))[:10]:
            chinese_count = len([m for m in members if m.is_chinese])
            lines.append(f"- {comp}: {len(members)}人 (华人: {chinese_count})")
        
        return '\n'.join(lines)


def main():
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='北美大厂AI+无线通信人才挖掘')
    parser.add_argument('--token', help='GitHub Personal Access Token')
    parser.add_argument('--output', default='bigtech_talents.json',
                       help='输出文件')
    parser.add_argument('--report', default='bigtech_talents_report.md',
                       help='报告文件')
    
    args = parser.parse_args()
    
    token = args.token or os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("⚠️  未提供GitHub Token，使用未认证模式（速率限制更严格）")
    
    miner = BigTechTalentMiner(token)
    candidates = miner.find_bigtech_talent()
    
    print(f"\n{'='*70}")
    print(f"📊 总计发现 {len(candidates)} 位候选人")
    print('='*70)
    
    # 统计
    chinese_count = len([c for c in candidates if c.is_chinese])
    high_score = len([c for c in candidates if c.match_score >= 0.5])
    
    print(f"华人候选人: {chinese_count}")
    print(f"高分候选人: {high_score}")
    
    # 保存
    data = [asdict(c) for c in candidates]
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 已保存到 {args.output}")
    
    # 生成报告
    report = miner.generate_report(candidates)
    with open(args.report, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"📝 报告已保存到 {args.report}")


if __name__ == '__main__':
    main()
