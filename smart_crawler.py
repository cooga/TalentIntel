"""
TalentIntel Smart Crawler Module
基于 Crawl4AI 架构改进的智能抓取模块

核心改进:
1. Playwright 浏览器抓取替代纯 HTTP
2. BM25 智能内容清洗
3. Profile 持久化管理
4. 行为模拟与反检测
"""

import asyncio
import json
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from pathlib import Path

# Playwright 浏览器控制
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


@dataclass
class CrawlProfile:
    """浏览器 Profile 配置"""
    name: str
    user_agent: str
    viewport: Dict[str, int]
    cookies: List[Dict]
    local_storage: Dict[str, str]
    created_at: datetime
    last_used: datetime
    
    @classmethod
    def create_default(cls, name: str = "default"):
        """创建默认 Profile"""
        return cls(
            name=name,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
            cookies=[],
            local_storage={},
            created_at=datetime.now(),
            last_used=datetime.now()
        )
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "user_agent": self.user_agent,
            "viewport": self.viewport,
            "cookies": self.cookies,
            "local_storage": self.local_storage,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            name=data["name"],
            user_agent=data["user_agent"],
            viewport=data["viewport"],
            cookies=data.get("cookies", []),
            local_storage=data.get("local_storage", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_used=datetime.fromisoformat(data["last_used"])
        )


class ProfileManager:
    """浏览器 Profile 持久化管理"""
    
    def __init__(self, profiles_dir: str = "~/.talentintel/profiles"):
        self.profiles_dir = Path(profiles_dir).expanduser()
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self._profiles: Dict[str, CrawlProfile] = {}
        self._load_profiles()
    
    def _load_profiles(self):
        """从磁盘加载所有 profiles"""
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                    profile = CrawlProfile.from_dict(data)
                    self._profiles[profile.name] = profile
            except Exception as e:
                print(f"Failed to load profile {profile_file}: {e}")
    
    def save_profile(self, profile: CrawlProfile):
        """保存 profile 到磁盘"""
        profile.last_used = datetime.now()
        self._profiles[profile.name] = profile
        
        profile_path = self.profiles_dir / f"{profile.name}.json"
        with open(profile_path, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)
    
    def get_profile(self, name: str) -> Optional[CrawlProfile]:
        """获取 profile"""
        return self._profiles.get(name)
    
    def list_profiles(self) -> List[str]:
        """列出所有 profile 名称"""
        return list(self._profiles.keys())


class BM25ContentFilter:
    """
    BM25 智能内容过滤
    基于 Crawl4AI 的 BM25 算法实现
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
    
    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        return text.lower().split()
    
    def _compute_bm25_score(self, query_terms: List[str], 
                           doc_terms: List[str], 
                           avg_doc_len: float) -> float:
        """
        计算 BM25 分数
        
        BM25 = Σ IDF(q_i) * (f(q_i) * (k1 + 1)) / (f(q_i) + k1 * (1 - b + b * |D|/avgdl))
        """
        if not doc_terms:
            return 0.0
        
        doc_len = len(doc_terms)
        term_freq = {}
        for term in doc_terms:
            term_freq[term] = term_freq.get(term, 0) + 1
        
        score = 0.0
        for term in query_terms:
            if term not in term_freq:
                continue
            
            # IDF (简化版)
            idf = np.log((1 + 1) / (1 + 1)) + 1  # 简化计算
            
            f = term_freq[term]
            numerator = f * (self.k1 + 1)
            denominator = f + self.k1 * (1 - self.b + self.b * doc_len / avg_doc_len)
            
            score += idf * numerator / denominator
        
        return score
    
    def extract_main_content(self, html_blocks: List[Dict[str, str]], 
                            query: str = "") -> str:
        """
        从多个 HTML 块中提取主要内容
        
        Args:
            html_blocks: [{"text": ..., "tag": ..., "class": ...}]
            query: 查询关键词（可选）
            
        Returns:
            主要内容文本
        """
        if not html_blocks:
            return ""
        
        # 计算平均文档长度
        avg_doc_len = np.mean([len(self._tokenize(b["text"])) for b in html_blocks])
        
        # 基于启发式规则过滤
        scores = []
        for block in html_blocks:
            score = 0.0
            text = block["text"]
            tag = block.get("tag", "")
            classes = block.get("class", "")
            
            # 标签权重
            if tag in ["article", "main", "section"]:
                score += 3.0
            elif tag in ["div"] and "content" in classes:
                score += 2.0
            elif tag in ["nav", "footer", "sidebar"]:
                score -= 2.0
            
            # 文本长度（适中为佳）
            text_len = len(text)
            if 100 < text_len < 5000:
                score += 1.0
            elif text_len < 50:
                score -= 1.0
            
            # 关键词匹配
            if query:
                query_terms = self._tokenize(query)
                doc_terms = self._tokenize(text)
                bm25_score = self._compute_bm25_score(query_terms, doc_terms, avg_doc_len)
                score += bm25_score
            
            scores.append((score, text))
        
        # 选择得分最高的块
        scores.sort(key=lambda x: x[0], reverse=True)
        
        # 合并前3个高分块
        top_blocks = [s[1] for s in scores[:3] if s[0] > 0]
        return "\n\n".join(top_blocks)


class SmartCrawler:
    """
    智能爬虫 - 基于 Playwright 的高级抓取
    
    特性:
    - 浏览器指纹隐藏
    - 行为模拟
    - 智能内容提取
    - Profile 持久化
    """
    
    def __init__(self, profile_name: str = "default", headless: bool = True):
        self.profile_manager = ProfileManager()
        self.profile = self.profile_manager.get_profile(profile_name)
        if not self.profile:
            self.profile = CrawlProfile.create_default(profile_name)
        
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.content_filter = BM25ContentFilter()
    
    async def __aenter__(self):
        """异步上下文管理器"""
        self.playwright = await async_playwright().start()
        
        # 启动浏览器
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process"
            ]
        )
        
        # 创建上下文，应用 profile
        self.context = await self.browser.new_context(
            user_agent=self.profile.user_agent,
            viewport=self.profile.viewport,
            cookies=self.profile.cookies,
            locale="en-US",
            timezone_id="America/New_York"
        )
        
        # 注入反检测脚本
        await self._inject_stealth_scripts()
        
        self.page = await self.context.new_page()
        
        # 设置默认超时
        self.page.set_default_timeout(30000)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """清理资源"""
        # 保存 cookies 和 storage
        if self.context:
            try:
                self.profile.cookies = await self.context.cookies()
                self.profile_manager.save_profile(self.profile)
            except:
                pass
        
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def _inject_stealth_scripts(self):
        """注入反检测脚本，隐藏自动化特征"""
        await self.context.add_init_script("""
            // 隐藏 webdriver 标记
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 覆盖 plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // 覆盖 languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // 修改 canvas 指纹（可选）
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                // 添加轻微噪声
                const ctx = this.getContext('2d');
                if (ctx) {
                    const imageData = ctx.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += Math.random() > 0.5 ? 1 : 0;
                    }
                    ctx.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, arguments);
            };
        """)
    
    async def simulate_human_behavior(self):
        """模拟人类浏览行为"""
        if not self.page:
            return
        
        # 随机滚动
        for _ in range(np.random.randint(2, 5)):
            scroll_y = np.random.randint(100, 500)
            await self.page.evaluate(f"window.scrollBy(0, {scroll_y})")
            await asyncio.sleep(np.random.uniform(0.5, 2.0))
        
        # 随机鼠标移动
        for _ in range(np.random.randint(1, 3)):
            x = np.random.randint(100, 800)
            y = np.random.randint(100, 600)
            await self.page.mouse.move(x, y, steps=10)
            await asyncio.sleep(np.random.uniform(0.3, 1.0))
    
    async def crawl(self, url: str, wait_for: str = None, 
                   extract_selector: str = None,
                   query: str = "") -> Dict[str, Any]:
        """
        智能抓取页面
        
        Args:
            url: 目标 URL
            wait_for: 等待的元素选择器
            extract_selector: 提取内容的 CSS 选择器
            query: 查询关键词（用于 BM25 过滤）
            
        Returns:
            抓取结果
        """
        result = {
            "url": url,
            "success": False,
            "title": "",
            "content": "",
            "markdown": "",
            "screenshot": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 访问页面
            response = await self.page.goto(url, wait_until="networkidle")
            
            if response.status >= 400:
                result["error"] = f"HTTP {response.status}"
                return result
            
            # 等待特定元素
            if wait_for:
                await self.page.wait_for_selector(wait_for, timeout=10000)
            else:
                await asyncio.sleep(2)  # 等待动态内容加载
            
            # 模拟人类行为
            await self.simulate_human_behavior()
            
            # 获取标题
            result["title"] = await self.page.title()
            
            # 提取内容
            if extract_selector:
                # 使用 CSS 选择器提取
                elements = await self.page.query_selector_all(extract_selector)
                html_blocks = []
                for el in elements:
                    text = await el.inner_text()
                    tag = await el.evaluate("el => el.tagName.toLowerCase()")
                    classes = await el.evaluate("el => el.className")
                    html_blocks.append({"text": text, "tag": tag, "class": classes})
                
                result["content"] = self.content_filter.extract_main_content(html_blocks, query)
            else:
                # 提取整个 body 文本
                result["content"] = await self.page.inner_text("body")
            
            # 转换为简单 Markdown
            result["markdown"] = self._to_markdown(result["content"])
            
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _to_markdown(self, text: str) -> str:
        """简单文本转 Markdown"""
        # 基本清洗
        lines = text.split('\n')
        cleaned = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:  # 过滤短行
                cleaned.append(line)
        
        return '\n\n'.join(cleaned)


# 同步包装函数（方便非异步代码调用）
def crawl_sync(url: str, profile_name: str = "default", 
               wait_for: str = None, query: str = "") -> Dict:
    """同步接口包装异步爬取"""
    return asyncio.run(_crawl_async(url, profile_name, wait_for, query))


async def _crawl_async(url: str, profile_name: str, 
                      wait_for: str, query: str) -> Dict:
    async with SmartCrawler(profile_name=profile_name) as crawler:
        return await crawler.crawl(url, wait_for=wait_for, query=query)


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("Smart Crawler Test")
    print("=" * 60)
    
    async def test():
        async with SmartCrawler(headless=True) as crawler:
            # 测试抓取
            result = await crawler.crawl(
                "https://www.example.com",
                query="example domain"
            )
            
            print(f"\nURL: {result['url']}")
            print(f"Success: {result['success']}")
            print(f"Title: {result['title']}")
            print(f"Content length: {len(result['content'])}")
            print(f"\nFirst 500 chars:\n{result['content'][:500]}")
    
    asyncio.run(test())
