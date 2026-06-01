# Direction B — OSU-NLP YAML cross-domain dedup technique

## Canonical source: scripts/direction-b-scan.py

The script's `KNOWN_ARXIV` set is the **single source of truth** for paper coverage.
Do not rely on filesystem grep (searching learning_log + reference files) for dedup —
KNOWN_ARXIV may have recorded papers that were never written to reference files.

**Workflow**: Run `python3 scripts/direction-b-scan.py --incremental` and trust its
[NEW]/[KNOWN] tagging over manual grep.

## Cross-domain security paper discovery (2026-06-02)

When direction B is saturated for GUI grounding papers, **do not skip OSU-NLP YAML
entirely**. Run a targeted security scan:

```
python3 scripts/direction-b-scan.py 2>/dev/null | grep -E "\[NEW\]"
```

Security papers (safety/guardrail/red teaming/security benchmark) use different
keywords from standard GUI grounding papers. They pass the keyword scoring
threshold (>=2) via terms like `security`, `safety`, `red teaming`, `guardrail`,
`benchmark`, but are easily missed by a direction-B-only scanning strategy.

**Examples found via cross-domain scan**:
- AutoElicit (2602.08235) — safety benchmark (originally security, not GUI grounding)
- MisActBench (2602.08995) — action-level alignment (safety domain)
- AdvCUA (2510.06607) — MITRE ATT&CK CUA benchmark (security domain)
- RiOSWorld (2506.00618) — misuse risk benchmark (safety domain)

## Saturation vs cross-domain: key insight

Saturation is **domain-specific**, not global:
- Direction B (GUI grounding) can be saturated while security/safety papers
  still yield new discoveries.
- Solution: add a `--security-targeted` flag to the script, or run full scan
  and filter by security keyword patterns.

## KNOWN_ARXIV maintenance

When a new paper is found via cross-domain scan:
1. Add its arxiv ID to `KNOWN_ARXIV` in `scripts/direction-b-scan.py`
2. Log it in `learning_log.md` (no need for a separate reference file unless
   it significantly changes Hermes architecture)
3. The script's --debug mode shows KNOWN papers too, useful for verification
