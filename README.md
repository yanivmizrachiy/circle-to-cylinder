<div dir="rtl">

# circle-to-cylinder · מעגל → גליל

חוברת עבודה מתמטית מדורגת בעברית (RTL, A4 להדפסה), שמובילה את התלמיד **מהמעגל אל הגליל** — מהיסודות ועד נפח ושטח פנים.
שתי חוברות, רצף הוראה אחד, ועיצוב אחיד.

| חוברת | נושא | עמודים | מנוע |
|---|---|---|---|
| **[maagal/](maagal/)** | מעגל ועיגול — יסודות, היקף, שטח, מערכת צירים | 99 | loader + `manifest.json` → `source/` |
| **[galil/](galil/)** | גליל — נפח, שטח פנים, מעבר מהמעגל | 39 | data-driven (`render.js` + JSON לכל עמוד) |

## 🎯 מקור אמת יחיד (SSOT)

**[`RULES.md`](RULES.md)** הוא המקור המחייב היחיד — כל כללי התוכן, העיצוב, המתמטיקה והמבנה.
כל עריכה עתידית **נקראת ממנו ומאומתת מולו** לפני "בוצע". אין כלל שחי רק בראש — הכול כתוב שם.

## 📁 מבנה

```
circle-to-cylinder/
├── RULES.md            ← מקור האמת היחיד (SSOT)
├── README.md           ← הקובץ הזה
├── maagal/             ← חוברת המעגל (99 עמ')
│   ├── index.html         מציג
│   ├── page-1..99.html    טוענים תוכן מ-source/ לפי manifest.json
│   ├── manifest.json      הסדר המדורג + designRules
│   ├── styles.css         טוקני עיצוב אחידים
│   └── source/            התוכן בפועל (bbb רשמי, original-88, targilim)
├── galil/              ← חוברת הגליל (39 עמ')
│   ├── index.html
│   ├── page-1..39.html    לכל עמוד אי-נתונים JSON יחיד
│   ├── render.js          מנוע רינדור משותף
│   └── styles.css
└── tools/              ← כלי בנייה ואימות
    ├── build.py           בונה PDF מאוחד (ללא שערים) → dist/
    ├── verify_maagal.py   אימות תאימות + A4 לכל 99 העמודים
    └── verify_galil.py    אימות תאימות + A4 לכל 39 העמודים
```

## 👁️ תצוגה מקדימה

```bash
# מעגל
python -m http.server 8411 --directory maagal
# גליל
python -m http.server 8412 --directory galil
```
ואז לפתוח `http://localhost:8411/page-1.html` / `http://localhost:8412/page-1.html`.
להדפסה: לפתוח עמוד ולהדפיס ב-A4, שוליים 0.

## 📦 בניית ה-PDF המאוחד

```bash
PYTHONIOENCODING=utf-8 python tools/build.py      # → dist/circle-to-cylinder.pdf (138 עמ', ללא שערים)
```

## ✅ אימות תאימות (מול RULES.md)

```bash
PYTHONIOENCODING=utf-8 python tools/verify_maagal.py
PYTHONIOENCODING=utf-8 python tools/verify_galil.py
```
בודק לכל עמוד: התאמה ל-A4 (ללא חריגה/גלילה), אין נקודת-כפל `·`, אין מספור-שאלות, נקודות כחולות קיימות, אין מידות על שרטוטים, פוטר מחוזי.

**דרישות:** Python 3, `playwright` (עם Chrome/Chromium) ו-`pypdf`.

---

<sub>יניב רז — מדריך מחוזי חט״ב, מנח״י, ירושלים. התוכן הרשמי (bbb) נשמר כפי שהוא; רק המיקום והעיצוב סביבו אוחדו. פירוט מקורות: `maagal/PROVENANCE.md`, `galil/PROVENANCE.md`.</sub>

</div>
