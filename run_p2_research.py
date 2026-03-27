#!/usr/bin/env python3
"""
TalentIntel P2 学术界候选人协同调研
教授和博士后人才挖掘
"""
import asyncio
from pathlib import Path

# P2 学术界候选人 (5人)
P2_CANDIDATES = [
    {
        "name": "Prof. Michael Wang",
        "url": "https://www.linkedin.com/in/prof-michael-wang-369",
        "company": "Stanford",
        "title": "Professor of Electrical Engineering"
    },
    {
        "name": "Dr. Mei Lin",
        "url": "https://www.linkedin.com/in/dr-mei-lin-3444",
        "company": "NTU Singapore",
        "title": "Associate Professor"
    },
    {
        "name": "Dr. Xiaoli Ma",
        "url": "https://www.linkedin.com/in/dr-xiaoli-ma-4920",
        "company": "Georgia Tech",
        "title": "Professor"
    },
    {
        "name": "Yaxiong Xie (谢亚雄)",
        "url": "",
        "company": "University at Buffalo",
        "title": "Assistant Professor",
        "note": "前Princeton Postdoc，需搜索LinkedIn"
    },
    {
        "name": "Xianbin Wang (王先斌)",
        "url": "",
        "company": "Western University",
        "title": "Distinguished Professor / IEEE Fellow",
        "note": "IEEE Fellow，需搜索LinkedIn"
    }
]

async def research_p2_candidates():
    """协同调研P2学术界候选人"""
    
    print("=" * 80)
    print("🔍 P2 学术界候选人协同调研 (5人)")
    print("=" * 80)
    print()
    
    from src.browser.stealth import StealthBrowser
    
    browser = StealthBrowser("config/researcher.yaml")
    page = await browser.launch(headless=False)
    
    researched = []
    
    try:
        for i, candidate in enumerate(P2_CANDIDATES, 1):
            print(f"\n{'=' * 80}")
            print(f"【{i}/5】{candidate['name']}")
            print(f"{'=' * 80}")
            print(f"职位: {candidate['title']}")
            print(f"学校: {candidate['company']}")
            
            if candidate.get('url'):
                print(f"正在打开: {candidate['url']}")
                await page.goto(candidate['url'])
                await asyncio.sleep(3)
                
                # 截图保存
                safe_name = candidate['name'].replace(' ', '_').replace('.', '').replace('(', '').replace(')', '')
                screenshot_path = f"data/research/P2_{safe_name}_linkedin.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"📸 截图已保存: {screenshot_path}")
                researched.append(candidate['name'])
            else:
                print("⚠️  缺少LinkedIn URL，需要手动搜索")
                # 尝试搜索
                search_query = f"{candidate['name']} {candidate['company']} LinkedIn"
                search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
                print(f"   建议搜索: {search_url}")
            
            print()
            print("⏳ 请查看浏览器中的档案")
            print("学术界调研要点:")
            print("  • 研究方向 (AI/无线通信交叉)")
            print("  • 发表论文数量/质量")
            print("  • 学生培养情况")
            print("  • 产业合作经验")
            print()
            
            await asyncio.sleep(6)
            
        print()
        print("=" * 80)
        print("✅ P2 学术界候选人调研完成")
        print("=" * 80)
        print()
        print(f"已调研: {len(researched)}/5 人")
        for name in researched:
            print(f"  ✓ {name}")
        print()
        
        if len(researched) < 5:
            print("⚠️  需要手动搜索:")
            for c in P2_CANDIDATES:
                if c['name'] not in researched:
                    print(f"  • {c['name']} ({c['company']})")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(research_p2_candidates())
