# TOCTOU Attacks on Computer-Use Agents (arXiv 2604.18860, Apr 20 2026)

## 基本信息
- **标题**: Temporal UI State Inconsistency in Desktop GUI Agents: Formalizing and Defending Against TOCTOU Attacks on Computer-Use Agents
- **作者**: Wenpeng Xu
- **来源**: arXiv 2604.18860, cs.CR
- **提交**: Apr 20, 2026

## 核心发现
GUI agents operating in screenshot→click loops have an **observation-to-action gap** (avg **6.51s** on OSWorld workloads). This creates a Time-Of-Check, Time-Of-Use (TOCTOU) window during which an unprivileged attacker can manipulate UI state.

Concept formalized as **Visual Atomicity Violation**.

## 三个攻击原语

| # | 攻击 | 描述 | 成功率 | 视觉痕迹 |
|---|------|------|--------|---------|
| A | Notification Overlay Hijack | 通知覆盖层劫持点击 | 高 | 临时覆盖 |
| B | Window Focus Manipulation | 窗口焦点劫持 | **100%** | 零视觉痕迹 |
| C | Web DOM Injection | DOM 注入改变页面内容 | 高 | 零视觉痕迹(屏幕级) |

**Primitive B** is the closest desktop analog to Android Action Rebinding — achieves 100% action-redirection with zero visual evidence at the observation time.

## PUSV Defense (Pre-execution UI State Verification)

三层防御，在每次 action 执行前立即 re-verify UI 状态：

| 层级 | 方法 | 耗时 | 检出率 |
|------|------|------|--------|
| L1 | Masked pixel SSIM at click target | <0.1s | 部分 |
| L2a | Global screenshot diff | 近零 | 覆盖 A 类 |
| L2b | X Window snapshot diff | 近零 | 覆盖 B 类 |
| **全部** | L1+L2a+L2b | **<0.1s total** | **100% AIR** (A+B), **零假阳性** |

**限制**: Primitive C (Web DOM Injection) 超出视觉检测范围，PUSV 对此 **0% AIR**。需要 OS+DOM defense-in-depth。

## 对 Hermes 的影响

### DRY_RUN=True → False 过渡条件
当前 handler 60s cooldown + handler 处理周期 (~8s) = **总和 ~68s TOCTOU window**。在切换 DRY_RUN=False 前必须实现 pre-execution verification：
- L1: SSIM between consecutive screenshot regions (PIL.ImageChops.difference + numpy)
- L2a: Full-frame pixel diff (numpy array subtraction)
- L2b: macOS Accessibility API window state snapshot (AX API via PyObjC)

### 架构验证
- PUSV 的 "no single layer alone achieves full coverage" → 验证 handler 多层检测（场景分类+否定检测+CRITICAL_KEYWORDS）设计方向正确
- 极低开销 (<0.1s) 意味着可在每次 action dispatch 前运行不卡顿
- DOM injection blind spot → 纯视觉 agent 需要额外机制（CDP DOM 检查/浏览器扩展）

## 参考文献
- Paper: https://arxiv.org/abs/2604.18860
- 相关: Android Action Rebinding (GUI agent TOCTOU 前身)
- 相关: OS-World (6.51s gap 测量来源)
