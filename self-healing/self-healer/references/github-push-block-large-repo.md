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
gh api repos/{owner}/{repo}/secret-scanning/push-protections
```

**注意**：`secret-scanning/push-protections` API返回空 ≠ push没被拦。Push Protection和Secret Scanning Alerts是两个独立系统。拦截发生在push时。

**修复流程（filter-branch）**：
```bash
cd /path/to/repo

# 执行历史重写
git filter-branch --force \
  --index-filter 'git rm --cached --ignore-unmatch config.yaml .env scripts/test_keys.py .hermes_history' \
  --prune-empty --tag-name-filter cat -- --all

# 验证HEAD中不再有真实key
git show HEAD:path/to/suspect/file.md | grep -c "sk-"

# 强制推送
GIT_TERMINAL_PROMPT=0 git push --force origin master
```

**filter-branch局限性（2026-06-02发现）**：
`--index-filter 'git rm --cached --ignore-unmatch <file>'` 只重写声明过该文件的commit，可能遗漏：
- 更早commit中存在的文件（如`.hermes_history`在50+个commit的多个文件中）
- 未被track但被paste进会话历史的敏感内容
- backup文件（`config.backup.yaml`、`config.yaml.test_bak`）

**确定性修复方案：重建仓库**（当filter-branch清理后仍被拦时）：
```bash
# 1. 创建干净仓库
mkdir ~/repo-clean && cd ~/repo-clean && git init

# 2. 只复制非敏感文件（绝对不复制含key的文件）
cp -r ~/.hermes/skills ./skills
# 不复制：.env、config.yaml、*.bak、.hermes_history、sessions/

# 3. 确保无敏感文件（skills目录内）
grep -rl "sk-\|gsk_\|ghp_\|csk-" skills/ 2>/dev/null
# 如果有假阳性（如注释中的sk-类型），手动审查后再推送

# 4. 提交并强制推送
git add -A && git commit -m "clean backup - no secrets"
git remote add origin https://github.com/{owner}/{repo}.git
git push origin master --force
```

**Git版本兼容性注意**（macOS默认Git 2.15.0）：
- `-- ':(exclude).env'` 负路径排除语法在Git < 2.22不工作
- 改用 `--index-filter 'git rm --cached --ignore-unmatch .env'`
- 脚本中用 `grep -vE "^\?\?\s+(\.env|auth\.json)"` 过滤 `git status --porcelain` 的方式更可靠

---

### 类型2：仓库过大导致Push失败（HTTP 400 / RPC failed）

**症状**：
```
error: RPC failed; HTTP 400 curl 56 The requested URL returned error: 400
fatal: The remote end hung up unexpectedly
Everything up-to-date
```

**根因**：`.git` 目录超过5GB（GitHub单个仓库限制5GB）

**诊断**：
```bash
du -sh .git
git count-objects -vH | grep size-pack
```

**修复流程**：
```bash
# 1. 增大git buffer
git config http.postBuffer 524288000

# 2. 推送
GIT_TERMINAL_PROMPT=0 git push origin main

# 3. 若仍失败且历史过大，创建新仓库选择性迁移
```

---

## 验证清单

```bash
# 1. 确认push成功
git push origin master  # 应无报错

# 2. 确认无残留key
grep -rn "sk-[a-zA-Z0-9]\{20,\}\|gsk_[a-zA-Z0-9]\{20,\}\|ghp_[a-zA-Z0-9]" . --include="*.md"

# 3. 检查仓库大小
du -sh .git  # 应在合理范围（<1GB为佳）
```

## 预防措施

1. **永远不要在git历史中存储真实API Key** — 使用占位符
2. **在 .gitignore 中排除** `.env`、`config.yaml`、`*.bak`、`.hermes_history`、`sessions/`
3. **API Key占位符规范**：OpenAI用`sk-xxx`/→`YOUR_API_KEY`，Groq用`gsk_xxx`→`GRSK_REDACTED`，GitHub Token用`gho_xxx`→`GH_TOKEN_REDACTED`
