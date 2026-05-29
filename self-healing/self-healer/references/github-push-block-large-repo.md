# Git Push 拦截与仓库过大问题

## 问题类型

### 类型1：GitHub Secret Scanning Push Protection 拦截

**症状**：
```
remote: error: GH013: Repository rule violations found for refs/heads/main.
remote: - Push cannot contain secrets
remote:   —— Groq API Key ———
remote:    locations:
remote:     - commit: abc123
remote:       path: some/file.md:123
```

**根因**：git历史中存在真实API Key（`sk-`、`gsk_`、`nvapi-`、`AIzaSy`等前缀），GitHub Push Protection扫描整个历史

**诊断流程**：
```bash
# 1. 检查当前文件是否还有真实key（占位符不算）
grep -rn "sk-[a-zA-Z0-9]\{20,\}" . --include="*.md"

# 2. 检查推送报错的完整输出，看具体哪个key类型
GIT_TERMINAL_PROMPT=0 git push --force origin main 2>&1 | grep "——"

# 3. 检查secret scanning alerts（可能为空但push仍被拦）
gh api repos/{owner}/{repo}/secret-scanning/alerts
# 如果返回[]，说明alert已处理，拦截来自Push Protection
```

**注意**：`secret-scanning/alerts` API返回空 ≠ push没被拦。Push Protection和Secret Scanning Alerts是两个独立系统。拦截发生在push时，不是在alerts页面显示。

**修复流程（git filter-branch）**：
```bash
# 适用于：git版本 < 2.22（无法使用git-filter-repo）
# 适用于：不想安装额外工具的情况

cd /path/to/repo

# 0. 先stash当前未提交的变更
git stash 2>&1 && git stash drop

# 1. 执行历史重写（替换所有API key模式）
git filter-branch --force \
  --tree-filter 'find . -type f \( -name "*.md" -o -name "*.txt" -o -name "*.json" \) \
    -exec sed -i "" \
      "s/sk-[a-zA-Z0-9]*/YOUR_API_KEY/g; \
       s/gsk_[a-zA-Z0-9]*/GRSK_REDACTED/g; \
       s/nvapi-[a-zA-Z0-9]*/NVIDAPI_REDACTED/g; \
       s/AIzaSy[a-zA-Z0-9]*/GOOGLE_AI_KEY_REDACTED/g; \
       s/gho_[a-zA-Z0-9]*/GH_TOKEN_REDACTED/g" {} +' \
  --tag-name-filter cat -- --all

# 2. 验证HEAD中不再有真实key
git show HEAD:path/to/suspect/file.md | grep -c "sk-"

# 3. 强制推送
GIT_TERMINAL_PROMPT=0 git push --force origin main
```

**关键点**：
- `--tree-filter` 会重写每个commit的文件内容，速度慢但可靠
- `--tag-name-filter cat` 保留所有tag
- `--all` 同时处理所有分支
- macOS sed语法用 `sed -i ""`（GNU sed用 `sed -i`）
- 第一次filter-branch只处理 `sk-` 和 `gho_`，后续需单独处理 `gsk_`、`nvapi-` 等其他类型
- git filter-repo 更优（更快，需git>=2.22），但非必须

**如果filter-branch后仍被拦**：
- 说明还有其他类型的key在历史中
- 从报错信息中找到key类型，添加到sed命令重新执行
- 常见key前缀：`sk-`（OpenAI）、`sk-or-`（OpenRouter）、`gsk_`（Groq）、`nvapi-`（NVIDIA）、`AIzaSy`（Google）、`gho_`（GitHub Token）

**如果无法重写历史（如仓库太大）**：
1. 创建新仓库：`git init && git remote add`
2. 选择性迁移：只迁移需要的目录/文件
3. 代价：丢失历史记录

---

### 类型2：仓库过大导致Push失败（HTTP 400 / RPC failed）

**症状**：
```
error: RPC failed; HTTP 400 curl 56 The requested URL returned error: 400
fatal: The remote end hung up unexpectedly
Everything up-to-date
```

**根因**：
- `.git` 目录超过5GB（GitHub单个仓库限制5GB）
- git buffer太小（`http.postBuffer` 不足）
- 网络超时

**诊断**：
```bash
# 检查.git大小
du -sh .git

# 检查pack大小
git count-objects -vH | grep size-pack

# 检查最大的文件
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | sort -k3 -n -r | head -20
```

**修复流程**：
```bash
# 1. 增大git buffer
git config http.postBuffer 524288000

# 2. 尝试推送
GIT_TERMINAL_PROMPT=0 git push origin main

# 3. 如果还是失败，检查是否是从未推送过的全新提交
git status  # "Everything up-to-date" + exit code 1 = 远程不接收

# 4. 如果是历史过大，需要从git历史中删除大文件
# 找到最大的文件/目录
git log --oneline --all | wc -l  # 看总commit数
git ls-tree -r HEAD | grep -E "weights\.bin|model\.tflite" | head -10

# 5. 从git历史中删除（示例：删除chrome-debug目录）
git rm -r --cached chrome-debug/
git commit -m "remove chrome-debug from git tracking"
echo "chrome-debug/" >> .gitignore
git add .gitignore && git commit -m "gitignore chrome-debug"

# 注意：这只能删除当前commit的内容，历史中的大文件仍会占用空间
# 完全清理需要git filter-branch（见类型1）
```

**如果远程仓库已经超限**：
- GitHub拒绝接收超限的pack文件
- 无法通过推送解决，必须创建新仓库
- 方案：创建新仓库，选择性迁移文件，通知所有协作者更新remote

---

## 验证清单

修复后执行以下验证：
```bash
# 1. 确认push成功
git push origin main  # 应无报错

# 2. 确认无残留key
grep -rn "sk-[a-zA-Z0-9]\{20,\}\|gsk_[a-zA-Z0-9]\{20,\}\|nvapi-[a-zA-Z0-9]\{30,\}" . --include="*.md"

# 3. 检查仓库大小
du -sh .git  # 应在合理范围（<1GB为佳）

# 4. 确认GitHub页面显示正常
# 访问 https://github.com/{owner}/{repo}/settings
```

---

## 预防措施

1. **永远不要在git历史中存储真实API Key**
   - 使用环境变量或 .env 文件
   - 示例：`api_key: sk-xxx` → `api_key: YOUR_API_KEY`（提交前替换）

2. **在 .gitignore 中排除大型调试文件**
   ```
   chrome-debug/
   *.log
   node_modules/
   ```

3. **定期检查仓库大小**
   ```bash
   # 放在cron中每月检查
   du -sh ~/.hermes/.git
   ```

4. **API Key占位符规范**
   - OpenAI: `sk-xxx` 或 `YOUR_API_KEY`
   - Groq: `gsk_xxx` 或 `GRSK_REDACTED`
   - GitHub Token: `gho_xxx` 或 `GH_TOKEN_REDACTED`
   - Google: `AIzaSyxxx` 或 `GOOGLE_AI_KEY_REDACTED`
