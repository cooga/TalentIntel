#!/usr/bin/env python3
"""
Academic Talent Miner - 学术人才挖掘器
利用arXiv和Semantic Scholar API发现AI+无线通信研究者
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict

@dataclass
class AcademicProfile:
    """学术人才档案"""
    name: str
    affiliations: List[str]  # 机构
    papers: List[Dict]  # 论文列表
    citations: int
    h_index: float
    ai_papers: List[str]  # AI相关论文
    wireless_papers: List[str]  # 无线通信论文
    match_score: float = 0.0
    orcid: str = ""
    homepage: str = ""

class ArxivMiner:
    """arXiv论文挖掘器"""
    
    API_URL = "http://export.arxiv.org/api/query"
    
    # 搜索关键词组合
    QUERIES = [
        'cat:cs.LG AND (wireless OR 5G OR 6G OR MIMO)',  # 机器学习+无线
        'cat:eess.SP AND (machine learning OR deep learning)',  # 信号处理+ML
        'cat:cs.NI AND (AI OR neural network)',  # 网络+AI
        'cat:eess.SY AND (federated learning OR reinforcement learning)',  # 系统+学习
    ]
    
    def search_papers(self, max_results: int = 200) -> List[Dict]:
        """搜索相关论文"""
        all_papers = []
        
        for query in self.QUERIES:
            print(f"🔍 arXiv搜索: {query[:50]}...")
            
            params = {
                'search_query': query,
                'start': 0,
                'max_results': max_results // len(self.QUERIES),
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            try:
                response = requests.get(self.API_URL, params=params)
                response.raise_for_status()
                
                # 解析Atom feed
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                # Atom命名空间
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                for entry in root.findall('atom:entry', ns):
                    title = entry.find('atom:title', ns)
                    authors = entry.findall('atom:author', ns)
                    summary = entry.find('atom:summary', ns)
                    published = entry.find('atom:published', ns)
                    
                    paper = {
                        'title': title.text.strip() if title is not None else '',
                        'authors': [
                            a.find('atom:name', ns).text 
                            for a in authors 
                            if a.find('atom:name', ns) is not None
                        ],
                        'abstract': summary.text.strip() if summary is not None else '',
                        'published': published.text[:10] if published is not None else '',
                        'url': entry.find('atom:id', ns).text if entry.find('atom:id', ns) is not None else ''
                    }
                    all_papers.append(paper)
                
                time.sleep(3)  # 礼貌延迟
                
            except Exception as e:
                print(f"❌ arXiv搜索失败: {e}")
                continue
        
        print(f"✅ 共获取 {len(all_papers)} 篇论文")
        return all_papers


class SemanticScholarMiner:
    """Semantic Scholar挖掘器"""
    
    API_URL = "https://api.semanticscholar.org/graph/v1"
    
    # AI + 无线通信关键词
    AI_TERMS = ['machine learning', 'deep learning', 'neural network', 
                'federated learning', 'reinforcement learning', 'AI']
    WIRELESS_TERMS = ['wireless communication', '5G', '6G', 'MIMO', 
                      'OFDM', 'beamforming', 'channel estimation', 'mmWave']
    
    def search_authors(self, query: str, fields: List[str] = None, limit: int = 100) -> List[Dict]:
        """搜索作者"""
        fields = fields or ['name', 'affiliations', 'paperCount', 'citationCount', 'hIndex', 'homepage']
        
        url = f"{self.API_URL}/author/search"
        params = {
            'query': query,
            'fields': ','.join(fields),
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            print(f"❌ Semantic Scholar搜索失败: {e}")
            return []
    
    def get_author_papers(self, author_id: str, limit: int = 100) -> List[Dict]:
        """获取作者论文"""
        url = f"{self.API_URL}/author/{author_id}/papers"
        params = {
            'fields': 'title,abstract,year,citationCount,fieldsOfStudy',
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            return []
    
    def find_ai_wireless_researchers(self, chinese_focus: bool = True) -> List[AcademicProfile]:
        """寻找AI+无线通信研究者（华人聚焦）"""
        print("\n" + "="*60)
        print("🔬 搜索AI+无线通信研究者")
        if chinese_focus:
            print("🎯 聚焦模式: 海外华人学者")
        print("="*60)
        
        # 搜索查询组合（华人学者关键词）
        search_queries = [
            'machine learning wireless communication',
            'deep learning 5G',
            'AI MIMO beamforming',
            'federated learning edge computing',
            'neural network channel estimation',
            'semantic communication deep learning',
            'reinforcement learning resource allocation wireless',
            'mmWave machine learning'
        ]
        
        all_authors = []
        seen_ids = set()
        
        for query in search_queries:
            print(f"\n🔍 搜索: {query}")
            authors = self.search_authors(query, limit=100)  # 增加获取数量
            
            for author in authors:
                author_id = author.get('authorId')
                if author_id in seen_ids:
                    continue
                seen_ids.add(author_id)
                all_authors.append(author)
            
            time.sleep(1)
        
        print(f"\n✅ 发现 {len(all_authors)} 位作者，分析论文并识别华人学者...")
        
        # 华人姓氏识别
        chinese_surnames = ['zhang', 'li', 'wang', 'liu', 'chen', 'yang', 
                           'zhao', 'huang', 'zhou', 'wu', 'xu', 'sun', 'hu',
                           'zhu', 'gao', 'lin', 'he', 'guo', 'ma', 'luo',
                           'liang', 'song', 'zheng', 'xie', 'han', 'tang',
                           'feng', 'yu', 'dong', 'xiao', 'cheng', 'cao',
                           'yuan', 'deng', 'xue', 'tian', 'pan', 'wei', 'jiang']
        
        # 分析每位作者的论文
        profiles = []
        
        for i, author in enumerate(all_authors):
            if i % 10 == 0:
                print(f"  处理中... {i}/{len(all_authors)}")
            
            author_id = author.get('authorId')
            papers = self.get_author_papers(author_id, limit=50)
            
            ai_papers = []
            wireless_papers = []
            
            for paper in papers:
                title = paper.get('title', '').lower()
                abstract = paper.get('abstract', '') or ''
                abstract_lower = abstract.lower()
                fields = paper.get('fieldsOfStudy', []) or []
                
                text = f"{title} {abstract_lower}"
                
                # 检查AI相关
                if any(term in text for term in self.AI_TERMS):
                    ai_papers.append(paper.get('title'))
                
                # 检查无线通信相关
                if any(term in text for term in self.WIRELESS_TERMS):
                    wireless_papers.append(paper.get('title'))
            
            # 华人姓名识别
            author_name_lower = author.get('name', '').lower()
            is_chinese = any(surname in author_name_lower.split() 
                            for surname in chinese_surnames)
            
            # 检查affiliations是否有中国机构（排除国内学者）
            affiliations = author.get('affiliations', []) or []
            has_china_affiliation = any(
                any(term in (aff or '').lower() for term in 
                    ['china', 'beijing', 'shanghai', 'tsinghua', 'peking', 
                     'fudan', 'zhejiang', 'sjtu', 'ustc', 'xian', 'harbin',
                     'nanjing', 'wuhan', 'chengdu', 'guangzhou', 'shenzhen'])
                for aff in affiliations
            )
            
            # 海外华人 = 华人姓名 + 非中国机构
            is_overseas_chinese = is_chinese and not has_china_affiliation
            
            # 只有双领域都有才计算分数
            if ai_papers and wireless_papers:
                # 计算匹配分数
                ai_ratio = len(ai_papers) / len(papers) if papers else 0
                wireless_ratio = len(wireless_papers) / len(papers) if papers else 0
                
                # 基础分数
                base_score = (ai_ratio + wireless_ratio) / 2
                
                # h-index加权（青年领军人才：h-index 10-30）
                h_index = author.get('hIndex', 0) or 0
                if 10 <= h_index <= 30:
                    h_weight = 0.25  # 青年领军加分
                else:
                    h_weight = min(h_index / 40, 0.2)
                
                # 引用加权
                citations = author.get('citationCount', 0) or 0
                cite_weight = min(citations / 2000, 0.15)
                
                match_score = min(base_score + h_weight + cite_weight, 1.0)
                
                # 海外华人加分
                if is_overseas_chinese:
                    match_score = min(match_score + 0.15, 1.0)
                    chinese_tag = "🏮海外华人"
                elif is_chinese and has_china_affiliation:
                    chinese_tag = "🇨🇳国内学者"
                else:
                    chinese_tag = ""
                
                profile = AcademicProfile(
                    name=author.get('name', ''),
                    affiliations=affiliations,
                    papers=papers[:5],  # 只保存前5篇
                    citations=citations,
                    h_index=h_index,
                    ai_papers=ai_papers[:5],
                    wireless_papers=wireless_papers[:5],
                    match_score=match_score,
                    homepage=author.get('homepage', '') or ''
                )
                
                profiles.append(profile)
                
                if match_score >= 0.6:
                    print(f"\n⭐ 高分研究者: {profile.name} {chinese_tag}")
                    print(f"   分数: {match_score:.2f}")
                    print(f"   机构: {', '.join(profile.affiliations[:2])}")
                    print(f"   h-index: {h_index}, 引用: {citations}")
            
            time.sleep(0.5)  # 礼貌延迟
        
        # 排序
        profiles.sort(key=lambda x: x.match_score, reverse=True)
        return profiles


class AcademicTalentAggregator:
    """学术人才聚合器"""
    
    def __init__(self):
        self.arxiv = ArxivMiner()
        self.s2 = SemanticScholarMiner()
    
    def run_full_search(self) -> Dict:
        """运行完整搜索"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'arxiv_papers': [],
            'semantic_scholar_profiles': []
        }
        
        # 1. arXiv搜索
        print("\n" + "="*60)
        print("📚 Phase 1: arXiv论文挖掘")
        print("="*60)
        arxiv_papers = self.arxiv.search_papers(max_results=100)
        results['arxiv_papers'] = arxiv_papers
        
        # 2. Semantic Scholar搜索
        print("\n" + "="*60)
        print("🎓 Phase 2: Semantic Scholar研究者挖掘")
        print("="*60)
        s2_profiles = self.s2.find_ai_wireless_researchers()
        results['semantic_scholar_profiles'] = [asdict(p) for p in s2_profiles]
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """生成报告"""
        lines = [
            "# 学术人才发现报告 (AI+无线通信)",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "\n## 数据来源",
            f"- arXiv论文: {len(results['arxiv_papers'])} 篇",
            f"- Semantic Scholar研究者: {len(results['semantic_scholar_profiles'])} 位",
            "\n## 高分研究者 (匹配度≥0.6)",
            ""
        ]
        
        profiles = results['semantic_scholar_profiles']
        high_score = [p for p in profiles if p.get('match_score', 0) >= 0.6]
        
        for i, p in enumerate(high_score[:20], 1):  # Top 20
            lines.extend([
                f"### {i}. {p['name']}",
                f"- **匹配分数**: {p['match_score']:.2f}",
                f"- **h-index**: {p['h_index']}",
                f"- **总引用**: {p['citations']}",
                f"- **机构**: {', '.join(p['affiliations'][:2])}",
                f"- **AI论文**: {len(p['ai_papers'])} 篇",
                f"- **无线论文**: {len(p['wireless_papers'])} 篇",
            ])
            
            if p.get('homepage'):
                lines.append(f"- **主页**: {p['homepage']}")
            
            lines.append("")
        
        return '\n'.join(lines)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='学术人才挖掘器')
    parser.add_argument('--output', default='academic_talents.json',
                       help='输出文件')
    parser.add_argument('--report', default='academic_talents_report.md',
                       help='报告文件')
    
    args = parser.parse_args()
    
    # 运行聚合器
    aggregator = AcademicTalentAggregator()
    results = aggregator.run_full_search()
    
    # 保存结果
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 结果已保存到 {args.output}")
    
    # 生成报告
    report = aggregator.generate_report(results)
    with open(args.report, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"📝 报告已保存到 {args.report}")
    
    # 统计
    profiles = results['semantic_scholar_profiles']
    high_score = len([p for p in profiles if p.get('match_score', 0) >= 0.6])
    print(f"\n📊 统计:")
    print(f"   总研究者: {len(profiles)}")
    print(f"   高分研究者(≥0.6): {high_score}")


if __name__ == '__main__':
    main()
