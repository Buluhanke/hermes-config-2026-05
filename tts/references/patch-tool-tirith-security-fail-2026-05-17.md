# patch 工具对 tirith_security.py 的异常行为

**日期**：2026-05-17

## 现象

对 `tools/tirith_security.py` 使用 patch 工具（mode=replace），预期只替换一行，实际上：

- 文件从 ~295 行膨胀到 360 行
- 出现了三处 `elif p.returncode == 2:` 的重复代码块
- 变量名错乱（`p.returndate` 而非 `p.returncode`）
- 新增了未定义的 `_translate_filling` 调用

## 根因

未确认。可能是：
1. patch 工具的 fuzzy matching 在处理含大量 f-string 和多行字符串的 Python 文件时匹配区域过大
2. 文件有隐藏的分隔符冲突
3. patch 工具对 `replace_all=true` 的行为在某些情况下异常

## 教训

**不要用 patch 工具修改 tirith_security.py**。如果要改：

```python
# 正确做法：用 execute_code 写 Python 脚本直接修改文件
# 不依赖 patch 工具的字符串匹配
```

## 当前状态

tirith_security.py 的汉化（"Pipe to interpreter" → "管道直连解释器"）未完成，该文件当前处于损坏状态，需要：
1. `git checkout tools/tirith_security.py` 恢复原始状态
2. 或用 Python 脚本直接写入正确的修改版本

## 替代方案

如需对 tirith 输出做翻译，不要改 `tirith_security.py` 本身，而是在调用层（`approval.py` / `terminal_tool.py`）处理输出字符串的翻译——这些文件 patch 工具行为正常。