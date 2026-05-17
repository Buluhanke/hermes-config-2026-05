---
name: data-analyzer
description: 数据分析与可视化 — 读取CSV/Excel文件，生成图表（折线图、柱状图、饼图、散点图、热力图等），支持matplotlib/plotly/seaborn。触发：数据分析、可视化、画图、生成图表。
triggers:
  - 数据分析
version: 1.0.0
---
name: data-analyzer
description: 数据分析与可视化 — 读取CSV/Excel文件，生成图表（折线图、柱状图、饼图、散点图、热力图等），支持matplotlib/plotly/seaborn。触发：数据分析、可视化、画图、生成图表。
triggers:
  - 数据分析
  - 可视化
  - 画图
  - 生成图表
  - 打开文件分析
  - csv分析
  - excel分析
  - 数据透视
  - 图表
---

# DataAnalyzer 数据分析与可视化

## 核心能力
- 读取 CSV / Excel / JSON 文件
- 数据清洗与处理（空值、排序、分组）
- 生成多种图表：折线图、柱状图、饼图、散点图、热力图
- 支持 matplotlib / plotly / seaborn
- 输出为 PNG 图片 或 交互式 HTML

## 使用方式

### 方式1：发送文件
直接发送 CSV/Excel 文件，说"分析这个数据"或"生成可视化图表"。

### 方式2：用 terminal 执行 Python 脚本

#### 读取 CSV
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("your_file.csv")
print(df.head())        # 前5行
print(df.describe())    # 统计摘要
print(df.dtypes)        # 列类型
```

#### 折线图
```python
df.plot(x='日期列', y='数值列', kind='line')
plt.title('标题')
plt.savefig('output.png', dpi=150)
plt.close()
```

#### 柱状图
```python
df.plot(x='类别列', y='数值列', kind='bar')
plt.savefig('output.png', dpi=150)
plt.close()
```

#### 饼图
```python
df['类别列'].value_counts().plot(kind='pie', autopct='%1.1f%%')
plt.savefig('output.png', dpi=150)
plt.close()
```

#### 热力图（相关性矩阵）
```python
import seaborn as sns
sns.heatmap(df.corr(), annot=True, cmap='coolwarm')
plt.savefig('output.png', dpi=150)
plt.close()
```

#### 散点图
```python
df.plot(x='列1', y='列2', kind='scatter')
plt.savefig('output.png', dpi=150)
plt.close()
```

#### 交互式图表（plotly）
```python
import plotly.express as px
fig = px.line(df, x='日期', y='数值', title='标题')
fig.write_html('output.html')  # 交互式HTML
fig.write_image('output.png')  # 静态图片
```

## 数据清洗
```python
# 删除空值
df.dropna()

# 填充空值
df.fillna(0)

# 按列排序
df.sort_values('列名')

# 分组聚合
df.groupby('类别列').sum()

# 筛选
df[df['列名'] > 100]

# 新增计算列
df['新列'] = df['列1'] / df['列2']
```

## 输出路径
图表默认保存到 `~/.hermes/data_output/`，文件名包含时间戳防止覆盖。

## 常用文件路径
- 用户主目录: `/Users/aimac/`
- 下载文件夹: `/Users/aimac/Downloads/`
- 桌面: `/Users/aimac/Desktop/`

---

## 扩展模块 A：1688采购数据分析模板

### 数据结构规范

1688采购数据通常包含以下核心字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `product_name` | str | 商品名称 |
| `supplier` | str | 供应商名称 |
| `price` | float | 单价（元） |
| `moq` | int | 最小起订量 |
| `sales` | int | 销量 |
| `rating` | float | 评分（1-5） |
| `province` | str | 省份 |
| `category` | str | 类目 |
| `date` | str | 日期（YYYY-MM-DD） |

### 数据导入

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 从CSV读取1688采购数据
df = pd.read_csv("1688_procurement.csv")
print(f"数据量: {len(df)} 条")
print(df.describe())
print(df.head())
```

### 采购分析仪表盘

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta
import os

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

os.makedirs("~/.hermes/data_output", exist_ok=True)

# 示例数据（实际使用时替换为 pd.read_csv）
data = {
    'product_name': ['蓝牙耳机A', '蓝牙耳机B', '充电线A', '充电线B', '手机壳A', '手机壳B'],
    'supplier': ['深圳XX电子', '东莞XX科技', '杭州XX实业', '宁波XX贸易', '广州XX皮具', '深圳XX塑胶'],
    'price': [45.0, 42.5, 8.5, 7.8, 12.0, 10.5],
    'moq': [50, 100, 200, 150, 100, 200],
    'sales': [1200, 3500, 8000, 5200, 3000, 4500],
    'rating': [4.5, 4.2, 4.8, 4.6, 4.3, 4.7],
    'province': ['广东', '广东', '浙江', '浙江', '广东', '广东'],
    'category': ['数码配件', '数码配件', '数码配件', '数码配件', '数码配件', '数码配件'],
}
df = pd.DataFrame(data)

# ========== 1688采购分析模板 ==========

fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('1688采购数据分析看板', fontsize=20, fontweight='bold', y=1.02)

# 1. 供应商数量与评分分布
ax1 = axes[0, 0]
supplier_stats = df.groupby('supplier').agg({'rating': 'mean', 'sales': 'sum'}).reset_index()
colors = sns.color_palette("husl", len(supplier_stats))
bars = ax1.bar(supplier_stats['supplier'], supplier_stats['rating'], color=colors)
ax1.set_title('各供应商评分', fontsize=14)
ax1.set_ylabel('评分')
ax1.set_ylim(0, 5)
ax1.tick_params(axis='x', rotation=45)
for bar, val in zip(bars, supplier_stats['rating']):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, f'{val:.1f}', ha='center', va='bottom', fontsize=10)

# 2. 价格 vs 销量 散点图
ax2 = axes[0, 1]
scatter = ax2.scatter(df['price'], df['sales'], c=df['rating'], cmap='RdYlGn', s=150, alpha=0.7, edgecolors='black')
ax2.set_title('价格-销量关系（颜色=评分）', fontsize=14)
ax2.set_xlabel('价格（元）')
ax2.set_ylabel('销量')
plt.colorbar(scatter, ax=ax2, label='评分')
for i, row in df.iterrows():
    ax2.annotate(row['product_name'], (row['price'], row['sales']), fontsize=8, ha='center', va='bottom')

# 3. 类目采购量饼图
ax3 = axes[0, 2]
category_sales = df.groupby('category')['sales'].sum()
ax3.pie(category_sales, labels=category_sales.index, autopct='%1.1f%%', colors=sns.color_palette("pastel", len(category_sales)), startangle=90)
ax3.set_title('类目采购量占比', fontsize=14)

# 4. 各省供应商数量
ax4 = axes[1, 0]
province_count = df.groupby('province')['supplier'].count()
bars = ax4.bar(province_count.index, province_count.values, color=sns.color_palette("Blues", len(province_count)))
ax4.set_title('各省供应商数量', fontsize=14)
ax4.set_ylabel('供应商数量')
for bar, val in zip(bars, province_count.values):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, str(val), ha='center', va='bottom')

# 5. MOQ vs 价格 关系
ax5 = axes[1, 1]
ax5.scatter(df['moq'], df['price'], s=df['sales']/50, alpha=0.6, c='steelblue', edgecolors='black')
ax5.set_title('MOQ-价格关系（气泡大小=销量）', fontsize=14)
ax5.set_xlabel('最小起订量（MOQ）')
ax5.set_ylabel('价格（元）')
for i, row in df.iterrows():
    ax5.annotate(row['supplier'][:6], (row['moq'], row['price']), fontsize=8, ha='center', va='bottom')

# 6. 综合评分TOP供应商
ax6 = axes[1, 2]
top_suppliers = supplier_stats.sort_values('rating', ascending=True).tail(5)
colors = ['#2ecc71' if r >= 4.5 else '#f39c12' if r >= 4.0 else '#e74c3c' for r in top_suppliers['rating']]
bars = ax6.barh(top_suppliers['supplier'], top_suppliers['rating'], color=colors)
ax6.set_title('供应商综合评分排名', fontsize=14)
ax6.set_xlabel('评分')
ax6.set_xlim(0, 5)
for bar, val in zip(bars, top_suppliers['rating']):
    ax6.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2, f'{val:.1f}', va='center', fontsize=10)

plt.tight_layout()
output_path = os.path.expanduser("~/.hermes/data_output/1688_procurement_dashboard.png")
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"图表已保存: {output_path}")
```

---

## 扩展模块 B：供应商比价图表

### 多供应商价格对比（分组柱状图）

```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

os.makedirs("~/.hermes/data_output", exist_ok=True)

# 示例数据：同类产品多供应商报价
data = {
    'product': ['蓝牙耳机', '蓝牙耳机', '蓝牙耳机', '充电线', '充电线', '充电线', '手机壳', '手机壳', '手机壳'],
    'supplier': ['深圳XX电子', '东莞XX科技', '杭州XX实业', '深圳XX电子', '宁波XX贸易', '广州XX实业', '深圳XX皮具', '东莞XX塑胶', '杭州XX实业'],
    'price': [45.0, 42.5, 48.0, 8.5, 7.8, 9.2, 12.0, 10.5, 11.8],
    'moq': [50, 100, 30, 200, 150, 100, 100, 200, 50],
    'rating': [4.5, 4.2, 4.8, 4.8, 4.6, 4.4, 4.3, 4.7, 4.5],
}
df = pd.DataFrame(data)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle('供应商比价分析', fontsize=18, fontweight='bold')

# 1. 同产品多供应商价格柱状对比
ax1 = axes[0]
products = df['product'].unique()
x = np.arange(len(products))
width = 0.25
for i, supplier in enumerate(df['supplier'].unique()):
    supplier_data = df[df['supplier'] == supplier].set_index('product')['price']
    prices = [supplier_data.get(p, 0) for p in products]
    ax1.bar(x + i*width, prices, width, label=supplier[:8])

ax1.set_title('同类产品供应商价格对比', fontsize=14)
ax1.set_xticks(x + width)
ax1.set_xticklabels(products)
ax1.set_ylabel('价格（元）')
ax1.legend(fontsize=8)

# 2. 价格-评分气泡图（性价比视图）
ax2 = axes[1]
for product in df['product'].unique():
    subset = df[df['product'] == product]
    ax2.scatter(subset['price'], subset['rating'], s=subset['moq']/2, alpha=0.7, label=product)
    for _, row in subset.iterrows():
        ax2.annotate(row['supplier'][:6], (row['price'], row['rating']), fontsize=8)

ax2.set_title('价格-评分性价比气泡图', fontsize=14)
ax2.set_xlabel('价格（元）')
ax2.set_ylabel('评分')
ax2.legend(fontsize=8)

# 3. 最低价供应商排名
ax3 = axes[2]
min_price = df.groupby('product')['price'].idxmin()
best_prices = df.loc[min_price].sort_values('price')
colors = ['#2ecc71' if r >= 4.5 else '#f39c12' if r >= 4.0 else '#e74c3c' for r in best_prices['rating']]
bars = ax3.barh(best_prices['product'] + '\n(' + best_prices['supplier'].str[:8] + ')', best_prices['price'], color=colors)
ax3.set_title('各产品最低价供应商', fontsize=14)
ax3.set_xlabel('价格（元）')
for bar, (_, row) in zip(bars, best_prices.iterrows()):
    ax3.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2, f'{row["price"]:.1f}元 | 评分:{row["rating"]}', va='center', fontsize=9)

plt.tight_layout()
output_path = os.path.expanduser("~/.hermes/data_output/supplier_comparison.png")
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"供应商比价图表已保存: {output_path}")
```

### 供应商竞争力雷达图

```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from math import pi
import os

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']

os.makedirs("~/.hermes/data_output", exist_ok=True)

# 供应商综合能力评分数据
suppliers = ['深圳XX电子', '东莞XX科技', '杭州XX实业']
categories = ['价格竞争力', '产品质量', '交货速度', '售后服务', '起订量灵活度']

# 各维度评分（0-10分）
scores = {
    '深圳XX电子': [7, 9, 8, 7, 6],
    '东莞XX科技': [9, 7, 7, 8, 8],
    '杭州XX实业': [6, 8, 9, 9, 7],
}

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

angles = [n / float(len(categories)) * 2 * pi for n in range(len(categories))]
angles += angles[:1]

colors = ['#3498db', '#e74c3c', '#2ecc71']
for i, (supplier, score) in enumerate(scores.items()):
    values = score + score[:1]
    ax.plot(angles, values, 'o-', linewidth=2, label=supplier, color=colors[i])
    ax.fill(angles, values, alpha=0.15, color=colors[i])

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=11)
ax.set_ylim(0, 10)
ax.set_title('供应商综合能力雷达图', fontsize=16, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
ax.grid(color='grey', linestyle='--', linewidth=0.5)

output_path = os.path.expanduser("~/.hermes/data_output/supplier_radar.png")
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"供应商雷达图已保存: {output_path}")
```

---

## 扩展模块 C：价格趋势预测

### 历史价格折线图 + 简单移动平均预测

```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import os

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

os.makedirs("~/.hermes/data_output", exist_ok=True)

# 模拟历史价格数据（实际使用时 pd.read_csv 读取）
dates = pd.date_range(start='2024-01-01', end='2025-05-17', freq='D')
np.random.seed(42)

# 模拟3个产品的历史价格走势（含季节性波动）
data = {
    'date': dates.tolist() * 3,
    'product': ['蓝牙耳机'] * len(dates) + ['充电线'] * len(dates) + ['手机壳'] * len(dates),
    'price': (
        list(45 + 5*np.sin(np.linspace(0, 8*np.pi, len(dates))) + np.cumsum(np.random.randn(len(dates))*0.5)) +
        list(8.5 + 1.5*np.sin(np.linspace(0, 8*np.pi, len(dates))) + np.cumsum(np.random.randn(len(dates))*0.2)) +
        list(11 + 2*np.sin(np.linspace(0, 8*np.pi, len(dates))) + np.cumsum(np.random.randn(len(dates))*0.3))
    )
}
df = pd.DataFrame(data)

# ========== 价格趋势预测 ==========

forecast_days = 30  # 预测未来30天

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('价格趋势预测分析', fontsize=18, fontweight='bold')

for idx, product in enumerate(['蓝牙耳机', '充电线', '手机壳']):
    ax = axes[idx // 2, idx % 2]
    subset = df[df['product'] == product].copy()
    subset = subset.set_index('date').sort_index()

    # 移动平均（7日、30日）
    subset['MA7'] = subset['price'].rolling(7).mean()
    subset['MA30'] = subset['price'].rolling(30).mean()

    # 简单线性回归预测未来
    from numpy.polynomial import polynomial as P
    x = np.arange(len(subset))
    y = subset['price'].values
    coef = np.polyfit(x, y, 1)
    poly = np.poly1d(coef)

    # 未来预测
    future_x = np.arange(len(subset), len(subset) + forecast_days)
    future_dates = pd.date_range(start=subset.index[-1] + timedelta(days=1), periods=forecast_days)
    future_prices = poly(future_x)

    # 绘制历史
    ax.plot(subset.index, subset['price'], alpha=0.3, label='历史价格', color='steelblue')
    ax.plot(subset.index, subset['MA7'], label='7日均线', color='steelblue', linewidth=1.5)
    ax.plot(subset.index, subset['MA30'], label='30日均线', color='navy', linewidth=2)

    # 绘制预测
    ax.plot(future_dates, future_prices, 'r--', label='线性预测', linewidth=2)

    # 置信区间（简单估算 ± 2倍标准差）
    std = subset['price'].std()
    ax.fill_between(future_dates, future_prices - 2*std, future_prices + 2*std, alpha=0.2, color='red', label='置信区间')

    ax.set_title(f'{product} 价格趋势', fontsize=14)
    ax.set_xlabel('日期')
    ax.set_ylabel('价格（元）')
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)

# 第4个图：预测汇总表
ax = axes[1, 1]
ax.axis('off')
summary_data = []
for product in ['蓝牙耳机', '充电线', '手机壳']:
    subset = df[df['product'] == product].copy().set_index('date').sort_index()
    coef = np.polyfit(np.arange(len(subset)), subset['price'].values, 1)
    trend = '上涨' if coef[0] > 0 else '下跌'
    current_price = subset['price'].iloc[-1]
    pred_price = poly(future_x[-1]) if product == '蓝牙耳机' else (poly(future_x[-1]) if product == '充电线' else poly(future_x[-1]))
    summary_data.append([product, f'{current_price:.2f}', trend, f'{coef[0]*30:+.2f}/月'])

table = ax.table(
    cellText=summary_data,
    colLabels=['产品', '当前价格', '趋势', '月均变化'],
    cellLoc='center',
    loc='center',
    colWidths=[0.3, 0.25, 0.2, 0.25]
)
table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1.2, 2)
ax.set_title('价格趋势预测汇总', fontsize=14, fontweight='bold', y=0.95)

plt.tight_layout()
output_path = os.path.expanduser("~/.hermes/data_output/price_forecast.png")
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"价格趋势预测已保存: {output_path}")
```

### 价格预测使用说明

```python
# 导入预测所需库
import pandas as pd
import numpy as np
from numpy.polynomial import polynomial as P
from datetime import timedelta

# 读取实际历史数据
df = pd.read_csv("price_history.csv")
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['product', 'date'])

# 预测函数
def predict_price(product_df, forecast_days=30):
    """给定产品历史价格，返回未来预测"""
    product_df = product_df.sort_values('date').reset_index(drop=True)
    x = np.arange(len(product_df))
    y = product_df['price'].values

    # 线性回归
    coef = np.polyfit(x, y, 1)
    poly = np.poly1d(coef)

    # 预测
    future_x = np.arange(len(product_df), len(product_df) + forecast_days)
    future_dates = pd.date_range(start=product_df['date'].max() + timedelta(days=1), periods=forecast_days)
    future_prices = poly(future_x)

    # 趋势判断
    trend_per_day = coef[0]
    trend_direction = '上涨' if trend_per_day > 0 else '下跌'

    return {
        'forecast_dates': future_dates,
        'forecast_prices': future_prices,
        'trend': trend_direction,
        'monthly_change': trend_per_day * 30,
        'current_price': y[-1],
        'predicted_price_30d': future_prices[-1],
    }

# 对每个产品预测
for product in df['product'].unique():
    result = predict_price(df[df['product'] == product])
    print(f"{product}: 当前价={result['current_price']:.2f}, "
          f"30天后预测={result['predicted_price_30d']:.2f}, "
          f"趋势={result['trend']}({result['monthly_change']:+.2f}/月)")
```

---

## 扩展模块 D：老板汇报数据看板

### 一页式汇报图表（高可读性）

```python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

os.makedirs("~/.hermes/data_output", exist_ok=True)

# 模拟采购汇总数据（替换为实际数据）
summary = {
    'total_suppliers': 12,
    'total_products': 48,
    'total_purchase_amount': 1250000,
    'avg_price': 26.04,
    'top_supplier': '深圳XX电子',
    'avg_lead_time': 7.2,
    'on_time_rate': 94.5,
}

monthly_data = {
    'month': ['2024-09', '2024-10', '2024-11', '2024-12', '2025-01', '2025-02', '2025-03', '2025-04', '2025-05'],
    'purchase_amount': [98000, 112000, 105000, 138000, 125000, 110000, 135000, 142000, 148000],
    'order_count': [42, 51, 48, 62, 55, 48, 61, 65, 68],
}
monthly_df = pd.DataFrame(monthly_data)

fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor('#f8f9fa')

# 标题区
ax_title = fig.add_axes([0, 0.88, 1, 0.1])
ax_title.axis('off')
ax_title.text(0.5, 0.6, '采购数据月度汇报', fontsize=24, fontweight='bold', ha='center', va='center', color='#2c3e50')
ax_title.text(0.5, 0.1, f'汇报周期：2024年9月 - 2025年5月 | 汇报日期：2025-05-17', fontsize=11, ha='center', va='center', color='#7f8c8d')

# KPI卡片区（顶部）
kpi_data = [
    ('供应商总数', f"{summary['total_suppliers']}家", '#3498db'),
    ('采购商品数', f"{summary['total_products']}个", '#2ecc71'),
    ('采购总金额', f"¥{summary['total_purchase_amount']:,}", '#e74c3c'),
    ('平均单价', f"¥{summary['avg_price']:.2f}", '#9b59b6'),
    ('平均交期', f"{summary['avg_lead_time']}天", '#f39c12'),
    ('准时率', f"{summary['on_time_rate']}%", '#1abc9c'),
]
kpi_axes = []
for i, (label, value, color) in enumerate(kpi_data):
    ax_kpi = fig.add_axes([0.03 + i*0.155, 0.72, 0.14, 0.14])
    kpi_axes.append(ax_kpi)
    ax_kpi.set_facecolor(color)
    ax_kpi.text(0.5, 0.7, value, fontsize=16, fontweight='bold', ha='center', va='center', color='white', transform=ax_kpi.transAxes)
    ax_kpi.text(0.5, 0.25, label, fontsize=10, ha='center', va='center', color='white', transform=ax_kpi.transAxes)
    ax_kpi.set_xticks([])
    ax_kpi.set_yticks([])
    for spine in ax_kpi.spines.values():
        spine.set_visible(False)

# 月度采购金额趋势（主图）
ax_main = fig.add_axes([0.05, 0.35, 0.6, 0.32])
ax_main.set_facecolor('white')
bars = ax_main.bar(monthly_df['month'], monthly_df['purchase_amount'], color='#3498db', alpha=0.85, edgecolor='white')

# 添加趋势线
z = np.polyfit(range(len(monthly_df)), monthly_df['purchase_amount'], 1)
p = np.poly1d(z)
ax_main.plot(monthly_df['month'], p(range(len(monthly_df))), 'r--', linewidth=2.5, label=f'趋势线(斜率:{z[0]:.0f})')

for bar, val in zip(bars, monthly_df['purchase_amount']):
    ax_main.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2000, f'¥{val/1000:.0f}K', ha='center', va='bottom', fontsize=9)

ax_main.set_title('月度采购金额趋势', fontsize=14, fontweight='bold', color='#2c3e50', pad=10)
ax_main.set_ylabel('采购金额（元）', fontsize=10)
ax_main.legend(fontsize=9)
ax_main.grid(axis='y', alpha=0.3)
ax_main.tick_params(axis='x', rotation=45)

# 右侧：月度订单数量
ax_orders = fig.add_axes([0.68, 0.35, 0.28, 0.32])
ax_orders.set_facecolor('white')
ax_orders.text(0.5, 1.02, '月度订单数量', fontsize=13, fontweight='bold', ha='center', va='top', color='#2c3e50', transform=ax_orders.transAxes)
colors = ['#e74c3c' if v == max(monthly_df['order_count']) else '#3498db' for v in monthly_df['order_count']]
ax_orders.bar(monthly_df['month'], monthly_df['order_count'], color=colors, alpha=0.85, edgecolor='white')
ax_orders.set_ylabel('订单数', fontsize=10)
ax_orders.tick_params(axis='x', rotation=45)
ax_orders.grid(axis='y', alpha=0.3)

# 底部：关键洞察
ax_insights = fig.add_axes([0.05, 0.08, 0.9, 0.2])
ax_insights.set_facecolor('#2c3e50')
ax_insights.set_xticks([])
ax_insights.set_yticks([])

insights_text = [
    f"📊 核心发现",
    f"• 近9个月采购金额呈上升趋势，月均增长约 ¥{z[0]*30:.0f} 元",
    f"• 5月采购金额最高（¥148,000），订单数量最多（68单），建议提前备货",
    f"• 核心供应商「{summary['top_supplier']}」表现稳定，建议深化合作",
    f"• 准时交付率 {summary['on_time_rate']}% 表现良好，建议继续保持",
    f"• 当前平均交期 {summary['avg_lead_time']} 天，建议对交期超过10天的供应商重点跟进",
]
for i, text in enumerate(insights_text):
    fontsize = 13 if i == 0 else 10
    fontweight = 'bold' if i == 0 else 'normal'
    color = '#ffffff' if i == 0 else '#ecf0f1'
    ax_insights.text(0.02, 0.85 - i*0.18, text, fontsize=fontsize, fontweight=fontweight, color=color, va='top', transform=ax_insights.transAxes)

# 底部备注
ax_footnote = fig.add_axes([0, 0, 1, 0.04])
ax_footnote.axis('off')
ax_footnote.text(0.5, 0.5, '数据来源：1688采购平台 | 统计周期：2024年9月-2025年5月 | 制作日期：2025-05-17', fontsize=8, ha='center', va='center', color='#95a5a6')

output_path = os.path.expanduser("~/.hermes/data_output/boss_report_dashboard.png")
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#f8f9fa')
plt.close()
print(f"老板汇报看板已保存: {output_path}")
```

---

## 常见问题

**中文字体显示方块**：matplotlib 需要配置中文字体
```python
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
```

**文件路径有空格**：用双引号包裹路径
```python
df = pd.read_csv("/Users/aimac/My Files/data.csv")
```
