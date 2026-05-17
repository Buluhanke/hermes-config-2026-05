---
name: tdd
description: "tdd skill from mattpocock/skills"
version: 1.0.0
source: mattpocock/skills
---
---
name: tdd
description: Test-driven development with red-green-refactor loop. Use when user wants to build features or fix bugs using TDD, mentions "red-green-refactor", wants integration tests, or asks for test-first development.
---

# Test-Driven Development

## Philosophy

**Core principle**: Tests should verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't.

**Good tests** are integration-style: they exercise real code paths through public APIs. They describe _what_ the system does, not _how_ it does it. A good test reads like a specification - "user can checkout with valid cart" tells you exactly what capability exists. These tests survive refactors because they don't care about internal structure.

**Bad tests** are coupled to implementation. They mock internal collaborators, test private methods, or verify through external means (like querying a database directly instead of using the interface). The warning sign: your test breaks when you refactor, but behavior hasn't changed. If you rename an internal function and tests fail, those tests were testing implementation, not behavior.

See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for mocking guidelines.

## Anti-Pattern: Horizontal Slices

**DO NOT write all tests first, then all implementation.** This is "horizontal slicing" - treating RED as "write all tests" and GREEN as "write all code."

This produces **crap tests**:

- Tests written in bulk test _imagined_ behavior, not _actual_ behavior
- You end up testing the _shape_ of things (data structures, function signatures) rather than user-facing behavior
- Tests become insensitive to real changes - they pass when behavior breaks, fail when behavior is fine
- You outrun your headlights, committing to test structure before understanding the implementation

**Correct approach**: Vertical slices via tracer bullets. One test → one implementation → repeat. Each test responds to what you learned from the previous cycle. Because you just wrote the code, you know exactly what behavior matters and how to verify it.

```
WRONG (horizontal):
  RED:   test1, test2, test3, test4, test5
  GREEN: impl1, impl2, impl3, impl4, impl5

RIGHT (vertical):
  RED→GREEN: test1→impl1
  RED→GREEN: test2→impl2
  RED→GREEN: test3→impl3
  ...
```

## Workflow

### 1. Planning

When exploring the codebase, use the project's domain glossary so that test names and interface vocabulary match the project's language, and respect ADRs in the area you're touching.

Before writing any code:

- [ ] Confirm with user what interface changes are needed
- [ ] Confirm with user which behaviors to test (prioritize)
- [ ] Identify opportunities for [deep modules](deep-modules.md) (small interface, deep implementation)
- [ ] Design interfaces for [testability](interface-design.md)
- [ ] List the behaviors to test (not implementation steps)
- [ ] Get user approval on the plan

Ask: "What should the public interface look like? Which behaviors are most important to test?"

**You can't test everything.** Confirm with the user exactly which behaviors matter most. Focus testing effort on critical paths and complex logic, not every possible edge case.

### 2. Tracer Bullet

Write ONE test that confirms ONE thing about the system:

```
RED:   Write test for first behavior → test fails
GREEN: Write minimal code to pass → test passes
```

This is your tracer bullet - proves the path works end-to-end.

### 3. Incremental Loop

For each remaining behavior:

```
RED:   Write next test → fails
GREEN: Minimal code to pass → passes
```

Rules:

- One test at a time
- Only enough code to pass current test
- Don't anticipate future tests
- Keep tests focused on observable behavior

### 4. Refactor

After all tests pass, look for [refactor candidates](refactoring.md):

- [ ] Extract duplication
- [ ] Deepen modules (move complexity behind simple interfaces)
- [ ] Apply SOLID principles where natural
- [ ] Consider what new code reveals about existing code
- [ ] Run tests after each refactor step

**Never refactor while RED.** Get to GREEN first.

## Checklist Per Cycle

```
[ ] Test describes behavior, not implementation
[ ] Test uses public interface only
[ ] Test would survive internal refactor
[ ] Code is minimal for this test
[ ] No speculative features added
```

---

## 1688场景测试策略

1688采购平台有以下特殊性，测试时需要特别处理：

### 平台特性与测试重点

| 1688特性 | 测试风险 | 策略 |
|---------|---------|------|
| 页面结构频繁变化 | 选择器失效 | 用语义化定位+fallback机制 |
| 登录态Cookie管理 | 匿名/过期 | 每个测试前检查登录态，失效则重新登录 |
| 异步加载（列表分页） | 元素未就绪 | 显式等待+重试机制 |
| 验证码/滑块 | 自动化阻断 | 人工介入或OCR绕过（仅测试用） |
| 价格浮点数精度 | 计算误差 | 用Decimal类型，避免float |
| 批量操作事务性 | 部分失败 | 验证补偿机制或回滚逻辑 |

### 页面对象模型（POM）实践

```python
# 1688_page.py
class1688Page:
    def __init__(self, page):
        self.p = page
        self.search_input = ("#search-input", "搜索框")
        self.price_filter = ("xpath://button[contains(text(),'价格')]", "价格筛选")

    def search(self, keyword):
        self.p.fill(*self.search_input, keyword)
        self.p.press(self.search_input, "Enter")

    def wait_for_results(self, timeout=10):
        # 等待骨架屏消失 + 至少一个商品出现
        self.p.wait_for_selector(".product-item", timeout=timeout)
```

### 反爬应对策略

```python
def test_search_with_rate_limit_handling(self):
    for attempt in range(3):
        try:
            page.search("蓝牙耳机")
            page.wait_for_results()
            break
        except TimeoutError:
            if attempt == 2:
                raise
            time.sleep(random.uniform(2, 5))  # 指数退避
```

---

## 采购流程测试用例

### 核心业务流程

```
采购流程：搜索商品 → 比价 → 加入采购车 → 确认订单 → 付款 → 等待发货 → 确认收货
```

### 测试用例模板

```python
class TestProcurementFlow:
    """1688采购完整流程测试"""

    @pytest.fixture(autouse=True)
    def setup(self, authenticated_page):
        self.page = authenticated_page
        self.page.goto("https://www.1688.com")

    def test_search_and_filter_products(self):
        """搜索关键词并按价格筛选"""
        self.page.fill("#search-input", "蓝牙耳机")
        self.page.press("#search-input", "Enter")
        
        # 等待结果加载
        self.page.wait_for_selector(".product-item", timeout=10)
        
        # 点击价格筛选
        self.page.click("button:has-text('价格')")
        self.page.wait_for_timeout(500)  # 等待筛选动画
        
        # 验证至少有一个结果
        items = self.page.query_selector_all(".product-item")
        assert len(items) > 0

    def test_add_to_cart(self):
        """添加商品到采购车"""
        # 先搜索
        self._search_product("蓝牙耳机")
        
        # 点击第一个商品的"加入采购车"按钮
        first_item = self.page.wait_for_selector(".product-item")
        first_item.click("button:has-text('加入采购车')")
        
        # 验证采购车数量更新
        cart_badge = self.page.wait_for_selector(".cart-badge")
        assert cart_badge.inner_text() == "1"

    def test_checkout_and_payment(self):
        """完整下单付款流程（mock支付）"""
        # 1. 加入商品到采购车
        self._add_first_item_to_cart()
        
        # 2. 进入采购车确认页
        self.page.click(".cart-badge")
        self.page.wait_for_url("**/cart**")
        
        # 3. 确认订单信息
        total_price = self.page.text_content(".total-price")
        
        # 4. 点击提交订单（mock支付成功回调）
        with self.page.expect_response("**/pay/callback**") as resp_info:
            self.page.click("button:has-text('提交订单')")
        
        response = resp_info.value
        assert response.ok or "order_id" in response.text

    def test_order_status_tracking(self):
        """订单状态追踪"""
        order_id = self._create_test_order()
        
        # 进入订单列表
        self.page.goto("https://www.1688.com/order/list")
        self.page.wait_for_selector(".order-item")
        
        # 查找对应订单
        order = self.page.query_selector(f".order-item[data-id='{order_id}']")
        assert order is not None
        
        # 验证状态流转
        status = order.text_content(".order-status")
        assert status in ["待付款", "待发货", "已发货", "已完成"]

    # ===== 辅助方法 =====
    def _search_product(self, keyword):
        self.page.fill("#search-input", keyword)
        self.page.press("#search-input", "Enter")
        self.page.wait_for_selector(".product-item", timeout=10)

    def _add_first_item_to_cart(self):
        self._search_product("蓝牙耳机")
        first_item = self.page.wait_for_selector(".product-item")
        first_item.click("button:has-text('加入采购车')")
        self.page.wait_for_timeout(300)

    def _create_test_order(self) -> str:
        """创建测试订单，返回order_id"""
        self._add_first_item_to_cart()
        self.page.click(".cart-badge")
        self.page.click("button:has-text('提交订单')")
        # 从URL或页面提取order_id
        return self.page.url.split("order_id=")[-1]
```

### 边界与异常测试用例

```python
class TestProcurementEdgeCases:

    def test_empty_cart_checkout_fails(self):
        """空采购车不能提交订单"""
        page.goto("/cart")
        page.click("button:has-text('提交订单')")
        
        # 验证错误提示
        error = page.wait_for_selector(".error-message")
        assert "请先添加商品" in error.text_content()

    def test_quantity_boundary(self):
        """数量边界：最低1件，最高999件"""
        self._add_to_cart("蓝牙耳机")
        
        # 测试超过上限
        quantity_input = page.query_selector("input[name='quantity']")
        quantity_input.fill("1000")
        page.click("button:has-text('确定')")
        
        error = page.wait_for_selector(".error-message")
        assert "最多购买999件" in error.text_content()

    def test_concurrent_cart_modification(self):
        """并发修改采购车数量"""
        import threading
        
        results = []
        def modify_cart(product_id, qty):
            # 模拟并发修改
            resp = api.update_cart_quantity(product_id, qty)
            results.append(resp)
        
        t1 = threading.Thread(target=modify_cart, args=(123, 5))
        t2 = threading.Thread(target=modify_cart, args=(123, 10))
        
        t1.start(); t2.start()
        t1.join(); t2.join()
        
        # 验证最终数量一致性（乐观锁或最终一致）
        final_qty = api.get_cart_item(123).quantity
        assert final_qty in [5, 10]
```

---

## Mock/Stub技巧

### 什么时候用Mock？

| 场景 | 用Mock | 用Real |
|-----|-------|-------|
| 外部API（支付、1688接口）| ✅ | ❌ |
| 数据库读写 | ❌（用Testcontainers）| ✅ |
| 内部Service调用 | ❌ | ✅ |
| 第三方发邮件 | ✅ | ❌ |
| 计时器/日期 | ✅（fake time）| ❌ |

### Python Mock实战

```python
from unittest.mock import Mock, patch, MagicMock
import pytest

class TestWithMocks:

    def test_payment_deduction(self):
        """测试支付扣款逻辑"""
        mock_payment = Mock()
        mock_payment.charge.return_value = {"status": "success", "txn_id": "TXN123"}
        
        # 注入mock到被测系统
        order = Order(processor=mock_payment)
        order.pay(amount=100)
        
        # 验证调用
        mock_payment.charge.assert_called_once_with(amount=100)

    def test_mock_with_complex_return(self):
        """复杂返回值mock"""
        mock_api = Mock()
        mock_api.get_products.return_value = [
            {"id": 1, "name": "蓝牙耳机", "price": 99.9},
            {"id": 2, "name": "数据线", "price": 9.9},
        ]
        
        products = mock_api.get_products(filter="category=耳机")
        assert len(products) == 2
        assert products[0]["price"] == 99.9

    def test_mock_side_effect(self):
        """Side Effect：模拟多次调用不同返回"""
        mock_api = Mock()
        mock_api.get_stock.side_effect = [
            100,   # 第一次调用返回100
            0,     # 第二次调用返回0（缺货）
            50,    # 第三次调用返回50
        ]
        
        assert mock_api.get_stock("SKU001") == 100
        assert mock_api.get_stock("SKU001") == 0
        assert mock_api.get_stock("SKU001") == 50

    def test_patch_decorator(self):
        """@patch装饰器用法"""
        @patch('myapp.external.SMSService.send')
        def test_sms_notification(mock_send):
            mock_send.return_value = True
            
            notification = NotificationService()
            notification.send_sms("13800000000", "您的订单已发货")
            
            mock_send.assert_called_with(
                to="13800000000",
                message="您的订单已发货"
            )

    def test_context_manager_mock(self):
        """模拟文件/网络等上下文管理器"""
        with patch('myapp.db.Connection') as mock_conn:
            mock_instance = MagicMock()
            mock_conn.return_value = mock_instance
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=None)
            mock_instance.query.return_value = [{"id": 1}]
            
            repo = Repository()
            result = repo.find_all()
            
            assert len(result) == 1
```

### JavaScript/TypeScript Mock实战

```typescript
// Jest风格的mock
describe('OrderService', () => {
  it('should deduct inventory on payment', async () => {
    // Mock库存服务
    const mockInventory = {
      deduct: jest.fn().mockResolvedValue({ success: true }),
      restore: jest.fn().mockResolvedValue({ success: true }),
    };
    
    const orderService = new OrderService(mockInventory);
    await orderService.pay(123, 100);
    
    expect(mockInventory.deduct).toHaveBeenCalledWith(123, 1);
  });

  it('should restore inventory on payment failure', async () => {
    const mockInventory = {
      deduct: jest.fn().mockRejectedValue(new Error('Network error')),
      restore: jest.fn().mockResolvedValue({ success: true }),
    };
    
    const orderService = new OrderService(mockInventory);
    
    await expect(orderService.pay(123, 100)).rejects.toThrow('Network error');
    expect(mockInventory.restore).toHaveBeenCalledWith(123, 1);
  });
});
```

### Stub技巧：Fake Time / Fake File

```python
import freezegun  # pip install freezegun

def test_order_expires_after_24h():
    """测试订单24小时后自动取消"""
    with freezegun.freeze_time("2024-01-01 10:00:00"):
        order = create_order()
        assert order.status == "pending"
    
    with freezegun.freeze_time("2024-01-02 10:00:01"):
        order.check_expiry()
        assert order.status == "cancelled"

# ---- Fake File System ----
import pyfakefs

def test_export_csv():
    with pyfakefs.FakeFilesystem():
        exporter = CSVExporter()
        exporter.export("orders", "/tmp/test.csv")
        
        with open("/tmp/test.csv") as f:
            content = f.read()
        assert "订单ID,金额" in content
```

---

## 集成测试模板

### 基础结构

```python
import pytest
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ===== Pytest Fixtures =====

@pytest.fixture(scope="session")
def browser():
    """Session级浏览器复用"""
    driver = webdriver.Chrome()
    driver.implicitly_wait(5)
    yield driver
    driver.quit()

@pytest.fixture(scope="function")
def authenticated_page(browser):
    """每个测试用例获取干净页面，登录状态隔离"""
    # 打开新标签页
    browser.execute_script("window.open('')")
    browser.switch_to.window(browser.window_handles[-1])
    
    # 登录
    browser.get("https://www.1688.com/login")
    browser.find_element("#username").send_keys("test_user")
    browser.find_element("#password").send_keys("test_pass")
    browser.find_element("button[type='submit']").click()
    
    yield browser
    
    # 清理：关闭标签页
    browser.close()
    browser.switch_to.window(browser.window_handles[0])

@pytest.fixture
def api_client():
    """API客户端（requests库）"""
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer test_token"})
    return session

# ===== 测试用例写法 =====

class TestIntegrationSmoke:
    """冒烟测试：验证核心链路"""

    def test_user_can_login_and_view_orders(self, authenticated_page):
        authenticated_page.get("https://www.1688.com/order/list")
        
        assert "我的订单" in authenticated_page.title
        assert authenticated_page.is_element_present(".order-list")

    def test_product_search_returns_results(self, browser):
        browser.get("https://www.1688.com")
        browser.find_element("#search-input").send_keys("蓝牙耳机")
        browser.find_element("#search-input").send_keys(Keys.ENTER)
        
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-item"))
        )
        
        items = browser.find_elements(By.CLASS_NAME, "product-item")
        assert len(items) > 0

class TestFullWorkflow:
    """端到端完整流程测试"""

    def test_buy_product_flow(self, authenticated_page):
        # 1. 搜索
        authenticated_page.get("https://www.1688.com")
        authenticated_page.find_element("#search").send_keys("蓝牙耳机")
        
        # 2. 等待搜索结果
        wait = WebDriverWait(authenticated_page, 10)
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "product-item")))
        
        # 3. 点击第一个商品
        authenticated_page.find_elements(By.CLASS_NAME, "product-item")[0].click()
        
        # 4. 切换到商品详情窗口
        authenticated_page.switch_to.window(authenticated_page.window_handles[-1])
        
        # 5. 加入采购车
        authenticated_page.find_element(By.XPATH, "//button[contains(text(),'加入采购车')]").click()
        
        # 6. 验证
        assert "已加入采购车" in authenticated_page.page_source
```

### API集成测试模板

```python
import requests
import pytest

class TestAPIIntegration:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.base_url = "https://api.example.com/v1"
        self.token = self._get_test_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def _get_test_token(self):
        """获取测试用token"""
        resp = requests.post(f"{self.base_url}/auth/login", json={
            "username": "test_user",
            "password": "test_pass"
        })
        return resp.json()["access_token"]

    def test_create_order_via_api(self):
        """API方式创建订单"""
        payload = {
            "items": [
                {"sku_id": "SKU001", "quantity": 2},
            ],
            "address": {
                "name": "张三",
                "phone": "13800000000",
                "address": "北京市朝阳区xxx"
            }
        }
        
        response = requests.post(
            f"{self.base_url}/orders",
            json=payload,
            headers=self.headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "order_id" in data
        assert data["status"] == "pending_payment"

    def test_payment_callback(self, api_client):
        """支付回调处理"""
        payload = {
            "order_id": "ORD123",
            "transaction_id": "TXN456",
            "amount": 199.00,
            "status": "success"
        }
        
        response = requests.post(
            f"{self.base_url}/payments/callback",
            json=payload
        )
        
        assert response.status_code == 200
        
        # 验证订单状态更新
        order = api_client.get(f"{self.base_url}/orders/ORD123")
        assert order.json()["status"] == "paid"

    def test_concurrent_order_creation(self):
        """并发创建订单测试"""
        import concurrent.futures
        
        def create_order():
            return requests.post(
                f"{self.base_url}/orders",
                json={"items": [{"sku_id": "SKU001", "quantity": 1}]},
                headers=self.headers
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_order) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # 验证：10个请求都成功（库存足够情况下）
        success_count = sum(1 for r in results if r.status_code == 201)
        assert success_count == 10
```

### Playwright集成测试模板（JS/TS）

```typescript
// procurement.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Procurement Flow', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('https://www.1688.com/login');
    await page.fill('#username', process.env.TEST_USER);
    await page.fill('#password', process.env.TEST_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/member/**');
  });

  test('complete purchase flow', async ({ page }) => {
    // 搜索
    await page.fill('#search-input', '蓝牙耳机');
    await page.press('#search-input', 'Enter');
    
    // 等待结果
    await page.waitForSelector('.product-item');
    
    // 加入采购车
    await page.click('.product-item:first-child button:has-text("加入采购车")');
    
    // 验证
    await expect(page.locator('.cart-badge')).toHaveText('1');
    
    // 进入采购车
    await page.click('.cart-badge');
    await page.waitForURL('**/cart');
    
    // 提交订单
    await page.click('button:has-text("提交订单")');
    
    // 验证订单创建成功
    await expect(page).toHaveURL(/order_id=/);
  });
});
```

### 集成测试 Checklist

```
[ ] 每个测试独立：不依赖其他测试的数据或状态
[ ] 测试间隔离：每个测试后还原数据（teardown）
[ ] 真实环境优先：能用真实API不用mock，能用真实DB不用fake
[ ] 失败即停：CI中第一个失败就停止后续测试
[ ] 详细日志：记录关键操作和响应，失败时容易定位
[ ] 截图/录屏：测试失败时自动截图或录屏
[ ] 重试机制：网络波动时自动重试（可配置）
[ ] 超时控制：每个操作设置合理超时，避免无限等待
```

---

## 参考

- [tests.md](tests.md) - 更多测试示例
- [mocking.md](mocking.md) - Mocking设计原则
- [interface-design.md](interface-design.md) - 可测试接口设计
