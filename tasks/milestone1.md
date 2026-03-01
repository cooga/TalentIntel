# TalentIntel - Milestone 1 开发任务

## 任务目标
完成项目核心骨架开发，建立可运行的基础框架。

## 详细需求

### 1. 项目结构初始化
按照架构文档建立目录结构：
```
TalentIntel/
├── src/
│   ├── __init__.py
│   ├── models/          # 数据库模型
│   ├── collectors/      # 数据采集器
│   ├── core/           # 核心引擎
│   ├── cli/            # 命令行工具
│   └── config/         # 配置管理
├── tests/
├── config/
└── requirements.txt
```

### 2. 数据库模型 (SQLAlchemy)
实现以下核心表：
- `entities` - 人物实体表
- `platform_snapshots` - 平台快照表（差分存储）
- `events` - 事件日志表
- `signals` - 信号检测表
- `alerts` - 告警表

参考架构文档 4.2 节的 SQL 定义。

### 3. 实体管理模块
- `EntityService` 类
  - `create_entity()` - 创建目标人物
  - `get_entity()` - 获取详情
  - `list_entities()` - 列出所有目标
  - `delete_entity()` - 删除目标

### 4. GitHub 基础监控
- `GitHubCollector` 类
  - `fetch_profile()` - 获取 GitHub 用户信息
  - `fetch_events()` - 获取用户事件
  - `detect_changes()` - 检测与上次的差异
  - 使用 ETag 进行条件请求

### 5. CLI 工具
使用 Click 或 Typer 实现：
- `sentinel add <github_username>` - 添加监控目标
- `sentinel list` - 列出所有目标
- `sentinel status <id>` - 查看目标状态
- `sentinel fetch <id>` - 手动触发数据获取

### 6. 配置系统
- YAML 配置文件支持
- 环境变量覆盖
- 配置项：数据库路径、GitHub token、日志级别

## 技术要求
- Python 3.10+
- SQLAlchemy 2.0 (异步支持)
- aiohttp (异步 HTTP)
- click 或 typer (CLI)
- pydantic (数据验证)
- structlog (结构化日志)

## 验收标准
- [ ] 能够成功添加 GitHub 用户作为监控目标
- [ ] 能够手动触发数据获取并存储到数据库
- [ ] 能够检测到 Profile 数据的变化
- [ ] CLI 所有命令可用
- [ ] 代码通过基本类型检查 (mypy)

## 参考文档
- `docs/ARCHITECTURE.md` - 架构设计文档
- `docs/DEVELOPMENT_PLAN.md` - 开发计划

## 注意事项
1. 优先使用异步编程 (asyncio)
2. 数据库操作使用 SQLAlchemy AsyncSession
3. GitHub API 请求使用 ETag 避免重复请求
4. 配置敏感信息（如 GitHub token）从环境变量读取
5. 日志使用结构化输出，便于后续分析

## 输出
完成所有代码后，提交到 git 并推送。
