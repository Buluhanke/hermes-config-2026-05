# Hermes 官方功能对照检查清单（2026-05-26）

## 已具备 ✅
- Memory (MEMORY.md/USER.md) — 持久记忆系统
- Context Files — SOUL.md + .hermes.md 已创建
- Checkpoints — config.yaml 已开启
- Cron — 每日03:00社区学习已建立
- Delegation — delegate_task 子代理功能
- Plugins — 17个已安装
- Web Dashboard — http://127.0.0.1:9119 运行中
- Voice Mode — TTS语音合成
- Vision — smolvlm2 本地VLM
- Browser — CDP + MCP 双驱动
- Skills System — 27个skills

## 需要额外配置 ⚙️
- Event Hooks — 需要写插件，gateway级触发
- MCP Integration — stdio/HTTP方式接入外部服务
- Image Generation — 需要 FAL.ai API Key（付费）
- Memory Providers — Mem0等外部服务，当前够用

## 官方特性（非日常需要）
- Spotify控制
- Batch Processing
- Daytona/Daytona代理
- SINGULARITY容器
- Vercel Runtime

## 本次补齐记录
1. SOUL.md → ~/.hermes/SOUL.md（官方指定全局人格路径）
2. .hermes.md → ~/.hermes/hermes-agent/.hermes.md（项目级上下文）
3. Web Dashboard → npm build + hermes dashboard --no-open
4. 每日03:00社区学习cron → job_id 64a85a32

## 配置优化（按官方推荐）
- checkpoints.enabled: true
- hard_stop_enabled: true
- language: zh
- show_cost: true
- human_delay.mode: on
- streaming: true
- sessions.auto_prune: true
- updates.pre_update_backup: true
- auxiliary.web_extract timeout: 600s