#!/usr/bin/env python3
"""
尝试恢复现有LinkedIn会话或检查状态
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.browser.stealth import StealthBrowser


async def check_login_status():
    """检查LinkedIn登录状态"""
    
    print("=" * 80)
    print("🔍 检查 LinkedIn 登录状态")
    print("=" * 80)
    print()
    
    browser = StealthBrowser("config/researcher.yaml")
    page = await browser.launch(headless=False)
    
    try:
        print("🚀 启动浏览器...")
        print("📱 访问 LinkedIn...")
        
        await page.goto("https://www.linkedin.com/feed/")
        await asyncio.sleep(5)
        
        current_url = page.url
        print(f"📍 当前URL: {current_url}")
        print()
        
        # 截图
        screenshot_path = "data/screenshots/linkedin_status.png"
        await page.screenshot(path=screenshot_path)
        print(f"📸 截图已保存: {screenshot_path}")
        print()
        
        if "/feed" in current_url:
            print("=" * 80)
            print("✅ 已登录！")
            print("=" * 80)
            print()
            print("现有账号可以正常使用")
            print("邮箱: minigeminicool@gmail.com")
            print()
            await browser.save_state()
            print("💾 会话状态已更新")
            return True
            
        elif "login" in current_url or "signin" in current_url:
            print("=" * 80)
            print("⚠️  需要重新登录")
            print("=" * 80)
            print()
            print("现有账号会话已过期")
            print("选项1: 使用现有账号重新登录")
            print("  邮箱: minigeminicool@gmail.com")
            print()
            print("选项2: 注册新账号 (kobe.claw.bot@gmail.com)")
            print()
            print("请选择:")
            return False
            
        else:
            print("⚠️  未知状态")
            print(f"当前页面: {current_url}")
            print("请查看浏览器")
            await asyncio.sleep(30)
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        
    finally:
        await browser.close()
        print("\n🔒 浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(check_login_status())
