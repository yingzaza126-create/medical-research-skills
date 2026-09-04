#!/usr/bin/env python3
"""
fill_prisma.py -- inject audited counts into the official PRISMA 2020
flow-diagram template `1Fig.PRISMA_2020_flow_diagram_SRs.docx`
(BMJ 2021;372:n71, CC BY 4.0) without disturbing the layout.

Each box in this template carries a `(n = )` placeholder. Because the
template stores every shape twice -- once as modern DrawingML and once as a
VML fallback -- there are 30 placeholders for 15 logical boxes. This script
fills BOTH copies of every box so the number shows in any Word renderer,
matching them by fixed document order (verified against this template).

Input: a JSON file of audited counts (all optional; anything omitted is left
blank). NOTHING is inferred except the reconciliation warnings printed at the
end -- the numbers you supply are written verbatim.

    {
      "databases": 1240, "registers": 0,
      "duplicates_removed": 210, "automation_removed": 0, "other_removed": 0,
      "records_screened": 1030, "records_excluded": 935,
      "reports_sought": 95, "reports_not_retrieved": 4,
      "reports_assessed": 91,
      "reasons": [ {"label": "Wrong outcome", "n": 40},
                   {"label": "Wrong design",  "n": 30},
                   {"label": "Conference abstract", "n": 9} ],
      "studies_included": 12, "reports_included": 15
    }

Usage:
    python fill_prisma.py \
        --template assets/templates/1Fig.PRISMA_2020_flow_diagram_SRs.docx \
        --counts prisma_counts.json \
        --out 1Fig.PRISMA_2020_flow_diagram_SRs_FILLED.docx
"""
import argparse
import json
import re
import shutil
import zipfile

# document-order key for each of the 30 placeholders (Choice + Fallback pairs)
ORDER = [
    "duplicates_removed", "automation_removed", "other_removed",   # box1 choice
    "duplicates_removed", "automation_removed", "other_removed",   # box1 fallback
    "databases", "registers",                                      # box2 choice
    "databases", "registers",                                      # box2 fallback
    "records_screened", "records_screened",
    "records_excluded", "records_excluded",
    "reports_sought", "reports_sought",
    "reports_not_retrieved", "reports_not_retrieved",
    "reports_assessed", "reports_assessed",
    "reason1", "reason2", "reason3",                               # box choice
    "reason1", "reason2", "reason3",                               # box fallback
    "studies_included", "reports_included",                       # box choice
    "studies_included", "reports_included",                       # box fallback
]

PLACEHOLDER = re.compile(r'<w:t([^>]*)>( ?)= \)</w:t>')


def val_map(counts):
    m = dict(counts)
    reasons = counts.get("reasons") or []
    for i in range(3):
        m[f"reason{i+1}"] = reasons[i]["n"] if i < len(reasons) else None
    return m


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--template", required=True)
    ap.add_argument("--counts", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    counts = json.load(open(a.counts, encoding="utf-8"))
    vmap = val_map(counts)

    with zipfile.ZipFile(a.template) as z:
        xml = z.read("word/document.xml").decode("utf-8")

    matches = list(PLACEHOLDER.finditer(xml))
    if len(matches) != len(ORDER):
        raise SystemExit(
            f"Expected {len(ORDER)} '(n = )' placeholders but found "
            f"{len(matches)}. Template differs from the bundled PRISMA 2020 "
            f"template -- aborting to avoid corrupting it.")

    # rebuild xml, replacing each placeholder in order
    out, last, filled = [], 0, 0
    for i, mt in enumerate(matches):
        key = ORDER[i]
        v = vmap.get(key)
        out.append(xml[last:mt.start()])
        attr, lead = mt.group(1), mt.group(2)
        if v not in (None, ""):
            out.append(f'<w:t{attr}>{lead}= {v} )</w:t>')
            filled += 1
        else:
            out.append(mt.group(0))
        last = mt.end()
    out.append(xml[last:])
    xml = "".join(out)

    # optional: relabel the three generic exclusion reasons
    for i, r in enumerate(counts.get("reasons") or [], 1):
        lbl = r.get("label")
        if lbl:
            safe = lbl.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            xml = re.sub(rf'>Reason {i} \(<', f'>{safe} (<', xml)

    # write new docx
    shutil.copyfile(a.template, a.out)
    # rewrite the single entry
    import os
    tmp = a.out + ".tmp"
    with zipfile.ZipFile(a.template) as zin, \
            zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = xml.encode("utf-8")
            zout.writestr(item, data)
    os.replace(tmp, a.out)

    print(f"Filled {filled}/30 placeholders ({filled//2} box(es)) -> {a.out}")

    # ---- PRISMA reconciliation (report only) ----
    def n(k):
        try:
            return float(counts.get(k))
        except (TypeError, ValueError):
            return None

    def _num_or_zero(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return 0
    reasons_total = sum(_num_or_zero(r.get("n")) for r in (counts.get("reasons") or []))
    ident = (n("databases") or 0) + (n("registers") or 0)
    removed = (n("duplicates_removed") or 0) + (n("automation_removed") or 0) + (n("other_removed") or 0)
    warn = []

    def chk(label, lhs, rhs):
        if lhs is not None and rhs is not None and abs(lhs - rhs) > 1e-9:
            warn.append(f"{label}: {lhs:g} != {rhs:g}")

    if n("records_screened") is not None and (n("databases") or n("registers")):
        chk("records_screened = identified - removed_before_screening",
            n("records_screened"), ident - removed)
    if None not in (n("records_screened"), n("records_excluded"), n("reports_sought")):
        chk("records_screened = records_excluded + reports_sought",
            n("records_screened"), n("records_excluded") + n("reports_sought"))
    if None not in (n("reports_sought"), n("reports_not_retrieved"), n("reports_assessed")):
        chk("reports_sought = not_retrieved + assessed",
            n("reports_sought"), n("reports_not_retrieved") + n("reports_assessed"))
    if n("reports_assessed") is not None and n("reports_included") is not None:
        chk("reports_assessed = reasons_excluded_total + reports_included",
            n("reports_assessed"), reasons_total + n("reports_included"))
    if None not in (n("studies_included"), n("reports_included")) and \
            n("studies_included") > n("reports_included"):
        warn.append(f"studies_included ({n('studies_included'):g}) > "
                    f"reports_included ({n('reports_included'):g}) -- "
                    "a study cannot have fewer reports than itself")

    if warn:
        print("\nPRISMA ARITHMETIC FLAGS -- verify against screening audit trail:")
        for w in warn:
            print("  FLAG:", w)
    else:
        print("PRISMA arithmetic: consistent (for the counts supplied).")


if __name__ == "__main__":
    main()
