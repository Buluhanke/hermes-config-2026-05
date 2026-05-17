/**
 * Purchase Order Confirmation PPTX generator using pptxgenjs.
 *
 * Usage: node render.js spec.json output.pptx
 *
 * spec.json fields:
 *   title           - Document title
 *   order_no        - Purchase order number (required)
 *   date            - Order date
 *   buyer           - Buyer company name (required)
 *   seller          - Seller/supplier name (required)
 *   contact         - Buyer contact person
 *   phone           - Buyer phone
 *   items           - Array of line items (required)
 *   subtotal        - Subtotal amount
 *   tax_rate        - Tax rate (e.g. "13%")
 *   tax_amount      - Tax amount
 *   total_amount    - Grand total (required)
 *   currency        - Currency code (default "CNY")
 *   delivery_date   - Expected delivery date
 *   delivery_address- Delivery address
 *   payment_terms   - Payment terms
 *   sign_date       - Signature date
 *   notes           - Additional notes
 */

const PptxgenJS = require("pptxgenjs");
const fs = require("fs");

const SPEC = JSON.parse(fs.readFileSync(process.argv[2], "utf-8"));
const OUTPUT = process.argv[3];

const pptx = new PptxgenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.title = SPEC.title || "采购订单确认";

const C = {
  primary: "1E3A5F",
  secondary: "2E7D9B",
  accent: "E8913A",
  light: "EDF4F7",
  white: "FFFFFF",
  text: "1A1A2E",
  muted: "6B7280",
  gridLine: "CBD5E1",
  warning: "B91C1C",
  success: "059669",
};

// ============================================================
// SLIDE 1: Cover / Header
// ============================================================
function addCoverSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.primary };

  // Top accent
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.15,
    fill: { color: C.accent },
  });

  // Title block
  slide.addText(SPEC.title || "采购订单确认书", {
    x: 0.8, y: 1.8, w: 11, h: 1.0,
    fontSize: 40, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  // Order number highlight
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.8, y: 3.0, w: 5.5, h: 0.6,
    fill: { color: C.accent },
  });
  slide.addText(`订单号: ${SPEC.order_no || "XXXX"}`, {
    x: 0.8, y: 3.0, w: 5.5, h: 0.6,
    fontSize: 18, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
    valign: "middle",
  });

  // Parties info
  slide.addText(`甲方（采购方）: ${SPEC.buyer || ""}`, {
    x: 0.8, y: 4.0, w: 8, h: 0.4,
    fontSize: 14, color: C.light,
    fontFace: "Microsoft YaHei",
  });
  slide.addText(`乙方（供应商）: ${SPEC.seller || ""}`, {
    x: 0.8, y: 4.5, w: 8, h: 0.4,
    fontSize: 14, color: C.light,
    fontFace: "Microsoft YaHei",
  });
  slide.addText(`日期: ${SPEC.date || ""}`, {
    x: 0.8, y: 5.0, w: 8, h: 0.4,
    fontSize: 14, color: C.light,
    fontFace: "Microsoft YaHei",
  });

  // Bottom bar
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 5.8, w: "100%", h: 0.7,
    fill: { color: C.secondary },
  });
  slide.addText(`${SPEC.buyer || ""} 采购部`, {
    x: 0.8, y: 5.85, w: 10, h: 0.6,
    fontSize: 13, color: C.white,
    fontFace: "Microsoft YaHei",
  });
}

// ============================================================
// SLIDE 2: Order Information
// ============================================================
function addOrderInfoSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.white };

  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.9,
    fill: { color: C.primary },
  });
  slide.addText("订单信息", {
    x: 0.6, y: 0.2, w: 6, h: 0.6,
    fontSize: 22, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  // Info grid - 2 columns
  const fields = [
    ["订单编号", SPEC.order_no || "-"],
    ["订单日期", SPEC.date || "-"],
    ["采购方", SPEC.buyer || "-"],
    ["供应商", SPEC.seller || "-"],
    ["联系人", SPEC.contact || "-"],
    ["联系电话", SPEC.phone || "-"],
    ["交货日期", SPEC.delivery_date || "-"],
    ["交货地址", SPEC.delivery_address || "-"],
    ["付款方式", SPEC.payment_terms || "-"],
  ];

  fields.forEach(([label, value], i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 6.5;
    const y = 1.2 + row * 0.85;

    slide.addShape(pptx.ShapeType.rect, {
      x, y, w: 1.8, h: 0.55,
      fill: { color: C.secondary },
    });
    slide.addText(label, {
      x, y, w: 1.8, h: 0.55,
      fontSize: 12, bold: true, color: C.white,
      align: "center", valign: "middle",
      fontFace: "Microsoft YaHei",
    });
    slide.addText(value, {
      x: x + 1.9, y: y, w: 4.3, h: 0.55,
      fontSize: 13, color: C.text, valign: "middle",
      fontFace: "Microsoft YaHei",
    });
  });

  addFooter(slide);
}

// ============================================================
// SLIDE 3: Line Items Table
// ============================================================
function addItemsSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.white };

  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.9,
    fill: { color: C.primary },
  });
  slide.addText("采购明细", {
    x: 0.6, y: 0.2, w: 6, h: 0.6,
    fontSize: 22, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  const items = SPEC.items || [];

  // Table
  const tableData = [
    [
      { text: "序号", options: { fill: { color: C.primary }, color: C.white, bold: true, align: "center" } },
      { text: "产品名称", options: { fill: { color: C.primary }, color: C.white, bold: true, align: "center" } },
      { text: "SKU/规格", options: { fill: { color: C.primary }, color: C.white, bold: true, align: "center" } },
      { text: "数量", options: { fill: { color: C.primary }, color: C.white, bold: true, align: "center" } },
      { text: "单价", options: { fill: { color: C.primary }, color: C.white, bold: true, align: "center" } },
      { text: "小计", options: { fill: { color: C.primary }, color: C.white, bold: true, align: "center" } },
    ],
  ];

  if (items.length === 0) {
    tableData.push([
      { text: "1", options: { align: "center" } },
      { text: "（请提供 items 数据）", options: {} },
      { text: "-", options: {} },
      { text: "-", options: {} },
      { text: "-", options: {} },
      { text: "-", options: {} },
    ]);
  } else {
    items.forEach((item, i) => {
      const bg = i % 2 === 0 ? C.light : C.white;
      tableData.push([
        { text: String(i + 1), options: { fill: { color: bg }, align: "center" } },
        { text: item.name || "-", options: { fill: { color: bg } } },
        { text: item.sku || "-", options: { fill: { color: bg } } },
        { text: String(item.qty || "-"), options: { fill: { color: bg }, align: "center" } },
        { text: item.price || "-", options: { fill: { color: bg }, align: "right" } },
        { text: item.subtotal || "-", options: { fill: { color: bg }, align: "right" } },
      ]);
    });
  }

  slide.addTable(tableData, {
    x: 0.5, y: 1.1, w: 12.2,
    colW: [0.7, 3.5, 2.2, 1.2, 1.8, 1.8],
    border: { pt: 0.5, color: C.gridLine },
    fontFace: "Microsoft YaHei",
    fontSize: 12,
    color: C.text,
  });

  // Totals
  const yStart = 1.1 + Math.max(items.length, 3) * 0.55 + 0.3;

  const addTotalRow = (label, value, y, highlight = false) => {
    slide.addShape(pptx.ShapeType.rect, {
      x: 7.5, y, w: 2, h: 0.45,
      fill: { color: highlight ? C.primary : C.muted },
    });
    slide.addText(label, {
      x: 7.5, y, w: 2, h: 0.45,
      fontSize: 12, bold: true, color: C.white,
      align: "center", valign: "middle",
      fontFace: "Microsoft YaHei",
    });
    slide.addShape(pptx.ShapeType.rect, {
      x: 9.5, y, w: 3.2, h: 0.45,
      fill: { color: highlight ? C.primary : C.light },
    });
    slide.addText(value || "-", {
      x: 9.5, y, w: 3.2, h: 0.45,
      fontSize: 13, bold: highlight, color: highlight ? C.white : C.text,
      align: "right", valign: "middle",
      fontFace: "Microsoft YaHei",
    });
  };

  addTotalRow("小计", SPEC.subtotal || "-", yStart);
  addTotalRow("税率", SPEC.tax_rate || "13%", yStart + 0.5);
  addTotalRow("税额", SPEC.tax_amount || "-", yStart + 1.0);
  addTotalRow("合计", SPEC.total_amount || "-", yStart + 1.5, true);

  addFooter(slide);
}

// ============================================================
// SLIDE 4: Terms & Conditions
// ============================================================
function addTermsSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.white };

  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.9,
    fill: { color: C.primary },
  });
  slide.addText("条款与备注", {
    x: 0.6, y: 0.2, w: 8, h: 0.6,
    fontSize: 22, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  const terms = [
    "1. 供应商应按合同约定的时间和质量标准完成交付。",
    "2. 采购方在收到货物后3个工作日内完成验收，如有质量问题应在7日内书面提出。",
    "3. 如因供应商原因导致交货延期，采购方有权要求赔偿。",
    "4. 本订单传真件/扫描件与原件具有同等法律效力。",
    "5. 争议解决：双方友好协商，协商不成提交甲方所在地人民法院管辖。",
  ];

  if (SPEC.notes) {
    terms.push(`备注: ${SPEC.notes}`);
  }

  terms.forEach((term, i) => {
    slide.addText(term, {
      x: 0.6, y: 1.2 + i * 0.6, w: 11.5, h: 0.55,
      fontSize: 13, color: C.text,
      fontFace: "Microsoft YaHei",
    });
  });

  addFooter(slide);
}

// ============================================================
// SLIDE 5: Signature Block
// ============================================================
function addSignSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.white };

  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.9,
    fill: { color: C.primary },
  });
  slide.addText("签章确认", {
    x: 0.6, y: 0.2, w: 6, h: 0.6,
    fontSize: 22, bold: true, color: C.white,
    fontFace: "Microsoft YaHei",
  });

  // Two signature boxes
  const boxes = [
    { title: "甲方（采购方）", name: SPEC.buyer || "", contact: SPEC.contact || "", signDate: SPEC.sign_date || "" },
    { title: "乙方（供应商）", name: SPEC.seller || "", contact: "", signDate: "" },
  ];

  boxes.forEach((box, i) => {
    const x = 0.5 + i * 7.0;

    slide.addShape(pptx.ShapeType.rect, {
      x, y: 1.2, w: 6.2, h: 3.8,
      fill: { color: C.light },
      line: { color: C.gridLine, width: 1 },
    });

    slide.addText(box.title, {
      x: x + 0.2, y: 1.4, w: 5.8, h: 0.5,
      fontSize: 16, bold: true, color: C.primary,
      fontFace: "Microsoft YaHei",
    });

    const sigFields = [
      ["公司名称", box.name],
      ["授权代表", box.contact],
      ["签章日期", box.signDate || SPEC.date || ""],
      ["（签章）", ""],
    ];

    sigFields.forEach(([label, value], j) => {
      slide.addText(label, {
        x: x + 0.3, y: 2.1 + j * 0.65, w: 1.5, h: 0.5,
        fontSize: 12, color: C.muted,
        fontFace: "Microsoft YaHei",
      });
      slide.addText(value, {
        x: x + 1.9, y: 2.1 + j * 0.65, w: 4, h: 0.5,
        fontSize: 13, color: C.text,
        fontFace: "Microsoft YaHei",
      });
      // Underline for signature line
      if (label === "（签章）") {
        slide.addShape(pptx.ShapeType.rect, {
          x: x + 1.9, y: 2.1 + j * 0.65 + 0.4, w: 4, h: 0.02,
          fill: { color: C.text },
        });
      }
    });
  });

  addFooter(slide);
}

function addFooter(slide) {
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 6.0, w: "100%", h: 0.3,
    fill: { color: C.light },
  });
  slide.addText(`${SPEC.order_no || ""}  |  ${SPEC.buyer || ""}  |  ${SPEC.date || ""}`, {
    x: 0.5, y: 6.0, w: 12, h: 0.3,
    fontSize: 9, color: C.muted,
    fontFace: "Microsoft YaHei",
  });
}

// ============================================================
// Build
// ============================================================
addCoverSlide();
addOrderInfoSlide();
addItemsSlide();
addTermsSlide();
addSignSlide();

pptx.writeFile({ fileName: OUTPUT })
  .then(() => console.log(`Created: ${OUTPUT}`))
  .catch(err => { console.error(err); process.exit(1); });
