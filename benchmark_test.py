"""
TalentIntel 全面检索效果测试

测试目标:
1. 对比不同数据源（Scholar/GitHub/arXiv/Semantic Scholar）的抓取效果
2. 评估反爬绕过能力
3. 测试缓存命中率
4. 验证 Schema 提取准确性
5. 测试 BM25 内容清洗效果
"""

import asyncio
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

from talent_intel_crawler import TalentIntelCrawler, TalentIntelSync
from smart_crawler import SmartCrawler, BM25ContentFilter
from intelligent_extractor import IntelligentExtractor, TALENT_SCHEMAS
from smart_cache import SmartCacheManager


@dataclass
class TestResult:
    """测试结果"""
    source: str
    url: str
    success: bool
    response_time: float
    data_quality: float  # 0-1
    fields_extracted: int
    fields_expected: int
    error: str = ""
    sample_data: Dict = None


class TalentIntelBenchmark:
    """TalentIntel 基准测试"""
    
    def __init__(self):
        self.crawler = TalentIntelCrawler()
        self.results: List[TestResult] = []
        
        # 测试用例 - 知名学者/开发者
        self.test_cases = {
            "google_scholar": [
                "https://scholar.google.com/citations?user=JicYPdAAAAAJ",  # Geoffrey Hinton
                "https://scholar.google.com/citations?user=DhfD8YYAAAAJ",  # Yann LeCun
            ],
            "github": [
                "https://github.com/torvalds",  # Linus Torvalds
                "https://github.com/karpathy",  # Andrej Karpathy
            ],
            "arxiv_author": [
                # arXiv 作者 ID 格式
                "https://arxiv.org/search/?searchtype=author&query=Hinton%2C+G+E",
            ],
            "arxiv_paper": [
                "https://arxiv.org/abs/2301.00027",
                "https://arxiv.org/abs/2301.00028",
            ],
            "semanticscholar_author": [
                "https://www.semanticscholar.org/author/Geoffrey-Hinton/1750128",
            ],
            "semanticscholar_paper": [
                "https://www.semanticscholar.org/paper/Attention-is-All-you-Need-Vaswani-Shazeer/204e3073870fae3d05bcbc2f6a8e263d9b72e776",
            ]
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("=" * 80)
        print(" TalentIntel 全面检索效果测试")
        print("=" * 80)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试目标数: {sum(len(urls) for urls in self.test_cases.values())}")
        print()
        
        # 1. 测试 BM25 内容清洗
        await self.test_bm25_filter()
        
        # 2. 测试缓存系统
        await self.test_cache_system()
        
        # 3. 测试各个数据源的抓取
        for source_type, urls in self.test_cases.items():
            await self.test_source(source_type, urls)
        
        # 4. 生成报告
        return self.generate_report()
    
    async def test_bm25_filter(self):
        """测试 BM25 内容清洗"""
        print("\n" + "-" * 80)
        print("[测试 1] BM25 智能内容清洗")
        print("-" * 80)
        
        bm25 = BM25ContentFilter()
        
        # 模拟网页内容块
        test_blocks = [
            {"text": "导航栏 Home About Contact Login", "tag": "nav", "class": "navbar"},
            {"text": "广告：特价服务器 99元/月", "tag": "div", "class": "ad-banner"},
            {"text": "Geoffrey Everest Hinton 是深度学习的先驱，他的研究兴趣包括机器学习、神经网络和人工智能。他在Google Scholar上有超过100万次引用。", "tag": "article", "class": "profile-content"},
            {"text": "© 2024 版权所有 隐私政策", "tag": "footer", "class": "footer"},
            {"text": "相关推荐：其他研究者", "tag": "aside", "class": "sidebar"},
            {"text": "发表论文：1. Deep Learning (2015) 2. ImageNet Classification (2012) 3. Backpropagation (1986)", "tag": "section", "class": "publications"},
        ]
        
        # 测试不同查询词的效果
        queries = ["deep learning", "machine learning", "neural networks", ""]
        
        for query in queries:
            start = time.time()
            result = bm25.extract_main_content(test_blocks, query=query)
            elapsed = time.time() - start
            
            print(f"\n查询词: '{query}' (耗时: {elapsed*1000:.2f}ms)")
            print(f"提取结果长度: {len(result)} 字符")
            print(f"提取内容预览: {result[:150]}...")
        
        print("\n✅ BM25 测试完成")
    
    async def test_cache_system(self):
        """测试缓存系统"""
        print("\n" + "-" * 80)
        print("[测试 2] 三层缓存系统")
        print("-" * 80)
        
        cache = SmartCacheManager()
        
        # 测试数据
        test_data = {"name": "Test User", "papers": 100, "citations": 5000}
        
        # L1 缓存测试
        print("\n1. L1 内存缓存测试:")
        cache.l1_memory.set("test_key", test_data, ttl=3600)
        l1_result = cache.l1_memory.get("test_key")
        print(f"   写入 -> 读取: {'✅ 成功' if l1_result else '❌ 失败'}")
        print(f"   L1 统计: {cache.l1_memory.stats()}")
        
        # L2 缓存测试
        print("\n2. L2 磁盘缓存测试:")
        cache.l2_disk.set("test_key_l2", test_data, ttl=3600)
        l2_result = cache.l2_disk.get("test_key_l2")
        print(f"   写入 -> 读取: {'✅ 成功' if l2_result else '❌ 失败'}")
        print(f"   L2 统计: {cache.l2_disk.stats()}")
        
        # 分层缓存测试
        print("\n3. 分层缓存测试:")
        # 清除 L1，保留 L2
        cache.l1_memory.delete("test_key_l2")
        tiered_result = cache.get("test_key_l2")  # 应该从 L2 读取并回填 L1
        print(f"   L1未命中 -> L2命中 -> 回填L1: {'✅ 成功' if tiered_result else '❌ 失败'}")
        print(f"   L1 现在有数据: {'✅ 是' if cache.l1_memory.get('test_key_l2') else '❌ 否'}")
        
        print("\n✅ 缓存系统测试完成")
    
    async def test_source(self, source_type: str, urls: List[str]):
        """测试特定数据源"""
        print("\n" + "-" * 80)
        print(f"[测试] {source_type.upper()}")
        print("-" * 80)
        
        for url in urls:
            result = await self.test_single_url(source_type, url)
            self.results.append(result)
    
    async def test_single_url(self, source_type: str, url: str) -> TestResult:
        """测试单个 URL"""
        print(f"\n测试: {url}")
        
        start_time = time.time()
        success = False
        error_msg = ""
        sample_data = {}
        fields_extracted = 0
        
        try:
            if source_type == "google_scholar":
                profile = await self.crawler.crawl_scholar_profile(url)
                if profile:
                    success = True
                    sample_data = {
                        "name": profile.name,
                        "citations": profile.raw_data.get("citations"),
                        "h_index": profile.raw_data.get("h_index")
                    }
                    fields_extracted = sum(1 for v in profile.raw_data.values() if v is not None)
                    print(f"  ✅ 成功: {profile.name}, Citations: {profile.raw_data.get('citations')}")
                else:
                    error_msg = "抓取失败或被封"
                    print(f"  ❌ 失败: {error_msg}")
                    
            elif source_type == "github":
                profile = await self.crawler.crawl_github_profile(url)
                if profile:
                    success = True
                    sample_data = {
                        "name": profile.name,
                        "username": profile.raw_data.get("username"),
                        "repos": profile.raw_data.get("repositories")
                    }
                    fields_extracted = sum(1 for v in profile.raw_data.values() if v is not None)
                    print(f"  ✅ 成功: {profile.name}, Repos: {profile.raw_data.get('repositories')}")
                else:
                    error_msg = "抓取失败"
                    print(f"  ❌ 失败: {error_msg}")
                    
            elif source_type == "arxiv_author":
                profile = await self.crawler.crawl_arxiv_author(url)
                if profile:
                    success = True
                    sample_data = {"name": profile.name}
                    fields_extracted = sum(1 for v in profile.raw_data.values() if v is not None)
                    print(f"  ✅ 成功: {profile.name}")
                else:
                    error_msg = "抓取失败"
                    print(f"  ❌ 失败: {error_msg}")
                    
            elif source_type == "arxiv_paper":
                paper = await self.crawler.crawl_arxiv_paper(url)
                if paper:
                    success = True
                    sample_data = {
                        "title": paper.get("title", "")[:50],
                        "authors": len(paper.get("authors", [])),
                        "arxiv_id": paper.get("arxiv_id")
                    }
                    fields_extracted = sum(1 for v in paper.values() if v is not None)
                    print(f"  ✅ 成功: {paper.get('title', '')[:50]}...")
                else:
                    error_msg = "抓取失败"
                    print(f"  ❌ 失败: {error_msg}")
                    
            elif source_type == "semanticscholar_author":
                profile = await self.crawler.crawl_semanticscholar_author(url)
                if profile:
                    success = True
                    sample_data = {
                        "name": profile.name,
                        "citations": profile.raw_data.get("citation_count"),
                        "h_index": profile.raw_data.get("h_index")
                    }
                    fields_extracted = sum(1 for v in profile.raw_data.values() if v is not None)
                    print(f"  ✅ 成功: {profile.name}, Citations: {profile.raw_data.get('citation_count')}")
                else:
                    error_msg = "抓取失败"
                    print(f"  ❌ 失败: {error_msg}")
                    
            elif source_type == "semanticscholar_paper":
                paper = await self.crawler.crawl_semanticscholar_paper(url)
                if paper:
                    success = True
                    sample_data = {
                        "title": paper.get("title", "")[:50],
                        "citations": paper.get("citation_count"),
                        "year": paper.get("year")
                    }
                    fields_extracted = sum(1 for v in paper.values() if v is not None)
                    print(f"  ✅ 成功: {paper.get('title', '')[:50]}...")
                else:
                    error_msg = "抓取失败"
                    print(f"  ❌ 失败: {error_msg}")
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ 异常: {error_msg}")
        
        elapsed = time.time() - start_time
        
        # 获取期望字段数
        schema_map = {
            "google_scholar": "google_scholar",
            "github": "github_profile",
            "arxiv_author": "arxiv_author",
            "arxiv_paper": "arxiv_paper",
            "semanticscholar_author": "semanticscholar_author",
            "semanticscholar_paper": "semanticscholar_paper"
        }
        schema_key = schema_map.get(source_type, "")
        fields_expected = len(TALENT_SCHEMAS.get(schema_key, {}).fields) if schema_key else 0
        
        # 计算数据质量
        data_quality = fields_extracted / fields_expected if fields_expected > 0 else 0
        
        return TestResult(
            source=source_type,
            url=url,
            success=success,
            response_time=elapsed,
            data_quality=data_quality,
            fields_extracted=fields_extracted,
            fields_expected=fields_expected,
            error=error_msg,
            sample_data=sample_data
        )
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        print("\n" + "=" * 80)
        print(" 测试结果汇总")
        print("=" * 80)
        
        # 按来源分组统计
        source_stats = {}
        for r in self.results:
            if r.source not in source_stats:
                source_stats[r.source] = {
                    "total": 0,
                    "success": 0,
                    "avg_response_time": 0,
                    "avg_data_quality": 0
                }
            source_stats[r.source]["total"] += 1
            if r.success:
                source_stats[r.source]["success"] += 1
                source_stats[r.source]["avg_response_time"] += r.response_time
                source_stats[r.source]["avg_data_quality"] += r.data_quality
        
        # 计算平均值
        for source, stats in source_stats.items():
            if stats["success"] > 0:
                stats["avg_response_time"] /= stats["success"]
                stats["avg_data_quality"] /= stats["success"]
        
        # 打印统计
        print("\n各数据源表现:")
        print(f"{'Source':<25} {'Success':<10} {'Avg Time':<12} {'Data Quality':<15}")
        print("-" * 80)
        
        total_tests = len(self.results)
        total_success = sum(1 for r in self.results if r.success)
        
        for source, stats in sorted(source_stats.items()):
            success_rate = f"{stats['success']}/{stats['total']} ({stats['success']/stats['total']*100:.1f}%)"
            avg_time = f"{stats['avg_response_time']:.2f}s"
            quality = f"{stats['avg_data_quality']*100:.1f}%"
            print(f"{source:<25} {success_rate:<10} {avg_time:<12} {quality:<15}")
        
        print("-" * 80)
        print(f"{'TOTAL':<25} {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        
        # 详细结果
        print("\n详细结果:")
        for r in self.results:
            status = "✅" if r.success else "❌"
            print(f"\n{status} {r.source}")
            print(f"   URL: {r.url}")
            print(f"   Time: {r.response_time:.2f}s")
            print(f"   Fields: {r.fields_extracted}/{r.fields_expected} ({r.data_quality*100:.1f}%)")
            if r.sample_data:
                print(f"   Sample: {r.sample_data}")
            if r.error:
                print(f"   Error: {r.error}")
        
        return {
            "total_tests": total_tests,
            "total_success": total_success,
            "success_rate": total_success / total_tests if total_tests > 0 else 0,
            "source_stats": source_stats,
            "detailed_results": [
                {
                    "source": r.source,
                    "url": r.url,
                    "success": r.success,
                    "response_time": r.response_time,
                    "data_quality": r.data_quality,
                    "error": r.error
                }
                for r in self.results
            ]
        }


async def run_benchmark():
    """运行基准测试"""
    benchmark = TalentIntelBenchmark()
    report = await benchmark.run_all_tests()
    return report


if __name__ == "__main__":
    report = asyncio.run(run_benchmark())
    
    print("\n" + "=" * 80)
    print(" 测试完成!")
    print("=" * 80)
    print(f"\n总体成功率: {report['success_rate']*100:.1f}%")
    print(f"通过测试: {report['total_success']}/{report['total_tests']}")
