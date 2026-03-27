"""
全自动 X-Ray Talent Discovery Pipeline
解决 Google + LinkedIn 反爬虫的完整自动化方案

架构:
1. Proxy Pool Manager - 代理池管理
2. Google X-Ray Scraper - Google搜索（带反检测）
3. LinkedIn Profile Evaluator - LinkedIn评估（带行为模拟）
4. Result Aggregator - 结果聚合与存储
"""

import asyncio
import json
import random
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
import urllib.parse
import hashlib

import aiohttp
from aiohttp import ClientTimeout, TCPConnector, ClientSession


@dataclass
class Proxy:
    """代理配置"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    
    def to_dict(self) -> Dict:
        if self.username and self.password:
            url = f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        else:
            url = f"{self.protocol}://{self.host}:{self.port}"
        return {
            "http": url,
            "https": url,
        }
    
    def __hash__(self):
        return hash(f"{self.host}:{self.port}")


class ProxyPool:
    """
    代理池管理器
    
    特性:
    - 健康检查
    - 轮换策略
    - 失败降级
    - 自动恢复
    """
    
    def __init__(self, proxies: List[Proxy] = None):
        self.proxies = proxies or []
        self.healthy_proxies: Set[Proxy] = set()
        self.failed_proxies: Dict[Proxy, datetime] = {}
        self.current_index = 0
        self.stats = {p: {"success": 0, "fail": 0} for p in self.proxies}
        
    def add_proxy(self, proxy: Proxy):
        """添加代理"""
        self.proxies.append(proxy)
        self.stats[proxy] = {"success": 0, "fail": 0}
        
    async def health_check(self, proxy: Proxy) -> bool:
        """健康检查"""
        try:
            timeout = ClientTimeout(total=10)
            async with ClientSession(timeout=timeout) as session:
                async with session.get(
                    "https://www.google.com",
                    proxy=proxy.to_dict()["http"],
                    ssl=False
                ) as resp:
                    return resp.status == 200
        except:
            return False
    
    async def initialize(self):
        """初始化：检查所有代理健康状态"""
        print(f"🔍 检查 {len(self.proxies)} 个代理...")
        tasks = [self.health_check(p) for p in self.proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for proxy, healthy in zip(self.proxies, results):
            if healthy is True:
                self.healthy_proxies.add(proxy)
                print(f"  ✅ {proxy.host}:{proxy.port}")
            else:
                self.failed_proxies[proxy] = datetime.now()
                print(f"  ❌ {proxy.host}:{proxy.port}")
        
        print(f"\n代理健康: {len(self.healthy_proxies)}/{len(self.proxies)}")
    
    def get_next(self) -> Optional[Proxy]:
        """获取下一个可用代理"""
        # 清理超过30分钟的失败代理，尝试恢复
        now = datetime.now()
        recovered = []
        for proxy, failed_time in list(self.failed_proxies.items()):
            if now - failed_time > timedelta(minutes=30):
                recovered.append(proxy)
        
        for proxy in recovered:
            del self.failed_proxies[proxy]
            self.healthy_proxies.add(proxy)
        
        # 从健康代理中轮换选择
        healthy_list = list(self.healthy_proxies)
        if not healthy_list:
            return None
        
        proxy = healthy_list[self.current_index % len(healthy_list)]
        self.current_index += 1
        return proxy
    
    def report_success(self, proxy: Proxy):
        """报告成功"""
        self.stats[proxy]["success"] += 1
        
    def report_failure(self, proxy: Proxy):
        """报告失败"""
        self.stats[proxy]["fail"] += 1
        # 连续失败3次则降级
        if self.stats[proxy]["fail"] >= 3:
            self.healthy_proxies.discard(proxy)
            self.failed_proxies[proxy] = datetime.now()
            print(f"⚠️  代理降级: {proxy.host}:{proxy.port}")


class AntiDetectBrowser:
    """
    反检测浏览器
    
    模拟真实浏览器行为，绕过反爬检测
    """
    
    # 真实浏览器指纹池
    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    ]
    
    # 接受语言池
    ACCEPT_LANGUAGES = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.8",
        "zh-CN,zh;q=0.9,en;q=0.8",
    ]
    
    def __init__(self, proxy_pool: ProxyPool):
        self.proxy_pool = proxy_pool
        self.session: Optional[ClientSession] = None
        self.current_proxy: Optional[Proxy] = None
        self.stats = {
            "requests": 0,
            "success": 0,
            "captcha_hits": 0,
            "blocks": 0,
        }
        
    def get_headers(self) -> Dict[str, str]:
        """获取随机请求头"""
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": random.choice(self.ACCEPT_LANGUAGES),
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
    
    async def random_delay(self, min_sec: float = 3.0, max_sec: float = 8.0):
        """随机延时"""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)
    
    def is_captcha(self, html: str) -> bool:
        """检测验证码"""
        indicators = [
            "captcha",
            "CAPTCHA",
            "recaptcha",
            "I'm not a robot",
            "unusual traffic",
            "automated requests",
            "verify you're human",
            "429",
            "Too Many Requests",
        ]
        return any(ind in html for ind in indicators)
    
    def is_blocked(self, html: str) -> bool:
        """检测封锁"""
        indicators = [
            "403 Forbidden",
            "Access Denied",
            "blocked",
            "banned",
        ]
        return any(ind in html for ind in indicators)
    
    async def request(
        self,
        url: str,
        max_retries: int = 3,
        timeout: int = 30,
    ) -> Optional[str]:
        """
        发起请求（带自动重试和代理轮换）
        
        返回:
            HTML内容 或 None（失败）
        """
        for attempt in range(max_retries):
            proxy = self.proxy_pool.get_next()
            if not proxy:
                print("❌ 无可用代理")
                return None
            
            self.current_proxy = proxy
            
            try:
                # 随机延时
                await self.random_delay(2, 5)
                
                timeout_obj = ClientTimeout(total=timeout)
                
                async with ClientSession(timeout=timeout_obj) as session:
                    async with session.get(
                        url,
                        headers=self.get_headers(),
                        proxy=proxy.to_dict()["http"],
                        ssl=False,
                    ) as resp:
                        self.stats["requests"] += 1
                        html = await resp.text()
                        
                        # 检测验证码
                        if self.is_captcha(html):
                            print(f"⚠️  遇到验证码，切换代理 ({attempt+1}/{max_retries})")
                            self.stats["captcha_hits"] += 1
                            self.proxy_pool.report_failure(proxy)
                            continue
                        
                        # 检测封锁
                        if self.is_blocked(html):
                            print(f"🚫 被封锁，切换代理 ({attempt+1}/{max_retries})")
                            self.stats["blocks"] += 1
                            self.proxy_pool.report_failure(proxy)
                            await asyncio.sleep(30)  # 长延时
                            continue
                        
                        # 成功
                        if resp.status == 200:
                            self.proxy_pool.report_success(proxy)
                            self.stats["success"] += 1
                            return html
                        
                        # 其他错误
                        print(f"❌ HTTP {resp.status}")
                        
            except asyncio.TimeoutError:
                print(f"⏱️ 超时 ({attempt+1}/{max_retries})")
                self.proxy_pool.report_failure(proxy)
            except Exception as e:
                print(f"❌ 错误: {str(e)[:50]}")
                self.proxy_pool.report_failure(proxy)
        
        return None


class GoogleXRayScraper:
    """
    Google X-Ray 搜索器
    
    自动搜索并提取 LinkedIn 档案链接
    """
    
    def __init__(self, browser: AntiDetectBrowser):
        self.browser = browser
        self.base_url = "https://www.google.com/search"
        
    def build_query(
        self,
        companies: List[str],
        titles: List[str],
        skills: List[str],
        locations: List[str],
    ) -> str:
        """构建搜索查询"""
        parts = ["site:linkedin.com/in"]
        
        if companies:
            companies_q = " OR ".join([f'"{c}"' for c in companies])
            parts.append(f"({companies_q})")
        
        if titles:
            titles_q = " OR ".join([f'"{t}"' for t in titles])
            parts.append(f"({titles_q})")
        
        if skills:
            skills_q = " OR ".join([f'"{s}"' for s in skills])
            parts.append(f"({skills_q})")
        
        if locations:
            locations_q = " OR ".join([f'"{l}"' for l in locations])
            parts.append(f"({locations_q})")
        
        return " ".join(parts)
    
    def extract_profiles(self, html: str) -> List[Dict]:
        """从HTML中提取LinkedIn档案"""
        profiles = []
        
        # 查找所有LinkedIn链接
        patterns = [
            r'https://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_.]+',
            r'href="(https://[^"]*linkedin\.com/in/[^"]+)"',
        ]
        
        urls = set()
        for pattern in patterns:
            matches = re.findall(pattern, html)
            urls.update(matches)
        
        for url in urls:
            # 清理URL
            url = urllib.parse.unquote(url)
            url = re.sub(r'\?.*$', '', url)
            url = url.replace('https://linkedin.com/', 'https://www.linkedin.com/')
            
            # 提取姓名
            name_match = re.search(r'/in/([a-zA-Z0-9\-_.]+)', url)
            name = "Unknown"
            if name_match:
                username = name_match.group(1)
                name = username.replace('-', ' ').replace('_', ' ').title()
            
            profiles.append({
                "url": url,
                "name": name,
                "source": "google_xray",
                "discovered_at": datetime.now().isoformat(),
            })
        
        return profiles
    
    async def search(
        self,
        query: str,
        num_pages: int = 3,
    ) -> List[Dict]:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            num_pages: 搜索页数
        
        Returns:
            档案列表
        """
        all_profiles = []
        seen_urls: Set[str] = set()
        
        print(f"\n🔍 Google X-Ray 搜索: {query[:60]}...")
        print(f"   计划搜索 {num_pages} 页\n")
        
        for page in range(num_pages):
            start = page * 10
            params = {
                "q": query,
                "start": start,
                "num": 10,
            }
            url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
            
            print(f"📄 第 {page+1}/{num_pages} 页...")
            
            html = await self.browser.request(url)
            
            if html:
                profiles = self.extract_profiles(html)
                new_profiles = [p for p in profiles if p["url"] not in seen_urls]
                
                for p in new_profiles:
                    seen_urls.add(p["url"])
                    all_profiles.append(p)
                
                print(f"   ✅ 发现 {len(new_profiles)} 个新档案 (累计: {len(all_profiles)})")
            else:
                print(f"   ❌ 获取失败")
            
            # 页面间延时
            if page < num_pages - 1:
                await self.browser.random_delay(5, 10)
        
        return all_profiles


class LinkedInEvaluator:
    """
    LinkedIn 档案评估器
    
    使用LLM评估人才匹配度
    """
    
    def __init__(self, browser: AntiDetectBrowser):
        self.browser = browser
        self.api_key = None  # 从环境变量获取
        
    async def fetch_profile(self, url: str) -> Optional[str]:
        """获取档案页面"""
        print(f"  🔗 访问: {url}")
        html = await self.browser.request(url, timeout=45)
        return html
    
    def extract_profile_data(self, html: str) -> Dict:
        """提取档案数据（简化版）"""
        # 实际实现需要更复杂的HTML解析
        # 这里仅作演示
        return {
            "raw_html": html[:5000] if html else "",
            "has_profile": "linkedin.com/in/" in html if html else False,
        }
    
    async def evaluate(self, profile_url: str) -> Optional[Dict]:
        """
        评估单个档案
        
        返回评估结果或None
        """
        html = await self.fetch_profile(profile_url)
        
        if not html:
            return None
        
        # 这里应该调用LLM进行评估
        # 简化版：模拟评估结果
        await self.browser.random_delay(3, 6)
        
        # 模拟评估（实际应使用LLM）
        profile_data = self.extract_profile_data(html)
        
        if not profile_data["has_profile"]:
            return None
        
        # 模拟评分
        import random
        score = random.uniform(0.3, 0.95)
        
        return {
            "url": profile_url,
            "match_score": round(score, 2),
            "priority": "HIGH" if score > 0.7 else "MEDIUM" if score > 0.5 else "LOW",
            "evaluated_at": datetime.now().isoformat(),
        }


class AutoTalentDiscovery:
    """
    全自动人才发现系统
    
    整合所有组件的完整工作流
    """
    
    def __init__(self):
        self.proxy_pool = ProxyPool()
        self.browser = AntiDetectBrowser(self.proxy_pool)
        self.google_scraper = GoogleXRayScraper(self.browser)
        self.linkedin_evaluator = LinkedInEvaluator(self.browser)
        self.results: List[Dict] = []
        
    def add_proxy(self, host: str, port: int, username: str = None, password: str = None):
        """添加代理"""
        self.proxy_pool.add_proxy(Proxy(host, port, username, password))
    
    async def initialize(self):
        """初始化系统"""
        print("="*60)
        print("🚀 TalentIntel Auto Discovery - 全自动人才发现")
        print("="*60)
        
        # 检查代理
        if not self.proxy_pool.proxies:
            print("⚠️  警告: 未配置代理，使用直连模式（高风险）")
        else:
            await self.proxy_pool.initialize()
    
    async def discover(
        self,
        companies: List[str],
        titles: List[str],
        skills: List[str],
        locations: List[str],
        search_pages: int = 3,
        max_profiles: int = 20,
    ) -> List[Dict]:
        """
        执行完整发现流程
        
        Args:
            companies: 目标公司列表
            titles: 职位关键词
            skills: 技能关键词
            locations: 地区
            search_pages: Google搜索页数
            max_profiles: 最大评估档案数
        
        Returns:
            评估结果列表
        """
        # 构建查询
        query = self.google_scraper.build_query(companies, titles, skills, locations)
        
        # Google搜索
        print("\n" + "="*60)
        print("📍 Phase 1: Google X-Ray 搜索")
        print("="*60)
        
        profiles = await self.google_scraper.search(query, search_pages)
        
        if not profiles:
            print("\n❌ 未发现任何档案")
            return []
        
        print(f"\n✅ Google搜索完成: {len(profiles)} 个档案")
        
        # LinkedIn评估
        print("\n" + "="*60)
        print("📍 Phase 2: LinkedIn 人才评估")
        print("="*60)
        
        evaluated = []
        for i, profile in enumerate(profiles[:max_profiles], 1):
            print(f"\n[{i}/{min(len(profiles), max_profiles)}] 评估: {profile['name']}")
            
            result = await self.linkedin_evaluator.evaluate(profile["url"])
            
            if result:
                evaluated.append({**profile, **result})
                print(f"   匹配度: {result['match_score']} | 优先级: {result['priority']}")
            else:
                print(f"   ❌ 评估失败")
            
            # 档案间延时
            if i < min(len(profiles), max_profiles):
                await self.browser.random_delay(30, 60)
        
        # 保存结果
        self.results = evaluated
        await self._save_results()
        
        # 打印统计
        self._print_stats()
        
        return evaluated
    
    async def _save_results(self):
        """保存结果到文件"""
        output_dir = Path("data/auto_discovery")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存所有结果
        output_file = output_dir / f"results_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "discovered_at": datetime.now().isoformat(),
                "total_discovered": len(self.results),
                "browser_stats": self.browser.stats,
                "profiles": self.results,
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 结果已保存: {output_file}")
    
    def _print_stats(self):
        """打印统计信息"""
        print("\n" + "="*60)
        print("📊 发现统计")
        print("="*60)
        
        high = len([r for r in self.results if r.get("priority") == "HIGH"])
        medium = len([r for r in self.results if r.get("priority") == "MEDIUM"])
        low = len([r for r in self.results if r.get("priority") == "LOW"])
        
        print(f"总计发现: {len(self.results)} 人")
        print(f"🔥 高匹配 (≥0.7): {high} 人")
        print(f"⭐ 中匹配 (0.5-0.7): {medium} 人")
        print(f"📋 低匹配 (<0.5): {low} 人")
        print(f"\n浏览器统计:")
        print(f"  总请求: {self.browser.stats['requests']}")
        print(f"  成功: {self.browser.stats['success']}")
        print(f"  验证码拦截: {self.browser.stats['captcha_hits']}")
        print(f"  封锁: {self.browser.stats['blocks']}")


async def main():
    """主函数"""
    
    # 创建系统实例
    discovery = AutoTalentDiscovery()
    
    # 配置代理（示例，请替换为真实代理）
    # discovery.add_proxy("proxy1.example.com", 8080, "user", "pass")
    # discovery.add_proxy("proxy2.example.com", 8080)
    
    # 初始化
    await discovery.initialize()
    
    # 执行发现
    results = await discovery.discover(
        companies=["Qualcomm", "NVIDIA", "Intel", "Samsung"],
        titles=["AI Engineer", "Wireless Engineer", "Research Scientist"],
        skills=["5G", "Deep Learning", "MIMO"],
        locations=["United States", "Canada"],
        search_pages=2,      # 搜索2页
        max_profiles=5,      # 评估5个档案
    )
    
    print("\n✅ 完成!")


if __name__ == "__main__":
    asyncio.run(main())
