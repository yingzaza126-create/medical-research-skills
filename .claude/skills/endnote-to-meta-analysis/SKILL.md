---
name: endnote-to-meta-analysis
description: >-
  Read and analyze an EndNote library / citation export (EndNote XML, RIS,
  .nbib, .enw) plus any full-text PDFs, then fill three systematic-review /
  meta-analysis deliverables WITHOUT breaking their structure: the meta-analysis
  data extraction sheet (1.1Data_templet_for_Meta.xlsx), the JBI critical-
  appraisal table (1S1_Table_JBI_Quality_Appraisal.xlsx), and the PRISMA 2020
  flow diagram (1Fig.PRISMA_2020_flow_diagram_SRs.docx). Use when the user has
  EndNote/reference files and wants deduplication, PRISMA screening/accounting,
  data extraction for meta-analysis, JBI quality appraisal, or the flow diagram
  and template sheets populated. Enforces evidence-first extraction: never
  invents effect sizes, CIs, SD, event counts, sample sizes, or PRISMA numbers;
  marks missing data NR/NA/NE and raises human-review flags. อ่านไฟล์ EndNote
  แล้วเติมข้อมูลลง template Meta-analysis, JBI, และ PRISMA 2020 โดยคงโครงสร้างเดิม
  และห้ามสร้างข้อมูลที่ไม่มีหลักฐาน.
---

# EndNote → Systematic Review & Meta-analysis Evidence Pipeline

Turn an EndNote library and its evidence files into three audit-ready outputs:

| # | Output | Filled by |
|---|--------|-----------|
| 1 | `1.1Data_templet_for_Meta.xlsx` — meta-analysis extraction | `scripts/fill_meta_template.py` |
| 2 | `1S1_Table_JBI_Quality_Appraisal.xlsx` — JBI appraisal | `scripts/fill_jbi_template.py` |
| 3 | `1Fig.PRISMA_2020_flow_diagram_SRs.docx` — PRISMA 2020 flow | `scripts/fill_prisma.py` |

Blank templates live in `assets/templates/`. Input-format examples live in
`assets/examples/`. **Always write to a `_FILLED` copy — never overwrite the
originals in `assets/templates/`.**

## The one rule that governs everything

> **Evidence first, calculation second, interpretation third.**

Every number written must be traceable to the source (full text > table/figure
> supplement > abstract > metadata). If a value is not in the source, write a
code, never a guess:

- `NR` Not Reported · `NA` Not Applicable · `NE` Not Estimable
- `Not poolable` insufficient data for meta-analysis
- `Needs verification` inconsistency found — raise a HUMAN REVIEW FLAG

Never fabricate OR/RR/HR/MD/SMD, CI, SE, SD, event counts, denominators, or
PRISMA counts to make a table look complete. See `reference/METHODOLOGY.md`
(the full 29-section master methodology) for the detailed rules behind each
step below — read it before making judgement calls on eligibility, linkage,
outcome/effect-measure compatibility, or statistical synthesis.

## Workflow

Work through the phases in order. Do the scriptable mechanics with the helper
scripts; do the *judgement* (screening decisions, extraction from full text,
JBI grading, exclusion reasons) yourself, from the evidence, and record where
each value came from.

### Phase A — Inventory & normalize references
Parse the EndNote export into one canonical record per reference plus a
deduplication report:

```bash
python scripts/parse_endnote.py <ENDNOTE_FILE> --out work/references
```
Accepts `.xml` (EndNote XML), `.ris`, `.nbib`, `.enw`. Produces
`references.csv` / `references.json` and prints an inventory (records, unique
keys, potential duplicates, PDF/abstract availability) plus data-quality flags.
Dedup key priority: DOI → PMID → title+year → title+first-author+year.
**Duplicate clusters are reported, not deleted** — confirm each before removing.

### Phase B — Study linkage (Record → Report → Study)
Reconcile the deduplicated references into *studies*. One study can have several
reports (primary article + protocol + follow-up + supplement). Build the
`Study_ID ↔ Report_ID ↔ Ref_ID` mapping. **Never count one study as many
studies, and never count PDFs as studies.** Ambiguous overlap/linkage →
HUMAN REVIEW FLAG.

### Phase C — Eligibility screening
Apply the researcher's inclusion/exclusion criteria only. Record every decision
(title → abstract → full text → final) with a standard exclusion reason
(wrong population/exposure/comparator/outcome/design/setting, protocol-only,
conference-abstract-only, duplicate, insufficient data, out of date range).
Keep the audit trail — PRISMA counts must trace back to it.

### Phase D — Data extraction (Table 1)
Read `assets/templates/1.1Data_templet_for_Meta.xlsx` headers first. Extract
study characteristics, population, exposure/intervention/comparator, and
outcomes with effect estimates — keeping adjusted vs unadjusted separate and
recording the source location for each value. Assemble a CSV/JSON whose column
names match the template header, then:

```bash
python scripts/fill_meta_template.py \
  --template assets/templates/1.1Data_templet_for_Meta.xlsx \
  --data work/extracted_meta.csv \
  --out  work/1.1Data_templet_for_Meta_FILLED.xlsx
```
The script preserves the sheet name, header row, and formatting; appends one
row per record from row 2; and flags duplicate Study_ID, events > sample size,
CI ordering errors, SD ≤ 0, and leftover Excel error cells. (Quote any field
containing a comma, or use JSON.)

### Phase E — JBI quality appraisal (Table 2)
Pick the JBI checklist matching each study's design. Grade each item Yes / No /
Unclear / NA **from evidence in the article** — a plausible-looking method is
not a "Yes"; unreported → Unclear/NR. Then:

```bash
python scripts/fill_jbi_template.py \
  --template assets/templates/1S1_Table_JBI_Quality_Appraisal.xlsx \
  --data work/jbi_appraisal.json \
  --out  work/1S1_Table_JBI_Quality_Appraisal_FILLED.xlsx
```
`JBI_Score` is computed only as `100 × Items_Met / Total_Items_Applicable`
(arithmetic). `Quality_Rating` is written only if you supply it, or pass
`--rating-cutoffs 80,50` to derive High/Moderate/Low from the score (document
the cut-off you chose — JBI has no universal % threshold).

### Phase F — PRISMA 2020 accounting (Figure)
Reconcile the counts from the screening audit trail, then verify the arithmetic
BEFORE filling:

```
records_screened      = records_identified − records_removed_before_screening
records_screened      = records_excluded + reports_sought
reports_sought        = reports_not_retrieved + reports_assessed
reports_assessed      = full_text_exclusions + reports_of_included_studies
studies_included      ≤ reports_of_included_studies
```
Put the audited counts in a JSON file (see `assets/examples/prisma_counts_example.json`), then:

```bash
python scripts/fill_prisma.py \
  --template assets/templates/1Fig.PRISMA_2020_flow_diagram_SRs.docx \
  --counts work/prisma_counts.json \
  --out  work/1Fig.PRISMA_2020_flow_diagram_SRs_FILLED.docx
```
The script fills every `(n = )` node (both the DrawingML and VML copies so the
number shows in any Word renderer), optionally relabels the three generic
exclusion reasons, and re-runs the reconciliation, printing FLAGs on any
mismatch. It refuses to run if the template's placeholder count differs from
the bundled PRISMA 2020 template.

## Final quality control (do before handing back)

- Every included study has a `Study_ID`; no unconfirmed duplicate studies.
- Effect measures classified correctly; adjusted/unadjusted not mixed; no
  auto-pooling of incompatible outcomes.
- JBI checklist matches each study design; scores are arithmetic only.
- PRISMA counts reconcile and trace to the screening audit trail.
- Missing data coded (NR/NA/NE), never guessed; template/DOCX structure intact.
- All validation FLAGs and HUMAN REVIEW FLAGs surfaced to the user.

## Report back (executive summary)

Records identified · duplicates · records screened · reports assessed ·
studies included · reports of included studies · studies meta-analysis-ready
(binary / continuous / time-to-event) · non-poolable studies · and the list of
critical flags requiring the researcher's own verification. Then list the three
`_FILLED` output files.

## Non-negotiables

Never invent evidence · never silently change source values · never treat
reports as studies without linkage · never mix OR/RR/HR/MD/SMD without
justification · never treat "not reported" as zero · never overwrite the input
templates · always give traceable source locations · always flag uncertainty
for human review.
