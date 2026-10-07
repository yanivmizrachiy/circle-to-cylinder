# Provenance — maagal (circle workbook)

Extracted 2026-09-23. Pedagogical content is byte-identical to the sources below; only the path changes listed under **Transforms** were made.

| Target | Source |
|---|---|
| `/` (index.html, manifest.json, page-1..100.html, styles.css, source/**) | `yanivmizrachiy/razpages@c8fe7bde7ee19215b5593f9379c3db2f0c846538:workbooks/circle/` |
| `vendor/mathjax/`, `vendor/fonts/` | `yanivmizrachiy/razpages@c8fe7bde7ee19215b5593f9379c3db2f0c846538:vendor/` |
| `styles/a4-base.css`, `styles/pages/עמוד-196..205.css`, `styles/topics/bbb-geometry8.css` | `yanivmizrachiy/razpages@c8fe7bde7ee19215b5593f9379c3db2f0c846538:styles/` |

Canonical choice: razpages `workbooks/circle/manifest.json` declares `sourceOfTruth: true`, 101 pages (consolidated 2026-08-18, commit 38ae6b3). Its `source/original-88/` is byte-identical to `smartschool-hebrew-voice-notes@760f64e82dc6f309c67324df100399532f89bc8f:circle/page-*.html`.

## Transforms
- `page-*.html` (loader shell): `'../../'+v` → `v` — BBB pages' `vendor/` and `styles/` now resolve inside this repo.
- `index.html`: link "כל החוברות" `../index.html` → https://yanivmizrachiy.github.io/razpages/workbooks/index.html
- Not carried: `qa.mjs` / `scripts/qa-circle-canonical.mjs` (checks razpages-only files such as CLAUDE.md and workbooks/manifest.json).

> **Reorder note (2026-10-05, later this day).** After the two passes below were written,
> the workbook was reordered so the enrichment/BBB section leads (SSOT: `manifest.json`
> `stages`/`segments`, which is authoritative for page numbers). The BBB pages
> `source/bbb/עמוד-196..205.html` now serve **maagal pages 1–10** (was 74–83):
> 196→1, 197→2, … 204→9, 205→10 (עמוד-205 = page 10, `bbb-fragment`). Sub-chapters:
> א "המעגל וחלקיו" = pages 1–2, ב "היקף מעגל ושטחו" = pages 3–10. Consequently the
> "three congruent squares" fix is on page 5 (עמוד-200); the fountain park on pages 9–10
> (עמוד-204/205); London Eye on page 8 (עמוד-203). Original/targilim page numbers in the
> sections below also shifted (original `page-1..88` now live in the 11–101 range). Any
> specific maagal page number quoted below is **pre-reorder**; resolve current numbers via
> `manifest.json`. The "known overflow" list near the end is likewise pre-reorder.

## Circle-improvement pass (branch `improve-circle-work`, 2026-10-05)

### "שאלות מתוך תוכנית הלימודים" — real BBB questions (pages 74–83)
Every question below is the **actual** question from BBB (`geometry8/topics/t01_circle.py`,
commit `ad12425c6b2e1d4dac84030a5cd865c2b03d3804`), rendered byte-for-byte into
`source/bbb/עמוד-196..205.html` and served at maagal pages 74–83. No question here was
invented, rewritten, or "inspired by" — only the minimal corrections listed afterwards.
All ten sit under the single chapter heading **"שאלות מתוך תוכנית הלימודים"**
(SSOT: `manifest.json` stage `enrichment`, pages 74–83), split into the source's own
sub-chapters: א "המעגל וחלקיו" (74–75) and ב "היקף מעגל ושטחו" (76–83).

| maagal page | source file | BBB question (identifying text) |
|---|---|---|
| 74 | `source/bbb/עמוד-196.html` | חוט/יתד/עיפרון — הגדרת המעגל כאוסף הנקודות במרחק קבוע; + מעגל r=5 במערכת צירים |
| 75 | `source/bbb/עמוד-197.html` | נתון קוטר → מהו אורך הרדיוס ומהם שיעורי מרכז המעגל |
| 76 | `source/bbb/עמוד-198.html` | תומר מדד רדיוס גלגל 30 ס״מ → חשבו היקף (π≈3.14) |
| 77 | `source/bbb/עמוד-199.html` | משושה משוכלל חסום במעגל — זוויות המשולשים והיקף המשושה |
| 78 | `source/bbb/עמוד-200.html` | אצטדיון (ריבוע 144 מ״ר + שני חצאי עיגול); שלושה ריבועים חופפים עם עיגולים משיקים |
| 79 | `source/bbb/עמוד-201.html` | ריבוע ABCD עם עיגול חסום (r=6) — היקף ריבוע ויחס שטחים |
| 80 | `source/bbb/עמוד-202.html` | מלבן + חצאי/רבעי עיגול — השוואת היקפים ושטחים של שתי צורות |
| 81 | `source/bbb/עמוד-203.html` | הגלגל הענק (London Eye) — גובה מרכז M מעל המים והיקף הגלגל |
| 82 | `source/bbb/עמוד-204.html` | פארק המזרקה — חלקים 1–3 (שטח בריכה, שטח טיילת כהפרש עיגולים) |
| 83 | `source/bbb/עמוד-205.html` | פארק המזרקה — חלקים 4–5 (הכפלת רדיוס ויחסי שטחים; אתגר תקציב −30%) |

### Minimal corrections to the BBB pages (content essence preserved)
- **Heading** (all 10 `source/bbb/עמוד-196..205.html`): page-title `גאומטריה לכיתה ח'` → `שאלות מתוך תוכנית הלימודים`.
- **עמוד-200.html (page 78)** — math fix: the "three congruent squares" multiple-choice had **no correct option** (the grey area is `π·s²/4` in all three figures, i.e. equal). Added the missing correct option **"בכל האיורים השטח שווה"**. Verified no A4 clipping after the addition.
- **עמוד-204.html / עמוד-205.html (pages 82–83)**: the fountain-park task is one problem split across two A4 pages; its part labels were renumbered to be continuous and self-consistent (`6,7,8` → `1,2,3` on p82; `9,10` → `4,5` on p83). The "גליל וחרוט" chapter-bar on עמוד-205 is kept (the loader uses it as the page-83 trim boundary) but its cylinder/cone questions are **not** served — page 83 carries circle content only (verified: no גליל/חרוט text leaks).

### Canonical language (SSOT) + wording consistency
- Added `canonicalLanguage` to `manifest.json` (the SSOT) with the four required statements:
  כל קוטר הוא מיתר אך לא כל מיתר הוא קוטר · אורך רדיוס הוא אורך חצי קוטר ·
  מרכז המעגל נמצא תמיד באמצע כל קוטר · קוטר הוא המיתר הארוך ביותר במעגל.
- `source/original-88/page-4.html` (page 4 "קוטר"): added a compact "הדגשה" note carrying the four statements verbatim. Page re-verified: no A4 overflow, all four present.
- Page-wording audit against the four statements (pages mentioning מיתר/רדיוס/קוטר: 3, 4, 8, 10, 21/g8-06): all already consistent — no contradictions, no edits needed.

### Other circle corrections
- `source/original-88/page-50.html` (page 53) & `page-51.html` (page 54): fixed regex artifact `r=x−$1` → `r=x−1`.
- `source/targilim/g8-06.html` (page 21): moved the chord segment endpoints onto the circle (center (130,88), r=55) so the "מיתר" is drawn correctly.
- `source/targilim/g8-01.html` (page 43): title `עיגול — …` → `מעגל ועיגול — …` for precision.

### Mobile (viewer) — `index.html`
- Added a phone-width fit (`@media(max-width:760px)`): the viewer measures the real `.a4-page` inside the iframe and scales it to the pane width (absolute `left:0` + `transform-origin:top left`), so the full A4 page is visible with **no horizontal scroll**, on both CSS systems (original `styles.css` and `styles/a4-base.css`). Desktop and print are untouched (fit resets above 760px).

## Uniform design pass (branch `improve-circle-work`, 2026-10-05)

Per the teacher's direction, a set of uniform design rules was recorded in the SSOT
(`manifest.json` → `designRules`) and enforced through the two shared stylesheets so the
rules apply across the whole workbook without per-page churn:

- **No question frames** — bbb `.q` card border removed; original `.coord-card`/`.puzzle-card`
  de-framed (concept/highlight boxes `.anchor`/`.thinking` kept).
- **No question numbering → bullet at the start (right in RTL)** — bbb `.qdot` floated to the
  right of the text; original `.task-num` rendered as a blue dot; numbered sub-parts of the
  fountain task (`source/bbb/עמוד-204/205.html`, parts 1–5) switched to `.plab.pdot` dots.
  Hebrew-letter sub-parts (א/ב/ג) and multiple-choice option labels kept.
- **Work-then-answer** — dark-blue full-width writing lines (`#1e3a8a`); a `תרגיל:` work area +
  answer line added on the single-compute questions (pages 76, 81).
- **No data on figure lines** — measurement labels removed from every bbb figure (bike r=30;
  circle r=5; square side 12 / area 144 מ"ר; hexagon r=1; square r=6). Given values live in the
  question text, with units (e.g. "מלבן שאורכו 20 ס\"מ ורוחבו 12 ס\"מ"). Coordinate-axis ticks and
  essential point coordinates (e.g. A(−3,0)) are kept — they are the problem data, not annotations.
- **Lighter type** — removed unnecessary bold on instructions/labels in both systems.
- **Vector graphics** — the two raster images on the circle pages replaced with clean SVG: the
  London Eye wheel (`עמוד-203.html`) and the fountain ring (`עמוד-204.html`).
- **Demo leftovers removed from source** — the `preview-nav` block and the demo `<title>` were
  stripped from all ten `source/bbb/עמוד-196..205.html` (the loader already hid them at render).
- **Uniform header** — big workbook name **"מעגל"** with the section caption
  **"שאלות מתוך תוכנית הלימודים"** beneath it, on pages 74–83.

Verified in a real browser (built-in Chromium) on pages 74–84 + 4: no console errors, no A4
overflow introduced, RTL intact, loader still sets the correct page number/title.

## Deep-clean + layout pass (branch `improve-circle-work`, 2026-10-05, later)

Teacher report: the bottom-of-page line "broke" on several pages. Root cause found and removed:
a **stale A4-utilization layer** keyed to an obsolete page numbering, which applied `!important`
font/spacing bumps (and a 20–40mm "work-space" box) to the **wrong** pages after the pages were
reordered and pages 2+3 were merged — inflating already-full pages so content spilled over the
single bottom rule.

- **Merged pages 2+3** → workbook is now **100 pages** (`manifest.json` `pageCount` 101→100;
  `segments`/`stages` updated; `source/bbb/עמוד-198.html` content folded into `עמוד-197.html`).
- **Removed the stale utilization layer** (deep clean): deleted `a4-utilization.css` and its
  `@import`, and removed the `--a4-work-extra` / `.task-body::after` "work-space" injection from
  `styles.css`. These were measurement-specific hacks tied to dead page numbers.
- **Overflow after removal:** a full 100-page browser sweep (built-in Chromium) dropped from
  **22 overflowing pages → 3** (59, 86, 90). Those three were fixed with a small, correctly
  **final-sequence-keyed** block in `styles.css` (font/figure/spacing trims). Re-sweep: **0/100
  pages overflow**; every page's single dark-blue bottom rule (`#1e3a8a`) now sits clear of the
  content, on both CSS systems.
- **Orphans deleted:** `source/bbb/עמוד-198.html` + `styles/pages/עמוד-198.css` (merged away) and
  the out-of-range loader `page-101.html`.

> The pre-reorder "known overflow" list that used to live here is superseded by this pass
> (full sweep = 0 overflow). Page numbers above are the current SSOT (`manifest.json`) sequence.
