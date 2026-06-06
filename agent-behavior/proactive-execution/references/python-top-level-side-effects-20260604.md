# Python 模块顶层副作用 = 隐形"看起来像 main 被触发"陷阱

## 事件时间
2026-06-04

## 场景
建立 `~/.hermes/scripts/` 下的节奏门控（`rhythm.py` + `hermes_notify.py`）。

`rhythm.py` 我从教科书式代码搬过来，**底部有"使用示例"段**：

```python
# 使用示例
ctx = get_rhythm()
print(f"当前时区: {ctx.zone.value}, 可主动: {ctx.should_proactive}")
print(f"发送 medium 消息: {should_send_message('medium')}")
```

→ 没有 `if __name__ == "__main__":` 守卫。这两行是**模块顶层**代码。

## 触发链

1. `hermes_notify.py` 顶部 `import rhythm` 加载 `rhythm.py`
2. 加载过程执行模块顶层所有可执行语句
3. `print(...)` 跑出"当前时区: work, ..."
4. `should_send_message("medium")` 跑出"发送 medium 消息: True"
5. `hermes_notify` 自己 import 也带 main 块 → 主块又跑一遍
6. 用户看到 `python3 -c "import hermes_notify"` 输出那 4 行

## 我走过的弯路（5+ 轮）

1. 怀疑 main 守卫失效 → `tail` 文件 → 守卫存在
2. 怀疑有 `__pycache__` 旧 .pyc → `find` → 没有
3. 怀疑 `PYTHONSTARTUP` / `sitecustomize` → `echo $PYTHONSTARTUP` → 空
4. 怀疑 sys.path 里有同名模块 → `find_spec` → 唯一
5. 怀疑是 importlib 状态污染 → `reload` → 同样问题
6. 怀疑 `__name__` 真的等于 `__main__` → `print(hermes_notify.__name__)` → 是 `hermes_notify`
7. 最后才意识到：**这不是 main 块在跑，是模块顶层 print 在跑**——和 main 守卫无关

## 根因总结

- **模块顶层** ≠ `__main__` 块
- `if __name__ == "__main__":` 守卫只保护 `if` 下缩进的内容
- **模块顶层 print / 调用** 在 import 时**永远会跑**
- 教科书 / 范例代码几乎都不带"使用示例"守卫，因为它们是 `python script.py` 直跑，不被 import

## 修复

把 `rhythm.py` 的示例段包进守卫：

```python
if __name__ == "__main__":
    ctx = get_rhythm()
    print(f"当前时区: {ctx.zone.value}, 可主动: {ctx.should_proactive}")
    print(f"发送 medium 消息: {should_send_message('medium')}")
```

## 自检 SOP（保存新 .py 后必走）

```bash
# 1) 找一个不会被命中的名字导入
python3 -c "import <module_name>" 2>&1 | head -10
# 期望：无输出 / 只有必要副作用（logging、模块级变量初始化等）

# 2) 看到示例文案 / "---" / "演示" / "测试" / "自测" → 缺守卫
```

## 教训

- 教科书代码 → 默认**有 top-level 示例副作用** → 搬到自己 `*.py` 时必须加守卫
- "看起来像 main 跑了" 的判断几乎都是错的——大概率是顶层副作用
- 修之前先**做最简反证**：`python3 -c "import X"` 看 import 阶段输出，比读源码快

## 相关

- `proactive-execution` 规则18（`if __name__ == "__main__":` 守卫必加）
- `notification-rhythm-pipeline` 完整链路（rhythm + notify + drain + cron）
