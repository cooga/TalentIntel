"""
阅读行为模拟
基于内容长度、类型模拟人类阅读时间
"""
import random
import math
from typing import Optional


class ReadingSimulator:
    """模拟人类阅读行为"""
    
    def __init__(self, wpm_mean: int = 200, wpm_std: int = 30):
        self.wpm_mean = wpm_mean
        self.wpm_std = wpm_std
    
    def calculate_reading_time(self, text: str, content_type: str = "profile") -> float:
        """
        计算阅读时间（秒）
        
        Args:
            text: 要阅读的内容
            content_type: profile, post, article, list
        """
        word_count = len(text.split())
        
        # 基于WPM计算基础时间
        wpm = random.gauss(self.wpm_mean, self.wpm_std)
        base_time = (word_count / wpm) * 60
        
        # 根据内容类型调整
        multipliers = {
            "profile": 1.0,      # 标准阅读
            "post": 0.6,         # 帖子浏览更快
            "article": 1.3,      # 长文更仔细
            "list": 0.4,         # 列表扫描式
            "skills": 0.8,       # 技能部分浏览
            "experience": 1.2,   # 工作经历仔细看
        }
        multiplier = multipliers.get(content_type, 1.0)
        
        # 添加随机性（有时跳读，有时精读）
        variance = random.uniform(0.7, 1.4)
        
        reading_time = base_time * multiplier * variance
        
        # 最短停留时间
        return max(reading_time, 3.0)
    
    def simulate_reading(self, page, selector: str, content_type: str = "profile") -> None:
        """
        模拟在页面上阅读特定区域
        """
        try:
            element = page.locator(selector).first
            if not element.is_visible():
                return
            
            # 获取文本内容估算
            text = element.inner_text() or ""
            reading_time = self.calculate_reading_time(text, content_type)
            
            # 模拟阅读过程：缓慢滚动 + 停顿
            self._read_with_scrolling(page, element, reading_time)
            
        except Exception:
            # 静默失败，继续执行
            pass
    
    def _read_with_scrolling(self, page, element, total_time: float) -> None:
        """模拟阅读时的滚动行为"""
        # 分段阅读，每段之间可能滚动
        segments = max(1, int(total_time / 5))  # 每5秒一段
        time_per_segment = total_time / segments
        
        for i in range(segments):
            # 阅读停顿
            jitter = random.uniform(0.8, 1.2)
            page.wait_for_timeout(int(time_per_segment * jitter * 1000))
            
            # 偶尔滚动（不是每次都滚）
            if random.random() < 0.4 and i < segments - 1:
                scroll_amount = random.randint(200, 400)
                page.mouse.wheel(0, scroll_amount)
                # 滚动后停顿
                page.wait_for_timeout(random.randint(500, 1200))
