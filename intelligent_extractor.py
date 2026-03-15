"""
Intelligent Content Extractor
智能内容提取器 - 基于 LLM 和启发式规则

从网页中提取结构化数据，适用于人才信息、学术档案等
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json


class FieldType(Enum):
    """字段类型"""
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    URL = "url"
    DATE = "date"
    LIST = "list"
    BOOLEAN = "boolean"


@dataclass
class ExtractionSchema:
    """提取模式定义"""
    name: str
    base_selector: str  # CSS选择器
    fields: Dict[str, Dict[str, Any]]  # 字段定义

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "base_selector": self.base_selector,
            "fields": self.fields
        }


# 预设提取模式
TALENT_SCHEMAS = {
    "google_scholar": ExtractionSchema(
        name="Google Scholar Profile",
        base_selector="#gsc_prf_w",
        fields={
            "name": {
                "selector": "#gsc_prf_in .gsc_prf_fn",
                "type": FieldType.TEXT,
                "required": True
            },
            "affiliation": {
                "selector": ".gsc_prf_il",
                "type": FieldType.TEXT,
                "required": False
            },
            "interests": {
                "selector": ".gsc_prf_inta",
                "type": FieldType.LIST,
                "required": False
            },
            "citations": {
                "selector": ".gsc_rsb_std",
                "type": FieldType.NUMBER,
                "index": 0,  # 第一个匹配元素
                "required": False,
                "transform": "parse_number"
            },
            "h_index": {
                "selector": ".gsc_rsb_std",
                "type": FieldType.NUMBER,
                "index": 2,
                "required": False,
                "transform": "parse_number"
            },
            "i10_index": {
                "selector": ".gsc_rsb_std",
                "type": FieldType.NUMBER,
                "index": 4,
                "required": False,
                "transform": "parse_number"
            }
        }
    ),

    "github_profile": ExtractionSchema(
        name="GitHub Profile",
        base_selector=".js-profile-editable-area",
        fields={
            "username": {
                "selector": ".vcard-username",
                "type": FieldType.TEXT,
                "required": True
            },
            "fullname": {
                "selector": ".vcard-fullname",
                "type": FieldType.TEXT,
                "required": False
            },
            "bio": {
                "selector": ".p-note",
                "type": FieldType.TEXT,
                "required": False
            },
            "company": {
                "selector": "[itemprop='worksFor']",
                "type": FieldType.TEXT,
                "required": False
            },
            "location": {
                "selector": ".p-label",
                "type": FieldType.TEXT,
                "required": False
            },
            "email": {
                "selector": ".u-email",
                "type": FieldType.EMAIL,
                "required": False
            },
            "website": {
                "selector": ".u-url",
                "type": FieldType.URL,
                "required": False
            },
            "repositories": {
                "selector": ".Counter",
                "type": FieldType.NUMBER,
                "index": 0,
                "required": False,
                "transform": "parse_number"
            },
            "followers": {
                "selector": ".text-bold",
                "type": FieldType.NUMBER,
                "index": 0,
                "required": False,
                "transform": "parse_number"
            }
        }
    ),

    "linkedin_profile": ExtractionSchema(
        name="LinkedIn Profile",
        base_selector="main",
        fields={
            "name": {
                "selector": ".top-card-layout__title",
                "type": FieldType.TEXT,
                "required": True
            },
            "headline": {
                "selector": ".top-card-layout__headline",
                "type": FieldType.TEXT,
                "required": False
            },
            "company": {
                "selector": ".top-card-layout__first-subline",
                "type": FieldType.TEXT,
                "required": False
            },
            "location": {
                "selector": ".top-card-layout__second-subline",
                "type": FieldType.TEXT,
                "required": False
            },
            "about": {
                "selector": ".core-section-container__content",
                "type": FieldType.TEXT,
                "required": False
            }
        }
    ),

    "arxiv_author": ExtractionSchema(
        name="arXiv Author Profile",
        base_selector=".author-profile",
        fields={
            "name": {
                "selector": "h1",
                "type": FieldType.TEXT,
                "required": True
            },
            "affiliation": {
                "selector": ".author-affiliation",
                "type": FieldType.TEXT,
                "required": False
            },
            "interests": {
                "selector": ".author-tag",
                "type": FieldType.LIST,
                "required": False
            },
            "total_papers": {
                "selector": ".author-stats .stat-value",
                "type": FieldType.NUMBER,
                "index": 0,
                "required": False,
                "transform": "parse_number"
            },
            "recent_papers": {
                "selector": ".paper-title",
                "type": FieldType.LIST,
                "required": False
            },
            "homepage": {
                "selector": ".author-homepage a",
                "type": FieldType.URL,
                "required": False
            },
            "orcid": {
                "selector": ".author-orcid",
                "type": FieldType.TEXT,
                "required": False
            }
        }
    ),

    "arxiv_paper": ExtractionSchema(
        name="arXiv Paper",
        base_selector="#content-inner",
        fields={
            "title": {
                "selector": "h1.title",
                "type": FieldType.TEXT,
                "required": True
            },
            "authors": {
                "selector": ".authors .author a",
                "type": FieldType.LIST,
                "required": True
            },
            "abstract": {
                "selector": ".abstract",
                "type": FieldType.TEXT,
                "required": True
            },
            "arxiv_id": {
                "selector": ".arxivid",
                "type": FieldType.TEXT,
                "required": True
            },
            "submission_date": {
                "selector": ".dateline",
                "type": FieldType.DATE,
                "required": False,
                "transform": "parse_date"
            },
            "primary_category": {
                "selector": ".primary-subject",
                "type": FieldType.TEXT,
                "required": False
            },
            "categories": {
                "selector": ".subject .primary-subject, .subject span",
                "type": FieldType.LIST,
                "required": False
            },
            "pdf_url": {
                "selector": ".download-pdf",
                "type": FieldType.URL,
                "required": False
            },
            "comments": {
                "selector": ".comments",
                "type": FieldType.TEXT,
                "required": False
            }
        }
    ),

    "semanticscholar_author": ExtractionSchema(
        name="Semantic Scholar Author Profile",
        base_selector="[data-test-id='author-page']",
        fields={
            "name": {
                "selector": "h1.author-name",
                "type": FieldType.TEXT,
                "required": True
            },
            "affiliation": {
                "selector": ".author-affiliation",
                "type": FieldType.TEXT,
                "required": False
            },
            "homepage": {
                "selector": ".author-homepage",
                "type": FieldType.URL,
                "required": False
            },
            "citation_count": {
                "selector": ".citation-stat .stat-value",
                "type": FieldType.NUMBER,
                "index": 0,
                "required": False,
                "transform": "parse_number"
            },
            "h_index": {
                "selector": ".h-index-stat .stat-value",
                "type": FieldType.NUMBER,
                "required": False,
                "transform": "parse_number"
            },
            "paper_count": {
                "selector": ".paper-count-stat .stat-value",
                "type": FieldType.NUMBER,
                "required": False,
                "transform": "parse_number"
            },
            "research_fields": {
                "selector": ".research-field",
                "type": FieldType.LIST,
                "required": False
            },
            "top_papers": {
                "selector": ".paper-title",
                "type": FieldType.LIST,
                "required": False
            },
            "co_authors": {
                "selector": ".co-author-name",
                "type": FieldType.LIST,
                "required": False
            }
        }
    ),

    "semanticscholar_paper": ExtractionSchema(
        name="Semantic Scholar Paper",
        base_selector="[data-test-id='paper-details']",
        fields={
            "title": {
                "selector": "h1.paper-title",
                "type": FieldType.TEXT,
                "required": True
            },
            "authors": {
                "selector": ".author-list .author-name",
                "type": FieldType.LIST,
                "required": True
            },
            "abstract": {
                "selector": ".abstract",
                "type": FieldType.TEXT,
                "required": True
            },
            "venue": {
                "selector": ".venue",
                "type": FieldType.TEXT,
                "required": False
            },
            "year": {
                "selector": ".year",
                "type": FieldType.NUMBER,
                "required": False,
                "transform": "parse_number"
            },
            "citation_count": {
                "selector": ".citation-count",
                "type": FieldType.NUMBER,
                "required": False,
                "transform": "parse_number"
            },
            "reference_count": {
                "selector": ".reference-count",
                "type": FieldType.NUMBER,
                "required": False,
                "transform": "parse_number"
            },
            "influential_citations": {
                "selector": ".influential-citation-count",
                "type": FieldType.NUMBER,
                "required": False,
                "transform": "parse_number"
            },
            "fields_of_study": {
                "selector": ".field-of-study",
                "type": FieldType.LIST,
                "required": False
            },
            "pdf_url": {
                "selector": "[data-test-id='paper-pdf-link']",
                "type": FieldType.URL,
                "required": False
            }
        }
    )
}


# 常量定义
MAX_LLM_CONTENT_LENGTH = 8000


class IntelligentExtractor:
    """
    智能内容提取器

    支持:
    - CSS选择器提取
    - 正则表达式提取
    - LLM辅助提取
    """

    def __init__(self):
        self.schemas = TALENT_SCHEMAS

    async def extract_with_schema(self, page, schema: ExtractionSchema) -> Dict[str, Any]:
        """
        使用 Schema 提取结构化数据

        Args:
            page: Playwright Page 对象
            schema: 提取模式

        Returns:
            提取的数据
        """
        result = {"_schema": schema.name, "_extracted_at": None}

        try:
            # 等待基础元素
            await page.wait_for_selector(schema.base_selector, timeout=5000)

            # 提取每个字段
            for field_name, field_config in schema.fields.items():
                try:
                    value = await self._extract_field(page, field_config)
                    result[field_name] = value
                except Exception as e:
                    if field_config.get("required", False):
                        result[field_name] = None
                    else:
                        result[field_name] = None

            result["_success"] = True

        except Exception as e:
            result["_error"] = str(e)
            result["_success"] = False

        return result

    async def _extract_field(self, page, config: Dict) -> Any:
        """提取单个字段"""
        selector = config["selector"]
        field_type = config.get("type", FieldType.TEXT)
        index = config.get("index", 0)

        # 获取元素
        elements = await page.query_selector_all(selector)

        if not elements or len(elements) <= index:
            return None

        element = elements[index]

        # 根据类型提取
        if field_type == FieldType.LIST:
            # 提取列表
            values = []
            for el in elements:
                text = await el.inner_text()
                if text.strip():
                    values.append(text.strip())
            return values

        else:
            # 提取单个值
            value = await element.inner_text()
            value = value.strip()

            # 应用转换
            transform = config.get("transform")
            if transform == "parse_number":
                value = self._parse_number(value)
            elif transform == "parse_date":
                value = self._parse_date(value)

            return value

    def _parse_number(self, text: str) -> Optional[int]:
        """解析数字"""
        if not text:
            return None

        # 移除逗号和空格
        cleaned = re.sub(r'[\s,]', '', text)

        # 提取数字
        match = re.search(r'\d+', cleaned)
        if match:
            return int(match.group())

        return None

    def _parse_date(self, text: str) -> Optional[str]:
        """解析日期"""
        # 简化处理，实际可使用 dateparser
        patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',
            r'(\d{2})/(\d{2})/(\d{4})',
            r'(\d{4})年(\d{2})月(\d{2})日'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()

        return text

    async def extract_with_llm(self, page, prompt: str) -> Dict[str, Any]:
        """
        使用 LLM 辅助提取

        Args:
            page: Playwright Page 对象
            prompt: 提取指令

        Returns:
            LLM提取结果
        """
        # 获取页面内容
        content = await page.inner_text("body")

        # 截断内容（避免超出token限制）
        if len(content) > MAX_LLM_CONTENT_LENGTH:
            content = content[:MAX_LLM_CONTENT_LENGTH] + "\n[Content truncated...]"

        # 构建提取提示
        extraction_prompt = f"""
从以下网页内容中提取信息：

{prompt}

网页内容：
{content}

请以JSON格式返回提取结果，不要包含任何解释文字。
如果某个字段未找到，返回null。
"""

        # 这里可以调用LLM API
        # result = await call_llm(extraction_prompt)

        # 简化返回，实际实现需要LLM集成
        return {
            "_method": "llm_extraction",
            "_prompt": prompt,
            "_content_length": len(content),
            "_note": "LLM extraction requires LLM API integration"
        }

    def extract_with_regex(self, text: str, patterns: Dict[str, str]) -> Dict[str, Any]:
        """
        使用正则表达式提取

        Args:
            text: 原始文本
            patterns: {字段名: 正则表达式}

        Returns:
            提取结果
        """
        result = {}

        for field_name, pattern in patterns.items():
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    result[field_name] = match.group(1) if match.groups() else match.group()
                else:
                    result[field_name] = None
            except Exception as e:
                result[field_name] = None
                result[f"{field_name}_error"] = str(e)

        return result

    def create_custom_schema(self, name: str, base_selector: str,
                           fields: Dict[str, Dict]) -> ExtractionSchema:
        """创建自定义提取模式"""
        return ExtractionSchema(
            name=name,
            base_selector=base_selector,
            fields=fields
        )


# 辅助函数
def extract_emails(text: str) -> List[str]:
    """提取邮箱地址"""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(pattern, text)


def extract_urls(text: str) -> List[str]:
    """提取URL"""
    pattern = r'https?://[^\s\">)]+'
    return re.findall(pattern, text)


def extract_phone_numbers(text: str) -> List[str]:
    """提取电话号码（简化版）"""
    pattern = r'\+?[\d\s\-\(\)]{10,}'
    matches = re.findall(pattern, text)
    return [m.strip() for m in matches if len(m.strip()) >= 10]


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("Intelligent Content Extractor Test")
    print("=" * 60)

    extractor = IntelligentExtractor()

    # 测试正则提取
    test_text = """
    Contact: John Doe <john.doe@example.com>
    Website: https://johndoe.com
    Phone: +1 (555) 123-4567
    Citations: 1,234
    H-index: 45
    """

    print("\n1. Regex Extraction:")
    print(f"   Emails: {extract_emails(test_text)}")
    print(f"   URLs: {extract_urls(test_text)}")
    print(f"   Phones: {extract_phone_numbers(test_text)}")

    # 测试 Schema
    print("\n2. Available Schemas:")
    for name, schema in extractor.schemas.items():
        print(f"   - {name}: {schema.name}")
        print(f"     Fields: {list(schema.fields.keys())}")

    print("\n" + "=" * 60)
    print("Test Completed!")
    print("=" * 60)
