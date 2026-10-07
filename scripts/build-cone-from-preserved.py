import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "source/razpages-cone-5f67398"
SOURCE_CONE = SOURCE_ROOT / "workbooks/cone"
SOURCE_VISUAL = SOURCE_ROOT / "workbooks/visual-assets"
TARGET = ROOT / "cone"
EXCLUDED_CORRUPT_ASSETS = {"anis-basics.jpg", "anis-basics.svg"}


def fail(message):
    print(f"CONE BUILD FAILED: {message}", file=sys.stderr)
    raise SystemExit(1)


def ignore_corrupt_historical_assets(directory, names):
    if pathlib.Path(directory).resolve() != SOURCE_VISUAL.resolve():
        return set()
    return {name for name in names if name in EXCLUDED_CORRUPT_ASSETS}


if TARGET.exists():
    fail("cone/ already exists; refusing to overwrite generated or edited content")

source_index = SOURCE_CONE / "index.html"
if not source_index.is_file():
    fail("preserved cone source index is missing")

html = source_index.read_text(encoding="utf-8")
pattern = re.compile(
    r'(<main\b(?=[^>]*\bdata-local-page="(\d+)")[^>]*>.*?</main>)',
    re.IGNORECASE | re.DOTALL,
)
found = [(int(number), block) for block, number in pattern.findall(html)]

if len(found) != 46:
    fail(f"expected 46 A4 pages, found {len(found)}")

numbers = [number for number, _ in found]
if numbers != list(range(1, 47)):
    fail(f"page order is not exactly 1..46: {numbers}")

TARGET.mkdir()
shutil.copy2(SOURCE_CONE / "styles.css", TARGET / "styles.css")
shutil.copytree(SOURCE_CONE / "assets", TARGET / "assets")
shutil.copytree(
    SOURCE_VISUAL,
    TARGET / "visual-assets",
    ignore=ignore_corrupt_historical_assets,
)

head = '''<!doctype html>
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
'''

for number, block in found:
    # Original monolithic cone lived in workbooks/cone/, where ../visual-assets/
    # resolved to workbooks/visual-assets/. In canonical cone/ both are siblings.
    page = block.replace("../visual-assets/", "visual-assets/")
    output = head.format(title=f"חרוט — עמוד {number}") + page + "\n</body>\n</html>\n"
    (TARGET / f"page-{number}.html").write_text(output, encoding="utf-8")

metadata = {
    "canonicalRepository": "yanivmizrachiy/circle-to-cylinder",
    "canonicalRoot": "cone",
    "canonicalPackage": True,
    "releaseSequenceAuthority": "../content-manifest.json",
    "contentEditingAuthority": "page-N.html",
    "historicalSourceImmutable": True,
    "pageCount": 46,
    "generatedFrom": "source/razpages-cone-5f67398/workbooks/cone/index.html",
    "sourceRepository": "yanivmizrachiy/razpages",
    "sourceCommit": "5f67398bcb100dd36e2275b34f4312e7f145e14e",
    "historicalRecoveryExclusions": sorted(
        f"visual-assets/{name}" for name in EXCLUDED_CORRUPT_ASSETS
    ),
    "generationPolicy": (
        "Historical recovery split only. Known corrupt historical assets are excluded from the active recovery output; "
        "future edits belong in cone/page-N.html; preserved source remains immutable. "
        "content-manifest.json alone controls release order."
    ),
}
(TARGET / "manifest.json").write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

# Structural smoke checks on generated pages and local assets.
for number in range(1, 47):
    page_path = TARGET / f"page-{number}.html"
    text = page_path.read_text(encoding="utf-8")
    if text.count("<main") != 1 or f'data-local-page="{number}"' not in text:
        fail(f"page-{number}.html does not contain exactly its expected A4 main")

for required in [
    TARGET / "assets/ayelet-original-cone.png",
    TARGET / "visual-assets/cone-3d-upright.svg",
    TARGET / "visual-assets/world-of-cones.jpg",
]:
    if not required.is_file():
        fail(f"required generated asset missing: {required.relative_to(ROOT)}")

for excluded in EXCLUDED_CORRUPT_ASSETS:
    if (TARGET / "visual-assets" / excluded).exists():
        fail(f"corrupt historical asset leaked into recovery output: visual-assets/{excluded}")

print(
    "OK: generated the 46-page historical recovery split without overwriting existing content or copying known corrupt assets. "
    "This output is not release-ready until canonical edits are reapplied and "
    "scripts/check-cone-package.py plus the full release renderer pass."
)
