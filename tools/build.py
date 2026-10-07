#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the merged circle->cylinder booklet PDF (maagal 99 + galil 39).
Continuous content only - no cover/separator pages. A4, zero margins.

Run from the repo root:
    PYTHONIOENCODING=utf-8 python tools/build.py

Output: dist/circle-to-cylinder.pdf
Requires: playwright (with Chrome/Chromium) and pypdf.
"""
import os, threading, functools
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
from pypdf import PdfWriter, PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
TMP = os.path.join(DIST, "_pages")
os.makedirs(TMP, exist_ok=True)

# (name, directory, page-count, local-port)
BOOKS = [
    ("maagal", os.path.join(ROOT, "maagal"), 99, 8301),
    ("galil",  os.path.join(ROOT, "galil"),  39, 8302),
]


def serve(root, port):
    handler = functools.partial(SimpleHTTPRequestHandler, directory=root)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def render(page, url, out_path):
    page.goto(url, wait_until="networkidle", timeout=60000)
    try:
        page.wait_for_selector(".a4-page", timeout=20000)
    except Exception:
        pass
    try:
        page.evaluate("async()=>{if(window.MathJax&&MathJax.startup&&MathJax.startup.promise){await MathJax.startup.promise;}}")
    except Exception:
        pass
    page.wait_for_timeout(450)
    page.emulate_media(media="print")
    page.pdf(path=out_path, format="A4", print_background=True,
             margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})


def main():
    pdfs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_context().new_page()
        for name, root, n, port in BOOKS:
            srv = serve(root, port)
            for i in range(1, n + 1):
                op = os.path.join(TMP, f"{name}_{i:03d}.pdf")
                render(page, f"http://127.0.0.1:{port}/page-{i}.html", op)
                pdfs.append(op)
            srv.shutdown()
            print(f"{name} {n} done")
        browser.close()

    writer = PdfWriter()
    total = 0
    for f in pdfs:
        for pg in PdfReader(f).pages:
            writer.add_page(pg)
            total += 1
    out = os.path.join(DIST, "circle-to-cylinder.pdf")
    with open(out, "wb") as fh:
        writer.write(fh)
    print(f"MERGED {total} pages (no covers) -> {out}")


if __name__ == "__main__":
    main()
