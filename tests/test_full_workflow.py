"""
完整人才研究流程测试
整合：浏览 + 解析 + LLM分析
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.browser.stealth import StealthBrowser
from src.behavior.mouse import MouseSimulator, Point
from src.behavior.reading import ReadingSimulator
from src.behavior.rhythm import RhythmManager, WorkSchedule
from src.cognition.parser import ProfileParser
from src.cognition.llm import LLMClient
import yaml


async def test_full_workflow():
    """测试完整人才研究流程"""
    
    print("=" * 60)
    print("🦞 TalentIntel - 完整人才研究流程测试")
    print("=" * 60)
    print()
    
    # 加载配置
    with open("config/researcher.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    with open("config/targets.yaml", 'r') as f:
        targets_config = yaml.safe_load(f)
    
    # 初始化组件
    browser = StealthBrowser("config/researcher.yaml")
    parser = ProfileParser()
    llm = LLMClient(config.get('llm', {}))
    mouse = MouseSimulator(speed_factor=0.3)
    reader = ReadingSimulator(wpm_mean=200, wpm_std=30)
    
    # 获取目标画像
    target_profile = targets_config['targets'][0]  # 使用第一个画像
    print(f"🎯 目标画像: {target_profile['name']}")
    print(f"   关键词: {', '.join(target_profile['criteria']['keywords'][:5])}")
    print()
    
    try:
        # 1. 启动浏览器
        print("🚀 启动浏览器...")
        page = await browser.launch(headless=False)
        
        # 2. 检查登录状态
        print("🔍 检查登录状态...")
        await page.goto("https://www.linkedin.com/feed/")
        await asyncio.sleep(3)
        
        if "/feed" not in page.url:
            print("❌ 未登录，请先运行 test_login.py")
            return
        print("✅ 已登录")
        print()
        
        # 3. 访问测试档案
        # 使用一个公开的技术领导者档案
        test_profiles = [
            "https://www.linkedin.com/in/williamhgates/",  # Bill Gates
            "https://www.linkedin.com/in/andrewyng/",      # Andrew Ng
        ]
        
        for profile_url in test_profiles[:1]:  # 先测试1个
            print(f"📄 研究档案: {profile_url}")
            print("-" * 40)
            
            # 导航到档案
            await page.goto(profile_url)
            await asyncio.sleep(4)
            
            # 4. 模拟人类阅读行为
            print("🧠 模拟人类阅读...")
            
            # 读取姓名和标题
            name_elem = page.locator('h1').first
            if await name_elem.is_visible():
                name = await name_elem.inner_text()
                print(f"   👤 {name.strip()}")
            
            # 模拟鼠标移动到页面上方
            await asyncio.sleep(1)
            
            # 滚动阅读关于部分
            await page.evaluate("window.scrollTo(0, 400)")
            await asyncio.sleep(2)
            
            # 滚动阅读经历
            await page.evaluate("window.scrollTo(0, 800)")
            await asyncio.sleep(2)
            
            print("   ✓ 阅读完成")
            print()
            
            # 5. 解析档案
            print("🔍 解析档案内容...")
            profile_data = await parser.parse(page)
            formatted_text = parser.format_for_llm(profile_data)
            print(f"   ✓ 提取内容长度: {len(formatted_text)} 字符")
            print()
            
            # 6. LLM 分析
            print("🤖 AI 分析人才匹配度...")
            analysis = llm.analyze_profile(formatted_text, target_profile['criteria'])
            
            if 'error' in analysis:
                print(f"   ⚠️ 分析出错: {analysis['error']}")
                if 'raw_response' in analysis:
                    print(f"   原始响应: {analysis['raw_response'][:200]}...")
            else:
                print("   " + "=" * 40)
                basic = analysis.get('basic_info', {})
                print(f"   📋 {basic.get('name', 'Unknown')}")
                print(f"      职位: {basic.get('current_role', 'N/A')}")
                print(f"      公司: {basic.get('current_company', 'N/A')}")
                print()
                
                ai_exp = analysis.get('ai_expertise', {})
                wireless_exp = analysis.get('wireless_expertise', {})
                print(f"   🤖 AI 水平: {ai_exp.get('level', 'unknown')}")
                print(f"      领域: {', '.join(ai_exp.get('domains', []))}")
                print(f"   📡 Wireless 水平: {wireless_exp.get('level', 'unknown')}")
                print(f"      领域: {', '.join(wireless_exp.get('domains', []))}")
                print()
                
                score = analysis.get('match_score', 0)
                priority = analysis.get('priority', 'unknown')
                print(f"   ⭐ 匹配分数: {score:.2f}")
                print(f"   🎯 优先级: {priority.upper()}")
                print()
                
                reasons = analysis.get('match_reasons', [])
                if reasons:
                    print("   ✅ 匹配理由:")
                    for reason in reasons[:3]:
                        print(f"      • {reason}")
                
                red_flags = analysis.get('red_flags', [])
                if red_flags:
                    print("   ⚠️  注意事项:")
                    for flag in red_flags:
                        print(f"      • {flag}")
                
                print(f"   💡 建议: {analysis.get('recommended_action', 'N/A')}")
            
            print()
            print("-" * 60)
            print()
        
        print("✅ 完整流程测试完成")
        print()
        print("⏳ 浏览器将在 10 秒后关闭...")
        await asyncio.sleep(10)
        
    except KeyboardInterrupt:
        print("\n👋 用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()
        print("浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(test_full_workflow())
