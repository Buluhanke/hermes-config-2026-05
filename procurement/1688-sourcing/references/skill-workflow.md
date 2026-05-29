# 1688采购技能联动工作流

## 技能串联

```
anysearch（批量搜索）→ 1688-sourcing（标准化比价流程）→ decision-helper（量化评估）
                                              ↓
                              hindsight（每次采购决策后自动记忆）
                                              ↓
                              hermes-ocr（辅助：读资质文件/报价单截图）
```

## 适用场景

老板说"找XX供应商"、"对比一下"、"哪家便宜"时触发完整工作流。

## 快捷命令

### AnySearch（已配置runtime.conf）
```bash
# 单次搜索
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py search "纸箱 义乌 工厂" --max_results 5

# 批量搜索（推荐，节省时间）
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py batch_search \
  --queries '[{"query":"纸箱 义乌 工厂","max_results":5},{"query":"气泡袋 金华 批发","max_results":5}]'

# 提取工厂详情页静态内容
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py extract "https://detail.1688.com/offer/ID.html"
```

### Hindsight记忆（已集成到Hermes）
- `hindsight_retain`: 每次采购完成后存入决策结果（供应商名、价格、推荐原因）
- `hindsight_recall`: 下次找供应商时先recall看是否有历史记忆
- 记忆格式：简洁事实陈述，不是AI叙事

### 统一OCR（已装）
```bash
python3 ~/.hermes/skills/vision/hermes-ocr/scripts/ocr.py screenshot --region "x,y,w,h"
python3 ~/.hermes/skills/vision/hermes-ocr/scripts/ocr.py read 文件路径
python3 ~/.hermes/skills/vision/hermes-ocr/scripts/ocr.py detect
```

## 决策阈值

老板说过：**小问题/中等问题AI自主决定，不需要问**。

具体到采购场景：
- 同一品类、价格差距<10%、其他条件相近 → 直接选，不问
- 价格差距>20%、供应商条件差异明显 → 汇报+建议
- 涉及未知供应商、首次合作 → 先hindsight查历史，再决定是否上报