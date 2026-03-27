#!/usr/bin/env python3
"""
X-Ray 自动化搜索 - 尝试直接访问 Google
使用 Playwright 模拟人类行为
"""
import asyncio
import json
import re
import time
from datetime import datetime
from pathlib import Path

# 搜索配置
SEARCH_URL = "https://www.google.com/search?q=site%3Alinkedin.com/in%20%28%22NVIDIA%22%29%20%28%22AI%20Engineer%22%20OR%20%22Machine%20Learning%22%20OR%20%22Deep%20Learning%22%29%20%28%22San%20Jose%22%20OR%20%22CA%22%29&num=20&hl=en"

CHINESE_SURNAMES = ['chen', 'wang', 'li', 'zhang', 'liu', 'lin', 'wu', 'zhou', 'huang', 'zhao', 'yang', 'xu', 'sun', 'zhu', 'ma', 'gao', 'guo', 'he', 'zheng', 'xie', 'han', 'tang', 'feng', 'cao', 'yuan', 'deng', 'xue', 'tian', 'pan', 'wei']

async def search_nvidia():
    """搜索 NVIDIA 人才"""
    
    print("=" * 80)
    print("🔍 NVIDIA San Jose AI工程师 - 自动化搜索")
    print("=" * 80)
    print()
    
    from src.browser.stealth import StealthBrowser
    
    browser = StealthBrowser("config/researcher.yaml")
    page = await browser.launch(headless=False)
    
    try:
        print("🚀 启动浏览器...")
        print(f"📱 访问 Google 搜索...")
        print(f"   URL: {SEARCH_URL[:80]}...")
        print()
        
        # 访问 Google
        await page.goto(SEARCH_URL)
        print("⏳ 等待页面加载...")
        await asyncio.sleep(8)  # 给足时间加载
        
        current_url = page.url
        print(f"📍 当前URL: {current_url}")
        print()
        
        # 截图
        screenshot_path = "data/screenshots/google_search_nvidia.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"📸 截图已保存: {screenshot_path}")
        print()
        
        # 获取页面内容
        content = await page.content()
        
        # 提取 LinkedIn 链接
        linkedin_pattern = r'https://[^"\s<>]+linkedin\.com/in/[^"\s<>]+'
        links = re.findall(linkedin_pattern, content)
        
        # 去重和清理
        unique_links = []
        seen = set()
        for link in links:
            # 去除追踪参数
            clean_link = re.sub(r'\?.*$', '', link)
            if clean_link not in seen and '/in/' in clean_link:
                seen.add(clean_link)
                unique_links.append(clean_link)
        
        print(f"🔍 发现 {len(unique_links)} 个 LinkedIn 档案链接")
        print()
        
        # 尝试提取姓名
        candidates = []
        for link in unique_links[:10]:  # 只处理前10个
            # 从URL提取用户名
            match = re.search(r'/in/([^/\?]+)', link)
            if match:
                username = match.group(1)
                # 转换为用户名格式
                name = username.replace('-', ' ').replace('_', ' ').title()
                
                # 检查是否为华人姓名
                is_chinese = any(name.lower().startswith(s + ' ') or 
                                 name.lower().endswith(' ' + s) or
                                 s in name.lower().split() 
                                 for s in CHINESE_SURNAMES)
                
                candidates.append({
                    'name': name,
                    'linkedin_url': link,
                    'is_chinese': is_chinese,
                    'company': 'NVIDIA (推测)',
                    'source': 'Google X-Ray'
                })
        
        # 显示结果
        print("=" * 80)
        print("🏆 搜索结果")
        print("=" * 80)
        print()
        
        chinese_candidates = [c for c in candidates if c['is_chinese']]
        
        print(f"总候选人: {len(candidates)} 人")
        print(f"华人候选人: {len(chinese_candidates)} 人")
        print()
        
        if chinese_candidates:
            print("🎯 华人候选人:")
            for i, c in enumerate(chinese_candidates, 1):
                print(f"  {i}. {c['name']}")
                print(f"     URL: {c['linkedin_url']}")
                print()
        
        # 保存结果
        if candidates:
            output_file = Path('data/xray_searches/nvidia_search_results.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'search_company': 'NVIDIA',
                    'search_location': 'San Jose',
                    'total_found': len(candidates),
                    'chinese_found': len(chinese_candidates),
                    'candidates': candidates
                }, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 结果已保存: {output_file}")
        
        # 检查是否需要验证
        if "sorry" in content.lower() or "captcha" in content.lower() or "unusual" in content.lower():
            print()
            print("⚠️  警告: 可能触发 Google 反爬验证")
            print("   请查看截图确认")
        
        await browser.save_state()
        print()
        print("💾 浏览器状态已保存")
        
        # 保持打开供查看
        print()
        print("⏳ 保持浏览器打开30秒...")
        await asyncio.sleep(30)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await browser.close()
        print("\n🔒 浏览器已关闭")

if __name__ == "__main__":
    asyncio.run(search_nvidia())
