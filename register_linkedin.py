#!/usr/bin/env python3
"""
LinkedIn 注册脚本 - Kobe 数字研究员身份
账号: kobe.claw.bot@gmail.com
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.browser.stealth import StealthBrowser


async def register_linkedin():
    """注册 LinkedIn 账号"""
    
    print("=" * 80)
    print("🎯 LinkedIn 注册 - Kobe 数字研究员")
    print("=" * 80)
    print()
    print("账号信息:")
    print("  Email: kobe.claw.bot@gmail.com")
    print("  身份: AI/Wireless Communication Researcher")
    print()
    
    # 启动浏览器
    browser = StealthBrowser("config/researcher.yaml")
    page = await browser.launch(headless=False)
    
    try:
        print("🚀 启动浏览器...")
        print("✅ 浏览器已启动")
        print()
        
        # 访问 LinkedIn 注册页面
        print("📱 访问 LinkedIn 注册页面...")
        await page.goto("https://www.linkedin.com/signup")
        await asyncio.sleep(3)
        
        current_url = page.url
        print(f"当前页面: {current_url}")
        print()
        
        # 检查是否在注册页面
        if "signup" in current_url or "join" in current_url:
            print("✅ 已进入注册页面")
            print()
            
            # 填写邮箱
            print("📝 填写注册信息...")
            
            # 等待邮箱输入框
            email_selector = 'input[name="email-address"], input#email-address, input[type="email"]'
            await page.wait_for_selector(email_selector, timeout=10000)
            await page.fill(email_selector, "kobe.claw.bot@gmail.com")
            print("  ✓ 邮箱: kobe.claw.bot@gmail.com")
            await asyncio.sleep(1)
            
            # 填写密码
            password = "2wsx_1QAZ"  # 用户提供的密码
            password_selector = 'input[name="password"], input#password, input[type="password"]'
            await page.fill(password_selector, password)
            print("  ✓ 密码: ********")
            await asyncio.sleep(1)
            
            # 检查是否有下一步按钮
            next_button_selectors = [
                'button[type="submit"]',
                'button[data-test-id="submit-btn"]',
                '.join-form__form-body-submit-button',
                'button:has-text("Agree & Join")',
                'button:has-text("Join")'
            ]
            
            next_button = None
            for selector in next_button_selectors:
                try:
                    if await page.is_visible(selector, timeout=2000):
                        next_button = selector
                        break
                except:
                    continue
            
            if next_button:
                print(f"  ✓ 找到下一步按钮")
                print()
                print("⚠️  即将点击提交，可能需要手机号验证")
                print("   如果遇到验证，请告诉我")
                print()
                
                # 截图保存当前状态
                screenshot_path = "data/screenshots/linkedin_register_step1.png"
                await page.screenshot(path=screenshot_path)
                print(f"📸 截图已保存: {screenshot_path}")
                
                # 点击下一步
                await page.click(next_button)
                print("⏳ 等待页面响应...")
                await asyncio.sleep(5)
                
                # 检查当前状态
                new_url = page.url
                print(f"\n当前URL: {new_url}")
                
                # 检查是否需要手机号验证
                phone_selectors = [
                    'input[name="phoneNumber"]',
                    'input#phoneNumber',
                    'input[type="tel"]',
                    'text="Verify your identity"',
                    'text="Phone number"'
                ]
                
                need_phone = False
                for selector in phone_selectors:
                    try:
                        if await page.is_visible(selector, timeout=2000):
                            need_phone = True
                            break
                    except:
                        continue
                
                if need_phone:
                    print("\n" + "=" * 80)
                    print("🛑 需要用户协助: 手机号验证")
                    print("=" * 80)
                    print()
                    print("LinkedIn 要求手机号验证，请:")
                    print("1. 在浏览器中查看页面")
                    print("2. 输入你的手机号")
                    print("3. 完成验证后告诉我")
                    print()
                    
                    # 保存状态
                    await browser.save_state()
                    print("💾 浏览器状态已保存")
                    print()
                    print("⏳ 等待用户协助...")
                    
                    # 保持页面打开
                    while True:
                        await asyncio.sleep(1)
                        
                elif "checkpoint" in new_url or "challenge" in new_url:
                    print("\n" + "=" * 80)
                    print("🛑 需要用户协助: 安全验证")
                    print("=" * 80)
                    print()
                    print("LinkedIn 触发安全验证，请:")
                    print("1. 在浏览器中查看页面")
                    print("2. 完成人机验证 (如CAPTCHA)")
                    print("3. 完成后告诉我")
                    print()
                    
                    await browser.save_state()
                    print("💾 浏览器状态已保存")
                    
                    while True:
                        await asyncio.sleep(1)
                        
                elif "feed" in new_url or "mynetwork" in new_url:
                    print("\n" + "=" * 80)
                    print("✅ 注册成功!")
                    print("=" * 80)
                    print()
                    print("LinkedIn 账号注册完成")
                    print("接下来需要完善档案信息")
                    print()
                    
                    # 保存登录状态
                    await browser.save_state()
                    print("💾 登录状态已保存")
                    
                    return True
                    
                else:
                    print("\n⚠️  未知状态，请查看浏览器")
                    screenshot_path = "data/screenshots/linkedin_register_unknown.png"
                    await page.screenshot(path=screenshot_path)
                    print(f"📸 截图已保存: {screenshot_path}")
                    
                    # 等待用户查看
                    print("\n⏳ 等待30秒供查看...")
                    await asyncio.sleep(30)
                    
            else:
                print("❌ 未找到下一步按钮")
                print("请查看浏览器手动操作")
                await asyncio.sleep(30)
                
        else:
            print("⚠️  不在注册页面")
            print(f"当前URL: {current_url}")
            
            # 检查是否已登录
            if "feed" in current_url:
                print("✅ 检测到已登录状态!")
                await browser.save_state()
                print("💾 登录状态已保存")
                return True
            else:
                print("需要手动处理")
                await asyncio.sleep(30)
                
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        
        # 尝试保存截图
        try:
            screenshot_path = "data/screenshots/linkedin_register_error.png"
            await page.screenshot(path=screenshot_path)
            print(f"📸 错误截图已保存: {screenshot_path}")
        except:
            pass
            
    finally:
        print("\n🔒 关闭浏览器...")
        await browser.close()


if __name__ == "__main__":
    print("=" * 80)
    print("🦞 LinkedIn 注册 - Kobe 数字研究员")
    print("=" * 80)
    print()
    
    asyncio.run(register_linkedin())
