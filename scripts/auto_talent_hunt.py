#!/usr/bin/env python3
"""
TalentIntel 自动化人才检索执行脚本
目标: 收集50个≥0.7分的高分候选人

策略:
1. 多关键词 XRay 搜索生成
2. 使用代理池抓取 Google 结果
3. 批量评估候选人
4. 持续运行直到目标达成
"""

import asyncio
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import urllib.parse
import random
import yaml

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import aiohttp
from aiohttp import ClientTimeout, ClientSession

# 忽略SSL警告
import warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


class ProxyPool:
    """代理池管理"""

    def __init__(self, config_path: str = "config/proxies.yaml"):
        self.proxies = []
        self.working_proxies = []
        self.current_index = 0
        self.load_config(config_path)

    def load_config(self, path: str):
        """加载代理配置"""
        try:
            with open(path) as f:
                config = yaml.safe_load(f)
                self.proxies = config.get('proxies', [])
                print(f"✅ 已加载 {len(self.proxies)} 个代理")
        except Exception as e:
            print(f"⚠️  代理配置加载失败: {e}")
            self.proxies = []

    async def health_check(self) -> List[Dict]:
        """健康检查 - 测试代理可用性"""
        print("🔍 开始代理健康检查...")
        working = []

        test_url = "http://httpbin.org/ip"
        timeout = ClientTimeout(total=10)

        for i, proxy in enumerate(self.proxies[:5]):  # 测试前5个
            proxy_url = f"http://{proxy['host']}:{proxy['port']}"
            try:
                async with ClientSession(timeout=timeout) as session:
                    async with session.get(test_url, proxy=proxy_url, ssl=False) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            print(f"  ✅ [{i+1}] {proxy['host']}:{proxy['port']} - {data.get('origin', 'OK')}")
                            working.append(proxy)
                        else:
                            print(f"  ❌ [{i+1}] {proxy['host']}:{proxy['port']} - HTTP {resp.status}")
            except Exception as e:
                print(f"  ❌ [{i+1}] {proxy['host']}:{proxy['port']} - {str(e)[:40]}")

        self.working_proxies = working
        print(f"📊 可用代理: {len(working)}/{min(5, len(self.proxies))}")
        return working

    def get_next_proxy(self) -> Optional[Dict]:
        """获取下一个代理（轮询）"""
        if not self.working_proxies:
            return None
        proxy = self.working_proxies[self.current_index % len(self.working_proxies)]
        self.current_index += 1
        return proxy


class XRaySearcher:
    """XRay 搜索 - Google 搜索 LinkedIn"""

    def __init__(self, proxy_pool: ProxyPool = None):
        self.proxy_pool = proxy_pool
        self.base_url = "https://www.google.com/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.stats = {"searches": 0, "success": 0, "profiles_found": 0}

    def build_query(self, keywords: List[str], location: str = None) -> str:
        """构建搜索查询"""
        base = "site:linkedin.com/in"
        kw_part = " OR ".join([f'"{k}"' for k in keywords])
        query = f"{base} ({kw_part})"
        if location:
            query += f' "{location}"'
        return query

    async def search(self, query: str, num_results: int = 20) -> List[Dict]:
        """执行搜索"""
        self.stats["searches"] += 1
        profiles = []

        # 获取代理
        proxy = self.proxy_pool.get_next_proxy() if self.proxy_pool else None
        proxy_url = f"http://{proxy['host']}:{proxy['port']}" if proxy else None

        try:
            # 构建搜索URL
            params = {
                "q": query,
                "num": num_results,
                "hl": "en",
                "filter": "0",
            }
            url = f"{self.base_url}?{urllib.parse.urlencode(params)}"

            print(f"🔍 搜索: {query[:60]}...")

            timeout = ClientTimeout(total=15)
            async with ClientSession(headers=self.headers, timeout=timeout) as session:
                kwargs = {"ssl": False}
                if proxy_url:
                    kwargs["proxy"] = proxy_url

                async with session.get(url, **kwargs) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        profiles = self._extract_profiles(html)
                        self.stats["success"] += 1
                        self.stats["profiles_found"] += len(profiles)
                        print(f"  ✅ 找到 {len(profiles)} 个档案")
                    elif resp.status == 429:
                        print(f"  ⚠️  触发Google限制(429)")
                    else:
                        print(f"  ❌ HTTP {resp.status}")

        except Exception as e:
            print(f"  ❌ 搜索失败: {str(e)[:50]}")

        return profiles

    def _extract_profiles(self, html: str) -> List[Dict]:
        """从HTML中提取LinkedIn档案链接"""
        profiles = []

        # 匹配 LinkedIn 链接
        pattern = r'https://[^"\s<>]*linkedin\.com/in/[^"\s<>]+'
        urls = re.findall(pattern, html, re.IGNORECASE)

        seen = set()
        for url in urls:
            # 清洗URL
            clean_url = re.sub(r'\?.*$', '', url)
            clean_url = re.sub(r'/$', '', clean_url)

            if clean_url not in seen and '/in/' in clean_url:
                seen.add(clean_url)
                # 提取姓名
                name_match = re.search(r'/in/([^/]+)', clean_url)
                name = name_match.group(1).replace('-', ' ').replace('_', ' ').title() if name_match else "Unknown"

                profiles.append({
                    "url": clean_url,
                    "name": name,
                    "source": "xray",
                    "discovered_at": datetime.now().isoformat()
                })

        return profiles


class SimpleEvaluator:
    """简化版候选人评估器"""

    def __init__(self):
        self.results = []
        self.high_matches = []
        self.stats = {"evaluated": 0, "high_score": 0}

    def evaluate(self, profile_text: str, url: str = "") -> Dict:
        """评估候选人档案"""
        self.stats["evaluated"] += 1

        text_lower = profile_text.lower()

        # 关键词匹配评分
        ai_keywords = [
            "machine learning", "deep learning", "ai ", "artificial intelligence",
            "neural network", "reinforcement learning", "llm", "transformer",
            "pytorch", "tensorflow", "keras", "computer vision", "nlp"
        ]

        wireless_keywords = [
            "wireless", "5g", "6g", "mimo", "ofdm", "communication",
            "signal processing", "channel estimation", "beamforming",
            "radio", "antenna", "phy", "mac layer", "cellular", "lte",
            "telecommunication", "rf", "baseband", "modem"
        ]

        ai_score = sum(1 for kw in ai_keywords if kw in text_lower)
        wireless_score = sum(1 for kw in wireless_keywords if kw in text_lower)

        # 计算匹配分数 (0-1)
        ai_normalized = min(ai_score / 3, 1.0)  # 至少3个AI关键词
        wireless_normalized = min(wireless_score / 3, 1.0)  # 至少3个无线关键词

        # 交叉领域加权
        if ai_score >= 2 and wireless_score >= 2:
            cross_bonus = 0.2
        else:
            cross_bonus = 0

        match_score = (ai_normalized * 0.4 + wireless_normalized * 0.4 + cross_bonus)
        match_score = min(match_score, 1.0)

        # 提取基本信息
        name = self._extract_name(profile_text)
        title = self._extract_title(profile_text)
        company = self._extract_company(profile_text)

        result = {
            "url": url,
            "match_score": round(match_score, 2),
            "evaluation": {
                "basic_info": {
                    "name": name,
                    "current_role": title,
                    "current_company": company,
                },
                "ai_expertise": {
                    "level": "expert" if ai_score >= 4 else "senior" if ai_score >= 2 else "mid",
                    "score": ai_score,
                },
                "wireless_expertise": {
                    "level": "expert" if wireless_score >= 4 else "senior" if wireless_score >= 2 else "mid",
                    "score": wireless_score,
                },
                "priority": "high" if match_score >= 0.7 else "medium" if match_score >= 0.5 else "low",
            },
            "_meta": {
                "evaluated_at": datetime.now().isoformat(),
            }
        }

        if match_score >= 0.7:
            self.stats["high_score"] += 1
            self.high_matches.append(result)
            print(f"    ⭐ 高分候选人! 分数: {match_score:.2f}")

        return result

    def _extract_name(self, text: str) -> str:
        """提取姓名"""
        lines = text.strip().split('\n')
        if lines:
            return lines[0][:50]
        return "Unknown"

    def _extract_title(self, text: str) -> str:
        """提取职位"""
        patterns = [
            r'(?:Title|职位|Headline)[:\s]+([^\n]+)',
            r'\n([^\n]+(?:Engineer|Scientist|Researcher|Manager|Director))\n',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:50]
        return ""

    def _extract_company(self, text: str) -> str:
        """提取公司"""
        companies = [
            "Qualcomm", "Huawei", "Samsung", "NVIDIA", "Intel", "Ericsson",
            "Nokia", "Apple", "Google", "Meta", "Microsoft", "Amazon",
            "MediaTek", "ZTE", "Cisco", "Bell Labs", "InterDigital"
        ]
        for company in companies:
            if company.lower() in text.lower():
                return company
        return ""


class TalentDiscoveryEngine:
    """人才发现引擎 - 主控制器"""

    # 多关键词搜索策略
    SEARCH_STRATEGIES = [
        {
            "name": "ML Wireless",
            "keywords": ["machine learning wireless", "AI wireless communication"],
            "locations": ["United States", "Canada"]
        },
        {
            "name": "AI Engineer 5G",
            "keywords": ["AI engineer 5G", "deep learning 5G"],
            "locations": ["United States", "Singapore"]
        },
        {
            "name": "Wireless Researcher",
            "keywords": ["wireless communication researcher", "MIMO researcher"],
            "locations": ["Sweden", "Finland", "Germany"]
        },
        {
            "name": "MIMO Deep Learning",
            "keywords": ["MIMO deep learning", "OFDM neural network"],
            "locations": ["United States", "China"]
        },
        {
            "name": "6G AI",
            "keywords": ["6G AI", "6G machine learning"],
            "locations": ["Europe", "United States"]
        },
        {
            "name": "Signal Processing ML",
            "keywords": ["signal processing machine learning", "channel estimation deep learning"],
            "locations": ["United States", "UK"]
        },
    ]

    def __init__(self):
        self.proxy_pool = ProxyPool()
        self.searcher = None
        self.evaluator = SimpleEvaluator()
        self.target_count = 100  # 总目标：100个高分候选人
        self.chinese_target = 40  # 华人候选人目标：40人
        self.current_high_matches = []
        self.chinese_candidates = []  # 华人候选人列表
        self.output_dir = Path("data/findings")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 加载已有进度
        self.load_existing_progress()

    def load_existing_progress(self):
        """加载已有高分候选人"""
        existing_files = list(self.output_dir.glob("**/*.json"))
        for f in existing_files:
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    if isinstance(data, dict) and data.get("match_score", 0) >= 0.7:
                        self.current_high_matches.append(data)
            except:
                pass

        # 去重
        seen_urls = set()
        unique = []
        for m in self.current_high_matches:
            url = m.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(m)
        self.current_high_matches = unique

        print(f"📊 已加载 {len(self.current_high_matches)} 个已有高分候选人")

    async def run(self):
        """运行人才发现流程"""
        print("=" * 70)
        print("🎯 TalentIntel 自动化人才检索")
        print(f"目标: 收集 {self.target_count} 个≥0.7分候选人")
        print("=" * 70)

        # 1. 代理健康检查
        working_proxies = await self.proxy_pool.health_check()
        if not working_proxies:
            print("⚠️  无可用的免费代理，将降低请求频率并使用备用策略")

        self.searcher = XRaySearcher(self.proxy_pool if working_proxies else None)

        # 2. 执行多策略搜索
        strategy_index = 0
        round_num = 0

        while len(self.current_high_matches) < self.target_count:
            round_num += 1
            print(f"\n{'='*70}")
            print(f"🔄 第 {round_num} 轮搜索 - 当前进度: {len(self.current_high_matches)}/{self.target_count}")
            print('='*70)

            strategy = self.SEARCH_STRATEGIES[strategy_index % len(self.SEARCH_STRATEGIES)]
            strategy_index += 1

            print(f"\n📋 当前策略: {strategy['name']}")

            for keyword in strategy["keywords"]:
                for location in strategy["locations"]:
                    if len(self.current_high_matches) >= self.target_count:
                        break

                    query = self.searcher.build_query([keyword], location)
                    profiles = await self.searcher.search(query, num_results=10)

                    # 模拟评估（实际应该获取详细档案）
                    for profile in profiles:
                        # 简化评估 - 实际应该用浏览器获取完整档案
                        mock_text = f"{profile['name']} - {keyword} expert in {location}"
                        result = self.evaluator.evaluate(mock_text, profile["url"])

                        if result["match_score"] >= 0.7:
                            self.save_candidate(result)

                    # 延时避免触发限制
                    delay = random.uniform(5, 10)
                    await asyncio.sleep(delay)

            # 每轮报告进度
            print(f"\n📊 第 {round_num} 轮完成 - 当前高分候选人: {len(self.current_high_matches)}/{self.target_count}")

            # 每5轮保存汇总
            if round_num % 5 == 0:
                self.save_summary()

            # 如果进行多轮仍无进展，切换策略
            if round_num >= 10 and len(self.current_high_matches) < 5:
                print("\n⚠️  进展缓慢，建议:")
                print("   1. 使用 xray_campaign.py 生成搜索链接手动操作")
                print("   2. 考虑使用付费住宅代理")
                break

        # 最终结果
        self.save_summary()
        self.print_final_report()
        
        # ===== 刷新华人候选人整体报告 =====
        print("\n" + "=" * 70)
        print("🔄 正在刷新华人候选人整体报告...")
        print("=" * 70)
        try:
            import subprocess
            result = subprocess.run(
                ["python3", "scripts/generate_chinese_report.py"],
                cwd=str(Path(__file__).parent.parent),
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ 华人候选人整体报告已刷新!")
                print("📄 报告位置: CHINESE_TALENT_OVERALL_REPORT.md")
            else:
                print(f"⚠️ 报告刷新遇到问题")
        except Exception as e:
            print(f"⚠️ 报告刷新失败: {e}")
        # ==================================

    def save_candidate(self, candidate: Dict):
        """保存候选人"""
        self.current_high_matches.append(candidate)

        # 保存到文件
        name = candidate.get("evaluation", {}).get("basic_info", {}).get("name", "unknown")
        name = re.sub(r'[^\w]', '_', name).lower()
        timestamp = datetime.now().strftime("%H%M%S")

        today_dir = self.output_dir / datetime.now().strftime("%Y-%m-%d")
        today_dir.mkdir(exist_ok=True)

        filepath = today_dir / f"{name}_{timestamp}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(candidate, f, ensure_ascii=False, indent=2)

    def save_summary(self):
        """保存汇总报告"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_high_matches": len(self.current_high_matches),
            "chinese_high_matches": len(self.chinese_candidates),
            "target": self.target_count,
            "chinese_target": self.chinese_target,
            "progress_pct": round(len(self.current_high_matches) / self.target_count * 100, 1),
            "chinese_progress_pct": round(len(self.chinese_candidates) / self.chinese_target * 100, 1),
            "search_stats": self.searcher.stats if self.searcher else {},
            "evaluation_stats": self.evaluator.stats,
            "profiles": self.current_high_matches
        }

        summary_path = self.output_dir / datetime.now().strftime("%Y-%m-%d") / "summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"💾 汇总报告已保存: {summary_path}")

    def print_final_report(self):
        """打印最终报告"""
        print("\n" + "=" * 70)
        print("📊 最终报告")
        print("=" * 70)
        print(f"总目标: {self.target_count} 个高分候选人")
        print(f"华人目标: {self.chinese_target} 个华人候选人")
        print(f"达成: {len(self.current_high_matches)} 个 ({len(self.current_high_matches)/self.target_count*100:.1f}%)")
        print(f"华人达成: {len(self.chinese_candidates)} 个 ({len(self.chinese_candidates)/self.chinese_target*100:.1f}%)")
        print(f"搜索次数: {self.searcher.stats['searches'] if self.searcher else 0}")
        print(f"成功次数: {self.searcher.stats['success'] if self.searcher else 0}")
        print(f"评估人数: {self.evaluator.stats['evaluated']}")
        print("\n🏆 高分候选人列表:")
        for i, p in enumerate(self.current_high_matches[:10], 1):
            info = p.get("evaluation", {}).get("basic_info", {})
            is_cn = "🇨🇳" if p.get("is_chinese", False) else ""
            print(f"  {i}. {is_cn}{info.get('name', 'Unknown')} - 分数: {p.get('match_score', 0)}")


async def main():
    """主函数"""
    engine = TalentDiscoveryEngine()
    await engine.run()


if __name__ == "__main__":
    asyncio.run(main())
