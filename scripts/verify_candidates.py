#!/usr/bin/env python3
"""
TalentIntel 候选人批量验证脚本
使用Kimi Web Search验证候选人真实性
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List
import sys
sys.path.insert(0, '/Users/cooga/.openclaw/workspace/Project/TalentIntel/poc')

from kimi_web_search import KimiWebSearcher, KimiSearchResult


class CandidateVerifier:
    """候选人验证器"""
    
    def __init__(self):
        self.searcher = KimiWebSearcher()
        self.verification_log = []
    
    def load_candidates(self, filepath: str) -> List[Dict]:
        """加载候选人数据"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data.get('candidates', [])
    
    def verify_candidate(self, candidate: Dict) -> Dict:
        """验证单个候选人"""
        name = candidate.get('name', '')
        company = candidate.get('company', '')
        title = candidate.get('title', '')
        linkedin_url = candidate.get('linkedin_url', '')
        
        print(f"\n{'='*70}")
        print(f"🔍 验证: {name}")
        print(f"   公司: {company} | 职位: {title}")
        print(f"   LinkedIn: {linkedin_url}")
        
        verification_result = {
            "name": name,
            "original_score": candidate.get('match_score', 0),
            "original_priority": candidate.get('priority', ''),
            "verification_status": "pending",
            "verification_notes": [],
            "new_score": 0,
            "new_priority": "",
            "new_background": "",
            "search_results": {}
        }
        
        # 1. 搜索LinkedIn验证
        print(f"\n   [1/3] 搜索LinkedIn验证...")
        if linkedin_url:
            # 提取LinkedIn用户名
            linkedin_name = linkedin_url.split('/')[-1] if '/' in linkedin_url else ''
            query = f'"{name}" {company} linkedin.com/in/{linkedin_name}'
        else:
            query = f'"{name}" {company} linkedin.com/in'
        
        li_results = self.searcher.search(query, count=5)
        verification_result["search_results"]["linkedin"] = [r.to_dict() for r in li_results]
        
        # 检查是否能找到匹配
        li_verified = False
        if li_results:
            for result in li_results:
                if linkedin_url and linkedin_url in result.url:
                    li_verified = True
                    break
                # 或者检查名字和公司匹配
                if name.lower() in result.title.lower() and company.lower() in result.snippet.lower():
                    li_verified = True
                    break
        
        if li_verified:
            print(f"   ✅ LinkedIn 找到匹配")
            verification_result["verification_notes"].append("LinkedIn档案存在")
        else:
            print(f"   ❌ LinkedIn 未找到匹配")
            verification_result["verification_notes"].append("无法验证LinkedIn档案")
        
        # 2. 搜索专业背景（论文、项目等）
        print(f"\n   [2/3] 搜索专业背景...")
        bg_query = f'"{name}" {company} AI wireless 5G 6G research paper'
        bg_results = self.searcher.search(bg_query, count=5)
        verification_result["search_results"]["background"] = [r.to_dict() for r in bg_results]
        
        bg_verified = False
        ai_keywords = ['AI', 'machine learning', 'deep learning', 'neural']
        wireless_keywords = ['wireless', '5G', '6G', 'MIMO', 'RAN', 'communication']
        
        if bg_results:
            for result in bg_results:
                content = (result.title + ' ' + result.snippet).lower()
                has_ai = any(kw.lower() in content for kw in ai_keywords)
                has_wireless = any(kw.lower() in content for kw in wireless_keywords)
                
                if has_ai and has_wireless:
                    bg_verified = True
                    verification_result["new_background"] = result.snippet[:200]
                    break
        
        if bg_verified:
            print(f"   ✅ 找到AI+Wireless背景")
            verification_result["verification_notes"].append("确认AI+Wireless研究背景")
        else:
            print(f"   ⚠️ 未找到明确AI+Wireless背景")
            verification_result["verification_notes"].append("无法确认AI+Wireless背景")
        
        # 3. 搜索其他社交平台
        print(f"\n   [3/3] 搜索其他平台...")
        x_query = f'"{name}" {company} x.com OR twitter.com'
        x_results = self.searcher.search(x_query, count=3)
        verification_result["search_results"]["x"] = [r.to_dict() for r in x_results]
        
        if x_results:
            print(f"   ✅ 找到X/Twitter相关")
            verification_result["verification_notes"].append("有X/Twitter存在")
        
        # 4. 综合判断
        print(f"\n   [判断] 综合评估...")
        
        if li_verified and bg_verified:
            verification_result["verification_status"] = "verified"
            verification_result["new_score"] = candidate.get('match_score', 0.8)
            verification_result["new_priority"] = candidate.get('priority', 'P1') or 'P1'
            print(f"   ✅ 验证通过")
        elif li_verified:
            verification_result["verification_status"] = "partial"
            verification_result["new_score"] = 0.6
            verification_result["new_priority"] = "P2"
            print(f"   ⚠️ 部分验证（LinkedIn存在但背景未确认）")
        else:
            verification_result["verification_status"] = "unverified"
            verification_result["new_score"] = 0.0
            verification_result["new_priority"] = "REMOVE"
            print(f"   ❌ 无法验证")
        
        self.verification_log.append(verification_result)
        return verification_result
    
    def run_batch_verification(self, candidates: List[Dict], max_candidates: int = None):
        """批量验证"""
        if max_candidates:
            candidates = candidates[:max_candidates]
        
        print(f"\n{'='*70}")
        print(f"🚀 开始批量验证 {len(candidates)} 位候选人")
        print(f"{'='*70}")
        
        results = []
        for i, candidate in enumerate(candidates, 1):
            print(f"\n进度: {i}/{len(candidates)}")
            result = self.verify_candidate(candidate)
            results.append(result)
        
        return results
    
    def generate_report(self, output_path: str):
        """生成验证报告"""
        verified = sum(1 for r in self.verification_log if r["verification_status"] == "verified")
        partial = sum(1 for r in self.verification_log if r["verification_status"] == "partial")
        unverified = sum(1 for r in self.verification_log if r["verification_status"] == "unverified")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_verified": len(self.verification_log),
            "summary": {
                "verified": verified,
                "partial": partial,
                "unverified": unverified
            },
            "details": self.verification_log
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*70}")
        print(f"📊 验证统计")
        print(f"{'='*70}")
        print(f"✅ 已验证: {verified}")
        print(f"⚠️ 部分验证: {partial}")
        print(f"❌ 无法验证: {unverified}")
        print(f"\n📁 报告已保存: {output_path}")


def main():
    """主函数"""
    print("="*70)
    print("🚀 TalentIntel 候选人验证工具")
    print("使用Kimi Web Search进行真实性验证")
    print("="*70)
    
    # 初始化验证器
    verifier = CandidateVerifier()
    
    # 加载候选人
    db_path = '/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/clean_candidates_db.json'
    candidates = verifier.load_candidates(db_path)
    
    # 筛选待验证候选人
    pending = [c for c in candidates if c.get('verified') == 'pending']
    
    print(f"\n总候选人: {len(candidates)}")
    print(f"待验证: {len(pending)}")
    
    # 按优先级排序
    pending_sorted = sorted(
        pending,
        key=lambda x: (
            0 if x.get('priority') == 'P0' else 1,
            -x.get('match_score', 0)
        )
    )
    
    # 询问验证数量
    print(f"\n将验证前5位高优先级候选人")
    
    # 运行验证
    results = verifier.run_batch_verification(pending_sorted, max_candidates=5)
    
    # 生成报告
    report_path = '/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/verification_report.json'
    verifier.generate_report(report_path)
    
    print("\n" + "="*70)
    print("✅ 验证完成")
    print("="*70)


if __name__ == "__main__":
    main()
