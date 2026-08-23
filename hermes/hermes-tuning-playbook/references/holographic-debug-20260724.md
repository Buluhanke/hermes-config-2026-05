# Holographic Memory Debugging — 2026-07-24

## Root Cause: 3 Independent Bugs

### Bug 1: FTS5 AND-join Failure
- FTS5 query `"AI"` → 0 candidates (AND-join requires ALL tokens in same column)
- FTS5 query `"arxiv"` → 224 chars ✓ (multi-char, content matches)
- FTS5 query `"Mac"` → 3 candidates found (actually works)
- Root cause: FTS5 tokenization drops single-char tokens AND/OR the content column doesn't index the terms that match

### Bug 2: HRR Dimension Mismatch (THE CRASH)
- `bytes_to_phases()` NOT passing `dim` parameter
- Query vector: 1024 dim (from `encode_text(query, self.hrr_dim)`)
- Stored vectors: 384 dim (3072 bytes / 8 = 384)
- `np.cos(a - b)` → shapes (1024,) vs (384,) → ValueError
- Crash happens BEFORE LIKE fallback can execute
- 6 facts have 384-dim vectors, rest have NULL → only those 6 crash

### Bug 3: LIKE Fallback Never Triggered
- Bug 2 crashes before `_like_candidates()` is called
- Fallback logic present but unreachable due to upstream crash

## Verification Commands

```python
# Test search directly
from memory.holographic import HolographicMemoryProvider
cfg = {'db_path': '/Users/aimac/.hermes/memory_store.db', 'hrr_dim': 1024, 'hrr_weight': 0.3}
hp = HolographicMemoryProvider(config=cfg); hp.initialize(session_id='test')

# FTS5 candidates (works)
fts = hp._retriever._fts_candidates('Mac', None, 0.3, 15)
print(f"FTS5: {len(fts)}")

# LIKE candidates (works)
like = hp._retriever._like_candidates('Mac', None, 0.3, 15)
print(f"LIKE: {len(like)}")

# Full search (crashes before fix)
try:
    results = hp._retriever.search('Mac', min_trust=0.3, limit=5)
    print(f"search: {len(results)}")
except ValueError as e:
    print(f"CRASH: {e}")
```

## Files Modified

1. `/Users/aimac/.hermes/hermes-agent/plugins/memory/holographic/holographic.py`
   - `bytes_to_phases(data, dim=None)` — add dim param + auto-infer from bytes

2. `/Users/aimac/.hermes/hermes-agent/plugins/memory/holographic/retrieval.py`
   - `search()` — add LIKE fallback after FTS5 empty
   - `bytes_to_phases(...)` — add `self.hrr_dim` param (2 of 7 places fixed)
   - `_like_candidates()` — new method for FTS5 fallback

## Remaining Work

Still 5 `bytes_to_phases` calls in `retrieval.py` without `self.hrr_dim`:
- Line 195: `fact_vec = hrr.bytes_to_phases(fact.pop("hrr_vector"))`
- Line 256: `fact_vec = hrr.bytes_to_phases(fact.pop("hrr_vector"))`
- Line 339: `fact_vec = hrr.bytes_to_phases(fact.pop("hrr_vector"))`
- Line 436-437: v1/v2 comparison

These are in scoring/ranking paths that only fire when facts have hrr_vectors. After fixing these, full verification needed.

## Key Insight: Multi-Layer Bug Pattern

```
Bug A crash at line X
    → Bug B never executed
    → Bug B invisible
Fix Bug A
    → Bug B now runs
    → new crash surfaces
```

This is NOT "fix broke X" — Bug B was always there, masked by Bug A's crash.
