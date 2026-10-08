import argparse
import hashlib
import json
import pathlib
import sys

from pypdf import PdfReader

ROOT = pathlib.Path(__file__).resolve().parents[1]
PDF_PATH = ROOT / "assets/circle-to-cylinder.pdf"
LOCK_PATH = ROOT / "assets/circle-to-cylinder.pdf.lock.json"
EXPECTED_PAGES = 192

SOURCE_FILES = [
    ROOT / "content-manifest.json",
    ROOT / "scripts/render-release.py",
]
SOURCE_DIRS = [
    ROOT / "maagal",
    ROOT / "galil",
    ROOT / "cone",
    ROOT / "gold",
]


def _iter_release_source_files():
    files = list(SOURCE_FILES)
    for directory in SOURCE_DIRS:
        files.extend(path for path in directory.rglob("*") if path.is_file())
    unique = {path.resolve(): path for path in files}
    return sorted(unique.values(), key=lambda p: p.relative_to(ROOT).as_posix())


def _sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in _iter_release_source_files():
        rel = path.relative_to(ROOT).as_posix().encode("utf-8")
        data = path.read_bytes()
        digest.update(len(rel).to_bytes(4, "big"))
        digest.update(rel)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def build_lock():
    if not PDF_PATH.is_file():
        raise RuntimeError(f"missing PDF: {PDF_PATH.relative_to(ROOT)}")
    pages = len(PdfReader(str(PDF_PATH)).pages)
    if pages != EXPECTED_PAGES:
        raise RuntimeError(f"PDF has {pages} pages, expected {EXPECTED_PAGES}")
    return {
        "version": 1,
        "sourceFingerprintSha256": source_fingerprint(),
        "pdfSha256": _sha256_file(PDF_PATH),
        "pdfPages": pages,
        "sourceFileCount": len(_iter_release_source_files()),
    }


def write_lock():
    lock = build_lock()
    LOCK_PATH.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "OK: wrote release lock "
        f"source={lock['sourceFingerprintSha256'][:12]}… "
        f"pdf={lock['pdfSha256'][:12]}… pages={lock['pdfPages']}"
    )


def check_lock():
    if not LOCK_PATH.is_file():
        raise RuntimeError(f"missing release lock: {LOCK_PATH.relative_to(ROOT)}")
    try:
        recorded = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"release lock is unreadable: {exc}") from exc

    current = build_lock()
    errors = []
    for key in ("version", "sourceFingerprintSha256", "pdfSha256", "pdfPages"):
        if recorded.get(key) != current.get(key):
            errors.append(f"{key}: recorded={recorded.get(key)!r} current={current.get(key)!r}")
    if errors:
        raise RuntimeError(
            "release PDF/source lock mismatch; regenerate the verified release:\n- "
            + "\n- ".join(errors)
        )
    print(
        "OK: committed PDF is locked to the current release sources "
        f"({current['pdfPages']} pages, source={current['sourceFingerprintSha256'][:12]}…)."
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("write", "check"))
    args = parser.parse_args()
    try:
        if args.mode == "write":
            write_lock()
        else:
            check_lock()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
