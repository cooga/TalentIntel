# TalentIntel - 代码审查任务

## 审查目标
代码质量监控、问题收集、经验总结

## 审查 Worktree
路径: `/Users/cooga/.openclaw/workspace/Project/TalentIntel`
分支: `main` (作为参考基准)

## 审查维度

### 1. 代码质量检查
```bash
# 类型检查
mypy src/

# 代码风格
ruff check src/
ruff format --check src/

# 复杂度检查
radon cc src/ -a
```

### 2. 架构一致性审查
对照 `docs/ARCHITECTURE.md` 检查：
- 是否遵循分层架构
- 模块依赖是否正确
- 接口设计是否一致

### 3. 问题收集模板

```markdown
## 审查报告 - 2026-03-01

### 🔴 严重问题 (Blockers)
| # | 位置 | 问题 | 建议 |
|---|------|------|------|
| 1 | | | |

### 🟡 改进建议 (Suggestions)
| # | 位置 | 当前 | 建议 |
|---|------|------|------|
| 1 | | | |

### 🟢 经验总结 (Learnings)
1. 
2. 
3. 
```

### 4. 最佳实践记录
创建 `docs/BEST_PRACTICES.md`：
- 发现的好的设计模式
- 避免的坑
- 工具使用技巧

## 反馈机制
1. 实时发现问题 → 写入审查报告
2. 每 30 分钟汇总一次
3. 将问题分类反馈给开发代理
4. 记录到项目知识库

## 输出
- `reviews/review-YYYYMMDD.md` - 详细审查报告
- `docs/BEST_PRACTICES.md` - 最佳实践文档
- `docs/LESSONS_LEARNED.md` - 经验教训
