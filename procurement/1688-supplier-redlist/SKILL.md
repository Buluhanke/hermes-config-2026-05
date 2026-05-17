# 1688供应商红黑榜动态管理

## 红黑榜机制

### 红榜（可信供应商）
- 条件：连续3次无纠纷+评分>4.6+交期达标
- 权益：优先推荐、简化询价流程、账期支持
- 维护：季度复审，动态升降级

### 黑榜（风险供应商）
- 条件：纠纷率>5% / 质量问题>2次 / 交期延误>3天 / 欺诈行为
- 处置：自动过滤、不推荐、不开启新合作
- 例外：情节轻微+整改承诺，可降级观察三个月

### 评级维度
```
质量维度：货品是否符合描述（退货率/投诉率）
交期维度：是否按时发货/到达（延误率）
价格维度：报价是否合理（对比市场行情）
服务维度：响应速度/态度/配合度
沟通维度：回复率/沟通效率/理解能力
```

### 动态调整算法
```python
def update_supplier_score(supplier_id, transaction):
    score = get_current_score(supplier_id)
    
    # 每次交易后调整
    if transaction.quality_issue:
        score -= 10
    if transaction.delayed:
        score -= 5
    if transaction.on_time:
        score += 3
    if transaction.price_competitive:
        score += 2
    
    # 红黑榜判定
    if score >= 80:
        move_to_redlist(supplier_id)
    elif score <= 30:
        move_to_blacklist(supplier_id)
    
    save_score(supplier_id, score)
```

### 与看板集成
- 供应商卡片显示当前评级（红/黄/绿）
- 交易完成后自动触发评分更新
- 黑榜供应商在看板中被红色高亮