import json
import pathlib
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

if errors:
    print("CONTENT INTEGRITY FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

counts = {key: len(value) for key, value in section_pages.items()}
print(
    "OK: "
    f"{len(listed)} pages; "
    f"circle={counts.get('circle', 0)}, "
    f"cylinder={counts.get('cylinder', 0)}, "
    f"cone={counts.get('cone', 0)}; "
    "SSOT is local; no missing, duplicate, external or unlisted gold pages."
)
