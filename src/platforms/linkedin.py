"""
LinkedIn 研究员
核心工作流程：登录 -> 搜索/浏览 -> 理解 -> 记录
"""
import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml

from src.browser.stealth import StealthBrowser
from src.behavior.mouse import MouseSimulator
from src.behavior.reading import ReadingSimulator
from src.behavior.rhythm import RhythmManager, WorkSchedule


class LinkedInResearcher:
    """LinkedIn 数字研究员"""
    
    def __init__(self, config_path: str = "config/researcher.yaml"):
        self.config = self._load_config(config_path)
        self.browser = StealthBrowser(config_path)
        self.mouse: Optional[MouseSimulator] = None
        self.reader = ReadingSimulator(
            wpm_mean=self.config['researcher']['reading_speed']['wpm_mean'],
            wpm_std=self.config['researcher']['reading_speed']['wpm_std']
        )
        
        # 工作节奏
        schedule = WorkSchedule(
            start_time=self._parse_time(self.config['researcher']['work_hours']['start']),
            end_time=self._parse_time(self.config['researcher']['work_hours']['end']),
            lunch_start=self._parse_time(self.config['researcher']['work_hours']['lunch_break'].split('-')[0]),
            lunch_end=self._parse_time(self.config['researcher']['work_hours']['lunch_break'].split('-')[1]),
            max_session_minutes=self.config['researcher']['work_hours']['max_session_duration'],
            min_break_minutes=self.config['researcher']['work_hours']['min_break_duration'],
        )
        self.rhythm = RhythmManager(schedule)
        
        self.is_logged_in = False
    
    def _load_config(self, path: str) -> Dict[str, Any]:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def _parse_time(self, time_str: str):
        h, m = map(int, time_str.split(':'))
        from datetime import time as dt_time
        return dt_time(h, m)
    
    async def start(self, headless: bool = False):
        """启动研究员"""
        print("🚀 启动 LinkedIn 研究员...")
        page = await self.browser.launch(headless=headless)
        self.mouse = MouseSimulator(
            speed_factor=self.config['researcher']['behavior']['mouse_speed']
        )
        return page
    
    async def login(self, page) -> bool:
        """
        登录 LinkedIn
        如果已登录（有保存的session），则跳过
        """
        # 检查是否已有登录状态
        await page.goto("https://www.linkedin.com/feed/")
        await asyncio.sleep(3)
        
        # 检查是否在feed页面（已登录）
        if "/feed" in page.url or "linkedin.com/in/" in page.url:
            print("✅ 已登录")
            self.is_logged_in = True
            return True
        
        # 需要登录
        print("🔑 需要登录...")
        email = self.config['accounts']['linkedin']['email']
        password = os.getenv('LINKEDIN_PASSWORD')
        
        if not password:
            print("❌ 请设置环境变量 LINKEDIN_PASSWORD")
            return False
        
        # 填写登录表单
        try:
            await page.goto("https://www.linkedin.com/login")
            await asyncio.sleep(2)
            
            # 输入邮箱
            await page.fill('input[name="session_key"]', email)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # 输入密码
            await page.fill('input[name="session_password"]', password)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # 点击登录（使用模拟的人类行为）
            sign_in_btn = page.locator('button[type="submit"]').first
            box = await sign_in_btn.bounding_box()
            if box:
                from src.behavior.mouse import Point
                await self.mouse.move_to(Point(box['x'] + box['width']/2, box['y'] + box['height']/2), page)
                await self.mouse.click(page)
            
            # 等待登录完成
            await asyncio.sleep(5)
            
            # 检查是否有验证挑战
            if "checkpoint" in page.url or "challenge" in page.url:
                print("⚠️  检测到验证挑战，请手动完成...")
                input("按 Enter 继续...")
            
            # 确认登录成功
            if "/feed" in page.url:
                print("✅ 登录成功")
                self.is_logged_in = True
                await self.browser.save_state()
                return True
            else:
                print(f"❌ 登录失败，当前URL: {page.url}")
                return False
                
        except Exception as e:
            print(f"❌ 登录出错: {e}")
            return False
    
    async def view_profile(self, page, profile_url: str) -> Optional[Dict]:
        """
        查看并理解一个人才档案
        """
        if not self.is_logged_in:
            print("❌ 未登录")
            return None
        
        print(f"🔍 查看: {profile_url}")
        
        # 导航到档案
        await page.goto(profile_url)
        await asyncio.sleep(random.uniform(3, 5))
        
        # 模拟阅读页面
        # 1. 先浏览顶部（姓名、职位）
        self.reader.simulate_reading(page, "h1", "profile")
        await asyncio.sleep(random.uniform(2, 4))
        
        # 2. 滚动到关于部分
        await page.evaluate("window.scrollTo(0, 400)")
        await asyncio.sleep(random.uniform(1, 2))
        self.reader.simulate_reading(page, "[data-section='about']", "profile")
        
        # 3. 继续滚动到经历
        await page.evaluate("window.scrollTo(0, 800)")
        await asyncio.sleep(random.uniform(1, 2))
        self.reader.simulate_reading(page, "[data-section='experience']", "experience")
        
        # 提取页面文本（用于LLM分析）
        page_text = await page.inner_text("body")
        
        # TODO: 调用 LLM 分析
        
        return {
            "url": profile_url,
            "raw_text": page_text[:5000],  # 截断
            "visited_at": asyncio.get_event_loop().time(),
        }
    
    async def shutdown(self):
        """关闭研究员"""
        await self.browser.close()
        print("👋 研究员已关闭")
