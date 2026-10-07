import json, pathlib, sys
root=pathlib.Path(__file__).resolve().parents[1]
m=json.loads((root/"content-manifest.json").read_text(encoding="utf-8"))
circle=json.loads((root/"maagal/manifest.json").read_text(encoding="utf-8"))
listed=[]
for sec in m["sections"]:
    for p in sec.get("pages",[]): listed.append(p)
    for r in sec.get("ranges",[]):
        end=r.get("to")
        if r.get("toManifest"): end=int(circle.get("pageCount",99))
        for n in range(int(r["from"]),int(end)+1): listed.append(f'{r["prefix"]}{n}{r.get("suffix","")}')
missing=[p for p in listed if not (root/p).is_file()]
expected_gold={p for p in listed if p.startswith("gold/")}
actual_gold={p.relative_to(root).as_posix() for p in (root/"gold").glob("page-*.html")}
unlisted=sorted(actual_gold-expected_gold)
if missing or unlisted:
    print("CONTENT INTEGRITY FAILED")
    if missing: print("Missing listed pages:", *missing, sep="\n- ")
    if unlisted: print("Unlisted gold pages:", *unlisted, sep="\n- ")
    sys.exit(1)
ids=[s["id"] for s in m["sections"]]
if ids != ["circle","cylinder","cone"] or not next(s for s in m["sections"] if s["id"]=="cone").get("pages"):
    print("CONTENT INTEGRITY FAILED: cone section missing/empty"); sys.exit(1)
print(f"OK: {len(listed)} pages; cone protected; no unlisted gold pages.")
