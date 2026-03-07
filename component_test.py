"""
TalentIntel 组件功能测试（简化版）

不依赖外部网络，测试核心组件功能
"""

import asyncio
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

# 导入各个组件
from smart_crawler import BM25ContentFilter, ProfileManager, CrawlProfile
from intelligent_extractor import IntelligentExtractor, TALENT_SCHEMAS, extract_emails, extract_urls
from smart_cache import SmartCacheManager, MemoryCache, DiskCache


@dataclass
class ComponentTestResult:
    """组件测试结果"""
    component: str
    test_name: str
    passed: bool
    details: str
    execution_time_ms: float


class TalentIntelComponentTest:
    """TalentIntel 组件测试"""
    
    def __init__(self):
        self.results: List[ComponentTestResult] = []
    
    async def run_all_tests(self):
        """运行所有组件测试"""
        print("=" * 80)
        print(" TalentIntel 组件功能测试报告")
        print("=" * 80)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. BM25 内容过滤测试
        await self.test_bm25_filter()
        
        # 2. Schema 定义测试
        await self.test_schemas()
        
        # 3. 缓存系统测试
        await self.test_cache_system()
        
        # 4. 正则提取工具测试
        await self.test_regex_tools()
        
        # 5. Profile 管理测试
        await self.test_profile_manager()
        
        # 生成报告
        self.generate_report()
    
    async def test_bm25_filter(self):
        """测试 BM25 内容过滤"""
        print("\n" + "-" * 80)
        print("[测试组 1] BM25 智能内容清洗")
        print("-" * 80)
        
        bm25 = BM25ContentFilter(k1=1.5, b=0.75)
        
        # 测试用例 1: 基本过滤
        start = time.time()
        test_blocks = [
            {"text": "导航栏 Home About Contact Login", "tag": "nav", "class": "navbar"},
            {"text": "广告：特价服务器 99元/月", "tag": "div", "class": "ad-banner"},
            {"text": "Geoffrey Everest Hinton 是深度学习的先驱，他的研究兴趣包括机器学习、神经网络和人工智能。他在Google Scholar上有超过100万次引用。", "tag": "article", "class": "profile-content"},
            {"text": "© 2024 版权所有 隐私政策", "tag": "footer", "class": "footer"},
            {"text": "相关推荐：其他研究者", "tag": "aside", "class": "sidebar"},
            {"text": "发表论文：1. Deep Learning (2015) 2. ImageNet Classification (2012) 3. Backpropagation (1986)", "tag": "section", "class": "publications"},
        ]
        
        result = bm25.extract_main_content(test_blocks, query="deep learning")
        elapsed = (time.time() - start) * 1000
        
        # 验证结果包含关键内容
        has_key_content = "深度学习" in result or "Deep Learning" in result
        no_nav = "导航栏" not in result
        no_ads = "广告" not in result
        
        passed = has_key_content and no_nav and no_ads
        
        self.results.append(ComponentTestResult(
            component="BM25ContentFilter",
            test_name="基本内容过滤",
            passed=passed,
            details=f"提取长度: {len(result)}字符, 含关键内容: {has_key_content}, 无导航: {no_nav}, 无广告: {no_ads}",
            execution_time_ms=elapsed
        ))
        
        print(f"  {'✅' if passed else '❌'} 基本内容过滤 - {elapsed:.2f}ms")
        print(f"     提取长度: {len(result)} 字符")
        print(f"     预览: {result[:100]}...")
        
        # 测试用例 2: 不同查询词效果对比
        queries = ["machine learning", "neural networks", ""]
        for query in queries:
            start = time.time()
            result = bm25.extract_main_content(test_blocks, query=query)
            elapsed = (time.time() - start) * 1000
            
            self.results.append(ComponentTestResult(
                component="BM25ContentFilter",
                test_name=f"查询词过滤: '{query}'",
                passed=len(result) > 0,
                details=f"查询'{query}'提取了 {len(result)} 字符",
                execution_time_ms=elapsed
            ))
            print(f"  ✅ 查询词 '{query}' - {elapsed:.2f}ms, 提取 {len(result)} 字符")
    
    async def test_schemas(self):
        """测试 Schema 定义"""
        print("\n" + "-" * 80)
        print("[测试组 2] Schema 定义完整性")
        print("-" * 80)
        
        extractor = IntelligentExtractor()
        
        expected_schemas = [
            ("google_scholar", 6),
            ("github_profile", 9),
            ("linkedin_profile", 5),
            ("arxiv_author", 7),
            ("arxiv_paper", 9),
            ("semanticscholar_author", 9),
            ("semanticscholar_paper", 10)
        ]
        
        for schema_name, min_fields in expected_schemas:
            start = time.time()
            schema = TALENT_SCHEMAS.get(schema_name)
            elapsed = (time.time() - start) * 1000
            
            if schema:
                field_count = len(schema.fields)
                passed = field_count >= min_fields
                
                self.results.append(ComponentTestResult(
                    component="IntelligentExtractor",
                    test_name=f"Schema: {schema_name}",
                    passed=passed,
                    details=f"字段数: {field_count}, 期望最少: {min_fields}, 基础选择器: {schema.base_selector}",
                    execution_time_ms=elapsed
                ))
                print(f"  {'✅' if passed else '❌'} {schema_name}: {field_count} 字段 - {elapsed:.2f}ms")
            else:
                self.results.append(ComponentTestResult(
                    component="IntelligentExtractor",
                    test_name=f"Schema: {schema_name}",
                    passed=False,
                    details="Schema 不存在",
                    execution_time_ms=elapsed
                ))
                print(f"  ❌ {schema_name}: Schema 不存在")
    
    async def test_cache_system(self):
        """测试缓存系统"""
        print("\n" + "-" * 80)
        print("[测试组 3] 三层缓存系统")
        print("-" * 80)
        
        cache = SmartCacheManager()
        test_data = {"name": "Test User", "papers": 100, "citations": 5000}
        
        # 测试 L1 内存缓存
        start = time.time()
        cache.l1_memory.set("l1_test", test_data, ttl=3600)
        l1_result = cache.l1_memory.get("l1_test")
        l1_elapsed = (time.time() - start) * 1000
        
        l1_passed = l1_result == test_data
        self.results.append(ComponentTestResult(
            component="SmartCacheManager",
            test_name="L1 内存缓存",
            passed=l1_passed,
            details=f"写入后读取成功: {l1_passed}, 统计: {cache.l1_memory.stats()}",
            execution_time_ms=l1_elapsed
        ))
        print(f"  {'✅' if l1_passed else '❌'} L1 内存缓存 - {l1_elapsed:.2f}ms")
        
        # 测试 L2 磁盘缓存
        start = time.time()
        cache.l2_disk.set("l2_test", test_data, ttl=3600)
        l2_result = cache.l2_disk.get("l2_test")
        l2_elapsed = (time.time() - start) * 1000
        
        l2_passed = l2_result == test_data
        self.results.append(ComponentTestResult(
            component="SmartCacheManager",
            test_name="L2 磁盘缓存",
            passed=l2_passed,
            details=f"写入后读取成功: {l2_passed}, 统计: {cache.l2_disk.stats()}",
            execution_time_ms=l2_elapsed
        ))
        print(f"  {'✅' if l2_passed else '❌'} L2 磁盘缓存 - {l2_elapsed:.2f}ms")
        
        # 测试分层缓存（L1未命中 -> L2命中 -> 回填L1）
        start = time.time()
        cache.l1_memory.delete("l2_test")  # 清除 L1
        tiered_result = cache.get("l2_test")  # 应该从 L2 读取
        tiered_elapsed = (time.time() - start) * 1000
        
        tiered_passed = tiered_result == test_data
        backfilled = cache.l1_memory.get("l2_test") is not None
        
        self.results.append(ComponentTestResult(
            component="SmartCacheManager",
            test_name="分层缓存 L1->L2",
            passed=tiered_passed and backfilled,
            details=f"L2命中: {tiered_passed}, 回填L1: {backfilled}",
            execution_time_ms=tiered_elapsed
        ))
        print(f"  {'✅' if tiered_passed and backfilled else '❌'} 分层缓存 - {tiered_elapsed:.2f}ms")
        print(f"     L2命中: {tiered_passed}, 回填L1: {backfilled}")
        
        # 测试缓存过期
        start = time.time()
        cache.l1_memory.set("expire_test", test_data, ttl=0)  # 立即过期
        import time as time_module
        time_module.sleep(0.1)  # 等待过期
        expired_result = cache.l1_memory.get("expire_test")
        expired_elapsed = (time.time() - start) * 1000
        
        expired_passed = expired_result is None
        self.results.append(ComponentTestResult(
            component="SmartCacheManager",
            test_name="缓存过期机制",
            passed=expired_passed,
            details=f"过期后返回None: {expired_passed}",
            execution_time_ms=expired_elapsed
        ))
        print(f"  {'✅' if expired_passed else '❌'} 缓存过期 - {expired_elapsed:.2f}ms")
    
    async def test_regex_tools(self):
        """测试正则提取工具"""
        print("\n" + "-" * 80)
        print("[测试组 4] 正则提取工具")
        print("-" * 80)
        
        test_text = """
        Contact: John Doe <john.doe@example.com>
        Backup: jane.smith@university.edu
        Website: https://johndoe.com, http://oldsite.org/page
        GitHub: https://github.com/johndoe
        Phone: +1 (555) 123-4567, +86 138-0000-0000
        Citations: 12,345
        H-index: 45
        """
        
        # 测试邮箱提取
        start = time.time()
        emails = extract_emails(test_text)
        elapsed = (time.time() - start) * 1000
        
        email_passed = len(emails) == 2 and "john.doe@example.com" in emails
        self.results.append(ComponentTestResult(
            component="RegexTools",
            test_name="邮箱提取",
            passed=email_passed,
            details=f"提取到 {len(emails)} 个邮箱: {emails}",
            execution_time_ms=elapsed
        ))
        print(f"  {'✅' if email_passed else '❌'} 邮箱提取 - {elapsed:.2f}ms: {emails}")
        
        # 测试 URL 提取
        start = time.time()
        urls = extract_urls(test_text)
        elapsed = (time.time() - start) * 1000
        
        url_passed = len(urls) >= 3
        self.results.append(ComponentTestResult(
            component="RegexTools",
            test_name="URL提取",
            passed=url_passed,
            details=f"提取到 {len(urls)} 个URL: {urls[:3]}",
            execution_time_ms=elapsed
        ))
        print(f"  {'✅' if url_passed else '❌'} URL提取 - {elapsed:.2f}ms: {len(urls)} 个")
        
        # 测试电话号码提取
        start = time.time()
        from intelligent_extractor import extract_phone_numbers
        phones = extract_phone_numbers(test_text)
        elapsed = (time.time() - start) * 1000
        
        phone_passed = len(phones) >= 2
        self.results.append(ComponentTestResult(
            component="RegexTools",
            test_name="电话号码提取",
            passed=phone_passed,
            details=f"提取到 {len(phones)} 个号码",
            execution_time_ms=elapsed
        ))
        print(f"  {'✅' if phone_passed else '❌'} 电话号码提取 - {elapsed:.2f}ms: {len(phones)} 个")
    
    async def test_profile_manager(self):
        """测试 Profile 管理"""
        print("\n" + "-" * 80)
        print("[测试组 5] Profile 管理")
        print("-" * 80)
        
        manager = ProfileManager()
        
        # 测试创建 Profile
        start = time.time()
        profile = CrawlProfile.create_default(name="test_profile")
        profile.user_agent = "Mozilla/5.0 (Test Browser)"
        profile.viewport = {"width": 1920, "height": 1080}
        elapsed = (time.time() - start) * 1000
        
        self.results.append(ComponentTestResult(
            component="ProfileManager",
            test_name="创建 Profile",
            passed=profile.name == "test_profile",
            details=f"Profile名: {profile.name}, UA: {profile.user_agent[:30]}...",
            execution_time_ms=elapsed
        ))
        print(f"  ✅ 创建 Profile - {elapsed:.2f}ms: {profile.name}")
        
        # 测试保存和加载
        start = time.time()
        manager.save_profile(profile)
        loaded_profile = manager.get_profile("test_profile")
        elapsed = (time.time() - start) * 1000
        
        save_load_passed = loaded_profile is not None and loaded_profile.name == "test_profile"
        self.results.append(ComponentTestResult(
            component="ProfileManager",
            test_name="保存/加载 Profile",
            passed=save_load_passed,
            details=f"加载成功: {save_load_passed}, 已保存profiles: {manager.list_profiles()}",
            execution_time_ms=elapsed
        ))
        print(f"  {'✅' if save_load_passed else '❌'} 保存/加载 Profile - {elapsed:.2f}ms")
        print(f"     已保存 profiles: {manager.list_profiles()}")
        
        # 清理测试数据
        import os
        test_profile_path = os.path.expanduser("~/.talentintel/profiles/test_profile.json")
        if os.path.exists(test_profile_path):
            os.remove(test_profile_path)
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 80)
        print(" 测试结果汇总")
        print("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        # 按组件分组
        component_stats = {}
        for r in self.results:
            if r.component not in component_stats:
                component_stats[r.component] = {"total": 0, "passed": 0}
            component_stats[r.component]["total"] += 1
            if r.passed:
                component_stats[r.component]["passed"] += 1
        
        # 打印组件统计
        print("\n各组件测试情况:")
        print(f"{'组件':<25} {'通过':<10} {'总计':<10} {'成功率':<10}")
        print("-" * 80)
        
        for component, stats in sorted(component_stats.items()):
            rate = f"{stats['passed']/stats['total']*100:.1f}%"
            print(f"{component:<25} {stats['passed']:<10} {stats['total']:<10} {rate:<10}")
        
        print("-" * 80)
        print(f"{'总计':<25} {passed_tests:<10} {total_tests:<10} {passed_tests/total_tests*100:.1f}%")
        
        # 打印失败项详情
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for r in self.results:
                if not r.passed:
                    print(f"  • {r.component} - {r.test_name}")
                    print(f"    详情: {r.details}")
        
        # 性能统计
        avg_time = sum(r.execution_time_ms for r in self.results) / len(self.results)
        max_time = max(r.execution_time_ms for r in self.results)
        min_time = min(r.execution_time_ms for r in self.results)
        
        print("\n性能统计:")
        print(f"  平均执行时间: {avg_time:.2f}ms")
        print(f"  最快: {min_time:.2f}ms")
        print(f"  最慢: {max_time:.2f}ms")
        
        # 生成评分
        score = passed_tests / total_tests * 100
        
        print("\n" + "=" * 80)
        if score >= 90:
            rating = "🌟 优秀"
        elif score >= 75:
            rating = "✅ 良好"
        elif score >= 60:
            rating = "⚠️ 及格"
        else:
            rating = "❌ 需要改进"
        
        print(f" 总体评分: {score:.1f}/100 - {rating}")
        print("=" * 80)
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "score": score,
            "rating": rating,
            "component_stats": component_stats,
            "avg_execution_time_ms": avg_time
        }


async def main():
    """运行测试"""
    test = TalentIntelComponentTest()
    report = await test.run_all_tests()
    return report


if __name__ == "__main__":
    report = asyncio.run(main())
    
    if report:
        print(f"\n测试完成! 最终评分: {report['score']:.1f}/100")
    else:
        print("\n测试完成!")
