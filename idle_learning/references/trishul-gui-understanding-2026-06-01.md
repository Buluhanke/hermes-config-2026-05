# TRISHUL: Training-Free GUI Understanding Framework

- **Paper**: arXiv 2502.08226 ("TRISHUL: Towards Region Identification and Screen Hierarchy Understanding for Large VLM based GUI Agents")
- **Authors**: Kunal Singh, Shreyas Singh, Mukund Khanna
- **Date**: Feb 2025 (8 pages, 5 figures)
- **Tags**: training-free, GUI comprehension, screen parsing, SoM alternative

## Core Architecture

### HSP — Hierarchical Screen Parsing
Multi-granularity screen parsing without HTML source. Instead of Set-of-Marks (SoM) which requires DOM metadata, HSP uses purely visual cues to build element hierarchies.

### SEED — Spatially Enhanced Element Description
For each identified GUI element, generates spatially and semantically enriched representations. Bridges the gap between "seeing" and "understanding" UI components.

## Key Differentiator vs SoM

| Aspect | SoM (GPT-4V approach) | TRISHUL (HSP+SEED) |
|--------|----------------------|-------------------|
| Input requirement | HTML/DOM metadata required | Pure screenshot only |
| Platform support | Web only | Cross-platform |
| Training | Fine-tuning on dataset | Training-free |
| Element description | Visual markers only | Semantic + spatial |

## Benchmark Results
- **ScreenSpot** — Superior action grounding (outperforms SoM-based methods)
- **VisualWebBench** — Cross-dataset generalization
- **AITW / Mind2Web** — Strong transfer without dataset-specific training
- **ScreenPR** — GUI referring surpasses ToL agent

## Relevance to Hermes handler

### Current approach
- qwen3-vl:2b with single-stage prompt for scene classification (coarse: browser/desktop/other/unknown)
- "other" and "unknown" scenes (42-49% of dry-run) get only wininfo action

### TRISHUL-inspired improvement
1. **Coarse → Fine hierarchy** (HSP): After initial scene=other classification, add a second-stage fine-grained prompt:
   - "List all visible UI elements, their types (button/text/input/icon/table), and spatial relationships"
2. **Element enrichment** (SEED): Instead of bare wininfo output, generate structured element descriptions with spatial context
3. **Training-free**: No model training needed — just prompt engineering in `screen_trigger_handler.py`

### Expected benefit
- Reduces "other" scene ambiguity
- Enables more targeted actions beyond generic wininfo
- Lays groundwork for safe auto_execute (better scene understanding = fewer false positives)

## References
- arXiv: https://arxiv.org/abs/2502.08226
- Related: ScreenParse (2602.14276), GUIDE benchmark (2603.25864), GUI Knowledge Bench (2510.26098)
