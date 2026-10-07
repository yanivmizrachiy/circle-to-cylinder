import json
import pathlib
import re
import sys

root = pathlib.Path(__file__).resolve().parents[1]
cone = root / "cone"
errors = []

manifest_path = cone / "manifest.json"
if not manifest_path.is_file():
    errors.append("cone/manifest.json is missing")
else:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("canonicalRepository") != "yanivmizrachiy/circle-to-cylinder":
        errors.append("cone manifest canonicalRepository is invalid")
    if manifest.get("canonicalRoot") != "cone":
        errors.append("cone manifest canonicalRoot must be cone")
    if manifest.get("sourceOfTruth") is not True:
        errors.append("cone manifest sourceOfTruth must be true")
    if manifest.get("pageCount") != 46:
        errors.append("cone manifest pageCount must be 46")
    if manifest.get("sourceCommit") != "5f67398bcb100dd36e2275b34f4312e7f145e14e":
        errors.append("cone manifest sourceCommit changed unexpectedly")

expected_pages = {f"page-{n}.html" for n in range(1, 47)}
actual_pages = {p.name for p in cone.glob("page-*.html")}
for name in sorted(expected_pages - actual_pages):
    errors.append(f"missing canonical cone page: cone/{name}")
for name in sorted(actual_pages - expected_pages):
    errors.append(f"unexpected canonical cone page: cone/{name}")

local_ref_pattern = re.compile(r'(?:src|href)="([^"]+)"', re.IGNORECASE)
for number in range(1, 47):
    path = cone / f"page-{number}.html"
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8")
    if len(re.findall(r"<main\b", text, re.IGNORECASE)) != 1:
        errors.append(f"cone/page-{number}.html must contain exactly one <main>")
    if f'data-local-page="{number}"' not in text:
        errors.append(f"cone/page-{number}.html has wrong or missing data-local-page")
    if "../visual-assets/" in text:
        errors.append(f"cone/page-{number}.html still points outside cone/ to visual-assets")

    for ref in local_ref_pattern.findall(text):
        if ref.startswith(("http://", "https://", "data:", "mailto:", "#")):
            continue
        clean = ref.split("#", 1)[0].split("?", 1)[0]
        if not clean:
            continue
        target = (path.parent / clean).resolve()
        try:
            target.relative_to(cone.resolve())
        except ValueError:
            errors.append(f"cone/page-{number}.html escapes cone/: {ref}")
            continue
        if not target.exists():
            errors.append(f"cone/page-{number}.html broken local reference: {ref}")

required_assets = [
    cone / "styles.css",
    cone / "assets/ayelet-original-cone.png",
    cone / "visual-assets/anis-basics.jpg",
    cone / "visual-assets/cone-3d-upright.svg",
    cone / "visual-assets/jerusalem-cone-vision.jpg",
    cone / "visual-assets/world-of-cones.jpg",
]
for path in required_assets:
    if not path.is_file():
        errors.append(f"required canonical cone asset missing: {path.relative_to(root)}")

if errors:
    print("CONE PACKAGE INTEGRITY FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("OK: cone/ contains exactly 46 standalone A4 pages; manifest and local asset references are valid.")
