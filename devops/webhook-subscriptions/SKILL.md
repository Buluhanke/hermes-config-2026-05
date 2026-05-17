---
name: webhook-subscriptions
description: "Webhook subscriptions: event-driven agent runs."
version: 1.2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [webhook, events, automation, integrations, notifications, push]
---

# Webhook Subscriptions

Create dynamic webhook subscriptions so external services (GitHub, GitLab, Stripe, CI/CD, IoT sensors, monitoring tools, 1688, payment gateways) can trigger Hermes agent runs by POSTing events to a URL.

## Table of Contents

- [Setup](#setup-required-first)
- [Commands](#commands)
- [Prompt Templates](#prompt-templates)
- [Common Patterns](#common-patterns)
- [1688 Order Webhook Processing](#1688-order-webhook-processing)
- [Payment Callback Security Verification](#payment-callback-security-verification)
- [Idempotency Handling](#idempotency-handling)
- [Automatic Purchase Confirmation Flow](#automatic-purchase-confirmation-flow)
- [Security](#security)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)

## Setup (Required First)

The webhook platform must be enabled before subscriptions can be created. Check with:
```bash
hermes webhook list
```

If it says "Webhook platform is not enabled", set it up:

### Option 1: Setup wizard
```bash
hermes gateway setup
```
Follow the prompts to enable webhooks, set the port, and set a global HMAC secret.

### Option 2: Manual config
Add to `~/.hermes/config.yaml`:
```yaml
platforms:
  webhook:
    enabled: true
    extra:
      host: "0.0.0.0"
      port: 8644
      secret: "generate-a-strong-secret-here"
```

### Option 3: Environment variables
Add to `~/.hermes/.env`:
```bash
WEBHOOK_ENABLED=true
WEBHOOK_PORT=8644
WEBHOOK_SECRET=generate-a-strong-secret-here
```

After configuration, start (or restart) the gateway:
```bash
hermes gateway run
# Or if using systemd:
systemctl --user restart hermes-gateway
```

Verify it's running:
```bash
curl http://localhost:8644/health
```

## Commands

All management is via the `hermes webhook` CLI command:

### Create a subscription
```bash
hermes webhook subscribe <name> \
  --prompt "Prompt template with {payload.fields}" \
  --events "event1,event2" \
  --description "What this does" \
  --skills "skill1,skill2" \
  --deliver telegram \
  --deliver-chat-id "12345" \
  --secret "optional-custom-secret"
```

Returns the webhook URL and HMAC secret. The user configures their service to POST to that URL.

### List subscriptions
```bash
hermes webhook list
```

### Remove a subscription
```bash
hermes webhook remove <name>
```

### Test a subscription
```bash
hermes webhook test <name>
hermes webhook test <name> --payload '{"key": "value"}'
```

## Prompt Templates

Prompts support `{dot.notation}` for accessing nested payload fields:

- `{issue.title}` — GitHub issue title
- `{pull_request.user.login}` — PR author
- `{data.object.amount}` — Stripe payment amount
- `{sensor.temperature}` — IoT sensor reading

If no prompt is specified, the full JSON payload is dumped into the agent prompt.

## Common Patterns

### GitHub: new issues
```bash
hermes webhook subscribe github-issues \
  --events "issues" \
  --prompt "New GitHub issue #{issue.number}: {issue.title}\n\nAction: {action}\nAuthor: {issue.user.login}\nBody:\n{issue.body}\n\nPlease triage this issue." \
  --deliver telegram \
  --deliver-chat-id "-100123456789"
```

Then in GitHub repo Settings → Webhooks → Add webhook:
- Payload URL: the returned webhook_url
- Content type: application/json
- Secret: the returned secret
- Events: "Issues"

### GitHub: PR reviews
```bash
hermes webhook subscribe github-prs \
  --events "pull_request" \
  --prompt "PR #{pull_request.number} {action}: {pull_request.title}\nBy: {pull_request.user.login}\nBranch: {pull_request.head.ref}\n\n{pull_request.body}" \
  --skills "github-code-review" \
  --deliver github_comment
```

### Stripe: payment events
```bash
hermes webhook subscribe stripe-payments \
  --events "payment_intent.succeeded,payment_intent.payment_failed" \
  --prompt "Payment {data.object.status}: {data.object.amount} cents from {data.object.receipt_email}" \
  --deliver telegram \
  --deliver-chat-id "-100123456789"
```

### CI/CD: build notifications
```bash
hermes webhook subscribe ci-builds \
  --events "pipeline" \
  --prompt "Build {object_attributes.status} on {project.name} branch {object_attributes.ref}\nCommit: {commit.message}" \
  --deliver discord \
  --deliver-chat-id "1234567890"
```

### Generic monitoring alert
```bash
hermes webhook subscribe alerts \
  --prompt "Alert: {alert.name}\nSeverity: {alert.severity}\nMessage: {alert.message}\n\nPlease investigate and suggest remediation." \
  --deliver origin
```

### Direct delivery (no agent, zero LLM cost)

For use cases where you just want to push a notification through to a user's chat — no reasoning, no agent loop — add `--deliver-only`. The rendered `--prompt` template becomes the literal message body and is dispatched directly to the target adapter.

Use this for:
- External service push notifications (Supabase/Firebase webhooks → Telegram)
- Monitoring alerts that should forward verbatim
- Inter-agent pings where one agent is telling another agent's user something
- Any webhook where an LLM round trip would be wasted effort

```bash
hermes webhook subscribe antenna-matches \
  --deliver telegram \
  --deliver-chat-id "123456789" \
  --deliver-only \
  --prompt "🎉 New match: {match.user_name} matched with you!" \
  --description "Antenna match notifications"
```

The POST returns `200 OK` on successful delivery, `502` on target failure — so upstream services can retry intelligently. HMAC auth, rate limits, and idempotency still apply.

Requires `--deliver` to be a real target (telegram, discord, slack, github_comment, etc.) — `--deliver log` is rejected because log-only direct delivery is pointless.

## 1688 Order Webhook Processing

1688 order webhooks notify when supplier orders change status (created, paid, shipped, completed, cancelled).

### 1688 Webhook Event Types

| 1688 Event | Description | Hermes Action |
|------------|-------------|---------------|
| `order.created` | New order placed | Log + human review |
| `order.paid` | Order payment confirmed | Trigger procurement |
| `order.shipped` | Supplier shipped goods | Track logistics |
| `order.completed` | Order delivered/completed | Close order loop |
| `order.cancelled` | Order cancelled | Handle refund |

### Create 1688 Order Subscription

```bash
hermes webhook subscribe 1688-orders \
  --events "order.paid,order.shipped,order.completed,order.cancelled" \
  --prompt "1688订单事件: {event_type}\n订单号: {order.id}\n供应商: {supplier.name}\n商品: {order.items[0].title}\n金额: ¥{order.total_amount}\n状态: {order.status}\n时间: {timestamp}" \
  --skills "1688-open-platform-api" \
  --deliver telegram \
  --deliver-chat-id "12345"
```

### 1688 Payload Structure

```json
{
  "event_type": "order.paid",
  "order": {
    "id": "ORDER_20240101_ABC123",
    "status": "paid",
    "total_amount": 15800.00,
    "currency": "CNY",
    "items": [
      {
        "sku_id": "SKU_001",
        "title": "蓝牙耳机 黑色",
        "quantity": 100,
        "unit_price": 158.00
      }
    ],
    "supplier": {
      "id": "SUP_456",
      "name": "深圳XX数码专营店",
      "wang_wang": "供应商昵称"
    }
  },
  "shipping": {
    "tracking_number": "SF1234567890",
    "carrier": "顺丰速运",
    "estimated_delivery": "2024-01-05"
  },
  "timestamp": "2024-01-01T10:30:00+08:00"
}
```

### Order Status State Machine

```
[created] → [paid] → [shipped] → [completed]
    ↓           ↓           ↓
[cancelled] [cancelled] [refund_requested]
```

## Payment Callback Security Verification

Payment callbacks (Alipay, WeChat Pay, Stripe, etc.) require rigorous signature verification to prevent spoofing.

### Signature Verification Flow

```
1. Extract signature header (X-Signature or sign field)
2. Extract timestamp from payload
3. Reject if timestamp > 5 minutes old (replay attack prevention)
4. Build signing string: timestamp + "." + raw_body
5. Compute HMAC-SHA256 with merchant secret
6. Compare signatures (timing-safe comparison)
7. Accept or reject request
```

### Hermes Payment Security Middleware

Hermes webhook adapter automatically verifies payment callbacks when configured:

```bash
hermes webhook subscribe payment-callback \
  --events "payment.*" \
  --payment-verification alipay \
  --payment-secret "your-alipay-trade-secret" \
  --prompt "Payment {event_type}: ¥{amount} from {buyer}\
  Order: {out_trade_no}" \
  --deliver telegram
```

Supported payment providers:
- `alipay` — RSA-SHA256 signature verification
- `wechat` — HMAC-SHA256 signature verification
- `stripe` — Stripe-Signature header verification
- `custom` — User-defined HMAC secret

### Alipay Callback Verification (Python Example)

```python
import hmac
import hashlib
import time
from starlette.requests import Request

async def verify_alipay_callback(request: Request, merchant_secret: str) -> bool:
    body = await request.body()
    headers = dict(request.headers)
    
    # Extract signature components
    sign = headers.get("x-alipay-signature", "")
    timestamp = headers.get("x-alipay-timestamp", "")
    
    # Reject old timestamps (> 5 minutes)
    if abs(time.time() - int(timestamp)) > 300:
        return False
    
    # Build signing string
    signing_string = f"{timestamp}.{body.decode()}"
    
    # Compute expected signature
    expected = hmac.new(
        merchant_secret.encode(),
        signing_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Timing-safe comparison
    return hmac.compare_digest(sign, expected)
```

### WeChat Pay Callback Verification

```python
async def verify_wechat_callback(request: Request, api_key: str) -> bool:
    body = await request.body()
    params = dict(request.query_params)
    
    # Extract signature
    sign = params.get("sign", "")
    time_end = params.get("time_end", "")
    
    # Build string to sign (sorted key=value&)
    sign_string = "&".join(
        f"{k}={v}" for k, v in sorted(params.items())
        if k != "sign" and v
    ) + f"&key={api_key}"
    
    expected = hashlib.md5(sign_string.encode()).hexdigest().upper()
    
    return hmac.compare_digest(sign, expected)
```

## Idempotency Handling

Webhook endpoints must handle duplicate deliveries gracefully (network retries, provider-side retries).

### Idempotency Key Pattern

Every webhook payload should include an idempotency key (`idempotency_key`, `event_id`, `message_id`):

```bash
hermes webhook subscribe idempotent-handler \
  --events "payment.succeeded,order.updated" \
  --idempotency-db ~/.hermes/webhook_idempotency.db \
  --prompt "Event: {event_type}, Key: {event.id}" \
  --deliver telegram
```

### Idempotency Storage Schema

```sql
CREATE TABLE idempotency_keys (
    key TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    response TEXT
);

CREATE INDEX idx_processed_at ON idempotency_keys(processed_at);
```

### Idempotency Flow

```
1. Extract idempotency key from payload
2. Check if key exists in DB
   - EXISTS + same payload hash → return cached response (200 OK)
   - EXISTS + different payload hash → reject (409 Conflict)
   - NOT EXISTS → continue
3. Process webhook
4. Store key + payload hash + response
5. Return response
```

### TTL Cleanup

Idempotency keys expire after 7 days by default (configurable):

```bash
hermes webhook subscribe my-webhook \
  --idempotency-ttl 604800 \  # 7 days in seconds
  ...
```

### Automatic Cleanup Cron

```bash
# Add to crontab -e
0 3 * * * sqlite3 ~/.hermes/webhook_idempotency.db "DELETE FROM idempotency_keys WHERE processed_at < datetime('now', '-7 days')"
```

## Automatic Purchase Confirmation Flow

When 1688 orders are paid, Hermes can automatically confirm purchase (拉取工厂发货)。

### Flow Diagram

```
[order.paid webhook]
       │
       ▼
┌─────────────────┐
│ Verify Signature│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Idempotency    │── Duplicate? ──→ Return cached response
│ Check          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Auto-confirm   │
│ Purchase        │
│ (call 1688 API) │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Success │
    └────┬────┘
         │         ┌──────────────┐
         ▼         │ notify_user  │
┌─────────────────┐│ (Telegram)   │
│ Update local    │└──────────────┘
│ order status    │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Failure │
    └────┬────┘
         │
         ▼
┌─────────────────┐
│ Retry 3x with   │
│ exponential     │
│ backoff         │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Still   │
    │ failing │
    └────┬────┘
         ▼
┌─────────────────┐
│ Alert human    │
│ (Telegram)      │
└─────────────────┘
```

### Create Auto-Confirm Subscription

```bash
hermes webhook subscribe 1688-auto-confirm \
  --events "order.paid" \
  --idempotency-db ~/.hermes/webhook_idempotency.db \
  --auto-confirm \
  --1688-api-key "your-api-key" \
  --1688-api-secret "your-api-secret" \
  --retry-attempts 3 \
  --retry-backoff 60 \
  --prompt "1688订单已支付，自动确认购买中...\n订单号: {order.id}\n金额: ¥{order.total_amount}" \
  --deliver telegram
```

### Auto-Confirm Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--auto-confirm` | Enable automatic purchase confirmation | false |
| `--1688-api-key` | 1688 Open Platform API key | Required |
| `--1688-api-secret` | 1688 API secret | Required |
| `--retry-attempts` | Number of retry attempts | 3 |
| `--retry-backoff` | Base backoff seconds (exponential) | 60 |
| `--idempotency-db` | SQLite DB for idempotency | Required |
| `--confirm-timeout` | Max seconds to wait for confirm | 300 |

### 1688 Confirm Purchase API Call

```python
import httpx
import time
import hmac
import hashlib

def confirm_1688_purchase(order_id: str, api_key: str, api_secret: str) -> dict:
    # Build request
    timestamp = str(int(time.time()))
    params = {
        "orderId": order_id,
        "timestamp": timestamp,
        "appKey": api_key,
    }
    
    # Sign request
    sign_string = "".join(f"{k}{v}" for k, v in sorted(params.items()))
    sign_string += api_secret
    signature = hashlib.md5(sign_string.encode()).hexdigest()
    
    # Call 1688 confirm API
    response = httpx.post(
        "https://gw.1688.com/service/openApi",
        params={**params, "sign": signature},
        json={
            "orderId": order_id,
            "action": "confirmPurchase"
        },
        timeout=60
    )
    
    return response.json()
```

### Retry with Exponential Backoff

```python
import asyncio

async def confirm_with_retry(order_id: str, max_attempts: int = 3, base_backoff: int = 60):
    for attempt in range(max_attempts):
        try:
            result = confirm_1688_purchase(order_id)
            if result.get("success"):
                return result
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
        
        wait_time = base_backoff * (2 ** attempt)
        await asyncio.sleep(wait_time)
    
    raise Exception(f"Failed after {max_attempts} attempts")
```

### Success Notification

```bash
# On successful auto-confirm, Hermes sends:
# 🎉 1688订单自动确认成功
# 订单号: ORDER_20240101_ABC123
# 供应商: 深圳XX数码专营店
# 商品: 蓝牙耳机 黑色 x 100
# 金额: ¥15,800.00
# 物流: 等待供应商发货
```

### Failure Alert

```bash
# On failure after retries:
# ⚠️ 1688订单自动确认失败
# 订单号: ORDER_20240101_ABC123
# 错误: 供应商响应超时
# 建议: 请手动登录1688确认订单状态
# 操作链接: https://trade.1688.com/order/detail.htm?orderId=...
```

## Security

- Each subscription gets an auto-generated HMAC-SHA256 secret (or provide your own with `--secret`)
- The webhook adapter validates signatures on every incoming POST
- Static routes from config.yaml cannot be overwritten by dynamic subscriptions
- Subscriptions persist to `~/.hermes/webhook_subscriptions.json`
- **Payment callbacks**: Automatic signature verification with timestamp replay protection (5-minute window)
- **Idempotency**: Built-in SQLite-based duplicate detection with configurable TTL
- **IP whitelisting**: Restrict webhooks to known provider IPs (e.g., Alipay, WeChat)

### IP Whitelist for Payment Providers

```yaml
platforms:
  webhook:
    enabled: true
    extra:
      allowed_ips:
        # Alipay
        - "110.42.0.0/14"
        - "203.209.224.0/24"
        # WeChat Pay
        - "101.226.0.0/15"
        - "140.207.0.0/16"
        # Stripe
        - "3.0.0.0/8"
        - "52.0.0.0/8"
```

## How It Works

1. `hermes webhook subscribe` writes to `~/.hermes/webhook_subscriptions.json`
2. The webhook adapter hot-reloads this file on each incoming request (mtime-gated, negligible overhead)
3. When a POST arrives matching a route, the adapter formats the prompt and triggers an agent run
4. The agent's response is delivered to the configured target (Telegram, Discord, GitHub comment, etc.)

## Troubleshooting

If webhooks aren't working:

1. **Is the gateway running?** Check with `systemctl --user status hermes-gateway` or `ps aux | grep gateway`
2. **Is the webhook server listening?** `curl http://localhost:8644/health` should return `{"status": "ok"}`
3. **Check gateway logs:** `grep webhook ~/.hermes/logs/gateway.log | tail -20`
4. **Signature mismatch?** Verify the secret in your service matches the one from `hermes webhook list`. GitHub sends `X-Hub-Signature-256`, GitLab sends `X-Gitlab-Token`.
5. **Firewall/NAT?** The webhook URL must be reachable from the service. For local development, use a tunnel (ngrok, cloudflared).
6. **Wrong event type?** Check `--events` filter matches what the service sends. Use `hermes webhook test <name>` to verify the route works.
7. **Payment signature verification failing?**
   - Check timestamp is within 5-minute window
   - Verify you're using the correct secret (not the webhook secret, but the payment provider's API secret)
   - For Alipay: ensure RSA public key is correctly configured
   - For WeChat: ensure API key (not secret) is used for signature
8. **Idempotency key conflicts?**
   - Check `~/.hermes/webhook_idempotency.db` for stuck keys
   - Verify the idempotency key extraction path matches payload structure
   - Run cleanup: `sqlite3 ~/.hermes/webhook_idempotency.db "DELETE FROM idempotency_keys WHERE processed_at < datetime('now', '-7 days')"`
9. **Auto-confirm failing?**
   - Check 1688 API credentials are valid
   - Verify API rate limits not exceeded
   - Check gateway logs for specific API error codes
   - Manual fallback: `hermes webhook test <name>` to re-trigger
