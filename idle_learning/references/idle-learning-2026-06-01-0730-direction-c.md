# 2026-06-01 07:30 空闲学习 — 方向C Agent Security + Production Guardrails

## 产线快照

**时间**：2026-06-01 07:30
**screen_watcher**：✅ PID 48245（07:06启动）
**截图新鲜度**：07:26更新，3.4MB
**YOLO预分类**：✅ 已部署 (07:25日志: "YOLO预分类: idle (1个UI元素)" → "跳过VLM分析 [silent]")
**双层分类器**：YOLO (93ms) → qwen3-vl:2b (仅活跃场景调用)
**June 1 场景分布（00:06-07:26）**：
- other: ~340+ (99.6%) — 全部正确标记 [silent] ✅
- browser: 2
- desktop: 1  
- unknown: 2 (00:04 and 00:06 — early morning contamination)
- **unknown = 0%** after 00:07 ✅
**总 dry-run**：967 ✅
**Gateway 污染**：1928（缓慢增长 ~1/天）
**Ollama**：✅ PID 98043 (0.6% CPU, 145MB RSS)
**模型**：qwen2.5:1.5b (0.92GB) + qwen3-vl:2b (1.76GB) — 按需加载
**handler lock**：无残留 ✅

## 方向C发现

### 新发现：ChatGPT for Google Sheets 数据窃取
- 来源：PromptArmor Threat Intelligence（HN 87pts, May 2026）
- 185K 下载扩展，上线 <1月
- 间接提示注入 → 跨工作表数据窃取 + 钓鱼弹窗 + 侧边栏覆盖
- **绕过 "require human approval" 设置**
- OpenAI 对负责任披露无回应

### OSU-NLP YAML 扫描结果
- 60+ 篇 Desktop/Safety 论文检查完成
- 所有论文已在 references 中记录
- **无新增方向C论文遗漏**
- **结论**：Direction C 论文覆盖完整，下次可跳过此步

## 更新记录
- 新参考文件：`references/promptarmor-chatgpt-sheets-exfiltration-2026-06-01.md`
- 更新参考文件：`references/promptarmor-agent-security-2026-06-01.md` — 追加ChatGPT Sheets发现
- SKILL.md 更新：添加「方向C标准巡检协议」5步流程

## 下次方向
A — Vision 模型巡检（检查新发布模型 + 双层分类器效能回溯）
