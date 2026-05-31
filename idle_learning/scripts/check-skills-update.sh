#!/bin/bash
# Quick check: verify new references were added to idle_learning skill
echo "=== New reference files ==="
ls -la ~/.hermes/skills/idle_learning/references/vlaa-gui-*
ls -la ~/.hermes/skills/idle_learning/references/gpt55-harness-*
echo ""
echo "=== Direction C new entries (count lines added) ==="
grep -c "VLAA-GUI\|GPT-5.5 Computer Use\|A11y-Compressor\|OSU-NLP-Group\|Context Window W20\|Codex sudo" ~/.hermes/skills/idle_learning/SKILL.md
echo ""
echo "=== Total reference files ==="
ls ~/.hermes/skills/idle_learning/references/ | wc -l
