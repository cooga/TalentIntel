#!/usr/bin/env python3
"""
LinkedIn 注册 - 继续完成注册流程
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.browser.stealth import StealthBrowser


async def complete_registration():
    """完成 LinkedIn 注册"""
    
    print("=" * 80)
    print("🎯 LinkedIn 注册 - 继续完成")
    print("=" * 80)
    print()
    
    browser = StealthBrowser("config/researcher.yaml")
    page = await browser.launch(headless=False)
    
    try:
        print("🚀 启动浏览器...")
        await page.goto("https://www.linkedin.com/signup")
        await asyncio.sleep(2)
        print("✅ 进入注册页面")
        print()
        
        # 填写邮箱
        print("📝 填写邮箱...")
        await page.fill('input[type="email"]', "kobe.claw.bot@gmail.com")
        print("  ✓ kobe.claw.bot@gmail.com")
        await asyncio.sleep(0.5)
        
        # 填写密码
        print("📝 填写密码...")
        await page.fill('input[type="password"]', "2wsx_1QAZ")
        print("  ✓ ********")
        await asyncio.sleep(0.5)
        
        # 点击 "Agree & Join" 按钮
        print()
        print("🖱️  点击 'Agree & Join' 按钮...")
        print("⏳ 等待页面跳转...")
        print()
        
        # 使用更精确的选择器
        await page.click('button:has-text("Agree")')
        
        # 等待页面变化
        await asyncio.sleep(8)
        
        # 检查当前状态
        current_url = page.url
        print(f"📍 当前URL: {current_url}")
        print()
        
        # 截图保存
        screenshot_path = "data/screenshots/linkedin_step2.png"
        await page.screenshot(path=screenshot_path)
        print(f"📸 截图已保存: {screenshot_path}")
        
        # 判断状态
        if "checkpoint" in current_url or "challenge" in current_url:
            print()
            print("=" * 80)
            print("🛑 需要用户协助: 安全验证")
            print("=" * 80)
            print()
            print("LinkedIn 需要验证，请查看浏览器并协助完成")
            print()
            await browser.save_state()
            print("💾 状态已保存")
            
            # 保持打开等待用户
            print("⏳ 保持浏览器打开，等待用户协助...")
            while True:
                await asyncio.sleep(1)
                
        elif "phone" in current_url or "verify" in current_url:
            print()
            print("=" * 80)
            print("🛑 需要用户协助: 手机号验证")
            print("=" * 80)
            print()
            print("LinkedIn 需要手机号验证")
            print("请在浏览器中输入手机号完成验证")
            print()
            await browser.save_state()
            print("💾 状态已保存")
            
            while True:
                await asyncio.sleep(1)
                
        elif "feed" in current_url or "onboarding" in current_url:
            print()
            print("=" * 80)
            print("✅ 注册成功！")
            print("=" * 80)
            print()
            print("LinkedIn 账号注册完成")
            print()
            await browser.save_state()
            print("💾 登录状态已保存")
            
            # 继续完善档案
            print()
            print("📝 下一步: 完善档案信息")
            print("   姓名: Kobe")
            print("   职位: AI/Wireless Communication Researcher")
            print()
            
            await asyncio.sleep(10)
            return True
            
        else:
            print()
            print("⚠️  请查看浏览器当前状态")
            print("如果需要协助，请告诉我")
            print()
            
            # 保持打开
            await asyncio.sleep(60)
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await browser.close()
        print("\n🔒 浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(complete_registration())
