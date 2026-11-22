#!/usr/bin/env python3
"""
step_verifier.py — per-step 动作验证闭环（UIAnchor / V-Droid 核心思想落地）

解决感知层最大的坑： agent "以为点到了、以为成功了"，但实际点空 / 状态没变。
三段式闭环：
  1. precheck  — 动作前校验目标元素当前是否还在、还是那个东西（走 4 层漏斗）
  2. action    — 调用方执行动作（回调）
  3. postcheck — 动作后强制重抓截图，验证期望状态（OCR 文字 + 整图/区域指纹）
  失败 → 定向恢复（重试一次 / 上报 human），全程 trace 落盘可审计。

设计原则（感知层铁律）：
  - 零 LLM 依赖，纯 stdlib + 复用 visual_verifier / local_detector / decision_engine
  - 任何失败都返回结构化结果，绝不抛异常
  - trace 用 buffer 批量写（避免 fd 泄漏）
  - 跨模型可移植：不依赖任何特定模型的判断

用法：
  from step_verifier import StepVerifier
  v = StepVerifier()
  r = v.run_step(
      step_id="click_submit",
      intent="提交表单",
      target_spec={"app":"Safari","window_title":"Checkout","title":"Submit","keywords":["Submit"]},
      expected_spec={"text_appears":["提交成功","Success"],"fp_changed":True},
      action_fn=lambda: click_at(920, 300),
      screenshot_before="/tmp/before.png",
      screenshot_after_fn=lambda: capture("/tmp/after.png"),
  )
  # r["ok"] / r["path"] / r["attempts"] / r["checks"]
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

_SCRIPT_DIR = Path(__file__).parent
import sys
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import visual_verifier
import local_detector

try:
    import decision_engine
except Exception:
    decision_engine = None

TRACE_PATH = Path.home() / ".hermes" / "step_trace.jsonl"
_TRACE_BUFFER: list = []
_TRACE_BUFFER_MAX = 50


def _fp(path: str) -> str:
    return visual_verifier.frame_fingerprint(path) if path and Path(path).exists() else ""


def _ocr_texts(path: str) -> List[str]:
    try:
        return [it.get("text", "") for it in visual_verifier._ocr(path)]
    except Exception:
        return []


def _text_hit(texts: List[str], needle: str) -> bool:
    n = needle.lower()
    return any(n in t.lower() for t in texts if t)


class StepVerifier:
    """per-step 事前校验 + 事后结果感知 + 状态追踪 + 定向恢复。"""

    def __init__(self, trace_path: Optional[str] = None):
        self.trace_path = Path(trace_path) if trace_path else TRACE_PATH
        self.steps: Dict[str, Dict[str, Any]] = {}

    # ---------- 1. 事前校验 ----------
    def precheck(self, target_spec: Dict[str, Any],
                 screenshot_path: str = "",
                 ax_elements: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        动作前：目标元素当前是否还在预期位置、还是那个东西。
        走 4 层漏斗找元素；找到即 ok（L0 命中自带 region_fp 一致性校验）。
        返回 {ok, reason, element, path, latency_ms}
        """
        t0 = time.time()
        result: Dict[str, Any] = {
            "ok": False, "reason": "", "element": None,
            "path": "none", "latency_ms": 0,
        }
        try:
            if decision_engine is None:
                result["reason"] = "decision_engine_unavailable"
                return result
            found = decision_engine.find_element(
                app=target_spec.get("app", ""),
                window_title=target_spec.get("window_title", ""),
                ax_elements=ax_elements,
                screenshot_path=screenshot_path,
                target_role=target_spec.get("role", ""),
                target_title=target_spec.get("title", ""),
                target_color=target_spec.get("color"),
                target_keywords=target_spec.get("keywords"),
            )
            result["path"] = found.get("path", "miss")
            result["latency_ms"] = int((time.time() - t0) * 1000)
            if found.get("found"):
                result["ok"] = True
                result["element"] = found.get("element")
                result["reason"] = "target_present"
                # 记录目标区域指纹，供事后对比
                el = found.get("element") or {}
                if screenshot_path and all(k in el for k in ("x", "y", "w", "h")):
                    try:
                        import perception_memory
                        result["region_fp_before"] = perception_memory.region_fingerprint(
                            screenshot_path, el["x"], el["y"], el["w"], el["h"]
                        )
                    except Exception:
                        pass
            else:
                result["reason"] = "target_not_found"
            self._log({"event": "precheck", "path": result["path"],
                       "ok": result["ok"], "latency_ms": result["latency_ms"]})
        except Exception as e:
            result["reason"] = "precheck_error: " + str(e)[:120]
            result["latency_ms"] = int((time.time() - t0) * 1000)
        return result

    # ---------- 2. 事后结果感知 ----------
    def postcheck(self, expected_spec: Dict[str, Any],
                  before_screenshot: str = "",
                  after_screenshot: str = "") -> Dict[str, Any]:
        """
        动作后：期望状态是否达成。
        expected_spec 支持：
          text_appears: list[str]  — 应出现的文字（OCR）
          text_gone:    list[str]  — 应消失的文字（OCR）
          fp_changed:   bool       — 整图是否应变化（指纹）
          任一维度不满足 → ok=False。OCR 读不到（空）时不误判为失败，标记 inconclusive，
          由 fp 维度决定是否通过（感知层"失败返回空、不硬判"铁律）。
        """
        t0 = time.time()
        checks: Dict[str, Any] = {}
        reasons: List[str] = []

        fp_before = _fp(before_screenshot)
        fp_after = _fp(after_screenshot)
        fp_changed = bool(fp_before and fp_after and fp_before != fp_after)
        if "fp_changed" in expected_spec:
            want = bool(expected_spec["fp_changed"])
            got = fp_changed
            checks["fp_changed"] = {"want": want, "got": got, "ok": got == want}
            if got != want:
                reasons.append("fp_changed_mismatch")

        texts_after = _ocr_texts(after_screenshot) if after_screenshot else []
        ocr_available = bool(texts_after)
        if "text_appears" in expected_spec:
            wants = expected_spec["text_appears"] or []
            missing = [w for w in wants if not _text_hit(texts_after, w)]
            if ocr_available or not wants:
                checks["text_appears"] = {"want": wants, "missing": missing,
                                          "ok": not missing}
                if missing:
                    reasons.append("text_not_appeared")
            else:
                checks["text_appears"] = {"want": wants, "status": "inconclusive_no_ocr"}
        if "text_gone" in expected_spec:
            wants = expected_spec["text_gone"] or []
            still = [w for w in wants if _text_hit(texts_after, w)]
            if ocr_available or not wants:
                checks["text_gone"] = {"want": wants, "still_present": still,
                                       "ok": not still}
                if still:
                    reasons.append("text_not_gone")
            else:
                checks["text_gone"] = {"want": wants, "status": "inconclusive_no_ocr"}

        # 综合：所有明确判定为 False 的 check 都算失败；inconclusive 不阻塞
        failed = [k for k, v in checks.items() if v.get("ok") is False]
        ok = not failed and bool(checks)  # 无期望项 = 不算通过（调用方应给期望）
        result = {
            "ok": ok,
            "reason": ",".join(reasons) if reasons else ("verified" if ok else "no_expectations"),
            "checks": checks,
            "ocr_available": ocr_available,
            "latency_ms": int((time.time() - t0) * 1000),
        }
        self._log({"event": "postcheck", "ok": ok, "reason": result["reason"],
                   "latency_ms": result["latency_ms"]})
        return result

    # ---------- 3. 完整闭环 ----------
    def run_step(self, step_id: str, intent: str,
                 target_spec: Dict[str, Any],
                 expected_spec: Dict[str, Any],
                 action_fn: Callable[[], Any],
                 screenshot_before: str = "",
                 screenshot_after_fn: Optional[Callable[[], str]] = None,
                 ax_elements: Optional[List[Dict]] = None,
                 max_retries: int = 1,
                 skip_precheck: bool = False) -> Dict[str, Any]:
        """
        闭环：precheck → action_fn → screenshot_after_fn → postcheck → (失败)retry → recovery。
        返回 {ok, step_id, intent, path, attempts, precheck, postcheck, recovery}
        """
        t0 = time.time()
        trace: Dict[str, Any] = {
            "step_id": step_id, "intent": intent, "ok": False,
            "path": "none", "attempts": 0, "precheck": None,
            "postcheck": None, "recovery": "", "latency_ms": 0,
        }
        try:
            # precheck
            if skip_precheck:
                pre = {"ok": True, "reason": "skipped", "path": "skip",
                       "element": None, "latency_ms": 0}
            else:
                pre = self.precheck(target_spec, screenshot_before, ax_elements)
            trace["precheck"] = pre
            if not pre.get("ok"):
                trace.update(path="precheck_failed", recovery="aborted_before_action",
                             reason="precheck:" + str(pre.get("reason")))
                self._log({"event": "step", **{k: trace[k] for k in
                           ("step_id", "path", "ok", "attempts")}})
                return trace

            # action + postcheck（失败可重试）
            attempts = 0
            last_post: Dict[str, Any] = {"ok": False, "reason": "not_executed"}
            while attempts <= max_retries:
                attempts += 1
                trace["attempts"] = attempts
                try:
                    action_fn()
                except Exception as e:
                    trace["recovery"] = "action_error: " + str(e)[:120]
                    break
                after_path = screenshot_after_fn() if screenshot_after_fn else ""
                last_post = self.postcheck(expected_spec, screenshot_before, after_path or "")
                trace["postcheck"] = last_post
                if last_post.get("ok"):
                    trace.update(ok=True, path="verified",
                                 recovery="none" if attempts == 1 else "recovered_by_retry")
                    break
            else:
                trace.update(path="postcheck_failed", recovery="escalate_to_human")

            trace["latency_ms"] = int((time.time() - t0) * 1000)
            self.steps[step_id] = trace
            self._log({"event": "step", **{k: trace[k] for k in
                       ("step_id", "intent", "path", "ok", "attempts", "recovery", "latency_ms")}})
            return trace
        except Exception as e:
            trace["recovery"] = "engine_error: " + str(e)[:120]
            trace["latency_ms"] = int((time.time() - t0) * 1000)
            return trace

    # ---------- 4. trace 审计 ----------
    def _log(self, entry: Dict[str, Any]):
        try:
            entry.setdefault("ts", datetime.now().isoformat())
            _TRACE_BUFFER.append(json.dumps(entry, ensure_ascii=False))
            if len(_TRACE_BUFFER) >= _TRACE_BUFFER_MAX:
                self.flush()
        except Exception:
            pass

    def flush(self):
        if not _TRACE_BUFFER:
            return
        try:
            self.trace_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.trace_path, "a") as f:
                f.write("\n".join(_TRACE_BUFFER) + "\n")
            _TRACE_BUFFER.clear()
        except Exception:
            _TRACE_BUFFER.clear()

    def trace(self, last_n: int = 20) -> List[Dict[str, Any]]:
        self.flush()
        out: List[Dict[str, Any]] = []
        try:
            if self.trace_path.exists():
                with open(self.trace_path) as f:
                    for line in f:
                        try:
                            out.append(json.loads(line))
                        except Exception:
                            continue
        except Exception:
            pass
        return out[-last_n:]


# ============================================================
# 自检（纯本地，不依赖 OCR / 屏幕 / LLM）
# ============================================================
def _selftest():
    import tempfile
    from PIL import Image, ImageDraw

    tmp = Path(tempfile.mkdtemp(prefix="stepver_"))
    v = StepVerifier(trace_path=str(tmp / "trace.jsonl"))
    checks = []

    # 造两张图：before 有 "Before"，after 整图变化
    p_before = tmp / "before.png"
    p_after = tmp / "after.png"
    Image.new("RGB", (200, 80), "white").save(p_before)
    Image.new("RGB", (200, 80), "black").save(p_after)

    # 1) postcheck: fp_changed 命中
    r = v.postcheck({"fp_changed": True}, str(p_before), str(p_after))
    checks.append(("postcheck fp_changed=True", r["checks"].get("fp_changed", {}).get("ok") is True))

    # 2) postcheck: fp_changed 应 False 但实际变了 → 判失败
    r = v.postcheck({"fp_changed": False}, str(p_before), str(p_after))
    checks.append(("postcheck fp mismatch detected", r["ok"] is False))

    # 3) postcheck: 无期望 → 不误判为通过
    r = v.postcheck({}, str(p_before), str(p_after))
    checks.append(("postcheck empty expect not ok", r["ok"] is False))

    # 4) run_step: precheck 失败 → 不执行动作
    called = {"n": 0}
    def action():
        called["n"] += 1
    r = v.run_step(
        "s1", "测试-前校验失败",
        target_spec={"app": "NoSuchApp__xyz", "window_title": "___none", "title": "__none__"},
        expected_spec={"fp_changed": True},
        action_fn=action,
        skip_precheck=False,
    )
    # 前校验用真实 decision_engine：找不到 → aborted（或引擎不可用也 aborted）
    checks.append(("run_step aborts on precheck fail", r["path"] in ("precheck_failed",) and called["n"] == 0))

    # 5) run_step: skip_precheck → 动作执行 + 事后验证通过（先写 before，再 action 改图）
    cur = {"path": str(p_before)}
    def action2():
        # 生成变化后的新图（新文件避免缓存）
        newp = tmp / f"after_{called['n']}.png"
        Image.new("RGB", (200, 80), "black").save(newp)
        cur["path"] = str(newp)
        called["n"] += 1
    r = v.run_step(
        "s2", "测试-闭环验证通过",
        target_spec={}, expected_spec={"fp_changed": True},
        action_fn=action2,
        screenshot_before=str(p_before),
        screenshot_after_fn=lambda: cur["path"],
        skip_precheck=True,
    )
    checks.append(("run_step verified via retry", r["ok"] is True and r["path"] == "verified"))

    # 6) trace 落盘读回
    tr = v.trace()
    checks.append(("trace persisted", len(tr) >= 5))

    ok = sum(1 for _, p in checks if p)
    for name, passed in checks:
        print(("  PASS " if passed else "  FAIL ") + name)
    print(f"\n{ok}/{len(checks)} passed")
    return ok == len(checks)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(0 if _selftest() else 1)
    else:
        print(__doc__)
