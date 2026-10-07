import hashlib
import json
import pathlib
import re
import sys
from collections import Counter

root = pathlib.Path(__file__).resolve().parents[1]
manifest = json.loads((root / "content-manifest.json").read_text(encoding="utf-8"))
circle = json.loads((root / "maagal/manifest.json").read_text(encoding="utf-8"))

errors = []

# Single-source-of-truth guard: canonical metadata must point back to this repo.
if circle.get("canonicalRepository") != "yanivmizrachiy/circle-to-cylinder":
    errors.append(
        "maagal/manifest.json canonicalRepository must be yanivmizrachiy/circle-to-cylinder"
    )
if circle.get("canonicalRoot") != "maagal":
    errors.append("maagal/manifest.json canonicalRoot must be maagal")
if circle.get("sourceOfTruth") is not True:
    errors.append("maagal/manifest.json sourceOfTruth must be true")

sections = manifest.get("sections") or []
ids = [section.get("id") for section in sections]
if ids != ["circle", "cylinder", "cone"]:
    errors.append("content-manifest sections must be exactly: circle, cylinder, cone")

listed = []
section_pages = {}
for section in sections:
    expanded = []
    for page in section.get("pages", []):
        expanded.append(page)
    for page_range in section.get("ranges", []):
        end = page_range.get("to")
        if page_range.get("toManifest"):
            if page_range["toManifest"] != "maagal/manifest.json":
                errors.append(
                    f"unsupported external manifest reference: {page_range['toManifest']}"
                )
                continue
            end = int(circle.get("pageCount", 0))
        if end is None:
            errors.append(f"range in {section.get('id')} has no end")
            continue
        for number in range(int(page_range["from"]), int(end) + 1):
            expanded.append(
                f"{page_range['prefix']}{number}{page_range.get('suffix', '')}"
            )
    section_pages[section.get("id")] = expanded
    listed.extend(expanded)

# No duplicate page may silently appear in two positions/sections.
for page, count in Counter(listed).items():
    if count > 1:
        errors.append(f"page listed more than once: {page} ({count}x)")

missing = [page for page in listed if not (root / page).is_file()]
if missing:
    errors.extend(f"missing listed page: {page}" for page in missing)

# Protect the known-good current book while cone consolidation is performed.
minimums = {"circle": 99, "cylinder": 46, "cone": 1}
for section_id, minimum in minimums.items():
    actual = len(section_pages.get(section_id, []))
    if actual < minimum:
        errors.append(
            f"{section_id} page count regressed: {actual} < protected minimum {minimum}"
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
    "SSOT is local; recovered 46-page cone source is preserved byte-for-byte; "
    "no missing, duplicate, external or unlisted gold pages."
)
