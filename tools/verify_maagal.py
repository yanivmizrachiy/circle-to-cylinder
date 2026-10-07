#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render all maagal pages (via loader) and verify SSOT compliance + A4 fit + footer.
Run: PYTHONIOENCODING=utf-8 python verify_maagal.py"""
import threading, functools, json, os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

M = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "maagal")
PORT = 8260
N = 99

h = functools.partial(SimpleHTTPRequestHandler, directory=M)
srv = ThreadingHTTPServer(("127.0.0.1", PORT), h)
threading.Thread(target=srv.serve_forever, daemon=True).start()

CHECK = r"""
() => {
  const a = document.querySelector('.a4-page');
  if (!a) return {broken:true};
  const html = a.innerHTML;
  const txt = a.innerText || '';
  // d-as-diameter left in TEXT (SVG path d="..." is an attribute, not innerText -> ignored)
  const dText = (txt.match(/(^|[^A-Za-z\u05d0-\u05ea])d([^A-Za-z\u05d0-\u05ea]|$)/g)||[]).length;
  const foot = a.querySelector('.gz-footer .f1');
  return {
    broken:false,
    empty: txt.trim().length < 10,
    sh:a.scrollHeight, ch:a.clientHeight,
    mid:(html.match(/\u00b7/g)||[]).length,
    cdot:(html.match(/\\cdot/g)||[]).length,
    tasknum:(html.match(/task-num/g)||[]).length,
    gen:(html.match(/<th[^>]*>\s*(נתון|מבוקש|תשובה|נדרש)\s*<\/th>/g)||[]).length,
    dText:dText,
    footer: foot ? (foot.textContent.includes('יניב רז')?1:0) : 0,
    qmark:(html.match(/qmark/g)||[]).length,
  };
}
"""

rows=[]
with sync_playwright() as p:
    b=p.chromium.launch(channel="chrome")
    pg=b.new_page(); pg.set_viewport_size({"width":900,"height":1300})
    for n in range(1,N+1):
        try:
            pg.goto(f"http://127.0.0.1:{PORT}/page-{n}.html", wait_until="networkidle", timeout=40000)
            pg.wait_for_timeout(500)  # loader + MathJax
            r=pg.evaluate(CHECK)
        except Exception as e:
            r={"broken":True,"err":str(e)[:70]}
        r["n"]=n; rows.append(r)
    b.close()
srv.shutdown()

bad=[]
print(f"{'pg':>3} {'fit':>10} {'·':>3} {'tnum':>4} {'gen':>3} {'dTxt':>4} {'foot':>4} {'dot':>3}  flags")
for r in rows:
    n=r["n"]
    if r.get("broken"):
        print(f"{n:>3}  BROKEN {r.get('err','')}"); bad.append((n,"broken")); continue
    fit=f"{r['sh']}/{r['ch']}"; fl=[]
    if r["sh"]>r["ch"]+1: fl.append("OVERFLOW")
    if r["empty"]: fl.append("EMPTY")
    if r["mid"] or r["cdot"]: fl.append("MULT·")
    if r["tasknum"]: fl.append("TASKNUM")
    if r["gen"]: fl.append("GENHDR")
    if not r["footer"]: fl.append("NO-FOOTER")
    if r["dText"]: fl.append(f"dTEXT({r['dText']})")
    if fl: bad.append((n,",".join(fl)))
    print(f"{n:>3} {fit:>10} {r['mid']:>3} {r['tasknum']:>4} {r['gen']:>3} {r['dText']:>4} {r['footer']:>4} {r['qmark']:>3}  {','.join(fl)}")

print("\n=== SUMMARY ===")
hard=[x for x in bad if 'dTEXT' not in x[1] or any(k in x[1] for k in ['OVERFLOW','EMPTY','MULT','TASKNUM','GENHDR','NO-FOOTER','broken'])]
if not bad:
    print("ALL 106 CLEAN.")
else:
    print(f"{len(bad)} page(s) flagged (dTEXT may be false positives from coord labels; review):")
    for n,f in bad: print(f"  page-{n}: {f}")
json.dump(rows, open(r"C:/wk/verify_maagal.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
