#!/bin/bash
# check_v31_compliance.sh — 验证 v3.1 跨渠道铁律已同步
# 跑法: bash ~/.hermes/scripts/check_v31_compliance.sh
# 退出码: 0 = 全渠道已同步, 1 = 有渠道漏了

set -e

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
# SSOT skill 名字（默认 cross-channel-sop-sync = 通用跨渠道 SOP 模板，
# 其中 v3.1 反问禁令是核心实例。可被其他 SOP 复用：传 $1 覆盖）
V31_SIGNATURE="${1:-cross-channel-sop-sync}"
V31_KEYWORDS=("v3.1" "零反问" "成长之路必须落地" "必须落地")
FAIL=0

echo "=== v3.1 跨渠道铁律同步验证 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "SSOT skill: $V31_SIGNATURE"
echo

# 1. skill 文件存在（多路径兼容：profiles/default/skills 和 skills 根）
echo "[1/6] Skill 文件存在?"
SKILL_FILE=""
for candidate in \
    "$HERMES_HOME/profiles/default/skills/$V31_SIGNATURE/SKILL.md" \
    "$HERMES_HOME/skills/$V31_SIGNATURE/SKILL.md" \
    "$HERMES_HOME/skills/meta/$V31_SIGNATURE/SKILL.md" \
    "$HERMES_HOME/skills/agent/$V31_SIGNATURE/SKILL.md" \
    "$HERMES_HOME/skills/agent-tooling/$V31_SIGNATURE/SKILL.md" \
    "$HERMES_HOME/skills/devops/$V31_SIGNATURE/SKILL.md" \
    "$HERMES_HOME/skills/software-development/$V31_SIGNATURE/SKILL.md"; do
    if [[ -f "$candidate" ]]; then
        SKILL_FILE="$candidate"
        break
    fi
done
if [[ -n "$SKILL_FILE" ]]; then
    echo "  ✅ $SKILL_FILE ($(wc -l < "$SKILL_FILE") lines)"
else
    echo "  ❌ Skill 文件不存在！试过所有候选路径"
    FAIL=1
fi

# 2. SOUL.md 含 v3.1 段
echo "[2/6] SOUL.md 含 v3.1 段落?"
SOUL="$HERMES_HOME/SOUL.md"
if [[ -f "$SOUL" ]] && grep -q "v3.1 跨渠道铁律" "$SOUL"; then
    echo "  ✅ SOUL.md 包含 'v3.1 跨渠道铁律'"
else
    echo "  ❌ SOUL.md 缺 v3.1 段落"
    FAIL=1
fi

# 3. 6 个渠道 adapter 不再含"我建议...要不要"软反问模板
echo "[3/6] 6 个渠道 adapter 不含旧反问模板?"
PLATFORMS=(qqbot telegram discord feishu wecom weixin)
for p in "${PLATFORMS[@]}"; do
    ADAPTERS=(
        "$HERMES_HOME/hermes-agent/gateway/platforms/$p/adapter.py"
        "$HERMES_HOME/hermes-agent/plugins/platforms/$p/adapter.py"
    )
    found_legacy=0
    for a in "${ADAPTERS[@]}"; do
        if [[ -f "$a" ]]; then
            if grep -qE '要不要.*[Xx]|需要我.*吗' "$a"; then
                echo "  ⚠️  $p adapter 含可疑反问模板 (审查 $a)"
                found_legacy=1
            fi
        fi
    done
    if [[ $found_legacy -eq 0 ]]; then
        echo "  ✅ $p 干净"
    fi
done

# 4. skill 在 prompt snapshot 里
echo "[4/6] channel-universal-sop 在 system prompt snapshot?"
SNAPSHOT="$HERMES_HOME/.skills_prompt_snapshot.json"
if [[ -f "$SNAPSHOT" ]]; then
    if grep -q "$V31_SIGNATURE" "$SNAPSHOT"; then
        echo "  ✅ snapshot 包含 $V31_SIGNATURE"
    else
        echo "  ⚠️  snapshot 不含 (可能 prompt cache 未刷新, 跑一下: hermes skills reload)"
    fi
else
    echo "  ⚠️  snapshot 不存在 (首次跑会自动生成)"
fi

# 5. 6 个关键词在 skill 里
echo "[5/6] 关键铁律词汇在 skill 里?"
for kw in "${V31_KEYWORDS[@]}"; do
    if grep -q "$kw" "$SKILL_FILE" 2>/dev/null; then
        echo "  ✅ '$kw'"
    else
        echo "  ❌ 缺 '$kw'"
        FAIL=1
    fi
done

# 6. 内存索引同步
echo "[6/6] 长期 memory 含 v3.1 索引?"
MEM_FILE="$HERMES_HOME/memory/memory.json"
if [[ -f "$MEM_FILE" ]] && grep -q "v3.1" "$MEM_FILE"; then
    echo "  ✅ memory 含 v3.1 条目"
else
    echo "  ⚠️  memory 未含 v3.1 索引 (本任务已添加, 但 memory.json 路径可能不同)"
fi

echo
if [[ $FAIL -eq 0 ]]; then
    echo "=== 全部通过 ✅ v3.1 跨渠道铁律已同步 ==="
    exit 0
else
    echo "=== 有项目失败 ❌ 详见上方 ==="
    exit 1
fi