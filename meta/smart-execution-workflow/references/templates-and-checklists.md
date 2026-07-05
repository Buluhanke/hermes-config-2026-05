# Smart Execution Templates & Checklists

## Community Search Template

### Quick Search Script
```bash
#!/bin/bash
# smart-execution-search.sh - 执行社区搜索

echo "=== Smart Execution: Community Search ==="
echo "Task: $1"
echo "Time: $(date)"
echo ""

# 1. Hermes官方社区搜索
echo "🔍 Searching Hermes official communities..."
echo "GitHub:"
curl -s "https://api.github.com/search?q=hermes+$1+best+practice" | jq -r '.items[].html_url' | head -5

echo ""
echo "Discord:"
echo "Check #help and #skills channels for: $1"

echo ""
echo "Documentation:"
echo "https://hermes-agent.nousresearch.com/docs/search?q=$1"

# 2. AI/Agent生态社区搜索
echo ""
echo "🔍 AI/Agent ecosystem..."
echo "Cocoloop Hub: https://cocoloop.ai/hub/search?q=$1"
echo "Anthropic Forum: https://forum.anthropic.com/search?q=$1"
echo "Hugging Face: https://huggingface.co/models?search=$1"

# 3. 技术论坛搜索
echo ""
echo "🔍 Technical forums..."
echo "Stack Overflow:"
curl -s "https://api.stackexchange.com/2.3/search?intitle=$1&order=desc&sort=activity&site=stackoverflow" | jq -r '.items[].link' | head -3

echo ""
echo "Reddit:"
echo "https://reddit.com/search/?q=$1+hermes"

echo ""
echo "=== Search Complete ==="
echo "Next: Evaluate found solutions and execute immediately"
```

### Quality Assessment Checklist

```markdown
## Solution Quality Assessment

### ✅ High Quality Indicators
- [ ] **Star Count**: > 100 (社区验证)
- [ ] **Last Update**: < 6 months (维护活跃)
- [ ] **Documentation**: 完整且更新
- [ ] **Issue Resolution**: > 80% 解决率
- [ ] **Community Activity**: 定期提交和讨论
- [ ] **Test Coverage**: 有测试用例
- [ ] **CI/CD**: 自动化构建部署

### ❌ Red Flags
- [ ] **Abandoned**: > 1年无更新
- [ ] **High Issues**: > 10 open issues
- [ ] **Poor Docs**: 文档缺失或过时
- [ ] **No Tests**: 无测试覆盖
- [ ] **Dependencies**: 依赖版本冲突
- [ ] **Security**: 已知安全漏洞

### 📊 Scoring System
- 6-7项✅: **优秀方案** - 立即采用
- 4-5项✅: **良好方案** - 评估后采用
- 2-3项✅: **一般方案** - 需要改进或寻找替代
- 0-1项✅: **较差方案** - 按Ponytail决策梯子实现
```

## Task Execution Template

### Smart Execution Checklist
```markdown
## Smart Execution: [任务名称]
### 执行时间: $(date)

### 🔍 步骤1: 社区搜索 (5分钟)
- [ ] 搜索Hermes官方社区
- [ ] 搜索AI/Agent生态社区  
- [ ] 搜索技术论坛
- [ ] 评估方案质量

### 📊 步骤2: 方案评估 (2分钟)
- [ ] 质量评分: ___/7
- [ ] 推荐方案: ___
- [ ] 替代方案: ___

### ⚡ 步骤3: 立即执行 (不等待)
- [ ] 采用推荐方案/最小化实现
- [ ] 创建任务文件
- [ ] 执行第一步tool call

### ✅ 步骤4: 三重验证
- [ ] ARTIFACT 真实存在 (ls/grep)
- [ ] fact_store INSERT 一条记录
- [ ] 通知发送 exit_code=0

### 📝 步骤5: 记录经验
- [ ] 成功方案记录到memory
- [ ] 坑点和替代方案记录
- [ ] 可复用技巧记录
```

### Common Task Scenarios

#### Skill Installation
```bash
# 搜索模板
site:github.com "hermes skill" [工具名] "best practice"
site:discord.com "hermes" [工具名] "setup guide"

# 评估重点
- Star数 > 50
- 最近更新 < 3个月
- 有README和安装说明
- 有使用示例
```

#### Code Implementation
```bash
# 搜索模板
site:github.com "hermes" [功能需求] "implementation"
site:stackoverflow.com "hermes" [技术问题] "solution"

# 评估重点
- 代码简洁性
- 可维护性
- 测试覆盖
- 文档完整性
```

#### Configuration
```bash
# 搜索模板
site:hermes-agent.nousresearch.com/docs [配置项] "example"
site:github.com "hermes config" [配置项] "yaml"

# 评估重点
- 配置示例清晰
- 参数说明完整
- 有错误处理
- 性能考虑
```

## Quick Reference Commands

```bash
# 社区搜索
curl -s "https://api.github.com/search?q=hermes+[任务关键词]+best+practice" | jq '.items[].html_url'
curl -s "https://api.stackexchange.com/2.3/search?intitle=[任务关键词]&order=desc&sort=activity&site=stackoverflow" | jq '.items[].link'

# 技能检查
hermes skills list
hermes skills check [技能名]
skill_view [技能名]

# 配置检查
hermes config show
hermes config check

# 任务管理
ls -la ~/.hermes/tasks/
tail -f ~/.hermes/logs/gateway.log
```

## Success Metrics

### ✅ 成功标准
1. **搜索时间**: < 10分钟
2. **方案质量**: > 4项✅评估指标
3. **执行时间**: 找到方案后<1分钟开始执行
4. **验证通过**: 三重验证全部通过
5. **经验记录**: 任务完成后立即写入memory

### 📊 效率提升目标
- **减少重复造轮子**: 90%任务通过社区解决
- **提高执行速度**: 搜索+执行总时间<15分钟
- **降低错误率**: 通过社区验证的最佳实践
- **知识积累**: 每次任务都记录可复用经验