const pptxgen = require("pptxgenjs");
const pres = new pptxgen();

pres.layout = "LAYOUT_16x9";
pres.author = "作者";
pres.title = "基于数据感知的多智能体专利分析系统设计与实现";

// ============================================================
// COLOR PALETTE - Midnight Executive + Teal accent
// ============================================================
const C = {
  navy:      "1A2332",   // primary dark
  darkBlue:  "1E3A5F",   // secondary dark
  steel:     "2D6A9F",   // mid blue
  teal:      "0891B2",   // accent
  cyan:      "06B6D4",   // bright accent
  lightBg:   "F0F5FA",   // slide light bg
  cardBg:    "FFFFFF",   // card white
  text:      "1E293B",   // dark text
  subtext:   "64748B",   // muted text
  lightText: "94A3B8",   // very muted
  white:     "FFFFFF",
  gold:      "F59E0B",   // highlight accent
  green:     "10B981",   // success
  red:       "EF4444",   // warning
  orange:    "F97316",   // warm accent
  purple:    "8B5CF6",   // purple accent
  gradTop:   "0F172A",   // gradient dark
  gradBot:   "1E3A5F",   // gradient mid
  stripe:    "E2E8F0",   // table stripe
};

// ============================================================
// HELPER FUNCTIONS
// ============================================================
const makeShadow = () => ({ type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.12 });

function addFooter(slide, pageNum, totalPages) {
  slide.addText(`${pageNum} / ${totalPages}`, {
    x: 8.8, y: 5.2, w: 1, h: 0.35,
    fontSize: 9, color: C.lightText, align: "right",
    fontFace: "Calibri",
  });
}

function addSectionDivider(slide, sectionNum, sectionTitle) {
  // Decorative left bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.12, h: 5.625,
    fill: { color: C.teal },
  });
  // Section number circle
  slide.addShape(pres.shapes.OVAL, {
    x: 0.6, y: 1.8, w: 1.0, h: 1.0,
    fill: { color: C.teal },
  });
  slide.addText(sectionNum, {
    x: 0.6, y: 1.8, w: 1.0, h: 1.0,
    fontSize: 36, fontFace: "Georgia", bold: true,
    color: C.white, align: "center", valign: "middle",
  });
  // Title
  slide.addText(sectionTitle, {
    x: 2.0, y: 1.8, w: 7.0, h: 1.0,
    fontSize: 32, fontFace: "Georgia", bold: true,
    color: C.navy, valign: "middle", margin: 0,
  });
  // Bottom line
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 2.0, y: 2.9, w: 3.0, h: 0.04,
    fill: { color: C.teal },
  });
}

function addSlideTitle(slide, title) {
  slide.addText(title, {
    x: 0.5, y: 0.2, w: 9.0, h: 0.55,
    fontSize: 22, fontFace: "Georgia", bold: true,
    color: C.navy, margin: 0,
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 0.78, w: 1.2, h: 0.035,
    fill: { color: C.teal },
  });
}

function addCard(slide, x, y, w, h, options = {}) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: options.fill || C.cardBg },
    shadow: makeShadow(),
    line: options.borderColor ? { color: options.borderColor, width: 1.5 } : undefined,
  });
  if (options.accentColor) {
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.06, h,
      fill: { color: options.accentColor },
    });
  }
}

const TOTAL_PAGES = 18;

// ============================================================
// SLIDE 1: TITLE SLIDE
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.navy };

  // Top decorative bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.06,
    fill: { color: C.cyan },
  });

  // Decorative accent circles (background)
  slide.addShape(pres.shapes.OVAL, {
    x: 7.5, y: -1.5, w: 5, h: 5,
    fill: { color: C.darkBlue, transparency: 60 },
  });
  slide.addShape(pres.shapes.OVAL, {
    x: 8.5, y: 3.0, w: 3, h: 3,
    fill: { color: C.steel, transparency: 70 },
  });

  // "硕士学位论文答辩" label
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.8, y: 1.0, w: 2.6, h: 0.45,
    fill: { color: C.teal },
  });
  slide.addText("硕士学位论文答辩", {
    x: 0.8, y: 1.0, w: 2.6, h: 0.45,
    fontSize: 14, fontFace: "Calibri", bold: true,
    color: C.white, align: "center", valign: "middle",
  });

  // Main title
  slide.addText("基于数据感知的多智能体\n专利分析系统设计与实现", {
    x: 0.8, y: 1.7, w: 7.5, h: 1.6,
    fontSize: 30, fontFace: "Georgia", bold: true,
    color: C.white, align: "left", valign: "middle",
  });

  // Subtitle line
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.8, y: 3.45, w: 2.0, h: 0.035,
    fill: { color: C.cyan },
  });

  // English subtitle
  slide.addText("Design and Implementation of a Data-Aware\nMulti-Agent Patent Analysis System", {
    x: 0.8, y: 3.6, w: 7.5, h: 0.8,
    fontSize: 14, fontFace: "Calibri",
    color: C.lightText, align: "left",
  });

  // Author info
  slide.addText([
    { text: "答辩人：XXX        ", options: { fontSize: 13, color: C.lightText } },
    { text: "指导教师：XXX 教授", options: { fontSize: 13, color: C.lightText } },
  ], {
    x: 0.8, y: 4.7, w: 7.0, h: 0.4,
    fontFace: "Calibri",
  });

  // Bottom bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.425, w: 10, h: 0.2,
    fill: { color: C.teal, transparency: 40 },
  });

  slide.addText("智慧治理学院 · 电子信息专业", {
    x: 0.8, y: 5.05, w: 5, h: 0.35,
    fontSize: 11, fontFace: "Calibri", color: C.lightText,
  });
})();

// ============================================================
// SLIDE 2: OUTLINE
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSlideTitle(slide, "汇报提纲");
  addFooter(slide, 2, TOTAL_PAGES);

  const items = [
    { num: "01", title: "研究背景与问题", desc: "专利计量分析的现状与挑战" },
    { num: "02", title: "相关工作与定位", desc: "数据感知规划的研究空白" },
    { num: "03", title: "系统设计方案",   desc: "四智能体架构与三能力层" },
    { num: "04", title: "关键技术实现",   desc: "DataPreview · 双图谱 · 两轮迭代" },
    { num: "05", title: "实验与评估",     desc: "渐进 + 消融实验与关键发现" },
    { num: "06", title: "应用案例验证",   desc: "三场景端到端分析示例" },
    { num: "07", title: "总结与展望",     desc: "研究贡献与后续方向" },
  ];

  items.forEach((item, i) => {
    const yStart = 1.1;
    const yGap = 0.6;
    const y = yStart + i * yGap;

    // Number badge
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.8, y: y, w: 0.65, h: 0.45,
      fill: { color: i === 0 ? C.teal : C.navy },
    });
    slide.addText(item.num, {
      x: 0.8, y: y, w: 0.65, h: 0.45,
      fontSize: 14, fontFace: "Georgia", bold: true,
      color: C.white, align: "center", valign: "middle",
    });

    // Title
    slide.addText(item.title, {
      x: 1.7, y: y, w: 3.0, h: 0.45,
      fontSize: 16, fontFace: "Calibri", bold: true,
      color: C.navy, valign: "middle", margin: 0,
    });

    // Description
    slide.addText(item.desc, {
      x: 4.8, y: y, w: 4.5, h: 0.45,
      fontSize: 12, fontFace: "Calibri",
      color: C.subtext, valign: "middle", margin: 0,
    });

    // Divider line
    if (i < items.length - 1) {
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 0.8, y: y + 0.5, w: 8.4, h: 0.01,
        fill: { color: C.stripe },
      });
    }
  });
})();

// ============================================================
// SLIDE 3: RESEARCH BACKGROUND
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSlideTitle(slide, "研究背景：专利计量分析的挑战");
  addFooter(slide, 3, TOTAL_PAGES);

  // Left card: patent data characteristics
  addCard(slide, 0.5, 1.1, 4.2, 2.0, { accentColor: C.teal });
  slide.addText("专利数据四重属性", {
    x: 0.75, y: 1.2, w: 3.8, h: 0.4,
    fontSize: 15, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });
  slide.addText([
    { text: "技术属性", options: { bold: true, breakLine: true, color: C.teal } },
    { text: "  IPC分类、技术方案、权利要求", options: { breakLine: true, color: C.subtext } },
    { text: "法律属性", options: { bold: true, breakLine: true, color: C.teal } },
    { text: "  授权状态、质押、转让记录", options: { breakLine: true, color: C.subtext } },
    { text: "时间属性", options: { bold: true, breakLine: true, color: C.teal } },
    { text: "  申请-授权-维持生命周期", options: { breakLine: true, color: C.subtext } },
    { text: "组织属性", options: { bold: true, breakLine: true, color: C.teal } },
    { text: "  发明人、申请人、优先权国家", options: { color: C.subtext } },
  ], {
    x: 0.75, y: 1.65, w: 3.8, h: 1.35,
    fontSize: 11, fontFace: "Calibri", paraSpaceAfter: 2,
  });

  // Right card: current challenges
  addCard(slide, 5.2, 1.1, 4.2, 2.0, { accentColor: C.orange });
  slide.addText("当前流程痛点", {
    x: 5.45, y: 1.2, w: 3.8, h: 0.4,
    fontSize: 15, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });
  slide.addText([
    { text: "人工密集", options: { bold: true, color: C.orange, breakLine: true } },
    { text: "  变量选择、方法匹配高度依赖专家经验", options: { color: C.subtext, breakLine: true } },
    { text: "方案泛化", options: { bold: true, color: C.orange, breakLine: true } },
    { text: "  分析方案与数据特征脱钩", options: { color: C.subtext, breakLine: true } },
    { text: "可复现性低", options: { bold: true, color: C.orange, breakLine: true } },
    { text: "  每次分析从零开始，过程难追溯", options: { color: C.subtext, breakLine: true } },
    { text: "迭代成本高", options: { bold: true, color: C.orange, breakLine: true } },
    { text: "  发现方案不足后需全流程重来", options: { color: C.subtext } },
  ], {
    x: 5.45, y: 1.65, w: 3.8, h: 1.35,
    fontSize: 11, fontFace: "Calibri", paraSpaceAfter: 2,
  });

  // Bottom: core gap highlight
  addCard(slide, 0.5, 3.4, 8.9, 1.0, { accentColor: C.navy });
  slide.addText("核心差距", {
    x: 0.75, y: 3.5, w: 2.0, h: 0.35,
    fontSize: 14, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });
  slide.addText([
    { text: "执行层自动化（代码生成/运行）已有较多突破   →   ", options: { color: C.subtext } },
    { text: "规划层自动化（方案设计/优化）仍高度依赖人工", options: { bold: true, color: C.teal } },
  ], {
    x: 0.75, y: 3.85, w: 8.4, h: 0.4,
    fontSize: 12, fontFace: "Calibri", margin: 0,
  });

  // Bottom highlight: core question
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.6, w: 8.9, h: 0.7,
    fill: { color: C.navy },
  });
  slide.addText("核心问题：如何让多智能体系统基于具体数据集，自动生成\"数据感知的\"分析方案？", {
    x: 0.7, y: 4.6, w: 8.5, h: 0.7,
    fontSize: 14, fontFace: "Calibri", bold: true,
    color: C.white, valign: "middle",
  });
})();

// ============================================================
// SLIDE 4: RESEARCH CONTENT & INNOVATIONS
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSlideTitle(slide, "研究内容与创新点");
  addFooter(slide, 4, TOTAL_PAGES);

  // Three research contents as cards
  const contents = [
    {
      num: "1", title: "数据感知方案生成",
      desc: "DataPreview（列级统计、Pearson相关、时间趋势）+ GraphPreview（社区检测、中心性）→ 结构化洞察 → 分析蓝图",
      color: C.teal,
    },
    {
      num: "2", title: "双知识图谱协同",
      desc: "因果图谱（30变量、99路径）约束假设空间 + 方法图谱（86+方法）约束执行空间",
      color: C.steel,
    },
    {
      num: "3", title: "两轮迭代优化",
      desc: "第一轮探索性分析 → 差距识别 → 第二轮验证性深化，从效应发现到机制解释",
      color: C.navy,
    },
  ];

  contents.forEach((item, i) => {
    const y = 1.1 + i * 1.15;
    addCard(slide, 0.5, y, 5.5, 0.95, { accentColor: item.color });

    slide.addShape(pres.shapes.OVAL, {
      x: 0.75, y: y + 0.2, w: 0.5, h: 0.5,
      fill: { color: item.color },
    });
    slide.addText(item.num, {
      x: 0.75, y: y + 0.2, w: 0.5, h: 0.5,
      fontSize: 16, fontFace: "Georgia", bold: true,
      color: C.white, align: "center", valign: "middle",
    });
    slide.addText(item.title, {
      x: 1.45, y: y + 0.08, w: 4.3, h: 0.35,
      fontSize: 14, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
    });
    slide.addText(item.desc, {
      x: 1.45, y: y + 0.42, w: 4.4, h: 0.45,
      fontSize: 10, fontFace: "Calibri", color: C.subtext, margin: 0,
    });
  });

  // Right side: innovations
  addCard(slide, 6.3, 1.1, 3.2, 3.35, { accentColor: C.gold });
  slide.addText("三项创新点", {
    x: 6.55, y: 1.2, w: 2.8, h: 0.4,
    fontSize: 15, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });

  const innovations = [
    { icon: "1", text: "提出\"数据感知前置\"的方案生成流程，将规划起点从问题语义转向数据证据" },
    { icon: "2", text: "提出双知识图谱协同架构，因果图谱约束假设合理性，方法图谱约束执行可行性" },
    { icon: "3", text: "通过重复实验识别知识图谱收益边界：在结构锚点清晰的问题上作用更明显" },
  ];

  innovations.forEach((item, i) => {
    const y = 1.7 + i * 0.85;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 6.55, y: y, w: 0.35, h: 0.35,
      fill: { color: C.gold },
    });
    slide.addText(item.icon, {
      x: 6.55, y: y, w: 0.35, h: 0.35,
      fontSize: 12, fontFace: "Georgia", bold: true,
      color: C.white, align: "center", valign: "middle",
    });
    slide.addText(item.text, {
      x: 7.05, y: y, w: 2.3, h: 0.7,
      fontSize: 10, fontFace: "Calibri", color: C.text, margin: 0,
    });
  });

  // Bottom note
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.7, w: 9.0, h: 0.55,
    fill: { color: C.navy },
  });
  slide.addText("论文类型：系统算法类  |  技术路线：系统构建 + 消融实验 + 案例验证", {
    x: 0.7, y: 4.7, w: 8.6, h: 0.55,
    fontSize: 13, fontFace: "Calibri", bold: true,
    color: C.white, valign: "middle",
  });
})();

// ============================================================
// SLIDE 5: RELATED WORK & POSITIONING
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSlideTitle(slide, "相关工作与研究定位");
  addFooter(slide, 5, TOTAL_PAGES);

  // Comparison table
  const tableHeader = [
    { text: "系统/方法", options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 11, fontFace: "Calibri", align: "center", valign: "middle" } },
    { text: "核心创新", options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 11, fontFace: "Calibri", align: "center", valign: "middle" } },
    { text: "数据感知", options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 11, fontFace: "Calibri", align: "center", valign: "middle" } },
    { text: "规划层优化", options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 11, fontFace: "Calibri", align: "center", valign: "middle" } },
    { text: "知识约束", options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 11, fontFace: "Calibri", align: "center", valign: "middle" } },
  ];

  const cellOpts = (stripe) => ({ fill: { color: stripe ? C.lightBg : C.cardBg }, fontSize: 10, fontFace: "Calibri", color: C.text, valign: "middle" });
  const cellCenter = (stripe) => ({ ...cellOpts(stripe), align: "center" });

  const tableRows = [
    tableHeader,
    [
      { text: "DS-Agent", options: cellOpts(false) },
      { text: "案例推理(CBR)，历史任务库", options: cellOpts(false) },
      { text: "---", options: cellCenter(false) },
      { text: "---", options: cellCenter(false) },
      { text: "---", options: cellCenter(false) },
    ],
    [
      { text: "Data Interpreter", options: cellOpts(true) },
      { text: "动态规划+代码反馈迭代", options: cellOpts(true) },
      { text: "部分", options: cellCenter(true) },
      { text: "---", options: cellCenter(true) },
      { text: "---", options: cellCenter(true) },
    ],
    [
      { text: "AI Scientist v2", options: cellOpts(false) },
      { text: "假设→实验→论文全自动", options: cellOpts(false) },
      { text: "---", options: cellCenter(false) },
      { text: "部分", options: cellCenter(false) },
      { text: "---", options: cellCenter(false) },
    ],
    [
      { text: "GraphRAG", options: cellOpts(true) },
      { text: "图结构增强复杂问答", options: cellOpts(true) },
      { text: "---", options: cellCenter(true) },
      { text: "---", options: cellCenter(true) },
      { text: "部分", options: cellCenter(true) },
    ],
    [
      { text: "本文系统", options: { ...cellOpts(false), bold: true, color: C.teal } },
      { text: "数据感知+双图谱+迭代", options: { ...cellOpts(false), bold: true, color: C.teal } },
      { text: "\u2713", options: { ...cellCenter(false), bold: true, color: C.green, fontSize: 16 } },
      { text: "\u2713", options: { ...cellCenter(false), bold: true, color: C.green, fontSize: 16 } },
      { text: "\u2713", options: { ...cellCenter(false), bold: true, color: C.green, fontSize: 16 } },
    ],
  ];

  slide.addTable(tableRows, {
    x: 0.5, y: 1.1, w: 9.0,
    colW: [1.6, 2.5, 1.2, 1.2, 1.2],
    rowH: [0.4, 0.38, 0.38, 0.38, 0.38, 0.42],
    border: { pt: 0.5, color: C.stripe },
  });

  // Bottom: key gap statement
  addCard(slide, 0.5, 3.7, 8.9, 1.5, { accentColor: C.teal });
  slide.addText("研究空白与本文定位", {
    x: 0.75, y: 3.8, w: 4.0, h: 0.35,
    fontSize: 14, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });

  slide.addText([
    { text: "三类共性不足  →  三项研究内容", options: { bold: true, color: C.teal, breakLine: true, fontSize: 12 } },
    { text: "1. 规划缺数据感知  →  DataPreview + GraphPreview + 洞察生成", options: { color: C.text, breakLine: true } },
    { text: "2. 专利文本多、计量分析少  →  四智能体端到端系统", options: { color: C.text, breakLine: true } },
    { text: "3. 检索问答多、分析引导少  →  双图谱协同约束框架", options: { color: C.text } },
  ], {
    x: 0.75, y: 4.15, w: 8.4, h: 0.9,
    fontSize: 11, fontFace: "Calibri", paraSpaceAfter: 3, margin: 0,
  });
})();

// ============================================================
// SLIDE 6: SECTION DIVIDER - SYSTEM DESIGN
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSectionDivider(slide, "03", "系统设计方案");
  addFooter(slide, 6, TOTAL_PAGES);

  slide.addText([
    { text: "四智能体流水线架构", options: { bold: true, breakLine: true, color: C.navy } },
    { text: "三层基础能力（数据感知 · 知识约束 · 执行反馈）", options: { breakLine: true, color: C.subtext } },
    { text: "数据感知方案生成流程（核心创新）", options: { color: C.subtext } },
  ], {
    x: 2.0, y: 3.3, w: 6.0, h: 1.2,
    fontSize: 14, fontFace: "Calibri", paraSpaceAfter: 6,
  });
})();

// ============================================================
// SLIDE 7: SYSTEM ARCHITECTURE
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSlideTitle(slide, "系统总体架构：四智能体流水线");
  addFooter(slide, 7, TOTAL_PAGES);

  // Four agents as horizontal pipeline
  const agents = [
    { name: "Strategist\n(战略家)", desc: "数据感知\n双图谱约束\nDAG蓝图生成", color: C.teal, model: "Qwen" },
    { name: "Methodologist\n(方法师)", desc: "技术规格化\n精确执行合同\n参数配置", color: C.steel, model: "Qwen" },
    { name: "CodingAgent\n(编码员)", desc: "代码生成\n沙箱执行\n结果捕获", color: C.navy, model: "Claude" },
    { name: "Reviewer\n(评审员)", desc: "结构验证\n语义评估\n最终报告", color: "6D28D9", model: "Qwen" },
  ];

  agents.forEach((agent, i) => {
    const x = 0.4 + i * 2.4;
    const y = 1.1;

    // Agent card
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.1, h: 2.3,
      fill: { color: C.cardBg },
      shadow: makeShadow(),
    });

    // Header bar
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.1, h: 0.55,
      fill: { color: agent.color },
    });
    slide.addText(agent.name, {
      x, y, w: 2.1, h: 0.55,
      fontSize: 11, fontFace: "Calibri", bold: true,
      color: C.white, align: "center", valign: "middle",
    });

    // Description
    slide.addText(agent.desc, {
      x: x + 0.1, y: y + 0.65, w: 1.9, h: 1.0,
      fontSize: 10, fontFace: "Calibri", color: C.text,
      align: "center", valign: "top",
    });

    // Model badge
    slide.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.55, y: y + 1.8, w: 1.0, h: 0.3,
      fill: { color: agent.model === "Claude" ? C.orange : C.steel },
    });
    slide.addText(agent.model, {
      x: x + 0.55, y: y + 1.8, w: 1.0, h: 0.3,
      fontSize: 9, fontFace: "Calibri", bold: true,
      color: C.white, align: "center", valign: "middle",
    });

    // Arrow between agents
    if (i < 3) {
      slide.addShape(pres.shapes.LINE, {
        x: x + 2.1, y: y + 1.15, w: 0.3, h: 0,
        line: { color: C.teal, width: 2 },
      });
      // Arrow head (small triangle approximation)
      slide.addText("\u25B6", {
        x: x + 2.25, y: y + 0.95, w: 0.3, h: 0.4,
        fontSize: 10, color: C.teal, align: "center", valign: "middle",
      });
    }
  });

  // Bottom: Three capability layers
  const layers = [
    { name: "数据感知层", desc: "DataPreview + GraphPreview + 洞察生成", color: C.teal },
    { name: "知识约束层", desc: "因果图谱(30变量) + 方法图谱(86+方法)", color: C.steel },
    { name: "执行反馈层", desc: "两轮迭代：探索 → 差距分析 → 验证", color: C.navy },
  ];

  layers.forEach((layer, i) => {
    const x = 0.4 + i * 3.1;
    const y = 3.8;
    addCard(slide, x, y, 2.85, 0.8, { accentColor: layer.color });
    slide.addText(layer.name, {
      x: x + 0.2, y: y + 0.05, w: 2.5, h: 0.35,
      fontSize: 12, fontFace: "Calibri", bold: true, color: layer.color, margin: 0,
    });
    slide.addText(layer.desc, {
      x: x + 0.2, y: y + 0.38, w: 2.5, h: 0.35,
      fontSize: 9, fontFace: "Calibri", color: C.subtext, margin: 0,
    });
  });

  // Label
  slide.addText("三层基础能力", {
    x: 0.4, y: 3.5, w: 2.0, h: 0.3,
    fontSize: 11, fontFace: "Calibri", bold: true, color: C.subtext, margin: 0,
  });
})();

// ============================================================
// SLIDE 8: DATA AWARENESS MECHANISM
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSlideTitle(slide, "核心创新：数据感知方案生成流程");
  addFooter(slide, 8, TOTAL_PAGES);

  // Flow: 3 stages
  // Stage 1: Data Fact Extraction
  addCard(slide, 0.3, 1.2, 2.8, 2.8, { accentColor: C.teal });
  slide.addText("阶段一：数据事实提取", {
    x: 0.55, y: 1.3, w: 2.4, h: 0.35,
    fontSize: 12, fontFace: "Calibri", bold: true, color: C.teal, margin: 0,
  });
  slide.addText([
    { text: "DataPreview", options: { bold: true, breakLine: true, color: C.navy } },
    { text: "  列类型识别、Pearson相关", options: { breakLine: true, color: C.subtext } },
    { text: "  分组对比、时间趋势", options: { breakLine: true, color: C.subtext } },
    { text: "", options: { breakLine: true } },
    { text: "GraphPreview", options: { bold: true, breakLine: true, color: C.navy } },
    { text: "  自动图构建（引用/共现/合作）", options: { breakLine: true, color: C.subtext } },
    { text: "  Louvain社区、介数中心性", options: { breakLine: true, color: C.subtext } },
    { text: "", options: { breakLine: true } },
    { text: "分层抽样", options: { bold: true, breakLine: true, color: C.navy } },
    { text: "  按IPC分部A-H各抽5条", options: { color: C.subtext } },
  ], {
    x: 0.55, y: 1.7, w: 2.4, h: 2.2,
    fontSize: 10, fontFace: "Calibri", paraSpaceAfter: 1,
  });

  // Arrow 1
  slide.addText("\u25B6", {
    x: 3.15, y: 2.2, w: 0.4, h: 0.4,
    fontSize: 18, color: C.teal, align: "center", valign: "middle",
  });

  // Stage 2: Insight Generation
  addCard(slide, 3.6, 1.2, 2.8, 2.8, { accentColor: C.gold });
  slide.addText("阶段二：洞察生成", {
    x: 3.85, y: 1.3, w: 2.4, h: 0.35,
    fontSize: 12, fontFace: "Calibri", bold: true, color: C.gold, margin: 0,
  });
  slide.addText([
    { text: "LLM提示词融合三类证据", options: { bold: true, breakLine: true, color: C.navy } },
    { text: "", options: { breakLine: true } },
    { text: "三类洞察输出：", options: { bold: true, breakLine: true, color: C.navy } },
    { text: "  统计信号型", options: { breakLine: true, color: C.teal } },
    { text: "  \"近年授权专利被引量骤降\"", options: { breakLine: true, color: C.subtext } },
    { text: "  图结构型", options: { breakLine: true, color: C.teal } },
    { text: "  \"H04L9/40为核心枢纽\"", options: { breakLine: true, color: C.subtext } },
    { text: "  内容驱动型", options: { breakLine: true, color: C.teal } },
    { text: "  \"硬件安全术语频繁\"", options: { color: C.subtext } },
  ], {
    x: 3.85, y: 1.7, w: 2.4, h: 2.2,
    fontSize: 10, fontFace: "Calibri", paraSpaceAfter: 1,
  });

  // Arrow 2
  slide.addText("\u25B6", {
    x: 6.45, y: 2.2, w: 0.4, h: 0.4,
    fontSize: 18, color: C.gold, align: "center", valign: "middle",
  });

  // Stage 3: Blueprint Planning
  addCard(slide, 6.9, 1.2, 2.8, 2.8, { accentColor: C.navy });
  slide.addText("阶段三：蓝图规划", {
    x: 7.15, y: 1.3, w: 2.4, h: 0.35,
    fontSize: 12, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });
  slide.addText([
    { text: "选择 2-3 条核心洞察", options: { bold: true, breakLine: true, color: C.navy } },
    { text: "", options: { breakLine: true } },
    { text: "双图谱约束：", options: { bold: true, breakLine: true, color: C.navy } },
    { text: "  因果图谱 → 约束假设合理性", options: { breakLine: true, color: C.subtext } },
    { text: "  方法图谱 → 约束方法可行性", options: { breakLine: true, color: C.subtext } },
    { text: "", options: { breakLine: true } },
    { text: "输出：DAG任务蓝图", options: { bold: true, breakLine: true, color: C.teal } },
    { text: "  任务依赖关系", options: { breakLine: true, color: C.subtext } },
    { text: "  列名、参数、输出格式", options: { color: C.subtext } },
  ], {
    x: 7.15, y: 1.7, w: 2.4, h: 2.2,
    fontSize: 10, fontFace: "Calibri", paraSpaceAfter: 1,
  });

  // Bottom: key principle
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 4.35, w: 9.4, h: 0.55,
    fill: { color: C.navy },
  });
  slide.addText("核心设计原则：\"数据先证据化、方案后生成\" —— 将规划起点从问题语义转向数据事实", {
    x: 0.5, y: 4.35, w: 9.0, h: 0.55,
    fontSize: 13, fontFace: "Calibri", bold: true,
    color: C.white, valign: "middle",
  });
})();

// ============================================================
// SLIDE 9: DUAL KNOWLEDGE GRAPHS
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSlideTitle(slide, "双知识图谱协同机制");
  addFooter(slide, 9, TOTAL_PAGES);

  // Left: Causal Graph
  addCard(slide, 0.4, 1.1, 4.3, 3.2, { accentColor: C.steel });
  slide.addText("因果图谱 — 约束假设空间", {
    x: 0.65, y: 1.2, w: 3.8, h: 0.4,
    fontSize: 14, fontFace: "Calibri", bold: true, color: C.steel, margin: 0,
  });

  // Stats row
  const causalStats = [
    { label: "变量数", value: "30", color: C.steel },
    { label: "因果路径", value: "99", color: C.steel },
    { label: "策略模板", value: "6", color: C.steel },
  ];
  causalStats.forEach((stat, i) => {
    const x = 0.65 + i * 1.3;
    slide.addText(stat.value, {
      x, y: 1.7, w: 1.1, h: 0.45,
      fontSize: 24, fontFace: "Georgia", bold: true,
      color: stat.color, align: "center", valign: "middle",
    });
    slide.addText(stat.label, {
      x, y: 2.1, w: 1.1, h: 0.25,
      fontSize: 9, fontFace: "Calibri",
      color: C.subtext, align: "center", valign: "middle",
    });
  });

  // Strategy templates list
  slide.addText("六种假设策略模板", {
    x: 0.65, y: 2.5, w: 3.8, h: 0.3,
    fontSize: 11, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });
  slide.addText([
    { text: "理论迁移 · 路径探索 · 边界条件", options: { breakLine: true, color: C.text } },
    { text: "中介机制 · 反事实推理 · 交互效应", options: { color: C.text } },
  ], {
    x: 0.65, y: 2.8, w: 3.8, h: 0.5,
    fontSize: 10, fontFace: "Calibri", paraSpaceAfter: 3,
  });

  // Workflow text
  slide.addText("先确定\"研究什么\" → 再确定\"怎么做\"", {
    x: 0.65, y: 3.5, w: 3.8, h: 0.35,
    fontSize: 10, fontFace: "Calibri", italic: true, color: C.teal, margin: 0,
  });

  // Right: Method Graph
  addCard(slide, 5.2, 1.1, 4.3, 3.2, { accentColor: "6D28D9" });
  slide.addText("方法图谱 — 约束执行空间", {
    x: 5.45, y: 1.2, w: 3.8, h: 0.4,
    fontSize: 14, fontFace: "Calibri", bold: true, color: "6D28D9", margin: 0,
  });

  // Stats
  const methodStats = [
    { label: "分析方法", value: "86+", color: "6D28D9" },
    { label: "两大维度", value: "2", color: "6D28D9" },
  ];
  methodStats.forEach((stat, i) => {
    const x = 5.65 + i * 1.8;
    slide.addText(stat.value, {
      x, y: 1.7, w: 1.5, h: 0.45,
      fontSize: 24, fontFace: "Georgia", bold: true,
      color: stat.color, align: "center", valign: "middle",
    });
    slide.addText(stat.label, {
      x, y: 2.1, w: 1.5, h: 0.25,
      fontSize: 9, fontFace: "Calibri",
      color: C.subtext, align: "center", valign: "middle",
    });
  });

  slide.addText([
    { text: "变量测量方法", options: { bold: true, breakLine: true, color: C.navy } },
    { text: "  为每个变量推荐量化方式", options: { breakLine: true, color: C.subtext } },
    { text: "", options: { breakLine: true } },
    { text: "统计分析方法", options: { bold: true, breakLine: true, color: C.navy } },
    { text: "  根据假设类型自动匹配", options: { breakLine: true, color: C.subtext } },
    { text: "  中介假设→Bootstrap中介检验", options: { breakLine: true, color: C.subtext } },
    { text: "  调节假设→层次回归方法", options: { color: C.subtext } },
  ], {
    x: 5.45, y: 2.45, w: 3.8, h: 1.4,
    fontSize: 10, fontFace: "Calibri", paraSpaceAfter: 1,
  });

  // Bottom bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 4.55, w: 9.2, h: 0.5,
    fill: { color: C.navy },
  });
  slide.addText("联动使用：因果图谱确定\"研究什么\" + 方法图谱确定\"怎么做\" → 双重约束确保方案可行", {
    x: 0.6, y: 4.55, w: 8.8, h: 0.5,
    fontSize: 12, fontFace: "Calibri", bold: true,
    color: C.white, valign: "middle",
  });
})();

// ============================================================
// SLIDE 10: TWO-ROUND ITERATION
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSlideTitle(slide, "两轮迭代优化机制");
  addFooter(slide, 10, TOTAL_PAGES);

  // Round 1
  addCard(slide, 0.4, 1.1, 3.8, 1.8, { accentColor: C.teal });
  slide.addText("第一轮：探索性分析", {
    x: 0.65, y: 1.2, w: 3.3, h: 0.35,
    fontSize: 13, fontFace: "Calibri", bold: true, color: C.teal, margin: 0,
  });
  slide.addText([
    { text: "基于数据洞察生成初始DAG", options: { breakLine: true, color: C.text } },
    { text: "2-3个探索性任务", options: { breakLine: true, color: C.text } },
    { text: "目标：验证效应存在性", options: { bold: true, color: C.navy } },
  ], {
    x: 0.65, y: 1.6, w: 3.3, h: 1.0,
    fontSize: 11, fontFace: "Calibri", paraSpaceAfter: 4, margin: 0,
    bullet: true,
  });
  slide.addText("典型方法：OLS · t检验 · 描述统计", {
    x: 0.65, y: 2.5, w: 3.3, h: 0.3,
    fontSize: 9, fontFace: "Calibri", italic: true, color: C.subtext, margin: 0,
  });

  // Gap Analysis (middle)
  slide.addText("\u25B6", {
    x: 4.3, y: 1.7, w: 0.4, h: 0.4,
    fontSize: 18, color: C.gold, align: "center", valign: "middle",
  });

  addCard(slide, 4.8, 1.4, 1.0, 1.2);
  slide.addText("差距\n分析", {
    x: 4.8, y: 1.5, w: 1.0, h: 1.0,
    fontSize: 11, fontFace: "Calibri", bold: true,
    color: C.gold, align: "center", valign: "middle",
  });

  slide.addText("\u25B6", {
    x: 5.9, y: 1.7, w: 0.4, h: 0.4,
    fontSize: 18, color: C.gold, align: "center", valign: "middle",
  });

  // Round 2
  addCard(slide, 6.3, 1.1, 3.3, 1.8, { accentColor: C.navy });
  slide.addText("第二轮：验证性深化", {
    x: 6.55, y: 1.2, w: 2.8, h: 0.35,
    fontSize: 13, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });
  slide.addText([
    { text: "引入控制变量、非线性模型", options: { breakLine: true, color: C.text } },
    { text: "交互项、机制检验", options: { breakLine: true, color: C.text } },
    { text: "目标：机制解释", options: { bold: true, color: C.navy } },
  ], {
    x: 6.55, y: 1.6, w: 2.8, h: 1.0,
    fontSize: 11, fontFace: "Calibri", paraSpaceAfter: 4, margin: 0,
    bullet: true,
  });
  slide.addText("负二项回归 · 层次回归 · ANCOVA", {
    x: 6.55, y: 2.5, w: 2.8, h: 0.3,
    fontSize: 9, fontFace: "Calibri", italic: true, color: C.subtext, margin: 0,
  });

  // Gap analysis detail
  addCard(slide, 0.4, 3.2, 9.2, 1.0);
  slide.addText("差距分析识别三类缺口", {
    x: 0.6, y: 3.3, w: 3.0, h: 0.3,
    fontSize: 12, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });
  slide.addText([
    { text: "1  已发现但未深入验证的效应", options: { breakLine: true, color: C.text } },
    { text: "2  方案提及但未覆盖的维度", options: { breakLine: true, color: C.text } },
    { text: "3  可能受混杂因素影响的结论", options: { color: C.text } },
  ], {
    x: 0.6, y: 3.6, w: 8.8, h: 0.5,
    fontSize: 10, fontFace: "Calibri", paraSpaceAfter: 2, margin: 0,
  });

  // Bottom: justification
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 4.5, w: 9.2, h: 0.6,
    fill: { color: C.navy },
  });
  slide.addText("设计依据：\"探索-验证\"实证研究经典结构 | 第三轮边际收益递减 | 两轮在深度与成本间最优", {
    x: 0.6, y: 4.5, w: 8.8, h: 0.6,
    fontSize: 11, fontFace: "Calibri", bold: true,
    color: C.white, valign: "middle",
  });
})();

// ============================================================
// SLIDE 11: SECTION DIVIDER - EXPERIMENT
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSectionDivider(slide, "05", "实验与评估");
  addFooter(slide, 11, TOTAL_PAGES);

  slide.addText([
    { text: "90组重复实验：渐进叠加主线 + 组件消融补强", options: { bold: true, breakLine: true, color: C.navy } },
    { text: "六模式总览用于展示整体分布", options: { breakLine: true, color: C.subtext } },
    { text: "机制归因回到 D/A/B/C 与 C/E/F 两条比较主线", options: { color: C.subtext } },
  ], {
    x: 2.0, y: 3.3, w: 6.0, h: 1.2,
    fontSize: 14, fontFace: "Calibri", paraSpaceAfter: 6,
  });
})();

// ============================================================
// SLIDE 12: EXPERIMENT DESIGN
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSlideTitle(slide, "实验设计：渐进叠加 + 组件消融");
  addFooter(slide, 12, TOTAL_PAGES);

  addCard(slide, 0.4, 1.05, 4.35, 2.45, { accentColor: C.teal });
  slide.addText("主实验：四方案渐进叠加", {
    x: 0.65, y: 1.18, w: 3.9, h: 0.32,
    fontSize: 14, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });
  slide.addText([
    { text: "D_baseline0", options: { bold: true, color: C.subtext, breakLine: true } },
    { text: "纯LLM基线", options: { color: C.subtext, breakLine: true } },
    { text: "A_template", options: { bold: true, color: C.orange, breakLine: true } },
    { text: "加入知识图谱模板", options: { color: C.subtext, breakLine: true } },
    { text: "B_data_aware", options: { bold: true, color: C.steel, breakLine: true } },
    { text: "加入数据感知证据", options: { color: C.subtext, breakLine: true } },
    { text: "C_iterative", options: { bold: true, color: C.teal, breakLine: true } },
    { text: "加入两轮迭代，形成完整系统", options: { color: C.subtext } },
  ], {
    x: 0.65, y: 1.58, w: 3.95, h: 1.65,
    fontSize: 10, fontFace: "Calibri", paraSpaceAfter: 2,
  });

  addCard(slide, 5.05, 1.05, 4.35, 2.45, { accentColor: C.orange });
  slide.addText("补强实验：组件消融", {
    x: 5.3, y: 1.18, w: 3.9, h: 0.32,
    fontSize: 14, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });
  slide.addText([
    { text: "C_iterative", options: { bold: true, color: C.teal, breakLine: true } },
    { text: "完整系统", options: { color: C.subtext, breakLine: true } },
    { text: "E_ablate_data", options: { bold: true, color: C.orange, breakLine: true } },
    { text: "移除数据感知，保留知识图谱与迭代", options: { color: C.subtext, breakLine: true } },
    { text: "F_ablate_kg", options: { bold: true, color: C.steel, breakLine: true } },
    { text: "移除知识图谱，保留数据感知与迭代", options: { color: C.subtext } },
  ], {
    x: 5.3, y: 1.58, w: 3.9, h: 1.55,
    fontSize: 10, fontFace: "Calibri", paraSpaceAfter: 2,
  });

  addCard(slide, 0.4, 3.8, 9.0, 1.25, { accentColor: C.navy });
  const expStats = [
    { label: "研究问题", value: "3", desc: "影响力·融合·竞争" },
    { label: "实验模式", value: "6", desc: "D/A/B/C + E/F" },
    { label: "重复次数", value: "5", desc: "每问题每模式独立重复" },
    { label: "实验总量", value: "90", desc: "6模式 × 3问题 × 5次" },
  ];
  expStats.forEach((s, i) => {
    const x = 0.8 + i * 2.2;
    slide.addText(s.value, {
      x, y: 4.1, w: 1.5, h: 0.36,
      fontSize: 22, fontFace: "Georgia", bold: true,
      color: C.teal, align: "center", valign: "middle",
    });
    slide.addText(s.label, {
      x, y: 4.45, w: 1.5, h: 0.18,
      fontSize: 9, fontFace: "Calibri", bold: true,
      color: C.navy, align: "center",
    });
    slide.addText(s.desc, {
      x, y: 4.63, w: 1.5, h: 0.2,
      fontSize: 8, fontFace: "Calibri",
      color: C.subtext, align: "center",
    });
  });
})();

// ============================================================
// SLIDE 13: KEY RESULTS - CHART
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSlideTitle(slide, "实验结果总览：六模式重复实验");
  addFooter(slide, 13, TOTAL_PAGES);

  slide.addChart(pres.charts.BAR, [
    { name: "LLM总分", labels: ["D", "A", "B", "C", "E", "F"], values: [15.47, 16.53, 18.60, 23.87, 22.07, 22.20] },
  ], {
    x: 0.35, y: 1.0, w: 5.7, h: 3.35,
    barDir: "col",
    chartColors: [C.teal],
    catAxisLabelColor: C.text,
    catAxisLabelFontSize: 10,
    valAxisLabelColor: C.subtext,
    valAxisLabelFontSize: 9,
    valGridLine: { color: C.stripe, size: 0.5 },
    catGridLine: { style: "none" },
    showLegend: false,
    valAxisMaxVal: 26,
    valAxisMinVal: 0,
    chartArea: { fill: { color: C.cardBg }, roundedCorners: true },
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelColor: C.text,
    dataLabelFormatCode: "0.00",
  });

  addCard(slide, 6.3, 1.0, 3.4, 3.35, { accentColor: C.orange });
  slide.addText("六模式总览（n=5）", {
    x: 6.55, y: 1.1, w: 2.9, h: 0.32,
    fontSize: 13, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });
  const overview = [
    { name: "C_iterative", score: "23.87 ± 1.77", color: C.teal },
    { name: "F_ablate_kg", score: "22.20 ± 3.26", color: C.steel },
    { name: "E_ablate_data", score: "22.07 ± 1.75", color: C.orange },
    { name: "B_data_aware", score: "18.60 ± 2.82", color: C.darkBlue },
    { name: "A_template", score: "16.53 ± 2.64", color: C.gold },
    { name: "D_baseline0", score: "15.47 ± 1.55", color: C.subtext },
  ];
  overview.forEach((item, i) => {
    const y = 1.55 + i * 0.4;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 6.55, y: y + 0.06, w: 0.12, h: 0.12,
      fill: { color: item.color },
    });
    slide.addText(item.name, {
      x: 6.75, y, w: 1.6, h: 0.22,
      fontSize: 9.5, fontFace: "Calibri", color: C.text, margin: 0,
    });
    slide.addText(item.score, {
      x: 8.2, y, w: 1.15, h: 0.22,
      fontSize: 9.5, fontFace: "Calibri", bold: true, color: item.color, align: "right", margin: 0,
    });
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y: 4.6, w: 9.35, h: 0.55,
    fill: { color: C.navy },
  });
  slide.addText("说明：六模式图用于展示整体分布；机制归因不依赖总排行榜，而回到四方案渐进叠加与 C/E/F 组件消融。", {
    x: 0.55, y: 4.6, w: 8.95, h: 0.55,
    fontSize: 11.5, fontFace: "Calibri", bold: true, color: C.white, valign: "middle",
  });
})();

// ============================================================
// SLIDE 14: KEY FINDINGS
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSlideTitle(slide, "主实验：四方案渐进叠加");
  addFooter(slide, 14, TOTAL_PAGES);

  slide.addChart(pres.charts.BAR, [
    { name: "D_baseline0", labels: ["相关性", "针对性", "方法合理性", "创新性", "深度"], values: [3.73, 3.00, 3.27, 2.47, 3.00] },
    { name: "A_template", labels: ["相关性", "针对性", "方法合理性", "创新性", "深度"], values: [3.93, 3.40, 3.33, 3.20, 2.67] },
    { name: "B_data_aware", labels: ["相关性", "针对性", "方法合理性", "创新性", "深度"], values: [4.07, 3.87, 3.40, 4.13, 3.13] },
    { name: "C_iterative", labels: ["相关性", "针对性", "方法合理性", "创新性", "深度"], values: [4.93, 4.73, 4.73, 4.73, 4.73] },
  ], {
    x: 0.3, y: 1.0, w: 5.75, h: 3.15,
    barDir: "col",
    chartColors: [C.subtext, C.gold, C.steel, C.teal],
    catAxisLabelColor: C.text,
    catAxisLabelFontSize: 10,
    valAxisLabelColor: C.subtext,
    valAxisLabelFontSize: 9,
    valGridLine: { color: C.stripe, size: 0.5 },
    catGridLine: { style: "none" },
    showLegend: true,
    legendPos: "b",
    legendFontSize: 9,
    valAxisMaxVal: 5.5,
    valAxisMinVal: 0,
    chartArea: { fill: { color: C.cardBg }, roundedCorners: true },
    barGapWidthPct: 80,
  });

  addCard(slide, 6.35, 1.0, 3.35, 2.0, { accentColor: C.teal });
  slide.addText("四方案总分（均值 ± 标准差）", {
    x: 6.58, y: 1.1, w: 2.9, h: 0.32,
    fontSize: 12.5, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });
  const mainScores = [
    { name: "C_iterative", score: "23.87 ± 1.77", color: C.teal },
    { name: "B_data_aware", score: "18.60 ± 2.82", color: C.steel },
    { name: "A_template", score: "16.53 ± 2.64", color: C.gold },
    { name: "D_baseline0", score: "15.47 ± 1.55", color: C.subtext },
  ];
  mainScores.forEach((s, i) => {
    const y = 1.5 + i * 0.33;
    slide.addText(s.name, {
      x: 6.58, y, w: 1.55, h: 0.2,
      fontSize: 9.5, fontFace: "Calibri", color: C.text, margin: 0,
    });
    slide.addText(s.score, {
      x: 8.05, y, w: 1.3, h: 0.2,
      fontSize: 9.5, fontFace: "Calibri", bold: true, color: s.color, align: "right", margin: 0,
    });
  });

  const qRows = [
    [
      { text: "问题", options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 9, fontFace: "Calibri", align: "center" } },
      { text: "D", options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 9, fontFace: "Calibri", align: "center" } },
      { text: "A", options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 9, fontFace: "Calibri", align: "center" } },
      { text: "B", options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 9, fontFace: "Calibri", align: "center" } },
      { text: "C", options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 9, fontFace: "Calibri", align: "center" } },
    ],
    [
      { text: "影响力", options: { fontSize: 9, fontFace: "Calibri", align: "center" } },
      { text: "16.2", options: { fontSize: 9, fontFace: "Calibri", align: "center" } },
      { text: "17.0", options: { fontSize: 9, fontFace: "Calibri", align: "center" } },
      { text: "19.6", options: { fontSize: 9, fontFace: "Calibri", align: "center" } },
      { text: "22.2", options: { fontSize: 9, fontFace: "Calibri", bold: true, color: C.teal, align: "center" } },
    ],
    [
      { text: "融合", options: { fontSize: 9, fontFace: "Calibri", align: "center", fill: { color: C.lightBg } } },
      { text: "15.2", options: { fontSize: 9, fontFace: "Calibri", align: "center", fill: { color: C.lightBg } } },
      { text: "16.8", options: { fontSize: 9, fontFace: "Calibri", align: "center", fill: { color: C.lightBg } } },
      { text: "17.4", options: { fontSize: 9, fontFace: "Calibri", align: "center", fill: { color: C.lightBg } } },
      { text: "24.6", options: { fontSize: 9, fontFace: "Calibri", align: "center", fill: { color: C.lightBg }, bold: true, color: C.teal } },
    ],
    [
      { text: "竞争", options: { fontSize: 9, fontFace: "Calibri", align: "center" } },
      { text: "15.0", options: { fontSize: 9, fontFace: "Calibri", align: "center" } },
      { text: "15.8", options: { fontSize: 9, fontFace: "Calibri", align: "center" } },
      { text: "18.8", options: { fontSize: 9, fontFace: "Calibri", align: "center" } },
      { text: "24.8", options: { fontSize: 9, fontFace: "Calibri", align: "center", bold: true, color: C.teal } },
    ],
  ];

  slide.addTable(qRows, {
    x: 6.58, y: 2.35, w: 2.8,
    colW: [1.0, 0.7, 0.7, 0.7, 0.7],
    rowH: [0.22, 0.22, 0.22, 0.22],
    border: { pt: 0.5, color: C.stripe },
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 4.55, w: 9.4, h: 0.58,
    fill: { color: C.navy },
  });
  slide.addText("主实验结论：C稳定最优，B稳定优于A/D；A与D差距有限，说明仅知识模板不足以稳定拉开性能差距。", {
    x: 0.5, y: 4.55, w: 9.0, h: 0.58,
    fontSize: 11.5, fontFace: "Calibri", bold: true, color: C.white, valign: "middle",
  });
})();

// ============================================================
// SLIDE 15: ABLATION RESULTS
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSlideTitle(slide, "组件消融：C / E / F");
  addFooter(slide, 15, TOTAL_PAGES);

  const ablationCards = [
    {
      name: "C_iterative", label: "完整系统",
      score: "23.87 ± 1.77", desc: "数据感知 + 知识图谱 + 两轮迭代", color: C.teal,
    },
    {
      name: "E_ablate_data", label: "移除数据感知",
      score: "22.07 ± 1.75", desc: "知识图谱 + 两轮迭代", color: C.orange,
    },
    {
      name: "F_ablate_kg", label: "移除知识图谱",
      score: "22.20 ± 3.26", desc: "数据感知 + 两轮迭代", color: C.steel,
    },
  ];

  ablationCards.forEach((c, i) => {
    const x = 0.35 + i * 3.15;
    addCard(slide, x, 1.0, 2.9, 1.55, { accentColor: c.color });
    slide.addText(c.name, {
      x: x + 0.18, y: 1.12, w: 2.5, h: 0.25,
      fontSize: 11, fontFace: "Calibri", bold: true, color: c.color, margin: 0,
    });
    slide.addText(c.label, {
      x: x + 0.18, y: 1.38, w: 2.5, h: 0.22,
      fontSize: 9.5, fontFace: "Calibri", color: C.subtext, margin: 0,
    });
    slide.addText(c.score, {
      x: x + 0.18, y: 1.72, w: 2.45, h: 0.28,
      fontSize: 16, fontFace: "Georgia", bold: true, color: c.color, align: "center", margin: 0,
    });
    slide.addText(c.desc, {
      x: x + 0.18, y: 2.05, w: 2.5, h: 0.25,
      fontSize: 8.5, fontFace: "Calibri", color: C.text, align: "center", margin: 0,
    });
  });

  addCard(slide, 0.35, 2.85, 4.6, 1.55, { accentColor: C.orange });
  slide.addText("数据感知的直接贡献", {
    x: 0.58, y: 2.98, w: 3.8, h: 0.28,
    fontSize: 12.5, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });
  slide.addText([
    { text: "C vs E：总分提升 1.80 分", options: { breakLine: true, color: C.text } },
    { text: "针对性引用数 14.2 → 3.0，降幅最明显", options: { breakLine: true, color: C.text } },
    { text: "说明 DataPreview/GraphPreview 直接决定方案是否围绕证据组织", options: { bold: true, color: C.teal } },
  ], {
    x: 0.58, y: 3.35, w: 4.0, h: 0.85,
    fontSize: 9.5, fontFace: "Calibri", paraSpaceAfter: 2,
  });

  addCard(slide, 5.1, 2.85, 4.6, 1.55, { accentColor: C.steel });
  slide.addText("知识图谱的任务依赖贡献", {
    x: 5.33, y: 2.98, w: 3.8, h: 0.28,
    fontSize: 12.5, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });
  slide.addText([
    { text: "Q1：F(24.6) > C(22.2)", options: { breakLine: true, color: C.text } },
    { text: "Q2：C(24.6) > F(21.4)；Q3：C(24.8) > F(20.6)", options: { breakLine: true, color: C.text } },
    { text: "平均上 C > F，但图谱收益强度随问题结构变化", options: { bold: true, color: C.teal } },
  ], {
    x: 5.33, y: 3.35, w: 4.0, h: 0.85,
    fontSize: 9.5, fontFace: "Calibri", paraSpaceAfter: 2,
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y: 4.6, w: 9.35, h: 0.55,
    fill: { color: C.navy },
  });
  slide.addText("消融结论：移除数据感知或知识图谱都会拉低平均表现；完整系统在平均意义上最优，但知识图谱收益具有明显任务依赖性。", {
    x: 0.55, y: 4.6, w: 8.95, h: 0.55,
    fontSize: 11.2, fontFace: "Calibri", bold: true, color: C.white, valign: "middle",
  });
})();

// ============================================================
// SLIDE 16: APPLICATION CASES
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSlideTitle(slide, "应用案例验证：三场景端到端分析");
  addFooter(slide, 16, TOTAL_PAGES);

  const cases = [
    {
      id: "Q1", title: "技术影响力\n驱动因素",
      round1: "多元回归检验\n技术跨界度→影响力",
      round2: "IPC共现特征+\n负二项回归+中介检验",
      tasks: "4", insight: "假设未支持→替代机制探索", color: C.teal,
    },
    {
      id: "Q2", title: "技术融合\n趋势识别",
      round1: "桥接IPC提取\n法律状态×融合度",
      round2: "层次回归+LDA主题\n识别5个融合簇",
      tasks: "6", insight: "宏观结构→微观融合簇", color: C.steel,
    },
    {
      id: "Q3", title: "国家竞争\n态势评估",
      round1: "质押专利中心性\n国家×技术分布",
      round2: "聚类+ANCOVA\n控制专利年龄",
      tasks: "5", insight: "国家对比→独立效应验证", color: C.navy,
    },
  ];

  cases.forEach((c, i) => {
    const x = 0.3 + i * 3.2;
    const y = 1.1;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.95, h: 3.4,
      fill: { color: C.cardBg },
      shadow: makeShadow(),
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.95, h: 0.7,
      fill: { color: c.color },
    });
    slide.addText(c.id, {
      x, y, w: 0.6, h: 0.7,
      fontSize: 20, fontFace: "Georgia", bold: true,
      color: C.white, align: "center", valign: "middle",
    });
    slide.addText(c.title, {
      x: x + 0.55, y, w: 2.3, h: 0.7,
      fontSize: 11, fontFace: "Calibri", bold: true,
      color: C.white, valign: "middle",
    });
    slide.addText("第一轮", {
      x: x + 0.1, y: y + 0.8, w: 1.2, h: 0.25,
      fontSize: 9, fontFace: "Calibri", bold: true, color: C.teal, margin: 0,
    });
    slide.addText(c.round1, {
      x: x + 0.1, y: y + 1.05, w: 2.7, h: 0.5,
      fontSize: 9, fontFace: "Calibri", color: C.text, margin: 0,
    });
    slide.addText("第二轮", {
      x: x + 0.1, y: y + 1.6, w: 1.2, h: 0.25,
      fontSize: 9, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
    });
    slide.addText(c.round2, {
      x: x + 0.1, y: y + 1.85, w: 2.7, h: 0.5,
      fontSize: 9, fontFace: "Calibri", color: C.text, margin: 0,
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.1, y: y + 2.4, w: 2.7, h: 0.01,
      fill: { color: C.stripe },
    });
    slide.addText(c.tasks, {
      x: x + 0.1, y: y + 2.5, w: 0.5, h: 0.4,
      fontSize: 20, fontFace: "Georgia", bold: true,
      color: c.color, align: "center", valign: "middle",
    });
    slide.addText("个任务\n100%成功", {
      x: x + 0.55, y: y + 2.5, w: 1.0, h: 0.4,
      fontSize: 8, fontFace: "Calibri", color: C.subtext, valign: "middle",
    });
    slide.addText(c.insight, {
      x: x + 0.1, y: y + 2.95, w: 2.7, h: 0.3,
      fontSize: 8, fontFace: "Calibri", italic: true,
      color: C.gold, margin: 0,
    });
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 4.7, w: 9.4, h: 0.55,
    fill: { color: C.navy },
  });
  slide.addText("案例页用于展示端到端执行链路；关于系统优劣与组件贡献的解释，以前述90组重复实验结论为准。", {
    x: 0.5, y: 4.7, w: 9.0, h: 0.55,
    fontSize: 11.5, fontFace: "Calibri", bold: true,
    color: C.white, valign: "middle",
  });
})();

// ============================================================
// SLIDE 17: CONTRIBUTIONS & FUTURE WORK
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };
  addSlideTitle(slide, "研究贡献与展望");
  addFooter(slide, 17, TOTAL_PAGES);

  // Left: Contributions
  addCard(slide, 0.3, 1.1, 4.8, 3.5, { accentColor: C.teal });
  slide.addText("三项研究贡献", {
    x: 0.55, y: 1.2, w: 4.3, h: 0.35,
    fontSize: 14, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });

  const contributions = [
    {
      label: "理论贡献", color: C.teal,
      text: "将关注点从\"执行正确性\"前移到\"规划合理性\"\n并刻画知识图谱收益的任务依赖边界",
    },
    {
      label: "方法贡献", color: C.steel,
      text: "可复用系统范式：数据感知 + 双图谱 + 迭代\n可迁移到其他结构化分析场景",
    },
    {
      label: "实践贡献", color: C.navy,
      text: "可落地工程资产：主流程代码、实验输出\n支持后续复验与扩展开发",
    },
  ];

  contributions.forEach((c, i) => {
    const y = 1.7 + i * 0.95;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.55, y, w: 1.2, h: 0.3,
      fill: { color: c.color },
    });
    slide.addText(c.label, {
      x: 0.55, y, w: 1.2, h: 0.3,
      fontSize: 10, fontFace: "Calibri", bold: true,
      color: C.white, align: "center", valign: "middle",
    });
    slide.addText(c.text, {
      x: 1.9, y, w: 3.0, h: 0.75,
      fontSize: 10, fontFace: "Calibri", color: C.text, margin: 0,
    });
  });

  // Right: Future Work
  addCard(slide, 5.4, 1.1, 4.3, 3.5, { accentColor: C.gold });
  slide.addText("后续研究方向", {
    x: 5.65, y: 1.2, w: 3.8, h: 0.35,
    fontSize: 14, fontFace: "Calibri", bold: true, color: C.navy, margin: 0,
  });

  const futures = [
    { num: "1", text: "统计稳健性增强\n在已有n=5基础上补bootstrap CI与显著性检验" },
    { num: "2", text: "混合评审框架\nLLM-as-Judge + 领域专家盲审" },
    { num: "3", text: "自适应约束强度\n基于数据信号强度动态调节图谱权重" },
    { num: "4", text: "广度-深度平衡\n最低覆盖率阈值 + 动态任务数校准" },
    { num: "5", text: "跨领域迁移验证\n生物医药 · 新能源 · 半导体" },
  ];

  futures.forEach((f, i) => {
    const y = 1.65 + i * 0.58;
    slide.addShape(pres.shapes.OVAL, {
      x: 5.65, y: y + 0.05, w: 0.28, h: 0.28,
      fill: { color: C.gold },
    });
    slide.addText(f.num, {
      x: 5.65, y: y + 0.05, w: 0.28, h: 0.28,
      fontSize: 9, fontFace: "Georgia", bold: true,
      color: C.white, align: "center", valign: "middle",
    });
    slide.addText(f.text, {
      x: 6.05, y: y, w: 3.4, h: 0.5,
      fontSize: 9, fontFace: "Calibri", color: C.text, margin: 0,
    });
  });

  // Bottom: core validation
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 4.8, w: 9.4, h: 0.5,
    fill: { color: C.navy },
  });
  slide.addText("核心命题验证：数据感知多智能体框架有效提升专利分析方案的质量与深度", {
    x: 0.5, y: 4.8, w: 9.0, h: 0.5,
    fontSize: 13, fontFace: "Calibri", bold: true,
    color: C.white, valign: "middle",
  });
})();

// ============================================================
// SLIDE 18: THANK YOU
// ============================================================
(() => {
  const slide = pres.addSlide();
  slide.background = { color: C.navy };

  // Top decorative bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.06,
    fill: { color: C.cyan },
  });

  // Decorative circles
  slide.addShape(pres.shapes.OVAL, {
    x: -1, y: -1.5, w: 4, h: 4,
    fill: { color: C.darkBlue, transparency: 50 },
  });
  slide.addShape(pres.shapes.OVAL, {
    x: 7, y: 3, w: 5, h: 5,
    fill: { color: C.steel, transparency: 70 },
  });

  // Thank you text
  slide.addText("感谢各位老师指导！", {
    x: 1, y: 1.5, w: 8, h: 1.2,
    fontSize: 36, fontFace: "Georgia", bold: true,
    color: C.white, align: "center", valign: "middle",
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 2.8, w: 3.0, h: 0.035,
    fill: { color: C.cyan },
  });

  slide.addText("敬请批评指正", {
    x: 1, y: 3.0, w: 8, h: 0.6,
    fontSize: 18, fontFace: "Calibri",
    color: C.lightText, align: "center", valign: "middle",
  });

  // Thesis info
  slide.addText("基于数据感知的多智能体专利分析系统设计与实现", {
    x: 1, y: 4.2, w: 8, h: 0.4,
    fontSize: 12, fontFace: "Calibri",
    color: C.lightText, align: "center",
  });

  // Bottom bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.425, w: 10, h: 0.2,
    fill: { color: C.teal, transparency: 40 },
  });
})();

// ============================================================
// WRITE FILE
// ============================================================
const outputPath = "C:\\Users\\73669\\Desktop\\专利分析\\patent_analysis\\docs\\thesis\\答辩PPT.pptx";
pres.writeFile({ fileName: outputPath })
  .then(() => console.log("PPT saved to: " + outputPath))
  .catch(err => console.error("Error:", err));
