"""
首次登录测试脚本
用途：验证 LinkedIn 登录流程，保存会话状态
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.browser.stealth import StealthBrowser


async def test_login(password: str):
    """测试 LinkedIn 登录"""
    
    if not password:
        print("❌ 请提供密码: python3 tests/test_login.py '你的密码'")
        return
    
    email = "minigeminicool@gmail.com"
    
    print("🚀 启动浏览器...")
    browser = StealthBrowser("config/researcher.yaml")
    page = await browser.launch(headless=False)
    
    try:
        print(f"🔑 正在登录: {email}")
        
        # 先访问登录页
        await page.goto("https://www.linkedin.com/login")
        await asyncio.sleep(2)
        
        # 填写邮箱
        await page.fill('input[name="session_key"]', email)
        print("✓ 已填写邮箱")
        await asyncio.sleep(0.8)
        
        # 填写密码
        await page.fill('input[name="session_password"]', password)
        print("✓ 已填写密码")
        await asyncio.sleep(0.8)
        
        # 点击登录按钮
        await page.click('button[type="submit"]')
        print("⏳ 等待登录响应...")
        
        # 等待页面跳转
        await asyncio.sleep(5)
        
        # 检查当前状态
        current_url = page.url
        print(f"\n当前URL: {current_url}")
        
        if "/feed" in current_url:
            print("✅ 登录成功！")
            await browser.save_state()
            print("💾 会话状态已保存")
            
            # 保持浏览器打开一段时间，方便观察
            print("\n⏳ 浏览器将在 10 秒后关闭...")
            await asyncio.sleep(10)
            
        elif "checkpoint" in current_url or "challenge" in current_url:
            print("⚠️  检测到安全验证挑战")
            print("   请在浏览器中手动完成验证")
            print("   完成后按 Ctrl+C 退出脚本")
            
            # 保持运行，让用户手动处理
            while True:
                await asyncio.sleep(1)
                
        elif "login" in current_url:
            # 检查错误信息
            error_elem = page.locator('.alert-content, [data-test-id="alert-content"]').first
            if await error_elem.is_visible():
                error_text = await error_elem.inner_text()
                print(f"❌ 登录失败: {error_text}")
            else:
                print("❌ 登录失败，请检查密码是否正确")
                
        else:
            print(f"⚠️  未知状态，请检查浏览器")
            await asyncio.sleep(30)  # 给用户时间查看
            
    except KeyboardInterrupt:
        print("\n👋 用户中断")
    finally:
        await browser.close()
        print("浏览器已关闭")


if __name__ == "__main__":
    print("=" * 50)
    print("🦞 TalentIntel - LinkedIn 登录测试")
    print("=" * 50)
    print()
    
    password = sys.argv[1] if len(sys.argv) > 1 else os.getenv('LINKEDIN_PASSWORD')
    asyncio.run(test_login(password))
