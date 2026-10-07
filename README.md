# circle-to-cylinder — חוברת עבודה במתמטיקה (מעגל → גליל → חרוט)

חוברת A4 בעברית (RTL), **אתר סטטי** ב-GitHub Pages.

> מקור-האמת היחיד והמחייב: **[RULES.md](RULES.md)** — קראו אותו ראשון.

## מבנה
- `index.html` — מציג את כל החוברת ברצף (iframes, A4, התאמה לרוחב).
- `maagal/` — מעגל, 99 עמ׳ (loader + `manifest.json` → `source/`).
- `gold/` — עמודי הזהב בעיצוב הקנוני: גליל 1–7 + חרוט (8) + `styles.css`.
- `galil/` — גליל-legacy, 39 עמ׳ (data-driven, `render.js` + JSON).
- `.nojekyll` — הגשה סטטית.

סדר בחוברת: מעגל 1–99 · גליל-זהב 100–106 · גליל-legacy 107–145 · חרוט-זהב 146.

אתר חי: https://yanivmizrachiy.github.io/circle-to-cylinder/
