#!/usr/bin/env python3
"""
完成 LinkedIn 邮箱验证
使用验证码: 176038
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.browser.stealth import StealthBrowser


async def verify_linkedin_email():
    """验证 LinkedIn 邮箱"""
    
    print("=" * 80)
    print("✉️  LinkedIn 邮箱验证")
    print("=" * 80)
    print()
    print("验证码: 176038")
    print()
    
    browser = StealthBrowser("config/researcher.yaml")
    page = await browser.launch(headless=False)
    
    try:
        print("🚀 启动浏览器...")
        
        # 访问LinkedIn验证页面
        verify_url = "https://www.linkedin.com/comm/psettings/email/confirm?id=7441375976774860801&ct=1774162286915&sig=2TtfS5kltrcsc1&crua=neptune%2Fonboarding%2Estart"
        print(f"📱 访问验证页面...")
        
        await page.goto(verify_url)
        await asyncio.sleep(5)
        
        current_url = page.url
        print(f"📍 当前URL: {current_url}")
        print()
        
        # 截图
        screenshot_path = "data/screenshots/linkedin_verification.png"
        await page.screenshot(path=screenshot_path)
        print(f"📸 截图已保存: {screenshot_path}")
        print()
        
        # 检查验证状态
        if "confirmed" in current_url.lower() or "success" in current_url.lower():
            print("=" * 80)
            print("✅ 邮箱验证成功！")
            print("=" * 80)
            print()
            print("LinkedIn 账号已完全激活")
            print("可以开始人才搜索了")
            
        elif "onboarding" in current_url.lower():
            print("=" * 80)
            print("📋 需要完善档案信息")
            print("=" * 80)
            print()
            print("邮箱已验证，需要继续设置LinkedIn档案")
            print("请查看浏览器完成剩余步骤")
            
        else:
            print("=" * 80)
            print("⚠️  请查看浏览器状态")
            print("=" * 80)
            print()
            print(f"当前页面: {current_url}")
            print("可能需要手动操作完成验证")
        
        print()
        await browser.save_state()
        print("💾 状态已保存")
        
        # 保持浏览器打开供查看
        print()
        print("⏳ 保持浏览器打开...")
        await asyncio.sleep(30)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await browser.close()
        print("\n🔒 浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(verify_linkedin_email())
