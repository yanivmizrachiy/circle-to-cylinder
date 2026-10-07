import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;
const HOST = '0.0.0.0';

const manifestPath = path.join(__dirname, 'maagal', 'manifest.json');
let maagalManifest = null;
try {
  maagalManifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
} catch (e) {
  console.error('Failed to load maagal manifest', e);
}

app.use((req, res, next) => {
  const line = `${new Date().toISOString()} ${req.method} ${req.url}\n`;
  fs.appendFileSync('/tmp/server.log', line);
  console.log(line.trim());
  next();
});

// Serve rendered maagal pages directly without client-side DOM replacement
app.get('/maagal/page-:n.html', (req, res, next) => {
  const seq = parseInt(req.params.n, 10);
  if (isNaN(seq) || seq < 1 || seq > 99 || !maagalManifest) {
    return next();
  }
  const segment = maagalManifest.segments.find(s => seq >= s.from && seq <= s.to);
  if (!segment) return next();
  let source;
  if (segment.kind === 'original') {
    const n = segment.sourceStart + (seq - segment.from);
    source = `source/original-88/page-${n}.html`;
  } else if (segment.kind === 'targilim') {
    source = `source/targilim/${segment.source}.html`;
  } else if (segment.kind === 'bbb' || segment.kind === 'bbb-fragment') {
    const n = segment.sourceStart + (seq - segment.from);
    source = `source/bbb/עמוד-${n}.html`;
  }
  const sourcePath = path.join(__dirname, 'maagal', source);
  if (!fs.existsSync(sourcePath)) return next();
  let html = fs.readFileSync(sourcePath, 'utf8');
  // Normalize multiplication to middle dot
  html = html.replace(/×/g, '·');
  html = html.replace(/<div class="page-number"[^>]*>[^<]*<\/div>/, `<div class="page-number" aria-label="עמוד ${seq}">${seq}</div>`);
  if (segment.kind === 'bbb' || segment.kind === 'bbb-fragment') {
    html = html.replace(/href="vendor\//g, 'href="vendor/');
    html = html.replace(/src="pages\/bbb\/geometry8\/assets\//g, 'src="source/bbb/assets/');
    if (segment.kind === 'bbb-fragment') {
      const marker = '<div class="chapter-bar">';
      const idx = html.indexOf(marker);
      if (idx !== -1) {
        const footerMarker = '<footer class="gz-footer">';
        const footerIdx = html.indexOf(footerMarker);
        if (footerIdx !== -1) {
          html = html.slice(0, idx) + '</div>\n    ' + html.slice(footerIdx);
        }
      }
    }
  }
  res.setHeader('Content-Type', 'text/html; charset=UTF-8');
  res.send(html);
});

// Serve static assets from project root
app.use(express.static(__dirname, {
  extensions: ['html'],
  index: 'index.html'
}));

// Fallback to index.html for any navigation routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, HOST, () => {
  console.log(`Server listening at http://${HOST}:${PORT}`);
});
