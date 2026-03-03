"""
人类行为模拟 - 鼠标轨迹生成
使用贝塞尔曲线 + Perlin噪声模拟自然鼠标移动
"""
import math
import random
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np


@dataclass
class Point:
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


class BezierCurve:
    """三阶贝塞尔曲线"""
    
    @staticmethod
    def generate(p0: Point, p3: Point, variance: float = 0.2) -> List[Point]:
        """
        生成从 p0 到 p3 的自然曲线路径
        variance: 控制曲线弯曲程度
        """
        distance = p0.distance_to(p3)
        
        # 控制点偏移（垂直于起点终点连线）
        mid_x = (p0.x + p3.x) / 2
        mid_y = (p0.y + p3.y) / 2
        
        # 随机偏移方向
        angle = random.uniform(0, 2 * math.pi)
        offset = distance * variance * random.uniform(0.3, 0.7)
        
        p1 = Point(
            p0.x + (mid_x - p0.x) * 0.5 + math.cos(angle) * offset * 0.5,
            p0.y + (mid_y - p0.y) * 0.5 + math.sin(angle) * offset * 0.5
        )
        p2 = Point(
            p3.x - (p3.x - mid_x) * 0.5 + math.cos(angle + math.pi) * offset * 0.5,
            p3.y - (p3.y - mid_y) * 0.5 + math.sin(angle + math.pi) * offset * 0.5
        )
        
        # 生成曲线点
        points = []
        steps = max(10, int(distance / 10))  # 步长自适应
        
        for t in np.linspace(0, 1, steps):
            x = (1-t)**3 * p0.x + 3*(1-t)**2*t * p1.x + 3*(1-t)*t**2 * p2.x + t**3 * p3.x
            y = (1-t)**3 * p0.y + 3*(1-t)**2*t * p1.y + 3*(1-t)*t**2 * p2.y + t**3 * p3.y
            points.append(Point(x, y))
        
        return points


class MouseSimulator:
    """鼠标行为模拟器"""
    
    def __init__(self, speed_factor: float = 0.3):
        self.speed_factor = speed_factor
        self.current_pos = Point(0, 0)
    
    def move_to(self, target: Point, page) -> None:
        """
        模拟人类式鼠标移动到目标位置
        page: Playwright page object
        """
        # 生成曲线路径
        path = BezierCurve.generate(self.current_pos, target, variance=0.2)
        
        # 添加微抖动（手抖模拟）
        path = self._add_tremor(path)
        
        # 计算移动时间（距离越远，时间略长但非线性）
        distance = self.current_pos.distance_to(target)
        base_duration = 0.1 + (distance / 1000) ** 0.5  # 次线性增长
        duration = base_duration * random.uniform(0.8, 1.2) / self.speed_factor
        
        # 执行移动
        step_duration = duration / len(path)
        for point in path:
            page.mouse.move(point.x, point.y)
            page.wait_for_timeout(int(step_duration * 1000))
        
        self.current_pos = target
    
    def _add_tremor(self, points: List[Point], amplitude: float = 2.0) -> List[Point]:
        """添加微抖动模拟手抖"""
        result = []
        for i, p in enumerate(points):
            # 边缘抖动小，中间抖动大
            factor = math.sin(math.pi * i / len(points))
            jitter_x = random.gauss(0, amplitude * factor * 0.3)
            jitter_y = random.gauss(0, amplitude * factor * 0.3)
            result.append(Point(p.x + jitter_x, p.y + jitter_y))
        return result
    
    def click(self, page, button: str = "left") -> None:
        """模拟点击（包含轻微延迟和可能的双击）"""
        # 按下前微停顿
        page.wait_for_timeout(random.randint(50, 150))
        page.mouse.down()
        # 按住时间
        page.wait_for_timeout(random.randint(80, 150))
        page.mouse.up()
        # 点击后停顿
        page.wait_for_timeout(random.randint(100, 300))
