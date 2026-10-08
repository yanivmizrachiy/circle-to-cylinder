import hashlib
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Files that can change the rendered workbook/PDF. Documentation and preserved
# source outside the active workbook trees are intentionally excluded.
ACTIVE_ROOTS = ("maagal", "galil", "cone", "gold")
ACTIVE_SUFFIXES = {
    ".html",
    ".css",
    ".js",
    ".json",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
}
ROOT_INPUTS = (
    "content-manifest.json",
    "scripts/render-release.py",
    "scripts/release_fingerprint.py",
)


def iter_release_inputs(root=ROOT):
    root = pathlib.Path(root)
    paths = []
    for relative in ROOT_INPUTS:
        path = root / relative
        if path.is_file():
            paths.append(path)
    for dirname in ACTIVE_ROOTS:
        base = root / dirname
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in ACTIVE_SUFFIXES:
                paths.append(path)
    return sorted(set(paths), key=lambda p: p.relative_to(root).as_posix())


def compute_release_fingerprint(root=ROOT):
    root = pathlib.Path(root)
    digest = hashlib.sha256()
    for path in iter_release_inputs(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        data = path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()
