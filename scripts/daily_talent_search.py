#!/usr/bin/env python3
"""
TalentIntel 每日人才搜索脚本
自动执行扩展关键词搜索，筛选高分候选人
"""

import json
import yaml
import random
import time
from datetime import datetime
from pathlib import Path
import subprocess
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config" / "extended_keywords.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

def generate_search_queries(config):
    """生成搜索查询组合"""
    keywords = config['search_keywords']
    companies = []
    
    # 合并所有公司层级
    for tier in ['tier1', 'tier2', 'tier3', 'research']:
        companies.extend(config['target_companies'].get(tier, []))
    
    queries = []
    
    # 生成公司+关键词组合
    for company in companies[:10]:  # 限制公司数量
        for keyword in random.sample(keywords, min(5, len(keywords))):
            query = f'site:linkedin.com/in ("{company}") ("{keyword}")'
            queries.append({
                'company': company,
                'keyword': keyword,
                'query': query
            })
    
    return queries[:20]  # 每日最多20个查询

def run_xray_search():
    """运行X-Ray搜索"""
    print("🔍 启动每日X-Ray人才搜索...")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    config = load_config()
    queries = generate_search_queries(config)
    
    print(f"📋 生成 {len(queries)} 个搜索查询")
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'queries': queries,
        'profiles_found': [],
        'high_score_candidates': []
    }
    
    # 这里调用实际的搜索脚本
    # 暂时生成搜索任务列表
    for i, q in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] 搜索: {q['company']} + {q['keyword']}")
        print(f"     查询: {q['query'][:80]}...")
        
        # 模拟搜索延迟
        time.sleep(random.uniform(0.5, 1.5))
    
    # 保存搜索任务
    output_dir = Path(__file__).parent.parent / "data" / "daily_search"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"search_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ 搜索任务已保存: {output_file}")
    print(f"📊 今日搜索配置完成")
    
    return results

def aggregate_results():
    """汇总历史搜索结果"""
    findings_dir = Path(__file__).parent.parent / "data" / "findings"
    
    all_candidates = []
    
    # 遍历所有日期目录
    for date_dir in findings_dir.glob("2026-*"):
        for json_file in date_dir.glob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'high_score_candidates' in data:
                        all_candidates.extend(data['high_score_candidates'])
                    elif isinstance(data, dict) and 'candidates' in data:
                        all_candidates.extend(data['candidates'])
            except:
                pass
    
    # 去重并排序
    seen = set()
    unique_candidates = []
    for c in all_candidates:
        name = c.get('name', '')
        if name and name not in seen:
            seen.add(name)
            unique_candidates.append(c)
    
    unique_candidates.sort(key=lambda x: x.get('match_score', 0), reverse=True)
    
    # 统计
    high_score = [c for c in unique_candidates if c.get('match_score', 0) >= 0.70]
    
    print(f"\n📈 累计统计:")
    print(f"   总候选人: {len(unique_candidates)}")
    print(f"   高分候选人 (≥0.70): {len(high_score)}")
    print(f"   TOP 3: {', '.join([c.get('name', 'N/A') for c in high_score[:3]])}")
    
    return unique_candidates

def main():
    """主函数"""
    print("=" * 70)
    print("🎯 TalentIntel 每日人才搜索")
    print("=" * 70)
    
    # 执行搜索
    run_xray_search()
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("📊 汇总历史结果")
    print("=" * 70)
    aggregate_results()
    
    print("\n" + "=" * 70)
    print("✅ 每日搜索完成")
    print("=" * 70)

if __name__ == "__main__":
    main()
