"""
人才档案解析器
从LinkedIn页面提取结构化信息
"""
import re
from typing import Dict, Any, List, Optional


class ProfileParser:
    """LinkedIn 档案解析器"""
    
    def __init__(self):
        pass
    
    async def parse(self, page) -> Dict[str, Any]:
        """
        从页面提取档案信息
        
        Args:
            page: Playwright page object
        
        Returns:
            结构化档案数据
        """
        profile = {
            "url": page.url,
            "raw_text": "",
            "sections": {}
        }
        
        try:
            # 获取页面全文
            full_text = await page.inner_text("body")
            profile["raw_text"] = full_text
            
            # 提取各部分内容
            profile["sections"]["name"] = await self._extract_name(page)
            profile["sections"]["headline"] = await self._extract_headline(page)
            profile["sections"]["about"] = await self._extract_about(page)
            profile["sections"]["experience"] = await self._extract_experience(page)
            profile["sections"]["education"] = await self._extract_education(page)
            profile["sections"]["skills"] = await self._extract_skills(page)
            
        except Exception as e:
            profile["error"] = str(e)
        
        return profile
    
    async def _extract_name(self, page) -> str:
        """提取姓名"""
        try:
            # 尝试多种选择器
            selectors = [
                'h1',
                '.top-card-layout__title',
                '[data-test-id="profile-card-name"]'
            ]
            for selector in selectors:
                elem = page.locator(selector).first
                if await elem.is_visible():
                    return (await elem.inner_text()).strip()
            return ""
        except:
            return ""
    
    async def _extract_headline(self, page) -> str:
        """提取头衔/简介"""
        try:
            selectors = [
                '.top-card-layout__headline',
                '[data-test-id="profile-card-headline"]'
            ]
            for selector in selectors:
                elem = page.locator(selector).first
                if await elem.is_visible():
                    return (await elem.inner_text()).strip()
            return ""
        except:
            return ""
    
    async def _extract_about(self, page) -> str:
        """提取关于部分"""
        try:
            # 尝试找到 About section
            about_section = page.locator('section:has-text("About")').first
            if await about_section.is_visible():
                # 获取section内的文本，但过滤掉"About"标题
                text = await about_section.inner_text()
                # 移除 "About" 标题和 "see more" 等
                text = re.sub(r'^About\s*', '', text, flags=re.IGNORECASE)
                text = re.sub(r'\s*…see more\s*', '', text)
                return text.strip()
            return ""
        except:
            return ""
    
    async def _extract_experience(self, page) -> List[Dict[str, str]]:
        """提取工作经历"""
        experiences = []
        try:
            # 查找经历列表项
            exp_items = await page.locator('section:has-text("Experience") li').all()
            for item in exp_items[:5]:  # 最多5条
                try:
                    text = await item.inner_text()
                    if text.strip():
                        experiences.append({"text": text.strip()})
                except:
                    continue
        except:
            pass
        return experiences
    
    async def _extract_education(self, page) -> List[Dict[str, str]]:
        """提取教育背景"""
        educations = []
        try:
            edu_items = await page.locator('section:has-text("Education") li').all()
            for item in edu_items[:3]:
                try:
                    text = await item.inner_text()
                    if text.strip():
                        educations.append({"text": text.strip()})
                except:
                    continue
        except:
            pass
        return educations
    
    async def _extract_skills(self, page) -> List[str]:
        """提取技能"""
        skills = []
        try:
            # 尝试找到 Skills section
            skill_items = await page.locator('section:has-text("Skills") span[dir="ltr"]').all()
            for item in skill_items[:10]:
                try:
                    text = await item.inner_text()
                    if text.strip() and len(text.strip()) < 50:
                        skills.append(text.strip())
                except:
                    continue
        except:
            pass
        return skills
    
    def format_for_llm(self, profile: Dict[str, Any]) -> str:
        """
        将档案格式化为 LLM 可读的文本
        """
        sections = profile.get("sections", {})
        
        formatted = []
        
        # 基本信息
        name = sections.get("name", "")
        headline = sections.get("headline", "")
        if name:
            formatted.append(f"Name: {name}")
        if headline:
            formatted.append(f"Headline: {headline}")
        
        formatted.append("")
        
        # 关于
        about = sections.get("about", "")
        if about:
            formatted.append(f"About:\n{about}")
            formatted.append("")
        
        # 经历
        experiences = sections.get("experience", [])
        if experiences:
            formatted.append("Experience:")
            for exp in experiences:
                text = exp.get("text", "")
                # 清理文本
                text = re.sub(r'\n+', ' | ', text)
                formatted.append(f"  - {text}")
            formatted.append("")
        
        # 教育
        educations = sections.get("education", [])
        if educations:
            formatted.append("Education:")
            for edu in educations:
                text = edu.get("text", "")
                text = re.sub(r'\n+', ' | ', text)
                formatted.append(f"  - {text}")
            formatted.append("")
        
        # 技能
        skills = sections.get("skills", [])
        if skills:
            formatted.append(f"Skills: {', '.join(skills)}")
        
        return "\n".join(formatted)
