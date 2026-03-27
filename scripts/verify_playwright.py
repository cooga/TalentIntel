#!/usr/bin/env python3
"""
TalentIntel 候选人验证工具 - Playwright版本
使用浏览器自动化验证候选人LinkedIn档案真实性
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class VerificationResult:
    """验证结果"""
    name: str
    linkedin_url: str
    status: str  # verified / unverified / partial
    found_name: Optional[str] = None
    found_title: Optional[str] = None
    found_company: Optional[str] = None
    screenshot_path: Optional[str] = None
    notes: List[str] = None
    
    def __post_init__(self):
        if self.notes is None:
            self.notes = []


class PlaywrightVerifier:
    """Playwright浏览器验证器"""
    
    def __init__(self):
        self.results = []
    
    async def verify_with_google(self, candidate: Dict, browser) -> VerificationResult:
        """使用Google搜索验证候选人"""
        name = candidate.get('name', '')
        company = candidate.get('company', '')
        title = candidate.get('title', '')
        linkedin_url = candidate.get('linkedin_url', '')
        
        print(f"\n{'='*70}")
        print(f"🔍 验证: {name}")
        print(f"   期望: {company} | {title}")
        print(f"   LinkedIn: {linkedin_url}")
        
        result = VerificationResult(
            name=name,
            linkedin_url=linkedin_url,
            status="unverified",
            notes=[]
        )
        
        try:
            # 1. Google搜索
            print(f"\n   [1/3] Google搜索...")
            search_query = f'"{name}" {company} linkedin.com/in'
            
            page = await browser.new_page()
            await page.goto(f'https://www.google.com/search?q={search_query.replace(" ", "+")}')
            await asyncio.sleep(3)
            
            # 检查搜索结果
            content = await page.content()
            
            # 检查是否找到LinkedIn链接
            if linkedin_url in content:
                print(f"   ✅ Google结果中找到LinkedIn链接")
                result.notes.append("Google搜索找到LinkedIn链接")
                
                # 尝试提取搜索结果中的信息
                try:
                    # 查找第一个搜索结果
                    title_elem = await page.query_selector('h3')
                    if title_elem:
                        title_text = await title_elem.inner_text()
                        result.found_name = title_text
                        print(f"   📄 搜索结果标题: {title_text}")
                except:
                    pass
            else:
                print(f"   ⚠️ Google结果中未直接找到LinkedIn链接")
                result.notes.append("Google搜索未找到LinkedIn链接")
            
            await page.close()
            
            # 2. 尝试访问LinkedIn（公共信息）
            print(f"\n   [2/3] 访问LinkedIn公共页面...")
            
            page = await browser.new_page()
            await page.goto(linkedin_url)
            await asyncio.sleep(5)
            
            content = await page.content()
            title = await page.title()
            
            print(f"   页面标题: {title}")
            
            # 检查页面内容
            if "Join LinkedIn" in content or "Sign in" in content:
                print(f"   ⚠️ LinkedIn需要登录才能查看完整档案")
                result.notes.append("LinkedIn需要登录，无法获取完整信息")
                
                # 检查是否有任何个人信息泄露在meta标签
                try:
                    meta_desc = await page.query_selector('meta[name="description"]')
                    if meta_desc:
                        desc = await meta_desc.get_attribute('content')
                        if desc and name.split()[0] in desc:
                            print(f"   ✅ Meta描述中包含姓名")
                            result.notes.append(f"Meta描述: {desc[:100]}")
                            result.status = "partial"
                except:
                    pass
                
            elif "404" in title or "Page not found" in content:
                print(f"   ❌ LinkedIn页面不存在 (404)")
                result.notes.append("LinkedIn页面返回404")
                result.status = "unverified"
            else:
                print(f"   ✅ 页面可访问")
                result.notes.append("LinkedIn页面可访问")
                result.status = "partial"
            
            # 截图保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/verification_screenshots/{name.replace(' ', '_')}_{timestamp}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            result.screenshot_path = screenshot_path
            print(f"   📸 截图已保存: {screenshot_path}")
            
            await page.close()
            
            # 3. 搜索专业背景
            print(f"\n   [3/3] 搜索专业背景...")
            
            page = await browser.new_page()
            bg_query = f'"{name}" "{company}" AI wireless 5G research paper'
            await page.goto(f'https://www.google.com/search?q={bg_query.replace(" ", "+")}')
            await asyncio.sleep(3)
            
            content = await page.content()
            
            ai_keywords = ['AI', 'machine learning', 'deep learning', 'neural']
            wireless_keywords = ['wireless', '5G', '6G', 'MIMO', 'RAN', 'communication']
            
            has_ai = any(kw.lower() in content.lower() for kw in ai_keywords)
            has_wireless = any(kw.lower() in content.lower() for kw in wireless_keywords)
            
            if has_ai and has_wireless:
                print(f"   ✅ 找到AI+Wireless背景")
                result.notes.append("搜索确认AI+Wireless研究背景")
                if result.status == "partial":
                    result.status = "verified"
            else:
                print(f"   ⚠️ 未找到明确AI+Wireless背景")
                result.notes.append("无法确认AI+Wireless背景")
            
            await page.close()
            
        except Exception as e:
            print(f"   ❌ 验证过程出错: {e}")
            result.notes.append(f"验证错误: {str(e)}")
        
        self.results.append(result)
        return result
    
    def generate_report(self, output_path: str):
        """生成验证报告"""
        verified = sum(1 for r in self.results if r.status == "verified")
        partial = sum(1 for r in self.results if r.status == "partial")
        unverified = sum(1 for r in self.results if r.status == "unverified")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(self.results),
                "verified": verified,
                "partial": partial,
                "unverified": unverified
            },
            "details": [
                {
                    "name": r.name,
                    "linkedin_url": r.linkedin_url,
                    "status": r.status,
                    "found_name": r.found_name,
                    "found_title": r.found_title,
                    "found_company": r.found_company,
                    "screenshot": r.screenshot_path,
                    "notes": r.notes
                }
                for r in self.results
            ]
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


async def main():
    """主函数"""
    from playwright.async_api import async_playwright
    
    print("="*70)
    print("🚀 TalentIntel 候选人验证工具 - Playwright版")
    print("="*70)
    
    # 加载候选人
    db_path = '/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/clean_candidates_db.json'
    with open(db_path, 'r') as f:
        data = json.load(f)
    
    candidates = data.get('candidates', [])
    pending = [c for c in candidates if c.get('verified') == 'pending']
    
    # 按优先级排序
    pending_sorted = sorted(
        pending,
        key=lambda x: (
            0 if x.get('priority') == 'P0' else 1,
            -x.get('match_score', 0)
        )
    )
    
    print(f"\n总候选人: {len(candidates)}")
    print(f"待验证: {len(pending)}")
    print(f"将验证前3位高优先级候选人")
    
    # 创建截图目录
    import os
    os.makedirs('/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/verification_screenshots', exist_ok=True)
    
    # 启动Playwright
    verifier = PlaywrightVerifier()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for i, candidate in enumerate(pending_sorted[:3], 1):
            print(f"\n进度: {i}/3")
            await verifier.verify_with_google(candidate, browser)
        
        await browser.close()
    
    # 生成报告
    report_path = '/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/playwright_verification_report.json'
    verifier.generate_report(report_path)
    
    print("\n" + "="*70)
    print("✅ 验证完成")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
