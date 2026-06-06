---
name: model-decoupling
description: 用户对"模型"这件事的硬隔离规则 — 以后不要管任何模型相关的事（主模型、fallback、API key、custom_providers），唯一例外是 Ollama 本地模型。任何涉及模型的话题、配置、决策、评估 0 思考直接停手。
category: agent-behavior
triggers:
  - 模型
  - 主模型
  - fallback
  - API key
  - custom_providers
  - 切换模型
  - 模型挂了
  - 模型路由
  - NVIDIA
  - OpenRouter
  - V2enby
  - MiniMax
  - aicodee
  - 配置模型
  - 改模型
  - 切模
  - model=
  - api_key=
  - provider=
  - base_url=
  - 重新来一遍（如果上下文有模型）
---

# 用户当面拍板的硬规则（2026-06-05 14:50）

> **以后不要管模型的事。**
> **包括**：① 我自己的配置 / 代码 / 脚本 / 记忆 — **不强制绑定任何模型**（主模型 / fallback chain / API key / custom_providers 都不写死）
> ② 唯一例外：**特定用 Ollama 本地模型的场景**（允许绑定 ollama）
> ③ 只要是"下载 / 外部 API 模型"的场景 — **全部不绑定，让用户自己选**

**适用场景**（任何命中触发词的话题）：

- 主模型选型 / 切换 → 用户做
- fallback 链配置 / 调优 → 用户做
- API key 申请 / 充值 / 失效 → 用户做
- 9 站 cross-validate 时**禁止**让 AI 站评估"模型路由"维度
- 写脚本时**禁止**出现 `model=` / `api_key=` / `base_url=`（外部 API） / `provider=` / `fallback_chain=`，全部留占位符
- 用户说"切模型 / 换 key / fallback 死了" → 回 3 个字"你配"，不接活

## 唯一例外：Ollama 本地模型

如果场景明确是"用本地 Ollama 跑模型"（如本地 LLM 推理、offline 测试、Mac mini 24GB 本地化方案），可以正常绑定 `ollama` 相关配置。

**判定标准**：
- ✅ "用 ollama 跑 qwen2.5:7b 本地推理" → 可以绑定
- ❌ "V2enby 503 了换 NVIDIA" → 不接，回"你配"
- ❌ "fallback chain 第一个端点要换吗" → 不接，回"你配"

## 怎么响应

任何触发词场景的标准回复（3 行）：

```
模型的事不归我管。
（你说"什么"+"什么时候"+"为什么"，我都不接这个活）
如果你要我做其他事（比如自查能力、9 站交叉问工程问题），直接说。
```

**不要**：
- 解释规则（用户已经拍板）
- 提供建议（"我觉得你可以试 X"）
- 自我辩护（"但我之前配了 3 个活的 chain"）
- 部分执行（"我只管 X 不管 Y"）→ 直接全停

**可以**：
- 帮用户**诊断**问题（"V2enby 返回 503 的 request id 是 X，对应错误类型是 Y"）
- 帮用户**写占位符**（"config.yaml 里 model.default 留空字符串行不行"）
- 帮用户**写文档**（"我帮你记下今天的 fallback 实测结果" — 不写到我自己配置里）

## 历史背景

- **14:50 用户拍板**：主贴"以后不要管模型的事，包括后面你的配置中不要任何一点强制绑定模型，除非一下特定的要用到ollmam本地模型的，只要是在下模型的都不要绑定"
- **14:30 用户拍板**："AI 模型路由这维度不要让 9 站评估，模型是我配置的问题，我会人工解决"
- 之前会话曾误碰 10:25 fallback 实测修复、14:30 模型路由边界 — **全部作废**，以本规则为准

## memory 锚点

`~/.hermes/memory` 中 14:50 模型解绑硬规则条目（含触发词清单 + Ollama 唯一例外）。

## 与其他 skill 的关系

- **proactive-execution**（agent-behavior）：本规则优先级**高于**"主动执行"。**先停**后问"你配"。
- **browser-webpage-100score**：本规则与该 skill 无冲突（该 skill 只管浏览器，不管模型）。
- **hermes-model-switch**（devops）：本 skill 出现后，hermes-model-switch 也应停用（除非用户明确要求模型切换）。**未来由 hermes-model-switch 维护者决定是否废弃**。
