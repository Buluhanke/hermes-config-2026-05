# Bash 严格模式 + 函数捕获 / group command 的 4 个坑

这次写 hermes_backup.sh 撞了 4 次 set -euo pipefail 的坑。每次都让脚本静默 exit（exit 141 = SIGPIPE），日志里看不到原因。**这 4 个坑任何写生产 bash 脚本的人都会撞**。

## 坑 1：`local x=$(func)` 拿到 func 内部所有 stdout

**症状**：
```bash
pack() {
    log "打包中..."           # 默认走 stdout
    tar -czf out.tar.gz ...
    local size=$(du -h ...)    # 默认走 stdout
    log "完成: $size"          # 默认走 stdout
    echo "/path/to/out.tar.gz"  # 这个是我要返回的
}

main() {
    local tarball=$(pack)      # ← 拿到一堆 log + size + 路径, 不是干净的路径
}
```

**真相**：`func` 里的 `log()` 默认走 stdout，`$()` 捕获时一并捕。`echo` 走 stdout 是要返回的，结果裹在一堆噪音里。

**修法**：
```bash
pack() {
    log "打包中..." >&2      # 日志走 stderr
    tar -czf out.tar.gz ...
    local size=$(du -h ...)
    log "完成: $size" >&2    # 日志走 stderr
    echo "/path/to/out.tar.gz" # 只有这一行走 stdout
}
```

**配套习惯**：函数里**所有诊断输出都 `>&2`**，只有最后一个 `echo "$返回值"` 走 stdout。

## 坑 2：`{...} > file` group command 里的 SIGPIPE

**症状**：
```bash
manifest() {
    {
        echo "Header"
        tar -tzf "$tarball" | while read p; do stat -f '%z %N' ...; done > tmp
        sort -rn tmp | head -50      # ← head 读完 50 行就退出, sort 收到 SIGPIPE
    } > manifest.txt                # ← 在 set -euo pipefail 下, 整 group 失败
    log "manifest 写完"             # ← 跑不到这里
}
```

**真相**：`sort | head -50` 的最后一条命令是 head，head 提前关 pipe → sort 收到 SIGPIPE → 退出码 141 → `set -e` 让 group 整体失败。

**修法 A**（推荐）：把数据先写 tmp file，再 head：
```bash
local tmp_manifest=$(mktemp)
tar -tzf "$tarball" | while read p; do stat -f '%z %N' ...; done > "$tmp_manifest"
sort -rn "$tmp_manifest" | head -50
rm -f "$tmp_manifest"
```

**修法 B**（不推荐，浪费）：`head -n 50` 换成 `awk 'NR<=50'`（awk 会读完所有输入，不发 SIGPIPE 给上游）。

**修法 C**（最后手段）：group 末尾加 `|| true` 容忍部分失败：
```bash
{ ... } > manifest.txt || log "警告: manifest 部分内容生成失败(非致命)"
```

## 坑 3：`set -u` + 数组未定义 = 崩

**症状**：
```bash
set -u
my_func() {
    local arr=("$@")   # 如果调用方传 0 个参数, arr 是空数组
    echo "${arr[0]}"  # ← "unbound variable" 错
}
my_func  # 崩
```

**修法**：用 `${arr[0]:-}` 加默认值，或用 `${arr[@]:-}` 加 `""`：
```bash
echo "${arr[0]:-}"
echo "${arr[@]:-}"
```

## 坑 4：`set -e` 不影响 `(( ))` 和 `[[ ]]` 的某些失败

**症状**：
```bash
set -e
n=0
(( n++ ))  # n=0 时, (( 1 )) 退出码 1, 但 set -e 不管 (( )) 算术
```

**真相**：`(( ))` 当 n=0 时返回 1（旧 bash 行为），但 `set -e` 默认不捕获。

**修法**：
- 显式 `set -e` + `set -o errtrace` + trap
- 或用 `n=$((n + 1))` 而不是 `(( n++ ))`（赋值形式不返回错）

## 综合防御模式

写生产 bash 脚本前先在脚本顶部加：
```bash
set -euo pipefail
shopt -s inherit_errexit 2>/dev/null || true   # 旧 bash 不支持
trap 'echo "ERROR at line $LINENO: $BASH_COMMAND" >&2' ERR
```

`inherit_errexit` 让 subshell 也继承 set -e，避免 "subshell 里失败但主脚本继续" 的诡异行为。

## 调试技巧

**快速定位 SIGPIPE 来源**：
```bash
bash -x script.sh 2>&1 | tail -100   # 看 xtrace 死在哪条 pipe
```

**让 set -e 在 group command 里不生效**：
```bash
{ set +e; some_dangerous_command; set -e; }  # 临时关掉
```

**或更简单**：
```bash
some_dangerous_command || true   # 显式容忍
```

## 实测复现（2026-06-06 hermes_backup.sh）

第一次跑：pack() 成功 129M，但 encrypt_chunk 没运行 → 整脚本 exit 141  
第二次跑：发现是 manifest() 的 `sort | head` 触发 SIGPIPE → 改用 tmp file  
第三次跑：encrypt_chunk 也触发 SIGPIPE（GPG + tee -a + tail -3）→ 改 `>&2` 隔离

**结论**：bash 严格模式 + 复杂 pipe 是地狱。能用 python 写的逻辑别用 bash。
