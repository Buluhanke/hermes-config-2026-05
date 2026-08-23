# E2E Spec Format Specification

## 文件格式

YAML，`.yaml` 或 `.yml` 扩展名。

## 顶层字段

| 字段 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `name` | string | ✅ | 测试名称 |
| `fixture` | string | ❌ | fixture 文件路径 |
| `timeout` | int | ❌ | 全局超时（ms），默认 30000 |
| `before` | list[Step] | ❌ | 全局前置步骤（每个 step 都执行前先跑） |
| `steps` | list[Step] | ✅ | 测试步骤列表 |
| `after` | list[Step] | ❌ | 全局后置步骤（测试结束后执行） |

## Step 类型

### `navigate`

```yaml
- action: navigate
  url: https://example.com/login
```

### `screenshot`

```yaml
- action: screenshot
  name: before_login          # 截图文件名（不含扩展名）
  path: ./screenshots         # 保存目录，默认 ./screenshots
```

### `click`

```yaml
- action: click
  selector: "#submit-btn"      # CSS 选择器
  timeout: 5000               # 等待元素超时
```

### `type`

```yaml
- action: type
  selector: "#username"
  text: "{{ username }}"      # 支持 fixture 占位符
  clear: true                 # 输入前清空，默认 true
```

### `hover`

```yaml
- action: hover
  selector: ".dropdown-menu"
```

### `wait_for`

```yaml
- action: wait_for
  selector: ".modal"           # CSS 选择器
  state: visible              # present | visible | hidden | enabled
  timeout: 10000              # ms，默认 10000
```

### `wait_for_url`

```yaml
- action: wait_for_url
  pattern: "*/dashboard*"     # glob 或正则
  timeout: 15000
```

### `wait_for_text`

```yaml
- action: wait_for_text
  text: "Welcome back"
  timeout: 8000
```

### `assert_screenshot`

```yaml
- action: assert_screenshot
  name: dashboard             # 和 screenshot 的 name 对应
  baseline: baselines/dashboard.png
  threshold: 0.05             # 0.05 = 5% 像素差异内通过
```

### `assert_text`

```yaml
- action: assert_text
  selector: ".welcome"
  expected: "Hello, {{ username }}"
```

### `assert_url`

```yaml
- action: assert_url
  pattern: "*/dashboard*"
```

### `execute_js`

```yaml
- action: execute_js
  script: |
    return document.title;
```

### `scroll_into_view`

```yaml
- action: scroll_into_view
  selector: "#footer"
```

### `select_option`

```yaml
- action: select_option
  selector: "select#country"
  value: CN                   # option value
  # 或者用 text:
  # text: China
```

### `upload_file`

```yaml
- action: upload_file
  selector: "input[type=file]"
  path: /tmp/test-image.png
```

### `refresh`

```yaml
- action: refresh
```

### `go_back`

```yaml
- action: go_back
```

### `mitm_start`

启动 mitmproxy 代理（在 `before` 里用）。

```yaml
- action: mitm_start
  port: 8080              # 可选，默认 8080
```

### `mitm_mock`

添加拦截规则（在 `before` 或 `steps` 里用）。

```yaml
- action: mitm_mock
  rule_id: mock_user      # 规则唯一 ID
  url_pattern: "**/api/user**"   # URL 正则
  phase: response         # request | response
  action_type: replace_body     # inject_header | replace_body | block
  value: '{"id": 1, "name": "test"}'   # 替换内容
  search_pattern: ".*"    # 可选，正则匹配要替换的 body 部分
```

### `mitm_wait`

等待某个请求出现（轮询 `get_traffic_summary` 实现）。

```yaml
- action: mitm_wait
  pattern: "**/api/login**"    # 要等到的 URL 模式
  timeout: 5000                # ms，默认 5000
```

### `mitm_clear`

清空所有拦截规则（在 `after` 里用）。

```yaml
- action: mitm_clear
```

### `mitm_stop`

停止 mitmproxy 代理（在 `after` 里用）。

```yaml
- action: mitm_stop
```

完整集成示例：

```yaml
name: 搜索功能测试（Mock 版）

before:
  - action: mitm_start
    port: 8080
  - action: mitm_mock
    rule_id: mock_search
    url_pattern: "**/api/search**"
    phase: response
    action_type: replace_body
    value: '{"results": [{"id": 1, "name": "mocked result"}]}'
    search_pattern: ".*"

steps:
  - action: navigate
    url: http://example.com
  - action: type
    selector: "#q"
    text: "test"
  - action: click
    selector: "button[type=submit]"
  - action: mitm_wait
    pattern: "**/api/search**"
    timeout: 5000
  - action: assert_text
    selector: ".results"
    expected: "mocked result"

after:
  - action: mitm_clear
  - action: mitm_stop
```

---

## Fixture 占位符

在 `text` 字段中用 `{{ key }}` 引用 fixture 数据：

```yaml
fixture: fixtures/user.yaml

steps:
  - action: type
    selector: "#username"
    text: "{{ username }}"        # → fixtures/user.yaml 的 username 字段
  - action: type
    selector: "#password"
    text: "{{ password }}"
```

支持嵌套：

```yaml
text: "{{ user.profile.display_name }}"
```

环境变量覆盖（`{{ ENV.VAR_NAME }}`）：

```yaml
text: "{{ ENV.API_KEY }}"
```

---

## 完整示例

```yaml
name: 搜索功能测试
timeout: 60000

fixture: fixtures/search.yaml

before:
  - action: navigate
    url: https://example.com
  - action: screenshot
    name: home_page

steps:
  - action: click
    selector: ".search-icon"

  - action: wait_for
    selector: "#search-input"
    state: visible

  - action: type
    selector: "#search-input"
    text: "{{ query }}"

  - action: click
    selector: "button.search-btn"

  - action: wait_for
    selector: ".results-list"
    timeout: 15000

  - action: screenshot
    name: search_results

  - action: assert_text
    selector: ".result-count"
    expected: "{{ expected_count }} results"

after:
  - action: screenshot
    name: final_state
```

---

## 错误处理

### step 级 `on_error`

```yaml
steps:
  - action: click
    selector: ".non-existent"
    timeout: 3000
    on_error: continue      # continue | abort（默认）
```

### 全局 `error_handling`

```yaml
name: 错误处理示例
error_handling:
  on_assertion_fail: abort    # abort | continue
  on_step_error: continue    # abort | continue
  max_retries: 2             # 每个 step 最多重试次数

steps:
  - ...
```

---

## 批量运行

目录批量：

```bash
python3 e2e_runner.py --spec-dir ./specs/
```

匹配 glob：

```bash
python3 e2e_runner.py --spec "**/login*.yaml"
```
