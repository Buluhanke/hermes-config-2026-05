# Hermes v3 Demo — 项目结构与运行方式（2026-05-14）

## 项目位置
`/Users/aimac/hermes_v3_demo/`

## 架构

```
Hermes工具层(browser_navigate/browser_snapshot/browser_click)
    ↓  控制主机Chrome
HermesPerceptionBridge (bridge.py, 12KB)
    ↓  observe()/execute() 接口
WebAgentV3Demo (demo_runner.py, 15KB) ← 主机终端直接运行
    ├── UCB1 选择器
    ├── ReflectionEngine
    ├── SkillLibrary
    ├── ExplorationManager
    └── WorldGraph
    ↓ 持久化
data/skills.json, data/agent_run_log.jsonl
```

## 文件清单

```
hermes_v3_demo/
├── README.md
├── requirements.txt          # numpy, matplotlib（可选：playwright, pyautogui）
├── start_demo.py            # 简单启动入口
├── demo_runner.py            # 核心agent主循环（UCB1+反思+技能库）← 主要工作文件
├── fake_site/               # 模拟商城
│   ├── index.html           # 商品展示 + 加入购物车
│   ├── login.html           # 登录页（用户名admin，密码123456）
│   └── cart.html            # 购物车 + 结算
├── perception/
│   └── bridge.py            # CDP WebSocket感知执行器
├── agent_v2/
│   └── web_agent_v2.py      # UCB1 + 状态编码 + 世界图 + 验证器
├── agent_v3/
│   ├── modules.py           # GoalQueue/Reflection/SkillLibrary/PolicyUpdater等
│   └── web_agent_v3_opt.py  # V3主循环（部分依赖Hermes工具）
└── data/
    ├── skills.json
    └── agent_run_log.jsonl
```

## 运行方式（在主机终端，不在execute_code沙盒）

```bash
cd ~/hermes_v3_demo
pip install numpy matplotlib
python3 start_demo.py
# 或指定目标：
python3 start_demo.py --goal 登录 --goal 加入购物车
# 指定最大迭代：
python3 demo_runner.py --goal 登录 --max-iter 3 --max-steps 10
```

## 目标序列

- `登录`：打开登录页 → 填写用户名(admin) → 填写密码(123456) → 提交登录
- `加入购物车`：打开商品页 → 点击加入购物车
- `结算`：打开购物车 → 点击结算 → 填写地址 → 提交订单

## 核心API

### demo_runner.py 中的 Agent

```python
from demo_runner import WebAgentV3Demo

agent = WebAgentV3Demo(start_url="file:///.../index.html", max_steps=20)
agent.add_goal("登录")
agent.add_goal("加入购物车")
agent.run(max_iterations=999)
```

### bridge.py 中的 Bridge

```python
from perception.bridge import HermesPerceptionBridge

bridge = HermesPerceptionBridge()
bridge.navigate("https://example.com")
page_info, clickables = bridge.observe()  # (dict, list[dict])
bridge.execute(action_dict)  # action_dict = {"text": "登录", "x": 200, "y": 300}
```

## 已知约束

1. CDP WebSocket 在沙盒里不work（沙盒网络隔离），必须在主机本地跑
2. `browser_snapshot` 有时返回空列表（页面加载未完成），bridge.py 已带重试
3. fake_site 登录凭据硬编码：admin / 123456
