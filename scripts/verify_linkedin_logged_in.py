#!/usr/bin/env python3
"""
TalentIntel 候选人验证工具 - 使用已登录的LinkedIn Profile
"""

import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

# LinkedIn已登录的Profile路径
LINKEDIN_PROFILE = "/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/profiles/linkedin_01"


async def verify_candidates():
    """验证候选人"""
    
    print("="*70)
    print("🚀 TalentIntel LinkedIn 验证工具")
    print("使用已登录的Profile")
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
    print(f"将验证前3位")
    
    # 使用已有Profile启动浏览器
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=LINKEDIN_PROFILE,
            headless=False,  # 设置为True可以隐藏浏览器
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # 验证前3位
        results = []
        for i, candidate in enumerate(pending_sorted[:3], 1):
            print(f"\n{'='*70}")
            print(f"进度: {i}/3")
            print(f"🔍 验证: {candidate.get('name')}")
            print(f"   LinkedIn: {candidate.get('linkedin_url')}")
            
            result = await verify_single_candidate(browser, candidate)
            results.append(result)
        
        await browser.close()
    
    # 生成报告
    await generate_report(results)
    
    print("\n" + "="*70)
    print("✅ 验证完成")
    print("="*70)


async def verify_single_candidate(browser, candidate):
    """验证单个候选人"""
    name = candidate.get('name', '')
    linkedin_url = candidate.get('linkedin_url', '')
    expected_company = candidate.get('company', '')
    expected_title = candidate.get('title', '')
    
    result = {
        "name": name,
        "linkedin_url": linkedin_url,
        "status": "unverified",
        "found_name": None,
        "found_title": None,
        "found_company": None,
        "notes": []
    }
    
    try:
        # 访问LinkedIn档案
        page = await browser.new_page()
        await page.goto(linkedin_url)
        await asyncio.sleep(5)  # 等待页面加载
        
        # 检查页面标题
        title = await page.title()
        print(f"   页面标题: {title}")
        
        # 如果已登录，应该能看到姓名
        if "LinkedIn" in title and "Sign" not in title:
            # 尝试提取姓名
            try:
                name_elem = await page.query_selector('h1')
                if name_elem:
                    found_name = await name_elem.inner_text()
                    result["found_name"] = found_name.strip()
                    print(f"   ✅ 找到姓名: {found_name.strip()}")
                    
                    # 验证姓名匹配
                    if name.split()[0] in found_name or name.split()[-1] in found_name:
                        result["notes"].append("姓名匹配")
            except Exception as e:
                print(f"   ⚠️ 无法提取姓名: {e}")
            
            # 尝试提取职位
            try:
                # LinkedIn的职位通常在h1下方
                headline = await page.query_selector('[class*="headline"]')
                if headline:
                    title_text = await headline.inner_text()
                    result["found_title"] = title_text.strip()
                    print(f"   📄 职位: {title_text.strip()}")
                    
                    # 检查公司匹配
                    if expected_company.lower() in title_text.lower():
                        result["notes"].append(f"公司匹配: {expected_company}")
            except:
                pass
            
            # 尝试提取公司
            try:
                company_elem = await page.query_selector('[class*="experience"] [class*="company"]')
                if company_elem:
                    company_text = await company_elem.inner_text()
                    result["found_company"] = company_text.strip()
                    print(f"   🏢 公司: {company_text.strip()}")
            except:
                pass
            
            # 综合判断
            if result["found_name"] and expected_company.lower() in str(result).lower():
                result["status"] = "verified"
                print(f"   ✅ 验证成功")
            elif result["found_name"]:
                result["status"] = "partial"
                print(f"   ⚠️ 部分验证")
            
            # 截图保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/verification_screenshots/{name.replace(' ', '_')}_{timestamp}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            result["screenshot"] = screenshot_path
            print(f"   📸 截图已保存")
            
        elif "Sign in" in title or "Join" in title:
            print(f"   ❌ 未登录，需要重新登录LinkedIn")
            result["notes"].append("LinkedIn session expired, need re-login")
        else:
            print(f"   ⚠️ 页面状态: {title}")
            result["notes"].append(f"页面标题: {title}")
        
        await page.close()
        
    except Exception as e:
        print(f"   ❌ 验证错误: {e}")
        result["notes"].append(f"Error: {str(e)}")
    
    return result


async def generate_report(results):
    """生成报告"""
    verified = sum(1 for r in results if r["status"] == "verified")
    partial = sum(1 for r in results if r["status"] == "partial")
    unverified = sum(1 for r in results if r["status"] == "unverified")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": len(results),
            "verified": verified,
            "partial": partial,
            "unverified": unverified
        },
        "details": results
    }
    
    report_path = '/Users/cooga/.openclaw/workspace/Project/TalentIntel/data/linkedin_verification_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"📊 验证统计")
    print(f"{'='*70}")
    print(f"✅ 已验证: {verified}")
    print(f"⚠️ 部分验证: {partial}")
    print(f"❌ 无法验证: {unverified}")
    print(f"\n📁 报告: {report_path}")


if __name__ == "__main__":
    asyncio.run(verify_candidates())
