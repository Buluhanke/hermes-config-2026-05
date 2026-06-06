# Chrome debug profile 磁盘占用诊断（2026-06-04）

## 背景

Hermes 寄生调试 Chrome 的 user-data-dir 位于 `~/.hermes/chrome-debug`。这个 Chrome 装了好几个 on-device AI 模型（Chrome 152+ 默认下载 Gemini Nano），几个月不清理会涨到 5+ GB。

用户经常误以为"5.6GB = 6 个 AI 站登录态"，**实际上登录态 < 10MB**。**别瞎清，否则要重登 6 个 AI 站**。

## 完整诊断脚本

```bash
# 1. 总大小
echo "=== 总大小 ==="
du -sh ~/.hermes/chrome-debug

# 2. 内部 TOP 15
echo "=== 内部 TOP 15 ==="
du -sh ~/.hermes/chrome-debug/* 2>/dev/null | sort -hr | head -15

# 3. 登录态实际大小
echo "=== 登录态实际大小 ==="
ls -la ~/.hermes/chrome-debug/Default/Cookies \
       ~/.hermes/chrome-debug/Default/"Local Storage"/ \
       ~/.hermes/chrome-debug/Default/"Session Storage"/ 2>/dev/null

# 4. 进程占用（确认 Chrome 是不是还在跑）
echo "=== Chrome 进程 ==="
ps aux | grep -i chrome | grep "user-data-dir.*chrome-debug" | grep -v grep | head -3
```

## 5.6GB 真实拆解（2026-06-04 实测）

| 大头 | 大小 | 是啥 | 跟登录态有关？ | 删的风险 |
|---|---|---|---|---|
| `OptGuideOnDeviceModel/` | **4.0GB** | Gemini Nano 本地 LLM | ❌ | 零 |
| `Default/` 整体 | 807MB | 浏览器配置/历史/缓存 | 部分 | 中（可能丢登录态） |
| `Extensions/` | 228MB | 装的扩展 | ❌ | 零（重装扩展） |
| `component_crx_cache/` | 146MB | 组件下载缓存 | ❌ | 零 |
| `screen_ai/` | 123MB | 屏幕 AI 模型 | ❌ | 零 |
| `OptGuideOnDeviceClassifierModel/` | 120MB | 分类模型 | ❌ | 零 |
| `optimization_guide_model_store/` | 76MB | 优化指南 | ❌ | 零 |
| `WasmTtsEngine/` | 22MB | 语音合成引擎 | ❌ | 零 |
| `Safe Browsing/` | 22MB | 反钓鱼黑名单 | ❌ | 零 |
| `History` | 12MB | 浏览历史 | ❌ | 零 |
| `GraphiteDawnCache/` | 8.2MB | GPU 编译缓存 | ❌ | 零 |
| `Default/Cookies` | **~30KB** | **6 个站登录态** | ✅ | **删了重登** |
| `Default/Local Storage/` | **~5MB** | **session 数据** | ✅ | **删了重登** |

**真相**：5.6GB 里 **5GB 是无关模型**，**10MB 才是登录态**。

## 安全清理脚本（保留登录态，删 4.5GB on-device AI）

```bash
# 清理前先停 Chrome（避免删了文件还被占用）
pkill -f "chrome.*user-data-dir.*chrome-debug" 2>/dev/null
sleep 2

# 删除 4.5GB on-device AI（零登录态丢失）
rm -rf ~/.hermes/chrome-debug/OptGuideOnDeviceModel
rm -rf ~/.hermes/chrome-debug/OptGuideOnDeviceClassifierModel
rm -rf ~/.hermes/chrome-debug/optimization_guide_model_store
rm -rf ~/.hermes/chrome-debug/screen_ai
rm -rf ~/.hermes/chrome-debug/component_crx_cache
rm -rf ~/.hermes/chrome-debug/Safe\ Browsing
rm -rf ~/.hermes/chrome-debug/WasmTtsEngine
rm -rf ~/.hermes/chrome-debug/GraphiteDawnCache

# 再清理各代 Default 里的缓存（保留 Cookies 和 Local Storage）
rm -rf ~/.hermes/chrome-debug/Default/Code\ Cache
rm -rf ~/.hermes/chrome-debug/Default/GPUCache
rm -rf ~/.hermes/chrome-debug/Default/DawnGraphiteCache
rm -rf ~/.hermes/chrome-debug/Default/DawnWebGPUCache
rm -rf ~/.hermes/chrome-debug/Default/blob_storage
rm -rf ~/.hermes/chrome-debug/Default/Shared\ Dictionary

# 重启 Chrome
open -a "Google Chrome" --args \
  --user-data-dir=/Users/aimac/.hermes/chrome-debug \
  --remote-debugging-port=9333 \
  --no-first-run --no-default-browser-check \
  --load-extension=/Users/aimac/.hermes/mcp-chrome-extension

sleep 3
du -sh ~/.hermes/chrome-debug
# 应该从 5.6GB 降到 1-1.5GB
```

## Chrome 152+ On-Device AI 用途速查

| 用途 | 触发场景 | 用户感不感觉得到 |
|---|---|---|
| **整页翻译** | 右键 → 翻译成中文 | ✅ 强（替代云端 Google 翻译） |
| **AI 摘要** | 长文章/报告一键 TL;DR | ✅ 中 |
| **AI 写作/改写** | Gmail "帮我写" | ✅ 弱（用 Gmail 才知道） |
| **语言检测** | 中英混输自动判语言 | ⚠️ 几乎不知道 |
| **Proofreader** | 邮件实时挑错 | ⚠️ 不开 Gmail 用不到 |
| **Screen AI** | 无障碍读屏（盲人辅助） | ❌ 普通用户无感 |

## 关键判断

- **对 Hermes Agent 用户**：本地 AI 模型**完全不影响** Hermes 的云端 AI 站对话（MiniMax-M3 / ChatGPT / Gemini 等），它们走 CDP 不走 Chrome 内置 API
- **删 4.5GB 模型 = Hermes 零影响** ✅
- **删 Default/Cookies = 6 个 AI 站全重登** ❌

## 配合规则

- `chrome-cdp-automation` SKILL.md "Chrome debug profile 磁盘占用诊断" 章节
- `proactive-execution` 规则15（先识别具体对象再答）
- `proactive-execution/references/du-disk-investigation-sop.md`（通用 du SOP）
