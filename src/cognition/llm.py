"""
LLM 客户端
支持多个提供商：OpenAI、Kimi (通过 OpenClaw)、Anthropic
"""
import os
import json
import subprocess
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List


# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent


class LLMClient:
    """LLM 客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        self.provider = config.get('provider', 'openai')
        self.model = config.get('model', 'kimi-coding/k2p5')
        self.base_url = config.get('base_url')
        self.api_key = config.get('api_key')
        
        self.client = None
        self._init_client()
    
    def _load_secrets(self) -> Dict[str, str]:
        """从 secrets 文件加载 API Keys"""
        secrets_path = PROJECT_ROOT / "config" / ".secrets.yaml"
        if secrets_path.exists():
            import yaml
            with open(secrets_path, 'r') as f:
                secrets = yaml.safe_load(f)
                return secrets or {}
        return {}
    
    def _init_client(self):
        """初始化 LLM 客户端"""
        secrets = self._load_secrets()
        
        if self.provider == 'kimi':
            # 使用 OpenClaw 调用 Kimi
            self.client = "openclaw"
        elif self.provider == 'openai':
            # 检查是否有 OpenAI API Key
            api_key = self.api_key or os.getenv('OPENAI_API_KEY') or secrets.get('openai_api_key')
            if api_key:
                self.client = "openai"
                self._api_key = api_key
            else:
                print("⚠️  未找到 OpenAI API Key")
                self.client = None
        else:
            self.client = None
    
    def _call_openclaw(self, messages: List[Dict], temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """通过 OpenClaw 调用模型"""
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
                timeout=120
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"⚠️  OpenClaw 错误: {result.stderr[:200]}")
                return ""
                
        except subprocess.TimeoutExpired:
            print("⚠️  OpenClaw 超时")
            return ""
        except Exception as e:
            print(f"⚠️  OpenClaw 调用失败: {e}")
            return ""
    
    def analyze(self, prompt: str, temperature: float = 0.3) -> str:
        """发送分析请求"""
        if not self.client:
            print("⚠️  LLM 客户端未初始化")
            return ""
        
        messages = [
            {"role": "system", "content": "你是一个专业的人才研究分析师，擅长从LinkedIn档案中提取关键信息并评估人才价值。"},
            {"role": "user", "content": prompt}
        ]
        
        if self.client == "openclaw":
            return self._call_openclaw(messages, temperature=temperature)
        else:
            print("⚠️  不支持的非 OpenClaw 模式")
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
        
        response = self.analyze(prompt, temperature=0.2)
        
        # 解析 JSON 响应
        try:
            json_start = response.find('{')
            json_end = response.rfind('}')
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end+1]
                result = json.loads(json_str)
                return result
            else:
                return {"error": "无法解析响应", "raw_response": response}
        except json.JSONDecodeError as e:
            return {"error": f"JSON解析错误: {e}", "raw_response": response}
