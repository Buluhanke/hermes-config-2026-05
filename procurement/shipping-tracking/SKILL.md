# 物流追踪 Skill

## 1. 1688物流信息获取

### 1.1 订单详情页解析
- **入口**: 1688订单列表页 → 订单详情 → 物流信息区块
- **解析字段**:
  - 物流公司名称 (logistics_company)
  - 运单号 (tracking_number)
  - 发货时间 (ship_time)
  - 预计到达时间 (eta)
  - 收货地址 (delivery_address)
- **触发时机**: 订单状态变为"已发货"时自动抓取

### 1.2 1688 Open API
- **API Endpoint**: `https://gw.1688.com/openapi/param2/1/com.alibaba.logistics/..."
- **鉴权**: 签名算法 (appKey + appSecret + timestamp)
- **接口调用**:
  ```
  getLogisticsInfo: 批量查询物流轨迹
  getLogisticsDetail: 单个运单详情
  ```
- **频率限制**: 200次/分钟，需做流量控制

---

## 2. 快递100/菜鸟API追踪

### 2.1 快递100 API
- **订阅推送模式**: 主动推送物流状态变更
- **查询接口**: `https://api.kuaidi100.com/poll/query.do`
- **必需参数**:
  - `customer`: 授权key
  - `sign`: MD5(content+key+secret)
  - `param`: JSON字符串 `{ "com": "yt", "num": "运单号", "from": "出发地", "to": "目的地" }`
- **返回字段**:
  - `state`: 物流状态 (0-未找到, 1-已揽收, 2-在途, 3-派送中, 4-已签收, 5-拒收, 6-退件)
  - `data[]`: 轨迹详情数组

### 2.2 菜鸟API
- **接口地址**: `https://wuliu.taobao.com/outer/race/trace.do`
- **鉴权**: 权限号 + 密码 + 验证码
- **查询方式**: 运单号 + 快递公司代码
- **特色**: 支持淘宝/天猫订单自动匹配快递公司

### 2.3 快递公司映射表
| 快递公司 | 代码 | 快递100映射 | 菜鸟映射 |
|---------|------|-------------|----------|
| 圆通 | YTO | YTO | YTO |
| 中通 | ZTO | ZTO | ZTO |
| 申通 | STO | STO | STO |
| 韵达 | YD | YUNDA | YUNDA |
| 顺丰 | SF | SF | SF |
| 京东 | JD | JD | JD |
| 邮政EMS | EMS | EMS | EMS |

---

## 3. 状态更新通知

### 3.1 物流状态定义
```
PENDING       = 0   # 待发货
SHIPPED       = 1   # 已发货
IN_TRANSIT    = 2   # 在途
OUT_FOR_DELIVERY = 3  # 派送中
DELIVERED     = 4   # 已签收
EXCEPTION     = 5   # 异常
RETURNED      = 6   # 退回
```

### 3.2 通知触发规则
| 状态 | 触发条件 | 通知方式 | 通知内容 |
|------|---------|---------|---------|
| 已发货 | 揽收成功 | 邮件+短信 | "您的订单已发货，运单号: XXX" |
| 在途 | 离开上一节点 | 邮件 | "包裹正在运输中，当前位置: XXX" |
| 派送中 | 到达配送站 | 短信 | "您的包裹正在派送，请保持电话畅通" |
| 已签收 | 签收成功 | 邮件 | "您的订单已签收，感谢购买" |
| 异常 | 状态码5 | 邮件+短信+电话 | "您的包裹出现异常，请联系客服" |

### 3.3 通知模板
```
【发货通知】
您好，您的订单 #{order_id} 已发货。
物流公司: {logistics_company}
运单号: {tracking_number}
当前状态: {status}
查看轨迹: {tracking_url}

【派送通知】
您好，您的包裹正在派送中。
收件人: {receiver_name}
联系方式: {receiver_phone}
配送员: {courier_name} {courier_phone}

【签收通知】
您好，您的订单 #{order_id} 已签收。
签收时间: {sign_time}
签收方式: {sign_method}
```

---

## 4. 异常处理

### 4.1 异常类型定义
| 异常类型 | 代码 | 描述 | 处理策略 |
|---------|------|------|---------|
| 超时未更新 | TIMEOUT | 48小时无新轨迹 | 自动查询+人工介入 |
| 丢件 | LOST | 连续5天无更新 | 启动理赔流程 |
| 退回 | RETURN | 包裹被退回 | 通知买家+退款处理 |
| 拒收 | REJECTED | 买家拒收 | 等待退回+二次销售 |
| 拦截 | INTERCEPTED | 发货前拦截 | 取消发货+库存释放 |
| 破损 | DAMAGED | 包裹破损 | 启动理赔+补发 |

### 4.2 超时监控规则
```
监控周期: 每小时扫描一次
超时阈值:
  - 国内快递: 48小时无轨迹更新
  - 国际快递: 7天无轨迹更新
  - 偏远地区: 72小时无轨迹更新

触发流程:
  1. 超时提醒 → 查询快递公司API
  2. 仍未更新 → 标记为异常订单
  3. 人工介入 → 联系物流公司/买家
  4. 确认丢件 → 启动理赔+重新发货
```

### 4.3 异常处理流程图
```
检测到异常 → 判断异常类型 → 执行对应策略
     ↓
    超时 → 自动查询 → 仍未更新 → 人工介入
    丢件 → 启动理赔 → 重新发货/退款
    退回 → 通知买家 → 等待接货/退款
    破损 → 拍照取证 → 理赔/补发
```

### 4.4 异常通知模板
```
【超时提醒】
您的订单 #{order_id} 已发货 {days} 天，物流信息暂时未更新。
我们已联系物流公司查询，请耐心等待。
如有任何问题，请联系客服。

【丢件通知】
非常抱歉，您的订单 #{order_id} 经确认已丢失。
我们将为您安排重新发货或全额退款，请选择:
1. 重新发货 (预计3-5天)
2. 全额退款 (1-3个工作日到账)
```

---

## 5. 与库存系统联动

### 5.1 签收后自动更新库存
```
触发条件: 物流状态变为 DELIVERED (已签收)
触发动作:
  1. 查询订单对应的SKU
  2. 调用库存系统API增加可用库存
  3. 记录入库日志
  4. 更新订单状态为已完成
```

### 5.2 库存更新API
```python
# 签收后库存更新
def update_inventory_on_delivery(order_id, tracking_number):
    # 1. 获取订单信息
    order = get_order(order_id)
    # 2. 获取SKU列表
    skus = order.get_skus()
    # 3. 更新库存
    for sku in skus:
        inventory_api.increment_available(
            sku_id=sku.id,
            warehouse_id=order.warehouse_id,
            quantity=sku.quantity,
            source=f"delivery:{tracking_number}",
            reason="签收入库"
        )
    # 4. 记录日志
    log_delivery_inventory(order_id, tracking_number, skus)
    # 5. 更新订单状态
    update_order_status(order_id, "COMPLETED")
```

### 5.3 库存联动规则
| 事件 | 库存操作 | 说明 |
|------|---------|------|
| 订单已发货 | 冻结库存 | 库存从"可用"转为"冻结" |
| 包裹退回 | 释放冻结 | 库存从"冻结"转回"可用" |
| 订单已签收 | 扣减冻结 | 减少冻结库存，增加可用库存 |
| 丢件/拒收 | 释放冻结 | 库存从"冻结"转回"可用" |
| 二次发货 | 重新冻结 | 库存从"可用"转为"冻结" |

### 5.4 库存同步日志
```json
{
    "event": "delivery_confirmed",
    "order_id": "TB20230515001",
    "tracking_number": "YT1234567890",
    "sign_time": "2023-05-18 14:30:00",
    "sku_updates": [
        {
            "sku_id": "SKU001",
            "warehouse_id": "WH001",
            "quantity": 2,
            "before": { "frozen": 2, "available": 100 },
            "after": { "frozen": 0, "available": 102 }
        }
    ],
    "timestamp": "2023-05-18T14:30:05+08:00"
}
```

---

## 6. 常用API参考

### 6.1 快递100订阅推送API
```http
POST https://api.kuaidi100.com/poll/query.do
Content-Type: application/x-www-form-urlencoded

customer=xxx&sign=xxx&param={"com":"YTO","num":"1234567890"}
```

### 6.2 菜鸟轨迹查询
```http
GET https://wuliu.taobao.com/outer/race/trace.do?mailNo=1234567890&code=YTO
```

### 6.3 1688物流查询
```http
GET https://gw.1688.com/openapi/param2/1/com.alibaba.logistics/{method}.do?access_token=xxx&orderId=xxx
```

---

## 7. 配置项

| 配置项 | 默认值 | 说明 |
|-------|-------|------|
| POLLING_INTERVAL | 3600 | 轨迹轮询间隔(秒) |
| TIMEOUT_THRESHOLD_HOURS | 48 | 超时阈值(小时) |
| MAX_RETRY_ATTEMPTS | 3 | 最大重试次数 |
| ENABLE_SMS_NOTIFICATION | true | 是否发送短信通知 |
| ENABLE_EMAIL_NOTIFICATION | true | 是否发送邮件通知 |
| AUTO_UPDATE_INVENTORY | true | 签收后是否自动更新库存 |

---

## 8. 错误代码

| 错误码 | 描述 | 处理建议 |
|-------|------|---------|
| 1001 | 运单号无效 | 检查运单号格式 |
| 1002 | 快递公司不支持 | 添加到映射表 |
| 1003 | 无物流信息 | 等待揽收或联系快递 |
| 1004 | API调用超限 | 降级或切换渠道 |
| 1005 | 网络超时 | 重试 |
| 1006 | 签名验证失败 | 检查密钥配置 |