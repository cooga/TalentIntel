"""
工作节奏管理
模拟人类研究员的工作/休息周期
"""
import random
from datetime import datetime, time, timedelta
from dataclasses import dataclass
from typing import Optional, Tuple
import asyncio


@dataclass
class WorkSchedule:
    """工作日程配置"""
    start_time: time
    end_time: time
    lunch_start: time
    lunch_end: time
    max_session_minutes: int
    min_break_minutes: int


class RhythmManager:
    """工作节奏管理器 - 让Agent像人一样工作"""
    
    def __init__(self, schedule: WorkSchedule):
        self.schedule = schedule
        self.session_start: Optional[datetime] = None
        self.tasks_completed = 0
        self.current_break_duration = 0
        
    def is_work_hours(self) -> bool:
        """检查当前是否在工作时间"""
        now = datetime.now().time()
        
        # 午休时间不算工作时间
        if self.schedule.lunch_start <= now <= self.schedule.lunch_end:
            return False
        
        return self.schedule.start_time <= now <= self.schedule.end_time
    
    def should_take_break(self) -> bool:
        """判断是否需要休息"""
        if not self.session_start:
            return False
        
        elapsed = (datetime.now() - self.session_start).total_seconds() / 60
        return elapsed >= self.schedule.max_session_minutes
    
    def start_session(self):
        """开始工作会话"""
        self.session_start = datetime.now()
        self.current_break_duration = 0
    
    async def take_break(self, min_seconds: int = 300, max_seconds: int = 900):
        """
        休息时间
        min_seconds: 最短休息（5分钟）
        max_seconds: 最长休息（15分钟）
        """
        duration = random.randint(min_seconds, max_seconds)
        self.current_break_duration = duration
        
        print(f"🛋️  休息 {duration//60} 分钟...")
        await asyncio.sleep(duration)
        
        # 重置会话计时
        self.session_start = datetime.now()
        print("💼 继续工作")
    
    def get_random_delay(self, base_seconds: float, variance: float = 0.3) -> float:
        """
        获取随机延迟
        用于任务间的自然停顿
        """
        return base_seconds * random.uniform(1 - variance, 1 + variance)
    
    def simulate_thinking(self, complexity: str = "medium") -> float:
        """
        模拟思考时间
        complexity: low, medium, high
        """
        thinking_times = {
            "low": (1, 3),      # 快速判断
            "medium": (3, 8),   # 一般决策
            "high": (8, 20),    # 深度分析
        }
        min_t, max_t = thinking_times.get(complexity, (3, 8))
        return random.uniform(min_t, max_t)
    
    async def between_tasks_delay(self):
        """任务间的自然延迟"""
        delay = self.get_random_delay(5, variance=0.5)  # 5秒基础，±50%变化
        await asyncio.sleep(delay)
