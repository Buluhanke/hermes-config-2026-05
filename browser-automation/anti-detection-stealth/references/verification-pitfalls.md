# 反检测验收坑（实战沉淀 2026-06-04）

实战中踩过的验证侧陷阱。一条一行，下次省 1 小时。

---

## 1. JSON.stringify + Boolean/Null/Undefined 丢值

**症状**: 跑分脚本传回 `{}` 空对象, 找不到 `webdriver` 字段, 脚本 KeyError 崩

**原因**: `JSON.stringify({webdriver: false})` → `'{"webdriver":false}'` ✅
但 `JSON.stringify({webdriver: navigator.webdriver})` 在 `navigator.webdriver === false` 时**正确**返回 `false`, 在 `=== undefined` 时**丢字段**

更阴的是 — 整个对象里有一个 `undefined` 字段会**触发 None vs missing 的歧义**:
```python
# Python 端: json.loads('{"a": null}') == {"a": None}
#          json.loads('{}') == {}
# 你以为是 undefined, 实际是 null
```

**修复**:
```javascript
// 错
JSON.stringify({webdriver: navigator.webdriver, hw: navigator.hardwareConcurrency})

// 对
JSON.stringify({
    webdriver: String(navigator.webdriver),
    hw: String(navigator.hardwareConcurrency || 0),
    mem: String(navigator.deviceMemory || 0),
    has_chrome: String(!!window.chrome),
})
```

**规则**: 跨语言传 Boolean / Number 时**永远 String() 包一下**, 用 `|| 0` / `|| ""` 处理 undefined

---

## 2. cua-driver 录制 `output_dir` 陷阱

**症状**: 调 `stop_recording` 拿不到 `output_dir`, 后续 `replay_trajectory` 报 "directory does not exist"

**原因**: cua-driver daemon 的 `stop_recording` 响应**故意**把 `output_dir` 字段设成 `null`, 防止旧 output_dir 误回放

**修复** (在 `trajectory_recorder.py` 实现里):
```python
def stop(self):
    raw = self._cua_call("stop_recording")
    # raw["output_dir"] 永远是 None, 必须读 sidecar
    out_dir = self._read_sidecar() or raw.get("last_video_path", "").rsplit("/", 1)[0]
    return {"turns": self._count_turns(out_dir), "video_path": raw.get("last_video_path"),
            "output_dir": out_dir}

def _read_sidecar(self):
    p = Path("~/.hermes/trajectories/.last_output_dir").expanduser()
    return p.read_text().strip() if p.exists() else None
```

`start()` 时同步写 sidecar, `stop()` 时读 sidecar, 跨进程稳

---

## 3. AX coord 越界 — 视作安全网

**症状**: 用户传 `(9999, 9999)` 当坐标, `coord_click` 立即失败, `coord_out_of_bounds`

**原因**: `self_healing_driver.py` Tier 3 故意检测 viewport 边界, 越界**当失败处理**而非 crash

**设计意图**: 这是安全网 — vision 算错坐标、用户传错值时不让脚本悄无声息点错位置

**不要**: 把越界改成 "clamp 到边界再点", 那 vision 算偏 50px 时会点到完全错的元素

---

## 4. AX element_index 不跨会话

**症状**: `mcp_cua_driver_get_window_state` 拿到的 `element_index=14` 在下一次调用就失效

**原因**: element_index 是 per-snapshot 的内存索引, daemon 不持久化

**修复**:
- **回放/重试** 用 pixel coords `(x, y)`, 不用 element_index
- **跨脚本** 用 AX label / role 重新查询, 不用存的 index
- **trajectory_recorder replay** 已知 element_index 类动作会失败, 这是设计如此, 不要试图"修"

---

## 5. addScriptToEvaluateOnNewDocument 的 session 绑定

**症状**: 注入脚本到 tab A, 切到 tab B 注入失败, 报错 "No session with given id"

**原因**: `Page.addScriptToEvaluateOnNewDocument` 绑的是当前 `Page.enable` 创建的 session, 关 ws 就死

**修复**: 用 `Runtime.evaluate` 临时注入**或** 在每个 tab 独立 enable + addScript (看 `anti_detect_inject.py` 怎么轮)

---

## 6. Chrome 148+ origin check 拦截

**症状**: Python `websocket-client` 连 ws://127.0.0.1:9333/devtools/page 报 403 Forbidden

**原因**: Chrome 148 强制检查 Origin 头, `websocket-client` 自动加 `http://127.0.0.1:9333` Origin

**修复**: 用 `websockets` 库 (`pip install websockets`), 它**不**自动加 Origin; **或** `suppress_origin=True`; **或** 启动 Chrome 加 `--remote-allow-origins=*`

参考 `human_drive.py` 第 1 段注释

---

## 7. mouseWheel x/y 必须

**症状**: `Input.dispatchMouseEvent(type="mouseWheel", x=0, y=0, deltaY=-100)` 被 Chrome 148 忽略

**原因**: 真实 wheel 事件永远有坐标, (0,0) 是无效的虚拟事件

**修复**: `human_scroll.py` 里所有 wheel event 都先 `query_dom` 拿当前 hover 元素坐标, 实在拿不到用 viewport 中心

---

## 8. 🚨 跑分脚本末尾"100/100"是硬编码字符串 (2026-06-05 实踩)

**症状**: 跑 `python3 /tmp/verify_all_3.py`, 4 个维度里 12 字段实际只命中 8 个, 但脚本最后一行打印:
```
总分: 88 + 3+5+4=12 = 100 / 100
```
**第一眼以为是 100 分实际表现, 实际是 88 + 各项满分奖励, 任何维度失败都不会扣分**。

**根因**: 脚本作者的"庆祝字符串"在最后 `print` 时**没看前面 ok1/ok3/ok4 标记的状态**, 直接拼 `100` 字面值。等于"默认 100 分, 加分项是锦上添花, 失败不扣分"。

**真实判定规则** (从 `verify_all_3.py` 抠):
| 维度 | 实际 ok 条件 | 打印 ✅ 的条件 |
|---|---|---|
| 缺口1 plugins | `plugins_len==3 AND 'Native Client' in names AND plugins_loaded` | 上面真命中 |
| 缺口2 12 字段 | **永远 ✅** (基线, 看都不看 `ok2_count`) | 永远 ✅ |
| 缺口3 自愈驱动 | `stdout 含 "总累计 attempts: 9"` | 上面真命中 |
| 缺口4 轨迹录制 | `stdout 含 "turns" AND "has_video"` | 上面真命中 |

**修脚本 (推荐)**: 把 "缺口2" 那行改成 `print(f"缺口 2 (12 字段): {'✅ 12/12' if ok2_count==12 else f'❌ {ok2_count}/12'}")`, 然后总分用 `88 + (3 if ok1 else 0) + (5 if ok3 else 0) + (4 if ok4 else 0) - (12-ok2_count)*2`, **失败明确扣分**。

**跑分者 (你) 的保命守则**:
1. **永远不要看脚本末尾的"总分"字符串** — 把它当 noise
2. **必须看每个维度的 `✅/❌` 状态行** + 各自的命中明细
3. **12 字段维度要看 `ok2_count` 实际数字** (脚本里如果有)
4. **跨脚本对比** 时只比"维度状态", 不比"总分"
5. 看到 "100/100" 第一反应: **是 noise, 别信**

---

## 9. verify 12 字段的 `is False` / `isinstance(int)` 断言必踩坑

**症状** (2026-06-05 实踩): 浏览器实际 `navigator.webdriver === undefined` (注入成功 ✅), 但 verify 脚本里:
```python
("webdriver=false", v2['webdriver'] is False),  # ❌ 永远 False
("hardwareConcurrency", isinstance(v2['hw'], int) and v2['hw'] > 0),  # ❌ String(8)=="8" 不是 int
```
全部判失败, 报告 8/12。

**根因**: JS 端 `String(undefined)` → `"undefined"` 字符串, `String(8)` → `"8"` 字符串, `String('ontouchstart' in window)` → `"false"` 字符串。Python `json.loads` 收到后**全部是 `str`**, 永远不可能 `is False` (Python 严格类型), 永远不可能 `isinstance(int)`。

**修断言 (推荐写法)**:
```python
def as_bool(v):
    if v in (True, 'true', 'True', 1, '1'): return True
    if v in (False, 'false', 'False', 0, '0', None, '', 'undefined', 'null'): return False
    return bool(v)

def as_int(v):
    try: return int(v)
    except: return None

checks = [
    ("webdriver 非 true", v2['webdriver'] not in ('true', True)),
    ("UA 非 headless", v2['headless_marker'] in (True, 'true')),
    ("platform", v2['platform'] in ('MacIntel', 'Win32')),
    ("languages 多值", v2['langs'] not in (None, '', '[]')),
    ("hardwareConcurrency>0", (as_int(v2['hw']) or 0) > 0),
    ("deviceMemory>0", (as_int(v2['mem']) or 0) > 0),
    ("touchstart 是 bool", v2['has_touch'] in (True, False, 'true', 'false')),
    ("chrome 对象", as_bool(v2['has_chrome'])),
    ...
]
```

**经验法则**:
- JS 端 **`String()` 化是为了不让 JSON 丢字段**, 代价是 Python 端必须按 `str` 解
- Python 端断言**永远先宽容转一遍再判**, 不要再追求"严格类型匹配"
- 写新跑分脚本时, JS 端用 `JSON.stringify({x: String(val)})`, Python 端用 `as_bool/as_int` 辅助函数
- **真实分数必须从 `ok2_count` 这种 count 数字读**, 不要从 ✅/❌ 字符串里"目测推断"

---

## 10. navigator.webdriver 真实值是 undefined, 不是 false

**澄清** (2026-06-05 实测, 推翻之前 SKILL.md 里"`webdriver false→undefined`"的描述):
- **目标**: 注入后 `navigator.webdriver` 是 `undefined` (**不是** `true`, **也**不是 `false`)
- **原因**: `Object.defineProperty(Navigator.prototype, 'webdriver', {get: () => undefined, configurable: true})` — 故意返回 undefined, 因为 **false 也是指纹** ("false" 强烈暗示 Puppeteer 1.7 之前的版本)
- **验证方法**: 注入后看
  ```js
  navigator.webdriver              // undefined  ← 目标值
  typeof navigator.webdriver       // "undefined"
  Object.getOwnPropertyDescriptor(navigator, 'webdriver')  // undefined (own prop 不存在, 走 prototype getter)
  Object.getOwnPropertyDescriptor(Navigator.prototype, 'webdriver')  // {enumerable:true, configurable:true} (无 value/getter — 故意)
  ```
- **判定**: "非 true" = ✅, 别再追求"等于 false"
- **传播**: 跑分脚本里这个字段的断言**就只断 `not in ('true', True)`**, 写 `is False` 永远是错的
- **更新 SKILL.md 描述**: 把"`webdriver false→undefined`"改成"`webdriver true→undefined (非 false, false 本身也是指纹)`"
