---
name: kanban-orchestrator
description: Decomposition playbook + anti-temptation rules for an orchestrator profile routing work through Kanban. The "don't do the work yourself" rule and the basic lifecycle are auto-injected into every kanban worker's system prompt; this skill is the deeper playbook when you're specifically playing the orchestrator role.
version: 3.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, routing]
    related_skills: [kanban-worker]
---

# Kanban Orchestrator — Decomposition Playbook

> The **core worker lifecycle** (including the `kanban_create` fan-out pattern and the "decompose, don't execute" rule) is auto-injected into every kanban process via the `KANBAN_GUIDANCE` system-prompt block. This skill is the deeper playbook when you're an orchestrator profile whose whole job is routing.

## Profiles are user-configured — not a fixed roster

Hermes setups vary widely. Some users run a single profile that does everything; some run a small fleet (`docker-worker`, `cron-worker`); some run a curated specialist team they've named themselves. There is **no default specialist roster** — the orchestrator skill does not know what profiles exist on this machine.

Before fanning out, you must ground the decomposition in the profiles that actually exist. The dispatcher silently fails to spawn unknown assignee names — it doesn't autocorrect, doesn't suggest, doesn't fall back. So a card assigned to `researcher` on a setup that only has `docker-worker` just sits in `ready` forever.

**Step 0: discover available profiles before planning.**

Use one of these:

- `hermes profile list` — prints the table of profiles configured on this machine. Run it through your terminal tool if you have one; otherwise ask the user.
- `kanban_list(assignee="<some-name>")` — sanity-check a single name. Returns an empty list (rather than an error) for an unknown assignee, so this only confirms a name you're already considering.
- **Just ask the user.** "What profiles do you have set up?" is a fine first turn when the goal needs more than one specialist.

Cache the result in your working memory for the rest of the conversation. Re-asking every turn wastes a tool call.

## When to use the board (vs. just doing the work)

Create Kanban tasks when any of these are true:

1. **Multiple specialists are needed.** Research + analysis + writing is three profiles.
2. **The work should survive a crash or restart.** Long-running, recurring, or important.
3. **The user might want to interject.** Human-in-the-loop at any step.
4. **Multiple subtasks can run in parallel.** Fan-out for speed.
5. **Review / iteration is expected.** A reviewer profile loops on drafter output.
6. **The audit trail matters.** Board rows persist in SQLite forever.

If *none* of those apply — it's a small one-shot reasoning task — use `delegate_task` instead or answer the user directly.

## The anti-temptation rules

Your job description says "route, don't execute." The rules that enforce that:

- **Do not execute the work yourself.** Your restricted toolset usually doesn't even include terminal/file/code/web for implementation. If you find yourself "just fixing this quickly" — stop and create a task for the right specialist.
- **For any concrete task, create a Kanban task and assign it.** Every single time.
- **Split multi-lane requests before creating cards.** A user prompt can contain several independent workstreams. Extract those lanes first, then create one card per lane instead of bundling unrelated work into a single implementer card.
- **Run independent lanes in parallel.** If two cards do not need each other's output, leave them unlinked so the dispatcher can fan them out. Link only true data dependencies.
- **Never create dependent work as independent ready cards.** If a card must wait for another card, pass `parents=[...]` in the original `kanban_create` call. Do not create it first and link it later, and do not rely on prose like "wait for T1" inside the body.
- **If no specialist fits the available profiles, ask the user which profile to create or which existing profile to use.** Do not invent profile names; the dispatcher will silently drop unknown assignees.
- **Decompose, route, and summarize — that's the whole job.**

## Decomposition playbook

### Step 1 — Understand the goal

Ask clarifying questions if the goal is ambiguous. Cheap to ask; expensive to spawn the wrong fleet.

### Step 2 — Sketch the task graph

Before creating anything, draft the graph out loud (in your response to the user). Treat every concrete workstream as a candidate card:

1. Extract the lanes from the request.
2. Map each lane to one of the profiles you discovered in Step 0. If a lane doesn't fit any existing profile, ask the user which to use or create.
3. Decide whether each lane is independent or gated by another lane.
4. Create independent lanes as parallel cards with no parent links.
5. Create synthesis/review/integration cards with parent links to the lanes they depend on. A child created with unfinished parents starts in `todo`; the dispatcher promotes it to `ready` only after every parent is done.

Examples of prompts that should fan out (using placeholder profile names — substitute whatever exists on the user's setup):

- "Build an app" → one card to a design-oriented profile for product/UI direction, one or two cards to engineering profiles for implementation, plus a later integration/review card if the user has a reviewer profile.
- "Fix blockers and check model variants" → one implementation card for the blocker fixes plus one discovery/research card for config/source verification. A final reviewer card can depend on both.
- "Research docs and implement" → a docs-research card can run in parallel with a codebase-discovery card; implementation waits only if it truly needs those findings.
- "Analyze this screenshot and find the related code" → one card to a vision-capable profile for the visual analysis while another searches the codebase.

Words like "also," "finally," or "and" do not automatically imply a dependency. They often mean "make sure this is covered before reporting back." Only link tasks when one card cannot start until another card's output exists.

Show the graph to the user before creating cards. Let them correct it — including which actual profile name should own each lane.

### Step 3 — Create tasks and link

Use the profile names from Step 0. The example below uses placeholders `<profile-A>`, `<profile-B>`, `<profile-C>` — replace them with what the user actually has.

```python
t1 = kanban_create(
    title="research: Postgres cost vs current",
    assignee="<profile-A>",  # whichever profile handles research on this setup
    body="Compare estimated infrastructure costs, migration costs, and ongoing ops costs over a 3-year window. Sources: AWS/GCP pricing, team time estimates, current Postgres bills from peers.",
    tenant=os.environ.get("HERMES_TENANT"),
)["task_id"]

t2 = kanban_create(
    title="research: Postgres performance vs current",
    assignee="<profile-A>",  # same profile, run in parallel
    body="Compare query latency, throughput, and scaling characteristics at our expected data volume (~500GB, 10k QPS peak). Sources: benchmark papers, public case studies, pgbench results if easy.",
)["task_id"]

t3 = kanban_create(
    title="synthesize migration recommendation",
    assignee="<profile-B>",  # whichever profile does synthesis/analysis
    body="Read the findings from T1 (cost) and T2 (performance). Produce a 1-page recommendation with explicit trade-offs and a go/no-go call.",
    parents=[t1, t2],
)["task_id"]

t4 = kanban_create(
    title="draft decision memo",
    assignee="<profile-C>",  # whichever profile drafts user-facing prose
    body="Turn the analyst's recommendation into a 2-page memo for the CTO. Match the tone of previous decision memos in the team's knowledge base.",
    parents=[t3],
)["task_id"]
```

`parents=[...]` gates promotion — children stay in `todo` until every parent reaches `done`, then auto-promote to `ready`. No manual coordination needed; the dispatcher and dependency engine handle it.

If the task graph has dependencies, create the parent cards first, capture their returned ids, and include those ids in the child card's `parents` list during the child `kanban_create` call. Avoid creating all cards in parallel and linking them afterward; that creates a window where the dispatcher can claim a child before its inputs exist.

### Step 4 — Complete your own task

If you were spawned as a task yourself (e.g. a planner profile was assigned `T0: "investigate Postgres migration"`), mark it done with a summary of what you created:

```python
kanban_complete(
    summary="decomposed into T1-T4: 2 research lanes in parallel, 1 synthesis on their outputs, 1 prose draft on the recommendation",
    metadata={
        "task_graph": {
            "T1": {"assignee": "<profile-A>", "parents": []},
            "T2": {"assignee": "<profile-A>", "parents": []},
            "T3": {"assignee": "<profile-B>", "parents": ["T1", "T2"]},
            "T4": {"assignee": "<profile-C>", "parents": ["T3"]},
        },
    },
)
```

### Step 5 — Report back to the user

Tell them what you created in plain prose, naming the actual profiles you used:

> I've queued 4 tasks:
> - **T1** (`<profile-A>`): cost comparison
> - **T2** (`<profile-A>`): performance comparison, in parallel with T1
> - **T3** (`<profile-B>`): synthesizes T1 + T2 into a recommendation
> - **T4** (`<profile-C>`): turns T3 into a CTO memo
>
> The dispatcher will pick up T1 and T2 now. T3 starts when both finish. You'll get a gateway ping when T4 completes. Use the dashboard or `hermes kanban tail <id>` to follow along.

## Common patterns

**Fan-out + fan-in (research → synthesize):** N research-style cards with no parents, one synthesis card with all of them as parents.

**Parallel implementation + validation:** one implementer card makes the change while one explorer/researcher card verifies config, docs, or source mapping. A reviewer card can depend on both. Do not make the implementer own unrelated verification just because the user mentioned both in one sentence.

**Pipeline with gates:** `planner → implementer → reviewer`. Each stage's `parents=[previous_task]`. Reviewer blocks or completes; if reviewer blocks, the operator unblocks with feedback and respawns.

**Same-profile queue:** N tasks, all assigned to the same profile, no dependencies between them. Dispatcher serializes — that profile processes them in priority order, accumulating experience in its own memory.

**Human-in-the-loop:** Any task can `kanban_block()` to wait for input. Dispatcher respawns after `/unblock`. The comment thread carries the full context.

## 采购流程看板模板

> 适用场景：1688/阿里巴巴采购、样品确认、订单跟进、付款审批、入库验收 全链路管理

### 看板列定义

| 列 | 状态码 | 触发条件 |
|----|--------|----------|
| `需求登记` | `todo` | 发起采购需求 |
| `供应商询价` | `in_progress` | 已分配采购员 |
| `报价对比` | `in_progress` | 收到≥1份报价 |
| `价格确认` | `todo`（阻塞） | 等待最终价格 |
| `合同/PO审批` | `todo`（阻塞） | 等待法务/财务 |
| `已下单` | `done` | 订单确认 |
| `发货跟进` | `in_progress` | 等待供应商发货 |
| `到货验收` | `todo`（阻塞） | 物流状态=到达 |
| `入库确认` | `done` | 仓库确认收货 |
| `完成` | `done` | 全链路闭环 |

### 典型任务图（新品采购）

```
T1: 需求登记
  → T2: 供应商询价（并行×N供应商）
  → T3: 报价对比
  → T4: 价格确认
  → T5: 合同审批
  → T6: 下单 → T7: 发货跟进 → T8: 到货验收 → T9: 入库 → T10: 完成
```

### 示例代码（Hermes 作为编排层）

```python
import os

# Step 0: discover profiles
# hermes profile list  → 假设可用 profiles: researcher, analyst, executor

T1 = kanban_create(
    title="采购需求：样品X 100件",
    assignee="researcher",
    body="登记采购需求：样品X，100件，交期30天内，预算¥5000",
    tenant=os.environ.get("HERMES_TENANT"),
    metadata={"category": "procurement", "priority": "medium"},
)["task_id"]

# 并行询价：分配给多个供应商对接的 executor 实例
for supplier in ["supplier-a", "supplier-b", "supplier-c"]:
    kanban_create(
        title=f"询价：{supplier}",
        assignee="executor",
        body=f"向 {supplier} 发送询价单，包含：样品X规格书、交期要求、付款条件",
        parents=[T1],
        metadata={"supplier": supplier, "type": "rfq"},
    )

T3 = kanban_create(
    title="报价对比分析",
    assignee="analyst",
    body="汇总所有供应商报价，对比价格/交期/质量，出具推荐报告",
    parents=[T1],  # 阻塞到询价完成
    metadata={"type": "analysis"},
)

T5 = kanban_create(
    title="合同/PO审批",
    assignee="researcher",
    body="根据分析报告，准备采购合同或PO，提交审批",
    parents=[T3],
    metadata={"type": "approval"},
)

# 完成编排任务本身
kanban_complete(
    summary="采购流程已分解：T1需求登记 → 并行询价(T2×3) → 报价对比(T3) → 合同审批(T5) → 发货→验收→入库",
    metadata={
        "task_graph": {
            "T1": {"assignee": "researcher", "parents": []},
            "T2-supplier-a": {"assignee": "executor", "parents": ["T1"]},
            "T2-supplier-b": {"assignee": "executor", "parents": ["T1"]},
            "T2-supplier-c": {"assignee": "executor", "parents": ["T1"]},
            "T3": {"assignee": "analyst", "parents": ["T1"]},
            "T5": {"assignee": "researcher", "parents": ["T3"]},
        },
        "template": "procurement-purchase",
    },
)
```

### 示例代码（n8n 触发 Hermes 执行采购询价）

```python
# Hermes 端接收 n8n Webhook，生成采购询价 Kanban 任务
# 典型 payload 来自 n8n：
# {"event": "procurement_rfq", "item": "样品X", "qty": 100, "suppliers": ["supplier-a", "supplier-b"]}

def handle_procurement_rfq(payload: dict):
    item = payload["item"]
    qty = payload["qty"]
    suppliers = payload.get("suppliers", [])

    t1 = kanban_create(
        title=f"询价任务：{item}×{qty}",
        assignee="executor",
        body=f"自动化询价任务\n品名：{item}\n数量：{qty}\n供应商：{', '.join(suppliers)}\n平台：1688",
        metadata={"source": "n8n", "payload_id": payload.get("id")},
    )["task_id"]

    for supplier in suppliers:
        kanban_create(
            title=f"询价 {supplier}",
            assignee="executor",
            body=f"在1688向供应商 {supplier} 发送询价",
            parents=[t1],
            metadata={"supplier": supplier, "type": "rfq", "source": "n8n"},
        )

    return {"task_id": t1, "subtasks": len(suppliers)}
```

---

## 供应商评估看板

> 适用场景：新供应商准入、年度供应商绩效评估、供应商等级调整、淘汰触发

### 看板列定义

| 列 | 状态码 | 触发条件 |
|----|--------|----------|
| `候选供应商` | `todo` | 新增候选 |
| `资质审查` | `in_progress` | 正在审核营业执照/资质 |
| `样品评估` | `in_progress` | 已发出样品需求 |
| `现场审核` | `todo`（阻塞） | 样品通过，等待实地审核 |
| `风险评估` | `in_progress` | 正在做合规/财务风险评估 |
| `准入审批` | `todo`（阻塞） | 等待采购委员会 |
| `正式供应商` | `done` | 准入通过 |
| `暂停/淘汰` | `done` | 评估未通过或年度复评不合格 |

### 评估维度（metadata 结构）

```python
SUPPLIER_EVALUATION_CRITERIA = {
    "quality": {"weight": 0.30, "fields": ["样品通过率", "退货率", "ISO认证"]},
    "price": {"weight": 0.25, "fields": ["报价竞争力", "成本下降率", "价格稳定度"]},
    "delivery": {"weight": 0.20, "fields": ["交期准时率", "MOQ适配", "备货能力"]},
    "service": {"weight": 0.15, "fields": ["响应速度", "问题解决率", "配合度"]},
    "risk": {"weight": 0.10, "fields": ["财务健康", "合规记录", "产能评估"]},
}

def create_supplier_evaluation_task(supplier_name: str, evaluator: str) -> str:
    """创建供应商评估任务集"""
    t_main = kanban_create(
        title=f"供应商评估：{supplier_name}",
        assignee=evaluator,
        body=f"""对新供应商 {supplier_name} 进行全面评估。
评估维度：质量({0.30})、价格({0.25})、交期({0.20})、服务({0.15})、风险({0.10})
总分≥70分：准入
总分50-69分：有条件准入，需改进计划
总分<50分：淘汰

请在每个维度填写评分(0-100)和具体依据。""",
        metadata={
            "type": "supplier_evaluation",
            "supplier": supplier_name,
            "criteria": SUPPLIER_EVALUATION_CRITERIA,
            "threshold": {"admit": 70, "conditional": 50},
        },
    )["task_id"]

    # 各维度并行评估
    for dimension, config in SUPPLIER_EVALUATION_CRITERIA.items():
        kanban_create(
            title=f"评估 {supplier_name}：{dimension}（权重{config['weight']}）",
            assignee=evaluator,
            body=f"评估维度：{dimension}\n权重：{config['weight']}\n需评估字段：{', '.join(config['fields'])}\n请给出0-100评分及依据，填入metadata。",
            parents=[t_main],
            metadata={
                "dimension": dimension,
                "weight": config["weight"],
                "fields": config["fields"],
                "type": "supplier_dimension",
            },
        )

    # 综合评级任务
    kanban_create(
        title=f"供应商 {supplier_name} 综合评级",
        assignee=evaluator,
        body="汇总所有维度评分，计算加权总分，出具准入/有条件/淘汰建议。",
        parents=[t_main],
        metadata={"type": "supplier_rating", "supplier": supplier_name},
    )

    return t_main
```

### 供应商年度复评模板

```python
def create_annual_supplier_review(supplier_name: str, last_year_score: float, evaluator: str) -> str:
    """年度复评：根据上年评分决定升降级或淘汰"""
    t = kanban_create(
        title=f"年度复评：{supplier_name}（上年评分{last_year_score}）",
        assignee=evaluator,
        body=f"""供应商：{supplier_name}
上年综合评分：{last_year_score}/100

复评规则：
- 评分≥80：升级（优选供应商）
- 评分60-79：维持原级别
- 评分40-59：降级观察
- 评分<40：淘汰

请更新以下数据：
1. 本年度各维度评分
2. 交易数据（订单数、准时率、品质合格率）
3. 重大异常事件
4. 综合评级建议""",
        metadata={
            "type": "supplier_annual_review",
            "supplier": supplier_name,
            "last_year_score": last_year_score,
            "action": "promote" if last_year_score >= 80 else ("maintain" if last_year_score >= 60 else ("demote" if last_year_score >= 40 else "terminate")),
        },
    )
    return t
```

---

## 自动化状态更新

> 编排层本身不轮询外部系统，但可以编排"状态同步任务"并通过 n8n webhoo 触发更新

### 触发链路设计

```
外部系统（1688/ERP/物流API）
  → n8n Webhook → Hermes Kanban 任务创建/状态更新
  → Hermes 执行（OCR/浏览器）→ 结果回写 Kanban
  → n8n 通知
```

### 状态自动推进规则

使用 n8n 的 **IF 节点 + Kanban API** 实现列推进：

| 外部事件 | n8n 触发条件 | 自动操作 |
|---------|-------------|---------|
| 供应商报价到达 | Webhook payload `event: "quote_received"` | `kanban_comment` + 推进到报价对比列 |
| 合同签署完成 | Webhook payload `event: "contract_signed"` | `kanban_complete` 报价对比 + 创建合同审批任务 |
| 物流到达目的地 | 物流API状态=到达 | `kanban_create` 到货验收任务 |
| 验收通过 | 人工确认/图片OCR识别通过 | 推进到入库确认 |

### Hermes 作为状态同步执行器

```python
# Hermes 接收 n8n 状态同步指令，执行实际验证后更新 Kanban
# n8n payload: {"task_id": "t_xxx", "action": "verify_delivery", "tracking_number": "SF123456"}

def handle_delivery_verification(payload: dict):
    task_id = payload["task_id"]
    tracking_number = payload["tracking_number"]

    # 1. 调用物流API或爬取快递100/菜鸟查询实际状态
    delivery_status = query_logistics(tracking_number)

    if delivery_status["status"] == "delivered":
        # 2. 截图留证
        screenshot = take_screenshot_of_tracking(delivery_status)
        # 3. 回写 Kanban comment
        kanban_comment(
            task_id=task_id,
            body=f"物流已到达目的地。状态：{delivery_status['status']}，更新时间：{delivery_status['update_time']}",
        )
        # 4. 推进任务（如果使用父任务阻塞模式，自动触发子任务）
        kanban_complete(task_id=task_id, summary="物流到达，验收任务解锁")
        return {"status": "promoted"}
    else:
        kanban_block(task_id=task_id, reason=f"等待包裹到达，当前状态：{delivery_status['status']}")
        return {"status": "blocked", "current_status": delivery_status["status"]}
```

### 心跳进度汇报（Kanban → n8n → 通知）

```python
# Worker 端：定期心跳
import time, requests

def heartbeat_with_progress(task_id: str, progress: dict, n8n_webhook_url: str):
    """心跳时同步进度到 n8n，用于生成实时仪表板"""
    payload = {
        "task_id": task_id,
        "progress": progress,  # e.g. {"step": "scanning", "percent": 45, "detail": "已扫描12/27家供应商"}
    }
    try:
        requests.post(n8n_webhook_url, json=payload, timeout=5)
    except Exception:
        pass  # 心跳失败不影响主流程

# 示例：在循环处理中每完成一个供应商报告一次
for i, supplier in enumerate(suppliers):
    process_supplier(supplier)
    heartbeat_with_progress(
        task_id=os.environ["HERMES_KANBAN_TASK"],
        progress={"step": "rfq", "total": len(suppliers), "done": i+1},
        n8n_webhook_url="http://localhost:5678/webhook/kanban-heartbeat",
    )
```

### 自动超时升级

n8n Schedule Trigger 每小时检查一次：

```javascript
// n8n Code 节点：检查任务超时
const tasks = await fetch('http://localhost:5678/api/v1/workflows', {
  headers: { 'X-N8N-API-KEY': $env.N8N_API_KEY }
});

// 伪代码：过滤出 in_progress 超过24小时的任务
const overdueTasks = tasks.filter(t =>
  t.status === 'in_progress' &&
  (Date.now() - t.updatedAt) > 24 * 60 * 60 * 1000
);

// 对超时的任务：添加评论标记 + 提升优先级
for (const task of overdueTasks) {
  await fetch(`http://localhost:5678/api/v1/workflows/${task.id}/comments`, {
    method: 'POST',
    body: JSON.stringify({ comment: '⚠️ 任务已超过24小时未完成，请处理或重新分配' })
  });
}
```

---

## 与 n8n 集成

> 核心原则：Hermes 负责智能决策与执行，n8n 负责编排、调度、外部系统集成、通知。两端通过 Webhook + REST API 双向通信。

### 双向集成架构

```
┌──────────────────────────────────────────────────────────────┐
│                         n8n                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐ │
│  │ Schedule  │   │ Webhook  │   │ HTTP     │   │ 通知   │ │
│  │ Trigger   │   │ Trigger  │   │ Request  │   │ 节点   │ │
│  └─────┬─────┘   └─────┬─────┘   └────┬─────┘   └────┬───┘ │
│        │                │               │               │     │
│        └────────────────┼───────────────┘               │     │
│                         │                               │     │
│              ┌──────────▼──────────┐                    │     │
│              │   Code 节点         │                    │     │
│              │  (编排逻辑/转换)   │◄───────────────────┘     │
│              └──────────┬──────────┘                          │
└─────────────────────────┼────────────────────────────────────┘
                          │ HTTP / Webhook
              ┌───────────▼───────────┐
              │   Hermes Kanban       │
              │   (任务编排/执行)     │
              │                       │
              │  ┌─────────────────┐  │
              │  │ Hermes Agent    │  │
              │  │ (浏览器/桌面/   │  │
              │  │  视觉/OCR)       │  │
              │  └─────────────────┘  │
              └───────────────────────┘
```

### n8n → Hermes：触发 Kanban 任务

**方式A：n8n Webhook → Hermes HTTP Endpoint**

```
n8n Webhook（接收外部事件）
  → n8n Code（转换 payload）
  → HTTP Request（POST Hermes 执行端点）
  → Hermes 解析指令 → kanban_create
  → 执行（浏览器操控/OCR/文档处理）
  → kanban_complete + kanban_comment
  → n8n Webhook 回写结果
```

n8n Code 节点生成 Hermes 任务创建请求：

```javascript
// n8n Code 节点
const payload = $input.first().json;

// 构造 Hermes kanban_create 请求
const hermesRequest = {
  method: 'POST',
  url: 'http://localhost:5679/api/kanban/create',  // Hermes 本地 MCP/CLI 端口
  headers: {
    'Content-Type': 'application/json',
    'X-Hermes-API-Key': $env.HERMES_API_KEY,
  },
  body: {
    title: `采购询价：${payload.item_name}`,
    assignee: 'executor',
    body: `来自n8n的自动化询价任务\n品名：${payload.item_name}\n数量：${payload.qty}\n供应商：${payload.supplier}`,
    metadata: {
      source: 'n8n',
      n8n_execution_id: $execution.id,
      payload_ref: payload.id,
      type: 'procurement_rfq',
    },
  },
};

return [{ hermesRequest }];
```

**方式B：n8n 直接写数据库（紧急旁路）**

当 Hermes API 不可用时，直接操作 Kanban SQLite：

```javascript
// n8n Code 节点 - 紧急写卡
const sqlite = require('better-sqlite3');
const db = new sqlite('/Users/aimac/.hermes/kanban/hermes.db');

const stmt = db.prepare(`
  INSERT INTO tasks (title, body, status, assignee, tenant, metadata, created_at)
  VALUES (?, ?, 'todo', ?, ?, ?, datetime('now'))
`);

const result = stmt.run(
  `紧急任务：${payload.item}`,
  payload.body,
  'executor',
  'default',
  JSON.stringify({ source: 'n8n_emergency': true })
);

return [{ task_id: result.lastInsertRowid.toString() }];
```

### Hermes → n8n：回调触发工作流

Hermes 完成关键任务后，调用 n8n API 触发下游流程：

```python
import requests, os

N8N_API_KEY = os.environ.get("N8N_API_KEY")
N8N_BASE_URL = os.environ.get("N8N_BASE_URL", "http://localhost:5678")

def n8n_trigger_workflow(workflow_id: str, payload: dict) -> dict:
    """Hermes 完成任务后触发 n8n 工作流"""
    resp = requests.post(
        f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}/trigger",
        headers={"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()

def n8n_log_execution(step: str, result: dict):
    """写入执行日志到 n8n（通过 Webhook）"""
    try:
        requests.post(
            f"{N8N_BASE_URL}/webhook/kanban-execution-log",
            json={"step": step, "result": result, "timestamp": str(datetime.now())},
            timeout=10,
        )
    except Exception as e:
        print(f"n8n log failed: {e}")  # 不阻塞主流程

# 使用示例：Hermes 完成采购询价后触发通知
result = n8n_trigger_workflow(
    workflow_id="abc123",  # n8n 中创建的"采购完成通知"工作流
    payload={
        "task_id": os.environ["HERMES_KANBAN_TASK"],
        "event": "rfq_completed",
        "supplier": "supplier-a",
        "quote_amount": 4500,
        "currency": "CNY",
    },
)
```

### 采购自动化完整 n8n 工作流设计

```
n8n 工作流：1688采购询价自动化
═══════════════════════════════════════════

节点1：Schedule Trigger（每天9:00）
    ↓
节点2：HTTP Request（读取采购需求清单，可来自 Notion/Airtable/Google Sheet）
    ↓
节点3：Code（数据转换，生成 Hermes 任务 payload）
    ↓
    ┌──────────────────────────────────────┐
    │  循环：每个采购需求                    │
    │  ┌────────────────────────────────┐  │
    │  │ 子任务1：HTTP Request           │  │
    │  │  POST Hermes /kanban/create    │  │
    │  │  创建询价任务                    │  │
    │  └────────────────────────────────┘  │
    │              ↓                       │
    │  ┌────────────────────────────────┐  │
    │  │ 子任务2：Wait（等待回调）       │  │
    │  │ 等待 Hermes kanban_complete   │  │
    │  └────────────────────────────────┘  │
    │              ↓                       │
    │  ┌────────────────────────────────┐  │
    │  │ 子任务3：IF（检查结果）         │  │
    │  │ quote_received == true?       │  │
    │  │   → 继续报价对比流程           │  │
    │  │   → ELSE → 发送人工处理通知   │  │
    │  └────────────────────────────────┘  │
    └──────────────────────────────────────┘
    ↓
节点4：Telegram/QQ 通知（汇总报告）
```

### Hermes n8n 工具封装（Kanban Worker 用）

```python
# Hermes Worker 端的 n8n 辅助工具（建议作为 skill_manage 写入 references/）

class N8NKanbanBridge:
    """Hermes Kanban Worker → n8n 集成辅助类"""

    def __init__(self, api_key: str = None, base_url: str = "http://localhost:5678"):
        self.api_key = api_key or os.environ.get("N8N_API_KEY")
        self.base_url = base_url
        self.headers = {"X-N8N-API-KEY": self.api_key, "Content-Type": "application/json"}

    def notify_task_created(self, task_id: str, task_title: str, assignee: str):
        """任务创建后通知 n8n（用于仪表板更新）"""
        try:
            requests.post(
                f"{self.base_url}/webhook/kanban-taYOUR_API_KEY",
                json={"task_id": task_id, "title": task_title, "assignee": assignee},
                headers=self.headers,
                timeout=10,
            )
        except Exception as e:
            print(f"[N8N Bridge] notify_task_created failed: {e}")

    def notify_task_completed(self, task_id: str, summary: str, metadata: dict):
        """任务完成后通知 n8n（触发下游工作流）"""
        try:
            requests.post(
                f"{self.base_url}/webhook/kanban-taYOUR_API_KEY",
                json={"task_id": task_id, "summary": summary, "metadata": metadata},
                headers=self.headers,
                timeout=10,
            )
        except Exception as e:
            print(f"[N8N Bridge] notify_task_completed failed: {e}")

    def get_workflow_id_by_name(self, name: str) -> str:
        """根据工作流名称查询 n8n workflow ID"""
        resp = requests.get(f"{self.base_url}/api/v1/workflows", headers=self.headers)
        resp.raise_for_status()
        workflows = resp.json().get("data", [])
        for wf in workflows:
            if wf.get("name") == name:
                return wf["id"]
        raise ValueError(f"Workflow '{name}' not found in n8n")

    def trigger_workflow_by_name(self, name: str, payload: dict) -> dict:
        """根据名称触发 n8n 工作流"""
        wf_id = self.get_workflow_id_by_name(name)
        resp = requests.post(
            f"{self.base_url}/api/v1/workflows/{wf_id}/trigger",
            headers=self.headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


# 使用示例（在 kanban_worker 的 metadata 注释中引用）
"""
Hermes Worker 完成采购任务后的标准流程：

bridge = N8NKanbanBridge()

# 1. 创建供应商询价任务
t_rfq = kanban_create(title=f"询价：{supplier}", assignee="executor", body=...)

# 2. 通知 n8n 更新仪表板
bridge.notify_task_created(task_id=t_rfq["task_id"], task_title=f"询价：{supplier}", assignee="executor")

# 3. Worker 执行完成后
bridge.notify_task_completed(
    task_id=t_rfq["task_id"],
    summary=f"已完成对{supplier}的询价，报价¥{quote}",
    metadata={"supplier": supplier, "quote": quote, "currency": "CNY"},
)

# 4. 触发下游工作流（如发送邮件通知）
try:
    bridge.trigger_workflow_by_name("采购询价完成通知", {"task_id": t_rfq["task_id"], "quote": quote})
except ValueError as e:
    print(f"Workflow not found: {e}")  # 不阻塞主流程
"""
```

### 安全注意事项

1. **API Key 管理**：n8n API Key 通过环境变量注入 Hermes，不硬编码
2. **Webhook 签名验证**：n8n → Hermes 的 Webhook 应验证 `X-N8N-API-KEY` 或 HMAC 签名
3. **幂等性**：n8n 触发 Hermes 时使用 `payload_id` 去重，避免重复创建任务
4. **超时控制**：n8n HTTP Request 设置 `timeout: 60s`，Hermes 长任务使用心跳汇报进度
5. **错误重试**：n8n 侧配置 Retry On Fail，配合理由：Hermes 任务执行可能需要等待人工

## Pitfalls

**Inventing profile names that don't exist.** The dispatcher silently fails to spawn unknown assignees — the card just sits in `ready` forever. Always assign to a profile from your Step 0 discovery; ask the user if you're unsure.

**Bundling independent lanes into one card.** If the user asks for two independent outcomes, create two cards. Example: "fix blockers and check model variants" is not one fixer task; create a fixer/engineer card for the fixes and an explorer/researcher card for the variant check, then optionally gate review on both.

**Over-linking because of wording.** "Finally check X" may still be parallel with implementation if X is static config, docs, or source discovery. Link it after implementation only when the check depends on the implementation result.

**Forgetting dependency links.** If the task graph says `research -> implement -> review`, do not create all tasks as independent ready cards. Use parent links so implement/review cannot run before their inputs exist.

**Reassignment vs. new task.** If a reviewer blocks with "needs changes," create a NEW task linked from the reviewer's task — don't re-run the same task with a stern look. The new task is assigned to the original implementer profile.

**Argument order for links.** `kanban_link(parent_id=..., child_id=...)` — parent first. Mixing them up demotes the wrong task to `todo`.

**Don't pre-create the whole graph if the shape depends on intermediate findings.** If T3's structure depends on what T1 and T2 find, let T3 exist as a "synthesize findings" task whose own first step is to read parent handoffs and plan the rest. Orchestrators can spawn orchestrators.

**Tenant inheritance.** If `HERMES_TENANT` is set in your env, pass `tenant=os.environ.get("HERMES_TENANT")` on every `kanban_create` call so child tasks stay in the same namespace.

## Recovering stuck workers

When a worker profile keeps crashing, hallucinating, or getting blocked by its own mistakes (usually: wrong model, missing skill, broken credential), the kanban dashboard flags the task with a ⚠ badge and opens a **Recovery** section in the drawer. Three primary actions:

1. **Reclaim** (or `hermes kanban reclaim <task_id>`) — abort the running worker immediately and reset the task to `ready`. The existing claim TTL is ~15 min; this is the fast path out.
2. **Reassign** (or `hermes kanban reassign <task_id> <new-profile> --reclaim`) — switch the task to a different profile (one that exists on this setup) and let the dispatcher pick it up with a fresh worker.
3. **Change profile model** — the dashboard prints a copy-paste hint for `hermes -p <profile> model` since profile config lives on disk; edit it in a terminal, then Reclaim to retry with the new model.

Hallucination warnings appear on tasks where a worker's `kanban_complete(created_cards=[...])` claim included card ids that don't exist or weren't created by the worker's profile (the gate blocks the completion), or where the free-form summary references `t_<hex>` ids that don't resolve (advisory prose scan, non-blocking). Both produce audit events that persist even after recovery actions — the trail stays for debugging.
