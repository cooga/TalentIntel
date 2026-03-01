# TalentIntel - 测试任务

## 测试目标
在独立 worktree 中测试功能，发现问题并反馈

## 测试 Worktree
路径: `/Users/cooga/.openclaw/workspace/Project/TalentIntel-test`
分支: `test-branch`

## 测试策略

### 1. 功能测试 (Functional Testing)
对每个功能进行手动测试：

```bash
# 1. 安装测试
pip install -e .

# 2. 初始化测试
sentinel init

# 3. 添加实体测试
sentinel add torvalds --name "Linus Torvalds" --priority 10
sentinel add <某个真实GitHub用户>

# 4. 列表功能测试
sentinel list
sentinel list --active-only

# 5. 状态查看测试
sentinel status <entity_id>

# 6. 数据获取测试（需要 GITHUB_TOKEN）
export SENTINEL_GITHUB_TOKEN=your_token
sentinel fetch <entity_id>

# 7. 更新测试
sentinel update <entity_id> --priority 8 --notes "测试更新"

# 8. 数据库验证
sqlite3 data/sentinel.db "SELECT * FROM entities;"
```

### 2. 问题记录
创建 `test-reports/YYYYMMDD.md` 记录发现的问题：

```markdown
## 测试日期: 2026-03-01

### 问题 #1
- **模块**: CLI/add
- **严重性**: 高/中/低
- **描述**: 
- **复现步骤**:
- **期望结果**:
- **实际结果**:
- **截图/日志**:

### 问题 #2
...

### 改进建议
...
```

### 3. 性能测试
- 数据库查询性能
- GitHub API 请求延迟
- 内存占用

### 4. 边界测试
- 空用户名
- 不存在的 GitHub 用户
- 超长输入
- 特殊字符

## 反馈机制
1. 发现问题 → 立即记录到 test-reports/
2. 每 15 分钟检查一次开发进度
3. 同步发现的问题给开发代理
4. 每日汇总测试报告

## 测试覆盖目标
- [ ] CLI 所有命令
- [ ] 数据库 CRUD
- [ ] GitHub API 调用
- [ ] 错误处理路径
