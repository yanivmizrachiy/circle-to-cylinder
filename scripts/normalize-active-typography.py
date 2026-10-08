import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]

UNIT_REPLACEMENTS = {
    "ס״מ²": "סמ״ר",
    "ס״מ³": "סמ״ק",
    'ס"מ²': "סמ״ר",
    'ס"מ³': "סמ״ק",
}


def replace_units(text: str) -> str:
    for old, new in UNIT_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def rewrite(path: pathlib.Path, transform):
    before = path.read_text(encoding="utf-8")
    after = transform(before)
    if after != before:
        path.write_text(after, encoding="utf-8")
        print(f"updated {path.relative_to(ROOT).as_posix()}")
        return 1
    return 0


def normalize_direct_pages():
    changed = 0
    for folder in ("cone", "galil", "gold"):
        for path in sorted((ROOT / folder).glob("page-*.html")):
            changed += rewrite(path, replace_units)
    return changed


def normalize_circle_loaders():
    changed = 0
    needle = "const doc=new DOMParser().parseFromString(raw,'text/html');"
    injection = (
        needle
        + "doc.body.innerHTML=doc.body.innerHTML"
        + ".replaceAll('ס״מ²','סמ״ר').replaceAll('ס״מ³','סמ״ק')"
        + ".replaceAll('ס\"מ²','סמ״ר').replaceAll('ס\"מ³','סמ״ק');"
    )
    marker = ".replaceAll('ס״מ²','סמ״ר')"
    for path in sorted((ROOT / "maagal").glob("page-*.html")):
        def transform(text):
            if marker in text:
                return text
            if needle not in text:
                raise RuntimeError(f"circle loader shape changed: {path}")
            return text.replace(needle, injection, 1)
        changed += rewrite(path, transform)
    return changed


def fix_gold_prompts():
    replacements = {
        "gold/page-6.html": {
            "באיזה משולש הצלע המודגשת היא הקצרה ביותר, ובאיזה היא הארוכה ביותר?":
                "קבעו באיזה משולש הצלע המודגשת היא הקצרה ביותר ובאיזה היא הארוכה ביותר:",
        },
        "gold/page-7.html": {
            "איזו צנצנת כדאי לקנות — המחיר הזול ביותר ליחידת נפח?":
                "קבעו איזו צנצנת כדאי לקנות לפי המחיר ליחידת נפח:",
            "מגלגלים כך שהרוחב (21 ס״מ) הוא היקף הבסיס — מהו רדיוס הבסיס ומהו נפח הגליל?":
                "מגלגלים כך שהרוחב (21 ס״מ) הוא היקף הבסיס — חשבו את רדיוס הבסיס ואת נפח הגליל:",
            "מגלגלים כך שהאורך (30 ס״מ) הוא היקף הבסיס — מהו רדיוס הבסיס ומהו נפח הגליל?":
                "מגלגלים כך שהאורך (30 ס״מ) הוא היקף הבסיס — חשבו את רדיוס הבסיס ואת נפח הגליל:",
        },
        "gold/page-8.html": {
            "הבעלים טוען שבשתיהן הנפח יגדל באותה מידה. האם צודק?":
                "הבעלים טוען שבשתיהן הנפח יגדל באותה מידה. קבעו אם הטענה נכונה ונמקו:",
            ">h = ?</text>": ">h</text>",
        },
    }
    changed = 0
    for rel, mapping in replacements.items():
        path = ROOT / rel
        def transform(text):
            for old, new in mapping.items():
                text = text.replace(old, new)
            return text
        changed += rewrite(path, transform)
    return changed


def fix_stale_ssot_comment():
    path = ROOT / "maagal/styles.css"
    old = "/* ===== כללי עיצוב אחידים — כל הדפים (SSOT: manifest.json → designRules, 2026-10-05) ===== */"
    new = "/* ===== כללי עיצוב אחידים — מונחה RULES.md; manifest.json משמש ניתוב מקומי בלבד ===== */"
    return rewrite(path, lambda text: text.replace(old, new))


def add_content_guards():
    path = ROOT / "scripts/check-content.py"
    marker = "# Active typography/prompt policy guard."
    anchor = "# The downloadable PDF must be derived from and match the active manifest page count."
    block = r'''# Active typography/prompt policy guard.
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

'''
    def transform(text):
        if marker in text:
            return text
        if anchor not in text:
            raise RuntimeError("check-content insertion anchor changed")
        return text.replace(anchor, block + anchor, 1)
    return rewrite(path, transform)


def optimize_pdf_merge_code():
    path = ROOT / "scripts/render-release.py"
    marker = "compress_identical_objects"
    anchor = "            pathlib.Path(output_pdf).parent.mkdir(parents=True, exist_ok=True)\n"
    insert = (
        "            # Lossless de-duplication of repeated fonts/images/resources from 192 one-page PDFs.\n"
        "            if hasattr(writer, \"compress_identical_objects\"):\n"
        "                writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)\n"
    )
    def transform(text):
        if marker in text:
            return text
        if anchor not in text:
            raise RuntimeError("render-release insertion anchor changed")
        return text.replace(anchor, insert + anchor, 1)
    return rewrite(path, transform)


def main():
    changed = 0
    changed += normalize_direct_pages()
    changed += normalize_circle_loaders()
    changed += fix_gold_prompts()
    changed += fix_stale_ssot_comment()
    changed += add_content_guards()
    changed += optimize_pdf_merge_code()
    print(f"done: {changed} files updated")


if __name__ == "__main__":
    main()
