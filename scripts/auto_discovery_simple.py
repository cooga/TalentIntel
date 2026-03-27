#!/usr/bin/env python3
"""
简化版自动人才发现脚本 - 支持直连模式
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import urllib.parse
import warnings
import yaml

import aiohttp
from aiohttp import ClientTimeout, ClientSession

# 忽略SSL警告
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# 加载secrets
SECRETS_FILE = Path("config/.secrets.yaml")
if SECRETS_FILE.exists():
    with open(SECRETS_FILE) as f:
        secrets = yaml.safe_load(f)
        KIMI_API_KEY = secrets.get('kimi_api_key', '')
else:
    KIMI_API_KEY = os.getenv('KIMI_API_KEY', '')


class SimpleBrowser:
    """简化浏览器 - 支持直连"""
    
    def __init__(self, use_proxy: bool = False):
        self.use_proxy = use_proxy
        self.stats = {'requests': 0, 'success': 0, 'captcha_hits': 0}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        }
    
    async def request(self, url: str, timeout: int = 30) -> Optional[str]:
        """发送请求"""
        self.stats['requests'] += 1
        
        try:
            async with ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=ClientTimeout(total=timeout), ssl=False) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        self.stats['success'] += 1
                        
                        # 检测验证码
                        if self._is_captcha(html):
                            self.stats['captcha_hits'] += 1
                            print(f"   ⚠️  检测到验证码")
                            return None
                        
                        return html
                    else:
                        print(f"   ❌ HTTP {resp.status}")
                        return None
        except Exception as e:
            print(f"   ❌ 请求失败: {str(e)[:50]}")
            return None
    
    def _is_captcha(self, html: str) -> bool:
        """检测是否遇到验证码"""
        captcha_indicators = [
            'captcha', 'CAPTCHA', 'recaptcha', 'I\'m not a robot',
            'unusual traffic', 'verify you are human'
        ]
        return any(indicator in html.lower() for indicator in captcha_indicators)
    
    async def random_delay(self, min_sec: int, max_sec: int):
        """随机延迟"""
        delay = min_sec + (max_sec - min_sec) * (time.time() % 1)
        await asyncio.sleep(delay)


class SimpleLLMClient:
    """简化LLM客户端"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or KIMI_API_KEY
        self.base_url = "https://api.moonshot.cn/v1"
        self.model = "kimi-coding/k2p5"
    
    async def evaluate_profile(self, profile_text: str) -> Dict:
        """评估档案"""
        if not self.api_key:
            return self._mock_evaluation(profile_text)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = self._build_prompt(profile_text)
            
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
                        return self._parse_response(content, profile_text)
                    else:
                        print(f"   ❌ API错误: {resp.status}")
                        return self._mock_evaluation(profile_text)
        except Exception as e:
            print(f"   ❌ LLM调用失败: {e}")
            return self._mock_evaluation(profile_text)
    
    def _build_prompt(self, profile_text: str) -> str:
        """构建提示词"""
        return f"""分析以下LinkedIn档案，评估其与"AI+无线通信交叉领域研究"的匹配度。

档案内容:
{profile_text[:3000]}

请返回JSON格式:
{{
  "basic_info": {{
    "name": "姓名",
    "current_role": "当前职位",
    "current_company": "当前公司",
    "location": "地点"
  }},
  "ai_expertise": {{
    "level": "junior/mid/senior/expert",
    "domains": ["AI领域1"],
    "evidence": "证据"
  }},
  "wireless_expertise": {{
    "level": "junior/mid/senior/expert",
    "domains": ["无线领域1"],
    "evidence": "证据"
  }},
  "chinese_origin": {{
    "is_chinese": true/false,
    "confidence": 0.0-1.0,
    "evidence": "华人身份证据"
  }},
  "match_score": 0.0-1.0,
  "chinese_bonus": 0.0-0.2,
  "final_score": 0.0-1.2,
  "priority": "HIGH/MEDIUM/LOW",
  "match_reasons": ["理由1"],
  "recommended_action": "建议行动"
}}

评分标准: AI能力40% + Wireless能力40% + 背景20%
华人加分: 中文姓名+0.1，华人学校+0.05，中文内容+0.05"""
    
    def _parse_response(self, content: str, raw_text: str) -> Dict:
        """解析LLM响应"""
        try:
            # 提取JSON
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_match = re.search(r'\{[\s\S]*\}', content)
                json_str = json_match.group(0) if json_match else content
            
            data = json.loads(json_str)
            
            # 确保字段存在
            if "chinese_origin" not in data:
                data["chinese_origin"] = self._detect_chinese(raw_text)
            
            # 计算最终得分
            base_score = data.get("match_score", 0.5)
            chinese_bonus = data.get("chinese_bonus", 0)
            data["final_score"] = min(base_score + chinese_bonus, 1.2)
            
            return data
        except Exception as e:
            print(f"   ⚠️ 解析失败，使用模拟评估")
            return self._mock_evaluation(raw_text)
    
    def _detect_chinese(self, text: str) -> Dict:
        """检测华人身份"""
        indicators = {
            'chinese_chars': bool(re.search(r'[\u4e00-\u9fff]', text)),
            'chinese_surnames': bool(re.search(r'\b(Wang|Li|Zhang|Liu|Chen|Yang|Huang|Zhao|Zhou|Wu|Xu|Sun|Ma|Zhu|Hu|Guo|Lin|He|Gao|Liang|Zheng)\b', text, re.I)),
            'chinese_schools': any(s in text.lower() for s in ['tsinghua', 'peking', 'fudan', 'sjtu', 'ustc', 'zhejiang', 'nanjing']),
            'chinese_companies': any(c in text.lower() for c in ['huawei', 'alibaba', 'tencent', 'baidu', 'xiaomi', 'zte'])
        }
        
        score = sum([
            0.3 if indicators['chinese_chars'] else 0,
            0.2 if indicators['chinese_surnames'] else 0,
            0.15 if indicators['chinese_schools'] else 0,
            0.1 if indicators['chinese_companies'] else 0
        ])
        
        evidence = []
        if indicators['chinese_chars']: evidence.append("包含中文字符")
        if indicators['chinese_surnames']: evidence.append("华人姓氏")
        if indicators['chinese_schools']: evidence.append("中国高校")
        if indicators['chinese_companies']: evidence.append("中国公司经历")
        
        return {
            "is_chinese": score > 0.3,
            "confidence": min(score, 1.0),
            "evidence": "; ".join(evidence) if evidence else "未发现明显华人特征"
        }
    
    def _mock_evaluation(self, profile_text: str) -> Dict:
        """模拟评估（规则基础）"""
        text_lower = profile_text.lower()
        
        # AI关键词
        ai_keywords = ['machine learning', 'deep learning', 'neural network', 'ai ', 'artificial intelligence',
                       'pytorch', 'tensorflow', 'llm', 'large language model', 'computer vision', 'nlp']
        ai_score = sum(0.1 for k in ai_keywords if k in text_lower)
        ai_score = min(ai_score, 0.4)
        
        # Wireless关键词
        wireless_keywords = ['5g', '6g', 'wireless', 'mimo', 'ofdm', 'communication', 'signal processing',
                             'channel estimation', 'beamforming', 'rf', 'antenna', 'telecommunication']
        wireless_score = sum(0.1 for k in wireless_keywords if k in text_lower)
        wireless_score = min(wireless_score, 0.4)
        
        # 背景得分
        background_score = 0.1 if 'phd' in text_lower or 'doctor' in text_lower else 0.05
        
        # 华人检测
        chinese_info = self._detect_chinese(profile_text)
        chinese_bonus = 0.1 if chinese_info['is_chinese'] else 0
        
        base_score = min(ai_score + wireless_score + background_score, 1.0)
        final_score = min(base_score + chinese_bonus, 1.2)
        
        # 确定优先级
        if final_score >= 0.7:
            priority = "HIGH"
        elif final_score >= 0.5:
            priority = "MEDIUM"
        else:
            priority = "LOW"
        
        return {
            "basic_info": {
                "name": "Unknown",
                "current_role": "Unknown",
                "current_company": "Unknown",
                "location": "Unknown"
            },
            "ai_expertise": {
                "level": "mid" if ai_score > 0.2 else "junior",
                "domains": [k for k in ai_keywords if k in text_lower][:3],
                "evidence": f"AI关键词匹配: {len([k for k in ai_keywords if k in text_lower])}个"
            },
            "wireless_expertise": {
                "level": "mid" if wireless_score > 0.2 else "junior",
                "domains": [k for k in wireless_keywords if k in text_lower][:3],
                "evidence": f"无线关键词匹配: {len([k for k in wireless_keywords if k in text_lower])}个"
            },
            "chinese_origin": chinese_info,
            "match_score": round(base_score, 2),
            "chinese_bonus": chinese_bonus,
            "final_score": round(final_score, 2),
            "priority": priority,
            "match_reasons": [
                f"AI匹配度: {ai_score:.2f}",
                f"Wireless匹配度: {wireless_score:.2f}",
                f"华人加分: +{chinese_bonus:.2f}" if chinese_bonus > 0 else "非华人"
            ],
            "recommended_action": "人工审核" if final_score > 0.6 else "暂不考虑"
        }


class TalentDiscovery:
    """人才发现主类"""
    
    def __init__(self):
        self.browser = SimpleBrowser(use_proxy=False)
        self.llm = SimpleLLMClient()
        self.results = []
        
    async def discover(self, search_pages: int = 10, max_profiles: int = 50) -> List[Dict]:
        """执行发现流程"""
        print("="*70)
        print("🚀 TalentIntel 自动人才发现 (直连模式)")
        print("="*70)
        
        if not KIMI_API_KEY:
            print("⚠️  未配置KIMI_API_KEY，将使用规则评估（精度较低）")
        else:
            print("✅ Kimi LLM 已配置")
        
        print(f"\n📍 Phase 1: Google X-Ray 搜索 ({search_pages}页)")
        print("="*70)
        
        # 使用多个查询策略
        queries = [
            'site:linkedin.com/in ("Qualcomm" OR "NVIDIA" OR "Intel" OR "Samsung") ("AI Engineer" OR "Research Scientist") ("5G" OR "Deep Learning")',
            'site:linkedin.com/in ("Huawei" OR "ZTE" OR "MediaTek") ("算法工程师" OR "Senior Engineer") ("5G" OR "MIMO")',
            'site:linkedin.com/in ("Ericsson" OR "Nokia") ("Wireless Researcher" OR "Research Scientist") ("6G" OR "Machine Learning")',
        ]
        
        all_profiles = []
        seen_urls = set()
        
        for query_idx, query in enumerate(queries):
            print(f"\n🔍 查询策略 {query_idx + 1}/{len(queries)}")
            
            for page in range(min(3, search_pages // len(queries) + 1)):
                start = page * 10
                url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&start={start}&num=10"
                
                print(f"   第 {page+1} 页...", end=" ")
                html = await self.browser.request(url, timeout=15)
                
                if html:
                    profiles = self._extract_profiles(html, seen_urls)
                    all_profiles.extend(profiles)
                    print(f"✅ 发现 {len(profiles)} 个新档案 (累计: {len(all_profiles)})")
                else:
                    print("❌ 获取失败")
                
                await asyncio.sleep(2)
                
                if len(all_profiles) >= max_profiles * 2:
                    break
            
            if len(all_profiles) >= max_profiles * 2:
                break
        
        if not all_profiles:
            print("\n❌ 未发现任何档案")
            return []
        
        # 评估档案
        print(f"\n📍 Phase 2: 评估人才 ({min(len(all_profiles), max_profiles)}人)")
        print("="*70)
        
        evaluated = []
        for i, profile in enumerate(all_profiles[:max_profiles], 1):
            print(f"\n[{i}/{min(len(all_profiles), max_profiles)}] {profile['name']}")
            
            # 获取档案内容
            html = await self.browser.request(profile["url"], timeout=20)
            
            if html:
                # LLM评估
                result = await self.llm.evaluate_profile(html)
                full_result = {**profile, **result}
                evaluated.append(full_result)
                
                # 显示结果
                is_chinese = result.get("chinese_origin", {}).get("is_chinese", False)
                final_score = result.get("final_score", 0)
                priority = result.get("priority", "LOW")
                
                chinese_tag = "🇨🇳" if is_chinese else ""
                priority_icon = "🔥" if priority == "HIGH" else "⭐" if priority == "MEDIUM" else "⚪"
                
                print(f"   基础分: {result.get('match_score', 0):.2f} | "
                      f"华人加分: +{result.get('chinese_bonus', 0):.2f} | "
                      f"最终分: {final_score:.2f} {priority_icon} {chinese_tag}")
            else:
                print(f"   ❌ 获取档案失败")
            
            if i < min(len(all_profiles), max_profiles):
                await asyncio.sleep(3)
        
        # 保存结果
        await self._save_results(evaluated)
        self._print_stats(evaluated)
        
        return evaluated
    
    def _extract_profiles(self, html: str, seen: set) -> List[Dict]:
        """提取LinkedIn档案"""
        profiles = []
        urls = re.findall(r'https://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_.]+', html)
        
        for url in urls:
            url = re.sub(r'\?.*$', '', url)
            if url not in seen:
                seen.add(url)
                name_match = re.search(r'/in/([a-zA-Z0-9\-_.]+)', url)
                name = name_match.group(1).replace('-', ' ').title() if name_match else "Unknown"
                profiles.append({
                    "url": url,
                    "name": name,
                    "discovered_at": datetime.now().isoformat()
                })
        
        return profiles
    
    async def _save_results(self, results: List[Dict]):
        """保存结果"""
        output_dir = Path("data/findings") / datetime.now().strftime("%Y-%m-%d")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存每个高分候选人的详细档案
        high_score_count = 0
        for result in results:
            if result.get('final_score', 0) >= 0.7:
                high_score_count += 1
                name = result.get('basic_info', {}).get('name', result.get('name', 'unknown'))
                name_clean = re.sub(r'[^\w\s]', '', name).replace(' ', '_').lower()[:20]
                
                file_path = output_dir / f"{name_clean}_{int(result.get('final_score', 0)*100000)}.json"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 保存汇总
        summary_file = output_dir / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_discovered": len(results),
                "high_score_count": high_score_count,
                "high_score_threshold": 0.7,
                "profiles": results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 结果已保存到: {output_dir}")
        print(f"   - 高分候选人档案: {high_score_count}个")
        print(f"   - 汇总文件: summary.json")
    
    def _print_stats(self, results: List[Dict]):
        """打印统计"""
        print("\n" + "="*70)
        print("📊 发现统计")
        print("="*70)
        
        if not results:
            print("未发现任何候选人")
            return
        
        chinese_count = sum(1 for r in results if r.get("chinese_origin", {}).get("is_chinese"))
        high_match = sum(1 for r in results if r.get("final_score", 0) >= 0.7)
        medium_match = sum(1 for r in results if 0.5 <= r.get("final_score", 0) < 0.7)
        
        print(f"总计评估: {len(results)} 人")
        print(f"🇨🇳 华人人才: {chinese_count} 人 ({chinese_count/len(results)*100:.1f}%)")
        print(f"🔥 高匹配 (≥0.7): {high_match} 人")
        print(f"⭐ 中匹配 (0.5-0.7): {medium_match} 人")
        print(f"⚪ 低匹配 (<0.5): {len(results) - high_match - medium_match} 人")
        
        print(f"\n浏览器统计:")
        print(f"  总请求: {self.browser.stats['requests']}")
        print(f"  成功: {self.browser.stats['success']}")
        print(f"  验证码: {self.browser.stats['captcha_hits']} 次")
        
        # 显示高分候选人
        if high_match > 0:
            print(f"\n🏆 高分候选人 (≥0.7):")
            for r in sorted(results, key=lambda x: x.get('final_score', 0), reverse=True)[:10]:
                if r.get('final_score', 0) >= 0.7:
                    name = r.get('basic_info', {}).get('name', r.get('name', 'Unknown'))
                    company = r.get('basic_info', {}).get('current_company', 'Unknown')
                    score = r.get('final_score', 0)
                    flag = "🇨🇳" if r.get('chinese_origin', {}).get('is_chinese') else ""
                    print(f"   {name} @ {company}: {score:.2f} {flag}")


async def main():
    """主函数"""
    discovery = TalentDiscovery()
    results = await discovery.discover(search_pages=12, max_profiles=50)
    print("\n✅ 完成!")
    return results


if __name__ == "__main__":
    results = asyncio.run(main())
    
    # 输出结果数量供主脚本解析
    high_score = sum(1 for r in results if r.get('final_score', 0) >= 0.7)
    print(f"\n🎯 RESULTS: total={len(results)}, high_score={high_score}")
