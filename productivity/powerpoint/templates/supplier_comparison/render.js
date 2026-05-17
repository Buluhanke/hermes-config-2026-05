/**
 * Supplier Comparison PPTX generator using pptxgenjs.
 *
 * Usage: node render.js spec.json output.pptx
 *
 * spec.json fields:
 *   title           - Presentation title
 *   subtitle        - Subtitle
 *   date            - Date string
 *   company         - Your company name
 *   products        - Array of { name, spec }
 *   suppliers       - Array of supplier objects (required)
 *   recommendation  - Recommendation text
 */

const PptxgenJS = require("pptxgenjs");
const fs = require("fs");

const SPEC = JSON.parse(fs.readFileSync(process.argv[2], "utf-8"));
const OUTPUT = process.argv[3];

const pptx = new PptxgenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.title = SPEC.title || "供应商比价分析报告";
pptx.author = SPEC.company || "采购部";

const C = {
  primary: "1E3A5F",
  secondary: "2E7D9B",
  accent: "E8913A",
  light: "EDF4F7",
  white: "FFFFFF",
  text: "1A1A2E",
  muted: "6B7280",
  success: "059669",
  warning: "B91C1C",
  gridLine: "CBD5E1",
};

// ============================================================
// SLIDE 1: Cover
// ============================================================
function addCoverSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.primary };

  // Top accent bar
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.15,
    fill: { color: C.accent },
  });

  // Company name top right
  slide.addText(SPEC.company || "采购部", {
    x: 7.5, y: 0.4, w: 4, h: 0.4,
    fontSize: 12, color: C.light, align: "right",
    fontFace: "Microsoft YaHei",
  });

  // Main title
  slide.addText(SPEC.title || "供应商比价分析报告", {
    x: 0.8, y: 2.0, w: 11, h: 1.2,
    fontSize: 42, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  // Subtitle
  slide.addText(SPEC.subtitle || "供应商综合评估与比价", {
    x: 0.8, y: 3.3, w: 8, h: 0.6,
    fontSize: 20, color: C.light,
    fontFace: "Microsoft YaHei",
  });

  // Bottom info bar
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 5.8, w: "100%", h: 0.7,
    fill: { color: C.secondary },
  });

  const dateStr = SPEC.date || new Date().toLocaleDateString("zh-CN");
  slide.addText(`${SPEC.company || ""}  |  ${dateStr}`, {
    x: 0.8, y: 5.85, w: 10, h: 0.6,
    fontSize: 14, color: C.white,
    fontFace: "Microsoft YaHei",
  });
}

// ============================================================
// SLIDE 2: Overview
// ============================================================
function addOverviewSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.white };

  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.9,
    fill: { color: C.primary },
  });
  slide.addText("比价概览", {
    x: 0.6, y: 0.2, w: 6, h: 0.6,
    fontSize: 22, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  const suppliers = SPEC.suppliers || [];
  const products = SPEC.products || [];

  // Stats row
  const stats = [
    { label: "参与供应商", value: String(suppliers.length), unit: "家" },
    { label: "比价产品", value: String(products.length > 0 ? products.length : "—"), unit: "类" },
    { label: "评估维度", value: "5", unit: "项" },
  ];

  stats.forEach((stat, i) => {
    const x = 0.5 + i * 4.2;
    slide.addShape(pptx.ShapeType.rect, {
      x, y: 1.2, w: 3.8, h: 1.4,
      fill: { color: C.light },
      line: { color: C.gridLine, width: 0.5 },
    });
    slide.addText(stat.value, {
      x, y: 1.3, w: 3.8, h: 0.8,
      fontSize: 36, bold: true, color: C.primary, align: "center",
      fontFace: "Microsoft YaHei",
    });
    slide.addText(`${stat.label}  ${stat.unit}`, {
      x, y: 2.1, w: 3.8, h: 0.4,
      fontSize: 12, color: C.muted, align: "center",
      fontFace: "Microsoft YaHei",
    });
  });

  // Evaluation dimensions
  slide.addText("评估维度", {
    x: 0.5, y: 2.9, w: 4, h: 0.4,
    fontSize: 14, bold: true, color: C.primary,
    fontFace: "Microsoft YaHei",
  });

  const dimensions = ["价格竞争力", "最小订货量(MOQ)", "交期", "资质认证", "综合评分"];
  dimensions.forEach((dim, i) => {
    slide.addShape(pptx.ShapeType.rect, {
      x: 0.5 + i * 2.4, y: 3.4, w: 2.2, h: 0.5,
      fill: { color: C.secondary },
    });
    slide.addText(dim, {
      x: 0.5 + i * 2.4, y: 3.4, w: 2.2, h: 0.5,
      fontSize: 11, bold: true, color: C.white, align: "center", valign: "middle",
      fontFace: "Microsoft YaHei",
    });
  });

  // Products list
  if (products.length > 0) {
    slide.addText("比价产品", {
      x: 0.5, y: 4.2, w: 4, h: 0.4,
      fontSize: 14, bold: true, color: C.primary,
      fontFace: "Microsoft YaHei",
    });
    const productText = products.map(p => `${p.name}${p.spec ? " (" + p.spec + ")" : ""}`).join("、");
    slide.addText(productText || "—", {
      x: 0.5, y: 4.6, w: 11.5, h: 0.6,
      fontSize: 13, color: C.text,
      fontFace: "Microsoft YaHei",
    });
  }

  addFooter(slide);
}

// ============================================================
// SLIDE 3: Comparison Table
// ============================================================
function addComparisonSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.white };

  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.9,
    fill: { color: C.primary },
  });
  slide.addText("供应商对比表", {
    x: 0.6, y: 0.2, w: 8, h: 0.6,
    fontSize: 22, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  const suppliers = SPEC.suppliers || [];

  const tableData = [
    [
      { text: "供应商", options: { fill: { color: C.primary }, color: C.white, bold: true, align: "center" } },
      { text: "单价", options: { fill: { color: C.primary }, color: C.white, bold: true, align: "center" } },
      { text: "MOQ", options: { fill: { color: C.primary }, color: C.white, bold: true, align: "center" } },
      { text: "交期", options: { fill: { color: C.primary }, color: C.white, bold: true, align: "center" } },
      { text: "评分", options: { fill: { color: C.primary }, color: C.white, bold: true, align: "center" } },
      { text: "资质认证", options: { fill: { color: C.primary }, color: C.white, bold: true, align: "center" } },
      { text: "付款方式", options: { fill: { color: C.primary }, color: C.white, bold: true, align: "center" } },
      { text: "备注", options: { fill: { color: C.primary }, color: C.white, bold: true, align: "center" } },
    ],
  ];

  if (suppliers.length === 0) {
    tableData.push([
      { text: "（请提供 suppliers 数据）", options: { colspan: 8 } },
    ]);
  } else {
    suppliers.forEach((s, i) => {
      const bg = i % 2 === 0 ? C.light : C.white;
      tableData.push([
        { text: s.name || "—", options: { fill: { color: bg }, bold: true } },
        { text: s.price || "—", options: { fill: { color: bg }, align: "right" } },
        { text: s.moq || "—", options: { fill: { color: bg }, align: "center" } },
        { text: s.lead_time || "—", options: { fill: { color: bg }, align: "center" } },
        { text: s.rating || "—", options: { fill: { color: bg }, align: "center" } },
        { text: (s.certifications || []).join(", ") || "—", options: { fill: { color: bg } } },
        { text: s.payment_terms || "—", options: { fill: { color: bg } } },
        { text: s.notes || "—", options: { fill: { color: bg } } },
      ]);
    });
  }

  slide.addTable(tableData, {
    x: 0.3, y: 1.1, w: 12.6,
    colW: [2.2, 1.4, 1.2, 1.2, 1.0, 2.0, 1.6, 2.0],
    border: { pt: 0.5, color: C.gridLine },
    fontFace: "Microsoft YaHei",
    fontSize: 11,
    color: C.text,
  });

  addFooter(slide);
}

// ============================================================
// SLIDE 4: Ranking
// ============================================================
function addRankingSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.white };

  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.9,
    fill: { color: C.primary },
  });
  slide.addText("综合排名", {
    x: 0.6, y: 0.2, w: 6, h: 0.6,
    fontSize: 22, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  const suppliers = SPEC.suppliers || [];

  if (suppliers.length === 0) {
    slide.addText("暂无供应商数据", {
      x: 0.5, y: 1.5, w: 12, h: 0.6,
      fontSize: 14, color: C.muted, align: "center",
      fontFace: "Microsoft YaHei",
    });
    return;
  }

  // Sort by price (lower is better), simple ranking
  const sorted = [...suppliers].sort((a, b) => {
    const priceA = parseFloat((a.price || "999999").replace(/[^0-9.]/g, ""));
    const priceB = parseFloat((b.price || "999999").replace(/[^0-9.]/g, ""));
    return priceA - priceB;
  });

  const medals = ["🥇", "🥈", "🥉"];
  sorted.forEach((s, i) => {
    const y = 1.2 + i * 1.0;
    const bg = i === 0 ? "FEF3C7" : i === 1 ? "F3F4F6" : i === 2 ? "FEF3C7" : C.white;
    const accentColor = i === 0 ? C.accent : i === 1 ? C.muted : "CD7F32";

    // Rank badge
    slide.addShape(pptx.ShapeType.rect, {
      x: 0.5, y, w: 0.8, h: 0.8,
      fill: { color: accentColor },
    });
    slide.addText(medals[i] || `#${i + 1}`, {
      x: 0.5, y, w: 0.8, h: 0.8,
      fontSize: 20, align: "center", valign: "middle",
    });

    // Card
    slide.addShape(pptx.ShapeType.rect, {
      x: 1.4, y, w: 11.2, h: 0.8,
      fill: { color: bg },
      line: { color: C.gridLine, width: 0.5 },
    });

    // Name
    slide.addText(s.name || "—", {
      x: 1.6, y: y + 0.1, w: 3.5, h: 0.6,
      fontSize: 14, bold: true, color: C.text, valign: "middle",
      fontFace: "Microsoft YaHei",
    });

    // Key metrics
    const metrics = [
      `价格: ${s.price || "-"}`,
      `MOQ: ${s.moq || "-"}`,
      `交期: ${s.lead_time || "-"}`,
      `评分: ${s.rating || "-"}`,
    ];
    metrics.forEach((m, mi) => {
      slide.addText(m, {
        x: 5.2 + mi * 1.8, y: y + 0.1, w: 1.7, h: 0.6,
        fontSize: 11, color: C.text, valign: "middle",
        fontFace: "Microsoft YaHei",
      });
    });
  });

  addFooter(slide);
}

// ============================================================
// SLIDE 5: Recommendation
// ============================================================
function addRecommendationSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.primary };

  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.15,
    fill: { color: C.accent },
  });

  slide.addText("推荐结论", {
    x: 0.8, y: 1.0, w: 10, h: 0.8,
    fontSize: 36, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  // Recommendation text
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.5, y: 2.0, w: 12.2, h: 2.8,
    fill: { color: C.secondary, transparency: 30 },
    line: { color: C.accent, width: 2 },
  });

  slide.addText(SPEC.recommendation || "综合价格、质量、交期等因素，建议选择性价比最优的供应商。", {
    x: 0.8, y: 2.2, w: 11.6, h: 2.4,
    fontSize: 16, color: C.white, valign: "middle",
    fontFace: "Microsoft YaHei",
  });

  // Bottom bar
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 5.8, w: "100%", h: 0.7,
    fill: { color: C.secondary },
  });
  slide.addText(SPEC.company || "期待合作", {
    x: 0.8, y: 5.85, w: 10, h: 0.6,
    fontSize: 14, color: C.white,
    fontFace: "Microsoft YaHei",
  });
}

// ============================================================
// Footer helper
// ============================================================
function addFooter(slide) {
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 6.0, w: "100%", h: 0.3,
    fill: { color: C.light },
  });
  slide.addText(`${SPEC.title || ""}  |  ${SPEC.date || ""}`, {
    x: 0.5, y: 6.0, w: 12, h: 0.3,
    fontSize: 9, color: C.muted,
    fontFace: "Microsoft YaHei",
  });
}

// ============================================================
// Build
// ============================================================
addCoverSlide();
addOverviewSlide();
addComparisonSlide();
addRankingSlide();
addRecommendationSlide();

pptx.writeFile({ fileName: OUTPUT })
  .then(() => console.log(`Created: ${OUTPUT}`))
  .catch(err => { console.error(err); process.exit(1); });
