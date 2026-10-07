import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "content-manifest.json"
errors = []

if not MANIFEST.is_file():
    errors.append("content-manifest.json is missing")
    manifest = {}
else:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

if manifest.get("version") != 3:
    errors.append("content-manifest.json version must be 3 for the self-contained release SSOT")

sections = manifest.get("sections") or []
if [section.get("id") for section in sections] != ["circle", "cylinder", "cone"]:
    errors.append("release sections must be exactly circle, cylinder, cone")

actual = []
for section in sections:
    for page_range in section.get("ranges", []):
        if "toManifest" in page_range:
            errors.append(
                f"release SSOT must be self-contained; toManifest is forbidden in {section.get('id')}"
            )
            continue
        if page_range.get("to") is None:
            errors.append(f"release range in {section.get('id')} has no explicit 'to'")
            continue
        start = int(page_range.get("from", 0))
        end = int(page_range["to"])
        if start < 1 or end < start:
            errors.append(f"invalid release range in {section.get('id')}: {start}..{end}")
            continue
        for number in range(start, end + 1):
            actual.append(f"{page_range['prefix']}{number}{page_range.get('suffix', '')}")
    actual.extend(section.get("pages", []))

expected = (
    [f"maagal/page-{n}.html" for n in range(1, 100)]
    + [f"gold/page-{n}.html" for n in range(1, 8)]
    + [f"galil/page-{n}.html" for n in range(1, 40)]
    + [f"cone/page-{n}.html" for n in range(1, 47)]
    + ["gold/page-8.html"]
)

if actual != expected:
    errors.append("content-manifest.json does not match the exact canonical 192-page release sequence")

if len(actual) != 192:
    errors.append(f"release SSOT expands to {len(actual)} pages instead of 192")

if len(set(actual)) != len(actual):
    errors.append("release SSOT contains duplicate page paths")

for page in actual:
    if "://" in page or page.startswith("/") or ".." in pathlib.PurePosixPath(page).parts:
        errors.append(f"release SSOT contains a non-local path: {page}")
    elif not (ROOT / page).is_file():
        errors.append(f"release SSOT points to a missing page: {page}")

if errors:
    print("RELEASE SSOT FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("OK: content-manifest.json is the self-contained release SSOT for the exact 192-page sequence.")
