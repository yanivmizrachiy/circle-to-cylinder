# Provenance — galil (cylinder workbook)

Extracted 2026-09-23. The two copies had diverged on disjoint files; both change sets are included.

| Target | Source |
|---|---|
| `index.html`, `page-1..38.html`, `qa.mjs` | `yanivmizrachiy/razpages@c8fe7bde7ee19215b5593f9379c3db2f0c846538:workbooks/cylinder/` — includes local-MathJax fixes on pages 11–14 (2026-08-19: 579bae9, 4620e54, c2e0106, df1b40b) |
| `styles.css` | `yanivmizrachiy/smartschool-hebrew-voice-notes@760f64e82dc6f309c67324df100399532f89bc8f:cylinder/styles.css` — A4 utilization (2026-08-24, 29d7c6c6a850d27a35d91b93db8d34e5b106d6a5) |
| `vendor/mathjax/` | `yanivmizrachiy/razpages@c8fe7bde7ee19215b5593f9379c3db2f0c846538:vendor/mathjax/` |

Pages 1–10 and 15–38 are identical in both sources.

## Transforms
- `page-*.html`: `../../vendor/mathjax/` → `vendor/mathjax/`
- `index.html`: link "כל החוברות" `../index.html` → https://yanivmizrachiy.github.io/razpages/workbooks/index.html
- `qa.mjs`: normalizes TeX (`\(\pi\)`, `\approx`) before the π notation checks. The QA predates the MathJax fix and failed on razpages main; page content is unchanged.
