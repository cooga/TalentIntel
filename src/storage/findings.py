"""
研究成果存储
保存人才发现记录
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class FindingsStorage:
    """研究发现存储"""
    
    def __init__(self, base_dir: str = "data/findings"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 按日期组织
        self.today_dir = self.base_dir / datetime.now().strftime("%Y-%m-%d")
        self.today_dir.mkdir(exist_ok=True)
    
    def save(self, finding: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        保存一个研究发现
        
        Returns:
            保存的文件路径
        """
        if filename is None:
            # 从档案信息生成文件名
            profile = finding.get("profile", {})
            name = profile.get("name", "unknown")
            name = name.replace(" ", "_").lower()
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{name}_{timestamp}.json"
        
        filepath = self.today_dir / filename
        
        # 添加元数据
        finding["_meta"] = {
            "saved_at": datetime.now().isoformat(),
            "filepath": str(filepath)
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(finding, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    def save_report(self, report_text: str, filename: str) -> str:
        """保存文本报告"""
        filepath = self.today_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_text)
        return str(filepath)
    
    def list_findings(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出研究发现"""
        if date:
            target_dir = self.base_dir / date
        else:
            target_dir = self.today_dir
        
        if not target_dir.exists():
            return []
        
        findings = []
        for filepath in sorted(target_dir.glob("*.json")):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    finding = json.load(f)
                    findings.append(finding)
            except:
                continue
        
        return findings
    
    def generate_daily_summary(self, date: Optional[str] = None) -> str:
        """生成每日汇总报告"""
        findings = self.list_findings(date)
        
        if not findings:
            return "今日无研究发现"
        
        high_priority = [f for f in findings if f.get("priority") == "high"]
        medium_priority = [f for f in findings if f.get("priority") == "medium"]
        
        lines = []
        lines.append("=" * 60)
        lines.append(f"📊 人才研究发现汇总 - {date or datetime.now().strftime('%Y-%m-%d')}")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"总计: {len(findings)} 人")
        lines.append(f"🔥 高优先级: {len(high_priority)} 人")
        lines.append(f"⭐ 中优先级: {len(medium_priority)} 人")
        lines.append("")
        
        # 按匹配分数排序
        sorted_findings = sorted(findings, key=lambda x: x.get("match_score", 0), reverse=True)
        
        lines.append("🏆 TOP 人才:")
        lines.append("")
        
        for i, f in enumerate(sorted_findings[:5], 1):
            profile = f.get("profile", {})
            name = profile.get("name", "Unknown")
            score = f.get("match_score", 0)
            priority = f.get("priority", "low")
            
            lines.append(f"{i}. {name}")
            lines.append(f"   分数: {score:.2f} | 优先级: {priority.upper()}")
            lines.append(f"   {f.get('url', '')}")
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
