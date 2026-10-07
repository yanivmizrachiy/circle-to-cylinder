/* ============================================================================
   גליל — מנוע רינדור יחיד (SSOT התנהגותי)
   ----------------------------------------------------------------------------
   כל עמוד מכיל אי-נתונים אחד: <script type="application/json" id="page">{...}</script>
   המנוע קורא אותו ובונה markup תקני אוטומטית. כללי ה-SSOT נאכפים כאן פעם אחת:
     • סמן משימה = נקודה כחולה (לעולם לא מספרים)   [כללי מספור]
     • כפל מוצג כ-·  ('×' / '\cdot' מומרים אוטומטית)  [כלל סימון כפל]
     • אזור פתרון = "תרגילים:" → רשת משבצות → משפט-השלמה עם יחידה
     • הסבר = "הסבירו:" → רשת משבצות
     • כותרת, מספר-עמוד (aria-label), פוטר — נוספים אוטומטית
   לעריכת תוכן בעתיד: פִתחו את page-N.html, שנו את ה-JSON. זהו.
   סוגי בלוקים נתמכים מפורטים בתחתית הקובץ וב-EDITING.md.
   ============================================================================ */
(function () {
  "use strict";

  /* ---- פוטר-קרדיט קבוע של המחוז (נוסח מחייב — אין לשנות מילה) ---- */
  const FOOTER =
    '<footer class="gz-footer">' +
    '<div class="f1">יניב רז - מדריך מחוזי חט"ב בעיר ירושלים</div>' +
    '<div class="f2">הדרכה במחוז ירושלים והעיר ירושלים - מנח"י, בהובלת איילת קריספין</div>' +
    '</footer>';

  /* ---- כלי-עזר לאכיפת SSOT ---- */
  const MULT = /×|∙/g;                         // תווי כפל יוניקוד → · (טקסט רגיל)
  function M(s) {                              // נירמול מתמטי (רשת-ביטחון)
    if (s == null) return "";
    s = String(s).replace(MULT, "·").replace(/\\times/g, "\\cdot"); // LaTeX: \times → \cdot (מתרנדר כ-·)
    if (/\bd\b/.test(s) && /קוטר|diameter/.test(s) === false && /[×·]|=|π/.test(s)) {
      // התרעה בלבד: סימון קוטר כ-d אסור; יש לכתוב "קוטר"
      console.warn("[SSOT] ייתכן סימון קוטר אסור 'd':", s);
    }
    return s;
  }
  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  // טקסט עם מתמטיקה: ממיר כפל, מכבד HTML גולמי מכוון (span dir=ltr וכו')
  const T = (s) => M(s);
  // המרת "___" (3+ קווים תחתונים) לשדה-השלמה (ברירת מחדל: בלוק משפטים)
  const fillBlanks = (s, cls) =>
    M(s).replace(/_{3,}/g, `<span class="${cls || "blank"}"></span>`);
  // השלמה בתוך שורה (הוראות/פסקאות): קו קצר אינליין
  const fillInline = (s) => M(s).replace(/_{3,}/g, '<span class="blankin"></span>');

  /* ---- בוני-בלוקים (כל אחד מחזיר מחרוזת HTML תקנית) ---- */
  const BLOCKS = {
    note: (b) => `<p class="note">${fillInline(b.text)}</p>`,

    // דוגמה פתורה: תווית "דוגמה" → נתון → צעדי פתרון → תשובה (לפני מיומנות חדשה)
    example: (b) => {
      const steps = (b.steps || []).map((s) => `<li>${T(s)}</li>`).join("");
      return `<div class="example">` +
        `<div class="example-lab">${T(b.lab || "דוגמה")}</div>` +
        (b.given ? `<div class="example-given">${T(b.given)}</div>` : "") +
        (steps ? `<ol class="example-steps">${steps}</ol>` : "") +
        (b.answer ? `<div class="example-answer">${T(b.answer)}</div>` : "") +
        `</div>`;
    },

    html: (b) => M(b.html),                    // פתח-מילוט: markup מדויק מותאם-אישית

    table: (b) => {
      const head = b.head ? `<tr>${b.head.map((h) => `<th>${T(h)}</th>`).join("")}</tr>` : "";
      const rows = (b.rows || []).map((r) =>
        `<tr>${r.map((c) => `<td>${c === "" ? "" : T(c)}</td>`).join("")}</tr>`).join("");
      return `<table class="classify-table">${head}${rows}</table>`;
    },

    bank: (b) =>
      `<div class="word-bank">${(b.words || []).map((w) =>
        b.plain ? `<span>${T(w)}</span>` : `<span class="word">${T(w)}</span>`)
        .join(b.plain ? ' <span class="sep">•</span> ' : "")}</div>`,

    fill: (b) =>
      `<div class="sentence-list">${(b.lines || []).map((l) =>
        `<div class="sentence">${fillBlanks(l)}</div>`).join("")}</div>`,

    // בחירה מרובה אופקית (גלולות). circle:true מוסיף תווית "הקיפו:"
    choice: (b) =>
      `<div class="choice-row${b.circle ? " mc-lead" : ""}">${(b.opts || []).map((o) =>
        `<span class="choice-pill"${/[A-Za-z=×·÷><πβ√]/.test(o) ? ' dir="ltr"' : ""}>${T(o)}</span>`)
        .join("")}</div>`,

    // רשימת טענות אנכית, כל אחת עם תיבת-סימון
    choices: (b) =>
      `<div class="choice-list">${(b.opts || []).map((o) =>
        `<div class="choice-row" style="justify-content:flex-start">${T(o)} <span class="mark-box"></span></div>`)
        .join("")}</div>`,

    // שרטוט יחיד (SVG מוכן, ללא מספרי מידה על הציור)
    fig: (b) =>
      `<div class="visual-card">${b.svg || ""}${b.cap ? `<div class="coord-caption">${T(b.cap)}</div>` : ""}</div>`,

    // שורת שרטוטים
    figrow: (b) =>
      `<div class="shape-grid"${b.cols ? ` style="grid-template-columns:repeat(${b.cols},1fr)"` : ""}>${
        (b.cards || []).map((c) =>
          `<div class="shape-card">${c.id ? `<div class="shape-id">${T(c.id)}</div>` : ""}${c.svg || ""}${
            c.cap ? `<div class="coord-caption">${T(c.cap)}</div>` : ""}</div>`).join("")}</div>`,

    // תיבת חשיבה (שרשראות קשרים וכו')
    think: (b) => `<div class="thinking">${M(b.html)}</div>`,

    // אזור פתרון תקני: "תרגילים:" → רשת משבצות → משפט-השלמה עם יחידה
    solve: (b) => {
      const lab = b.lab || "תרגילים:";
      const grid = `<div class="work-grid${b.grid ? " " + b.grid : ""}"></div>`;
      const sentence = b.sentence
        ? `<div class="answer-sentence">${M(b.sentence).replace(/_{2,}/g, '<span class="ansline"></span>')}</div>`
        : "";
      return `<div class="solve"><div class="solve-lab">${T(lab)}</div>${grid}${sentence}</div>`;
    },

    // הסבר: "הסבירו:" → רשת משבצות (ללא משפט-תשובה)
    explain: (b) =>
      `<div class="solve"><div class="solve-lab">${T(b.lab || "הסבירו:")}</div><div class="work-grid${
        b.grid ? " " + b.grid : ""}"></div></div>`,

    // פריסת עמודות (למשל שני תת-חלקים זה-לצד-זה)
    cols: (b) =>
      `<div style="display:grid;grid-template-columns:repeat(${b.n || 2},minmax(0,1fr));gap:4mm;align-items:start">${
        (b.cells || []).map((cell) => `<div>${renderBlocks(cell)}</div>`).join("")}</div>`,
  };

  function renderBlocks(blocks) {
    return (blocks || []).map((b) => (BLOCKS[b.t] || BLOCKS.note)(b)).join("\n");
  }

  function renderTask(tk) {
    const body = `${tk.q ? `<p class="instruction">${fillInline(tk.q)}</p>` : ""}${renderBlocks(tk.blocks)}`;
    return `<section class="task${tk.think ? " thinking" : ""}"><div class="task-row">` +
      `<span class="qmark"></span><div class="task-body">${body}</div></div></section>`;
  }

  function render(page) {
    const header =
      `<header class="page-header"><div>` +
      `<h1 class="page-title">${T(page.title)}</h1>` +
      `${page.sub ? `<div class="page-subtitle">${T(page.sub)}</div>` : ""}</div>` +
      `<div class="page-number" aria-label="עמוד ${page.n}">${page.n}</div></header>`;
    const anchor = page.anchor ? `<div class="anchor">${T(page.anchor)}</div>` : "";
    const example = page.example ? BLOCKS.example(page.example) : "";
    const tasks = (page.tasks || []).map(renderTask).join("\n");
    const main = document.createElement("main");
    main.className = "a4-page" + (page.tight ? " tight" : "");
    main.innerHTML = header + anchor + example + tasks + FOOTER;
    document.body.innerHTML = "";
    document.body.appendChild(main);
    document.title = (page.title || "גליל").replace(/<[^>]+>/g, "");

    // MathJax רק אם העמוד משתמש ב-\( ... \)
    if (/\\\(/.test(main.innerHTML) && !window.MathJax) {
      window.MathJax = { tex: { inlineMath: [["\\(", "\\)"]] } };
      const s = document.createElement("script");
      s.src = "vendor/mathjax/tex-mml-chtml.js"; s.async = true; s.id = "MathJax-script";
      document.head.appendChild(s);
    }
  }

  /* ---- איתחול: קריאת אי-הנתונים והרנדור ---- */
  function boot() {
    const el = document.getElementById("page");
    if (!el) { console.error("[galil] חסר <script id=page>"); return; }
    let data;
    try { data = JSON.parse(el.textContent); }
    catch (e) { console.error("[galil] JSON שגוי בעמוד:", e); return; }
    render(data);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  // חשיפה לשימוש המציג (index/preview) — רינדור עמוד לתוך אלמנט נתון
  window.GALIL = {
    renderInto(mount, page) {
      const html = (function () {
        const prev = document.body; // reuse builders via a detached container
        return page;
      })();
      const tmp = document.createElement("div");
      const header =
        `<header class="page-header"><div><h1 class="page-title">${T(page.title)}</h1>` +
        `${page.sub ? `<div class="page-subtitle">${T(page.sub)}</div>` : ""}</div>` +
        `<div class="page-number" aria-label="עמוד ${page.n}">${page.n}</div></header>`;
      const anchor = page.anchor ? `<div class="anchor">${T(page.anchor)}</div>` : "";
      const example = page.example ? BLOCKS.example(page.example) : "";
      const tasks = (page.tasks || []).map(renderTask).join("\n");
      tmp.className = "a4-page" + (page.tight ? " tight" : "");
      tmp.innerHTML = header + anchor + example + tasks + FOOTER;
      mount.appendChild(tmp);
      return tmp;
    },
    _M: M,
  };
})();

/* ----------------------------------------------------------------------------
   אוצר סוגי-בלוקים (t):
     note    {text}                               פסקה חופשית
     example {lab?, given?, steps:[...], answer?}  דוגמה פתורה (לפני מיומנות חדשה)
     html    {html}                                markup גולמי מדויק (פתח-מילוט)
     table   {head:[...], rows:[[...]]}            טבלה; תא "" = ריק להשלמה
     bank    {words:[...], plain?}                 מחסן מילים/קשרים
     fill    {lines:["A הוא ___."]}                משפטי השלמה ("___" → שדה)
     choice  {opts:[...], circle?}                 בחירה אופקית (גלולות)
     choices {opts:[...]}                          רשימת טענות אנכית עם תיבת-סימון
     fig     {svg, cap?}                            שרטוט יחיד
     figrow  {cols?, cards:[{svg,id?,cap?}]}        שורת שרטוטים
     think   {html}                                תיבת חשיבה
     solve   {lab?, sentence?, grid?:'sm'|'lg'}     "תרגילים:"+משבצות+משפט ("__"→קו)
     explain {lab?, grid?}                          "הסבירו:"+משבצות
     cols    {n?, cells:[[block...],[block...]]}    פריסת עמודות
   ---------------------------------------------------------------------------- */
