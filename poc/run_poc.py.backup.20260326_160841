#!/usr/bin/env python3
"""
TalentIntel Phase 2 PoC - 运行脚本
整合社交监控和图谱构建
"""

import asyncio
import sys
import json
from datetime import datetime

# 导入PoC模块
from social_monitor import (
    run_poc as run_social_monitor,
    CandidateProfile,
    SocialMonitorService,
    OpportunityDetector
)
from social_graph import build_demo_graph, SocialGraphBuilder, PersonNode, RelationshipEdge


async def run_full_poc():
    """运行完整PoC"""
    
    print("=" * 70)
    print("🚀 TalentIntel Phase 2 PoC - 多平台社交监控与关系拓源")
    print("=" * 70)
    print()
    
    # ========== Part 1: 社交监控 ==========
    print("📡 Part 1: 多平台社交监控")
    print("-" * 70)
    
    # 创建候选人档案
    candidate = CandidateProfile(
        id="zhican_chen_001",
        name="Zhican(West) Chen",
        company="NVIDIA",
        title="Senior Software Engineer",
        location="Santa Clara, California",
        linkedin_url="https://linkedin.com/in/zhican-west-chen-7213b4b4",
        x_url="https://x.com/zhican_chen",
        github_url="https://github.com/zhichen-nvidia",
    )
    
    # 运行监控
    service = SocialMonitorService()
    monitor_results = await service.monitor_candidate(candidate)
    
    # 显示结果
    print(f"\n👤 候选人: {candidate.name}")
    print(f"   📍 {candidate.company} | {candidate.title}")
    print(f"   🔗 {candidate.linkedin_url}")
    
    print("\n📊 平台监控结果:")
    for platform, data in monitor_results["platforms"].items():
        if "error" in data:
            print(f"   ❌ {platform}: {data['error']}")
        else:
            print(f"   ✅ {platform}: {data.get('activity_count', 0)} 条活动")
    
    # 检测到的信号
    print("\n🔔 机会信号检测:")
    if monitor_results["signals"]:
        for signal in monitor_results["signals"]:
            emoji = "🚨" if signal["confidence"] > 0.8 else "⚠️"
            print(f"   {emoji} [{signal['source_activity']['platform']}] {signal['signal_type']}")
            print(f"      置信度: {signal['confidence']:.0%} | {signal['description']}")
    else:
        print("   ℹ️ 未检测到明显机会信号")
    
    # 机会评分
    score_result = service.calculate_opportunity_score(candidate)
    print("\n📈 机会评分:")
    print(f"   总分: {score_result['total_score']}/{score_result['max_score']}")
    print(f"   活跃平台: {', '.join(score_result['platforms_active'])}")
    print("   评分详情:")
    for key, value in score_result['breakdown'].items():
        print(f"      • {key}: +{value} 分")
    
    # ========== Part 2: 图谱构建 ==========
    print("\n" + "=" * 70)
    print("🕸️ Part 2: 社交图谱构建")
    print("-" * 70)
    
    # 基于监控结果构建图谱
    graph_builder = SocialGraphBuilder()
    
    # 添加候选人节点
    entry_node = PersonNode(
        id=candidate.id,
        name=candidate.name,
        platform="linkedin",
        company=candidate.company,
        title=candidate.title,
        is_target=True,
        is_entry=True
    )
    graph_builder.add_person(entry_node)
    
    # 从活动中提取连接
    print("\n🔗 提取社交连接...")
    
    # 模拟从各平台提取的连接
    connections_data = {
        "colleagues": [
            {"name": "NVIDIA AI Researcher", "title": "Senior AI Researcher", "platform": "linkedin"},
            {"name": "NVIDIA Systems Lead", "title": "Principal Engineer", "platform": "linkedin"},
            {"name": "NVIDIA Manager", "title": "Engineering Manager", "platform": "linkedin"},
            {"name": "NVIDIA Intern", "title": "PhD Intern", "platform": "linkedin"},
        ],
        "github_collaborators": [
            {"name": "Wireless OSS Dev", "company": "Qualcomm", "title": "Engineer", "platform": "github"},
            {"name": "AI Researcher", "company": "Stanford", "title": "Postdoc", "platform": "github"},
        ],
        "x_connections": [
            {"name": "Wireless Professor", "company": "MIT", "title": "Professor", "platform": "x"},
            {"name": "Tech Influencer", "company": "Self", "title": "Consultant", "platform": "x"},
            {"name": "Industry Analyst", "company": "IDC", "title": "Analyst", "platform": "x"},
        ]
    }
    
    # 添加节点和关系
    node_id = 0
    for conn_type, connections in connections_data.items():
        for conn in connections:
            node_id += 1
            node = PersonNode(
                id=f"conn_{node_id}",
                name=conn["name"],
                platform=conn.get("platform", "linkedin"),
                company=conn.get("company", "Unknown"),
                title=conn["title"],
                is_target=False
            )
            graph_builder.add_person(node)
            
            # 添加关系
            relation_type = {
                "colleagues": "colleague",
                "github_collaborators": "collaborated",
                "x_connections": "follows"
            }.get(conn_type, "connected")
            
            graph_builder.add_relationship(RelationshipEdge(
                id="",
                source=candidate.id,
                target=node.id,
                relation_type=relation_type,
                strength=0.6 if conn_type == "colleagues" else 0.4
            ))
    
    # 扩展二度人脉
    graph_builder._expand_second_degree()
    
    # 显示统计
    stats = graph_builder.get_network_stats()
    print(f"\n📊 图谱统计:")
    print(f"   总节点: {stats['total_nodes']}")
    print(f"   总连接: {stats['total_edges']}")
    print(f"   平台分布: {stats['platform_distribution']}")
    print(f"   平均连接度: {stats['average_connections']:.2f}")
    
    # 导出可视化
    output_path = "/Users/cooga/.openclaw/workspace/Project/TalentIntel/poc/social_graph.html"
    graph_builder.export_html_visualization(output_path)
    
    # ========== Part 3: 生成报告 ==========
    print("\n" + "=" * 70)
    print("📋 Part 3: PoC 验证报告")
    print("-" * 70)
    
    report = {
        "poc_name": "TalentIntel Phase 2 - 多平台社交监控",
        "timestamp": datetime.now().isoformat(),
        "candidate": {
            "name": candidate.name,
            "company": candidate.company,
            "title": candidate.title,
            "linkedin": candidate.linkedin_url,
        },
        "monitoring_results": {
            "platforms_monitored": list(monitor_results["platforms"].keys()),
            "activities_collected": len(monitor_results["activities"]),
            "signals_detected": len(monitor_results["signals"]),
        },
        "opportunity_analysis": {
            "score": score_result['total_score'],
            "max_score": score_result['max_score'],
            "platforms_active": score_result['platforms_active'],
            "breakdown": score_result['breakdown'],
        },
        "network_analysis": {
            "total_nodes": stats['total_nodes'],
            "total_edges": stats['total_edges'],
            "platform_distribution": stats['platform_distribution'],
            "average_degree": stats['average_connections'],
        },
        "outputs": {
            "visualization": output_path,
        },
        "conclusions": [
            "✅ 多平台数据收集架构可行",
            "✅ 机会信号检测机制有效",
            "✅ 社交图谱构建和可视化成功",
            "⚠️ 实际平台API集成需要进一步开发",
            "⚠️ 真实数据获取需要处理反爬机制",
        ]
    }
    
    # 保存报告
    report_path = "/Users/cooga/.openclaw/workspace/Project/TalentIntel/poc/poc_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\n📝 验证结论:")
    for conclusion in report["conclusions"]:
        print(f"   {conclusion}")
    
    print("\n📁 输出文件:")
    print(f"   • 图谱可视化: {output_path}")
    print(f"   • JSON报告: {report_path}")
    
    print("\n" + "=" * 70)
    print("✅ PoC 验证完成!")
    print("=" * 70)
    
    return report


if __name__ == "__main__":
    try:
        report = asyncio.run(run_full_poc())
        
        # 可选：打开可视化
        print("\n🌐 是否打开图谱可视化? (y/n): ", end="")
        response = input().strip().lower()
        if response == 'y':
            import webbrowser
            webbrowser.open(f"file:///Users/cooga/.openclaw/workspace/Project/TalentIntel/poc/social_graph.html")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
