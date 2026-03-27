"""
TalentIntel Phase 2 PoC - 社交网络图谱构建与可视化
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple
from datetime import datetime
import json

@dataclass
class PersonNode:
    """人物节点"""
    id: str
    name: str
    platform: str  # linkedin, x, github
    company: str
    title: str
    is_target: bool = False  # 是否为目标候选人
    is_entry: bool = False   # 是否为入口点
    
    def to_cytoscape(self) -> Dict:
        """转换为 Cytoscape.js 格式"""
        return {
            "data": {
                "id": self.id,
                "name": self.name,
                "platform": self.platform,
                "company": self.company,
                "title": self.title,
                "is_target": self.is_target,
                "is_entry": self.is_entry,
            }
        }

@dataclass
class RelationshipEdge:
    """关系边"""
    id: str
    source: str
    target: str
    relation_type: str  # colleague, connected, follows, collaborated
    strength: float = 0.5  # 关系强度 0-1
    metadata: Dict = field(default_factory=dict)
    
    def to_cytoscape(self) -> Dict:
        """转换为 Cytoscape.js 格式"""
        return {
            "data": {
                "id": self.id,
                "source": self.source,
                "target": self.target,
                "relation_type": self.relation_type,
                "strength": self.strength,
                **self.metadata
            }
        }

class SocialGraphBuilder:
    """社交图谱构建器"""
    
    def __init__(self):
        self.nodes: Dict[str, PersonNode] = {}
        self.edges: Dict[str, RelationshipEdge] = {}
    
    def add_person(self, person: PersonNode):
        """添加人物节点"""
        self.nodes[person.id] = person
    
    def add_relationship(self, edge: RelationshipEdge):
        """添加关系边"""
        edge_id = f"{edge.source}_{edge.target}_{edge.relation_type}"
        edge.id = edge_id
        self.edges[edge_id] = edge
    
    def build_from_candidate(self, candidate_id: str, candidate_data: Dict):
        """以候选人为中心构建图谱"""
        
        # 1. 添加候选人节点（入口点）
        entry_node = PersonNode(
            id=candidate_id,
            name=candidate_data.get("name", "Unknown"),
            platform="linkedin",
            company=candidate_data.get("company", "Unknown"),
            title=candidate_data.get("title", "Unknown"),
            is_target=True,
            is_entry=True
        )
        self.add_person(entry_node)
        
        # 2. 添加同事（从同一公司推断）
        colleagues = candidate_data.get("colleagues", [])
        for i, colleague in enumerate(colleagues):
            col_id = f"col_{i}"
            col_node = PersonNode(
                id=col_id,
                name=colleague.get("name", f"Colleague {i}"),
                platform="linkedin",
                company=candidate_data.get("company"),
                title=colleague.get("title", "Unknown")
            )
            self.add_person(col_node)
            
            # 添加同事关系
            self.add_relationship(RelationshipEdge(
                id="",
                source=candidate_id,
                target=col_id,
                relation_type="colleague",
                strength=0.7,
                metadata={"company": candidate_data.get("company")}
            ))
        
        # 3. 添加 GitHub 连接（从共同项目推断）
        github_connections = candidate_data.get("github_connections", [])
        for i, conn in enumerate(github_connections):
            conn_id = f"gh_conn_{i}"
            conn_node = PersonNode(
                id=conn_id,
                name=conn.get("name", f"GitHub User {i}"),
                platform="github",
                company=conn.get("company", "Unknown"),
                title=conn.get("title", "Developer")
            )
            self.add_person(conn_node)
            
            self.add_relationship(RelationshipEdge(
                id="",
                source=candidate_id,
                target=conn_id,
                relation_type="collaborated",
                strength=0.5,
                metadata={"platform": "github"}
            ))
        
        # 4. 添加 X/Twitter 关注关系
        x_connections = candidate_data.get("x_connections", [])
        for i, conn in enumerate(x_connections):
            conn_id = f"x_conn_{i}"
            conn_node = PersonNode(
                id=conn_id,
                name=conn.get("name", f"X User {i}"),
                platform="x",
                company=conn.get("company", "Unknown"),
                title=conn.get("title", "Unknown")
            )
            self.add_person(conn_node)
            
            self.add_relationship(RelationshipEdge(
                id="",
                source=candidate_id,
                target=conn_id,
                relation_type="follows",
                strength=0.3,
                metadata={"platform": "x"}
            ))
        
        # 5. 发现二度人脉（同事的同事）
        self._expand_second_degree()
    
    def _expand_second_degree(self):
        """扩展二度人脉"""
        # 找到所有一度连接
        first_degree = set()
        for edge in self.edges.values():
            if edge.source in self.nodes and self.nodes[edge.source].is_entry:
                first_degree.add(edge.target)
        
        # 为一度连接添加虚拟连接（模拟他们之间的关系）
        first_degree_list = list(first_degree)
        for i, person1 in enumerate(first_degree_list):
            for person2 in first_degree_list[i+1:]:
                # 模拟两个一度连接之间也有关系
                if self.nodes[person1].company == self.nodes[person2].company:
                    self.add_relationship(RelationshipEdge(
                        id="",
                        source=person1,
                        target=person2,
                        relation_type="colleague",
                        strength=0.4,
                        metadata={"inferred": True}
                    ))
    
    def find_connection_paths(self, from_id: str, to_id: str, max_depth: int = 3) -> List[List[str]]:
        """查找两个节点之间的连接路径"""
        paths = []
        visited = set()
        
        def dfs(current: str, target: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            if current == target:
                paths.append(path.copy())
                return
            
            visited.add(current)
            
            # 找到所有相邻节点
            for edge in self.edges.values():
                if edge.source == current and edge.target not in visited:
                    path.append(edge.target)
                    dfs(edge.target, target, path, depth + 1)
                    path.pop()
                elif edge.target == current and edge.source not in visited:
                    path.append(edge.source)
                    dfs(edge.source, target, path, depth + 1)
                    path.pop()
            
            visited.remove(current)
        
        dfs(from_id, to_id, [from_id], 0)
        return paths
    
    def get_network_stats(self) -> Dict:
        """获取网络统计信息"""
        target_nodes = [n for n in self.nodes.values() if n.is_target]
        entry_nodes = [n for n in self.nodes.values() if n.is_entry]
        
        # 按平台统计
        platform_counts = {}
        for node in self.nodes.values():
            platform_counts[node.platform] = platform_counts.get(node.platform, 0) + 1
        
        # 按关系类型统计
        relation_counts = {}
        for edge in self.edges.values():
            relation_counts[edge.relation_type] = relation_counts.get(edge.relation_type, 0) + 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "target_nodes": len(target_nodes),
            "entry_nodes": len(entry_nodes),
            "platform_distribution": platform_counts,
            "relation_distribution": relation_counts,
            "average_connections": len(self.edges) / len(self.nodes) if self.nodes else 0,
        }
    
    def to_cytoscape_json(self) -> Dict:
        """导出为 Cytoscape.js 格式"""
        return {
            "nodes": [node.to_cytoscape() for node in self.nodes.values()],
            "edges": [edge.to_cytoscape() for edge in self.edges.values()]
        }
    
    def export_html_visualization(self, output_path: str):
        """导出为 HTML 可视化文件"""
        graph_data = self.to_cytoscape_json()
        
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TalentIntel - Social Graph Visualization</title>
    <script src="https://unpkg.com/cytoscape@3.26.0/dist/cytoscape.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
        }}
        #header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}
        #header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        #header p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
        }}
        #stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            padding: 15px;
            background: white;
            border-bottom: 1px solid #e0e0e0;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        #cy {{
            width: 100%;
            height: calc(100vh - 200px);
            background: white;
        }}
        #legend {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
            font-size: 12px;
        }}
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>🕸️ TalentIntel Social Graph</h1>
        <p>Candidate Network Visualization</p>
    </div>
    
    <div id="stats">
        <div class="stat-item">
            <div class="stat-value">{len(self.nodes)}</div>
            <div class="stat-label">Total People</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{len(self.edges)}</div>
            <div class="stat-label">Connections</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{len([n for n in self.nodes.values() if n.is_target])}</div>
            <div class="stat-label">Targets</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{len(set(n.platform for n in self.nodes.values()))}</div>
            <div class="stat-label">Platforms</div>
        </div>
    </div>
    
    <div id="cy"></div>
    
    <div id="legend">
        <div style="font-weight: bold; margin-bottom: 10px;">Platform</div>
        <div class="legend-item">
            <div class="legend-color" style="background: #0077b5;"></div>
            <span>LinkedIn</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #1da1f2;"></div>
            <span>X (Twitter)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #333;"></div>
            <span>GitHub</span>
        </div>
        <div style="margin-top: 15px; font-weight: bold;">Node Type</div>
        <div class="legend-item">
            <div class="legend-color" style="background: #e74c3c; border: 2px solid #c0392b;"></div>
            <span>Target Candidate</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #3498db;"></div>
            <span>Connection</span>
        </div>
    </div>

    <script>
        var cy = cytoscape({{
            container: document.getElementById('cy'),
            elements: {json.dumps(graph_data)},
            style: [
                {{
                    selector: 'node',
                    style: {{
                        'background-color': function(ele) {{
                            var platform = ele.data('platform');
                            if (platform === 'linkedin') return '#0077b5';
                            if (platform === 'x') return '#1da1f2';
                            if (platform === 'github') return '#333';
                            return '#95a5a6';
                        }},
                        'width': function(ele) {{
                            return ele.data('is_target') ? 50 : 30;
                        }},
                        'height': function(ele) {{
                            return ele.data('is_target') ? 50 : 30;
                        }},
                        'border-width': function(ele) {{
                            return ele.data('is_target') ? 4 : 1;
                        }},
                        'border-color': function(ele) {{
                            return ele.data('is_target') ? '#e74c3c' : '#fff';
                        }},
                        'label': 'data(name)',
                        'font-size': '10px',
                        'text-valign': 'bottom',
                        'text-halign': 'center',
                        'text-background-color': '#fff',
                        'text-background-opacity': 0.8,
                        'text-background-padding': '2px',
                        'color': '#333'
                    }}
                }},
                {{
                    selector: 'edge',
                    style: {{
                        'width': 'mapData(strength, 0, 1, 1, 4)',
                        'line-color': '#bdc3c7',
                        'target-arrow-color': '#bdc3c7',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'opacity': 0.7
                    }}
                }},
                {{
                    selector: 'edge[relation_type = "colleague"]',
                    style: {{
                        'line-color': '#27ae60',
                        'line-style': 'solid'
                    }}
                }},
                {{
                    selector: 'edge[relation_type = "collaborated"]',
                    style: {{
                        'line-color': '#8e44ad',
                        'line-style': 'dashed'
                    }}
                }},
                {{
                    selector: 'edge[relation_type = "follows"]',
                    style: {{
                        'line-color': '#3498db',
                        'line-style': 'dotted'
                    }}
                }}
            ],
            layout: {{
                name: 'cose',
                padding: 50,
                nodeRepulsion: 400000,
                edgeElasticity: 100,
                nestingFactor: 5,
                gravity: 80,
                numIter: 1000,
                initialTemp: 200,
                coolingFactor: 0.95,
                minTemp: 1.0
            }}
        }});
        
        // 点击节点显示详情
        cy.on('tap', 'node', function(evt) {{
            var node = evt.target;
            var data = node.data();
            alert('Name: ' + data.name + '\\n' +
                  'Platform: ' + data.platform + '\\n' +
                  'Company: ' + data.company + '\\n' +
                  'Title: ' + data.title);
        }});
    </script>
</body>
</html>'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ 图谱可视化已导出: {output_path}")


def build_demo_graph():
    """构建演示图谱"""
    builder = SocialGraphBuilder()
    
    # 模拟候选人数据
    candidate_data = {
        "name": "Zhican(West) Chen",
        "company": "NVIDIA",
        "title": "Senior Software Engineer",
        "colleagues": [
            {"name": "NVIDIA Engineer A", "title": "AI Researcher"},
            {"name": "NVIDIA Engineer B", "title": "Systems Engineer"},
            {"name": "NVIDIA Manager", "title": "Engineering Manager"},
        ],
        "github_connections": [
            {"name": "Wireless AI Contributor", "company": "Qualcomm", "title": "Researcher"},
            {"name": "Open Source Dev", "company": "Meta", "title": "Engineer"},
        ],
        "x_connections": [
            {"name": "Wireless Expert", "company": "Stanford", "title": "Professor"},
            {"name": "Tech Influencer", "company": "Unknown", "title": "Consultant"},
            {"name": "AI Researcher", "company": "Google", "title": "Scientist"},
        ]
    }
    
    # 构建图谱
    builder.build_from_candidate("zhican_chen", candidate_data)
    
    # 打印统计
    stats = builder.get_network_stats()
    print("\n📊 社交图谱统计:")
    print("-" * 40)
    print(f"  总节点数: {stats['total_nodes']}")
    print(f"  总连接数: {stats['total_edges']}")
    print(f"  目标节点: {stats['target_nodes']}")
    print(f"  平台分布: {stats['platform_distribution']}")
    print(f"  关系类型: {stats['relation_distribution']}")
    print(f"  平均连接度: {stats['average_connections']:.2f}")
    
    # 导出可视化
    output_path = "/Users/cooga/.openclaw/workspace/Project/TalentIntel/poc/social_graph.html"
    builder.export_html_visualization(output_path)
    
    return builder


if __name__ == "__main__":
    print("=" * 60)
    print("TalentIntel Phase 2 PoC - 社交图谱构建")
    print("=" * 60)
    
    builder = build_demo_graph()
    
    print("\n🔗 连接路径示例:")
    print("-" * 40)
    paths = builder.find_connection_paths("zhican_chen", "x_conn_0", max_depth=2)
    for i, path in enumerate(paths[:3]):
        print(f"  路径 {i+1}: {' → '.join(path)}")
    
    print("\n" + "=" * 60)
