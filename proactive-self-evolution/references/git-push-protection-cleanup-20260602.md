# GitHub Push Protection 清理实战（2026-06-02）

## 问题描述

历史commit包含API key，Push Protection持续拦截，导致cron备份任务error。

**敏感文件**：`.env`、`config.yaml`、`.hermes_history`、`config.backup.yaml`、`scripts/test_keys.py`

**错误信息**：
```
remote: — GH013: Repository rule violations found
remote: Push cannot contain secrets
remote: — Groq API Key — path: scripts/test_keys.py:26
remote: — OpenRouter API Key — path: .env:58
remote: — GitHub Personal Access Token — path: config.yaml:149
```

## 清理方案

### 方案1：filter-branch（文件少时推荐）

```bash
cd ~/.hermes
# 从git索引移除敏感文件（保留本地）
git rm --cached config.yaml .env scripts/test_keys.py .hermes_history

# 提交
git commit -m "remove sensitive files from index"

# 从所有历史中清除
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch config.yaml .env scripts/test_keys.py .hermes_history' \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送
git push origin master --force
```

### 方案2：新建orphan分支（文件多时用）

```bash
cd ~/.hermes
git checkout --orphan clean-start

# 只add需要的文件
git add -A  # 先add所有
git reset HEAD <敏感文件>  # 移除敏感文件
git reset HEAD skills/.git  # 如果skills是嵌套git仓库
git commit -m "clean snapshot"

# 强制推送
git push origin clean-start:master --force
```

## 本次实战（2026-06-02）

**根因**：48个commit中散落5+个敏感文件，filter-branch清理后仍残留（可能是因为有些文件在多个commit中以不同名称出现）

**最终方案**：创建新orphan仓库，只保留skills目录

```bash
# 在home目录创建干净仓库
cd ~
rm -rf hermes-config-clean
mkdir hermes-config-clean && cd hermes-config-clean
git init

# 复制需要备份的文件
cp -r ~/.hermes/skills ./skills

# 清理嵌套git
rm -rf skills/.git

# 提交并强制推送
git add -A
git commit -m "Initial clean backup - skills only"
git remote add origin https://github.com/Buluhanke/hermes-config-2026-05.git
git push origin master --force
```

**推送结果**：✅ 成功，无Push Protection拦截

## 教训

1. `.gitignore`只能排除**新提交**的文件，对历史commit无效
2. API key一旦进入git历史，必须用filter-branch或重建方式清理
3. 文件多时（50+个commit，多个敏感文件），重建比filter-branch更可靠
4. `git add -A` + `.gitignore`在Git 2.15上不生效（负路径语法不支持），旧版Git兼容写法：
   ```bash
   git add -- ':!.env' ':!config.yaml'  # 仅排除特定文件
   ```
5. 建议：所有包含真实API key的文件一开始就加入`.gitignore`，不要依赖事后清理

## GitHub Secret Scanning 允许列表（2026-06-02）

如果只是想临时allow secret继续推送，可通过GitHub API解除：
```
https://github.com/{owner}/{repo}/security/secret-scanning/unblock-secret/{secret_id}
```

但根本解决方案还是从历史中清除。
