---
name: e2e-testing
description: E2E testing harness for browser automation — class Cypress. Use when you need to run structured browser tests with assertions, fixtures, screenshots, waits, and reports.
triggers:
  - run e2e test
  - browser test with assertions
  - cypress-like test
  - 端到端测试
  - 浏览器自动化测试
---

# E2E Testing Harness — Hermes Edition

Cypress 同款 E2E 测试能力，Hermes 驱动。

## 架构概览

```
e2e-testing/
├── SKILL.md                    # 本文件
├── references/
│   └── spec-format.md          # spec 文件格式规范
└── scripts/
    ├── e2e_runner.py           # 测试运行器
    ├── assert_screenshot.py    # 截图断言
    ├── wait_for.py             # 元素等待
    └── load_fixture.py         # fixture 加载
```

## 快速开始

### 1. 写一个 spec 文件

```yaml
# example_spec.yaml
name: 登录流程测试
fixture: fixtures/login_data.yaml

steps:
  - action: navigate
    url: https://example.com/login

  - action: screenshot
    name: before_login

  - action: type
    selector: "#username"
    text: "{{ username }}"

  - action: type
    selector: "#password"
    text: "{{ password }}"

  - action: click
    selector: "button[type=submit]"

  - action: wait_for
    selector: ".dashboard"
    timeout: 10000

  - action: screenshot
    name: after_login

  - action: assert_screenshot
    name: after_login
    baseline: baselines/after_login.png
    threshold: 0.05
```

### 2. 运行测试

```bash
python3 ~/.hermes/skills/e2e-testing/scripts/e2e_runner.py \
  --spec path/to/example_spec.yaml \
  --browser chrome \
  --headless
```

### 3. 查看报告

HTML 报告生成在 `./e2e-report-<timestamp>.html`

---

## 核心模块

### e2e_runner.py

测试运行器主入口。

**参数：**
- `--spec` — spec YAML 文件路径（必需）
- `--browser` — `chrome`（默认）| `chromium` | `firefox`
- `--headless` — 无头模式（默认 True）
- `--cdp-url` — CDP 端点，默认 `http://localhost:9222`
- `--output` — 报告输出目录
- `--record` — 是否录制视频

**工作流程：**
1. 解析 spec YAML
2. 加载 fixture 数据
3. 启动/连接浏览器
4. 按顺序执行每个 step
5. 每步截图（可选）
6. 执行断言
7. 失败时停止并报告
8. 生成 HTML 报告

### assert_screenshot.py

截图断言 — 和 baseline 比对，输出差异率。

**Python API：**
```python
from assert_screenshot import assert_screenshot

result = assert_screenshot(
    current="screenshots/after_login.png",
    baseline="baselines/after_login.png",
    threshold=0.05  # 5% 像素差异内通过
)

print(result["passed"])       # True / False
print(result["diff_ratio"])   # 0.0321
print(result["diff_image"])    # diff.png 路径
```

**阈值判断：**
- `diff_ratio <= threshold` → 通过
- `diff_ratio > threshold` → 失败

### wait_for.py

等待元素出现/消失。

**Python API：**
```python
from wait_for import wait_for_element, wait_for_url, wait_for_text

# 等待元素出现
wait_for_element(driver, selector="#error-msg", timeout=10000, state="visible")

# 等待 URL 匹配
wait_for_url(driver, pattern="*/dashboard*", timeout=15000)

# 等待文本出现
wait_for_text(driver, text="Welcome back", timeout=8000)
```

**state 选项：** `present` | `visible` | `hidden` | `enabled`

### load_fixture.py

加载测试数据 fixture。

**Python API：**
```python
from load_fixture import load_fixture

# 加载 YAML fixture
data = load_fixture("fixtures/login_data.yaml")
print(data["username"])  # "testuser"
print(data["password"])  # "secret123"

# 支持环境变量覆盖
# fixture: "{{ username }}" → 替换为环境变量 USERNAME
```

**支持格式：** YAML | JSON | ENV

---

## Browser 控制

使用 cua-driver（`computer_use` 工具）驱动浏览器：

```python
# 连接已有 Chrome 实例
from cua_driver import CUAClient

client = CUAClient(cdp_url="http://localhost:9222")
client.capture()  # 截图

# 点击元素
client.click(selector="#submit-btn")

# 填表
client.type(selector="#username", text="user")
```

或者用 CDP 直连：

```python
import httpx

cdp = httpx.Client(base_url="http://localhost:9222")

# 执行 JavaScript
cdp.post("/json", json={
    "method": "Runtime.evaluate",
    "params": {"expression": "document.title"}
})
```

---

## 报告格式

HTML 报告包含：
- 测试名称、开始/结束时间、耗时
- 每个 step 的截图（before/after）
- 断言结果（通过/失败）
- 失败 step 的完整错误信息
- diff 图像（截图断言失败时）
- 导出 JSON 格式供 CI 使用

---

## 命令行用法

```bash
# 完整示例
python3 ~/.hermes/skills/e2e-testing/scripts/e2e_runner.py \
  --spec ./specs/login_test.yaml \
  --browser chrome \
  --headless \
  --output ./test-results \
  --record

# 批量运行
python3 ~/.hermes/skills/e2e-testing/scripts/e2e_runner.py \
  --spec-dir ./specs/ \
  --parallel 4

# 仅截图比对
python3 ~/.hermes/skills/e2e-testing/scripts/assert_screenshot.py \
  --current ./screenshots/test.png \
  --baseline ./baselines/test.png \
  --threshold 0.05
```

---

## 已知限制

1. **无内置视频录制** — 需要外部 ffmpeg 配合
2. ✅ **网络拦截** — 已集成 mitmproxy-mcp（MCP 协议，开箱即用）
3. **无并行 CI 云端** — 需自己搭报告服务
4. **依赖 Chrome CDP** — 必须有可连接的 Chrome 实例
5. **mitm_wait 实现** — 轮询 `get_traffic_summary` 实现，非原生等待，极快请求可能漏掉
