"""
TalentIntel Phase 2 - Kimi Web Search 实现
使用Kimi内置的 $web_search 函数进行联网搜索

特性:
- 使用 Kimi builtin_function.$web_search
- 每次调用收费 ￥0.03
- 自动处理搜索和网页内容获取
- 返回结构化的搜索结果
"""

import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

# 尝试导入 openai 客户端
try:
    from openai import OpenAI
except ImportError:
    print("⚠️  openai 包未安装，请运行: pip install openai")
    raise


@dataclass
class KimiSearchResult:
    """Kimi搜索结果"""
    title: str
    url: str
    snippet: str
    source: str
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
        }


class KimiWebSearcher:
    """
    Kimi Web Search 客户端
    使用Kimi内置的 $web_search 函数
    """
    
    # 默认API Key (kimi-coding provider)
    DEFAULT_API_KEY = "sk-kimi-DCsw2VdvoK0hNurkl6r8NJo3Zsz5f6LQHH5nbXCwr32fBM7bZuvTUWaGPHi12hJj"
    DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"  # 使用Moonshot的base_url但用kimi-coding的key
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化Kimi Web Searcher
        
        Args:
            api_key: Kimi API Key，如果不提供则使用默认Key
            base_url: API Base URL
        """
        self.api_key = api_key or os.getenv("KIMI_API_KEY") or self.DEFAULT_API_KEY
        self.base_url = base_url or os.getenv("KIMI_BASE_URL") or self.DEFAULT_BASE_URL
        
        if not self.api_key:
            raise ValueError(
                "MOONSHOT_API_KEY 未设置。请设置环境变量或在初始化时提供。\n"
                "获取API Key: https://platform.moonshot.cn/"
            )
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # 搜索统计
        self.search_count = 0
        self.total_tokens = 0
    
    def search(
        self, 
        query: str, 
        count: int = 5,
        model: str = "kimi-k2.5"
    ) -> List[KimiSearchResult]:
        """
        执行联网搜索
        
        Args:
            query: 搜索查询
            count: 期望结果数量（实际结果由Kimi决定）
            model: 使用的模型，建议使用 kimi-k2.5 以支持长上下文
            
        Returns:
            List[KimiSearchResult]: 搜索结果列表
            
        Note:
            每次调用收费 ￥0.03
        """
        print(f"🔍 Kimi Web Search: {query}")
        
        # 定义 $web_search 工具
        tools = [
            {
                "type": "builtin_function",
                "function": {
                    "name": "$web_search"
                }
            }
        ]
        
        # 第一轮：让Kimi决定使用web_search
        messages = [
            {
                "role": "system",
                "content": "你是一个搜索助手。当需要获取最新信息时，请使用web_search工具。"
            },
            {
                "role": "user",
                "content": f"请搜索以下信息，返回前{count}条相关结果：\n\n{query}"
            }
        ]
        
        try:
            # 发送请求，启用工具调用
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                temperature=0.3,  # 低温度以获得更确定的结果
            )
            
            # 检查是否需要调用工具
            if response.choices[0].finish_reason == "tool_calls":
                # 获取工具调用信息
                tool_call = response.choices[0].message.tool_calls[0]
                
                # 获取消耗的tokens信息
                arguments = json.loads(tool_call.function.arguments)
                total_tokens = arguments.get("total_tokens", 0)
                self.total_tokens += total_tokens
                self.search_count += 1
                
                print(f"   📊 Tokens消耗: {total_tokens}")
                print(f"   💰 本次收费: ￥0.03")
                
                # 第二轮：将工具调用结果返回给Kimi
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "builtin_function",
                            "function": {
                                "name": "$web_search",
                                "arguments": tool_call.function.arguments
                            }
                        }
                    ]
                })
                
                # 添加工具返回结果（按照Kimi的要求，原封不动返回参数）
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_call.function.arguments
                })
                
                # 获取最终结果
                final_response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                )
                
                # 解析结果
                content = final_response.choices[0].message.content
                results = self._parse_search_results(content)
                
                print(f"   ✅ 找到 {len(results)} 条结果")
                return results
                
            else:
                # Kimi直接回答了，没有使用搜索
                print("   ⚠️  Kimi未使用搜索，直接回答了问题")
                return []
                
        except Exception as e:
            print(f"   ❌ 搜索失败: {e}")
            return []
    
    def _parse_search_results(self, content: str) -> List[KimiSearchResult]:
        """
        解析Kimi返回的搜索结果
        
        Kimi会以自然语言形式返回搜索结果，我们需要从中提取结构化信息
        """
        results = []
        
        # 尝试从内容中提取URL和标题
        import re
        
        # 匹配常见的URL模式
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, content)
        
        # 按行解析，尝试找到标题和描述的对应关系
        lines = content.split('\n')
        current_result = {}
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # 检测是否是标题（数字开头或特定标记）
            if re.match(r'^\d+[:\.\)]', line) or line.startswith('- ') or line.startswith('**'):
                # 保存之前的结果
                if current_result and 'url' in current_result:
                    results.append(KimiSearchResult(
                        title=current_result.get('title', 'Unknown'),
                        url=current_result['url'],
                        snippet=current_result.get('snippet', ''),
                        source=self._extract_domain(current_result['url'])
                    ))
                    current_result = {}
                
                # 提取标题
                title = re.sub(r'^\d+[:\.\)]\s*', '', line)
                title = re.sub(r'^[-\*]\s*', '', title)
                title = title.strip('*')
                current_result['title'] = title
            
            # 检测URL
            elif 'http' in line:
                url_match = re.search(url_pattern, line)
                if url_match:
                    current_result['url'] = url_match.group(0)
            
            # 其他行作为描述
            elif current_result and len(line) > 20:
                if 'snippet' not in current_result:
                    current_result['snippet'] = line
                else:
                    current_result['snippet'] += ' ' + line
        
        # 保存最后一个结果
        if current_result and 'url' in current_result:
            results.append(KimiSearchResult(
                title=current_result.get('title', 'Unknown'),
                url=current_result['url'],
                snippet=current_result.get('snippet', ''),
                source=self._extract_domain(current_result['url'])
            ))
        
        # 如果没有解析出结果，但整体有内容，创建一个通用结果
        if not results and content:
            # 尝试提取所有URL
            for url in urls[:5]:
                results.append(KimiSearchResult(
                    title="Search Result",
                    url=url,
                    snippet=content[:200] + "...",
                    source=self._extract_domain(url)
                ))
        
        return results
    
    def _extract_domain(self, url: str) -> str:
        """从URL提取域名"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except:
            return url
    
    def get_stats(self) -> Dict:
        """获取搜索统计"""
        return {
            "search_count": self.search_count,
            "total_tokens": self.total_tokens,
            "estimated_cost": self.search_count * 0.03,  # 每次￥0.03
        }
    
    def search_social_accounts(
        self, 
        name: str, 
        company: str,
        platforms: List[str] = None
    ) -> Dict[str, List[KimiSearchResult]]:
        """
        搜索社交媒体账号
        
        Args:
            name: 人名
            company: 公司名
            platforms: 平台列表，如 ['x.com', 'github.com', 'linkedin.com']
            
        Returns:
            各平台的搜索结果
        """
        if platforms is None:
            platforms = ['x.com', 'twitter.com', 'github.com', 'linkedin.com']
        
        results = {}
        
        for platform in platforms:
            query = f'"{name}" {company} site:{platform}'
            platform_results = self.search(query, count=5)
            
            if platform_results:
                # 过滤出个人主页（排除推文/帖子页面）
                profile_results = [
                    r for r in platform_results 
                    if not any(x in r.url for x in ['/status/', '/tweet/', '/issues/', '/blob/'])
                ]
                
                if platform in ['x.com', 'twitter.com']:
                    results['x'] = profile_results
                elif platform == 'github.com':
                    results['github'] = profile_results
                elif platform == 'linkedin.com':
                    results['linkedin'] = profile_results
        
        return results


# 便捷函数，类似之前的 web_search
def kimi_search(query: str, count: int = 5) -> List[Dict]:
    """
    使用Kimi进行联网搜索（便捷函数）
    
    Args:
        query: 搜索查询
        count: 结果数量
        
    Returns:
        搜索结果列表，每项包含 title, url, snippet, source
    """
    searcher = KimiWebSearcher()
    results = searcher.search(query, count)
    return [r.to_dict() for r in results]


# 测试代码
if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Kimi Web Search 测试")
    print("=" * 70)
    
    # 检查API Key
    if not os.getenv("MOONSHOT_API_KEY"):
        print("\n❌ 错误: MOONSHOT_API_KEY 环境变量未设置")
        print("\n请设置环境变量:")
        print("   export MOONSHOT_API_KEY='your-api-key'")
        print("\n或从代码中传入:")
        print("   searcher = KimiWebSearcher(api_key='your-key')")
        print("\n获取API Key: https://platform.moonshot.cn/")
        exit(1)
    
    # 创建搜索器
    searcher = KimiWebSearcher()
    
    # 测试搜索
    test_queries = [
        "Zhican Chen NVIDIA x.com twitter",
        "OpenClaw GitHub repository",
    ]
    
    for query in test_queries:
        print(f"\n🔍 测试搜索: {query}")
        print("-" * 70)
        
        results = searcher.search(query, count=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result.title}")
                print(f"   URL: {result.url}")
                print(f"   {result.snippet[:150]}...")
        else:
            print("   未找到结果")
    
    # 显示统计
    stats = searcher.get_stats()
    print("\n" + "=" * 70)
    print("📊 搜索统计")
    print("=" * 70)
    print(f"   搜索次数: {stats['search_count']}")
    print(f"   Tokens消耗: {stats['total_tokens']}")
    print(f"   预估费用: ￥{stats['estimated_cost']:.2f}")
