#!/usr/bin/env python3
"""
TalentIntel P1 候选人协同调研
自动打开5位P1候选人的LinkedIn档案
"""
import asyncio
from pathlib import Path

# P1 候选人列表 (前5位)
P1_CANDIDATES = [
    {
        "name": "Dr. Sarah Chen",
        "url": "https://www.linkedin.com/in/dr-sarah-chen-246",
        "company": "Qualcomm",
        "title": "Senior AI Research Scientist"
    },
    {
        "name": "Wei C.",
        "url": "https://www.linkedin.com/in/weicui6",
        "company": "NVIDIA",
        "title": "Systems Software Engineer"
    },
    {
        "name": "Jenny Chu",
        "url": "https://www.linkedin.com/in/jennychu47",
        "company": "SpaceX",
        "title": "Starlink Engineer"
    },
    {
        "name": "Tan Yu",
        "url": "https://www.linkedin.com/in/tan-yu-78675862",
        "company": "NVIDIA",
        "title": "Machine Learning Engineer"
    },
    {
        "name": "Kai-Hsiang Liu",
        "url": "https://www.linkedin.com/in/kaihsiangliu",
        "company": "NVIDIA",
        "title": "Senior Deep Learning Software Engineer"
    }
]

async def research_p1_candidates():
    """协同调研P1候选人"""
    
    print("=" * 80)
    print("🔍 P1 候选人协同调研 (第一批 5人)")
    print("=" * 80)
    print()
    
    from src.browser.stealth import StealthBrowser
    
    browser = StealthBrowser("config/researcher.yaml")
    page = await browser.launch(headless=False)
    
    try:
        for i, candidate in enumerate(P1_CANDIDATES, 1):
            print(f"\n{'=' * 80}")
            print(f"【{i}/5】{candidate['name']}")
            print(f"{'=' * 80}")
            print(f"职位: {candidate['title']}")
            print(f"公司: {candidate['company']}")
            print()
            print(f"正在打开: {candidate['url']}")
            
            await page.goto(candidate['url'])
            await asyncio.sleep(3)
            
            # 截图保存
            safe_name = candidate['name'].replace(' ', '_').replace('.', '').replace('(', '').replace(')', '')
            screenshot_path = f"data/research/P1_{safe_name}_linkedin.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 截图已保存: {screenshot_path}")
            
            print()
            print("⏳ 请查看浏览器中的LinkedIn档案")
            print("调研要点:")
            print("  • 确认职位和公司")
            print("  • 查看工作经历")
            print("  • 评估技术背景")
            print("  • 查找联系方式")
            print()
            
            # 等待用户查看
            await asyncio.sleep(8)
            
        print()
        print("=" * 80)
        print("✅ P1 第一批候选人调研完成")
        print("=" * 80)
        print()
        print("已调研候选人:")
        for c in P1_CANDIDATES:
            print(f"  • {c['name']} ({c['company']})")
        print()
        print("下一步:")
        print("  1. 查看截图分析档案信息")
        print("  2. 继续第二批P1候选人 (8人)")
        print("  3. 填写调研评分")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(research_p1_candidates())
