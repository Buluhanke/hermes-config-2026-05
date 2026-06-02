# 视觉点选 (vision_click) — 进化二: 语义锚定 + 动态坐标

## 场景
按钮/链接 没有稳定 id/class, 或在 Shadow DOM 内, 或 id 是哈希随机生成的.
用**文字+坐标**两路兜底, 不依赖 selector.

## 三种用法
```bash
# 1. 列出当前 tab 所有可交互元素
python3 hermes_vision_click.py deepseek list

# 2. 关键词匹配 + 点击
python3 hermes_vision_click.py deepseek "开启新对话"

# 3. 坐标直接点击 (绕过匹配, 万能)
python3 hermes_vision_click.py deepseek "130,90"
```

## 抓元素原理
1. `Accessibility.getFullAXTree` 拿所有 AX 节点 (role=button/link/textbox/menuitem)
2. 对每个 leaf 节点调用 `DOM.getBoxModel` 拿中心坐标
3. JS 启发式扫描 div/span, 检测 `cursor:pointer` 或 button-like class
4. 合并去重, 返回 `[{tag, text, x, y, hint, role}, ...]`

## 匹配算法 (按分排序)
| 信号 | 加分 |
|------|------|
| 完全匹配 query | +10 |
| 开头匹配 | +5 |
| 包含 query | +2 |
| 是按钮 (cursor:pointer / button / a / role=button) | +2 |
| 文本长度 ≤ 6 字 | +1 |
| 在 sidebar/aside/nav 容器内 | **-5** |

取分最高, ≥ 阈值 (默认 5) 才点. 否则打印 top-3 候选让用户决定.

## 三大坑
1. **侧边栏聊天列表** — "新对话"/"开启对话" 会命中 10+ 个 sidebar item.
   解: 负分 -5, 或直接用 `coord="x,y"`.
2. **坐标 0,0** — 元素在视口外 / 隐藏. 解: 滚屏后重抓.
3. **多语种界面** — 中文用户面对英文按钮. 解: 抓所有元素后让 LLM 二次匹配.

## 坐标兜底: 怎么知道 x,y
- AX 树带 box 信息 → `DOM.getBoxModel` → center [x, y]
- 抓元素列表里直接看 (e.g. `DIV '开启新对话' @ (130, 90)`)
- 不知道时用 vision_analyze 截图让 VLM 指出

## 实战例子
DeepSeek 顶部 "开启新对话" 按钮:
- 关键词匹配: "开启新对话" 会被侧边栏干扰 (sidebar -5)
- 坐标兜底: `coord="130,90"` 一击必中

## 进化方向
- LLM 二次匹配 (拿到候选元素后让 MiniMax 选最像按钮的)
- 视觉反馈 (点完截屏确认是否生效, 否则降级到下一个候选)
- 长按 / 双击 / 右键 (目前只支持单击)
