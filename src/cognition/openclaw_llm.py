"""
通过 OpenClaw Gateway 调用 LLM
使用 OpenClaw 内置的 Kimi 配置
"""
import json
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional


class OpenClawLLM:
    """通过 OpenClaw Gateway 调用 LLM"""
    
    def __init__(self, model: str = "kimi-coding/k2p5"):
        self.model = model
    
    def complete(self, messages: List[Dict], temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """
        调用模型完成
        
        Args:
            messages: 消息列表 [{"role": "system"/"user"/"assistant", "content": "..."}]
            temperature: 温度
            max_tokens: 最大 token 数
        
        Returns:
            生成的文本
        """
        # 构建 prompt
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
        
        prompt += "Assistant: "
        
        try:
            # 使用 openclaw agent --local 调用模型，使用独立的 session
            import uuid
            session_id = f"talentintel_{uuid.uuid4().hex[:8]}"
            
            result = subprocess.run(
                [
                    'openclaw', 'agent',
                    '--local',
                    '--session-id', session_id,
                    '--message', prompt,
                    '--thinking', 'off'
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"⚠️  OpenClaw agent 错误: {result.stderr}")
                return ""
                
        except subprocess.TimeoutExpired:
            print("⚠️  OpenClaw agent 超时")
            return ""
        except Exception as e:
            print(f"⚠️  OpenClaw agent 调用失败: {e}")
            return ""
    
    def analyze_profile(self, profile_text: str, target_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """分析人才档案"""
        criteria_desc = json.dumps(target_criteria, ensure_ascii=False, indent=2)
        
        prompt = f"""请分析以下LinkedIn人才档案，并与目标画像进行匹配评估。

## 目标人才画像
{criteria_desc}

## 档案内容
```
{profile_text[:8000]}  
```

## 分析要求
请按以下JSON格式返回分析结果：
{{
  "basic_info": {{
    "name": "姓名",
    "current_role": "当前职位",
    "current_company": "当前公司",
    "location": "地点",
    "education": "最高学历"
  }},
  "ai_expertise": {{
    "level": "expert/senior/mid/junior/none",
    "domains": ["领域1", "领域2"],
    "evidence": "证据描述"
  }},
  "wireless_expertise": {{
    "level": "expert/senior/mid/junior/none", 
    "domains": ["领域1", "领域2"],
    "evidence": "证据描述"
  }},
  "match_score": 0.0-1.0,
  "match_reasons": ["理由1", "理由2"],
  "red_flags": ["警告1"],
  "priority": "high/medium/low",
  "recommended_action": "建议操作"
}}

注意：
- match_score 基于目标画像的匹配度（0-1）
- 优先关注 AI + Wireless 交叉背景
- 北美学界/业界背景加分
- 只返回JSON，不要其他文字
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的人才研究分析师，擅长从LinkedIn档案中提取关键信息并评估人才价值。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.complete(messages, temperature=0.2)
        
        # 解析 JSON 响应
        try:
            json_start = response.find('{')
            json_end = response.rfind('}')
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end+1]
                return json.loads(json_str)
            else:
                return {"error": "无法解析响应", "raw_response": response}
        except json.JSONDecodeError as e:
            return {"error": f"JSON解析错误: {e}", "raw_response": response}


# 测试
if __name__ == "__main__":
    llm = OpenClawLLM()
    
    # 简单测试
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello in Chinese"}
    ]
    
    print("Testing OpenClaw LLM connection...")
    result = llm.complete(messages)
    print(f"Result: {result}")
