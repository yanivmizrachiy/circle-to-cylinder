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
    if manifest.get("canonicalPackage") is not True:
        errors.append("cone manifest canonicalPackage must be true")
    if "sourceOfTruth" in manifest:
        errors.append("cone manifest must not declare sourceOfTruth; release sequence authority belongs only to content-manifest.json")
    if manifest.get("releaseSequenceAuthority") != "../content-manifest.json":
        errors.append("cone manifest releaseSequenceAuthority must point to ../content-manifest.json")
    if manifest.get("contentEditingAuthority") != "page-N.html":
        errors.append("cone manifest contentEditingAuthority must be page-N.html")
    if manifest.get("historicalSourceImmutable") is not True:
        errors.append("cone manifest must mark historicalSourceImmutable=true")
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
forbidden_historical_refs = {
    "visual-assets/anis-basics.jpg",
    "visual-assets/anis-basics.svg",
}

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
        if ref in forbidden_historical_refs:
            errors.append(f"cone/page-{number}.html references inactive corrupt historical asset: {ref}")
            continue
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
    cone / "visual-assets/cone-3d-upright.svg",
    cone / "visual-assets/jerusalem-cone-vision.jpg",
    cone / "visual-assets/world-of-cones.jpg",
]
for path in required_assets:
    if not path.is_file():
        errors.append(f"required canonical cone asset missing: {path.relative_to(root)}")

# Guard the distinction between the disk (base) and its boundary circle.
page1 = cone / "page-1.html"
if page1.is_file():
    text = page1.read_text(encoding="utf-8")
    if "בסיס החרוט הוא  - מעגל" in text:
        errors.append("cone/page-1.html incorrectly calls the cone base a circle boundary instead of a disk")
    if "בסיס החרוט הוא  - עיגול" not in text:
        errors.append("cone/page-1.html must state that the cone base is an עיגול")

# Page 6 is the canonical accessible replacement for an unrecoverable historical illustration.
page6 = cone / "page-6.html"
if page6.is_file():
    text = page6.read_text(encoding="utf-8")
    required = [
        "בסיס החרוט הוא",
        "שפת הבסיס היא",
        "רדיוס",
        "גובה",
        "יוצר",
    ]
    if any(value not in text for value in required):
        errors.append("cone/page-6.html must keep the canonical diagnostic concepts")
    if "anis-basics" in text:
        errors.append("cone/page-6.html must not depend on the unrecoverable Anis historical image")

# Guard the basic geometric meanings taught before any formula is used.
page5 = cone / "page-5.html"
if page5.is_file():
    text = page5.read_text(encoding="utf-8")
    forbidden = [
        "מהמרכז אל שפת הבסיס / מן הקודקוד אל המרכז",
        "האנך מן הקודקוד אל מרכז הבסיס / הקו המשופע על המעטפת",
    ]
    if any(value in text for value in forbidden):
        errors.append("cone/page-5.html mixes radius/height with other cone dimensions")
    required = [
        "קטע ממרכז הבסיס אל נקודה על שפת הבסיס",
        "האנך מן הקודקוד אל מרכז הבסיס",
        "קטע מן הקודקוד אל נקודה על שפת הבסיס",
    ]
    if any(value not in text for value in required):
        errors.append("cone/page-5.html must keep the canonical radius, height and slant-height definitions")

# Guard the exact terminology used in the cone-volume formula lesson.
# Diameter must be converted to radius; slant height is not the perpendicular height in V=(1/3)πr²h.
page12 = cone / "page-12.html"
if page12.is_file():
    text = page12.read_text(encoding="utf-8")
    if "רדיוס הבסיס / קוטר הבסיס" in text:
        errors.append("cone/page-12.html incorrectly treats diameter as the formula radius")
    if "גובה החרוט / היוצר" in text:
        errors.append("cone/page-12.html incorrectly treats slant height as the formula height")
    if "רדיוס הבסיס</td>" not in text or "הגובה המאונך של החרוט</td>" not in text:
        errors.append("cone/page-12.html must state radius and perpendicular height explicitly")

if errors:
    print("CONE PACKAGE INTEGRITY FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("OK: cone/ contains exactly 46 standalone A4 pages; scoped manifest authority, local references, required assets and core cone terminology are valid.")
