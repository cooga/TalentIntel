#!/usr/bin/env python3
"""
启动 TalentIntel 数字研究员 - 真实 LinkedIn 搜索
执行 Phase 2 人才发现任务
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

async def run_researcher_session():
    """运行研究员会话"""
    from src.platforms.linkedin_v2 import LinkedInResearcherV2
    
    print("=" * 70)
    print("🦞 TalentIntel 数字研究员 - Phase 2 启动")
    print("=" * 70)
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    researcher = LinkedInResearcherV2()
    results = {
        'start_time': datetime.now().isoformat(),
        'profiles_viewed': 0,
        'candidates_found': [],
        'errors': []
    }
    
    try:
        # 启动浏览器 (headless模式用于服务器运行)
        print("🚀 启动浏览器...")
        await researcher.start(headless=True)
        
        # 检查/执行登录
        print("🔐 检查登录状态...")
        if not await researcher.ensure_login():
            print("❌ LinkedIn 登录失败，请检查:")
            print("   1. 账号密码是否正确 (环境变量 LINKEDIN_PASSWORD)")
            print("   2. 是否需要验证码验证")
            print("   3. 账号是否被限制")
            results['errors'].append('Login failed')
            return results
        
        print("✅ 登录成功!")
        print()
        
        # 加载目标配置
        print("📋 加载搜索目标...")
        targets_path = Path(__file__).parent.parent / "config" / "targets.yaml"
        if targets_path.exists():
            import yaml
            with open(targets_path) as f:
                config = yaml.safe_load(f)
            targets = config.get('targets', [])
            print(f"   发现 {len(targets)} 个搜索目标")
        else:
            print("   使用默认目标: AI-Wireless Researchers")
            targets = [{'name': 'AI-Wireless Researchers', 'priority': 'high'}]
        
        # 执行搜索
        print()
        print("🔍 开始人才搜索...")
        print("-" * 70)
        
        # 这里调用实际搜索逻辑
        # 由于 LinkedIn 需要交互式登录，我们先执行一个简单的测试搜索
        
        print("⚠️  注意: LinkedIn 需要真实登录验证")
        print("   请在本地运行以下命令启动交互式会话:")
        print()
        print("   cd /Users/cooga/.openclaw/workspace/Project/TalentIntel")
        print("   export LINKEDIN_PASSWORD='你的密码'")
        print("   python3 -m src.main")
        print()
        print("   首次登录后，会话会保存，后续可无人值守运行")
        print()
        
        # 模拟搜索结果展示 (真实数据将由研究员收集)
        results['status'] = 'awaiting_login'
        results['message'] = '需要首次交互式登录'
        
    except KeyboardInterrupt:
        print("\n👋 用户中断")
        results['errors'].append('User interrupted')
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        results['errors'].append(str(e))
        import traceback
        traceback.print_exc()
    finally:
        await researcher.shutdown()
        results['end_time'] = datetime.now().isoformat()
        print("\n✅ 会话结束")
    
    return results

def generate_search_plan():
    """生成搜索执行计划"""
    
    # 加载关键词配置
    keywords_path = Path(__file__).parent.parent / "config" / "extended_keywords.yaml"
    if keywords_path.exists():
        import yaml
        with open(keywords_path) as f:
            config = yaml.safe_load(f)
    else:
        config = {}
    
    keywords = config.get('search_keywords', [])
    companies = config.get('target_companies', {})
    
    plan = {
        'generated_at': datetime.now().isoformat(),
        'search_strategy': {
            'approach': 'LinkedIn X-Ray + Direct Search',
            'daily_limit': 20,  # 每日搜索上限
            'cooldown_seconds': 30,  # 搜索间隔
        },
        'targets': []
    }
    
    # Tier 1 公司 (优先)
    for company in companies.get('tier1', [])[:3]:
        plan['targets'].append({
            'company': company,
            'priority': 'P0',
            'keywords': keywords[:5],  # 前5个关键词
            'estimated_profiles': 10
        })
    
    # Tier 2 公司
    for company in companies.get('tier2', [])[:3]:
        plan['targets'].append({
            'company': company,
            'priority': 'P1',
            'keywords': keywords[:3],
            'estimated_profiles': 5
        })
    
    return plan

def save_search_plan(plan):
    """保存搜索计划"""
    output_dir = Path(__file__).parent.parent / "data" / "research"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plan_file = output_dir / f"SEARCH_PLAN_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(plan_file, 'w') as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    
    return plan_file

def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TalentIntel 数字研究员')
    parser.add_argument('--plan-only', action='store_true', help='仅生成搜索计划')
    parser.add_argument('--run', action='store_true', help='执行搜索 (需要登录)')
    
    args = parser.parse_args()
    
    if args.plan_only:
        # 仅生成计划
        print("=" * 70)
        print("📋 生成搜索计划")
        print("=" * 70)
        
        plan = generate_search_plan()
        plan_file = save_search_plan(plan)
        
        print(f"\n✅ 搜索计划已生成: {plan_file}")
        print(f"\n目标公司:")
        for t in plan['targets']:
            print(f"  [{t['priority']}] {t['company']} - {len(t['keywords'])} 个关键词")
        
    elif args.run:
        # 执行搜索
        results = asyncio.run(run_researcher_session())
        
        # 保存结果
        output_dir = Path(__file__).parent.parent / "data" / "research"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        result_file = output_dir / f"SESSION_RESULT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 结果已保存: {result_file}")
        
    else:
        # 默认：显示帮助
        print("=" * 70)
        print("🦞 TalentIntel 数字研究员")
        print("=" * 70)
        print()
        print("用法:")
        print("  python3 launch_researcher.py --plan-only  # 生成搜索计划")
        print("  python3 launch_researcher.py --run        # 执行搜索 (需登录)")
        print()
        print("首次使用步骤:")
        print("  1. 确认 LinkedIn 账号配置正确")
        print("  2. 设置环境变量: export LINKEDIN_PASSWORD='密码'")
        print("  3. 运行交互式登录: python3 -m src.main")
        print("  4. 后续可后台运行: python3 launch_researcher.py --run")

if __name__ == "__main__":
    main()
