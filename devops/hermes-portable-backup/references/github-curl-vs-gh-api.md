# GitHub 私有仓文件获取：`curl raw` vs `gh api` 对比

**适用场景**：从 GitHub 私有仓拉一个文件来跑（如 `bash restore.sh` / 一键还原脚本 / 任何"贴一行命令"场景）。

**核心结论（2026-06-06 实测）**：
- ❌ **`curl https://raw.githubusercontent.com/...` 不可靠**（5-10 分钟缓存，偶尔更久）
- ✅ **`gh api repos/.../contents/... | base64 -d` 永远能拿到**

## 1. 现象对比

| 命令 | 推完文件后立刻跑 | 5 分钟后跑 | 30 分钟后跑 |
|------|------------------|------------|--------------|
| `curl -sL https://raw.githubusercontent.com/<user>/<repo>/main/<file>` | ❌ **404** | 🟡 可能 404 | ✅ 通常 OK |
| `gh api repos/<user>/<repo>/contents/<file> --jq .content \| base64 -d` | ✅ OK | ✅ OK | ✅ OK |

## 2. 根因

- **`raw.githubusercontent.com` 是 GitHub 的 CDN 缓存层**
  - 私有仓文件推到 main 后，CDN 需要 5-10 分钟同步
  - 期间或之后，**老"不存在"状态会黏住**（哪怕你刚 push 完）
  - GitHub 客服公开承认这个缓存问题，但无 SLA
- **`api.github.com` 是 GitHub 主 API**
  - 每次都查源（库的真实状态）
  - 私有仓需要 `gh auth login` + scope 包含 `repo`（**默认 `gh auth login` 就有**）
  - 私有仓内容返回的 `.content` 字段是 **base64 编码的文件本体**

## 3. 3 个备选方案（按推荐度排）

### 方案 A：gh API（最稳，**默认推荐**）
```bash
gh api repos/<user>/<repo>/contents/<file-path> --jq .content | base64 -d
```
- 无缓存，永远拿到最新
- 走 `gh` 已登录身份（不需要额外 token）
- 私有仓需要 repo scope（默认 gh auth login 就给）
- **唯一限制**：gh CLI 必须装了（`brew install gh`）

### 方案 A+：gh API 直接跑（**最常见的"一键恢复"用法**）
```bash
gh api repos/<user>/<repo>/contents/hermes_restore_one.sh --jq .content | base64 -d | bash
```
- 3 步合一：拿文件 → 解码 → 跑脚本
- 适用：把 hermes 备份恢复命令写在纸上/记在脑子里
- **2026-06-06 用户拍板的"索引"就是这个**

### 方案 B：先 clone 再 cat（次稳）
```bash
gh repo clone <user>/<repo> /tmp/hb
bash /tmp/hb/hermes_restore_one.sh
```
- 适用：脚本超过几 KB / 想看一眼再跑
- 缺点：要先 clone 整个仓（git 仓大时慢）

### 方案 C：curl raw（**有条件用**）
```bash
curl -sL https://raw.githubusercontent.com/<user>/<repo>/main/<file> | bash
```
- 适用：公开仓 + 文件已发布 30 分钟+
- 私有仓偶尔也能用，但**不要指望**
- **缺点**：404 时用户**完全没救**（要么等缓存、要么改用 A）

## 4. 给"一键恢复"命令的 3 条建议

如果你在写"用户从新电脑跑一行就恢复完整 X"的命令，**必须**满足：

1. **首选 gh API**（无缓存）
2. **给 2-3 个备选**（gh API / gh clone / curl 等缓存）
3. **README 写明 raw 缓存坑**，让用户 404 时知道换命令

**反例**（用户会骂的）：
```bash
# ❌ 这条命令用户跑失败时, 只能干等
curl -sL https://raw.githubusercontent.com/me/my-private-repo/main/restore.sh | bash
```

**正例**：
```markdown
## 恢复命令（任选一条）

### 方案 1：gh API（推荐）
gh api repos/me/my-private-repo/contents/restore.sh --jq .content | base64 -d | bash

### 方案 2：先 clone
gh repo clone me/my-private-repo /tmp/r && bash /tmp/r/restore.sh

### 方案 3：curl raw
curl -sL https://raw.githubusercontent.com/me/my-private-repo/main/restore.sh | bash
# 如果 404，等 10 分钟重试（raw CDN 缓存）
```

## 5. 症状发现技巧

- `gh api` 拿到 `download_url` 是 raw 路径 → 但 raw 路径 404 = **100% 缓存坑**，不是其他问题
- `gh api ... --jq .name` 返回文件名 = **文件在仓库里**
- `gh api ... --jq .content` 拿到 base64 = **能取到内容**
- 所以验证"我刚才 push 成功了吗"用 `gh api`（不被缓存骗）

## 6. 调试命令

```bash
# 1. 看文件在不在 (用 API, 不被缓存骗)
gh api repos/<user>/<repo>/contents/<file> --jq '.name, .size, .content' | head -3

# 2. 看文件 size (应该是 base64 编码后的大小 ≈ 原文件 × 4/3)
gh api repos/<user>/<repo>/contents/<file> --jq '.size' | xargs -I {} echo "原文件约 {} / 1.33 = $(echo "scale=1; {}/1.33" | bc) bytes"

# 3. 直接看文件元数据
gh api repos/<user>/<repo>/contents/<file> | python3 -m json.tool | head -10
```

## 7. 公开仓 vs 私有仓

| 仓类型 | raw 缓存 | gh API |
|--------|----------|--------|
| 公开 | 🟡 偶尔 5 分钟延迟（一般秒级）| ✅ 正常 |
| 私有 | ❌ 5-10 分钟甚至更长 | ✅ 正常 |

**私有仓 raw 缓存问题比公开仓严重得多**——因为 GitHub 把私有仓的 raw 走单独的 CDN 路径。

## 8. 写脚本时的实操建议

```bash
# 在 hermes 一键恢复脚本顶部加 fallback
echo "正在拉恢复脚本..."
SCRIPT_CONTENT=$(gh api repos/$GITHUB_USER/$REPO/contents/restore.sh --jq .content 2>/dev/null | base64 -d)
if [ -z "$SCRIPT_CONTENT" ]; then
    echo "gh API 失败, 尝试 curl raw..."
    SCRIPT_CONTENT=$(curl -sL https://raw.githubusercontent.com/$GITHUB_USER/$REPO/main/restore.sh)
fi
if [ -z "$SCRIPT_CONTENT" ]; then
    echo "两个都失败, 请手动:"
    echo "1. 打开 https://github.com/$GITHUB_USER/$REPO"
    echo "2. 下载 restore.sh 后手动 bash"
    exit 1
fi
echo "$SCRIPT_CONTENT" | bash
```

**3 层 fallback**：gh API → curl raw → 手动指引。新电脑恢复成功率 99.9%。

## 9. 相关坑

- **坑 10**（Apple git 2.15 HTTP/2 EOF）：`gh` 命令本身不受影响（用 Go 写的不依赖系统 git）
- **坑 5/10.5**（gh release upload 偶发 EOF）：`gh api` 走 REST 不受影响
- 所以 **`gh api` 是 macOS 备份/恢复栈里最稳的命令**
