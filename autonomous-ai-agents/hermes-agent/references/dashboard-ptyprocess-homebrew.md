# Dashboard ptyprocess 问题（Homebrew Python）

## 症状
网页 UI `/chat` 提示：
```
Chat unavailable: The `ptyprocess` package is missing.
Install with: pip install ptyprocess
```

## 根因
Dashboard（`hermes dashboard`）由 Homebrew Python 运行，不走 venv：
```
/opt/homebrew/Cellar/python@3.13/3.13.3_1/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python -m hermes_cli.main dashboard
```

在 venv 里 `pip install ptyprocess` 对 Dashboard **无效**。

## 修复
```bash
# 找到 Homebrew Python 的 pip3 路径
/opt/homebrew/Cellar/python@3.13/3.13.3_1/Frameworks/Python.framework/Versions/3.13/bin/pip3 install ptyprocess --break-system-packages
```

装完后需要**重启 Dashboard**（kill 旧 PID，新起一个）。

## 验证
刷新 Dashboard `/chat` 页面即可。
