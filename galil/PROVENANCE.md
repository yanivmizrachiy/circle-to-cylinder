# Provenance — galil (cylinder workbook)

Historical extraction recorded on 2026-09-23. This file documents where the imported legacy material came from; it does **not** define the current publication order or QA commands.

| Historical target | Source |
|---|---|
| `index.html`, `page-1..38.html`, historical `qa.mjs` | `yanivmizrachiy/razpages@c8fe7bde7ee19215b5593f9379c3db2f0c846538:workbooks/cylinder/` — includes local-MathJax fixes on pages 11–14 (2026-08-19: 579bae9, 4620e54, c2e0106, df1b40b) |
| `styles.css` | `yanivmizrachiy/smartschool-hebrew-voice-notes@760f64e82dc6f309c67324df100399532f89bc8f:cylinder/styles.css` — A4 utilization (2026-08-24, 29d7c6c6a850d27a35d91b93db8d34e5b106d6a5) |
| `vendor/mathjax/` | `yanivmizrachiy/razpages@c8fe7bde7ee19215b5593f9379c3db2f0c846538:vendor/mathjax/` |

The historical snapshot covered pages 1–38. The current repository also contains `page-39.html`; current publication order is owned only by `../content-manifest.json`.

## Historical transforms
- `page-*.html`: `../../vendor/mathjax/` → `vendor/mathjax/`
- historical `index.html`: link "כל החוברות" `../index.html` → https://yanivmizrachiy.github.io/razpages/workbooks/index.html
- historical `qa.mjs`: normalized TeX (`\(\pi\)`, `\approx`) before π notation checks.

## Current authority
- Publication order: `../content-manifest.json`
- Project policy: `../RULES.md`
- Active QA: `../scripts/` + `../.github/workflows/content-integrity.yml`
- The historical `qa.mjs` is not an active QA command in this canonical repository.
