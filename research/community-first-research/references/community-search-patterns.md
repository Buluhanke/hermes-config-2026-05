# Community Search Patterns & Resources

## Hermes Official Communities

### Discord
- **Server**: https://discord.gg/hermes (invite link)
- **Key Channels**:
  - `#help` - 技术问题支持
  - `#skills` - 技能分享和讨论
  - `#plugins` - 插件开发
  - `#showcase` - 成功案例展示

### GitHub
- **Main Repo**: https://github.com/NousResearch/hermes-agent
- **Skill Hub**: https://github.com/topics/hermes-skill
- **Search Commands**:
  ```bash
  # 搜索Hermes技能
  site:github.com "hermes skill" "best practice"
  site:github.com "hermes-agent" "skill"
  
  # 搜索特定功能实现
  site:github.com "hermes-agent" "implementation"
  site:github.com "hermes" "workflow"
  ```

### Documentation
- **Official Docs**: https://hermes-agent.nousresearch.com/docs
- **Release Notes**: https://hermes-agent.nousresearch.com/docs/release-notes
- **API Reference**: https://hermes-agent.nousresearch.com/docs/api

## AI/Agent Ecosystem Communities

### Cocoloop Hub
- **URL**: https://cocoloop.ai/hub
- **Focus**: AI技能市场，预训练模型
- **Search**: "hermes" + [功能需求]

### Anthropic Communities
- **Discord**: https://discord.gg/anthropic
- **Forum**: https://forum.anthropic.com
- **Search**: "hermes" + "claude integration"

### Hugging Face
- **URL**: https://huggingface.co
- **Spaces**: 搜索 "hermes" 相关应用
- **Models**: 搜索兼容模型

## Technical Forums

### Stack Overflow
- **Search Commands**:
  ```bash
  site:stackoverflow.com "hermes" "setup"
  site:stackoverflow.com "hermes-agent" "configuration"
  site:stackoverflow.com "hermes" "skill installation"
  ```

### Reddit
- **r/hermes**: https://reddit.com/r/hermes
- **r/LocalLLM**: https://reddit.com/r/LocalLLM
- **r/MachineLearning**: https://reddit.com/r/MachineLearning

### V2EX
- **Node**: https://v2ex.com/go/hermes
- **Search**: "hermes" + [技术问题]

## Search Templates by Task Type

### Skill Installation
```bash
# 搜索最佳实践
site:github.com "hermes skill" [工具名] "best practice"
site:discord.com "hermes" [工具名] "setup guide"

# 检查官方技能
hermes skills list | grep [工具名]
hermes skills install github:[owner]/[repo]/path/to/skill
```

### Code Implementation
```bash
# 搜索现成实现
site:github.com "hermes" [功能需求] "implementation"
site:stackoverflow.com "hermes" [技术问题] "solution"

# 搜索插件/扩展
site:github.com "hermes plugin" [功能需求]
site:github.com "hermes extension" [功能需求]
```

### Configuration
```bash
# 搜索配置示例
site:hermes-agent.nousresearch.com/docs [配置项] "example"
site:github.com "hermes config" [配置项] "yaml"

# 检查默认配置
hermes config show
hermes config check
```

## Quality Assessment Checklist

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

## Quick Reference Commands

```bash
# 搜索Hermes技能
curl -s "https://api.github.com/search?q=hermes+skill+best+practice" | jq '.items[].html_url'

# 检查技能安装状态
ls -la ~/.hermes/skills/
hermes skills list

# 验证技能可用性
hermes skills check [skill_name]

# 查看技能文档
skill_view [skill_name]
```

## Community Engagement Tips

1. **Before Asking**: 先搜索，90%的问题已有解答
2. **When Searching**: 使用具体的技术关键词
3. **When Contributing**: 分享你的解决方案和经验
4. **When Stuck**: 在社区求助时提供详细信息
5. **When Succeeding**: 回馈解决方案，帮助他人