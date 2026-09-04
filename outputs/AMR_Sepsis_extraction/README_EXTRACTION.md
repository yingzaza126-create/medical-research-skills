# Abstract-level extraction — AMR/Sepsis BSI meta-analysis (62 EndNote records)

**⚠️ อ่านก่อนใช้ / Read first**

1. ไฟล์ EndNote ที่อัปโหลดรอบนี้ **เหมือนไฟล์เดิมทุกไบต์ (MD5 ตรงกัน)** — ยังไม่มี PDF ฉบับเต็ม
   และ **ยังไม่ได้แนบเกณฑ์ inclusion/exclusion (PECO)**
2. ทั้งหมดนี้จึงเป็น **การสกัดระดับ ABSTRACT เท่านั้น** (Source = Abstract) — ตัวเลขทุกตัวคัดจาก abstract จริง
   **ไม่มีการสร้างข้อมูลขึ้นเอง**; ค่าที่คำนวณจาก % (event counts) กำกับว่า *derived / Low confidence*
   และ **ต้องยืนยันกับ full text** ทุกค่า
3. **PECO ที่สมมติไว้ (โปรดยืนยัน):** all-cause mortality ใน **antimicrobial-RESISTANT vs SUSCEPTIBLE**
   bloodstream infection (สอดคล้องกับคอลัมน์ Intervention/Control ของ template)

---

## Executive summary
- Records identified (EndNote library): **62**
- Duplicates removed (DOI/PMID/title): **0**
- Records with usable abstract: **43** (19 ไม่มี abstract → ต้อง title/full-text screening)
- Studies classified in evidence map: **46**
- **Proposed eligibility (ต้องยืนยันด้วย protocol):**
  - `INCLUDE` (resistant-vs-susceptible mortality, สกัด effect ได้): **8**
  - `RELEVANT` (cohort เชื้อดื้อยา แต่ abstract ไม่มี comparator/effect): **12**
  - `REVIEW` (systematic review/meta-analysis — เป็น reference ไม่ pool กับ primary): **7**
  - `OTHER_PECO` (treatment / risk-factor / prediction / surveillance — คนละคำถาม): **19**

## 8 การศึกษาที่สกัด effect ได้ (INCLUDE) — resistant vs susceptible, all-cause mortality
| Study | เชื้อ/การดื้อยา | เปรียบเทียบ (R vs S) | Effect (verbatim จาก abstract) |
|---|---|---|---|
| S05 Allel 2024 (Chile) | ARB vs susceptible | 638 vs 711* | **adj OR 1.35 (1.16–1.58)**; crude OR 1.42 (1.20–1.68) |
| S06 Alwashaish 2025 (Libya) | MDR-GNB vs non-MDR | 252 vs 421* | **MDR aOR 1.9**; 30d 32.1% vs 18.8% |
| S12 Calderón-Parra 2025 (Spain) | CR-K vs CS-K | 30 vs 156 | **aOR 3.97 (1.40–9.12)**; 40.0% vs 10.9% |
| S14 Chotiprasitsakul 2025 (Thailand) | CRAB vs NCRAB | 75 vs 47 | aHR 0.83 (0.26–2.59) NS; 66.7% vs 25.5% |
| S28 Kong 2026 (China) | CRE vs CSE | 144 vs 144 | **aHR 1.37 (1.01–1.86)** (patient-group) |
| S32 Li 2026 (China) | CRKP vs CSKP | 90 vs 324 | crude 21.1% vs 9.3% (no adj OR in abstract) |
| S35 Olivares-Navarro 2026 (Spain) | ESBL vs non-ESBL E. coli | 322 vs 2072 | crude OR 1.61 (1.14–2.27); **adj OR 1.12 (0.75–1.67) NS** |
| S36 Özçelik 2026 (Turkey) | CRKP vs CSKP (ICU) | 113 vs 76 | 28d survival no diff (log-rank p=0.45) |

\* N ต่อกลุ่มของ S05/S06 = derived จาก % (Low confidence) — ต้องดึงจาก full text
**สำคัญเรื่อง methodology:** effect เหล่านี้ปน **adjusted กับ crude** และปน **OR กับ HR** →
ตามหลัก meta-analysis **ห้าม pool รวมกันตรง ๆ** ต้องแยกตาม effect measure และ adjusted/crude ก่อน (ดู audit trail)

## ไฟล์ที่ส่งมอบ
| ไฟล์ | เนื้อหา |
|---|---|
| `1.1Data_templet_for_Meta.xlsx` | 46 แถว: ทุก study มี Study_ID/Author/Year/Design/Country; 8 INCLUDE มี Intervention(=ดื้อยา)/Control(=ไว)/N/deaths/OR/CI |
| `1S1_Table_JBI_Quality_Appraisal.xlsx` | 46 แถว: Study + Author,Year + Study Design + JBI Tool (เลือกตาม design) — **domain แต่ละข้อยังเว้นไว้** เพราะ JBI ต้องอ่าน full text |
| `1Fig.PRISMA_2020_flow_diagram_SRs.docx` | เติมเฉพาะ Identification (Databases=62, Duplicates=0, Records screened=62); node หลัง screening เว้นไว้รอเกณฑ์ |
| `Evidence_Map_abstract_level.xlsx` | ตารางสรุป 46 studies: design, เชื้อ, คำถาม, eligibility ที่เสนอ, effect (adjusted/crude verbatim), source |
| `audit_trail.csv` | ทุกค่าที่สกัด: study, field, value, source, confidence, สูตร/หมายเหตุ |

## คอลัมน์ที่ mapping ใน 1.1Data_templet
- `Intervention` = กลุ่ม **ดื้อยา** (resistant) · `Control` = กลุ่ม **ไวต่อยา** (susceptible)
- `Success_Intervention/Control` = **จำนวนผู้เสียชีวิต (deaths)** — โปรดยืนยันว่าตรงกับนิยาม event ที่ท่านต้องการ
- `OR/CI_95_Lower/Upper` = ใส่ **crude OR** (เทียบชนิดเดียวกันได้) ส่วน **adjusted OR/HR อยู่ใน audit_trail**
- ยังไม่มีคอลัมน์ Source ใน template → traceability เก็บไว้ใน `audit_trail.csv` และ `Evidence_Map`

## HUMAN REVIEW FLAGS
- **HR-001** REF001: record ว่าง (ไม่มี title/year/DOI) — ตรวจว่าเป็นบทความจริงหรือ record เสีย
- **HR-002** REF002 (Kiya/BMC 2025): ชื่อผู้แต่งต่อกันไม่มีตัวคั่น — โปรดยืนยัน
- **HR-003** S05/S06: N ต่อกลุ่มเป็นค่า derived จาก % — ดึงตัวเลขจริงจาก full text
- **HR-004** effect ปน adjusted/crude และ OR/HR — ต้องจัดกลุ่มก่อน pooling (compatibility check)
- **HR-005** 8 INCLUDE เป็น "resistant vs susceptible mortality"; แต่ studies ที่รายงานเฉพาะแขนดื้อยา
  (S48 So-Ngern, S/Suh, S/Xie, S/Kypraiou ฯลฯ) อาจเข้าเกณฑ์ได้ถ้ามี comparator ใน full text

## ต้องการให้ทำต่อ (เพื่อได้ชุดข้อมูลพร้อม pool + JBI ต่อ item + PRISMA ครบ node)
โปรดส่ง **(1) PECO + เกณฑ์ inclusion/exclusion** และ **(2) PDF ฉบับเต็ม** ของ studies ที่คัดเข้า
แล้วผมจะ: ยืนยัน 2×2 event counts/effect จริง, ให้คะแนน JBI ทีละ item พร้อมหลักฐาน,
คัดกรอง eligibility ให้ครบ, เติม PRISMA ทุก node พร้อม reconciliation, และอัปเดต audit trail
