import argparse
import functools
import http.server
import json
import pathlib
import tempfile
import threading
import urllib.parse

from pypdf import PdfReader, PdfWriter
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_TOTAL = 192


def expand_manifest():
    content = json.loads((ROOT / "content-manifest.json").read_text(encoding="utf-8"))
    pages = []
    starts = {}
    for section in content.get("sections", []):
        section_id = section["id"]
        starts[section_id] = len(pages) + 1
        for item in section.get("ranges", []):
            if "toManifest" in item:
                raise RuntimeError(
                    f"release manifest must be self-contained; toManifest found in {section_id}"
                )
            if item.get("to") is None:
                raise RuntimeError(f"release range in {section_id} has no explicit 'to'")
            end = int(item["to"])
            for number in range(int(item["from"]), end + 1):
                pages.append(f"{item['prefix']}{number}{item.get('suffix', '')}")
        pages.extend(section.get("pages", []))
    return pages, starts


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


def start_server():
    handler = functools.partial(QuietHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}"


def wait_for_page_ready(page):
    page.evaluate(
        """
        async () => {
          if (document.fonts && document.fonts.ready) await document.fonts.ready;
          if (window.MathJax && MathJax.startup && MathJax.startup.promise) {
            await MathJax.startup.promise;
          }
        }
        """
    )
    page.wait_for_timeout(120)


def qa_metrics(page):
    return page.locator(".a4-page").evaluate(
        """
        el => {
          const directFooter = Array.from(el.children).find(
            child => child.classList && child.classList.contains('gz-footer')
          );
          let footerOverlap = 0;
          if (directFooter && getComputedStyle(directFooter).display !== 'none') {
            const content = Array.from(el.children).find(
              child => child.classList && (
                child.classList.contains('sheet-content') ||
                child.classList.contains('ayelet-source-sheet')
              )
            );
            if (content) {
              const visibleChildren = Array.from(content.children).filter(child => {
                const style = getComputedStyle(child);
                const rect = child.getBoundingClientRect();
                return style.display !== 'none' && style.visibility !== 'hidden' && rect.height > 0;
              });
              if (visibleChildren.length) {
                const lastBottom = Math.max(
                  ...visibleChildren.map(child => child.getBoundingClientRect().bottom)
                );
                footerOverlap = Math.max(
                  0,
                  Math.ceil(lastBottom - directFooter.getBoundingClientRect().top)
                );
              }
            }
          }
          return {
            clientWidth: el.clientWidth,
            clientHeight: el.clientHeight,
            scrollWidth: el.scrollWidth,
            scrollHeight: el.scrollHeight,
            rectWidth: el.getBoundingClientRect().width,
            rectHeight: el.getBoundingClientRect().height,
            footerOverlap,
            brokenImages: Array.from(document.images)
              .filter(img => !img.complete || img.naturalWidth === 0)
              .map(img => img.getAttribute('src') || '')
          };
        }
        """
    )


def write_report(report_path, report):
    if not report_path:
        return
    path = pathlib.Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def check_viewer(browser, base_url, pages, starts):
    errors = []
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto(base_url + "/index.html", wait_until="domcontentloaded")
    page.wait_for_function(
        f"document.querySelectorAll('.slot').length === {len(pages)}", timeout=30000
    )
    actual = page.locator(".slot").count()
    if actual != len(pages):
        errors.append(f"viewer slot count {actual} != manifest {len(pages)}")

    expected_samples = {
        1: pages[0],
        starts["cylinder"]: pages[starts["cylinder"] - 1],
        starts["cone"]: pages[starts["cone"] - 1],
        len(pages) - 1: pages[-2],
        len(pages): pages[-1],
    }
    for number, expected in expected_samples.items():
        actual_src = page.locator(f"#p{number}").evaluate("el => el._src || ''")
        if actual_src != expected:
            errors.append(
                f"viewer p{number} source mismatch: {actual_src!r} != {expected!r}"
            )

    if starts != {"circle": 1, "cylinder": 100, "cone": 146}:
        errors.append(f"unexpected section starts: {starts}")

    desktop_overflow = page.evaluate(
        "document.documentElement.scrollWidth > window.innerWidth + 2"
    )
    if desktop_overflow:
        errors.append("viewer has horizontal overflow at desktop width")
    page.close()

    mobile = browser.new_page(viewport={"width": 390, "height": 844})
    mobile.goto(base_url + "/index.html", wait_until="domcontentloaded")
    mobile.wait_for_function(
        f"document.querySelectorAll('.slot').length === {len(pages)}", timeout=30000
    )
    mobile.wait_for_timeout(200)
    mobile_overflow = mobile.evaluate(
        "document.documentElement.scrollWidth > window.innerWidth + 2"
    )
    if mobile_overflow:
        errors.append("viewer has horizontal overflow at mobile width 390px")
    mobile.close()
    return errors


def render_release(output_pdf, report_path=None):
    pages, starts = expand_manifest()
    errors = []
    report = {
        "status": "running",
        "total": len(pages),
        "starts": starts,
        "first": pages[0] if pages else None,
        "last": pages[-1] if pages else None,
        "pages": [],
        "errors": [],
    }

    if len(pages) != EXPECTED_TOTAL:
        errors.append(f"manifest has {len(pages)} pages, expected {EXPECTED_TOTAL}")
    if len(set(pages)) != len(pages):
        errors.append("manifest contains duplicate page paths")
    missing = [path for path in pages if not (ROOT / path).is_file()]
    errors.extend(f"manifest page missing: {path}" for path in missing)
    if errors:
        report["status"] = "failed"
        report["errors"] = errors
        write_report(report_path, report)
        raise RuntimeError("; ".join(errors))

    server, base_url = start_server()
    try:
        with sync_playwright() as pw, tempfile.TemporaryDirectory() as tmp:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1200, "height": 1400})
            page = context.new_page()
            bad_local_responses = []
            failed_local_requests = []

            def on_response(response):
                if response.url.startswith(base_url) and response.status >= 400:
                    bad_local_responses.append((response.status, response.url))

            def on_request_failed(request):
                if request.url.startswith(base_url):
                    failed_local_requests.append(
                        (request.url, request.failure or "request failed")
                    )

            page.on("response", on_response)
            page.on("requestfailed", on_request_failed)

            pdf_parts = []
            tmp_root = pathlib.Path(tmp)
            for index, relative in enumerate(pages, start=1):
                before_bad = len(bad_local_responses)
                before_failed = len(failed_local_requests)
                url = base_url + "/" + urllib.parse.quote(relative, safe="/-._~")
                page.goto(url, wait_until="load", timeout=30000)
                wait_for_page_ready(page)

                main_count = page.locator(".a4-page").count()
                if main_count != 1:
                    errors.append(
                        f"page {index} {relative}: expected one .a4-page, found {main_count}"
                    )
                    continue

                metrics = qa_metrics(page)
                overflow_x = metrics["scrollWidth"] - metrics["clientWidth"]
                overflow_y = metrics["scrollHeight"] - metrics["clientHeight"]
                if overflow_x > 2:
                    errors.append(
                        f"page {index} {relative}: horizontal A4 overflow {overflow_x}px"
                    )
                if overflow_y > 2:
                    errors.append(
                        f"page {index} {relative}: vertical A4 overflow {overflow_y}px"
                    )
                if metrics["footerOverlap"] > 1:
                    errors.append(
                        f"page {index} {relative}: footer overlaps content by {metrics['footerOverlap']}px"
                    )
                for src in metrics["brokenImages"]:
                    errors.append(f"page {index} {relative}: broken image {src}")

                for status, failed_url in bad_local_responses[before_bad:]:
                    errors.append(
                        f"page {index} {relative}: local HTTP {status} {failed_url}"
                    )
                for failed_url, reason in failed_local_requests[before_failed:]:
                    errors.append(
                        f"page {index} {relative}: local request failed {failed_url}: {reason}"
                    )

                part = tmp_root / f"{index:03d}.pdf"
                page.pdf(
                    path=str(part),
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                    margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                )
                part_pages = len(PdfReader(str(part)).pages)
                if part_pages != 1:
                    errors.append(
                        f"page {index} {relative}: Chromium produced {part_pages} PDF pages"
                    )
                pdf_parts.append(part)
                report["pages"].append(
                    {
                        "number": index,
                        "path": relative,
                        "a4Width": metrics["clientWidth"],
                        "a4Height": metrics["clientHeight"],
                        "overflowX": overflow_x,
                        "overflowY": overflow_y,
                        "footerOverlap": metrics["footerOverlap"],
                    }
                )

            errors.extend(check_viewer(browser, base_url, pages, starts))
            context.close()
            browser.close()

            if errors:
                report["status"] = "failed"
                report["errors"] = errors
                write_report(report_path, report)
                raise RuntimeError("\n".join(errors))

            writer = PdfWriter()
            for part in pdf_parts:
                writer.append(str(part))
            # Lossless de-duplication of repeated fonts/images/resources from 192 one-page PDFs.
            if hasattr(writer, "compress_identical_objects"):
                writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)
            pathlib.Path(output_pdf).parent.mkdir(parents=True, exist_ok=True)
            with pathlib.Path(output_pdf).open("wb") as handle:
                writer.write(handle)

            final_count = len(PdfReader(str(output_pdf)).pages)
            if final_count != len(pages):
                errors.append(
                    f"merged PDF has {final_count} pages, expected {len(pages)}"
                )
                report["status"] = "failed"
                report["errors"] = errors
                report["pdfPages"] = final_count
                write_report(report_path, report)
                raise RuntimeError(errors[-1])

            report["status"] = "passed"
            report["pdfPages"] = final_count
            report["errors"] = []
            write_report(report_path, report)
            print(
                f"OK: Chromium validated {len(pages)} A4 pages with no footer overlap; "
                f"viewer starts={starts}; merged PDF has {final_count} pages."
            )
    except Exception as exc:
        if report.get("status") != "failed":
            report["status"] = "failed"
            report["errors"] = [str(exc)]
            write_report(report_path, report)
        raise
    finally:
        server.shutdown()
        server.server_close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=str(ROOT / "assets/circle-to-cylinder.pdf"),
        help="Output PDF path",
    )
    parser.add_argument(
        "--report",
        default=str(ROOT / ".qa/release-report.json"),
        help="QA JSON report path",
    )
    args = parser.parse_args()
    render_release(args.output, args.report)


if __name__ == "__main__":
    main()
