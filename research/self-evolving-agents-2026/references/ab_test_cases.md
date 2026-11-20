# A/B 测试用例（reference）

## 测试用例（固定 5 条，不扩展）

| 编号 | 用例 | 验证内容 |
|---|---|---|
| T1 | 相同输入，重复 3 次 | 输出一致性 |
| T2 | 边界输入（空、超长、特殊字符） | 无崩溃 |
| T3 | 组合输入（多条件叠加） | 不误判 |
| T4 | 长程任务（>10 步） | 不丢状态 |
| T5 | 错误注入（模拟失败） | 恢复机制生效 |

## 输出标准化 JSON

```json
{
  "variant": "v2",
  "test_cases": [
    {"name": "T1", "pass": true, "steps": 3, "errors": []},
    {"name": "T2", "pass": true, "steps": 1, "errors": []},
    {"name": "T3", "pass": true, "steps": 5, "errors": []},
    {"name": "T4", "pass": true, "steps": 12, "errors": []},
    {"name": "T5", "pass": false, "steps": 8, "errors": ["recovery_timeout"]}
  ],
  "metrics": {
    "pass_rate": 0.8,
    "avg_steps": 5.8,
    "avg_tool_calls": 12.4
  }
}
```

## 决策规则

- 按「通过率 + 平均步骤数」双维度评分
- 若 v2/v3 优于 v1：保留变体，写入 `skill_audit.json`（含 diff + 日期）
- 若 v2/v3 劣于 v1：回滚到 v1，记录失败原因到 `lesson_store`
- 保留 last-known-good（总是保留原版备份，`cp -r skill skill_backup_$(date +%F)`）

## 坑

- 变体太多会变成评估噪声：固定 3 个变体、上限 5 条测试用例
- 不同时间运行的变体环境可能不同：统一快照日期记录
- 模型自评代替不了工具实测：任何 A/B 决策必须基于工具调用输出，不能依靠「感觉更好」
