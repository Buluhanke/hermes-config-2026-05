# Per-model tool-call benchmark harness

How to compare Hermes models' tool-calling reliability **without touching global
config** — run each candidate through one forced-tool task and record success/failure.

## Why forced tool use
A plain "what is X?" prompt can be answered from the model's training memory, so it
tells you nothing about whether the model actually invokes tools in an agent loop.
Force a tool by requiring it to **read a file it cannot know from memory**:

```
Read the file at /Users/aimac/.hermes/config.yaml using your file-reading tool
(do NOT answer from memory). Report the exact string value set for model.default.
Reply with just that value and the name of the tool you used.
```

Correct answer is `tencent/hy3:free` (the live config value). A model that answers
without calling `read_file` is failing the test.

## Command shape (verified)
```bash
hermes chat -Q -m "<model>" --provider <provider> \
  --query-file /tmp/prompt.txt --max-turns 3 --run-budget 120
```
- `-Q` quiet: only final response + session info, good for parsing.
- `--query-file` keeps the prompt verbatim (no shell interpolation of `$`, backticks).
- `--max-turns 3 --run-budget 120` bounds a single run to ~2 min.

## CRITICAL pitfall — free models need `--provider nous`
Free Nous Portal models resolve to **OpenRouter** under `auto` provider mode and
return `HTTP 402: billing or credits exhausted` even though they are free on Nous.
Always pin the provider:

```bash
hermes chat -Q -m "meituan/longcat-2.0" --provider nous --query-file /tmp/prompt.txt
```

Without `--provider nous`, only the model matching your `config.yaml` provider
(e.g. `hy3:free` when provider is `nous`) succeeds; the other five 402.

## The 6 free Nous Portal models (verified 2026-08-27, portal.nousresearch.com/models)
| Model id | Vendor |
|---|---|
| `tencent/hy3:free` | Tencent Hunyuan 3 (295B-A21B, 256K ctx, agent-tuned) |
| `meituan/longcat-2.0` | Meituan (1M ctx) |
| `upstage/solar-pro-4` | Upstage (long-doc specialist) |
| `stepfun/step-3.7-flash` | StepFun (image input, fastest) |
| `poolside/laguna-s-2.1` | Poolside (strong agentic coding; tool-schema friction in 3rd-party harnesses) |
| `poolside/laguna-xs-2.1` | Poolside (smaller) |

Note: this list changes — fetch live from `portal.nousresearch.com/models`
("Free Models" block) rather than trusting this snapshot.

## Loop recipe
```bash
for m in tencent/hy3:free meituan/longcat-2.0 upstage/solar-pro-4 \
         stepfun/step-3.7-flash poolside/laguna-s-2.1 poolside/laguna-xs-2.1; do
  echo "===== $m ====="
  hermes chat -Q -m "$m" --provider nous --query-file /tmp/prompt.txt \
    --max-turns 3 --run-budget 120 2>&1 | tail -12
done
```
Run sequentially (not parallel) to avoid tripping the free tier's rate limits.
