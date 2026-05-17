# Excel/CSV 自动化处理

## 核心依赖

```bash
pip install pandas openpyxl xlsxwriter
```

---

## 1. pandas 读取/写入 CSV 和 Excel

### 读取

```python
import pandas as pd

# CSV
df = pd.read_csv("data.csv", encoding="utf-8-sig")

# Excel（单sheet）
df = pd.read_excel("data.xlsx", sheet_name="Sheet1")

# Excel（多sheet，返回dict）
sheets = pd.read_excel("data.xlsx", sheet_name=None)
```

### 写入

```python
# CSV
df.to_csv("output.csv", index=False, encoding="utf-8-sig")

# Excel（openpyxl引擎）
df.to_excel("output.xlsx", sheet_name="Sheet1", index=False, engine="openpyxl")

# 写入已存在的Excel（追加sheet）
with pd.ExcelWriter("output.xlsx", mode="a", engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="NewSheet", index=False)
```

---

## 2. 数据清洗

### 去重

```python
# 按指定列去重
df = df.drop_duplicates(subset=["供应商", "日期"])

# 保留最后一条
df = df.drop_duplicates(subset=["编码"], keep="last")
```

### 填充空值

```python
# 数值列用0填充
df["数量"] = df["数量"].fillna(0)

# 文本列用"未知"填充
df["备注"] = df["备注"].fillna("未知")

# 用前一行值填充（向前填充）
df["价格"] = df["价格"].ffill()

# 用列均值填充
df["评分"] = df["评分"].fillna(df["评分"].mean())
```

### 类型转换

```python
# 日期字符串转datetime
df["日期"] = pd.to_datetime(df["日期"])

# 数值字符串转float
df["价格"] = pd.to_numeric(df["价格"], errors="coerce")

# 类别转换
df["等级"] = df["等级"].astype("category")
```

---

## 3. 条件筛选和汇总

### 条件筛选

```python
# 单条件
result = df[df["价格"] > 100]

# 多条件
result = df[(df["价格"] > 100) & (df["供应商"] == "A公司")]

# 模糊筛选
result = df[df["名称"].str.contains("北京", na=False)]
```

### 分组汇总（groupby）

```python
# 按供应商统计
summary = df.groupby("供应商").agg(
    总量=("数量", "sum"),
    平均价=("价格", "mean"),
    记录数=("日期", "count")
).reset_index()
```

### 透视表（pivot）

```python
pivot = pd.pivot_table(
    df,
    index="供应商",
    columns="月份",
    values="价格",
    aggfunc="mean",
    fill_value="-"
)
```

---

## 4. 格式化输出

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active

# 写入数据
ws.append(["供应商", "价格", "评分"])
for _, row in df.iterrows():
    ws.append(row.tolist())

# 表头样式
header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
header_font = Font(bold=True, color="FFFFFF")

for col in range(1, ws.max_column + 1):
    cell = ws.cell(row=1, column=col)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center")

# 数据行样式（隔行变色）
for row in range(2, ws.max_row + 1):
    if row % 2 == 0:
        for col in range(1, ws.max_column + 1):
            ws.cell(row=row, column=col).fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")

# 自动列宽
for col in range(1, ws.max_column + 1):
    max_len = max(len(str(ws.cell(row=r, column=col).value or "") for r in range(1, ws.max_row + 1)))
    ws.column_dimensions[get_column_letter(col)].width = max_len + 4

# 边框
thin = Side(style="thin", color="000000")
for row in range(1, ws.max_row + 1):
    for col in range(1, ws.max_column + 1):
        ws.cell(row=row, column=col).border = Border(left=thin, right=thin, top=thin, bottom=thin)

wb.save("formatted.xlsx")
```

---

## 5. 自动化报表生成脚本

```python
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from datetime import datetime

def generate_report(input_file: str, output_file: str):
    # 读取数据
    df = pd.read_excel(input_file)

    # 清洗数据
    df = df.drop_duplicates()
    df["日期"] = pd.to_datetime(df["日期"])
    df["价格"] = pd.to_numeric(df["价格"], errors="coerce").fillna(0)

    # 生成汇总
    summary = df.groupby("供应商").agg(
        总量=("数量", "sum"),
        平均价=("价格", "mean"),
        最高价=("价格", "max"),
        最低价=("价格", "min")
    ).round(2).reset_index()

    # 写入Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "汇总"

    # 写入汇总表
    headers = list(summary.columns)
    ws.append(headers)

    for _, row in summary.iterrows():
        ws.append(row.tolist())

    # 格式化表头
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center")

    # 自动列宽
    for col in range(1, len(headers) + 1):
        max_len = max(len(str(summary.iloc[r, col-1] or "") for r in range(len(summary))))
        ws.column_dimensions[get_column_letter(col)].width = max_len + 4

    # 写入明细sheet
    ws2 = wb.create_sheet("明细")
    ws2.append(["日期", "供应商", "数量", "价格"])

    df_sorted = df.sort_values("日期")
    for _, row in df_sorted.iterrows():
        ws2.append([row["日期"].strftime("%Y-%m-%d"), row["供应商"], row["数量"], row["价格"]])

    wb.save(output_file)
    print(f"报表已生成: {output_file}")

if __name__ == "__main__":
    generate_report("raw_data.xlsx", f"report_{datetime.now().strftime('%Y%m%d')}.xlsx")
```

---

## 6. 与看板数据联动

### 供应商评估表

```python
def supplier_evaluation(supply_df: pd.DataFrame, score_df: pd.DataFrame):
    """
    合并供应数据和评分数据，生成供应商评估表
    """
    # 按供应商汇总供应数据
    supply_summary = supply_df.groupby("供应商").agg(
        供货总量=("数量", "sum"),
        平均交期=("交期", "mean")
    ).reset_index()

    # 合并评分
    result = supply_summary.merge(score_df, on="供应商", how="left")

    # 计算综合评分
    result["综合评分"] = (
        result["质量评分"] * 0.4 +
        result["交付评分"] * 0.3 +
        result["价格评分"] * 0.3
    ).round(2)

    # 排序
    result = result.sort_values("综合评分", ascending=False)

    return result

# 使用示例
supply_data = pd.read_excel("供货记录.xlsx")
score_data = pd.read_excel("评分数据.xlsx")
evaluation = supplier_evaluation(supply_data, score_data)
evaluation.to_excel("供应商评估.xlsx", index=False)
```

### 价格追踪表

```python
def price_tracking(price_history: pd.DataFrame):
    """
    追踪历史价格变化，生成价格追踪报表
    """
    # 按月汇总
    price_history["月份"] = price_history["日期"].dt.to_period("M")
    monthly = price_history.groupby(["供应商", "月份"])["价格"].mean().reset_index()

    # 透视表
    pivot = monthly.pivot(index="供应商", columns="月份", values="价格")

    # 计算月环比变化
    for col in range(1, len(pivot.columns)):
        current = pivot.iloc[:, col]
        previous = pivot.iloc[:, col - 1]
        pivot[f"{pivot.columns[col]}_环比"] = ((current - previous) / previous * 100).round(2)

    return pivot

# 使用示例
history = pd.read_excel("价格历史.xlsx")
tracking = price_tracking(history)
tracking.to_excel("价格追踪.xlsx")
```

### 自动刷新看板数据

```python
from datetime import datetime
import schedule
import time

def refresh_kanban():
    """定时刷新看板数据并输出报表"""
    # 读取最新数据
    df = pd.read_excel("看板数据源.xlsx")

    # 处理
    result = process_kanban_data(df)

    # 输出（带时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result.to_excel(f"看板报表_{timestamp}.xlsx", index=False)

# 每天9点执行
schedule.every().day.at("09:00").do(refresh_kanban)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 常用工具函数

```python
def read_excel_safe(path: str, **kwargs) -> pd.DataFrame:
    """安全读取Excel，处理常见错误"""
    try:
        return pd.read_excel(path, **kwargs)
    except Exception as e:
        print(f"读取失败: {e}")
        return pd.DataFrame()

def write_excel_safe(df: pd.DataFrame, path: str, **kwargs) -> bool:
    """安全写入Excel"""
    try:
        df.to_excel(path, index=False, engine="openpyxl", **kwargs)
        return True
    except Exception as e:
        print(f"写入失败: {e}")
        return False

def apply_style(ws, header_row=1):
    """快速应用标准表头样式"""
    from openpyxl.styles import Font, PatternFill, Alignment
    for cell in ws[header_row]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
```

---

## 快捷命令

```bash
# 快速运行报表脚本
python generate_report.py

# 批量转换CSV为Excel
python -c "
import pandas as pd
import glob
for f in glob.glob('*.csv'):
    df = pd.read_csv(f)
    df.to_excel(f.replace('.csv', '.xlsx'), index=False)
    print(f'已转换: {f}')
"
```