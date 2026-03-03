"""
LinkedIn 研究员 V2
整合搜索、评估、存储的完整工作流
"""
import asyncio
import random
from datetime import datetime
from typing import Optional, Dict, Any, List
import yaml

from src.browser.stealth import StealthBrowser
from src.behavior.rhythm import RhythmManager, WorkSchedule
from src.scheduler.search import TalentSearcher
from src.cognition.evaluator import TalentEvaluator
from src.storage.findings import FindingsStorage


class LinkedInResearcherV2:
    """LinkedIn 数字研究员 V2"""
    
    def __init__(self, config_path: str = "config/researcher.yaml"):
        self.config = self._load_config(config_path)
        self.browser = StealthBrowser(config_path)
        self.page = None
        
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
        
        # 功能模块
        self.searcher = TalentSearcher(self.rhythm)
        
        # 评估器（需要目标配置）
        targets_config = self._load_config("config/targets.yaml")
        self.targets = targets_config.get('targets', [])
        search_strategy = targets_config.get('search_strategy', {})
        self.daily_limit = search_strategy.get('daily_batch_size', 10)
        self.min_match_score = search_strategy.get('min_match_score', 0.6)
        
        # 存储
        self.storage = FindingsStorage()
        
        self.is_logged_in = False
        self.evaluators = {}  # 按目标画像缓存评估器
    
    def _load_config(self, path: str) -> Dict[str, Any]:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def _parse_time(self, time_str: str):
        from datetime import time as dt_time
        h, m = map(int, time_str.split(':'))
        return dt_time(h, m)
    
    def _get_evaluator(self, target: Dict[str, Any]) -> TalentEvaluator:
        """获取或创建评估器"""
        target_name = target.get('name', 'default')
        if target_name not in self.evaluators:
            self.evaluators[target_name] = TalentEvaluator(
                llm_config=self.config.get('llm', {}),
                target_criteria=target.get('criteria', {})
            )
        return self.evaluators[target_name]
    
    async def start(self, headless: bool = False):
        """启动研究员"""
        print("🚀 启动 LinkedIn 研究员...")
        self.page = await self.browser.launch(headless=headless)
        print("✅ 浏览器已启动")
    
    async def ensure_login(self) -> bool:
        """确保已登录"""
        print("🔍 检查登录状态...")
        
        await self.page.goto("https://www.linkedin.com/feed/")
        await asyncio.sleep(3)
        
        if "/feed" in self.page.url:
            print("✅ 已登录")
            self.is_logged_in = True
            return True
        
        print("❌ 未登录，请先运行 tests/test_login.py 进行首次登录")
        return False
    
    async def run_daily_research(self):
        """执行今日研究计划"""
        print()
        print("📋 今日研究计划")
        print(f"   目标数量: {self.daily_limit} 人")
        print(f"   最低匹配分数: {self.min_match_score}")
        print()
        
        findings_count = 0
        
        for target in self.targets:
            if findings_count >= self.daily_limit:
                print("✅ 已达今日研究上限")
                break
            
            target_name = target.get('name', 'Unknown')
            print(f"🎯 目标画像: {target_name}")
            print()
            
            # 获取评估器
            evaluator = self._get_evaluator(target)
            
            # 构建搜索关键词
            criteria = target.get('criteria', {})
            keywords = criteria.get('keywords', [])
            locations = criteria.get('locations', [])
            
            # 执行搜索
            remaining = self.daily_limit - findings_count
            profile_urls = await self.searcher.search(
                self.page, 
                keywords[:3],  # 最多3个关键词
                locations[:2],  # 最多2个地点
                max_results=remaining
            )
            
            print(f"   发现 {len(profile_urls)} 个候选档案")
            print()
            
            # 逐个评估
            for url in profile_urls:
                if findings_count >= self.daily_limit:
                    break
                
                # 访问档案
                print(f"🔍 查看: {url}")
                await self.page.goto(url)
                await asyncio.sleep(random.uniform(3, 5))
                
                # 评估
                result = await evaluator.evaluate(self.page)
                score = result.get("match_score", 0)
                
                print(f"   匹配分数: {score:.2f}")
                
                # 判断是否保存
                if evaluator.should_save(result, self.min_match_score):
                    filepath = self.storage.save(result)
                    findings_count += 1
                    print(f"   ✅ 已保存: {filepath}")
                    
                    # 打印报告
                    report = evaluator.format_report(result)
                    print()
                    print(report)
                else:
                    print(f"   ⏭️  匹配度不足，跳过")
                
                print()
                
                # 档案间休息
                if findings_count < self.daily_limit:
                    cooldown = self.config['limits']['cooldown_between_visits']
                    await asyncio.sleep(random.uniform(cooldown, cooldown * 2))
            
            print(f"   完成目标画像: {target_name}")
            print()
        
        # 生成今日汇总
        print()
        summary = self.storage.generate_daily_summary()
        print(summary)
        
        # 保存汇总报告
        summary_file = self.storage.save_report(
            summary, 
            f"summary_{datetime.now().strftime('%H%M%S')}.txt"
        )
        print(f"\n📄 汇总报告已保存: {summary_file}")
    
    async def shutdown(self):
        """关闭研究员"""
        await self.browser.close()
        print("👋 研究员已关闭")
