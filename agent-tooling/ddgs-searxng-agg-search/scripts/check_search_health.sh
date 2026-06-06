#!/bin/bash
# Hermes 搜索健康问诊脚本 (v4 — anysearch 单通道版) — 30 秒出真相
# 跑法: bash scripts/check_search_health.sh
#
# 适用场景: 用户问 "anysearch 正常吗" / "搜索正不正常" /
#          搜索结果一会有一会无、想看路由走的哪条、后端 CLI 是否能起。
#
# 原理: 分 5 段 — ①路由入口存在性 ②anysearch 后端实地跑
#                ③search.py 完整路由 ④gateway.log 搜索相关错误
#                ⑤Python 路径/包版本
#
# 2026-06-06 v4 状态:
#   - anysearch 唯一通道 ✅
#   - last30days 已亡 ❌（脚本里**不**再测, 测了会误导成"刚挂"）
#   - ddgs 已废, 反查用
#
# 设计要点:
#   - set +e: 任一命令失败不退出, 全跑完让用户看完整图
#   - timeout 15s: 单条 query 实际耗时, 不卡死脚本
#   - 退出码打印: 不只 "跑没跑", 还看 "成没成"
#   - 输出截 500 字符: 不爆控制台, 关键信息保留
#
# 2026-06-06 16:00 固化: 用户问"X 正不正常"时, 30 秒给真答案,
#                别靠"应该是好的"猜。
# 2026-06-06 16:30 修订: 对齐 v4 (last30days 段移除, 因已亡)

set +e

echo "════════════════════════════════════════════"
echo "  1. search.py 路由入口"
echo "════════════════════════════════════════════"
SP="$HOME/.hermes/scripts/search.py"
if [ -f "$SP" ]; then
    echo "✅ 存在: $SP"
    echo "   大小: $(wc -c < "$SP") bytes, 行数: $(wc -l < "$SP")"
    echo "   最近改: $(stat -f '%Sm' "$SP" 2>/dev/null || stat -c '%y' "$SP" 2>/dev/null)"
else
    echo "❌ 不存在: $SP"
fi
echo

echo "════════════════════════════════════════════"
echo "  2. anysearch 后端（唯一通道，v4 状态）"
echo "════════════════════════════════════════════"
ANY="$HOME/.hermes/scripts/anysearch_cli.py"
if [ -f "$ANY" ]; then
    echo "✅ 存在: $ANY"
    echo "   行数: $(wc -l < "$ANY")"
    echo "   最近改: $(stat -f '%Sm' "$ANY" 2>/dev/null)"
else
    echo "❌ 不存在: $ANY — anysearch 通道挂了, 整个搜索停摆"
    echo "   下一步: 查 ~/.hermes/scripts/ 下 anysearch 是不是被误删/重命名"
fi

# 实地跑一条简单 query — 15s 超时
echo "   → 跑 query: 'Mac mini M4 内存' (15s 超时)"
T0=$(date +%s)
OUT=$(timeout 15 python3 "$ANY" "Mac mini M4 内存" 2>&1)
RC=$?
T1=$(date +%s)
echo "   退出码: $RC, 耗时: $((T1-T0))s"
echo "   输出前 500 字符:"
echo "$OUT" | head -c 500
echo
echo

echo "════════════════════════════════════════════"
echo "  3. search.py 走完整路由"
echo "════════════════════════════════════════════"
if [ -f "$SP" ]; then
    echo "   → 路由词 '今天推荐什么' (15s, 应走 anysearch)"
    timeout 15 python3 "$SP" "今天推荐什么" 2>&1 | head -c 600
    echo
    echo
    echo "   → 路由词 '特斯拉最新消息' (15s, 应走 anysearch)"
    timeout 15 python3 "$SP" "特斯拉最新消息" 2>&1 | head -c 600
    echo
fi

echo
echo "════════════════════════════════════════════"
echo "  4. 网关日志最近的搜索相关错误"
echo "════════════════════════════════════════════"
tail -300 ~/.hermes/logs/gateway.log 2>/dev/null | grep -iE 'search|anysearch' | tail -20
echo
echo "════════════════════════════════════════════"
echo "  5. Python 路径 + venv"
echo "════════════════════════════════════════════"
echo "   python3: $(which python3)"
echo "   hermes 虚拟环境: ${VIRTUAL_ENV:-未激活}"
echo "   reqs 里的搜索包:"
ls -la "$HOME/hermes/hermes-agent/venv/lib/python"*/site-packages/ 2>/dev/null | grep -iE 'anysearch|ddgs|serp' | head -5 || echo "   没找到 anysearch/ddgs 包（可能装在别处）"

echo
echo "════════════════════════════════════════════"
echo "  6. 顺手扫一下：last30days 真亡了？"
echo "════════════════════════════════════════════"
L30_DIR="$HOME/.hermes/skills/last30days"
L30_PKG=$(python3 -c "import importlib.util; print('YES' if importlib.util.find_spec('last30days') else 'NO')" 2>/dev/null)
L30_NPM=$(npm list -g last30days 2>/dev/null | grep last30days || echo "(not in npm)")
if [ ! -d "$L30_DIR" ]; then
    echo "✅ last30days skill 目录不存在（符合 v4 预期：已亡）"
else
    echo "⚠️  last30days skill 目录还在: $L30_DIR — 跟 v4 状态不符, 需查"
fi
echo "   Python 包: $L30_PKG"
echo "   npm: $L30_NPM"
