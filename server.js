import express from 'express';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

const maagalDir = path.join(__dirname, 'maagal');
const galilDir = path.join(__dirname, 'galil');
const manifestPath = path.join(maagalDir, 'manifest.json');

let manifestMtime = 0;
let manifest = null;

function getManifest() {
  if (!fs.existsSync(manifestPath)) return null;
  const stat = fs.statSync(manifestPath);
  if (!manifest || stat.mtimeMs !== manifestMtime) {
    manifestMtime = stat.mtimeMs;
    manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  }
  return manifest;
}

// Function to resolve metadata and source file for any page 1..138
function getPageMeta(seq) {
  const m = getManifest();
  if (seq >= 1 && seq <= 99 && m) {
    const segment = m.segments.find((s) => seq >= s.from && seq <= s.to);
    let srcFile = '';
    let kind = segment ? segment.kind : '';
    if (segment) {
      if (segment.kind === 'original') {
        srcFile = `maagal/source/original-88/page-${segment.sourceStart + (seq - segment.from)}.html`;
      } else if (segment.kind === 'targilim') {
        srcFile = `maagal/source/targilim/${segment.source}.html`;
      } else if (segment.kind === 'bbb' || segment.kind === 'bbb-fragment') {
        srcFile = `maagal/source/bbb/עמוד-${segment.sourceStart + (seq - segment.from)}.html`;
      }
    }
    const stage = (m.stages || []).find((st) => seq >= st.from && seq <= st.to);
    return {
      sequence: seq,
      booklet: 'maagal',
      bookletTitle: 'מעגל',
      pageInBooklet: seq,
      totalPagesInBooklet: 99,
      chapter: stage ? stage.title : '',
      sourceFile: srcFile,
      kind: kind
    };
  } else if (seq >= 100 && seq <= 138) {
    const galilPage = seq - 99;
    let ch = 'מושגים בסיסיים והכרת הגוף';
    if (galilPage > 10 && galilPage <= 24) ch = 'פריסה, מעטפת ושטח פנים';
    else if (galilPage > 24) ch = 'נפח ובעיות מורכבות';
    return {
      sequence: seq,
      booklet: 'galil',
      bookletTitle: 'גליל',
      pageInBooklet: galilPage,
      totalPagesInBooklet: 39,
      chapter: ch,
      sourceFile: `galil/page-${galilPage}.html`,
      kind: 'galil-json'
    };
  }
  return null;
}

// Dynamic mtime-based memory cache (never stale; instant updates on disk changes!)
const pageCache = new Map();

function getCompiledMaagalPage(seq) {
  const meta = getPageMeta(seq);
  if (!meta || !meta.sourceFile) return null;
  const fullPath = path.join(__dirname, meta.sourceFile);
  if (!fs.existsSync(fullPath)) return null;

  const stat = fs.statSync(fullPath);
  const cached = pageCache.get(seq);
  if (cached && cached.mtime === stat.mtimeMs) {
    return cached.html;
  }

  let html = fs.readFileSync(fullPath, 'utf8');
  html = html.replace(/<div class="page-number"[^>]*>.*?<\/div>/, `<div class="page-number" aria-label="עמוד ${seq}">${seq}</div>`);
  html = html.replace(/<title>.*?<\/title>/, `<title>חוברת המעגל — עמוד ${seq}</title>`);
  if (meta.kind === 'bbb' || meta.kind === 'bbb-fragment') {
    html = html.replace(/pages\/bbb\/geometry8\/assets\//g, 'source/bbb/assets/');
  }

  pageCache.set(seq, { mtime: stat.mtimeMs, html });
  return html;
}

// REST API for developer inspection & easy editing navigation
app.get('/api/pages', (req, res) => {
  const list = [];
  for (let i = 1; i <= 138; i++) {
    list.push(getPageMeta(i));
  }
  res.json(list);
});

app.get('/api/page/:n', (req, res) => {
  const n = parseInt(req.params.n, 10);
  const meta = getPageMeta(n);
  if (!meta) return res.status(404).json({ error: 'Page not found' });
  res.json(meta);
});

// Dynamic fast route for maagal pages with mtime hot-reloading
app.get('/maagal/page-:n.html', (req, res, next) => {
  const n = parseInt(req.params.n, 10);
  const html = getCompiledMaagalPage(n);
  if (html) {
    res.setHeader('Content-Type', 'text/html; charset=UTF-8');
    res.setHeader('Cache-Control', 'no-cache');
    return res.send(html);
  }
  next();
});

// Serve static assets from project root
app.use(express.static(__dirname));

// Fallback to index.html for root or SPA navigation
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server listening on http://0.0.0.0:${PORT}`);
});
