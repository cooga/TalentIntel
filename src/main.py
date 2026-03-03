"""
主入口 - 数字人才研究员
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.platforms.linkedin_v2 import LinkedInResearcherV2


async def main():
    """主流程"""
    print("=" * 60)
    print("🦞 TalentIntel - Digital Talent Researcher")
    print("=" * 60)
    print()
    
    researcher = LinkedInResearcherV2()
    
    try:
        # 启动
        await researcher.start(headless=False)
        
        # 检查登录
        if not await researcher.ensure_login():
            print("❌ 登录失败")
            return
        
        # 运行今日研究计划
        await researcher.run_daily_research()
        
    except KeyboardInterrupt:
        print("\n👋 用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await researcher.shutdown()
        print("\n✅ 研究完成")


if __name__ == "__main__":
    asyncio.run(main())
