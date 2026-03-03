"""
LinkedIn 搜索页面调试
用于分析页面结构和测试提取逻辑
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.browser.stealth import StealthBrowser


async def debug_search():
    """调试搜索页面"""
    
    print("=" * 60)
    print("🔍 LinkedIn 搜索页面调试")
    print("=" * 60)
    print()
    
    browser = StealthBrowser("config/researcher.yaml")
    page = await browser.launch(headless=False)
    
    try:
        # 检查登录
        await page.goto("https://www.linkedin.com/feed/")
        await asyncio.sleep(3)
        
        if "/feed" not in page.url:
            print("❌ 未登录")
            return
        
        print("✅ 已登录")
        print()
        
        # 访问搜索页
        search_url = "https://www.linkedin.com/search/results/people/?keywords=machine%20learning"
        print(f"🌐 访问: {search_url}")
        await page.goto(search_url)
        
        # 等待较长时间
        print("⏳ 等待 10 秒让页面完全加载...")
        await asyncio.sleep(10)
        
        # 分析页面
        print()
        print("📊 页面分析:")
        print("-" * 40)
        
        # 1. 检查页面标题
        title = await page.title()
        print(f"页面标题: {title}")
        
        # 2. 检查 URL
        print(f"当前 URL: {page.url}")
        
        # 3. 尝试多种方式找档案链接
        print()
        print("🔎 尝试提取档案链接:")
        
        # 方式1: 标准选择器
        links1 = await page.locator('a[href^="/in/"]').all()
        print(f"  a[href^='/in/']: {len(links1)} 个")
        
        # 方式2: 实体结果
        links2 = await page.locator('.entity-result__item a[href*="/in/"]').all()
        print(f"  .entity-result__item a: {len(links2)} 个")
        
        # 方式3: 搜索结果
        links3 = await page.locator('.search-result__info a[href*="/in/"]').all()
        print(f"  .search-result__info a: {len(links3)} 个")
        
        # 方式4: 任何包含 /in/ 的链接
        all_links = await page.locator('a').all()
        in_links = []
        for link in all_links:
            href = await link.get_attribute('href')
            if href and '/in/' in href:
                in_links.append(href)
        print(f"  所有包含 /in/ 的链接: {len(in_links)} 个")
        
        # 显示前几个链接
        if in_links:
            print()
            print("🔗 前 5 个档案链接:")
            seen = set()
            for href in in_links[:10]:
                base = href.split('?')[0]
                if base not in seen:
                    seen.add(base)
                    print(f"  - {base}")
                    if len(seen) >= 5:
                        break
        
        # 4. 检查页面内容长度
        content = await page.content()
        print()
        print(f"📄 页面 HTML 长度: {len(content)} 字符")
        
        # 5. 检查是否有特定文本
        page_text = await page.inner_text("body")
        if "No results found" in page_text or "未找到结果" in page_text:
            print("⚠️  页面显示: 未找到结果")
        if "results" in page_text.lower():
            print("✅ 页面包含 'results' 关键词")
        
        print()
        print("-" * 40)
        print("⏳ 浏览器保持打开，按 Ctrl+C 关闭...")
        
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 用户中断")
    finally:
        await browser.close()
        print("浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(debug_search())
