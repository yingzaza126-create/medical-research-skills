#!/usr/bin/env python3
"""
parse_endnote.py  --  EndNote / citation-manager reference normalizer.

Reads an EndNote export (EndNote XML `.xml`, RIS `.ris`, PubMed `.nbib`,
EndNote `.enw`) and produces ONE normalized record per bibliographic
reference, plus a deduplication report. It does NOT screen, extract outcome
data, or invent anything -- it only inventories bibliographic identity so a
human/AI reviewer can proceed with PRISMA screening.

Deduplication key priority (per master methodology, section 4):
    1. DOI
    2. PMID
    3. Exact title + year
    4. Title(normalized) + first author + year

Output:
    - <out>.csv   one row per reference (canonical record)
    - <out>.json  same data as JSON list
    - prints an INVENTORY summary + duplicate clusters to stdout

Usage:
    python parse_endnote.py INPUT.xml --out references
    python parse_endnote.py INPUT.ris --out references

Records are flagged, never silently dropped. Duplicate clusters are reported
for HUMAN confirmation before any record is removed from screening counts.
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict

FIELDS = [
    "Ref_ID", "dedup_key", "dup_cluster", "first_author", "authors", "year",
    "title", "journal", "volume", "issue", "pages", "doi", "pmid", "pmcid",
    "url", "ref_type", "abstract_available", "fulltext_pdf", "keywords",
    "flags",
]


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


# ---------------------------------------------------------------- EndNote XML
def parse_endnote_xml(path):
    from lxml import etree
    tree = etree.parse(path)
    out = []
    for rec in tree.findall(".//record"):
        def g(p):
            el = rec.find(p)
            return "".join(el.itertext()).strip() if el is not None else ""

        authors = ["".join(a.itertext()).strip()
                   for a in rec.findall("contributors/authors/author")]
        # EndNote sometimes crams all authors into one node -> split on caps runs
        if len(authors) == 1 and len(authors[0]) > 80 and "," not in authors[0]:
            pass  # leave as-is; flagged below
        rt = rec.find("ref-type")
        ref_type = rt.get("name", "") if rt is not None else ""
        urls = g("urls")
        pdf = "internal-pdf" in urls or ".pdf" in urls.lower()
        out.append({
            "first_author": authors[0] if authors else "",
            "authors": "; ".join(authors),
            "year": g("dates/year"),
            "title": g("titles/title"),
            "journal": (g("titles/secondary-title")
                        or g("periodical/full-title")),
            "volume": g("volume"),
            "issue": g("number"),
            "pages": g("pages"),
            "doi": g("electronic-resource-num"),
            "pmid": g("accession-num"),
            "pmcid": g("custom2"),
            "url": urls,
            "ref_type": ref_type,
            "abstract_available": "Y" if g("abstract") else "NR",
            "fulltext_pdf": "Y" if pdf else "NR",
            "keywords": "; ".join(k.text or "" for k in
                                  rec.findall("keywords/keyword")),
        })
    return out


# ---------------------------------------------------------------- RIS / nbib / enw
def parse_tagged(path, sep_re):
    text = open(path, encoding="utf-8", errors="replace").read()
    records, cur = [], defaultdict(list)
    for line in text.splitlines():
        m = sep_re.match(line)
        if m:
            tag, val = m.group(1).strip(), m.group(2).strip()
            if tag in ("ER", "") and cur:
                records.append(cur)
                cur = defaultdict(list)
            elif tag:
                cur[tag].append(val)
    if cur:
        records.append(cur)
    return records


def parse_ris(path):
    sep = re.compile(r"^([A-Z0-9]{2})\s+-\s*(.*)$")
    out = []
    for r in parse_tagged(path, sep):
        au = r.get("AU") or r.get("A1") or []
        doi = (r.get("DO") or r.get("DOI") or [""])[0]
        out.append(_std(au, (r.get("PY") or r.get("Y1") or [""])[0][:4],
                        (r.get("TI") or r.get("T1") or [""])[0],
                        (r.get("JO") or r.get("JF") or r.get("T2") or [""])[0],
                        (r.get("VL") or [""])[0], (r.get("IS") or [""])[0],
                        (r.get("SP") or [""])[0], doi,
                        (r.get("AN") or [""])[0], "",
                        (r.get("UR") or r.get("L1") or [""])[0],
                        (r.get("TY") or [""])[0],
                        r.get("AB"), r.get("KW"),
                        bool(r.get("L1") or r.get("UR"))))
    return out


def parse_nbib(path):
    sep = re.compile(r"^([A-Z]{2,4})\s*-\s*(.*)$")
    out = []
    for r in parse_tagged(path, sep):
        out.append(_std(r.get("AU") or r.get("FAU") or [], (r.get("DP") or [""])[0][:4],
                        " ".join(r.get("TI") or []), (r.get("JT") or r.get("TA") or [""])[0],
                        (r.get("VI") or [""])[0], (r.get("IP") or [""])[0],
                        (r.get("PG") or [""])[0],
                        next((x.split()[0] for x in (r.get("AID") or []) if "doi" in x.lower()), ""),
                        (r.get("PMID") or [""])[0], (r.get("PMC") or [""])[0], "",
                        "Journal Article", r.get("AB"), r.get("OT"), False))
    return out


def parse_enw(path):
    sep = re.compile(r"^%([A-Z0-9])\s+(.*)$")
    out = []
    for r in parse_tagged(path, sep):
        out.append(_std(r.get("A") or [], (r.get("D") or [""])[0][:4],
                        " ".join(r.get("T") or []), (r.get("J") or r.get("B") or [""])[0],
                        (r.get("V") or [""])[0], (r.get("N") or [""])[0],
                        (r.get("P") or [""])[0], (r.get("R") or [""])[0],
                        (r.get("M") or [""])[0], "", (r.get("U") or [""])[0],
                        (r.get("0") or ["Journal Article"])[0], r.get("X"), r.get("K"), False))
    return out


def _std(au, yr, ti, jo, vl, iss, sp, doi, pmid, pmcid, url, rt, ab, kw, pdf):
    return {
        "first_author": au[0] if au else "", "authors": "; ".join(au),
        "year": yr, "title": ti, "journal": jo, "volume": vl, "issue": iss,
        "pages": sp, "doi": re.sub(r"^https?://(dx\.)?doi\.org/", "", doi or "").strip(),
        "pmid": pmid, "pmcid": pmcid, "url": url, "ref_type": rt,
        "abstract_available": "Y" if ab else "NR",
        "fulltext_pdf": "Y" if pdf else "NR",
        "keywords": "; ".join(kw or []),
    }


# ---------------------------------------------------------------- dedup + flags
def build_dedup(records):
    for i, r in enumerate(records, 1):
        r["Ref_ID"] = f"REF{i:03d}"
        doi = (r.get("doi") or "").lower().strip()
        pmid = (r.get("pmid") or "").strip()
        if doi:
            key = f"doi:{doi}"
        elif pmid and pmid.isdigit():
            key = f"pmid:{pmid}"
        elif r.get("title") and r.get("year"):
            key = f"ty:{norm_title(r['title'])}|{r['year']}"
        elif r.get("title"):
            key = f"taf:{norm_title(r['title'])}|{(r.get('first_author') or '').lower()}|{r.get('year')}"
        else:
            key = f"noid:{r['Ref_ID']}"
        r["dedup_key"] = key

    clusters = defaultdict(list)
    for r in records:
        clusters[r["dedup_key"]].append(r["Ref_ID"])
    cid = {}
    n = 0
    for key, ids in clusters.items():
        if len(ids) > 1:
            n += 1
            cid[key] = f"DUP{n:02d}"
    for r in records:
        r["dup_cluster"] = cid.get(r["dedup_key"], "")
        flags = []
        if not r.get("title"):
            flags.append("MISSING_TITLE")
        if not r.get("year"):
            flags.append("MISSING_YEAR")
        if not r.get("doi") and not (r.get("pmid") or "").isdigit():
            flags.append("NO_DOI_NO_PMID")
        if r.get("authors") and ";" not in r["authors"] and len(r["authors"]) > 90:
            flags.append("AUTHORS_UNSPLIT")
        if r["dup_cluster"]:
            flags.append(f"POSSIBLE_DUPLICATE:{r['dup_cluster']}")
        r["flags"] = "; ".join(flags)
    return records, cid


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--out", default="references", help="output basename")
    a = ap.parse_args()
    ext = a.input.lower().rsplit(".", 1)[-1]
    parser = {"xml": parse_endnote_xml, "ris": parse_ris, "nbib": parse_nbib,
              "enw": parse_enw, "txt": parse_ris}.get(ext)
    if not parser:
        sys.exit(f"Unsupported extension .{ext}. Use xml/ris/nbib/enw.")
    records = parser(a.input)
    records, clusters = build_dedup(records)

    with open(a.out + ".csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in records:
            w.writerow(r)
    with open(a.out + ".json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    n = len(records)
    dup_extra = n - len({r["dedup_key"] for r in records})
    print("=" * 60)
    print("ENDNOTE INVENTORY (Phase A)")
    print("=" * 60)
    print(f"Input file            : {a.input}")
    print(f"Records identified    : {n}")
    print(f"Unique dedup keys     : {len({r['dedup_key'] for r in records})}")
    print(f"Potential duplicates  : {dup_extra} extra record(s) in "
          f"{len(clusters)} cluster(s)  -> CONFIRM before removing")
    print(f"With full-text PDF    : {sum(1 for r in records if r['fulltext_pdf']=='Y')}")
    print(f"With abstract         : {sum(1 for r in records if r['abstract_available']=='Y')}")
    flagged = [r for r in records if r["flags"]]
    if clusters:
        print("\nDUPLICATE CLUSTERS (for human confirmation):")
        by = defaultdict(list)
        for r in records:
            if r["dup_cluster"]:
                by[r["dup_cluster"]].append(r)
        for cid, rs in sorted(by.items()):
            print(f"  {cid}: {[r['Ref_ID'] for r in rs]}  key={rs[0]['dedup_key'][:60]}")
    if flagged:
        print(f"\nDATA-QUALITY FLAGS ({len(flagged)} record(s)):")
        for r in flagged:
            print(f"  {r['Ref_ID']}: {r['flags']}  | {r['title'][:50]}")
    print(f"\nWrote {a.out}.csv and {a.out}.json")
    print("NOTE: counts above are RECORDS, not studies. Link reports->studies "
          "and screen eligibility before PRISMA accounting.")


if __name__ == "__main__":
    main()
