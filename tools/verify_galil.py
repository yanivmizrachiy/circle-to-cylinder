#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render all galil pages in Chrome and verify SSOT compliance + A4 fit.
Run with: PYTHONIOENCODING=utf-8 python verify_galil.py"""
import threading, functools, json, os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

G = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "galil")
PORT = 8240
N = 39

h = functools.partial(SimpleHTTPRequestHandler, directory=G)
srv = ThreadingHTTPServer(("127.0.0.1", PORT), h)
threading.Thread(target=srv.serve_forever, daemon=True).start()

CHECK_JS = r"""
() => {
  const a = document.querySelector('.a4-page');
  if (!a) return {broken:true};
  const html = a.innerHTML;
  const txt = a.innerText || '';
  // dimension numbers left on SVG figures: <text> inside <svg> containing a digit followed by unit
  let svgDimText = 0;
  a.querySelectorAll('svg text').forEach(t => {
    const s = (t.textContent||'').trim();
    if (/\d/.test(s) && /ס|מ"|cm|ס\u05f4מ/.test(s)) svgDimText++;
  });
  return {
    broken:false,
    empty: txt.trim().length < 10,
    sh: a.scrollHeight, ch: a.clientHeight,
    mid: (html.match(/\u00b7/g)||[]).length,          // ·
    mid2: (html.match(/\u2219/g)||[]).length,          // ∙
    cdot: (html.match(/\\cdot/g)||[]).length,
    tasknum: (html.match(/task-num/g)||[]).length,
    qmark: (html.match(/qmark/g)||[]).length,
    svgDimText: svgDimText,
    hasHeader: !!document.querySelector('.page-header'),
  };
}
"""

rows = []
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page(); pg.set_viewport_size({"width":900,"height":1300})
    for n in range(1, N+1):
        try:
            pg.goto(f"http://127.0.0.1:{PORT}/page-{n}.html", wait_until="networkidle", timeout=30000)
            pg.wait_for_timeout(350)
            r = pg.evaluate(CHECK_JS)
        except Exception as e:
            r = {"broken":True, "err":str(e)[:80]}
        r["n"] = n
        rows.append(r)
    b.close()
srv.shutdown()

# report
bad = []
print(f"{'pg':>3} {'fit':>9} {'·':>3} {'∙':>3} {'cdot':>4} {'tnum':>4} {'dot':>3} {'svgDim':>6}  flags")
for r in rows:
    n = r["n"]
    if r.get("broken"):
        print(f"{n:>3}  BROKEN  {r.get('err','')}"); bad.append((n,"broken")); continue
    fit = f"{r['sh']}/{r['ch']}"
    flags = []
    if r["sh"] > r["ch"]+1: flags.append("OVERFLOW")
    if r["empty"]: flags.append("EMPTY")
    if r["mid"] or r["mid2"] or r["cdot"]: flags.append("MULT·")
    if r["tasknum"]: flags.append("TASKNUM")
    if r["qmark"]==0: flags.append("NO-DOTS")
    if r["svgDimText"]: flags.append(f"SVGDIM({r['svgDimText']})")
    if not r["hasHeader"]: flags.append("NO-HEADER")
    if flags: bad.append((n, ",".join(flags)))
    print(f"{n:>3} {fit:>9} {r['mid']:>3} {r['mid2']:>3} {r['cdot']:>4} {r['tasknum']:>4} {r['qmark']:>3} {r['svgDimText']:>6}  {','.join(flags)}")

print("\n=== SUMMARY ===")
if not bad:
    print("ALL 39 PAGES CLEAN: A4 fit, no ·, no task-num, dots present, no SVG dimension numbers.")
else:
    print(f"{len(bad)} page(s) need attention:")
    for n,f in bad: print(f"  page-{n}: {f}")
json.dump(rows, open(r"C:/wk/verify_galil.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
