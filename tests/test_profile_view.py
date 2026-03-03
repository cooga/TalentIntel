"""
人才档案浏览测试
验证人类行为模拟效果
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.browser.stealth import StealthBrowser
from src.behavior.mouse import MouseSimulator, Point
from src.behavior.reading import ReadingSimulator


async def test_profile_view():
    """测试浏览人才档案"""
    
    print("=" * 50)
    print("🦞 TalentIntel - 档案浏览测试")
    print("=" * 50)
    print()
    
    # 启动浏览器（会自动恢复登录状态）
    print("🚀 启动浏览器...")
    browser = StealthBrowser("config/researcher.yaml")
    page = await browser.launch(headless=False)
    
    # 初始化行为模拟器
    mouse = MouseSimulator(speed_factor=0.3)
    reader = ReadingSimulator(wpm_mean=200, wpm_std=30)
    
    try:
        # 测试1: 检查是否已登录
        print("🔍 检查登录状态...")
        await page.goto("https://www.linkedin.com/feed/")
        await asyncio.sleep(3)
        
        if "/feed" not in page.url:
            print("❌ 未登录，请先运行 test_login.py")
            return
        
        print("✅ 已登录")
        print()
        
        # 测试2: 访问一个示例档案（Bill Gates 的公开档案）
        test_profile = "https://www.linkedin.com/in/williamhgates/"
        print(f"📄 测试档案: {test_profile}")
        print()
        
        await page.goto(test_profile)
        await asyncio.sleep(4)
        
        # 测试3: 模拟人类阅读行为
        print("🧠 模拟阅读行为...")
        
        # 3.1 获取页面基本信息
        name_elem = page.locator('h1').first
        if await name_elem.is_visible():
            name = await name_elem.inner_text()
            print(f"   👤 姓名: {name.strip()}")
        
        # 3.2 模拟鼠标移动（移动到某个按钮）
        print("   🖱️  模拟鼠标移动...")
        connect_btn = page.locator('button:has-text("Connect")').first
        if await connect_btn.is_visible():
            box = await connect_btn.bounding_box()
            if box:
                await mouse.move_to(Point(box['x'] + box['width']/2, box['y'] + box['height']/2), page)
                print("   ✓ 鼠标移动到 Connect 按钮")
        
        # 3.3 模拟滚动阅读
        print("   📜 模拟滚动阅读...")
        await asyncio.sleep(2)
        
        # 读取关于部分
        about_section = page.locator('section:has-text("About")').first
        if await about_section.is_visible():
            text = await about_section.inner_text()
            reading_time = reader.calculate_reading_time(text, "profile")
            print(f"   ⏱️  预计阅读时间: {reading_time:.1f}秒")
            print("   ⏳ 正在阅读...")
            await asyncio.sleep(min(reading_time, 8))  # 最多8秒
        
        # 滚动到经历部分
        await page.evaluate("window.scrollTo(0, 600)")
        await asyncio.sleep(1.5)
        
        experience_section = page.locator('section:has-text("Experience")').first
        if await experience_section.is_visible():
            text = await experience_section.inner_text()
            reading_time = reader.calculate_reading_time(text, "experience")
            print(f"   ⏱️  预计阅读时间: {reading_time:.1f}秒")
            print("   ⏳ 正在阅读经历...")
            await asyncio.sleep(min(reading_time, 6))
        
        # 3.4 继续滚动
        await page.evaluate("window.scrollTo(0, 1200)")
        await asyncio.sleep(1.5)
        
        print()
        print("✅ 行为模拟测试完成")
        print()
        print("观察点:")
        print("  - 鼠标移动是否自然（贝塞尔曲线）")
        print("  - 停留时间是否符合阅读速度（200 WPM）")
        print("  - 滚动是否有人类停顿")
        
        # 保持浏览器打开一段时间供观察
        print()
        print("⏳ 浏览器将在 15 秒后关闭...")
        print("   按 Ctrl+C 立即关闭")
        await asyncio.sleep(15)
        
    except KeyboardInterrupt:
        print("\n👋 用户中断")
    finally:
        await browser.close()
        print("浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(test_profile_view())
