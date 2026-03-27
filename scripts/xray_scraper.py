"""
Google X-Ray Search 自动化抓取
带频率控制和反检测机制

特性:
- 代理池轮换
- 随机延时
- User-Agent 轮换
- 验证码检测
- 断点续传
- 结果去重
"""

import asyncio
import json
import random
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
import urllib.parse

import aiohttp
from aiohttp import ClientTimeout, TCPConnector


@dataclass
class ProxyConfig:
    """代理配置"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    
    def to_url(self) -> str:
        if self.username and self.password:
            return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"http://{self.host}:{self.port}"


@dataclass
class ScrapingConfig:
    """抓取配置"""
    # 延时配置（秒）
    min_delay: float = 5.0      # 最小延时
    max_delay: float = 15.0     # 最大延时
    page_delay: float = 10.0    # 页面间延时
    
    # 重试配置
    max_retries: int = 3
    retry_delay: float = 30.0
    
    # 批次配置
    batch_size: int = 10        # 每批处理数量
    batch_pause: float = 60.0   # 批次间暂停（秒）
    
    # 限制配置
    daily_limit: int = 100      # 每日抓取上限
    consecutive_errors: int = 5  # 连续错误阈值（触发暂停）


class GoogleXRayScraper:
    """Google X-Ray 自动化抓取器"""
    
    # User-Agent 池
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    ]
    
    def __init__(self, config: ScrapingConfig, proxy_list: Optional[List[ProxyConfig]] = None):
        self.config = config
        self.proxies = proxy_list or []
        self.proxy_index = 0
        
        # 统计
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "captcha_hits": 0,
            "profiles_found": 0,
            "start_time": datetime.now().isoformat(),
        }
        
        # 去重集合
        self.seen_urls: Set[str] = set()
        
        # 会话状态
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 断点续传
        self.checkpoint_file = Path("data/xray_checkpoint.json")
        self.load_checkpoint()
    
    def load_checkpoint(self):
        """加载断点"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.seen_urls = set(data.get("seen_urls", []))
                self.stats.update(data.get("stats", {}))
            print(f"📂 已加载断点: {len(self.seen_urls)} 个已抓取档案")
    
    def save_checkpoint(self):
        """保存断点"""
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump({
                "seen_urls": list(self.seen_urls),
                "stats": self.stats,
                "saved_at": datetime.now().isoformat(),
            }, f, ensure_ascii=False, indent=2)
    
    def get_next_proxy(self) -> Optional[str]:
        """获取下一个代理"""
        if not self.proxies:
            return None
        proxy = self.proxies[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy.to_url()
    
    def get_random_headers(self) -> Dict[str, str]:
        """获取随机请求头"""
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.9", "en;q=0.8"]),
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
    
    async def init_session(self):
        """初始化会话"""
        connector = TCPConnector(
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        timeout = ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
        )
    
    async def close_session(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
    
    async def random_delay(self, min_seconds: float = None, max_seconds: float = None):
        """随机延时"""
        min_sec = min_seconds or self.config.min_delay
        max_sec = max_seconds or self.config.max_delay
        delay = random.uniform(min_sec, max_sec)
        print(f"⏳ 延时 {delay:.1f} 秒...")
        await asyncio.sleep(delay)
    
    def is_captcha_page(self, html: str) -> bool:
        """检测是否遇到验证码"""
        captcha_indicators = [
            "captcha",
            "CAPTCHA",
            "recaptcha",
            "I'm not a robot",
            "unusual traffic",
            "automated requests",
            "verify you're human",
        ]
        return any(indicator in html for indicator in captcha_indicators)
    
    def is_blocked_page(self, html: str) -> bool:
        """检测是否被封锁"""
        block_indicators = [
            "429 Too Many Requests",
            "403 Forbidden",
            "Access Denied",
            "blocked",
            "rate limit",
        ]
        return any(indicator in html for indicator in block_indicators)
    
    async def fetch_page(self, url: str, retry_count: int = 0) -> Optional[str]:
        """
        抓取页面
        
        返回 HTML 内容，或 None（遇到验证码/封锁）
        """
        if retry_count >= self.config.max_retries:
            print(f"❌ 超过最大重试次数: {url}")
            return None
        
        # 随机延时
        await self.random_delay()
        
        # 准备请求
        headers = self.get_random_headers()
        proxy = self.get_next_proxy()
        
        try:
            print(f"🌐 请求: {url[:80]}...")
            if proxy:
                print(f"   代理: {proxy.split('@')[-1] if '@' in proxy else proxy}")
            
            async with self.session.get(
                url,
                headers=headers,
                proxy=proxy,
                allow_redirects=True,
            ) as response:
                self.stats["total_requests"] += 1
                
                if response.status == 200:
                    html = await response.text()
                    
                    # 检测验证码
                    if self.is_captcha_page(html):
                        print("⚠️  检测到验证码页面，暂停并更换代理...")
                        self.stats["captcha_hits"] += 1
                        await asyncio.sleep(self.config.retry_delay)
                        return await self.fetch_page(url, retry_count + 1)
                    
                    # 检测封锁
                    if self.is_blocked_page(html):
                        print("🚫 检测到访问限制，暂停...")
                        await asyncio.sleep(self.config.retry_delay * 2)
                        return await self.fetch_page(url, retry_count + 1)
                    
                    self.stats["successful_requests"] += 1
                    return html
                
                elif response.status in [429, 503]:
                    print(f"⚠️  状态码 {response.status}，重试...")
                    await asyncio.sleep(self.config.retry_delay)
                    return await self.fetch_page(url, retry_count + 1)
                
                else:
                    print(f"❌ HTTP {response.status}")
                    self.stats["failed_requests"] += 1
                    return None
                    
        except asyncio.TimeoutError:
            print("⏱️ 请求超时，重试...")
            return await self.fetch_page(url, retry_count + 1)
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            self.stats["failed_requests"] += 1
            return None
    
    def extract_linkedin_profiles(self, html: str) -> List[Dict]:
        """
        从 Google 搜索结果中提取 LinkedIn 档案
        """
        profiles = []
        
        # 方法1: 直接查找 LinkedIn 链接
        pattern = r'https://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_.]+'
        urls = re.findall(pattern, html)
        
        # 方法2: 从 Google 重定向链接中提取
        redirect_pattern = r'/url\?q=(https://[^&]+linkedin\.com/in/[^&]+)'
        redirect_urls = re.findall(redirect_pattern, html)
        
        # 合并并去重
        all_urls = set(urls + redirect_urls)
        
        for url in all_urls:
            # 解码 URL
            url = urllib.parse.unquote(url)
            # 去除追踪参数
            url = re.sub(r'\?.*$', '', url)
            # 规范化 URL
            url = url.replace('https://linkedin.com/', 'https://www.linkedin.com/')
            
            if url in self.seen_urls:
                continue
            
            # 尝试从 URL 提取姓名
            name_match = re.search(r'/in/([a-zA-Z0-9\-_.]+)', url)
            name = "Unknown"
            if name_match:
                username = name_match.group(1)
                name = username.replace('-', ' ').replace('_', ' ').title()
            
            profiles.append({
                "url": url,
                "name": name,
                "discovered_at": datetime.now().isoformat(),
            })
            self.seen_urls.add(url)
        
        self.stats["profiles_found"] += len(profiles)
        return profiles
    
    async def scrape_search_results(
        self,
        search_query: str,
        max_results: int = 50,
    ) -> List[Dict]:
        """
        抓取搜索结果
        
        分页抓取 Google 搜索结果
        """
        all_profiles = []
        consecutive_errors = 0
        
        print(f"\n🔍 开始抓取: {search_query[:60]}...")
        print(f"   目标数量: {max_results}")
        print(f"   已有档案: {len(self.seen_urls)}")
        print()
        
        # 分页抓取
        for start in range(0, min(max_results, 100), 10):
            # 检查每日限制
            if len(all_profiles) >= self.config.daily_limit:
                print(f"⚠️  达到每日限制 ({self.config.daily_limit})，停止")
                break
            
            # 构建分页 URL
            params = {
                "q": search_query,
                "start": start,
                "num": 10,
            }
            url = f"https://www.google.com/search?{urllib.parse.urlencode(params)}"
            
            # 抓取页面
            html = await self.fetch_page(url)
            
            if html:
                profiles = self.extract_linkedin_profiles(html)
                all_profiles.extend(profiles)
                consecutive_errors = 0
                
                print(f"✅ 第 {start//10 + 1} 页: 发现 {len(profiles)} 个新档案")
                print(f"   累计: {len(all_profiles)} 个")
                
                # 保存断点
                self.save_checkpoint()
            else:
                consecutive_errors += 1
                print(f"❌ 第 {start//10 + 1} 页抓取失败")
                
                # 连续错误过多，暂停
                if consecutive_errors >= self.config.consecutive_errors:
                    print(f"🛑 连续 {consecutive_errors} 次错误，暂停 5 分钟...")
                    await asyncio.sleep(300)
                    consecutive_errors = 0
            
            # 页面间延时
            if start + 10 < max_results:
                await self.random_delay(
                    self.config.page_delay,
                    self.config.page_delay * 1.5
                )
        
        return all_profiles
    
    def print_stats(self):
        """打印统计信息"""
        print("\n" + "=" * 60)
        print("📊 抓取统计")
        print("=" * 60)
        print(f"总请求数: {self.stats['total_requests']}")
        print(f"成功请求: {self.stats['successful_requests']}")
        print(f"失败请求: {self.stats['failed_requests']}")
        print(f"验证码拦截: {self.stats['captcha_hits']}")
        print(f"发现档案: {self.stats['profiles_found']}")
        print(f"去重后档案: {len(self.seen_urls)}")
        print(f"开始时间: {self.stats['start_time']}")
        print("=" * 60)


async def main():
    """主函数"""
    
    print("=" * 70)
    print("🕷️ Google X-Ray Scraper - 自动化人才发现")
    print("=" * 70)
    print()
    
    # 配置
    config = ScrapingConfig(
        min_delay=5.0,      # 5-15秒随机延时
        max_delay=15.0,
        page_delay=10.0,    # 页面间10秒
        batch_size=10,
        batch_pause=60.0,   # 批次间暂停1分钟
        daily_limit=50,     # 每日上限50人
        max_retries=3,
    )
    
    # 代理配置（示例，可根据需要添加真实代理）
    proxies = [
        # ProxyConfig("proxy1.example.com", 8080, "user", "pass"),
        # ProxyConfig("proxy2.example.com", 8080),
    ]
    
    # 搜索查询（使用之前的 X-Ray 查询）
    search_query = (
        'site:linkedin.com/in '
        '("Qualcomm" OR "NVIDIA" OR "Intel" OR "Samsung") '
        '("AI Engineer" OR "Wireless Engineer" OR "Research Scientist") '
        '("5G" OR "Deep Learning" OR "MIMO") '
        '("United States" OR "Canada") '
        '-"recruiter" -"HR" -"sales"'
    )
    
    # 创建抓取器
    scraper = GoogleXRayScraper(config, proxies)
    
    try:
        await scraper.init_session()
        
        # 执行抓取
        profiles = await scraper.scrape_search_results(
            search_query,
            max_results=30,  # 先抓取30个测试
        )
        
        # 打印统计
        scraper.print_stats()
        
        # 保存结果
        if profiles:
            output_file = Path("data/xray_profiles.json")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "query": search_query,
                    "profiles": profiles,
                    "total_found": len(profiles),
                    "generated_at": datetime.now().isoformat(),
                }, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 结果已保存: {output_file}")
            print(f"   发现 {len(profiles)} 个新档案")
        
    except KeyboardInterrupt:
        print("\n\n👋 用户中断")
    finally:
        await scraper.close_session()
        scraper.save_checkpoint()
        print("\n✅ 抓取完成，断点已保存")


if __name__ == "__main__":
    asyncio.run(main())
