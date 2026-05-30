# Chrome GPU合成层截屏限制（2026-06-01实测）

## 问题描述
Chrome运行在GPU合成层，`CGWindowListCreateImage`（底层调用）和`computer_use` capture都截不到Chrome网页内容。

## 现象
- screencapture -x → PNG存在但内容空白
- CGWindowListCreateImage → RGBA(0,0,0,0)或只有浏览器UI框架
- Vision OCR → 0个文本区域
- computer_use capture → `capture failed`

## 根因
Chrome使用GPU合成层渲染网页内容，不画到屏幕缓冲区。这是macOS的安全限制，不是bug。

## 当前可用方案

| 能力 | 状态 | 工具 |
|------|------|------|
| 读取网页DOM | ✅ | browser_snapshot (8ms, AX Tree) |
| 点击网页元素 | ✅ | browser_click (ref索引) |
| 输入文本 | ✅ | browser_type |
| 滚动页面 | ✅ | browser_scroll |
| 截取Chrome内容 | ❌ | 无替代（DOM够用） |

## 结论
browser工具链（DOM读取+点击输入）本身就是完整闭环，截屏OCR对Chrome场景不需要。

## 验证命令
```bash
# 检查Chrome PID对应的window类型
ps aux | grep "Google Chrome" | grep -v grep

# screencapture测试（会失败）
screencapture -x /tmp/test.png
file /tmp/test.png
```
