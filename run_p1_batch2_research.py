#!/usr/bin/env python3
"""
TalentIntel P1 候选人协同调研 - 第二批
自动打开剩余8位P1候选人的LinkedIn档案
"""
import asyncio
from pathlib import Path

# P1 候选人列表 - 第二批 (8人)
P1_CANDIDATES_BATCH2 = [
    {
        "name": "Jocelyn Huang",
        "url": "https://www.linkedin.com/in/huangjocelyn",
        "company": "NVIDIA",
        "title": "Deep Learning Research Scientist"
    },
    {
        "name": "Jingkun Zhang",
        "url": "https://www.linkedin.com/in/jkzhang7",
        "company": "NVIDIA",
        "title": "Deep Learning Compilers"
    },
    {
        "name": "BOR JIUN LIN",
        "url": "https://tw.linkedin.com/in/bor-jiun-lin-b99b80191",
        "company": "NVIDIA",
        "title": "Machine Learning Engineer"
    },
    {
        "name": "Qiqi Hou (侯琪琪)",
        "url": "https://www.linkedin.com/in/hou-qiqi-511096b9",
        "company": "Qualcomm AI Research",
        "title": "Machine Learning Researcher"
    },
    {
        "name": "Chao-Wei Cheng (郑朝伟)",
        "url": "https://tw.linkedin.com/in/chao-wei-kibon-cheng-3791b8104",
        "company": "SpaceX",
        "title": "Starlink Supply Chain Quality"
    },
    {
        "name": "Albert Kuo (郭/柯)",
        "url": "https://www.linkedin.com/in/albert-kuo",
        "company": "SpaceX",
        "title": "Lead Software Engineer"
    },
    {
        "name": "Dr. Hao Chen",
        "url": "https://www.linkedin.com/in/dr-hao-chen-2829",
        "company": "Alibaba DAMO",
        "title": "Principal Engineer"
    },
    {
        "name": "Dr. Kevin Zhang",
        "url": "https://www.linkedin.com/in/dr-kevin-zhang-2460",
        "company": "MediaTek",
        "title": "Senior Director"
    }
]

async def research_p1_batch2():
    """协同调研P1第二批候选人"""
    
    print("=" * 80)
    print("🔍 P1 候选人协同调研 (第二批 8人)")
    print("=" * 80)
    print()
    
    from src.browser.stealth import StealthBrowser
    
    browser = StealthBrowser("config/researcher.yaml")
    page = await browser.launch(headless=False)
    
    try:
        for i, candidate in enumerate(P1_CANDIDATES_BATCH2, 1):
            print(f"\n{'=' * 80}")
            print(f"【{i}/8】{candidate['name']}")
            print(f"{'=' * 80}")
            print(f"职位: {candidate['title']}")
            print(f"公司: {candidate['company']}")
            print()
            print(f"正在打开: {candidate['url']}")
            
            await page.goto(candidate['url'])
            await asyncio.sleep(3)
            
            # 截图保存
            safe_name = candidate['name'].replace(' ', '_').replace('.', '').replace('(', '').replace(')', '')
            screenshot_path = f"data/research/P1_2_{safe_name}_linkedin.png"
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
            await asyncio.sleep(6)
            
        print()
        print("=" * 80)
        print("✅ P1 第二批候选人调研完成")
        print("=" * 80)
        print()
        print("已调研候选人:")
        for c in P1_CANDIDATES_BATCH2:
            print(f"  • {c['name']} ({c['company']})")
        print()
        print("P1全部候选人调研完成！")
        print("下一步: 继续P2学术界候选人调研")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(research_p1_batch2())
