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

try:
    import screen_parser
except Exception:
    screen_parser = None

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


def _box_iou(a, b) -> float:
    """两个 [x, y, w, h] 框的交并比；任一非法返回 0。"""
    try:
        ax, ay, aw, ah = [float(v) for v in a]
        bx, by, bw, bh = [float(v) for v in b]
        if aw <= 0 or ah <= 0 or bw <= 0 or bh <= 0:
            return 0.0
        ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
        iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
        inter = ix * iy
        union = aw * ah + bw * bh - inter
        return inter / union if union > 0 else 0.0
    except Exception:
        return 0.0


class StepVerifier:
    """per-step 事前校验 + 事后结果感知 + 状态追踪 + 定向恢复。"""

    def __init__(self, trace_path: Optional[str] = None):
        self.trace_path = Path(trace_path) if trace_path else TRACE_PATH
        self.steps: Dict[str, Dict[str, Any]] = {}

    # ---------- 1. 事前校验 ----------
    def precheck(self, target_spec: Dict[str, Any],
                 screenshot_path: str = "",
                 ax_elements: Optional[List[Dict]] = None,
                 guard_spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        动作前：目标元素当前是否还在预期位置、还是那个东西。
        走 4 层漏斗找元素；找到后若给 guard_spec 再做一次陈旧目标核验
        （HCU 的 action guard：身份不符直接拒绝，绝不"找相似元素"凑合）。
        guard_spec 支持：title / box=[x,y,w,h] / min_iou=0.45 / role
        返回 {ok, reason, element, path, latency_ms, guard_violations}
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
                # HCU 式 action guard：重新核验目标身份，失效直接拒绝（绝不找相似元素凑合）
                violations: List[str] = []
                if guard_spec:
                    want_title = guard_spec.get("title")
                    if want_title:
                        labels = [str(v) for k, v in el.items()
                                  if k in ("title", "label", "text", "name") and v]
                        if labels and not _text_hit(labels, want_title):
                            violations.append("identity_changed")
                    want_box = guard_spec.get("box")
                    if want_box and all(k in el for k in ("x", "y", "w", "h")):
                        iou = _box_iou(want_box, [el["x"], el["y"], el["w"], el["h"]])
                        result["guard_iou"] = round(iou, 3)
                        if iou < float(guard_spec.get("min_iou", 0.45)):
                            violations.append("moved")
                    want_role = guard_spec.get("role")
                    if want_role and el.get("role") and \
                            str(el["role"]).lower() != str(want_role).lower():
                        violations.append("role_changed")
                if violations:
                    result["ok"] = False
                    result["reason"] = "stale_target:" + ",".join(violations)
                    result["guard_violations"] = violations
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
        # LGWM 式异常转移检测：变化本身不算成功，冒出禁止信号即判可疑。
        # 例：点"提交订单"后出现"验证码/登录/风控"→ 动作被拦截，不能算 verified。
        if "unexpected_appears" in expected_spec:
            bads = expected_spec["unexpected_appears"] or []
            hits = [b for b in bads if _text_hit(texts_after, b)]
            if ocr_available or not bads:
                checks["unexpected_appears"] = {"blocked": bads, "hits": hits,
                                                "ok": not hits}
                if hits:
                    reasons.append("unexpected_appeared")
            else:
                checks["unexpected_appears"] = {"blocked": bads,
                                                "status": "inconclusive_no_ocr"}

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

    # ---------- 2b. 最强版：结构化元素级 diff 验证 ----------
    def postcheck_structural(self, expected_spec: Dict[str, Any],
                             before_screenshot: str = "",
                             after_screenshot: str = "") -> Dict[str, Any]:
        """
        最强验证路径（UIAnchor 式）：不比整图 md5，而是把前后两屏解析成结构化元素清单，
        做元素级 diff，精确回答"哪个按钮消失/哪个文字出现/哪个框变了"。
        expected_spec 支持：
          added_min / removed_min / changed_min : int  — 元素级变化数量下限
          text_appears / text_gone : list[str]          — 文字（从 diff 的 label 判定）
          any_change : bool                            — 只要有变化即可
        screen_parser 不可用时自动降级到普通 postcheck。
        """
        t0 = time.time()
        if not screen_parser or not (before_screenshot and after_screenshot):
            return self.postcheck(expected_spec, before_screenshot, after_screenshot)
        try:
            a = screen_parser.parse_screen(before_screenshot)
            b = screen_parser.parse_screen(after_screenshot)
            d = screen_parser.diff_screens(a, b, inspect_path=after_screenshot)
            if not d.get("ok"):
                return self.postcheck(expected_spec, before_screenshot, after_screenshot)
            s = d["summary"]
            checks: Dict[str, Any] = {}
            # 兼容旧接口：fp_changed 用整图指纹兜底（结构化 diff 之外的快速信号）
            if "fp_changed" in expected_spec:
                fb, fa = _fp(before_screenshot), _fp(after_screenshot)
                got = bool(fb and fa and fb != fa)
                want = bool(expected_spec["fp_changed"])
                checks["fp_changed"] = {"want": want, "got": got, "ok": got == want}
            for key in ("added", "removed", "changed"):
                want_key = key + "_min"
                if want_key in expected_spec:
                    want, got = int(expected_spec[want_key]), s.get(key, 0)
                    checks[want_key] = {"want_min": want, "got": got, "ok": got >= want}
            if "any_change" in expected_spec:
                total = s["added"] + s["removed"] + s["changed"]
                want, got = bool(expected_spec["any_change"]), total > 0
                checks["any_change"] = {"want": want, "got": got, "ok": got == want}
            labels_after = [e.get("label", "") for e in b.get("elements", []) if e.get("label")]
            labels_before = [e.get("label", "") for e in a.get("elements", []) if e.get("label")]
            if "text_appears" in expected_spec:
                wants = expected_spec["text_appears"] or []
                missing = [w for w in wants if not _text_hit(labels_after, w)]
                checks["text_appears"] = {"want": wants, "missing": missing, "ok": not missing}
            if "text_gone" in expected_spec:
                wants = expected_spec["text_gone"] or []
                persisted = [w for w in wants if _text_hit(labels_after, w) and _text_hit(labels_before, w)]
                checks["text_gone"] = {"want": wants, "still_present": persisted, "ok": not persisted}
            if "unexpected_appears" in expected_spec:
                bads = expected_spec["unexpected_appears"] or []
                evidence_labels = list(labels_after)
                for ins in (d.get("inspected") or []):
                    if isinstance(ins, dict) and ins.get("text"):
                        evidence_labels.append(str(ins["text"]))
                hits = [b for b in bads if _text_hit(evidence_labels, b)]
                checks["unexpected_appears"] = {"blocked": bads, "hits": hits,
                                                "ok": not hits}
                if hits:
                    reasons.append("unexpected_appeared")
            failed = [k for k, v in checks.items() if v.get("ok") is False]
            ok = not failed and bool(checks)
            result = {
                "ok": ok,
                "reason": "structural_ok" if ok else "structural_mismatch:" + ",".join(failed + reasons),
                "mode": "structural", "diff_summary": s,
                "focus_regions": d.get("focus_regions", []),
                "inspected": d.get("inspected", []),
                "checks": checks, "latency_ms": int((time.time() - t0) * 1000),
            }
            self._log({"event": "postcheck_structural", "ok": ok,
                       "diff": s, "latency_ms": result["latency_ms"]})
            return result
        except Exception as e:
            fb = self.postcheck(expected_spec, before_screenshot, after_screenshot)
            fb["structural_fallback_reason"] = str(e)[:120]
            return fb

    # ---------- 3. 完整闭环 ----------
    def run_step(self, step_id: str, intent: str,
                 target_spec: Dict[str, Any],
                 expected_spec: Dict[str, Any],
                 action_fn: Callable[[], Any],
                 screenshot_before: str = "",
                 screenshot_after_fn: Optional[Callable[[], str]] = None,
                 ax_elements: Optional[List[Dict]] = None,
                 max_retries: int = 1,
                 skip_precheck: bool = False,
                 structural: bool = True,
                 guard_spec: Optional[Dict[str, Any]] = None,
                 verify_web_fn: Optional[Callable[[], Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        闭环：precheck → (guard) → action_fn → screenshot_after_fn → postcheck
              → (web evidence) → (失败)retry → recovery。
        guard_spec: HCU 式陈旧目标拦截，传给 precheck。
        verify_web_fn: Tsaagan 式结构化证据块，返回 {url_delta, console_errors,
                       network_failures}；后两者非空即判本步失败。
        返回 {ok, step_id, intent, path, attempts, precheck, postcheck, evidence, recovery}
        """
        t0 = time.time()
        trace: Dict[str, Any] = {
            "step_id": step_id, "intent": intent, "ok": False,
            "path": "none", "attempts": 0, "precheck": None,
            "postcheck": None, "recovery": "", "latency_ms": 0,
            "evidence": {"focus_regions": [], "inspected": [], "web": None},
        }
        try:
            # precheck（含 HCU 式陈旧目标 guard）
            if skip_precheck:
                pre = {"ok": True, "reason": "skipped", "path": "skip",
                       "element": None, "latency_ms": 0}
            else:
                pre = self.precheck(target_spec, screenshot_before, ax_elements,
                                    guard_spec=guard_spec)
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
                # structural=True 走元素级 diff（最强），否则走整图指纹（快）
                if structural:
                    last_post = self.postcheck_structural(
                        expected_spec, screenshot_before, after_path or "")
                else:
                    last_post = self.postcheck(
                        expected_spec, screenshot_before, after_path or "")
                trace["postcheck"] = last_post
                trace["evidence"]["focus_regions"] = last_post.get("focus_regions", [])
                trace["evidence"]["inspected"] = last_post.get("inspected", [])
                # Tsaagan 式结构化证据：console 错误 / 失败网络请求直接否决成功
                if verify_web_fn:
                    try:
                        web = verify_web_fn() or {}
                    except Exception as e:
                        web = {"error": str(e)[:120]}
                    trace["evidence"]["web"] = web
                    wchecks: Dict[str, Any] = {}
                    for key in ("console_errors", "network_failures"):
                        if key in web:
                            items = web.get(key) or []
                            wchecks[key] = {"count": len(items), "ok": not items}
                    if wchecks:
                        last_post.setdefault("checks", {}).update(wchecks)
                        bad = [k for k, v in wchecks.items() if v.get("ok") is False]
                        if bad:
                            last_post["ok"] = False
                            last_post["reason"] = \
                                str(last_post.get("reason", "")) + ",web_evidence:" + ",".join(bad)
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

    # 7) 结构化模式：any_change 命中（真实元素级 diff，必须用有结构的图）
    cur2 = {"path": str(p_before)}
    struct_a = tmp / "struct_a.png"
    struct_b = tmp / "struct_b.png"
    im_a = Image.new("RGB", (300, 200), "white")
    ImageDraw.Draw(im_a).rectangle([50, 50, 150, 90], fill="red")
    im_a.save(struct_a)
    im_b = Image.new("RGB", (300, 200), "white")
    ImageDraw.Draw(im_b).rectangle([180, 110, 260, 160], fill="green")
    im_b.save(struct_b)
    def action3():
        cur2["path"] = str(struct_b)
        called["n"] += 1
    r = v.run_step(
        "s3", "测试-结构化diff验证",
        target_spec={}, expected_spec={"any_change": True},
        action_fn=action3, screenshot_before=str(struct_a),
        screenshot_after_fn=lambda: cur2["path"],
        skip_precheck=True, structural=True,
    )
    checks.append(("run_step structural diff", r.get("postcheck", {}).get("mode") == "structural" and r["ok"] is True))

    # 8) HCU guard：陈旧目标直接拦截（mock find_element，纯本地）
    orig_find = decision_engine.find_element if decision_engine else None
    if decision_engine:
        decision_engine.find_element = lambda **kw: {
            "found": True, "path": "l0",
            "element": {"title": "Submit", "role": "button",
                        "x": 10, "y": 20, "w": 100, "h": 40}}
    try:
        g = v.precheck({"title": "Submit"},
                       guard_spec={"title": "Submit", "box": [10, 20, 100, 40]})
        checks.append(("guard accepts same target", g["ok"] is True))
        g2 = v.precheck({"title": "Submit"},
                        guard_spec={"title": "Cancel", "box": [10, 20, 100, 40]})
        checks.append(("guard rejects changed identity",
                       g2["ok"] is False and
                       "identity_changed" in (g2.get("guard_violations") or [])))
        g3 = v.precheck({"title": "Submit"},
                        guard_spec={"title": "Submit", "box": [500, 500, 100, 40]})
        checks.append(("guard rejects moved target",
                       g3["ok"] is False and
                       "moved" in (g3.get("guard_violations") or [])))
    finally:
        if decision_engine and orig_find:
            decision_engine.find_element = orig_find

    # 9) LGWM 式异常转移：禁止信号出现即否决（mock OCR）
    orig_ocr = visual_verifier._ocr
    visual_verifier._ocr = lambda p: [{"text": "Success"}, {"text": "captcha blocked"}]
    try:
        r = v.postcheck({"text_appears": ["Success"],
                         "unexpected_appears": ["captcha"]},
                        str(p_before), str(p_after))
        checks.append(("unexpected signal vetoes success",
                       r["ok"] is False and
                       r["checks"]["unexpected_appears"]["ok"] is False))
    finally:
        visual_verifier._ocr = orig_ocr

    # 10) Tsaagan 式 web 证据：失败网络请求否决成功 + trace 留证
    def bad_web_fn():
        return {"url_delta": "/checkout -> /login", "console_errors": [],
                "network_failures": [{"url": "POST /pay", "status": 500}]}
    cur3 = {"path": str(p_before)}
    def action4():
        newp = tmp / f"web_{called['n']}.png"
        Image.new("RGB", (200, 80), "black").save(newp)
        cur3["path"] = str(newp)
        called["n"] += 1
    r = v.run_step(
        "s4", "测试-web证据否决",
        target_spec={}, expected_spec={"fp_changed": True},
        action_fn=action4, screenshot_before=str(p_before),
        screenshot_after_fn=lambda: cur3["path"],
        skip_precheck=True, verify_web_fn=bad_web_fn, max_retries=1,
    )
    checks.append(("web evidence vetoes + recorded",
                   r["ok"] is False and
                   bool((r.get("evidence", {}).get("web") or {}).get("network_failures"))))

    # 6) trace 落盘读回
    tr = v.trace()
    checks.append(("trace persisted", len(tr) >= 9))

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
