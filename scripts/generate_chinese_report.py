#!/usr/bin/env python3
"""
华人候选人整体报告生成器
每次洞察后自动刷新华人候选人整体报告
聚合所有数据源，生成统一视图
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# 华人姓氏库
CHINESE_SURNAMES = {
    'chen', 'wang', 'li', 'liu', 'zhang', 'zhao', 'yang', 'wu', 'zhou', 
    'huang', 'xu', 'sun', 'hu', 'ma', 'guo', 'he', 'zheng', 'xie', 'lin',
    'tang', 'deng', 'ye', 'cheng', 'cai', 'cao', 'dai', 'ding', 'dong', 
    'du', 'duan', 'fan', 'fang', 'fu', 'gao', 'ge', 'gong', 'guan', 'han',
    'hao', 'hong', 'hou', 'jiang', 'jin', 'kang', 'kong', 'lai', 'lan', 
    'lei', 'liang', 'liao', 'lu', 'luo', 'mao', 'meng', 'miao', 'ni', 
    'ning', 'pan', 'peng', 'qi', 'qian', 'qiao', 'qin', 'qiu', 'qu',
    'ren', 'rong', 'shao', 'shen', 'shi', 'song', 'su', 'tan', 'tao', 
    'tian', 'wan', 'wei', 'wen', 'weng', 'xia', 'xiang', 'xiao', 'xin', 
    'xing', 'xiong', 'xue', 'yan', 'yao', 'yi', 'yin', 'ying', 'you', 
    'yu', 'yuan', 'zeng', 'zhan', 'zhuang', 'zhuo', 'zong', 'zu', 'zuo'
}

# 北美地区
NORTH_AMERICA = ['united states', 'usa', 'california', 'ca', 'texas', 'tx', 
                 'new york', 'ny', 'washington', 'wa', 'massachusetts', 'ma',
                 'illinois', 'il', 'colorado', 'co', 'north carolina', 'nc',
                 'oregon', 'or', 'arizona', 'az', 'florida', 'fl', 'georgia', 'ga',
                 'canada', 'toronto', 'vancouver', 'montreal', 'ottawa',
                 'palo alto', 'san francisco', 'san jose', 'seattle', 'austin',
                 'boston', 'new york city', 'mountain view', 'sunnyvale', 'cupertino',
                 'santa clara', 'menlo park', 'redmond', 'bellevue', 'san diego']

# 大厂列表
BIG_TECH = ['google', 'meta', 'facebook', 'nvidia', 'apple', 'microsoft', 'amazon', 
            'aws', 'qualcomm', 'intel', 'broadcom', 'cisco', 'amd', 'tesla', 
            'oracle', 'ibm', 'marvell', 'texas instruments', 'ericsson', 'samsung',
            'bytedance', 'tiktok', 'alibaba', 'tencent', 'baidu']

# 排除的公司（中国大陆）
EXCLUDED_COMPANIES = ['huawei', 'zte']

# 中国大陆关键词（用于排除）
CHINA_LOCATIONS = ['china', 'beijing', 'shanghai', 'shenzhen', 'guangzhou', 'hangzhou', 
                   'chengdu', 'wuhan', 'xi\'an', 'nanjing', 'suzhou', 'qingdao',
                   '中国', '北京', '上海', '深圳', '广州', '杭州']


class ChineseTalentReport:
    """华人候选人报告生成器"""
    
    def __init__(self, base_dir: str = "/Users/cooga/.openclaw/workspace/Project/TalentIntel"):
        self.base_dir = Path(base_dir)
        self.findings_dir = self.base_dir / "data" / "findings"
        self.active_dir = self.base_dir / "data" / "active"
        self.chinese_candidates = []
        self.stats = {
            "total_chinese": 0,
            "high_score_chinese": 0,  # >= 0.7
            "na_chinese": 0,  # 北美地区
            "by_company": {},
            "by_location": {},
        }
        self.target_chinese = 40
    
    def is_chinese_name(self, name: str) -> bool:
        """判断是否为华人姓名"""
        if not name or name == 'N/A':
            return False
        name_lower = name.lower()
        words = name_lower.replace('.', ' ').replace('-', ' ').split()
        for word in words:
            if word in CHINESE_SURNAMES:
                return True
        return False
    
    def is_north_america(self, location: str) -> bool:
        """判断是否北美地区"""
        if not location:
            return False
        location_lower = location.lower()
        return any(loc in location_lower for loc in NORTH_AMERICA)
    
    def extract_company(self, text: str) -> str:
        """提取公司信息"""
        if not text:
            return 'Unknown'
        text_lower = text.lower()
        for company in BIG_TECH:
            if company in text_lower:
                return company.title()
        return text.split(',')[0] if ',' in text else text
    
    def is_excluded_company(self, company: str) -> bool:
        """检查是否在排除公司列表中"""
        if not company:
            return False
        company_lower = company.lower()
        for excluded in EXCLUDED_COMPANIES:
            if excluded in company_lower:
                return True
        return False
    
    def is_in_china(self, location: str) -> bool:
        """检查是否在中国大陆"""
        if not location:
            return False
        location_lower = location.lower()
        for china_loc in CHINA_LOCATIONS:
            if china_loc in location_lower:
                return True
        return False
    
    def load_all_candidates(self):
        """加载所有候选人数据"""
        print("🔍 扫描所有候选人数据...")
        
        all_candidates = []
        
        # 1. 优先从 active/candidates.json 读取（Phase 2 主库）
        candidates_file = self.active_dir / "candidates.json"
        if candidates_file.exists():
            try:
                with open(candidates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "candidates" in data:
                        all_candidates.extend(data["candidates"])
                        print(f"   📁 从 active/candidates.json 加载 {len(data['candidates'])} 人")
            except Exception as e:
                print(f"   ⚠️ 读取 candidates.json 失败: {e}")
        
        # 2. 从 findings 目录加载历史数据（Phase 1 兼容）
        findings_count = 0
        if self.findings_dir.exists():
            for json_file in self.findings_dir.rglob("*.json"):
                if "summary" in json_file.name:
                    continue
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # 处理不同格式的数据
                        if isinstance(data, dict):
                            if "candidates" in data:
                                all_candidates.extend(data["candidates"])
                                findings_count += len(data["candidates"])
                            elif "match_score" in data:
                                all_candidates.append(data)
                                findings_count += 1
                except Exception as e:
                    pass
        
        if findings_count > 0:
            print(f"   📁 从 findings/ 历史数据加载 {findings_count} 人")
        
        print(f"✅ 已加载 {len(all_candidates)} 个候选人记录")
        return all_candidates
    
    def filter_chinese_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """筛选华人候选人 - 海外华人（排除华为/中兴和中国大陆）"""
        chinese = []
        excluded_count = 0
        
        for c in candidates:
            # 获取姓名
            name = c.get('name', '')
            if not name:
                eval_data = c.get('evaluation', {})
                basic = eval_data.get('basic_info', {})
                name = basic.get('name', '')
            
            # 判断是否为华人（优先使用 is_chinese 标记，其次按姓氏）
            is_chinese = c.get('is_chinese', False)
            if not is_chinese:
                is_chinese = self.is_chinese_name(name)
            
            if is_chinese:
                # 补充信息
                eval_data = c.get('evaluation', {})
                basic = eval_data.get('basic_info', {})
                
                company = c.get('company', '') or basic.get('current_company', self.extract_company(name))
                location = c.get('location', '') or basic.get('location', '')
                
                # 检查排除条件：华为/中兴
                if self.is_excluded_company(company):
                    excluded_count += 1
                    print(f"   🚫 排除 Huawei/ZTE: {name} @ {company}")
                    continue
                
                # 检查排除条件：中国大陆地区
                if self.is_in_china(location):
                    excluded_count += 1
                    print(f"   🚫 排除中国大陆: {name} @ {location}")
                    continue
                
                enriched = {
                    'name': name,
                    'url': c.get('url', '') or c.get('linkedin_url', ''),
                    'match_score': c.get('match_score', 0),
                    'company': company,
                    'role': c.get('title', '') or basic.get('current_role', ''),
                    'location': location,
                    'ai_level': eval_data.get('ai_expertise', {}).get('level', ''),
                    'wireless_level': eval_data.get('wireless_expertise', {}).get('level', ''),
                    'is_north_america': self.is_north_america(location),
                    'source_file': c.get('_source', c.get('source', 'unknown'))
                }
                chinese.append(enriched)
        
        # 去重（基于 URL）
        seen_urls = set()
        unique = []
        for c in chinese:
            url = c.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(c)
        
        if excluded_count > 0:
            print(f"   ⚠️ 共排除 {excluded_count} 位（华为/中兴/中国大陆）")
        
        return unique
    
    def calculate_stats(self, candidates: List[Dict]):
        """计算统计信息"""
        self.stats["total_chinese"] = len(candidates)
        self.stats["high_score_chinese"] = len([c for c in candidates if c.get('match_score', 0) >= 0.7])
        self.stats["na_chinese"] = len([c for c in candidates if c.get('is_north_america', False)])
        
        # 公司分布
        company_dist = {}
        for c in candidates:
            company = c.get('company', 'Unknown')
            company_dist[company] = company_dist.get(company, 0) + 1
        self.stats["by_company"] = dict(sorted(company_dist.items(), key=lambda x: x[1], reverse=True)[:15])
        
        # 地点分布
        location_dist = {}
        for c in candidates:
            loc = c.get('location', 'Unknown')
            loc_short = loc.split(',')[0] if ',' in loc else loc
            location_dist[loc_short] = location_dist.get(loc_short, 0) + 1
        self.stats["by_location"] = dict(sorted(location_dist.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def generate_markdown_report(self) -> str:
        """生成 Markdown 报告"""
        candidates = sorted(self.chinese_candidates, key=lambda x: x.get('match_score', 0), reverse=True)
        high_score = [c for c in candidates if c.get('match_score', 0) >= 0.7]
        na_candidates = [c for c in candidates if c.get('is_north_america', False)]
        
        progress_pct = (len(high_score) / self.target_chinese * 100) if self.target_chinese > 0 else 0
        
        report = f"""# 🇺🇸 海外华人AI+无线通信专家整体报告

> **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
> **数据来源**: TalentIntel 人才检索系统  
> **筛选条件**: 海外华人 | 排除华为/中兴 | 排除中国大陆地区

---

## 📊 总体统计

| 指标 | 数值 | 目标 | 进度 |
|------|------|------|------|
| 海外华人候选人总数 | {self.stats['total_chinese']} | - | - |
| **高分候选人 (≥0.7)** | **{self.stats['high_score_chinese']}** | {self.target_chinese} | **{progress_pct:.1f}%** |
| 北美地区候选人 | {self.stats['na_chinese']} | - | - |

---

## 🏢 公司分布 (Top 15)

"""
        for company, count in self.stats['by_company'].items():
            bar = '█' * count + '░' * (10 - min(count, 10))
            report += f"- **{company}**: {bar} {count}人\n"
        
        report += f"""
---

## 🌎 地点分布 (Top 10)

"""
        for loc, count in self.stats['by_location'].items():
            report += f"- {loc}: {count}人\n"
        
        # 高分候选人详细列表
        report += f"""
---

## 🏆 高分华人候选人列表 (≥0.7)

共 **{len(high_score)}** 位高分候选人

"""
        for i, c in enumerate(high_score, 1):
            na_tag = "🇺🇸" if c.get('is_north_america') else ""
            report += f"""### {i}. {na_tag} {c['name']}

- **匹配度**: ⭐ {c['match_score']:.2f}
- **公司**: {c['company']}
- **职位**: {c['role']}
- **地点**: {c['location']}
- **LinkedIn**: {c['url']}
- **AI专长**: {c.get('ai_level', 'N/A')}
- **无线专长**: {c.get('wireless_level', 'N/A')}

---

"""
        
        # 其他候选人
        other = [c for c in candidates if c.get('match_score', 0) < 0.7]
        if other:
            report += f"""## 📋 其他候选人 (0.5-0.7)

共 **{len(other)}** 位候选人

| 姓名 | 匹配度 | 公司 | 地点 | 北美 |
|------|--------|------|------|------|
"""
            for c in other[:30]:  # 限制显示数量
                na_mark = "✅" if c.get('is_north_america') else ""
                report += f"| {c['name']} | {c['match_score']:.2f} | {c['company']} | {c['location']} | {na_mark} |\n"
        
        # 总结与建议
        report += f"""
---

## 🎯 目标达成情况

- **华人高分候选人**: {len(high_score)}/{self.target_chinese} ({progress_pct:.1f}%)
- **状态**: {'✅ 目标达成!' if len(high_score) >= self.target_chinese else '⏳ 进行中...'}

### 下一步建议

"""
        if len(high_score) < self.target_chinese:
            remaining = self.target_chinese - len(high_score)
            report += f"""
1. **继续搜索**: 还需 {remaining} 位高分华人候选人
2. **北美专项**: 当前北美华人 {len(na_candidates)} 人，可考虑增加北美地区搜索权重
3. **公司覆盖**: 已覆盖 {len(self.stats['by_company'])} 家公司，可扩展至更多初创公司
"""
        else:
            report += """
1. ✅ 目标已达成！建议开始联系候选人
2. 准备 outreach 邮件模板
3. 建立候选人跟进系统
"""
        
        return report
    
    def save_report(self, report: str):
        """保存报告"""
        # 保存 Markdown 报告
        report_file = self.base_dir / "CHINESE_TALENT_OVERALL_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 保存 JSON 数据
        json_file = self.base_dir / "data" / "chinese_talent_summary.json"
        json_file.parent.mkdir(parents=True, exist_ok=True)
        
        summary_data = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "target": self.target_chinese,
            "candidates": self.chinese_candidates
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        return report_file, json_file
    
    def run(self) -> str:
        """运行报告生成"""
        print("=" * 80)
        print("🇨🇳 华人候选人整体报告生成")
        print("=" * 80)
        
        # 1. 加载所有候选人
        all_candidates = self.load_all_candidates()
        
        # 2. 筛选华人候选人
        self.chinese_candidates = self.filter_chinese_candidates(all_candidates)
        print(f"\n✅ 找到 {len(self.chinese_candidates)} 位华人候选人")
        
        # 3. 计算统计
        self.calculate_stats(self.chinese_candidates)
        
        # 4. 生成报告
        report = self.generate_markdown_report()
        
        # 5. 保存报告
        report_file, json_file = self.save_report(report)
        
        print(f"\n{'=' * 80}")
        print("✅ 华人候选人报告已生成!")
        print(f"{'=' * 80}")
        print(f"📄 Markdown报告: {report_file}")
        print(f"📊 JSON数据: {json_file}")
        print(f"\n📈 统计摘要:")
        print(f"   华人候选人总数: {self.stats['total_chinese']}")
        print(f"   高分候选人(≥0.7): {self.stats['high_score_chinese']} / {self.target_chinese}")
        print(f"   北美地区: {self.stats['na_chinese']}")
        
        return str(report_file)


def main():
    """主函数 - 供外部调用"""
    generator = ChineseTalentReport()
    report_path = generator.run()
    return report_path


if __name__ == "__main__":
    main()
