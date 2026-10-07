import functools
import http.server
import json
import pathlib
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_TOTAL = 192
EXPECTED_STARTS = {"circle": 1, "cylinder": 100, "cone": 146}


def expand_manifest():
    manifest = json.loads((ROOT / "content-manifest.json").read_text(encoding="utf-8"))
    pages = []
    starts = {}
    for section in manifest.get("sections", []):
        starts[section["id"]] = len(pages) + 1
        for item in section.get("ranges", []):
            if "toManifest" in item or item.get("to") is None:
                raise RuntimeError("publication manifest must be self-contained")
            for number in range(int(item["from"]), int(item["to"]) + 1):
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


def attach_local_network_guards(page, base_url, errors, label):
    def on_response(response):
        if response.url.startswith(base_url) and response.status >= 400:
            errors.append(f"{label}: local HTTP {response.status} {response.url}")

    def on_request_failed(request):
        if request.url.startswith(base_url):
            errors.append(f"{label}: local request failed {request.url}: {request.failure}")

    page.on("response", on_response)
    page.on("requestfailed", on_request_failed)
    page.on("pageerror", lambda exc: errors.append(f"{label}: page error: {exc}"))


def check_viewport(browser, base_url, pages, starts, viewport, jump_section, label):
    errors = []
    page = browser.new_page(viewport=viewport)
    attach_local_network_guards(page, base_url, errors, label)
    page.goto(base_url + "/index.html", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_function(
        f"document.querySelectorAll('.slot').length === {len(pages)}", timeout=30000
    )
    page.wait_for_timeout(350)

    actual_sources = page.locator(".slot").evaluate_all(
        "els => els.map(el => el._src || '')"
    )
    if actual_sources != pages:
        errors.append(f"{label}: viewer source sequence does not match content-manifest.json")

    initial_iframes = page.locator(".slot iframe").count()
    if initial_iframes < 2:
        errors.append(f"{label}: expected at least the first two iframes, found {initial_iframes}")
    if initial_iframes > 8:
        errors.append(
            f"{label}: lazy loading regressed; {initial_iframes} iframes loaded immediately"
        )
    if page.locator(f"#p{len(pages)} iframe").count() != 0:
        errors.append(f"{label}: last page was loaded eagerly")

    overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 2")
    if overflow:
        errors.append(f"{label}: horizontal viewer overflow")

    target_number = starts[jump_section]
    page.evaluate(f"jump('{jump_section}')")
    page.wait_for_selector(f"#p{target_number} iframe", timeout=10000)
    page.wait_for_function(
        f"document.querySelector('#p{target_number} iframe')?.contentDocument?.querySelector('.a4-page') !== null",
        timeout=15000,
    )
    target_src = page.locator(f"#p{target_number}").evaluate("el => el._src || ''")
    if target_src != pages[target_number - 1]:
        errors.append(
            f"{label}: {jump_section} navigation loaded {target_src!r}, expected {pages[target_number - 1]!r}"
        )

    loaded_after_jump = page.locator(".slot iframe").count()
    if loaded_after_jump > 18:
        errors.append(
            f"{label}: section jump loaded too many iframes ({loaded_after_jump}); lazy loading regressed"
        )

    page.close()
    return errors


def main():
    pages, starts = expand_manifest()
    errors = []
    if len(pages) != EXPECTED_TOTAL:
        errors.append(f"manifest has {len(pages)} pages, expected {EXPECTED_TOTAL}")
    if starts != EXPECTED_STARTS:
        errors.append(f"section starts changed: {starts} != {EXPECTED_STARTS}")
    if errors:
        raise SystemExit("\n".join(errors))

    server, base_url = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            errors.extend(
                check_viewport(
                    browser,
                    base_url,
                    pages,
                    starts,
                    {"width": 1280, "height": 900},
                    "cone",
                    "desktop",
                )
            )
            errors.extend(
                check_viewport(
                    browser,
                    base_url,
                    pages,
                    starts,
                    {"width": 390, "height": 844},
                    "cylinder",
                    "mobile",
                )
            )
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    if errors:
        print("VIEWER RUNTIME QA FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(
        "OK: viewer uses the exact 192-page publication sequence, stays lazy on desktop/mobile, "
        "loads section jumps on demand, and has no local request/page errors or horizontal overflow."
    )


if __name__ == "__main__":
    main()
