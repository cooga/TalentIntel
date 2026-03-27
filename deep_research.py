#!/usr/bin/env python3
"""
TalentIntel 候选人深入调研工具
系统化调研已发现候选人的详细背景
"""
import json
from datetime import datetime
from pathlib import Path

print("=" * 80)
print("🔍 TalentIntel 候选人深入调研")
print("=" * 80)
print()

# 读取当前人才库
active_file = Path('data/active/candidates.json')
with open(active_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

candidates = data.get('candidates', [])

print(f"📊 当前人才库: {len(candidates)} 人")
print()

# 按公司分组
by_company = {}
for c in candidates:
    company = c.get('company', 'Unknown')
    if company not in by_company:
        by_company[company] = []
    by_company[company].append(c)

print("=" * 80)
print("📁 候选人分布")
print("=" * 80)
print()

for company, members in sorted(by_company.items(), key=lambda x: -len(x[1])):
    print(f"【{company}】: {len(members)} 人")
    for m in members:
        verified = "✅" if m.get('verified') == 'done' else "⬜"
        print(f"  {verified} {m.get('name', 'Unknown')}")
    print()

# 生成调研优先级
print("=" * 80)
print("🎯 调研优先级建议")
print("=" * 80)
print()

# P0: 大厂高级职位
p0_candidates = [c for c in candidates if 
    any(x in c.get('title', '').lower() for x in ['svp', 'vp', 'director', 'principal', 'senior staff']) 
    and any(x in c.get('company', '') for x in ['NVIDIA', 'Qualcomm', 'SpaceX', 'Google', 'Meta', 'Apple'])]

# P1: 工程师级别
p1_candidates = [c for c in candidates if 
    any(x in c.get('title', '').lower() for x in ['engineer', 'scientist', 'researcher'])
    and c not in p0_candidates]

# P2: 学术界
p2_candidates = [c for c in candidates if 
    any(x in c.get('company', '') for x in ['University', 'Stanford', 'Georgia Tech', 'NTU', 'Buffalo', 'Western'])]

print(f"P0 (高管/高级别): {len(p0_candidates)} 人")
for c in p0_candidates:
    print(f"  • {c['name']} - {c['title']} @ {c['company']}")
print()

print(f"P1 (工程师/研究员): {len(p1_candidates)} 人")
for c in p1_candidates[:5]:
    print(f"  • {c['name']} - {c['title']} @ {c['company']}")
if len(p1_candidates) > 5:
    print(f"  ... 还有 {len(p1_candidates)-5} 人")
print()

print(f"P2 (学术界): {len(p2_candidates)} 人")
for c in p2_candidates:
    print(f"  • {c['name']} - {c['title']} @ {c['company']}")
print()

# 生成调研模板
print("=" * 80)
print("📝 深入调研清单")
print("=" * 80)
print()

checklist = """
对于每位候选人，需要调研:

□ 1. LinkedIn档案验证
   - 访问LinkedIn链接确认档案存在
   - 核实职位、公司、地点信息
   - 查看工作经历完整度

□ 2. 技术背景评估
   - AI/机器学习经验年限
   - 无线通信/5G/6G相关项目
   - 发表论文/专利情况
   - GitHub/技术博客

□ 3. 教育背景
   - 最高学历 (PhD/Master/Bachelor)
   - 毕业院校 (Top学校优先)
   - 专业方向 (CS/EE/通信)

□ 4. 职业轨迹
   - 当前公司任职时长
   - 过往工作经历 (大厂背景)
   - 晋升速度 ( Senior → Staff → Principal)

□ 5. 联系方式获取
   - LinkedIn私信
   - 邮箱猜测 (firstname.lastname@company.com)
   - 学术邮箱 (如果是教授)
   - 共同联系人推荐

□ 6. 匹配度评分 (1-10)
   - AI技术深度: _/10
   - 无线通信背景: _/10
   - 职业级别: _/10
   - 可接触性: _/10
   - 总体匹配度: _/10

□ 7. 优先级定级
   - P0 (立即联系): 高管/稀缺人才
   - P1 (重点跟进): 高级工程师/研究员
   - P2 (保持关注): 学术界/潜在人才

□ 8. 备注记录
   - 特殊技能/成就
   - 职业兴趣/跳槽可能性
   - 推荐联系方式
"""

print(checklist)

# 生成调研模板文件
template = """# 候选人深入调研报告

## 基本信息
- **姓名**: 
- **LinkedIn**: 
- **公司**: 
- **职位**: 
- **地点**: 
- **调研日期**: 

## 档案验证
- [ ] LinkedIn档案可访问
- [ ] 信息匹配度: ____%

## 技术背景
- **AI/ML经验年限**: 
- **无线通信经验**: 
- **专业技能**: 
- **发表论文/专利**: 

## 教育背景
- **最高学历**: 
- **毕业院校**: 
- **专业**: 

## 职业轨迹
- **当前公司**:  (入职年份: )
- **过往经历**: 
- **晋升速度**: 

## 联系方式
- **LinkedIn**: 
- **邮箱猜测**: 
- **共同联系人**: 

## 匹配度评分
- AI技术深度: _/10
- 无线通信背景: _/10
- 职业级别: _/10
- 可接触性: _/10
- **总体匹配度**: _/10

## 优先级
- [ ] P0 (立即联系)
- [ ] P1 (重点跟进)
- [ ] P2 (保持关注)

## 备注
- 
- 
- 

---
*调研员: Kobe*
*日期: """

output_dir = Path('data/research')
output_dir.mkdir(parents=True, exist_ok=True)

with open(output_dir / 'candidate_research_template.md', 'w', encoding='utf-8') as f:
    f.write(template)

print(f"✅ 调研模板已保存: {output_dir}/candidate_research_template.md")
print()

print("=" * 80)
print("🚀 建议调研顺序")
print("=" * 80)
print()
print("第一批 (今天完成 3-5人):")
for i, c in enumerate(p0_candidates[:3], 1):
    print(f"{i}. {c['name']} ({c['company']})")
print()
print("第二批 (本周完成):")
for i, c in enumerate(p1_candidates[:5], 1):
    print(f"{i}. {c['name']} ({c['company']})")
print()
print("=" * 80)
