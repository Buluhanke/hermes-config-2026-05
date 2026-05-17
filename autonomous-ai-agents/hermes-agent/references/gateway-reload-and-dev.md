# Hermes Agent 开发/调试核心教训

## ⚠️ 改了插件/代码后必须重启 gateway 进程

**场景**：修改了 `plugins/model-providers/`、`skills/`、或其他运行时加载的代码后，发现行为没变。

**根因**：运行中的 gateway 进程（PID 66453 等）内存中保留了旧代码模块，重启前改文件等于没改。

**正确流程**：
```bash
# 1. 查运行中的进程
ps aux | grep gateway

# 2. 改插件文件
# ...

# 3. 删缓存（如果修改了 provider）
rm ~/.hermes/cache/model_catalog.json

# 4. 重启进程（关键！）
kill <gateway_pid>
hermes gateway run --replace
```

**涉及场景**：
- 修改 `plugins/model-providers/` 下的 provider 注册
- 修改 `skills/` 下的 skill 内容
- 修改 `~/.hermes/config.yaml`（某些生效，有些需要完整重启）
- 任何 MCP server 配置变更

**验证**：改完后，查询 `/model` 或相关命令，确认新行为已生效。

---

## cc-haha 架构精髓（借鉴到 Hermes）

### 1. 分层解耦（最重要）
```
Layer 1 — 接口层（MCP工具定义）← 不改
Layer 2 — 安全关卡（9层）← 不改
Layer 3 — 会话上下文 ← 不改
Layer 4 — CLI集成 ← 不改
Layer 5 — 桥接层 ← 可替换
Layer 6 — 执行层 ← 可替换
```
核心思路：**不改原始接口和安全机制，只换底层实现**。

### 2. Plugin/Skills 热重载
cc-haha 的 stop/start plugin 后自动刷新 slash commands、skills、CLI 设置，**不需要重启进程**。
Hermes 目前还不支持这个，需要重启 gateway 才能 reload skills。

### 3. Project Memory 树形结构
从散列表升级为项目树导航，支持中文路径/空格路径，记忆恢复优先级：`cwd` → session元数据 → 真实文件系统。

### 4. 应用分类系统（值得借鉴）
cc-haha 有 191 个 Bundle ID 分类，每个对应权限等级。Hermes 的 computer use 也可以建立类似白名单机制，对不同应用分配不同权限级别（read/click/full 三级）。

---

## Provider 注册机制

### 注册流程
1. Provider plugin 放在 `plugins/model-providers/<name>/__init__.py`
2. 调用 `register_provider(profile)` 注册到 `_REGISTRY`
3. 首次 `get_provider_profile()` 时触发懒加载（`_discover_providers()`）
4. 扫描 `_BUNDLED_PLUGINS_DIR` 和 `$HERMES_HOME/plugins/model-providers/`

### 缓存机制
- `~/.hermes/cache/model_catalog.json` 缓存了已发现的 providers
- 改完 provider 后需要删除此缓存，让系统重新发现

### 别名机制
- `get_provider_profile("minimax-cn")` → 先查 `_ALIASES`，再查 `_REGISTRY`
- ProviderProfile 的 `aliases` 字段会自动建立别名映射

### 用户插件覆盖
用户插件（`$HERMES_HOME/plugins/model-providers/`）可以覆盖内置插件，last-writer-wins。