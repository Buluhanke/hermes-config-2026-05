/**
 * 1688 Supplier Report PPTX generator using pptxgenjs.
 *
 * Usage: node render.js spec.json output.pptx
 *
 * spec.json fields:
 *   title           - Presentation title
 *   subtitle        - Subtitle
 *   date            - Date string
 *   supplier_name   - Supplier company name
 *   contact         - Contact person name
 *   phone           - Phone number
 *   email           - Email address
 *   company         - Your company name
 *   summary         - Business summary paragraph
 *   products        - Array of { name, category, moq, price_range, lead_time }
 *   quality         - Quality certifications / assurance measures
 *   payment_terms   - Payment terms offered
 */

const PptxgenJS = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const SPEC = JSON.parse(fs.readFileSync(process.argv[2], "utf-8"));
const OUTPUT = process.argv[3];

const pptx = new PptxgenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.title = SPEC.title || "供应商汇报";
pptx.author = SPEC.company || "采购部";

// Color palette - Professional Navy/Teal
const C = {
  primary: "1E3A5F",      // deep navy
  secondary: "2E7D9B",    // teal
  accent: "E8913A",        // amber accent
  light: "EDF4F7",        // light gray-blue
  white: "FFFFFF",
  text: "1A1A2E",          // dark text
  muted: "6B7280",         // muted gray
  success: "059669",       // green
  gridLine: "CBD5E1",
};

// Helper factories
const mkText = (text, opts = {}) => ({
  text,
  fontFace: "Microsoft YaHei",
  color: C.text,
  ...opts,
});

const mkTitle = (text) => mkText(text, {
  fontSize: 36, bold: true, color: C.white,
  fontFace: "Microsoft YaHei",
});

const mkSectionTitle = (text) => mkText(text, {
  fontSize: 20, bold: true, color: C.primary,
  fontFace: "Microsoft YaHei",
});

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
  slide.addText(SPEC.title || "1688供应商汇报", {
    x: 0.8, y: 2.2, w: 11, h: 1.2,
    fontSize: 44, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  // Subtitle
  slide.addText(SPEC.subtitle || SPEC.supplier_name || "供应商合作汇报", {
    x: 0.8, y: 3.5, w: 8, h: 0.6,
    fontSize: 22, color: C.light,
    fontFace: "Microsoft YaHei",
  });

  // Bottom info bar
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 5.8, w: "100%", h: 0.7,
    fill: { color: C.secondary },
  });

  const dateStr = SPEC.date || new Date().toLocaleDateString("zh-CN");
  slide.addText(`${SPEC.supplier_name || ""}  |  ${dateStr}`, {
    x: 0.8, y: 5.85, w: 10, h: 0.6,
    fontSize: 14, color: C.white,
    fontFace: "Microsoft YaHei",
  });
}

// ============================================================
// SLIDE 2: Summary / Overview
// ============================================================
function addSummarySlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.white };

  // Header bar
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.9,
    fill: { color: C.primary },
  });
  slide.addText("企业概况", {
    x: 0.6, y: 0.2, w: 6, h: 0.6,
    fontSize: 22, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  // Left: company info card
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.5, y: 1.2, w: 5.2, h: 3.2,
    fill: { color: C.light },
    line: { color: C.gridLine, width: 1 },
  });

  const supplierInfo = [
    { label: "企业名称", value: SPEC.supplier_name || "-" },
    { label: "联系人", value: SPEC.contact || "-" },
    { label: "联系电话", value: SPEC.phone || "-" },
    { label: "电子邮箱", value: SPEC.email || "-" },
    { label: "主营业务", value: SPEC.main_business || "-" },
    { label: "合作时间", value: SPEC.cooperation_years || "-" },
  ];

  let yPos = 1.4;
  for (const item of supplierInfo) {
    slide.addText(item.label, {
      x: 0.7, y: yPos, w: 1.6, h: 0.4,
      fontSize: 12, bold: true, color: C.muted,
      fontFace: "Microsoft YaHei",
    });
    slide.addText(item.value, {
      x: 2.4, y: yPos, w: 3, h: 0.4,
      fontSize: 13, color: C.text,
      fontFace: "Microsoft YaHei",
    });
    yPos += 0.45;
  }

  // Right: summary text
  slide.addText("企业简介", {
    x: 6.0, y: 1.2, w: 6, h: 0.4,
    fontSize: 14, bold: true, color: C.primary,
    fontFace: "Microsoft YaHei",
  });

  slide.addText(SPEC.summary || "暂无企业简介", {
    x: 6.0, y: 1.7, w: 6, h: 2.5,
    fontSize: 13, color: C.text,
    fontFace: "Microsoft YaHei",
    valign: "top",
  });

  // Page footer
  addFooter(slide);
}

// ============================================================
// SLIDE 3: Products / Main categories
// ============================================================
function addProductsSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.white };

  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.9,
    fill: { color: C.primary },
  });
  slide.addText("主营产品", {
    x: 0.6, y: 0.2, w: 6, h: 0.6,
    fontSize: 22, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  const products = SPEC.products || [];
  if (products.length === 0) {
    slide.addText("暂无产品数据，请提供 products 字段", {
      x: 0.5, y: 1.5, w: 12, h: 0.6,
      fontSize: 14, color: C.muted, align: "center",
      fontFace: "Microsoft YaHei",
    });
    return;
  }

  // Product cards - 2 columns
  const colW = 5.8;
  const cardH = 1.1;
  const startY = 1.2;

  products.forEach((prod, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * (colW + 0.4);
    const y = startY + row * (cardH + 0.2);

    // Card background
    slide.addShape(pptx.ShapeType.rect, {
      x, y, w: colW, h: cardH,
      fill: { color: i % 2 === 0 ? C.light : C.white },
      line: { color: C.gridLine, width: 0.5 },
    });

    // Product name
    slide.addText(prod.name || "产品", {
      x: x + 0.15, y: y + 0.1, w: colW - 0.3, h: 0.4,
      fontSize: 14, bold: true, color: C.primary,
      fontFace: "Microsoft YaHei",
    });

    // Details
    const details = [
      `类别: ${prod.category || "-"}`,
      `MOQ: ${prod.moq || "-"}`,
      `价格区间: ${prod.price_range || "-"}`,
      `交期: ${prod.lead_time || "-"}`,
    ].join("   |   ");

    slide.addText(details, {
      x: x + 0.15, y: y + 0.55, w: colW - 0.3, h: 0.45,
      fontSize: 11, color: C.muted,
      fontFace: "Microsoft YaHei",
    });
  });

  addFooter(slide);
}

// ============================================================
// SLIDE 4: Pricing & Terms
// ============================================================
function addPricingSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.white };

  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.9,
    fill: { color: C.primary },
  });
  slide.addText("价格与合作条款", {
    x: 0.6, y: 0.2, w: 8, h: 0.6,
    fontSize: 22, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  const terms = [
    { label: "付款方式", value: SPEC.payment_terms || "T/T 30%" },
    { label: "最小订货量", value: SPEC.moq_policy || "500件起订" },
    { label: "报价有效期", value: SPEC.price_validity || "30天" },
    { label: "交货方式", value: SPEC.delivery_terms || "FOB" },
    { label: "年供货能力", value: SPEC.annual_capacity || "-" },
    { label: "质检方式", value: SPEC.inspection || "出厂全检" },
  ];

  // 2-column grid
  terms.forEach((term, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 6.5;
    const y = 1.2 + row * 1.1;

    // Label pill
    slide.addShape(pptx.ShapeType.rect, {
      x, y, w: 1.8, h: 0.5,
      fill: { color: C.secondary },
    });
    slide.addText(term.label, {
      x, y, w: 1.8, h: 0.5,
      fontSize: 12, bold: true, color: C.white, align: "center", valign: "middle",
      fontFace: "Microsoft YaHei",
    });

    // Value
    slide.addText(term.value, {
      x: x + 2.0, y: y, w: 4, h: 0.5,
      fontSize: 14, color: C.text, valign: "middle",
      fontFace: "Microsoft YaHei",
    });
  });

  // Notes
  if (SPEC.pricing_notes) {
    slide.addText(SPEC.pricing_notes, {
      x: 0.5, y: 4.6, w: 12, h: 0.8,
      fontSize: 12, color: C.muted,
      fontFace: "Microsoft YaHei",
    });
  }

  addFooter(slide);
}

// ============================================================
// SLIDE 5: Quality Assurance
// ============================================================
function addQualitySlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.white };

  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.9,
    fill: { color: C.primary },
  });
  slide.addText("质量保障", {
    x: 0.6, y: 0.2, w: 6, h: 0.6,
    fontSize: 22, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  const certs = SPEC.certifications || ["ISO9001", "CE"];
  const assurances = SPEC.quality_measures || ["出厂全检", "来料检验", "过程控制"];

  // Certifications row
  slide.addText("资质认证", {
    x: 0.5, y: 1.2, w: 3, h: 0.4,
    fontSize: 13, bold: true, color: C.primary,
    fontFace: "Microsoft YaHei",
  });

  certs.forEach((cert, i) => {
    slide.addShape(pptx.ShapeType.rect, {
      x: 0.5 + i * 2.2, y: 1.7, w: 2, h: 0.55,
      fill: { color: C.success },
    });
    slide.addText(cert, {
      x: 0.5 + i * 2.2, y: 1.7, w: 2, h: 0.55,
      fontSize: 12, bold: true, color: C.white, align: "center", valign: "middle",
      fontFace: "Microsoft YaHei",
    });
  });

  // Quality measures
  slide.addText("质量管控措施", {
    x: 0.5, y: 2.5, w: 4, h: 0.4,
    fontSize: 13, bold: true, color: C.primary,
    fontFace: "Microsoft YaHei",
  });

  assurances.forEach((measure, i) => {
    slide.addText(`✓  ${measure}`, {
      x: 0.5, y: 3.0 + i * 0.5, w: 6, h: 0.45,
      fontSize: 13, color: C.text,
      fontFace: "Microsoft YaHei",
    });
  });

  addFooter(slide);
}

// ============================================================
// SLIDE 6: Contact
// ============================================================
function addContactSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.primary };

  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.15,
    fill: { color: C.accent },
  });

  slide.addText("联系方式", {
    x: 0.8, y: 1.5, w: 10, h: 0.8,
    fontSize: 36, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  const contactItems = [
    { label: "供应商", value: SPEC.supplier_name || "-" },
    { label: "联系人", value: SPEC.contact || "-" },
    { label: "电话", value: SPEC.phone || "-" },
    { label: "邮箱", value: SPEC.email || "-" },
  ];

  let yPos = 2.6;
  for (const item of contactItems) {
    slide.addText(item.label, {
      x: 0.8, y: yPos, w: 1.5, h: 0.5,
      fontSize: 16, bold: true, color: C.accent,
      fontFace: "Microsoft YaHei",
    });
    slide.addText(item.value, {
      x: 2.5, y: yPos, w: 8, h: 0.5,
      fontSize: 18, color: C.white,
      fontFace: "Microsoft YaHei",
    });
    yPos += 0.65;
  }

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
  slide.addText(`${SPEC.supplier_name || ""}  |  ${SPEC.date || ""}`, {
    x: 0.5, y: 6.0, w: 8, h: 0.3,
    fontSize: 9, color: C.muted,
    fontFace: "Microsoft YaHei",
  });
}

// ============================================================
// Build
// ============================================================
addCoverSlide();
addSummarySlide();
addProductsSlide();
addPricingSlide();
addQualitySlide();
addContactSlide();

pptx.writeFile({ fileName: OUTPUT })
  .then(() => console.log(`Created: ${OUTPUT}`))
  .catch(err => { console.error(err); process.exit(1); });
