#!/usr/bin/env python3
"""
1688 Procurement Infographic Generator

Generate infographics from 1688 procurement data CSV files.
Supports: supplier comparison, price trend, category breakdown, KPI dashboard.

Usage:
    python generate_1688_infographic.py --type dashboard --input data.csv --output ./output
    python generate_1688_infographic.py --type supplier-compare --input suppliers.csv --output ./output
    python generate_1688_infographic.py --type price-trend --input prices.csv --output ./output
    python generate_1688_infographic.py --type full-report --input data.csv --output ./output
"""

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class SupplierData:
    name: str
    overall_score: float
    price_score: float
    quality_score: float
    lead_time_score: float
    service_score: float
    monthly_orders: int
    cooperation_months: int


@dataclass
class PricePoint:
    date: str
    sku: str
    price: float
    category: str = ""


@dataclass
class CategoryData:
    name: str
    spend: float
    order_count: int
    period: str


@dataclass
class KpiData:
    total_spend: float
    order_count: int
    supplier_count: int
    avg_lead_time: str
    completion_rate: float


class ProcurementDataParser:
    """Parse 1688 procurement data from CSV files."""

    @staticmethod
    def parse_suppliers(filepath: str) -> List[SupplierData]:
        """Parse supplier comparison data from CSV."""
        suppliers = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                suppliers.append(SupplierData(
                    name=row.get('supplier_name', row.get('name', '')),
                    overall_score=float(row.get('overall_score', row.get('score', 0))),
                    price_score=float(row.get('price_score', 0)),
                    quality_score=float(row.get('quality_score', 0)),
                    lead_time_score=float(row.get('lead_time_score', row.get('delivery_score', 0))),
                    service_score=float(row.get('service_score', 0)),
                    monthly_orders=int(row.get('monthly_orders', row.get('orders', 0))),
                    cooperation_months=int(row.get('cooperation_months', row.get('months', 0)))
                ))
        return suppliers

    @staticmethod
    def parse_prices(filepath: str) -> List[PricePoint]:
        """Parse price history data from CSV."""
        prices = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                prices.append(PricePoint(
                    date=row.get('date', row.get('日期', '')),
                    sku=row.get('sku', row.get('product_name', row.get('产品', ''))),
                    price=float(row.get('price', row.get('价格', 0))),
                    category=row.get('category', row.get('品类', ''))
                ))
        return prices

    @staticmethod
    def parse_categories(filepath: str) -> List[CategoryData]:
        """Parse category breakdown data from CSV."""
        categories = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                categories.append(CategoryData(
                    name=row.get('category_name', row.get('name', row.get('品类', ''))),
                    spend=float(row.get('spend', row.get('采购额', 0))),
                    order_count=int(row.get('order_count', row.get('orders', 0))),
                    period=row.get('period', row.get('周期', 'Monthly'))
                ))
        return categories

    @staticmethod
    def parse_kpis(filepath: str) -> KpiData:
        """Parse KPI summary data from CSV."""
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            return KpiData(
                total_spend=float(row.get('total_spend', row.get('总支出', 0))),
                order_count=int(row.get('order_count', row.get('订单数', 0))),
                supplier_count=int(row.get('supplier_count', row.get('供应商数', 0))),
                avg_lead_time=row.get('avg_lead_time', row.get('平均交期', '7-15天')),
                completion_rate=float(row.get('completion_rate', row.get('完成率', 0)))
            )


class StructuredContentGenerator:
    """Generate structured content markdown from parsed data."""

    def __init__(self, output_lang: str = "zh"):
        self.lang = output_lang
        self.is_en = output_lang != "zh"

    def generate_supplier_comparison(self, suppliers: List[SupplierData]) -> str:
        """Generate structured content for supplier comparison."""
        title = "Supplier Comparison" if self.is_en else "供应商对比"
        headline = "1688 Supplier Evaluation Matrix" if self.is_en else "1688供应商评价矩阵"

        lines = [
            f"# {title}",
            "",
            "## Overview",
            f"{headline}" if self.is_en else f"{headline}",
            "",
            "## Learning Objectives",
            "The viewer will understand:",
            "1. Overall supplier performance rankings",
            "2. Strengths and weaknesses per supplier",
            "3. Recommendation for supplier selection",
            "",
            "---",
            "",
            "## Section 1: Overall Rankings",
            "",
            "**Key Concept**: Suppliers ranked by overall performance score",
            "",
            "**Content**:",
        ]

        for i, s in enumerate(sorted(suppliers, key=lambda x: x.overall_score, reverse=True), 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            lines.append(f"- {medal} **{s.name}**: {s.overall_score}/5.0 ({s.monthly_orders} orders/mo)")

        lines.extend([
            "",
            "**Visual Element**:",
            "- Type: ranked list with medal indicators",
            "- Subject: supplier performance hierarchy",
            "- Treatment: color gradient from gold to bronze",
            "",
            "**Text Labels**:",
            f"- Headline: \"{title}\"",
            "- Labels: supplier names, scores, order volumes",
            "",
            "---",
            "",
            "## Section 2: Score Breakdown by Criteria",
            "",
            "**Key Concept**: Detailed scores across price, quality, lead time, and service",
            "",
            "**Content**:",
            "",
            "| Supplier | Price | Quality | Lead Time | Service | Overall |",
            "|-----------|-------|---------|-----------|---------|---------|",
        ])

        for s in sorted(suppliers, key=lambda x: x.overall_score, reverse=True):
            lines.append(f"| {s.name} | {s.price_score}/5 | {s.quality_score}/5 | {s.lead_time_score}/5 | {s.service_score}/5 | **{s.overall_score}/5** |")

        lines.extend([
            "",
            "**Visual Element**:",
            "- Type: grouped bar chart or radar chart",
            "- Subject: multi-dimensional supplier comparison",
            "- Treatment: side-by-side bars per criteria, color-coded",
            "",
            "**Text Labels**:",
            f"- Headline: \"Score Breakdown\" if self.is_en else \"评分明细\"",
            "- Labels: criteria names, score values",
            "",
            "---",
            "",
            "## Data Points (Verbatim)",
            "",
            "### Supplier Scores",
        ])

        for s in suppliers:
            lines.append(f'- "{s.name}": Overall {s.overall_score}/5, Price {s.price_score}/5, Quality {s.quality_score}/5')

        return "\n".join(lines)

    def generate_price_trend(self, prices: List[PricePoint]) -> str:
        """Generate structured content for price trend."""
        title = "Price Trend Analysis" if self.is_en else "价格趋势分析"

        # Group by SKU
        sku_groups: Dict[str, List[PricePoint]] = {}
        for p in prices:
            if p.sku not in sku_groups:
                sku_groups[p.sku] = []
            sku_groups[p.sku].append(p)

        lines = [
            f"# {title}",
            "",
            "## Overview",
            "Historical pricing data and trend analysis for key SKUs" if self.is_en else "关键SKU的历史价格数据与趋势分析",
            "",
            "## Learning Objectives",
            "The viewer will understand:",
            "1. Price variation patterns over time",
            "2. Best timing for procurement decisions",
            "3. Price volatility per product category",
            "",
            "---",
        ]

        for sku, points in sku_groups.items():
            sorted_points = sorted(points, key=lambda x: x.date)
            min_price = min(p.price for p in sorted_points)
            max_price = max(p.price for p in sorted_points)
            avg_price = sum(p.price for p in sorted_points) / len(sorted_points)
            current_price = sorted_points[-1].price
            trend = "up" if current_price > avg_price else "down" if current_price < avg_price else "stable"
            trend_symbol = "📈" if trend == "up" else "📉" if trend == "down" else "➡️"

            lines.extend([
                "",
                f"## Section: {sku}",
                "",
                f"**Key Concept**: Price history and trend for {sku}",
                "",
                "**Content**:",
                f"- Date range: {sorted_points[0].date} to {sorted_points[-1].date}",
                f"- Min price: ¥{min_price:.2f}",
                f"- Max price: ¥{max_price:.2f}",
                f"- Avg price: ¥{avg_price:.2f}",
                f"- Current price: ¥{current_price:.2f} {trend_symbol}",
                f"- Data points: {len(sorted_points)}",
                "",
                "**Visual Element**:",
                "- Type: line chart with area fill",
                "- Subject: price over time",
                "- Treatment: smooth curve, shaded area, current price marker",
                "",
                "**Text Labels**:",
                f"- Headline: \"{sku}\"",
                f"- Y-axis: \"Price (¥)\" if self.is_en else \"价格 (¥)\"",
                f"- X-axis: \"Date\" if self.is_en else \"日期\"",
                f"- Stats: Min ¥{min_price:.0f}, Max ¥{max_price:.0f}, Avg ¥{avg_price:.0f}",
            ])

        lines.extend([
            "",
            "---",
            "",
            "## Data Points (Verbatim)",
            "",
            "### Price Statistics",
        ])

        for sku, points in sku_groups.items():
            sorted_points = sorted(points, key=lambda x: x.date)
            prices_only = [p.price for p in sorted_points]
            lines.append(f'- "{sku}": {len(points)} data points, range ¥{min(prices_only):.2f}-¥{max(prices_only):.2f}')

        return "\n".join(lines)

    def generate_category_breakdown(self, categories: List[CategoryData]) -> str:
        """Generate structured content for category breakdown."""
        title = "Category Breakdown" if self.is_en else "品类采购分布"
        total_spend = sum(c.spend for c in categories)

        lines = [
            f"# {title}",
            "",
            "## Overview",
            f"Spend distribution across {len(categories)} product categories" if self.is_en else f"共{len(categories)}个产品品类的采购额分布",
            "",
            "## Learning Objectives",
            "The viewer will understand:",
            "1. Which categories account for largest spend",
            "2. Order volume per category",
            "3. Category concentration risk",
            "",
            "---",
            "",
            "## Section 1: Spend Distribution",
            "",
            "**Key Concept**: Categories ranked by procurement spend",
            "",
            "**Content**:",
        ]

        sorted_cats = sorted(categories, key=lambda x: x.spend, reverse=True)
        for c in sorted_cats:
            pct = (c.spend / total_spend) * 100 if total_spend > 0 else 0
            lines.append(f"- **{c.name}**: ¥{c.spend:,.0f} ({pct:.1f}%) - {c.order_count} orders")

        lines.extend([
            "",
            "**Visual Element**:",
            "- Type: horizontal bar chart or treemap",
            "- Subject: proportional spend by category",
            "- Treatment: sorted by value, percentage labels",
            "",
            "**Text Labels**:",
            f"- Headline: \"{title}\"",
            f"- Subhead: \"Total: ¥{total_spend:,.0f}\" if self.is_en else f\"总计: ¥{total_spend:,.0f}\"",
            "- Labels: category names, values, percentages",
            "",
            "---",
            "",
            "## Data Points (Verbatim)",
            "",
            "### Category Spend",
        ])

        for c in sorted_cats:
            pct = (c.spend / total_spend) * 100 if total_spend > 0 else 0
            lines.append(f'- "{c.name}": ¥{c.spend:,.0f}, {pct:.1f}%, {c.order_count} orders')

        return "\n".join(lines)

    def generate_kpi_dashboard(self, kpis: KpiData) -> str:
        """Generate structured content for KPI dashboard."""
        title = "Procurement KPIs" if self.is_en else "采购KPI概览"

        lines = [
            f"# {title}",
            "",
            "## Overview",
            "Key performance indicators for procurement operations" if self.is_en else "采购运营关键绩效指标",
            "",
            "## Learning Objectives",
            "The viewer will understand:",
            "1. Overall procurement performance metrics",
            "2. Spend and order volume trends",
            "3. Supplier and delivery performance",
            "",
            "---",
            "",
            "## Section 1: Key Metrics",
            "",
            "**Key Concept**: Summary of core procurement KPIs",
            "",
            "**Content**:",
            f"- Total Spend: ¥{kpis.total_spend:,.0f}",
            f"- Order Count: {kpis.order_count:,} orders",
            f"- Active Suppliers: {kpis.supplier_count} suppliers",
            f"- Avg Lead Time: {kpis.avg_lead_time}",
            f"- Completion Rate: {kpis.completion_rate:.1f}%",
            "",
            "**Visual Element**:",
            "- Type: KPI cards with trend indicators",
            "- Subject: 5 key metrics",
            "- Treatment: big numbers, trend arrows, color-coded status",
            "",
            "**Text Labels**:",
            f"- Headline: \"{title}\"",
            f"- Labels: \"Total Spend\" / \"总支出\", \"Orders\" / \"订单数\", \"Suppliers\" / \"供应商数\", \"Lead Time\" / \"交期\", \"Completion\" / \"完成率\"",
            "",
            "---",
            "",
            "## Data Points (Verbatim)",
            "",
            "### KPI Summary",
            f'- "Total Spend": ¥{kpis.total_spend:,.0f}',
            f'- "Order Count": {kpis.order_count:,}',
            f'- "Supplier Count": {kpis.supplier_count}',
            f'- "Avg Lead Time": {kpis.avg_lead_time}',
            f'- "Completion Rate": {kpis.completion_rate:.1f}%',
        ]

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate 1688 procurement infographics")
    parser.add_argument("--type", "-t", required=True,
                        choices=["supplier-compare", "price-trend", "category", "kpi", "full-report"],
                        help="Type of infographic to generate")
    parser.add_argument("--input", "-i", required=True,
                        help="Input CSV file path")
    parser.add_argument("--output", "-o", default="./output",
                        help="Output directory for structured content")
    parser.add_argument("--lang", "-l", default="zh",
                        choices=["zh", "en"],
                        help="Output language (zh/en)")
    parser.add_argument("--format", "-f", default="markdown",
                        choices=["markdown", "json"],
                        help="Output format")

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    generator = StructuredContentGenerator(output_lang=args.lang)

    content = ""
    output_file = None

    if args.type == "supplier-compare":
        suppliers = ProcurementDataParser.parse_suppliers(args.input)
        content = generator.generate_supplier_comparison(suppliers)
        output_file = output_dir / f"supplier-comparison-{timestamp}.md"

    elif args.type == "price-trend":
        prices = ProcurementDataParser.parse_prices(args.input)
        content = generator.generate_price_trend(prices)
        output_file = output_dir / f"price-trend-{timestamp}.md"

    elif args.type == "category":
        categories = ProcurementDataParser.parse_categories(args.input)
        content = generator.generate_category_breakdown(categories)
        output_file = output_dir / f"category-breakdown-{timestamp}.md"

    elif args.type == "kpi":
        kpis = ProcurementDataParser.parse_kpis(args.input)
        content = generator.generate_kpi_dashboard(kpis)
        output_file = output_dir / f"kpi-dashboard-{timestamp}.md"

    elif args.type == "full-report":
        # Generate all sections
        sections = []
        try:
            suppliers = ProcurementDataParser.parse_suppliers(args.input)
            sections.append(generator.generate_supplier_comparison(suppliers))
        except Exception as e:
            print(f"Warning: Could not parse suppliers: {e}")

        try:
            prices = ProcurementDataParser.parse_prices(args.input)
            sections.append(generator.generate_price_trend(prices))
        except Exception as e:
            print(f"Warning: Could not parse prices: {e}")

        try:
            categories = ProcurementDataParser.parse_categories(args.input)
            sections.append(generator.generate_category_breakdown(categories))
        except Exception as e:
            print(f"Warning: Could not parse categories: {e}")

        try:
            kpis = ProcurementDataParser.parse_kpis(args.input)
            sections.append(generator.generate_kpi_dashboard(kpis))
        except Exception as e:
            print(f"Warning: Could not parse KPIs: {e}")

        content = "\n\n---\n\n".join(sections)
        output_file = output_dir / f"full-procurement-report-{timestamp}.md"

    # Write output
    if output_file is None:
        print("Error: No content generated")
        sys.exit(1)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Generated: {output_file}")
    print(f"Content type: {args.type}")
    print(f"Language: {args.lang}")
    print(f"\nNext steps:")
    print(f"1. Review the generated structured content")
    print(f"2. Use it as input for the baoyu-infographic skill")
    print(f"3. Select layout (dashboard/supplier-comparison/price-trend) and style")


if __name__ == "__main__":
    main()
