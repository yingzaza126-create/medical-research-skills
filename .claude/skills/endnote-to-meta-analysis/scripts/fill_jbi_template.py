#!/usr/bin/env python3
"""
fill_jbi_template.py -- write JBI critical-appraisal results into
`1S1_Table_JBI_Quality_Appraisal.xlsx`, preserving the template's title
rows and two-row header (rows 1-4). Data is written from row 5 down.

The template's fixed layout (do not change):
    A Study (#)      B Author, Year   C Study Design   D JBI Tool Used
    E-J Core appraisal domains (row-4 sub-labels):
        E Eligibility Criteria         F Participants Representative
        G Exposure Measured Validly    H Confounders Identified
        I Outcomes Measured Validly    J Statistical Analysis Appropriate
    K Additional Domains Met   L Total Items Applicable   M Items Met (Yes)
    N JBI Score (%)            O Quality Rating

Input CSV/JSON keys (any missing key -> left blank):
    Study, Author_Year, Study_Design, JBI_Tool,
    Domain_1..Domain_6            (Y / N / Unclear / NA -- per checklist item)
    Additional_Domains_Met, Total_Items_Applicable, Items_Met,
    JBI_Score, Quality_Rating

Rules honoured:
    * JBI_Score is arithmetic: if left blank AND Items_Met + Total_Items_
      Applicable are numeric, it is computed = round(100*Items/Total).
      Nothing else is derived.
    * Quality_Rating is NEVER auto-assigned (no official universal % cut-off);
      it is written only if supplied. Use --rating-cutoffs to opt in.
    * A domain must be graded from evidence in the source; this script only
      transcribes what you provide. Blank domains stay blank (=> Unclear/NR
      is your call, recorded in your input).

Usage:
    python fill_jbi_template.py \
        --template assets/templates/1S1_Table_JBI_Quality_Appraisal.xlsx \
        --data jbi_appraisal.csv \
        --out  1S1_Table_JBI_Quality_Appraisal_FILLED.xlsx
"""
import argparse
import csv
import json

import openpyxl
from openpyxl.cell.cell import MergedCell

COLS = {
    "Study": 1, "Author_Year": 2, "Study_Design": 3, "JBI_Tool": 4,
    "Domain_1": 5, "Domain_2": 6, "Domain_3": 7, "Domain_4": 8,
    "Domain_5": 9, "Domain_6": 10, "Additional_Domains_Met": 11,
    "Total_Items_Applicable": 12, "Items_Met": 13, "JBI_Score": 14,
    "Quality_Rating": 15,
}


def load_data(path):
    if path.lower().endswith(".json"):
        return json.load(open(path, encoding="utf-8"))
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        return float(str(v))
    except (ValueError, TypeError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--template", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--start-row", type=int, default=5)
    ap.add_argument("--rating-cutoffs", default="",
                    help="optional 'high,moderate' %% cut-offs, e.g. '80,50' "
                         "to derive Quality_Rating from JBI_Score when blank")
    a = ap.parse_args()

    cut = None
    if a.rating_cutoffs:
        hi, mod = (float(x) for x in a.rating_cutoffs.split(","))
        cut = (hi, mod)

    wb = openpyxl.load_workbook(a.template)
    ws = wb.active
    rows = load_data(a.data)

    # rows that contain merged cells (e.g. a footnote row) are left untouched
    merged_rows = {cr.min_row for cr in ws.merged_cells.ranges}

    def put(r, c, v):
        cell = ws.cell(r, c)
        if isinstance(cell, MergedCell):
            return False
        cell.value = v
        return True

    # clear existing example/placeholder value cells (keep formatting) below header
    for r in range(a.start_row, ws.max_row + 1):
        if r in merged_rows:
            continue
        for c in range(1, 16):
            put(r, c, None)

    r_out = a.start_row
    flags = []
    for i, rec in enumerate(rows, 1):
        if "Study" not in rec or rec.get("Study") in (None, ""):
            rec["Study"] = i
        # arithmetic score only
        if not rec.get("JBI_Score"):
            im, ta = num(rec.get("Items_Met")), num(rec.get("Total_Items_Applicable"))
            if im is not None and ta and ta > 0:
                if im > ta:
                    flags.append(f"row {r_out}: Items_Met {im} > Total {ta}")
                rec["JBI_Score"] = round(100 * im / ta)
        if cut and not rec.get("Quality_Rating") and num(rec.get("JBI_Score")) is not None:
            s = num(rec["JBI_Score"])
            rec["Quality_Rating"] = ("High" if s >= cut[0]
                                     else "Moderate" if s >= cut[1] else "Low")
        if r_out in merged_rows:
            flags.append(f"row {r_out}: skipped (merged footer row); "
                         "increase template rows if more studies are needed")
            r_out += 1
            continue
        for key, col in COLS.items():
            if key in rec and rec[key] not in (None, ""):
                put(r_out, col, rec[key])
        r_out += 1

    wb.save(a.out)
    print(f"Wrote {r_out - a.start_row} appraisal row(s) -> {a.out}")
    if not cut:
        print("Quality_Rating written only where supplied "
              "(no cut-offs given; pass --rating-cutoffs to derive it).")
    if flags:
        print(f"\nVALIDATION FLAGS ({len(flags)}):")
        for fl in flags:
            print("  FLAG:", fl)


if __name__ == "__main__":
    main()
