#!/usr/bin/env python3
"""
LinkedIn 注册 - 完成姓名和档案设置
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.browser.stealth import StealthBrowser


async def setup_profile():
    """设置 LinkedIn 档案"""
    
    print("=" * 80)
    print("🎯 LinkedIn 注册 - 设置档案")
    print("=" * 80)
    print()
    print("数字研究员身份:")
    print("  First name: Kobe")
    print("  Last name: Lee")
    print("  职位: AI & Wireless Communication Researcher")
    print()
    
    browser = StealthBrowser("config/researcher.yaml")
    page = await browser.launch(headless=False)
    
    try:
        print("🚀 启动浏览器...")
        await page.goto("https://www.linkedin.com/signup")
        await asyncio.sleep(2)
        print()
        
        # Step 1: 填写邮箱密码
        print("📝 Step 1: 邮箱和密码")
        await page.fill('input[type="email"]', "kobe.claw.bot@gmail.com")
        await page.fill('input[type="password"]', "2wsx_1QAZ")
        print("  ✓ 邮箱: kobe.claw.bot@gmail.com")
        print("  ✓ 密码: ********")
        
        # 点击 Agree & Join
        await page.click('button:has-text("Agree")')
        print("  ✓ 点击 Agree & Join")
        await asyncio.sleep(5)
        print()
        
        # Step 2: 填写姓名
        print("📝 Step 2: 填写姓名")
        
        # 等待姓名输入框出现
        await page.wait_for_selector('input[name="firstName"], input#firstName', timeout=10000)
        
        await page.fill('input[name="firstName"], input#firstName', "Kobe")
        print("  ✓ First name: Kobe")
        await asyncio.sleep(0.5)
        
        await page.fill('input[name="lastName"], input#lastName', "Lee")
        print("  ✓ Last name: Lee")
        await asyncio.sleep(0.5)
        
        # 点击 Continue
        await page.click('button:has-text("Continue")')
        print("  ✓ 点击 Continue")
        await asyncio.sleep(5)
        print()
        
        # 检查当前状态
        current_url = page.url
        print(f"📍 当前URL: {current_url}")
        
        # 截图
        screenshot_path = "data/screenshots/linkedin_step3.png"
        await page.screenshot(path=screenshot_path)
        print(f"📸 截图已保存: {screenshot_path}")
        print()
        
        # 判断状态
        if "phone" in current_url or "verify" in current_url:
            print("=" * 80)
            print("🛑 需要用户协助: 手机号验证")
            print("=" * 80)
            print()
            print("LinkedIn 需要手机号验证")
            print("请在浏览器中:")
            print("1. 选择国家代码")
            print("2. 输入你的手机号")
            print("3. 完成短信验证")
            print()
            print("完成后告诉我，我会继续设置档案信息")
            print()
            
            await browser.save_state()
            print("💾 状态已保存")
            
            # 保持打开
            while True:
                await asyncio.sleep(1)
                
        elif "feed" in current_url or "onboarding" in current_url:
            print("=" * 80)
            print("✅ 注册成功！")
            print("=" * 80)
            print()
            await browser.save_state()
            print("💾 登录状态已保存")
            return True
            
        else:
            # 检查是否需要填写更多信息
            page_content = await page.content()
            
            if "location" in page_content.lower() or "country" in page_content.lower():
                print("📝 Step 3: 设置位置和职位")
                print("   需要选择位置和填写职位信息")
                print("   请查看浏览器协助完成")
                print()
                
                await browser.save_state()
                print("💾 状态已保存")
                
                while True:
                    await asyncio.sleep(1)
            else:
                print("⚠️  请查看浏览器当前状态")
                print("如果需要协助，请告诉我")
                await asyncio.sleep(60)
                
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await browser.close()
        print("\n🔒 浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(setup_profile())
