"""
增强版全自动人才发现系统
- 10个代理池
- 集成Kimi LLM真实评估
- 验证码即时提醒
- 华人优先识别和加分
"""

import asyncio
import json
import os
import random
import re
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
import urllib.parse
import hashlib
import warnings

import aiohttp
from aiohttp import ClientTimeout, TCPConnector, ClientSession

# 忽略SSL警告
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


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
        return {"http": url, "https": url}
    
    def __hash__(self):
        return hash(f"{self.host}:{self.port}")
    
    def __str__(self):
        return f"{self.host}:{self.port}"


class NotificationManager:
    """通知管理器 - 用于验证码等关键事件提醒"""
    
    def __init__(self):
        self.captcha_count = 0
        self.last_notification = None
    
    def notify_captcha(self, proxy: str, url: str):
        """验证码提醒"""
        self.captcha_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        message = f"""
{'='*60}
🚨 【验证码警报 #{self.captcha_count}】 {timestamp}
{'='*60}
⚠️  检测到验证码/反爬验证！

📍 位置: {url[:60]}...
🔌 代理: {proxy}

💡 建议操作:
1. 检查代理池状态
2. 增加延时时间
3. 更换更高质量代理
4. 暂停运行，稍后重试

⏳ 系统将自动切换代理并重试...
{'='*60}
"""
        print(message)
        self.last_notification = datetime.now()
        
        # 如果连续多次验证码，建议暂停
        if self.captcha_count >= 3:
            print("\n⚠️  警告: 已连续触发3次验证码，建议暂停运行并检查代理配置！\n")


class ProxyPool:
    """增强版代理池管理器 - 支持10+代理"""
    
    def __init__(self, proxies: List[Proxy] = None):
        self.proxies = proxies or []
        self.healthy_proxies: Set[Proxy] = set()
        self.failed_proxies: Dict[Proxy, datetime] = {}
        self.current_index = 0
        self.stats = {p: {"success": 0, "fail": 0, "consecutive_fail": 0} for p in self.proxies}
        
    def add_proxy(self, proxy: Proxy):
        """添加代理"""
        self.proxies.append(proxy)
        self.stats[proxy] = {"success": 0, "fail": 0, "consecutive_fail": 0}
        
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
        
        # 并发检查所有代理
        tasks = [self.health_check(p) for p in self.proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        healthy_count = 0
        for proxy, healthy in zip(self.proxies, results):
            if healthy is True:
                self.healthy_proxies.add(proxy)
                healthy_count += 1
                print(f"  ✅ {proxy}")
            else:
                self.failed_proxies[proxy] = datetime.now()
                print(f"  ❌ {proxy}")
        
        print(f"\n代理健康: {healthy_count}/{len(self.proxies)} ({healthy_count/len(self.proxies)*100:.1f}%)")
        
        if healthy_count < 3:
            print("⚠️  警告: 健康代理少于3个，建议添加更多代理！")
    
    def get_next(self) -> Optional[Proxy]:
        """获取下一个可用代理"""
        # 清理超过30分钟的失败代理，尝试恢复
        now = datetime.now()
        recovered = []
        for proxy, failed_time in list(self.failed_proxies.items()):
            if now - failed_time > timedelta(minutes=30):
                recovered.append(proxy)
                self.stats[proxy]["consecutive_fail"] = 0
        
        for proxy in recovered:
            del self.failed_proxies[proxy]
            self.healthy_proxies.add(proxy)
            print(f"🔄 代理恢复: {proxy}")
        
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
        self.stats[proxy]["consecutive_fail"] = 0
        
    def report_failure(self, proxy: Proxy, is_captcha: bool = False):
        """报告失败"""
        self.stats[proxy]["fail"] += 1
        self.stats[proxy]["consecutive_fail"] += 1
        
        # 连续失败2次或遇到验证码则降级
        if self.stats[proxy]["consecutive_fail"] >= 2 or is_captcha:
            self.healthy_proxies.discard(proxy)
            self.failed_proxies[proxy] = datetime.now()
            print(f"⚠️  代理降级: {proxy} (连续失败: {self.stats[proxy]['consecutive_fail']})")


class KimiLLMClient:
    """Kimi LLM 客户端"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
        self.base_url = "https://api.moonshot.cn/v1"
        self.model = "kimi-coding/k2p5"  # 使用K2.5模型
        
        if not self.api_key:
            print("⚠️  警告: 未设置KIMI_API_KEY，将使用模拟评估")
    
    async def evaluate_profile(self, profile_text: str) -> Dict:
        """评估LinkedIn档案"""
        if not self.api_key:
            # 模拟评估
            await asyncio.sleep(1)
            return self._mock_evaluation(profile_text)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = self._build_evaluation_prompt(profile_text)
            
            async with ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "你是一个资深HR和AI领域专家，专门评估AI+无线通信领域人才。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1500
                    },
                    timeout=ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        return self._parse_llm_response(content, profile_text)
                    else:
                        print(f"❌ LLM API错误: {resp.status}")
                        return self._mock_evaluation(profile_text)
                        
        except Exception as e:
            print(f"❌ LLM调用失败: {e}")
            return self._mock_evaluation(profile_text)
    
    def _build_evaluation_prompt(self, profile_text: str) -> str:
        """构建评估提示词"""
        return f"""请分析以下LinkedIn档案，评估其与"AI+无线通信交叉领域研究"的匹配度。

档案内容:
{profile_text[:3000]}

请从以下维度评估，并以JSON格式返回:

```json
{{
  "basic_info": {{
    "name": "姓名",
    "current_role": "当前职位",
    "current_company": "当前公司",
    "location": "地点",
    "education": "最高学历"
  }},
  "ai_expertise": {{
    "level": "junior/mid/senior/expert",
    "domains": ["AI领域1", "AI领域2"],
    "evidence": "支持证据"
  }},
  "wireless_expertise": {{
    "level": "junior/mid/senior/expert", 
    "domains": ["无线领域1", "无线领域2"],
    "evidence": "支持证据"
  }},
  "chinese_origin": {{
    "is_chinese": true/false,
    "confidence": 0.0-1.0,
    "evidence": "华人身份证据（姓名、学校、经历等）"
  }},
  "match_score": 0.0-1.0,
  "chinese_bonus": 0.0-0.2,
  "final_score": 0.0-1.2,
  "priority": "HIGH/MEDIUM/LOW",
  "match_reasons": ["理由1", "理由2", "理由3"],
  "red_flags": ["潜在顾虑1"],
  "recommended_action": "建议行动"
}}
```

评分标准:
- 基础匹配度0-1.0：AI能力40% + Wireless能力40% + 背景20%
- 华人加分0-0.2：中文姓名+0.1，华人学校+0.05，中文内容+0.05
- 最终得分可达1.2

请确保JSON格式正确。"""
    
    def _parse_llm_response(self, content: str, raw_text: str) -> Dict:
        """解析LLM响应"""
        try:
            # 提取JSON
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content
            
            data = json.loads(json_str)
            
            # 确保有chinese_origin字段
            if "chinese_origin" not in data:
                data["chinese_origin"] = self._detect_chinese_origin(raw_text)
            
            # 计算最终得分
            base_score = data.get("match_score", 0.5)
            chinese_bonus = data.get("chinese_bonus", 0)
            data["final_score"] = min(base_score + chinese_bonus, 1.2)
            
            return data
            
        except Exception as e:
            print(f"⚠️  LLM响应解析失败，使用默认值: {e}")
            return self._mock_evaluation(raw_text)
    
    def _detect_chinese_origin(self, text: str) -> Dict:
        """检测华人身份"""
        chinese_indicators = {
            "name_patterns": [r'[\u4e00-\u9fff]', r'\b(Wang|Li|Zhang|Liu|Chen|Yang|Huang|Zhao|Zhou|Wu)\b'],
            "schools": ["Tsinghua", "Peking", "USTC", "SJTU", "Fudan", "Zhejiang", "Nanjing"],
            "companies": ["Huawei", "Alibaba", "Tencent", "Baidu", "Xiaomi", "ZTE"],
            "locations": ["China", "Beijing", "Shanghai", "Shenzhen", "Hong Kong"],
        }
        
        score = 0
        evidence = []
        
        # 检测中文
        if re.search(chinese_indicators["name_patterns"][0], text):
            score += 0.3
            evidence.append("包含中文字符")
        
        # 检测华人姓氏
        if re.search(chinese_indicators["name_patterns"][1], text, re.IGNORECASE):
            score += 0.2
            evidence.append("华人常见姓氏")
        
        # 检测学校
        for school in chinese_indicators["schools"]:
            if school.lower() in text.lower():
                score += 0.15
                evidence.append(f"毕业于{school}")
                break
        
        # 检测公司
        for company in chinese_indicators["companies"]:
            if company.lower() in text.lower():
                score += 0.1
                evidence.append(f"曾在{company}工作")
                break
        
        # 检测地点
        for loc in chinese_indicators["locations"]:
            if loc.lower() in text.lower():
                score += 0.05
                evidence.append(f"位于{loc}")
                break
        
        return {
            "is_chinese": score >= 0.3,
            "confidence": min(score, 1.0),
            "evidence": "; ".join(evidence) if evidence else "无明显华人特征"
        }
    
    def _mock_evaluation(self, text: str) -> Dict:
        """模拟评估（当LLM不可用时）"""
        chinese_info = self._detect_chinese_origin(text)
        
        # 基于文本特征生成评分
        has_ai = any(kw in text.lower() for kw in ["ai", "machine learning", "deep learning"])
        has_wireless = any(kw in text.lower() for kw in ["wireless", "5g", "mimo", "communication"])
        
        base_score = 0.5
        if has_ai: base_score += 0.2
        if has_wireless: base_score += 0.2
        
        chinese_bonus = min(chinese_info["confidence"] * 0.2, 0.2)
        final_score = min(base_score + chinese_bonus, 1.2)
        
        return {
            "basic_info": {"name": "Unknown", "current_role": "Unknown", "location": "Unknown"},
            "ai_expertise": {"level": "mid" if has_ai else "junior", "domains": ["AI"], "evidence": "关键词匹配"},
            "wireless_expertise": {"level": "mid" if has_wireless else "junior", "domains": ["Wireless"], "evidence": "关键词匹配"},
            "chinese_origin": chinese_info,
            "match_score": base_score,
            "chinese_bonus": chinese_bonus,
            "final_score": final_score,
            "priority": "HIGH" if final_score > 0.7 else "MEDIUM" if final_score > 0.5 else "LOW",
            "match_reasons": ["关键词匹配"],
            "red_flags": ["LLM评估失败，使用规则评估"],
            "recommended_action": "建议人工复核"
        }


class AntiDetectBrowser:
    """增强版反检测浏览器"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    ]
    
    def __init__(self, proxy_pool: ProxyPool, notifier: NotificationManager):
        self.proxy_pool = proxy_pool
        self.notifier = notifier
        self.stats = {"requests": 0, "success": 0, "captcha_hits": 0, "blocks": 0}
        
    def get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8"]),
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    async def random_delay(self, min_sec: float = 3.0, max_sec: float = 8.0):
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)
    
    def is_captcha(self, html: str) -> bool:
        indicators = ["captcha", "CAPTCHA", "recaptcha", "I'm not a robot", 
                     "unusual traffic", "automated requests", "429", "Too Many Requests"]
        return any(ind in html for ind in indicators)
    
    async def request(self, url: str, max_retries: int = 3, timeout: int = 30) -> Optional[str]:
        for attempt in range(max_retries):
            proxy = self.proxy_pool.get_next()
            if not proxy:
                print("❌ 无可用代理")
                return None
            
            try:
                await self.random_delay(2, 5)
                timeout_obj = ClientTimeout(total=timeout)
                
                async with ClientSession(timeout=timeout_obj) as session:
                    async with session.get(
                        url, headers=self.get_headers(),
                        proxy=proxy.to_dict()["http"], ssl=False
                    ) as resp:
                        self.stats["requests"] += 1
                        html = await resp.text()
                        
                        # 检测验证码
                        if self.is_captcha(html):
                            self.stats["captcha_hits"] += 1
                            self.notifier.notify_captcha(str(proxy), url)
                            self.proxy_pool.report_failure(proxy, is_captcha=True)
                            await asyncio.sleep(10)
                            continue
                        
                        if resp.status == 200:
                            self.proxy_pool.report_success(proxy)
                            self.stats["success"] += 1
                            return html
                        
            except asyncio.TimeoutError:
                self.proxy_pool.report_failure(proxy)
            except Exception as e:
                self.proxy_pool.report_failure(proxy)
        
        return None


class EnhancedTalentDiscovery:
    """增强版全自动人才发现系统"""
    
    def __init__(self):
        self.proxy_pool = ProxyPool()
        self.notifier = NotificationManager()
        self.browser = AntiDetectBrowser(self.proxy_pool, self.notifier)
        self.llm = KimiLLMClient()
        self.results: List[Dict] = []
        
        # 配置10个代理
        self._setup_proxies()
    
    def _setup_proxies(self):
        """配置10个代理（示例配置，需替换为真实代理）"""
        # 这里使用示例代理，实际应替换为你的代理
        proxy_list = [
            # 免费代理示例（不稳定）
            Proxy("103.152.112.157", 80),
            Proxy("47.242.43.189", 1080),
            Proxy("47.74.152.29", 8888),
            Proxy("47.243.175.55", 8080),
            Proxy("8.210.83.33", 80),
            # 添加更多代理...
        ]
        
        for proxy in proxy_list:
            self.proxy_pool.add_proxy(proxy)
    
    async def initialize(self):
        """初始化"""
        print("="*70)
        print("🚀 TalentIntel Auto Discovery - 增强版全自动人才发现")
        print("   特性: 10代理池 | Kimi LLM评估 | 华人优先 | 验证码警报")
        print("="*70)
        
        await self.proxy_pool.initialize()
        
        # 检查LLM
        if not self.llm.api_key:
            print("⚠️  未配置KIMI_API_KEY，将使用规则评估（精度较低）")
        else:
            print("✅ Kimi LLM 已配置")
    
    async def discover(self, search_pages: int = 10, max_profiles: int = 20) -> List[Dict]:
        """执行发现流程"""
        # 构建查询（华人优先）
        query = self._build_chinese_priority_query()
        
        # Google搜索
        profiles = await self._google_search(query, search_pages)
        
        if not profiles:
            print("❌ 未发现任何档案")
            return []
        
        # 评估档案
        evaluated = await self._evaluate_profiles(profiles[:max_profiles])
        
        # 保存结果
        await self._save_results(evaluated)
        self._print_stats(evaluated)
        
        return evaluated
    
    def _build_chinese_priority_query(self) -> str:
        """构建华人优先的搜索查询"""
        companies = [
            "Qualcomm", "NVIDIA", "Intel", "Samsung", "Apple", "Meta",
            "Huawei", "Alibaba", "Tencent", "Baidu", "ByteDance"
        ]
        titles = ["AI Engineer", "Research Scientist", "算法工程师", "Staff Engineer"]
        skills = ["5G", "Deep Learning", "MIMO", "AI", "机器学习"]
        locations = ["United States", "Canada", "Singapore", "China"]
        
        parts = ["site:linkedin.com/in"]
        parts.append(f"({' OR '.join([f'\"{c}\"' for c in companies])})")
        parts.append(f"({' OR '.join([f'\"{t}\"' for t in titles])})")
        parts.append(f"({' OR '.join([f'\"{s}\"' for s in skills])})")
        parts.append(f"({' OR '.join([f'\"{l}\"' for l in locations])})")
        
        return " ".join(parts)
    
    async def _google_search(self, query: str, num_pages: int) -> List[Dict]:
        """Google搜索"""
        print(f"\n📍 Phase 1: Google X-Ray 搜索 ({num_pages}页)")
        print("="*70)
        
        profiles = []
        seen = set()
        
        for page in range(num_pages):
            start = page * 10
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&start={start}&num=10"
            
            print(f"\n📄 第 {page+1}/{num_pages}页...")
            html = await self.browser.request(url)
            
            if html:
                # 提取档案
                new_profiles = self._extract_profiles(html, seen)
                profiles.extend(new_profiles)
                print(f"   ✅ 发现 {len(new_profiles)} 个新档案 (累计: {len(profiles)})")
            else:
                print(f"   ❌ 获取失败")
            
            if page < num_pages - 1:
                await self.browser.random_delay(5, 10)
        
        return profiles
    
    def _extract_profiles(self, html: str, seen: Set[str]) -> List[Dict]:
        """提取LinkedIn档案"""
        profiles = []
        urls = re.findall(r'https://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_.]+', html)
        
        for url in urls:
            url = re.sub(r'\?.*$', '', url)
            if url not in seen:
                seen.add(url)
                name_match = re.search(r'/in/([a-zA-Z0-9\-_.]+)', url)
                name = name_match.group(1).replace('-', ' ').title() if name_match else "Unknown"
                profiles.append({"url": url, "name": name, "discovered_at": datetime.now().isoformat()})
        
        return profiles
    
    async def _evaluate_profiles(self, profiles: List[Dict]) -> List[Dict]:
        """评估档案"""
        print(f"\n📍 Phase 2: LLM人才评估 ({len(profiles)}人)")
        print("="*70)
        
        evaluated = []
        
        for i, profile in enumerate(profiles, 1):
            print(f"\n[{i}/{len(profiles)}] {profile['name']}")
            
            # 获取档案内容
            html = await self.browser.request(profile["url"], timeout=45)
            
            if html:
                # LLM评估
                result = await self.llm.evaluate_profile(html)
                evaluated.append({**profile, **result})
                
                # 显示结果
                is_chinese = result.get("chinese_origin", {}).get("is_chinese", False)
                final_score = result.get("final_score", 0)
                chinese_tag = "🇨🇳" if is_chinese else ""
                
                print(f"   基础分: {result.get('match_score', 0):.2f} | "
                      f"华人加分: +{result.get('chinese_bonus', 0):.2f} | "
                      f"最终分: {final_score:.2f} {chinese_tag}")
            else:
                print(f"   ❌ 获取失败")
            
            if i < len(profiles):
                await self.browser.random_delay(30, 60)
        
        return evaluated
    
    async def _save_results(self, results: List[Dict]):
        """保存结果"""
        output_dir = Path("data/auto_discovery")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"results_enhanced_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "config": {
                    "search_pages": 10,
                    "max_profiles": 20,
                    "llm": "kimi-k2.5" if self.llm.api_key else "mock",
                    "chinese_priority": True,
                },
                "stats": {
                    "total": len(results),
                    "high_match": len([r for r in results if r.get('final_score', 0) > 0.7]),
                    "chinese": len([r for r in results if r.get('chinese_origin', {}).get('is_chinese')]),
                },
                "profiles": results,
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 结果已保存: {output_file}")
    
    def _print_stats(self, results: List[Dict]):
        """打印统计"""
        print("\n" + "="*70)
        print("📊 发现统计")
        print("="*70)
        
        chinese_count = len([r for r in results if r.get("chinese_origin", {}).get("is_chinese")])
        high_match = len([r for r in results if r.get("final_score", 0) > 0.7])
        
        print(f"总计发现: {len(results)} 人")
        print(f"🇨🇳 华人人才: {chinese_count} 人 ({chinese_count/len(results)*100:.1f}%)")
        print(f"🔥 高匹配 (≥0.7): {high_match} 人")
        print(f"\n浏览器统计:")
        print(f"  总请求: {self.browser.stats['requests']}")
        print(f"  成功: {self.browser.stats['success']}")
        print(f"  验证码: {self.browser.stats['captcha_hits']} 次")


async def main():
    """主函数"""
    discovery = EnhancedTalentDiscovery()
    await discovery.initialize()
    
    # 执行发现 (10页搜索，评估20人)
    results = await discovery.discover(search_pages=10, max_profiles=20)
    
    print("\n✅ 完成!")


if __name__ == "__main__":
    asyncio.run(main())
