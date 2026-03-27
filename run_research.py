#!/usr/bin/env python3
"""
TalentIntel 协同调研执行脚本
自动打开候选人LinkedIn档案进行调研
"""
import asyncio
import json
from pathlib import Path

# P0 候选人列表
P0_CANDIDATES = [
    {
        "name": "Wai San Wong (黄伟山)",
        "url": "https://www.linkedin.com/in/wai-san-wong-00a4b45",
        "company": "Qualcomm",
        "title": "Principal Engineer / Manager"
    },
    {
        "name": "Lulu Wang (王璐璐)",
        "url": "https://www.linkedin.com/in/luluawang",
        "company": "Qualcomm",
        "title": "Senior Staff Engineer / Manager, AI/ML Leadership"
    },
    {
        "name": "Hong (Herbert) Cai (蔡宏)",
        "url": "https://www.linkedin.com/in/hong-herbert-cai",
        "company": "Qualcomm AI Research",
        "title": "Senior Staff Engineer, Deep Learning Researcher"
    }
]

async def research_candidates():
    """协同调研执行"""
    
    print("=" * 80)
    print("🔍 P0 候选人协同调研")
    print("=" * 80)
    print()
    print("我将依次打开每位候选人的LinkedIn档案")
    print("你需要:")
    print("  1. 查看档案信息")
    print("  2. 截图关键信息")
    print("  3. 填写调研模板")
    print()
    
    from src.browser.stealth import StealthBrowser
    
    browser = StealthBrowser("config/researcher.yaml")
    page = await browser.launch(headless=False)
    
    try:
        for i, candidate in enumerate(P0_CANDIDATES, 1):
            print(f"\n{'=' * 80}")
            print(f"【{i}/3】{candidate['name']}")
            print(f"{'=' * 80}")
            print(f"职位: {candidate['title']}")
            print(f"公司: {candidate['company']}")
            print()
            print(f"正在打开: {candidate['url']}")
            
            await page.goto(candidate['url'])
            await asyncio.sleep(3)
            
            # 截图保存
            screenshot_path = f"data/research/{candidate['name'].replace(' ', '_').replace('(', '').replace(')', '')}_linkedin.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 截图已保存: {screenshot_path}")
            
            print()
            print("⏳ 请查看浏览器中的LinkedIn档案")
            print("调研要点:")
            print("  • 确认职位和公司")
            print("  • 查看工作经历")
            print("  �� 评估技术背景")
            print("  • 查找联系方式")
            print()
            print("按 Enter 继续下一位...")
            
            # 等待用户确认
            await asyncio.sleep(10)  # 给用户10秒查看
            
        print()
        print("=" * 80)
        print("✅ P0 候选人调研完成")
        print("=" * 80)
        print()
        print("下一步:")
        print("  1. 填写调研模板: data/research/P0_candidates_research.md")
        print("  2. 为每位候选人评分")
        print("  3. 确定联系方式")
        print()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(research_candidates())
