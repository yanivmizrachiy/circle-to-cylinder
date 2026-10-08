from pathlib import Path

render_path = Path("scripts/render-release.py")
render = render_path.read_text(encoding="utf-8")

old_import = "import urllib.parse\n\nfrom pypdf import PdfReader, PdfWriter"
new_import = "import urllib.parse\n\nfrom release_fingerprint import compute_release_fingerprint\nfrom pypdf import PdfReader, PdfWriter"
if old_import not in render:
    raise SystemExit("render import anchor changed")
render = render.replace(old_import, new_import, 1)

old_compress = "writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)"
new_compress = "writer.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)"
if old_compress not in render:
    raise SystemExit("render compression anchor changed")
render = render.replace(old_compress, new_compress, 1)

old_write = '''            pathlib.Path(output_pdf).parent.mkdir(parents=True, exist_ok=True)\n            with pathlib.Path(output_pdf).open("wb") as handle:\n                writer.write(handle)\n\n            final_count = len(PdfReader(str(output_pdf)).pages)\n'''
new_write = '''            source_fingerprint = compute_release_fingerprint(ROOT)\n            writer.add_metadata(\n                {\n                    "/WorkbookSourceSHA256": source_fingerprint,\n                    "/WorkbookPageCount": str(len(pages)),\n                }\n            )\n            pathlib.Path(output_pdf).parent.mkdir(parents=True, exist_ok=True)\n            with pathlib.Path(output_pdf).open("wb") as handle:\n                writer.write(handle)\n\n            final_count = len(PdfReader(str(output_pdf)).pages)\n'''
if old_write not in render:
    raise SystemExit("render write anchor changed")
render = render.replace(old_write, new_write, 1)

old_report = '''            report["status"] = "passed"\n            report["pdfPages"] = final_count\n            report["errors"] = []\n'''
new_report = '''            report["status"] = "passed"\n            report["pdfPages"] = final_count\n            report["sourceFingerprint"] = source_fingerprint\n            report["errors"] = []\n'''
if old_report not in render:
    raise SystemExit("render report anchor changed")
render = render.replace(old_report, new_report, 1)
render_path.write_text(render, encoding="utf-8")

check_path = Path("scripts/check-content.py")
check = check_path.read_text(encoding="utf-8")
old_import = "from pypdf import PdfReader\n"
new_import = "from pypdf import PdfReader\n\nfrom release_fingerprint import compute_release_fingerprint\n"
if old_import not in check:
    raise SystemExit("check import anchor changed")
check = check.replace(old_import, new_import, 1)

old_pdf = '''# The downloadable PDF must be derived from and match the active manifest page count.\npdf_path = root / "assets/circle-to-cylinder.pdf"\nif not pdf_path.is_file():\n    errors.append("downloadable PDF is missing: assets/circle-to-cylinder.pdf")\nelse:\n    try:\n        pdf_pages = len(PdfReader(str(pdf_path)).pages)\n    except Exception as exc:\n        errors.append(f"downloadable PDF cannot be read: {exc}")\n    else:\n        if pdf_pages != len(listed):\n            errors.append(\n                f"downloadable PDF page count mismatch: {pdf_pages} != active manifest {len(listed)}"\n            )\n'''
new_pdf = '''# The downloadable PDF must match both the active page count and the exact\n# repository-local sources/assets that can affect the rendered workbook.\npdf_path = root / "assets/circle-to-cylinder.pdf"\nif not pdf_path.is_file():\n    errors.append("downloadable PDF is missing: assets/circle-to-cylinder.pdf")\nelse:\n    try:\n        pdf_reader = PdfReader(str(pdf_path))\n        pdf_pages = len(pdf_reader.pages)\n        pdf_metadata = pdf_reader.metadata or {}\n    except Exception as exc:\n        errors.append(f"downloadable PDF cannot be read: {exc}")\n    else:\n        if pdf_pages != len(listed):\n            errors.append(\n                f"downloadable PDF page count mismatch: {pdf_pages} != active manifest {len(listed)}"\n            )\n        expected_fingerprint = compute_release_fingerprint(root)\n        actual_fingerprint = pdf_metadata.get("/WorkbookSourceSHA256")\n        if actual_fingerprint != expected_fingerprint:\n            errors.append(\n                "downloadable PDF source fingerprint mismatch: "\n                f"{actual_fingerprint!r} != {expected_fingerprint!r}; rebuild the PDF from current sources"\n            )\n        declared_count = pdf_metadata.get("/WorkbookPageCount")\n        if declared_count != str(len(listed)):\n            errors.append(\n                f"downloadable PDF metadata page count mismatch: {declared_count!r} != {len(listed)!r}"\n            )\n'''
if old_pdf not in check:
    raise SystemExit("check PDF anchor changed")
check = check.replace(old_pdf, new_pdf, 1)
check_path.write_text(check, encoding="utf-8")
