# 远程技能市场参考

SkillHub、虾评、ClawHub 等远程技能市场的 API 端点和使用方式。

---

## ① SkillHub 官方市场

官方市场主域名：`https://lightmake.site/api/v1/search`

**搜索技能：**
```bash
curl -s "https://lightmake.site/api/v1/search?q=<URL-encoded 中文关键词>&limit=10"
curl -s "https://lightmake.site/api/v1/search?q=<URL-encoded English keywords>&limit=10"
```

**过滤规则：** 保留 `score >= 0.05` 的结果，过滤低相关。

**常见问题：**
- 若 429 限流，指数退避 15s → 30s → 60s
- 若 403 阻止，检查网络代理或 DNS

---

## ② 虾评技能市场

中文技能的核心来源。API Base URL：`https://xiaping.coze.com`（注意：不是 `coze.site`）

**搜索技能：**
```bash
curl -s "https://xiaping.coze.com/api/skills/search?q=<URL-encoded 关键词>&limit=10"
```

**获取技能详情：**
```bash
curl -s "https://xiaping.coze.com/api/skills/<skill-id>"
```

**获取下载链接：**
```bash
curl -s "https://xiaping.coze.com/api/skills/<skill-id>/download"
```

**说明：** 虾评结果往往比 SkillHub 更相关（中文场景下）。需要先加载 `虾评指南` 技能（路径：`~/.openclaw/workspace/skills/虾评指南/SKILL.md`），按其中 §1.1 + §1.2 的规范执行搜索和下载。

---

## ③ ClawHub 技能市场

- 参考 `skills_hub_clawhub.py` 的搜索接口
- 按需调用附带的 ClawHub 相关工具
- 作为补充兜底层（第七层），优先级低于前 6 层

---

## 市场层级优先级

1. **本地内置技能**（Hermes / OpenClaw 自带）
2. **本地已安装技能**（~/.hermes/skills/、~/.openclaw/workspace/skills/）
3. **本地 marketplace 缓存**（~/.openclaw/workspace/skills-marketplace/skills/）
4. **GitHub 技能仓库**（gh CLI 搜索，用户显式请求时提升至第一远程层）
5. **SkillHub 官方市场**（lightmake.site）
6. **虾评技能市场**（xiaping.coze.com）
7. **ClawHub 技能市场**（补充兜底）
