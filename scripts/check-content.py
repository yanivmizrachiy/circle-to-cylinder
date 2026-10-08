import hashlib
import json
import pathlib
import re
import sys
from collections import Counter

from pypdf import PdfReader

from release_fingerprint import compute_release_fingerprint

root = pathlib.Path(__file__).resolve().parents[1]
manifest = json.loads((root / "content-manifest.json").read_text(encoding="utf-8"))
circle = json.loads((root / "maagal/manifest.json").read_text(encoding="utf-8"))

errors = []

# Authority guard: RULES.md owns policy, content-manifest.json owns publication order,
# and maagal/manifest.json is routing metadata for the circle loaders only.
if circle.get("canonicalRepository") != "yanivmizrachiy/circle-to-cylinder":
    errors.append(
        "maagal/manifest.json canonicalRepository must be yanivmizrachiy/circle-to-cylinder"
    )
if circle.get("canonicalRoot") != "maagal":
    errors.append("maagal/manifest.json canonicalRoot must be maagal")
if circle.get("role") != "local-circle-routing":
    errors.append("maagal/manifest.json role must be local-circle-routing")
if circle.get("rulesFile") != "../RULES.md":
    errors.append("maagal/manifest.json rulesFile must point to ../RULES.md")
if circle.get("publicationManifest") != "../content-manifest.json":
    errors.append(
        "maagal/manifest.json publicationManifest must point to ../content-manifest.json"
    )
for stale_key in ("sourceOfTruth", "singleWorkbook", "canonicalLanguage", "designRules", "viewer"):
    if stale_key in circle:
        errors.append(
            f"maagal/manifest.json must not duplicate global authority/policy key: {stale_key}"
        )

sections = manifest.get("sections") or []
ids = [section.get("id") for section in sections]
if ids != ["circle", "cylinder", "cone"]:
    errors.append("content-manifest sections must be exactly: circle, cylinder, cone")

listed = []
section_pages = {}
for section in sections:
    expanded = []
    # Canonical manifest semantics are ranges first, then explicit pages.
    # Keep this identical to index.html and scripts/render-release.py.
    for page_range in section.get("ranges", []):
        if "toManifest" in page_range:
            errors.append(
                f"release SSOT must be self-contained; toManifest is forbidden in {section.get('id')}"
            )
            continue
        end = page_range.get("to")
        if end is None:
            errors.append(f"range in {section.get('id')} has no end")
            continue
        for number in range(int(page_range["from"]), int(end) + 1):
            expanded.append(
                f"{page_range['prefix']}{number}{page_range.get('suffix', '')}"
            )
    for page in section.get("pages", []):
        expanded.append(page)
    section_pages[section.get("id")] = expanded
    listed.extend(expanded)

# No duplicate page may silently appear in two positions/sections.
for page, count in Counter(listed).items():
    if count > 1:
        errors.append(f"page listed more than once: {page} ({count}x)")

missing = [page for page in listed if not (root / page).is_file()]
if missing:
    errors.extend(f"missing listed page: {page}" for page in missing)

# Canonical 192-page release lock.
expected_active_counts = {"circle": 99, "cylinder": 46, "cone": 47}
for section_id, expected in expected_active_counts.items():
    actual = len(section_pages.get(section_id, []))
    if actual != expected:
        errors.append(
            f"active {section_id} page count changed: {actual} != release lock {expected}; "
            "update manifest + PDF + RULES atomically before changing the live sequence"
        )
if len(listed) != 192:
    errors.append(
        f"active workbook page count changed: {len(listed)} != release lock 192; "
        "the downloadable PDF and RULES must be rebuilt/updated in the same change"
    )

expected_cone = [f"cone/page-{n}.html" for n in range(1, 47)] + ["gold/page-8.html"]
if section_pages.get("cone") != expected_cone:
    errors.append(
        "cone section must be cone/page-1..46 followed by gold/page-8.html"
    )

# Every gold page must be represented in the canonical manifest.
expected_gold = {page for page in listed if page.startswith("gold/")}
actual_gold = {
    page.relative_to(root).as_posix() for page in (root / "gold").glob("page-*.html")
}
for page in sorted(actual_gold - expected_gold):
    errors.append(f"unlisted gold page: {page}")

# Manifest paths must be repository-local. No URL or parent traversal is allowed.
for page in listed:
    if "://" in page or page.startswith("/") or ".." in pathlib.PurePosixPath(page).parts:
        errors.append(f"non-local manifest path is forbidden: {page}")

# The root viewer must consume the publication manifest directly and only.
viewer_path = root / "index.html"
if not viewer_path.is_file():
    errors.append("root viewer is missing: index.html")
else:
    viewer = viewer_path.read_text(encoding="utf-8")
    if "content-manifest.json" not in viewer:
        errors.append("root viewer must load content-manifest.json")
    if "maagal/manifest.json" in viewer:
        errors.append("root viewer must not depend on maagal/manifest.json")
    if "toManifest" in viewer:
        errors.append("root viewer must not implement deprecated toManifest semantics")
    if "loading='lazy'" not in viewer and 'loading="lazy"' not in viewer:
        errors.append("root viewer iframes must use lazy loading")
    if "function pump" in viewer or "setTimeout(pump" in viewer:
        errors.append("root viewer must not eagerly pump-load the full workbook")

# Active typography/prompt policy guard.
# Historical preserved sources stay untouched; canonical direct pages must use RULES.md units.
bad_units = ("ס״מ²", "ס״מ³", 'ס"מ²', 'ס"מ³')
for page_path in listed:
    if page_path.startswith(("cone/", "galil/", "gold/")):
        text = (root / page_path).read_text(encoding="utf-8")
        for bad in bad_units:
            if bad in text:
                errors.append(f"non-canonical unit {bad!r} in active page: {page_path}")

# Circle keeps historical source files immutable; every active loader must normalize visible legacy units.
for page_path in section_pages.get("circle", []):
    text = (root / page_path).read_text(encoding="utf-8")
    if ".replaceAll('ס״מ²','סמ״ר')" not in text or ".replaceAll('ס״מ³','סמ״ק')" not in text:
        errors.append(f"circle loader does not normalize visible legacy units: {page_path}")

# Gold prompts are canonical: q-line instructions must use a colon, never a question mark.
for page_path in sorted(expected_gold):
    text = (root / page_path).read_text(encoding="utf-8")
    for match in re.finditer(r'<p class="q-line"[^>]*>(.*?)</p>', text, flags=re.S):
        plain = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        if "?" in plain or "؟" in plain:
            errors.append(f"question mark in canonical gold prompt: {page_path}: {plain}")
        if not plain.endswith(":"):
            errors.append(f"gold prompt must end with colon: {page_path}: {plain}")

# The downloadable PDF must match both the active page count and the exact
# repository-local sources/assets that can affect the rendered workbook.
pdf_path = root / "assets/circle-to-cylinder.pdf"
if not pdf_path.is_file():
    errors.append("downloadable PDF is missing: assets/circle-to-cylinder.pdf")
else:
    try:
        pdf_reader = PdfReader(str(pdf_path))
        pdf_pages = len(pdf_reader.pages)
        pdf_metadata = pdf_reader.metadata or {}
    except Exception as exc:
        errors.append(f"downloadable PDF cannot be read: {exc}")
    else:
        if pdf_pages != len(listed):
            errors.append(
                f"downloadable PDF page count mismatch: {pdf_pages} != active manifest {len(listed)}"
            )
        expected_fingerprint = compute_release_fingerprint(root)
        actual_fingerprint = pdf_metadata.get("/WorkbookSourceSHA256")
        if actual_fingerprint != expected_fingerprint:
            errors.append(
                "downloadable PDF source fingerprint mismatch: "
                f"{actual_fingerprint!r} != {expected_fingerprint!r}; rebuild the PDF from current sources"
            )
        declared_count = pdf_metadata.get("/WorkbookPageCount")
        if declared_count != str(len(listed)):
            errors.append(
                f"downloadable PDF metadata page count mismatch: {declared_count!r} != {len(listed)!r}"
            )

# Keep human-readable authority docs aligned with the release count.
for doc_name in ["RULES.md", "README.md"]:
    doc_path = root / doc_name
    if not doc_path.is_file():
        errors.append(f"{doc_name} is missing")
    else:
        text = doc_path.read_text(encoding="utf-8")
        if "192" not in text:
            errors.append(f"{doc_name} does not document the 192-page release")

# Preserve the recovered 46-page cone source byte-for-byte inside the canonical repo.
preserved = root / "source/razpages-cone-5f67398"
source_json = preserved / "SOURCE.json"
if not source_json.is_file():
    errors.append("preserved cone SOURCE.json is missing")
else:
    source = json.loads(source_json.read_text(encoding="utf-8"))
    if source.get("repository") != "yanivmizrachiy/razpages":
        errors.append("preserved cone provenance repository changed")
    if source.get("commit") != "5f67398bcb100dd36e2275b34f4312e7f145e14e":
        errors.append("preserved cone provenance commit changed")
    if source.get("conePages") != 46:
        errors.append("preserved cone provenance must declare 46 pages")

cone_source = preserved / "workbooks/cone/index.html"
if not cone_source.is_file():
    errors.append("preserved 46-page cone index is missing")
else:
    cone_html = cone_source.read_text(encoding="utf-8")
    local_pages = [int(value) for value in re.findall(r'data-local-page="(\d+)"', cone_html)]
    if sorted(set(local_pages)) != list(range(1, 47)):
        errors.append("preserved cone must contain local pages 1..46 exactly")

expected_visual_assets = {
    "anis-basics.jpg",
    "anis-basics.svg",
    "cone-3d-down.svg",
    "cone-3d-side.svg",
    "cone-3d-upright.svg",
    "cone-in-my-head.jpg",
    "cone-in-my-head.svg",
    "count-scene.svg",
    "find-scene.svg",
    "jerusalem-cone-vision.jpg",
    "jerusalem-cone-vision.svg",
    "world-of-cones.jpg",
    "world-of-cones.svg",
}
visual_dir = preserved / "workbooks/visual-assets"
actual_visual_assets = {p.name for p in visual_dir.iterdir() if p.is_file()} if visual_dir.is_dir() else set()
for missing_asset in sorted(expected_visual_assets - actual_visual_assets):
    errors.append(f"preserved cone visual asset missing: {missing_asset}")

# Git blob SHA verification catches silent modification of key recovered source files.
def git_blob_sha(path):
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


protected_blobs = {
    "workbooks/cone/index.html": "8c2ce749d644e4e37e48b83f86a39f6460927ef4",
    "workbooks/cone/styles.css": "567b9465c41b69f4207b82cddc8d143ef022eaa2",
    "workbooks/cone/reader.css": "09f236ccff149684dee591fb4a57e27a422509f1",
    "workbooks/cone/reader.js": "f53a95a7c84e2671607af32ab148febd58f39d89",
    "workbooks/cone/assets/ayelet-original-cone.png": "296d61eb90086cb9b928ccc74ce2109f8c7f0264",
    "workbooks/visual-assets/anis-basics.jpg": "ccef40caf7c7f3c489f34cf1e6c4dd4c114176ce",
    "workbooks/visual-assets/cone-3d-upright.svg": "6a017982e243eb54e9f006df66b1277b2ac7f611",
    "workbooks/visual-assets/jerusalem-cone-vision.jpg": "702dccd0d914352224f13b37cd58fc9c1c7ec96d",
    "workbooks/visual-assets/world-of-cones.jpg": "cb721a5ebed7664188882b049257a8d9fc45e0c9",
}
for relative, expected_sha in protected_blobs.items():
    path = preserved / relative
    if not path.is_file():
        errors.append(f"protected preserved source file missing: {relative}")
    elif git_blob_sha(path) != expected_sha:
        errors.append(f"protected preserved source file changed: {relative}")

if errors:
    print("CONTENT INTEGRITY FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

counts = {key: len(value) for key, value in section_pages.items()}
print(
    "OK: "
    f"{len(listed)} active pages; "
    f"circle={counts.get('circle', 0)}, "
    f"cylinder={counts.get('cylinder', 0)}, "
    f"cone={counts.get('cone', 0)}; "
    "192-page release lock and PDF count match; authority split is clean; "
    "root viewer consumes only the publication SSOT and lazy-loads pages; "
    "recovered 46-page cone source is preserved byte-for-byte; "
    "no missing, duplicate, external or unlisted gold pages."
)
