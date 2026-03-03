"""
人才评估器
基于目标画像评估人才价值
"""
from typing import Dict, Any, List
import json

from src.cognition.llm import LLMClient
from src.cognition.parser import ProfileParser


class TalentEvaluator:
    """人才评估器"""
    
    def __init__(self, llm_config: Dict[str, Any], target_criteria: Dict[str, Any]):
        self.llm = LLMClient(llm_config)
        self.parser = ProfileParser()
        self.criteria = target_criteria
    
    async def evaluate(self, page) -> Dict[str, Any]:
        """
        评估一个人才档案
        
        Args:
            page: Playwright page object (当前在档案页面)
        
        Returns:
            评估结果
        """
        # 1. 解析档案
        profile = await self.parser.parse(page)
        
        # 2. 格式化用于 LLM
        formatted_text = self.parser.format_for_llm(profile)
        
        # 3. LLM 评估（如果客户端可用）否则使用规则评估
        if self.llm.client:
            evaluation = self.llm.analyze_profile(formatted_text, self.criteria)
        else:
            print("   ⚠️  LLM 未配置，使用规则评估")
            evaluation = self._rule_based_evaluate(profile, formatted_text)
        
        # 4. 合并结果
        result = {
            "url": profile.get("url", ""),
            "profile": profile.get("sections", {}),
            "evaluation": evaluation,
            "match_score": evaluation.get("match_score", 0),
            "priority": evaluation.get("priority", "low"),
        }
        
        return result
    
    def _rule_based_evaluate(self, profile: Dict[str, Any], text: str) -> Dict[str, Any]:
        """
        基于规则的简单评估（LLM 不可用时使用）
        """
        text_lower = text.lower()
        
        # 关键词匹配
        ai_keywords = ["machine learning", "deep learning", "ai", "artificial intelligence", 
                       "neural network", "llm", "computer vision", "nlp"]
        wireless_keywords = ["wireless", "5g", "6g", "ofdm", "mimo", "communication",
                            "signal processing", "channel", "cellular", "lte", "wifi"]
        
        ai_score = sum(1 for kw in ai_keywords if kw in text_lower) / len(ai_keywords)
        wireless_score = sum(1 for kw in wireless_keywords if kw in text_lower) / len(wireless_keywords)
        
        # 综合评分
        match_score = min((ai_score + wireless_score) / 2 * 2, 1.0)  # 归一化到 0-1
        
        # 确定优先级
        if match_score >= 0.6:
            priority = "high"
        elif match_score >= 0.3:
            priority = "medium"
        else:
            priority = "low"
        
        sections = profile.get("sections", {})
        
        return {
            "basic_info": {
                "name": sections.get("name", "Unknown"),
                "current_role": sections.get("headline", ""),
            },
            "ai_expertise": {
                "level": "expert" if ai_score > 0.3 else "senior" if ai_score > 0.1 else "mid",
                "domains": [kw for kw in ai_keywords if kw in text_lower][:3],
            },
            "wireless_expertise": {
                "level": "expert" if wireless_score > 0.3 else "senior" if wireless_score > 0.1 else "mid",
                "domains": [kw for kw in wireless_keywords if kw in text_lower][:3],
            },
            "match_score": round(match_score, 2),
            "match_reasons": ["关键词匹配"],
            "red_flags": [],
            "priority": priority,
            "recommended_action": "手动审核",
        }
    
    def should_save(self, result: Dict[str, Any], min_score: float = 0.6) -> bool:
        """
        判断是否值得保存这个人才
        """
        score = result.get("match_score", 0)
        priority = result.get("priority", "low")
        
        # 高分或高优先级都保存
        if score >= min_score:
            return True
        if priority == "high":
            return True
        
        return False
    
    def format_report(self, result: Dict[str, Any]) -> str:
        """
        格式化为可读报告
        """
        profile = result.get("profile", {})
        evaluation = result.get("evaluation", {})
        
        lines = []
        lines.append("=" * 50)
        lines.append("🎯 人才评估报告")
        lines.append("=" * 50)
        lines.append("")
        
        # 基本信息
        name = profile.get("name", "Unknown")
        headline = profile.get("headline", "")
        lines.append(f"👤 {name}")
        if headline:
            lines.append(f"   {headline}")
        lines.append(f"   {result.get('url', '')}")
        lines.append("")
        
        # 评分
        score = result.get("match_score", 0)
        priority = result.get("priority", "low")
        score_emoji = "🔥" if score >= 0.8 else "⭐" if score >= 0.6 else "📌"
        lines.append(f"{score_emoji} 匹配分数: {score:.2f} | 优先级: {priority.upper()}")
        lines.append("")
        
        # AI 专业能力
        ai_exp = evaluation.get("ai_expertise", {})
        if ai_exp:
            lines.append(f"🤖 AI 能力: {ai_exp.get('level', 'unknown')}")
            domains = ai_exp.get("domains", [])
            if domains:
                lines.append(f"   领域: {', '.join(domains)}")
            lines.append("")
        
        # Wireless 专业能力
        wireless_exp = evaluation.get("wireless_expertise", {})
        if wireless_exp:
            lines.append(f"📡 Wireless 能力: {wireless_exp.get('level', 'unknown')}")
            domains = wireless_exp.get("domains", [])
            if domains:
                lines.append(f"   领域: {', '.join(domains)}")
            lines.append("")
        
        # 匹配理由
        reasons = evaluation.get("match_reasons", [])
        if reasons:
            lines.append("✅ 匹配理由:")
            for reason in reasons:
                lines.append(f"   • {reason}")
            lines.append("")
        
        # 警告
        flags = evaluation.get("red_flags", [])
        if flags:
            lines.append("⚠️  注意:")
            for flag in flags:
                lines.append(f"   • {flag}")
            lines.append("")
        
        # 建议操作
        action = evaluation.get("recommended_action", "")
        if action:
            lines.append(f"💡 建议: {action}")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)
