---
name: code-simplification
description: 代码简化 — 识别过度工程，把复杂的代码变简单。简单是代码最重要的质量。
triggers:
  - "代码过于复杂，难以理解"
  - "有人写了过度设计的代码"
  - "需要重构时"
  - "代码评审发现过度工程"
  -
version: 1.0.0 "有重复代码需要抽象"
---

# Code Simplification

## Overview

简单是代码最重要的质量。写出别人能理解的代码比写出"聪明"的代码更重要。过度工程的代码往往比过度简单的代码更难维护。

## When to Use

- 代码难以理解
- 需要重构时
- 发现重复代码
- 代码评审发现过度设计
- 要在"简单方案"和"通用方案"之间选择

## Process

### Phase 1: 评估复杂度

#### 1.1 复杂度指标
- 函数长度（建议<50行）
- 圈复杂度（建议<10）
- 参数数量（建议<4）
- 嵌套深度（建议<3）
- 文件长度（建议<300行）

#### 1.2 理解代码意图
- 这个函数在做什么？
- 有没有更好的名字？
- 注释和代码一致吗？

#### 1.3 识别过度工程信号
- 为了"未来可能的需求"写的代码
- 无法说清楚为什么要这样设计
- 过度抽象导致难以理解
- 用复杂方式实现简单功能

### Phase 2: 简化策略

#### 2.1 函数简化
```python
# 简化前
def process_user_data(user_data: dict) -> dict:
    result = {}
    if user_data.get('name'):
        result['name'] = user_data['name'].strip()
    if user_data.get('email'):
        result['email'] = user_data['email'].strip().lower()
    if user_data.get('age'):
        result['age'] = int(user_data['age'])
    return result

# 简化后
def process_user_data(user_data: dict) -> dict:
    return {
        'name': user_data.get('name', '').strip(),
        'email': user_data.get('email', '').strip().lower(),
        'age': int(user_data.get('age', 0))
    }
```

#### 2.2 去除不必要的抽象
```python
# 简化前
class UserDataProcessor:
    def __init__(self, config: ProcessorConfig):
        self.config = config
    def process(self, data: dict) -> dict:
        return self._process_impl(data)
    def _process_impl(self, data: dict) -> dict:
        # ... 50行代码

# 简化后
def process_user_data(data: dict) -> dict:
    # ... 20行代码
```

#### 2.3 拆分复杂函数
- 一个函数只做一件事
- 每个函数可以被单独测试
- 函数名清晰表达意图

### Phase 3: 验证简化

#### 3.1 功能保持
- 简化后功能必须完全一致
- 运行所有测试确认
- 对比新旧代码的输出

#### 3.2 可读性提升
- 其他人能理解吗？
- 注释是否变少但更清晰？
- 命名是否更直观？

#### 3.3 性能检查
- 简化后性能是否下降？
- 如果性能重要，对比基准测试

## Common Rationalizations

| 常见借口 | 真相 | 反制 |
|---------|------|------|
| "这个设计更通用，以后能扩展" | YAGNI原则：不要写你不需要的 | 先简单，需求来时再扩展 |
| "这段代码我以后还要用" | 实际上很少会复用 | DRY，但不要过度抽象 |
| "简单代码显得我不专业" | 专业是能解决实际问题 | 简单是最难写的 |
| "这个框架就是这样用的" | 框架不等于最佳实践 | 基于具体场景判断 |

## Red Flags

- 无法在30秒内解释一个函数
- 有"以后可能用到"的代码
- 过度使用设计模式
- 函数名是动词而非描述
- 有注释说明"这段代码很复杂"
- 测试比实现代码还难懂
- 重构后代码比之前还复杂

---

# 重构模式库 (Refactoring Patterns)

## _extract_method

**问题**: 函数过长，内部有可以分组的概念

**方法**: 将一段代码提取为独立函数

**示例**:
```python
# 重构前
def print_report(employees: list[Employee]) -> None:
    print("=== Employee Report ===")
    total_salary = 0
    for emp in employees:
        print(f"{emp.name}: ${emp.salary}")
        total_salary += emp.salary
    print(f"Total: ${total_salary}")

# 重构后
def print_report(employees: list[Employee]) -> None:
    print("=== Employee Report ===")
    print_employee_list(employees)
    print_total(get_total_salary(employees))

def print_employee_list(employees: list[Employee]) -> None:
    for emp in employees:
        print(f"{emp.name}: ${emp.salary}")

def get_total_salary(employees: list[Employee]) -> int:
    return sum(emp.salary for emp in employees)

def print_total(total: int) -> None:
    print(f"Total: ${total}")
```

## _rename

**问题**: 名称不能表达意图

**方法**: 重命名变量/函数/类

**示例**:
```python
# 重构前 - 名称模糊
def process(d: dict) -> dict:
    r = {}
    for k, v in d.items():
        if v > 0:
            r[k] = v * 1.1
    return r

# 重构后 - 名称清晰
def apply_discount(prices: dict[str, float]) -> dict[str, float]:
    discounted = {}
    for product, price in prices.items():
        if price > 0:
            discounted[product] = price * 1.1
    return discounted
```

## _inline

**问题**: 过度抽象，中间层没有价值

**方法**: 内联消除中间函数

**示例**:
```python
# 重构前 - 无意义的间接层
def get_default_config() -> dict:
    return _load_config_internal()

def _load_config_internal() -> dict:
    return {"timeout": 30, "retries": 3}

config = get_default_config()

# 重构后 - 直接使用
config = {"timeout": 30, "retries": 3}
```

## _replace_conditional_with_polymorphism

**问题**: type-based dispatch 用 if/elif 实现

**方法**: 用多态替代类型判断

**示例**:
```python
# 重构前
def calculate_area(shape: dict) -> float:
    if shape["type"] == "rectangle":
        return shape["width"] * shape["height"]
    elif shape["type"] == "circle":
        return 3.14 * shape["radius"] ** 2
    elif shape["type"] == "triangle":
        return 0.5 * shape["base"] * shape["height"]

# 重构后
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

class Rectangle(Shape):
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
    def area(self) -> float:
        return self.width * self.height

class Circle(Shape):
    def __init__(self, radius: float):
        self.radius = radius
    def area(self) -> float:
        return 3.14 * self.radius ** 2
```

## _consolidate_duplicate_conditional

**问题**: 重复的条件检查

**方法**: 合并相同逻辑的条件分支

**示例**:
```python
# 重构前
def process_order(order: Order) -> None:
    if order.status == "pending":
        send_notification(order)
        update_inventory(order)
    if order.status == "confirmed":
        send_notification(order)
        update_inventory(order)
    if order.status == "shipped":
        send_notification(order)
        update_inventory(order)

# 重构后
def process_order(order: Order) -> None:
    if order.status in ("pending", "confirmed", "shipped"):
        send_notification(order)
        update_inventory(order)
```

## _introduce_parameter_object

**问题**: 参数过多（>3个）

**方法**: 将相关参数封装为对象

**示例**:
```python
# 重构前
def create_user(name: str, email: str, age: int, phone: str, address: str) -> User: ...

# 重构后
@dataclass
class UserRegistration:
    name: str
    email: str
    age: int
    phone: str
    address: str

def create_user(registration: UserRegistration) -> User: ...
```

## _remove_dead_code

**问题**: 有从未调用的代码

**方法**: 删除它

```python
# 重构前
def _unused_helper(x: int) -> int:
    return x * 2

def main():
    print("hello")

# 重构后
def main():
    print("hello")
```

---

# 长函数拆分策略 (Long Function Splitting)

## 拆分信号

| 信号 | 说明 |
|------|------|
| 行数 > 50 | 函数过长 |
| 嵌套深度 > 3 | 过度缩进 |
| 参数 > 4 | 可能有内聚性问题 |
| 需要注释说明"这段做什么" | 该拆了 |
| 多个抽象层次混在一起 | 分层 |

## 拆分步骤

### Step 1: 识别代码块

找到"这段代码在做什么"能回答的部分：

```python
def generate_monthly_report(data: list[Transaction]) -> str:
    # === 步骤1: 过滤数据 ===
    monthly = [t for t in data if t.date.month == current_month()]
    
    # === 步骤2: 计算汇总 ===
    total = sum(t.amount for t in monthly)
    by_category = {}
    for t in monthly:
        by_category.setdefault(t.category, 0)
        by_category[t.category] += t.amount
    
    # === 步骤3: 格式化输出 ===
    lines = ["Monthly Report"]
    lines.append(f"Total: ${total:.2f}")
    for cat, amt in by_category.items():
        lines.append(f"  {cat}: ${amt:.2f}")
    
    return "\n".join(lines)
```

### Step 2: 提取每个块为独立函数

```python
def generate_monthly_report(data: list[Transaction]) -> str:
    monthly = filter_current_month(data)
    total = calculate_total(monthly)
    by_category = group_by_category(monthly)
    return format_report(total, by_category)

def filter_current_month(data: list[Transaction]) -> list[Transaction]:
    return [t for t in data if t.date.month == current_month()]

def calculate_total(transactions: list[Transaction]) -> float:
    return sum(t.amount for t in transactions)

def group_by_category(transactions: list[Transaction]) -> dict[str, float]:
    result = {}
    for t in transactions:
        result.setdefault(t.category, 0)
        result[t.category] += t.amount
    return result

def format_report(total: float, by_category: dict[str, float]) -> str:
    lines = ["Monthly Report"]
    lines.append(f"Total: ${total:.2f}")
    for cat, amt in by_category.items():
        lines.append(f"  {cat}: ${amt:.2f}")
    return "\n".join(lines)
```

### Step 3: 验证

- [ ] 每个函数是否只做一件事？
- [ ] 函数名是否描述了它在做什么？
- [ ] 函数是否可以独立测试？
- [ ] 参数是否减少了？

## 常见模式

### 3.1 循环拆分

```python
# 重构前 - 循环内做太多事
for item in items:
    validate(item)
    transform(item)
    save(item)
    log(item)

# 重构后 - 先集合再处理
validated = [validate(i) for i in items]
transformed = [transform(i) for i in validated]
for i in transformed:
    save(i)
    log(i)
```

### 3.2 条件分支拆分

```python
# 重构前
def handle(event: Event) -> None:
    if event.type == "click":
        highlight(event.target)
        update_history(event)
        notify_listeners("click", event)
    elif event.type == "keypress":
        highlight(event.target)
        update_history(event)
        notify_listeners("keypress", event)

# 重构后
def handle(event: Event) -> None:
    pre_handler(event)
    specific_handler(event)
    post_handler(event)

def specific_handler(event: Event) -> None:
    handlers = {"click": handle_click, "keypress": handle_keypress}
    handlers[event.type](event)
```

### 3.3 递归终止条件提取

```python
# 重构前
def fibonacci(n: int) -> int:
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n-1) + fibonacci(n-2)

# 重构后
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

---

# 重复代码消除 (Duplicate Code Elimination)

## 重复类型

| 类型 | 严重程度 | 解决方案 |
|------|----------|----------|
| 完全相同 | 高 | 提取函数 |
| 结构相同内容不同 | 中 | 参数化/模板 |
| 表面相同语义不同 | 低 | 可能是巧合，不需要消除 |

## 消除策略

### 4.1 提取函数

**完全相同的代码** -> 提取为共享函数

```python
# 重构前
def process_order(order: Order) -> None:
    email = order.customer_email
    if email and "@" in email:
        send_email(email, "Order confirmed")
    ...

def process_inquiry(inquiry: Inquiry) -> None:
    email = inquiry.email
    if email and "@" in email:
        send_email(email, "Inquiry received")
    ...

# 重构后
def send_if_valid(email: str, message: str) -> None:
    if email and "@" in email:
        send_email(email, message)

def process_order(order: Order) -> None:
    send_if_valid(order.customer_email, "Order confirmed")
    ...

def process_inquiry(inquiry: Inquiry) -> None:
    send_if_valid(inquiry.email, "Inquiry received")
    ...
```

### 4.2 参数化

**结构相同内容不同** -> 提取参数

```python
# 重构前
def validate_username(username: str) -> bool:
    if len(username) < 3:
        return False
    if len(username) > 20:
        return False
    if not username.isalnum():
        return False
    return True

def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if len(password) > 128:
        return False
    if password.isalnum():
        return False
    return True

# 重构后
def validate_length(value: str, min_len: int, max_len: int) -> bool:
    return min_len <= len(value) <= max_len

def validate_username(username: str) -> bool:
    return (validate_length(username, 3, 20) and username.isalnum())

def validate_password(password: str) -> bool:
    return (validate_length(password, 8, 128) and not password.isalnum())
```

### 4.3 模板方法模式

**步骤相同但每步实现不同** -> 模板方法

```python
# 重构前
def run_backup_mysql() -> None:
    connect("mysql")
    execute("SELECT * FROM users")
    write_to_file("backup.sql")
    disconnect()

def run_backup_postgres() -> None:
    connect("postgres")
    execute("SELECT * FROM users")
    write_to_file("backup.sql")
    disconnect()

# 重构后
from abc import ABC, abstractmethod

class BackupStrategy(ABC):
    def run_backup(self) -> None:
        self.connect()
        data = self.query()
        self.save(data)
        self.disconnect()
    
    @abstractmethod
    def connect(self) -> None: ...
    
    @abstractmethod
    def query(self) -> str: ...
    
    def save(self, data: str) -> None:
        write_to_file("backup.sql")
    
    def disconnect(self) -> None:
        pass

class MySQLBackup(BackupStrategy):
    def connect(self) -> None: connect("mysql")
    def query(self) -> str: return execute("SELECT * FROM users")
```

### 4.4 合并相似分支

```python
# 重构前
def get_discount(customer: Customer) -> float:
    if customer.type == "premium":
        if customer.years > 5:
            return 0.30
        elif customer.years > 2:
            return 0.20
        else:
            return 0.15
    elif customer.type == "regular":
        if customer.years > 5:
            return 0.15
        elif customer.years > 2:
            return 0.10
        else:
            return 0.05

# 重构后
def get_discount(customer: Customer) -> float:
    rates = {"premium": 0.30, "regular": 0.05}
    thresholds = [(5, 0.30), (2, 0.20), (0, 0.15)]
    
    base = rates[customer.type]
    for years_threshold, rate in thresholds:
        if customer.years > years_threshold:
            return rate if customer.type == "premium" else rate * 0.5
    return base
```

---

# 1688自动化代码简化

## 1688场景特点

- 批量操作：需要处理大量商品/订单
- 页面交互：登录、搜索、翻页、填写表单
- 数据提取：从列表页/详情页提取结构化数据
- 网络请求：调用1688开放API

## 简化原则

### 5.1 避免过度封装

```python
# ❌ 过度封装 - 1688场景不需要
class AlibabaClient:
    def __init__(self, config: AlibabaConfig):
        self.http_client = HttpClient(config)
        self.auth_manager = AuthManager(config)
        self.rate_limiter = RateLimiter(config)
        
    def get_product(self, product_id: str) -> Product:
        return self._fetch_with_retry(product_id)

# ✅ 直接简单 - 1688场景适合
def get_product(product_id: str) -> dict:
    resp = requests.get(f"https://api.1688.com/product/{product_id}")
    return resp.json()
```

### 5.2 简化批量处理

```python
# ❌ 过度设计 - 用类封装每个商品
class ProductProcessor:
    def __init__(self, product: dict): self.product = product
    def extract_title(self) -> str: return self.product.get("title", "")
    def extract_price(self) -> float: return float(self.product.get("price", 0))
    
products = [ProductProcessor(p).extract_title() for p in product_list]

# ✅ 简单直接 - 用dict操作
titles = [p.get("title", "") for p in product_list]
prices = [float(p.get("price", 0)) for p in product_list]
```

### 5.3 简化分页逻辑

```python
# ❌ 过度封装
class PagedResultIterator:
    def __init__(self, client, endpoint): self.client = client; self.page = 1
    def __iter__(self): return self
    def __next__(self):
        result = self.client.fetch(self.endpoint, self.page)
        if not result: raise StopIteration
        self.page += 1
        return result

# ✅ 简单明了
def fetch_all_pages(client, endpoint):
    page = 1
    while True:
        result = client.fetch(endpoint, page)
        if not result:
            break
        yield from result
        page += 1
```

### 5.4 简化数据提取

```python
# ❌ 过度设计 - 每个字段一个函数
def extract_product_data(raw_html: str) -> dict:
    return {
        "title": extract_title(raw_html),
        "price": extract_price(raw_html),
        "sales": extract_sales(raw_html),
    }

# ✅ 简单组合
def extract_product_data(raw_html: str) -> dict:
    title = re.search(r'"title":"([^"]+)"', raw_html)
    price = re.search(r'"price":"([\d.]+)"', raw_html)
    sales = re.search(r'"saleCount":(\d+)', raw_html)
    return {
        "title": title.group(1) if title else "",
        "price": float(price.group(1)) if price else 0,
        "sales": int(sales.group(1)) if sales else 0,
    }
```

### 5.5 常见1688简化模式

| 场景 | 过度工程 | 简化方案 |
|------|----------|----------|
| 单次API调用 | 封装Client类 | 直接requests调用 |
| 简单数据提取 | BeautifulSoup解析器类 | 正则表达式 |
| 批量处理 | 生成器封装类 | list comprehension |
| 错误处理 | 异常类层次结构 | 简单if检查 |
| 配置管理 | 配置加载器+验证 | 简单dict |

---

# Verification

验证清单：

- [ ] 圈复杂度降低
- [ ] 函数长度缩短
- [ ] 测试覆盖率没有下降
- [ ] 功能完全一致
- [ ] 代码意图更清晰
- [ ] 没有引入新的概念
- [ ] 其他开发者能理解