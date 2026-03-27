#!/usr/bin/env python3
"""
GitHub Talent Miner - GitHub人才挖掘器
利用GitHub API自动发现AI+无线通信领域开发者
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class GitHubProfile:
    """GitHub开发者档案"""
    username: str
    name: str
    bio: str
    location: str
    company: str
    email: str
    blog: str
    repos_count: int
    followers: int
    ai_repos: List[str]  # AI相关仓库
    wireless_repos: List[str]  # 无线通信相关仓库
    match_score: float = 0.0
    
class GitHubTalentMiner:
    """GitHub人才挖掘器"""
    
    # AI + 无线通信关键词
    AI_KEYWORDS = [
        'machine learning', 'deep learning', 'neural network',
        'pytorch', 'tensorflow', 'AI', 'ML', 'federated learning',
        'reinforcement learning', 'computer vision', 'NLP'
    ]
    
    WIRELESS_KEYWORDS = [
        'wireless', '5G', '6G', 'MIMO', 'OFDM', 'beamforming',
        'channel estimation', 'signal processing', 'communication',
        'RF', 'mmWave', 'satellite', 'WiFi', 'LTE', 'NR'
    ]
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        if token:
            self.headers['Authorization'] = f'token {token}'
    
    def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """发送GitHub API请求"""
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 403:
            # 速率限制，等待重置
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            wait_time = max(reset_time - int(time.time()), 0) + 1
            print(f"⏳ 速率限制，等待 {wait_time} 秒...")
            time.sleep(wait_time)
            return self._request(endpoint, params)
        
        response.raise_for_status()
        return response.json()
    
    def search_users(self, location: str = None, language: str = None, 
                    min_followers: int = 10) -> List[Dict]:
        """
        搜索GitHub用户
        
        Args:
            location: 地点 (e.g., "Hong Kong", "California")
            language: 主要语言 (e.g., "Python", "C++")
            min_followers: 最少followers数
        """
        # 构建查询
        query_parts = []
        if location:
            query_parts.append(f"location:{location}")
        if language:
            query_parts.append(f"language:{language}")
        query_parts.append(f"followers:>={min_followers}")
        
        query = " ".join(query_parts)
        
        print(f"🔍 搜索: {query}")
        
        all_users = []
        page = 1
        per_page = 100
        
        while page <= 10:  # 最多1000个结果
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
                
                # 检查是否还有更多
                if len(users) < per_page:
                    break
                
                page += 1
                time.sleep(2)  # 避免速率限制
                
            except Exception as e:
                print(f"❌ 搜索失败: {e}")
                break
        
        return all_users
    
    def get_user_details(self, username: str) -> Optional[GitHubProfile]:
        """获取用户详细信息"""
        try:
            # 获取用户基本信息
            user = self._request(f'/users/{username}')
            
            # 获取用户仓库
            repos = self._request(f'/users/{username}/repos', {'per_page': 100})
            
            # 分析仓库
            ai_repos = []
            wireless_repos = []
            
            for repo in repos:
                repo_name = repo.get('name', '').lower()
                repo_desc = repo.get('description', '') or ''
                topics = repo.get('topics', [])
                repo_text = f"{repo_name} {repo_desc} {' '.join(topics)}".lower()
                
                # 检查AI关键词
                if any(kw in repo_text for kw in self.AI_KEYWORDS):
                    ai_repos.append(repo['name'])
                
                # 检查无线通信关键词
                if any(kw in repo_text for kw in self.WIRELESS_KEYWORDS):
                    wireless_repos.append(repo['name'])
            
            # 计算匹配分数
            ai_score = min(len(ai_repos) / 3, 1.0)  # 最多3个AI仓库得满分
            wireless_score = min(len(wireless_repos) / 3, 1.0)
            match_score = (ai_score + wireless_score) / 2
            
            # 有AI和无线通信双领域才给高分
            if ai_repos and wireless_repos:
                match_score = min(match_score + 0.2, 1.0)
            
            # 华人特征识别（通过姓名拼音）
            name_lower = (user.get('name') or '').lower()
            username_lower = user.get('login', '').lower()
            
            # 常见华人姓氏拼音
            chinese_surnames = ['zhang', 'li', 'wang', 'liu', 'chen', 'yang', 
                               'zhao', 'huang', 'zhou', 'wu', 'xu', 'sun', 'hu',
                               'zhu', 'gao', 'lin', 'he', 'guo', 'ma', 'luo',
                               'liang', 'song', 'zheng', 'xie', 'han', 'tang',
                               'feng', 'yu', 'dong', 'xiao', 'cheng', 'cao',
                               'yuan', 'deng', 'xue', 'tian', 'pan', 'wei',
                               'jian', 'jason', 'kevin', 'eric', 'alex']
            
            is_chinese = any(surname in name_lower.split() or surname in username_lower 
                            for surname in chinese_surnames)
            
            # 额外线索：Bio中提及中文背景
            bio_lower = (user.get('bio') or '').lower()
            chinese_hints = ['phd', 'professor', 'researcher', 'tsinghua', 'peking',
                            'fudan', 'sjtu', 'zhejiang', 'ustc', 'harbin', 'xian']
            has_chinese_edu = any(hint in bio_lower for hint in chinese_hints)
            
            if is_chinese or has_chinese_edu:
                match_score = min(match_score + 0.1, 1.0)  # 华人加分
            
            return GitHubProfile(
                username=user.get('login'),
                name=user.get('name') or '',
                bio=user.get('bio') or '',
                location=user.get('location') or '',
                company=user.get('company') or '',
                email=user.get('email') or '',
                blog=user.get('blog') or '',
                repos_count=user.get('public_repos', 0),
                followers=user.get('followers', 0),
                ai_repos=ai_repos,
                wireless_repos=wireless_repos,
                match_score=match_score
            )
            
        except Exception as e:
            print(f"❌ 获取用户 {username} 详情失败: {e}")
            return None
    
    def find_ai_wireless_talent(self, locations: List[str] = None, 
                                 chinese_focus: bool = False) -> List[GitHubProfile]:
        """
        寻找AI+无线通信双领域人才
        
        Args:
            locations: 地点列表
            chinese_focus: 是否聚焦华人（通过姓名拼音和中文特征识别）
        """
        # 海外华人聚集地（北美、欧洲、新加坡、澳洲）
        locations = locations or [
            'California', 'Seattle', 'New York', 'Boston', 'Texas',  # 美国
            'Toronto', 'Vancouver',  # 加拿大
            'London', 'Cambridge', 'Oxford',  # 英国
            'Singapore',  # 新加坡
            'Sydney', 'Melbourne',  # 澳洲
            'Germany', 'Switzerland', 'Netherlands',  # 欧洲
            'Sweden', 'Finland',  # 北欧
        ]
        
        candidates = []
        seen_users = set()
        
        for location in locations:
            print(f"\n{'='*60}")
            print(f"🌍 搜索地点: {location}")
            print('='*60)
            
            # 搜索用户
            users = self.search_users(location=location, min_followers=10)
            
            for user in users:
                username = user['login']
                if username in seen_users:
                    continue
                seen_users.add(username)
                
                # 获取详情
                profile = self.get_user_details(username)
                if profile and (profile.ai_repos or profile.wireless_repos):
                    candidates.append(profile)
                    
                    # 打印发现
                    print(f"\n👤 {profile.name or username}")
                    print(f"   地点: {profile.location}")
                    print(f"   公司: {profile.company}")
                    print(f"   AI仓库: {len(profile.ai_repos)}个")
                    print(f"   无线仓库: {len(profile.wireless_repos)}个")
                    print(f"   匹配分数: {profile.match_score:.2f}")
                    
                    if profile.match_score >= 0.5:
                        print(f"   ⭐ 高分候选人!")
            
            time.sleep(3)  # 地点间延迟
        
        # 排序
        candidates.sort(key=lambda x: x.match_score, reverse=True)
        return candidates
    
    def export_candidates(self, candidates: List[GitHubProfile], filepath: str):
        """导出候选人列表"""
        data = [asdict(c) for c in candidates]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 已保存 {len(candidates)} 位候选人到 {filepath}")
    
    def generate_report(self, candidates: List[GitHubProfile]) -> str:
        """生成Markdown报告"""
        lines = [
            "# GitHub AI+无线通信人才发现报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"候选人总数: {len(candidates)}",
            "\n## 高分候选人 (匹配度≥0.5)",
            ""
        ]
        
        high_score = [c for c in candidates if c.match_score >= 0.5]
        
        for i, c in enumerate(high_score, 1):
            lines.extend([
                f"### {i}. {c.name or c.username}",
                f"- **匹配分数**: {c.match_score:.2f}",
                f"- **GitHub**: https://github.com/{c.username}",
                f"- **地点**: {c.location}",
                f"- **公司**: {c.company}",
                f"- **AI仓库**: {', '.join(c.ai_repos[:3])}",
                f"- **无线仓库**: {', '.join(c.wireless_repos[:3])}",
                ""
            ])
        
        return '\n'.join(lines)


def main():
    """主函数"""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='GitHub AI+无线通信人才挖掘')
    parser.add_argument('--token', help='GitHub Personal Access Token')
    parser.add_argument('--location', nargs='+', 
                       default=['Hong Kong', 'California', 'New York'],
                       help='搜索地点列表')
    parser.add_argument('--output', default='github_talents.json',
                       help='输出文件')
    parser.add_argument('--min-score', type=float, default=0.3,
                       help='最低匹配分数')
    
    args = parser.parse_args()
    
    # 从环境变量获取token
    token = args.token or os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("⚠️  未提供GitHub Token，使用未认证模式（速率限制更严格）")
        print("   建议设置环境变量: export GITHUB_TOKEN='your_token'")
    
    # 运行挖掘
    miner = GitHubTalentMiner(token)
    candidates = miner.find_ai_wireless_talent(args.location)
    
    # 过滤
    filtered = [c for c in candidates if c.match_score >= args.min_score]
    
    print(f"\n{'='*60}")
    print(f"📊 总计发现 {len(filtered)} 位候选人 (≥{args.min_score}分)")
    print('='*60)
    
    # 导出
    miner.export_candidates(filtered, args.output)
    
    # 生成报告
    report = miner.generate_report(filtered)
    report_path = args.output.replace('.json', '_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"📝 报告已保存到 {report_path}")


if __name__ == '__main__':
    main()
