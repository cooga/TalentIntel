"""
人才搜索器
基于LinkedIn搜索发现目标人才
"""
import asyncio
import random
from typing import List, Dict, Any, Optional
from urllib.parse import quote

from src.behavior.mouse import MouseSimulator, Point
from src.behavior.reading import ReadingSimulator
from src.behavior.rhythm import RhythmManager


class TalentSearcher:
    """LinkedIn 人才搜索器"""
    
    def __init__(self, rhythm: RhythmManager):
        self.rhythm = rhythm
        self.mouse: Optional[MouseSimulator] = None
        self.reader = ReadingSimulator()
    
    async def search(
        self, 
        page, 
        keywords: List[str],
        locations: Optional[List[str]] = None,
        max_results: int = 10
    ) -> List[str]:
        """
        搜索人才
        
        Args:
            page: Playwright page
            keywords: 搜索关键词列表
            locations: 地点过滤
            max_results: 最大结果数
        
        Returns:
            人才档案URL列表
        """
        if not self.mouse:
            self.mouse = MouseSimulator()
        
        profile_urls = []
        
        for keyword in keywords:
            if len(profile_urls) >= max_results:
                break
            
            print(f"🔍 搜索: {keyword}")
            
            # 构建搜索URL
            search_query = quote(keyword)
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={search_query}"
            
            if locations:
                # 添加地点过滤 (简化版)
                location_param = quote(locations[0])
                search_url += f"&location={location_param}"
            
            # 访问搜索页
            await page.goto(search_url)
            
            # 等待页面加载 - 给更多时间
            print("   ⏳ 等待页面加载...")
            await asyncio.sleep(5)
            
            # 等待结果加载 - 尝试多种选择器
            try:
                # 等待结果容器或至少一个结果出现
                await page.wait_for_selector('a[href^="/in/"], .entity-result__item, .search-result__info', timeout=15000)
                print("   ✅ 搜索结果已加载")
            except:
                print("   ⚠️  搜索结果加载超时，尝试提取现有内容...")
            
            # 再等待一下让内容稳定
            await asyncio.sleep(2)
            
            # 提取档案链接
            links = await self._extract_profile_links(page)
            print(f"   找到 {len(links)} 个档案")
            
            for url in links:
                if len(profile_urls) >= max_results:
                    break
                if url not in profile_urls:
                    profile_urls.append(url)
            
            # 搜索间隔休息
            if len(profile_urls) < max_results:
                await asyncio.sleep(random.uniform(5, 10))
        
        return profile_urls[:max_results]
    
    async def _extract_profile_links(self, page) -> List[str]:
        """从搜索结果页提取档案链接"""
        urls = []
        
        try:
            # 获取所有链接
            all_links = await page.locator('a').all()
            
            for link in all_links:
                href = await link.get_attribute('href')
                if href:
                    # 清理并提取基础 URL
                    # 处理两种格式:
                    # 1. 相对路径: /in/username
                    # 2. 完整 URL: https://linkedin.com/in/username
                    if '/in/' in href:
                        # 移除查询参数
                        base_url = href.split('?')[0]
                        # 确保是完整 URL
                        if base_url.startswith('/'):
                            base_url = f"https://www.linkedin.com{base_url}"
                        # 去重
                        if base_url not in urls:
                            urls.append(base_url)
                        
        except Exception as e:
            print(f"   提取链接出错: {e}")
        
        return urls
    
    async def discover_by_company(
        self,
        page,
        company_name: str,
        roles: Optional[List[str]] = None,
        max_results: int = 10
    ) -> List[str]:
        """
        从特定公司发现人才
        
        Args:
            page: Playwright page
            company_name: 公司名称
            roles: 职位关键词
            max_results: 最大结果数
        """
        query = f"\"{company_name}\""
        if roles:
            query += " " + " OR ".join([f"\"{role}\"" for role in roles])
        
        return await self.search(page, [query], max_results=max_results)
