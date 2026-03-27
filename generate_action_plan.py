#!/usr/bin/env python3
"""
TalentIntel 数字研究员 - 实战搜索方案
基于已有真实数据，制定系统化搜索策略
"""

from pathlib import Path
import json

print("=" * 80)
print("🎯 TalentIntel 数字研究员 - 实战搜索方案")
print("=" * 80)
print()

# 当前真实数据
print("📊 当前真实候选人状态:")
print()
print("Phase 1 (X-Ray搜索 - 3月4日):")
print("  1. Dr. Sarah Chen - Qualcomm - San Diego, CA")
print("  2. Prof. Michael Wang - Stanford - Stanford, CA")
print("  3. Dr. Kevin Zhang - MediaTek - Taiwan")
print("  4. Dr. Hao Chen - Alibaba DAMO - Hangzhou")
print("  5. Dr. Mei Lin - NTU Singapore - Singapore")
print("  6. Dr. Xiaoli Ma - Georgia Tech - Atlanta, GA")
print()
print("Phase 2 (LinkedIn浏览 - 3月20日):")
print("  7. Wei C. - NVIDIA - San Jose, CA ⭐")
print("  8. Jenny Chu - SpaceX - Hawthorne, CA ⭐")
print("  9. Wai San Wong - Qualcomm - San Diego, CA ⭐")
print("  10. Yaxiong Xie - UB - Buffalo, NY")
print("  11. Xianbin Wang - Western U - London, Canada")
print()
print("=" * 80)
print("🎯 推荐搜索策略")
print("=" * 80)
print()

strategies = """
【策略1】相似职位扩展搜索
基于已确认的候选人，搜索同公司相似职位:

• NVIDIA San Jose:
  - Systems Software Engineer (Wei C.的职位)
  - 搜索: site:linkedin.com/in ("NVIDIA") ("San Jose") ("engineer" OR "scientist")
  
• Qualcomm San Diego:
  - Principal Engineer (Wai San Wong的职位)
  - 搜索: site:linkedin.com/in ("Qualcomm") ("San Diego") ("engineer" OR "scientist")

• SpaceX Hawthorne:
  - Starlink Engineer (Jenny Chu的职位)
  - 搜索: site:linkedin.com/in ("SpaceX") ("Hawthorne") ("engineer")

【策略2】学术大佬学生网络
基于已确认的教授，搜索其学生/合作者:

• Prof. Michael Wang (Stanford) 的学生
  - 搜索: Google Scholar 查看其论文合作者
  - 筛选: 刚毕业或即将毕业的PhD

• Dr. Xiaoli Ma (Georgia Tech) 的学生
  - 搜索: 同样方法

• Yaxiong Xie (UB) - 前Princeton Postdoc
  - 搜索: Princeton 无线通信实验室其他成员

【策略3】会议/论文作者挖掘
搜索顶级会议中华人作者的LinkedIn:

• 会议: ICC, Globecom, MobiCom, INFOCOM, NeurIPS, ICML
• 关键词: wireless + machine learning
• 方法: 下载论文PDF → 查看作者单位 → LinkedIn搜索

【策略4】GitHub交叉验证
搜索同时有AI+无线项目的华人开发者:

• 搜索: site:github.com ("wireless" OR "5G") ("machine learning" OR "deep learning")
• 筛选: 有LinkedIn链接的profile
• 验证: 查看LinkedIn确认工作单位

【策略5】公司校友网络
通过已知候选人的前雇主挖掘:

• Wei C.: 前Samsung/Tesla/Huawei → 搜索这些公司的现员工
• Wai San Wong: 可能在Qualcomm有团队 → 搜索同组其他华人
"""

print(strategies)

print("=" * 80)
print("🚀 立即可执行的行动")
print("=" * 80)
print()

actions = """
【今天可完成】

1. 验证现有11位候选人 LinkedIn 档案 (30分钟)
   - 逐个访问 linkedin.com/in/xxx
   - 确认档案存在且信息匹配
   - 记录是否有邮箱/联系方式

2. 搜索3位高优先级候选人的同事 (1小时)
   - NVIDIA San Jose office 其他华人工程师
   - Qualcomm San Diego 6G团队其他成员
   - SpaceX Starlink 团队其他华人

3. Google Scholar 搜索3位教授的学生 (1小时)
   - Michael Wang (Stanford)
   - Xiaoli Ma (Georgia Tech)
   - 筛选即将毕业的PhD学生

【本周可完成】

4. 系统执行X-Ray搜索 (每天30分钟)
   - 每天尝试1-2个搜索组合
   - 记录发现的候选人
   - 人工验证后入库

5. 建立跟踪系统
   - 设置 Google Alerts 监控目标公司+职位
   - 关注 IEEE Xplore 新论文华人作者
"""

print(actions)

print("=" * 80)
print("💡 当前最佳搜索组合 (复制到Google)")
print("=" * 80)
print()

searches = [
    ("NVIDIA San Jose 华人工程师", 'site:linkedin.com/in ("NVIDIA") ("San Jose") ("engineer" OR "scientist")'),
    ("Qualcomm San Diego 华人工程师", 'site:linkedin.com/in ("Qualcomm") ("San Diego") ("engineer" OR "researcher")'),
    ("SpaceX 华人工程师", 'site:linkedin.com/in ("SpaceX") ("engineer" OR "scientist") ("Starlink" OR "wireless")'),
    ("Google 无线AI华人", 'site:linkedin.com/in ("Google") ("wireless" OR "5G" OR "communication") ("AI" OR "machine learning")'),
]

for name, query in searches:
    print(f"【{name}】")
    print(f"  {query}")
    print()

# 保存为文件
output_dir = Path("data/xray_searches")
output_dir.mkdir(parents=True, exist_ok=True)

with open(output_dir / "action_plan_20260322.md", 'w') as f:
    f.write("# TalentIntel 实战搜索方案\n\n")
    f.write(strategies)
    f.write("\n\n")
    f.write(actions)
    f.write("\n\n## 推荐搜索组合\n\n")
    for name, query in searches:
        f.write(f"### {name}\n```\n{query}\n```\n\n")

print(f"✅ 方案已保存: data/xray_searches/action_plan_20260322.md")
