# agent-browser CLI 调用细节（用于 BrowserPerception）

## 核心命令

```bash
npx agent-browser snapshot -c -J <session_key>
```

参数说明：
- `-c` — compact mode（只输出交互元素）
- `-J` — JSON 格式输出（含 axTree、refs、url、title 等结构化数据）
- `<session_key>` — 浏览器会话标识，默认 `"default"`

## 返回数据结构

```json
{
  "success": true,
  "data": {
    "url": "https://example.com",
    "title": "Example Domain",
    "axTree": [
      {
        "nodeId": "1",
        "role": "rootWebArea",
        "properties": [
          {"name": "name", "value": "Example Domain"},
          {"name": "focusable", "value": false}
        ]
      },
      {
        "nodeId": "10",
        "role": "link",
        "properties": [
          {"name": "name", "value": "More information"},
          {"name": "clickable", "value": true},
          {"name": "url", "value": "https://www.iana.org/domains/example"}
        ]
      }
    ],
    "refs": {
      "e1": "nodeId:10",
      "e2": "nodeId:15"
    },
    "frameTree": {
      "frame_id": "1234",
      "url": "https://example.com",
      "childFrames": []
    },
    "pendingDialogs": [],
    "consoleErrors": []
  }
}
```

## 关键字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `axTree[]` | array | flat 的 AX 节点数组，每个节点有 `nodeId`、`role`、`properties[]` |
| `properties[].name` | string | 属性名：name, value, focusable, clickable, checked, selected, url, description 等 |
| `properties[].value` | any | 属性值（字符串或布尔值） |
| `refs` | object | `"eN": "nodeId:<id>"` 映射，@eN 引用用于 browser_click/browser_type |
| `frameTree` | object | iframe 嵌套结构，含 frame_id, url, childFrames |
| `pendingDialogs` | array | 未处理的 alert/confirm/prompt |
| `consoleErrors` | array | 页面上 JS 错误 |

## 在 perception.py 中的使用

```python
# BrowserPerception.__init__ 接收 session_key
bp = BrowserPerception(session_key="default")

# perceive_full() 执行 CLI 调用并解析 JSON
elements, meta = await bp.perceive_full()

# _parse_ax_nodes() 将 axTree + refs 转为 PerceptionElement 列表
# 关键映射逻辑：
# - role → PerceptionElement.role
# - properties 中的 name/value/focusable/clickable → 对应字段
# - refs 中的 eN → perception_id 以 "browser_cdp:page@eN" 格式
```

## 注意事项

- agent-browser CLI 需要 `~/.hermes/hermes-agent/` 下运行（含 node_modules）
- 首次调用会启动 agent-browser daemon（socket 通信）
- session_key 隔离不同浏览器实例，每个 key 独立 CDP 连接
- `-J` 输出是 JSON 纯文本，`-c` (compact mode) 只影响非 JSON 模式的文本输出
- 如果浏览器网关未运行，返回 `{"success": false, "error": "..."}`
