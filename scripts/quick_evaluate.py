#!/usr/bin/env python3
"""
快速人才评估 - 使用已有链接进行评估
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

# 导入简化版评估模块
import sys
sys.path.insert(0, str(Path(__file__).parent))

from auto_discovery_simple import SimpleLLMClient, SimpleBrowser


# 测试链接列表
TEST_PROFILES = [
    {"url": "https://www.linkedin.com/in/owen-wen-731524334/", "name": "Owen Wen"},
    {"url": "https://www.linkedin.com/in/yousef-shawky-ba0239167/", "name": "Yousef Shawky"},
    {"url": "https://www.linkedin.com/in/wu-kwong-yiu-a3776423a/", "name": "Wu Kwong Yiu"},
    {"url": "https://www.linkedin.com/in/gauravkumarindia/", "name": "Gaurav Kumar"},
]


async def evaluate_profiles():
    """评估测试档案"""
    print("="*70)
    print("🚀 TalentIntel 快速人才评估")
    print("="*70)
    
    browser = SimpleBrowser(use_proxy=False)
    llm = SimpleLLMClient()
    
    results = []
    high_scores = []
    
    for i, profile in enumerate(TEST_PROFILES, 1):
        print(f"\n[{i}/{len(TEST_PROFILES)}] 评估: {profile['name']}")
        print(f"   URL: {profile['url']}")
        
        # 获取档案内容
        html = await browser.request(profile['url'], timeout=25)
        
        if html:
            # LLM评估
            result = await llm.evaluate_profile(html)
            full_result = {**profile, **result}
            results.append(full_result)
            
            # 显示结果
            is_chinese = result.get("chinese_origin", {}).get("is_chinese", False)
            final_score = result.get("final_score", 0)
            priority = result.get("priority", "LOW")
            
            chinese_tag = "🇨🇳" if is_chinese else ""
            priority_icon = "🔥" if priority == "HIGH" else "⭐" if priority == "MEDIUM" else "⚪"
            
            print(f"   基础分: {result.get('match_score', 0):.2f} | "
                  f"华人加分: +{result.get('chinese_bonus', 0):.2f} | "
                  f"最终分: {final_score:.2f} {priority_icon} {chinese_tag}")
            
            if final_score >= 0.7:
                high_scores.append(full_result)
                print(f"   ✅ 高分候选人! 保存到 findings")
        else:
            print(f"   ❌ 获取档案失败")
        
        if i < len(TEST_PROFILES):
            await asyncio.sleep(3)
    
    # 保存结果
    output_dir = Path("data/findings") / datetime.now().strftime("%Y-%m-%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存高分候选人
    for result in high_scores:
        name = result.get('basic_info', {}).get('name', result.get('name', 'unknown'))
        name_clean = re.sub(r'[^\w\s]', '', name).replace(' ', '_').lower()[:20]
        score_int = int(result.get('final_score', 0) * 100000)
        
        file_path = output_dir / f"{name_clean}_{score_int}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 保存汇总
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_evaluated": len(results),
        "high_score_count": len(high_scores),
        "high_score_threshold": 0.7,
        "profiles": results
    }
    
    with open(output_dir / "summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    # 打印统计
    print("\n" + "="*70)
    print("📊 评估统计")
    print("="*70)
    print(f"总计评估: {len(results)} 人")
    print(f"🔥 高分候选人 (≥0.7): {len(high_scores)} 人")
    
    if high_scores:
        print(f"\n🏆 高分候选人:")
        for r in sorted(high_scores, key=lambda x: x.get('final_score', 0), reverse=True):
            name = r.get('basic_info', {}).get('name', r.get('name', 'Unknown'))
            company = r.get('basic_info', {}).get('current_company', 'Unknown')
            score = r.get('final_score', 0)
            flag = "🇨🇳" if r.get('chinese_origin', {}).get('is_chinese') else ""
            print(f"   {name} @ {company}: {score:.2f} {flag}")
    
    print(f"\n💾 结果已保存到: {output_dir}")
    print("\n✅ 完成!")
    
    return results, high_scores


if __name__ == "__main__":
    results, high_scores = asyncio.run(evaluate_profiles())
    print(f"\n🎯 RESULTS: total={len(results)}, high_score={len(high_scores)}")
