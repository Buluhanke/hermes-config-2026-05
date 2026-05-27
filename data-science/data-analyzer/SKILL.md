---
name: data-analyzer
description: 数据分析与可视化 — 读取CSV/Excel文件，生成图表（折线图、柱状图、饼图、散点图、热力图等），支持matplotlib/plotly/seaborn。触发：数据分析、可视化、画图、生成图表。
triggers:
  - 数据分析
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
