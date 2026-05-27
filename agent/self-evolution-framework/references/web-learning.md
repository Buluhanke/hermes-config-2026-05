# 联网学习路径（外部信息获取）

## 核心理念

联网学习是自我进化的氧气供给——信息是外部输入，经验积累是内部沉淀，两者缺一不可。

---

## 联网学习路径（按实用性排序）

### 1. 实时搜索（RAG / 联网问答）⭐ 最常用

**工具：** Exa（语义/英文）、SearXNG（中文/学术/代码）

**执行方式：**
```python
# 在 agent 运行时用 web_search 工具
web_search(query, limit=5)

# execute_code 环境中不可用，必须在 agent 对话中调用
```

**触发场景：** 事实类问题、供应商查询、价格行情、政策动态

---

### 2. Deep Research（复杂调研）

**触发场景：** 竞品分析、供应商尽职调查、行业报告

**流程：** 搜索 → 提取 → 再搜 → 再提炼 → 综合报告

**执行：** 多轮 web_search + web_extract 配合，结果写 Obsidian

---

### 3. RSS 监控订阅

**状态：** blogwatcher CLI 尚未安装，待配置

**目标订阅源：**
- GitHub Trending（AI/开发工具）
- Arxiv（学术论文）
- 行业媒体（电商/物流/包装）

**安装后配置：**
```bash
blogwatcher --help  # 验证安装
# 配置订阅源 → n8n 工作流定时抓取 → AI 提炼 → Obsidian
```

---

### 4. MCP 自动抓取

**已装能力：** mcp-chrome-stdio（浏览器自动化）

**场景：** 自动抓取供应商主页、批量采集竞品价格

---

### 5. 论文/Arxiv 追踪

**已跑通：** GitHub Hermes Agent 巡检（cron job，every 90m）

**扩展方向：** AI/电商/供应链 Arxiv 关键词追踪

---

## 知识更新闭环

```
信息源（搜索/RSS/MCP）
    ↓
过滤 + 提炼 + 去重
    ↓
有价值 → 写 Obsidian（~/Obsidian/迅龙贸易/ai-research/）
        ↓
无价值 → 丢弃
    ↓
定期回顾 → 合并 / 更新 / 删除
```

---

## 执行发现

- `hermes_tools` 在 execute_code 中不可用，只能在 agent 运行时通过内置 web_search 调用
- blogwatcher 未安装，需要时先 `which blogwatcher` 验证
- 搜索结果写 Obsidian 时用 `ai-research/` 目录，与每日日志分开