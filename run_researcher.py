#!/usr/bin/env python3
"""
启动 LinkedIn 数字研究员 - 大厂人才搜索
"""
import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.platforms.linkedin_v2 import LinkedInResearcherV2


async def main():
    """主程序"""
    print("=" * 80)
    print("🎯 TalentIntel LinkedIn 数字研究员 - 大厂人才搜索")
    print("=" * 80)
    print()
    
    # 检查环境
    if not os.environ.get('LINKEDIN_PASSWORD'):
        print("⚠️  警告: 未设置 LINKEDIN_PASSWORD 环境变量")
        print("   如果已保存登录状态，可以跳过")
        print()
    
    # 启动研究员
    researcher = LinkedInResearcherV2(
        config_path="config/researcher.yaml"
    )
    
    print("🔧 配置加载完成")
    print(f"   数据目录: {researcher.storage.base_dir}")
    print(f"   每日上限: {researcher.daily_limit}")
    print()
    
    # 启动浏览器
    print("🚀 启动浏览器...")
    try:
        await researcher.start(headless=False)  # 非headless便于观察
        print("✅ 浏览器已启动")
        print()
    except Exception as e:
        print(f"❌ 浏览器启动失败: {e}")
        print("   请检查 Playwright 是否安装: playwright install")
        return
    
    # 检查登录状态
    print("🔐 检查登录状态...")
    is_logged_in = await researcher.ensure_login()
    
    if not is_logged_in:
        print()
        print("❌ 未登录 LinkedIn")
        print("   请运行: python tests/test_login.py")
        print("   进行首次登录并保存会话")
        return
    
    # 执行今日研究
    print()
    print("📋 开始执行人才搜索...")
    print(f"   目标: 北美大厂 (Google, NVIDIA, Meta, Apple, Qualcomm等)")
    print(f"   筛选: AI + 无线通信交叉领域华人人才")
    print()
    
    try:
        findings = await researcher.run_daily_research()
        
        print()
        print("=" * 80)
        print("📊 搜索完成")
        print("=" * 80)
        print(f"   发现候选人: {len(findings)} 人")
        print(f"   数据保存至: {researcher.storage.base_dir}")
        print()
        
        if findings:
            print("🏆 高分候选人:")
            for i, f in enumerate(findings[:5], 1):
                name = f.get('name', 'Unknown')
                score = f.get('match_score', 0)
                company = f.get('company', 'Unknown')
                print(f"   {i}. {name} ({company}) - 匹配度: {score:.2f}")
        
    except Exception as e:
        print(f"❌ 搜索过程出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭浏览器
        print()
        print("🔒 关闭浏览器...")
        await researcher.browser.close()
        print("✅ 已完成")


if __name__ == "__main__":
    asyncio.run(main())
