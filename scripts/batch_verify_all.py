#!/usr/bin/env python3
"""
TalentIntel 批量验证工具 - 验证所有待验证候选人
更新推荐理由和匹配分数
"""

import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

LINKEDIN_PROFILE = "/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/profiles/linkedin_01"

# 人才评估标准
EVALUATION_CRITERIA = {
    "ai_keywords": ["AI", "machine learning", "deep learning", "neural network", "LLM", "generative AI"],
    "wireless_keywords": ["wireless", "5G", "6G", "MIMO", "RAN", "communication", "signal processing", "OFDM"],
    "company_tier": {
        "T1": ["NVIDIA", "Google", "Apple", "Meta", "Microsoft", "OpenAI", "DeepMind"],
        "T2": ["Qualcomm", "Intel", "AMD", "Samsung", "Broadcom", "Marvell"],
        "T3": ["SpaceX", "Tesla", "Amazon", "Alibaba", "Tencent"]
    }
}


class CandidateEvaluator:
    """候选人评估器"""
    
    def __init__(self):
        self.results = []
    
    def calculate_match_score(self, profile_data: dict) -> float:
        """计算匹配分数 0-1"""
        score = 0.0
        
        # 1. AI 背景 (40%)
        ai_score = 0
        content = str(profile_data).lower()
        for kw in EVALUATION_CRITERIA["ai_keywords"]:
            if kw.lower() in content:
                ai_score += 0.1
        ai_score = min(ai_score, 0.4)
        
        # 2. Wireless 背景 (40%)
        wireless_score = 0
        for kw in EVALUATION_CRITERIA["wireless_keywords"]:
            if kw.lower() in content:
                wireless_score += 0.1
        wireless_score = min(wireless_score, 0.4)
        
        # 3. 公司层级 (10%)
        company_score = 0
        company = profile_data.get("company", "").lower()
        for tier, companies in EVALUATION_CRITERIA["company_tier"].items():
            if any(c.lower() in company for c in companies):
                company_score = {"T1": 0.1, "T2": 0.08, "T3": 0.05}[tier]
                break
        
        # 4. 职位级别 (10%)
        title_score = 0
        title = profile_data.get("title", "").lower()
        if any(kw in title for kw in ["senior", "principal", "staff", "lead"]):
            title_score = 0.08
        elif any(kw in title for kw in ["manager", "director", "vp", "head"]):
            title_score = 0.1
        elif "professor" in title:
            title_score = 0.1
        
        total_score = ai_score + wireless_score + company_score + title_score
        return round(min(total_score, 1.0), 2)
    
    def generate_recommendation(self, profile_data: dict) -> str:
        """生成推荐理由"""
        reasons = []
        
        name = profile_data.get("name", "")
        company = profile_data.get("company", "")
        title = profile_data.get("title", "")
        
        # 公司亮点
        for tier, companies in EVALUATION_CRITERIA["company_tier"].items():
            if any(c.lower() in company.lower() for c in companies):
                reasons.append(f"{company} - 顶尖科技公司背景")
                break
        
        # AI背景
        content = str(profile_data)
        ai_found = [kw for kw in EVALUATION_CRITERIA["ai_keywords"] if kw.lower() in content.lower()]
        if ai_found:
            reasons.append(f"AI技术专长: {', '.join(ai_found[:3])}")
        
        # Wireless背景
        wireless_found = [kw for kw in EVALUATION_CRITERIA["wireless_keywords"] if kw.lower() in content.lower()]
        if wireless_found:
            reasons.append(f"无线通信专长: {', '.join(wireless_found[:3])}")
        
        # 职位亮点
        if "phd" in title.lower() or "professor" in title.lower():
            reasons.append("博士/教授背景，学术影响力强")
        
        if not reasons:
            reasons.append(f"{company} {title}，有待进一步评估")
        
        return " | ".join(reasons)


async def batch_verify():
    """批量验证"""
    
    print("="*80)
    print("🚀 TalentIntel 批量验证工具")
    print("验证所有待验证候选人并更新推荐理由")
    print("="*80)
    
    # 加载数据
    db_path = '/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/clean_candidates_db.json'
    with open(db_path, 'r') as f:
        data = json.load(f)
    
    candidates = data.get('candidates', [])
    
    # 获取待验证候选人
    pending = [c for c in candidates if c.get('verified') in ['pending', False]]
    
    # 按分数排序
    pending_sorted = sorted(pending, key=lambda x: -x.get('match_score', 0))
    
    print(f"\n总候选人: {len(candidates)}")
    print(f"待验证: {len(pending)}")
    print(f"\n将验证全部 {len(pending)} 位候选人")
    print("="*80)
    
    evaluator = CandidateEvaluator()
    verified_results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=LINKEDIN_PROFILE,
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        for i, candidate in enumerate(pending_sorted, 1):
            print(f"\n[{i}/{len(pending)}] {candidate.get('name')}")
            print("-"*80)
            
            result = await verify_candidate(browser, candidate, evaluator)
            verified_results.append(result)
            
            # 每5人保存一次进度
            if i % 5 == 0:
                save_progress(verified_results, candidates, db_path)
                print(f"   💾 进度已保存 ({i}/{len(pending)})")
        
        await browser.close()
    
    # 最终保存
    final_data = save_progress(verified_results, candidates, db_path, final=True)
    
    # 生成统计
    generate_statistics(final_data)
    
    print("\n" + "="*80)
    print("✅ 批量验证完成")
    print("="*80)


async def verify_candidate(browser, candidate: dict, evaluator: CandidateEvaluator) -> dict:
    """验证单个候选人"""
    name = candidate.get('name', '')
    linkedin_url = candidate.get('linkedin_url', '')
    expected_company = candidate.get('company', '')
    expected_title = candidate.get('title', '')
    
    result = {
        "original": candidate,
        "verified_status": "unverified",
        "found_name": None,
        "found_company": None,
        "found_title": None,
        "new_score": candidate.get('match_score', 0),
        "new_recommendation": candidate.get('background', ''),
        "notes": []
    }
    
    if not linkedin_url:
        result["notes"].append("无LinkedIn链接")
        return result
    
    try:
        page = await browser.new_page()
        await page.goto(linkedin_url, timeout=30000)
        await asyncio.sleep(3)
        
        title = await page.title()
        
        # 检查页面有效性
        if name.replace(" ", "") in title.replace(" ", "") or name.split()[-1] in title:
            result["verified_status"] = "verified"
            result["notes"].append("LinkedIn档案存在")
            
            # 尝试提取信息
            try:
                # 提取可见文本
                text_content = await page.inner_text('body')
                
                # 构建档案数据用于评估
                profile_data = {
                    "name": name,
                    "company": expected_company,
                    "title": expected_title,
                    "content": text_content[:2000]  # 前2000字符
                }
                
                # 重新计算分数
                new_score = evaluator.calculate_match_score(profile_data)
                result["new_score"] = new_score
                
                # 生成推荐理由
                new_recommendation = evaluator.generate_recommendation(profile_data)
                result["new_recommendation"] = new_recommendation
                
                print(f"   ✅ 验证成功 | 新分数: {new_score}")
                print(f"   📝 推荐理由: {new_recommendation[:60]}...")
                
            except Exception as e:
                print(f"   ⚠️ 提取信息失败: {e}")
                result["notes"].append(f"提取信息失败: {e}")
        
        elif "Sign" in title or "Join" in title or title.strip() == "":
            result["verified_status"] = "unverified"
            result["notes"].append("LinkedIn需要登录或档案不存在")
            print(f"   ❌ 无法访问 | {title}")
        
        else:
            result["verified_status"] = "partial"
            result["notes"].append(f"页面标题: {title}")
            print(f"   ⚠️ 部分验证 | {title}")
        
        await page.close()
        
    except Exception as e:
        print(f"   ❌ 验证错误: {e}")
        result["notes"].append(f"Error: {str(e)}")
    
    return result


def save_progress(results: list, all_candidates: list, db_path: str, final: bool = False) -> dict:
    """保存进度"""
    # 更新候选人数据
    for result in results:
        original = result["original"]
        
        # 查找并更新原数据
        for candidate in all_candidates:
            if candidate.get('linkedin_url') == original.get('linkedin_url'):
                candidate['verified'] = result["verified_status"] == "verified"
                candidate['verification_status'] = result["verified_status"]
                candidate['verification_notes'] = " | ".join(result["notes"])
                
                if result["verified_status"] == "verified":
                    candidate['match_score'] = result["new_score"]
                    candidate['background'] = result["new_recommendation"]
                    candidate['verified_at'] = datetime.now().isoformat()
                
                break
    
    if final:
        # 保存完整数据库
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_candidates": len(all_candidates),
                "candidates": all_candidates
            }, f, indent=2, ensure_ascii=False)
    
    # 保存进度报告
    progress_path = '/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/verification_progress.json'
    with open(progress_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "processed": len(results),
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    return {"candidates": all_candidates}


def generate_statistics(data: dict):
    """生成统计"""
    candidates = data.get('candidates', [])
    
    verified = sum(1 for c in candidates if c.get('verified') == True)
    pending = sum(1 for c in candidates if c.get('verified') == 'pending')
    unverified = sum(1 for c in candidates if c.get('verified') == False)
    
    # 高分候选人统计
    high_score = [c for c in candidates if c.get('match_score', 0) >= 0.8]
    
    print(f"\n{'='*80}")
    print("📊 验证统计")
    print(f"{'='*80}")
    print(f"总候选人: {len(candidates)}")
    print(f"✅ 已验证: {verified}")
    print(f"⏳ 待验证: {pending}")
    print(f"❌ 未验证: {unverified}")
    print(f"🏆 高分候选人 (≥0.8): {len(high_score)}")
    
    print(f"\n高分候选人列表:")
    for c in sorted(high_score, key=lambda x: -x.get('match_score', 0))[:10]:
        print(f"   {c.get('match_score', 0):.2f} | {c.get('name', '')[:25]:25} | {c.get('company', '')[:15]:15}")


if __name__ == "__main__":
    asyncio.run(batch_verify())
