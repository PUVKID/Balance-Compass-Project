# Round 6 · Prediction Integrity and Facility Eligibility

[한국어](../../6차/docs/차수설명.md) · **English**

[LEVEL 1](#user-content-reading-level-1) · [LEVEL 2](#user-content-reading-level-2) · [LEVEL 3](#user-content-reading-level-3) · [LEVEL 4](#user-content-reading-level-4) · [LEVEL 5](#user-content-reading-level-5)

**Real training remains stopped; the eight hypotheses have no measured real-data results.** This round repairs seven reproduced errors and one artifact-status inconsistency. It does not add training, data acquisition, a completed manuscript, a publication, a PDF or a release.

<a id="reading-level-1"></a>

## LEVEL 1 - Beginner

A repeated contract can change the reported error. A result that has never been measured must not appear as a measured result. This round checks the saved input and the displayed output before accepting either. If a comparison requires all three Seoul contracts but receives only two, it stops rather than quietly comparing a smaller group.

| Everyday question | Current behavior | What it does not prove |
|---|---|---|
| Is each contract counted once? | Keep its text ID and reject missing or repeated IDs and inconsistent counts | That the source's factual claims are true |
| Are the same homes compared? | Require the complete matching Seoul test set and matching actual values/dates | That any model predicts well |
| Is this real or test-made data? | Accept only REAL or SYNTHETIC; synthetic outcomes cannot support paper hypotheses | That a syntactically valid REAL label is independent proof |
| Was anything measured? | If every hypothesis effect is absent, mark the artifact unmeasured too | A zero effect or a completed experiment |

Facility checks are like checking labels on a map. Conflicting park identities remain unresolved; station numbers on different railway lines are not automatically physical station identities. Passing a date or ID check does not establish where a facility really operated in earlier years.

Technical verification recorded **145 passing checks**. Four facility sources were audited at two dates, producing eight reports without deleting source rows. Those are implementation and data-eligibility checks, not measured prediction accuracy. Final features, historical evidence, resource validation and a completed training run remain outstanding.

[Same-level guide](levels/level1.md) · [Round 5](round5.md#user-content-reading-level-1) · [Facility observations](#user-content-facility-observations)

<a id="reading-level-2"></a>

## LEVEL 2 - Explorer

Saved predictions flow through **IDs → splits and mode → matching Seoul contracts → hypothesis calculations → dashboard consistency**. Facility rows flow through identity/date/coordinate checks into reproducible reports and then a feature manifest. A row can have several reasons for being held back; adding reason counts is not a count of unique rows.

| Stage | Required connection | Rejected shortcut |
|---|---|---|
| Saved prediction | Declared target, split counts, text source ID and date | Duplicate/empty IDs, overlapping calibration/test rows |
| Seoul H5 comparison | Same snapshot and mode, fixed Seoul-excluded run, complete Seoul test IDs | Partial Seoul sets, other cities or Seoul in calibration |
| Summary display | Regional counts and weighted metrics agree with totals | Contradictory totals, invalid interval ordering or incompatible decisions |
| Facility report | Original source, policy dates, report path/hash and recalculated content | Editing an approval flag to bypass an ineligible source |

Calibration dates are **2024-07-01 through 2024-12-31**, and test dates are in **2025**. Declared targets need both calibration and test CSVs. Undeclared targets stay unmeasured; their unexpected CSVs are errors. Leading zeroes in source IDs remain part of the identity.

Current school records pass the stated machine checks at 2026-11-27, but not at 2025-12-31. Some park rows pass individually, while conflicts and source-wide eligibility remain unresolved. Railways and KAPT have no eligible rows at either audit date under these policies. **An eligible row is not an approved model feature or proof of a complete national list.**

[Same-level guide](levels/level2.md) · [Round 5](round5.md#user-content-reading-level-2) · [Facility observations](#user-content-facility-observations)

<a id="reading-level-3"></a>

## LEVEL 3 - Practitioner

Prepare Python 3.12, the fixed `requirements.txt` and `requirements_acquire.txt` environment, and the Rust amount parser. Run from `6차/`. With the existing local sources available, the following commands create eight facility reports and a manifest in a **new output directory** and run controlled implementation tests. They do not resume training or acquire new data. The example project path must match the actual local source layout.

```powershell
python -B -X utf8 scripts/audit_facility_eligibility.py --project "E:/2026/Balance Compass Project" --output "검증 근거/시설자격_실측" --as-of 2026-11-27 --reference-start 2026-01-01
$env:OMP_NUM_THREADS='2'
$env:OPENBLAS_NUM_THREADS='2'
$env:MKL_NUM_THREADS='2'
python -B -X utf8 -m unittest discover -s tests -v
```

| Inspect | Expected evidence | On failure |
|---|---|---|
| `hypothesis_results.json` | `mode`, `input_files`, `hypotheses`, `artifacts` | Compare prediction CSVs with declared targets/counts |
| `input_files` | SHA-256, byte size and row count of bytes actually read | Preserve the failing source and diagnose the mismatch |
| Feature manifest `quality_reports` | `source_id`, report path and SHA-256 | Rehash original CSV and report; recompute the complete report |
| Facility rows | Identity, coordinate and explicit date-policy reasons | Do not average conflicting rows or force eligibility flags |
| Artifact status | All effects absent → unmeasured in JSON and return value | Do not replace missing results with zero |

`write_research_results` validates before calculation. REAL mode requires valid snapshot hash, ID and row-count evidence. Both REAL and SYNTHETIC require coherent inputs; an unknown mode is rejected. The stored source-identity claim still needs independent factual evidence.

Preserve original manifest/CSV hashes and row counts before and after the audit. Outputs must not overwrite existing evidence. Correct and independently substantiate a source before producing a new report. The 145 technical checks include controlled inputs; they measure neither paper performance, effect size nor statistical power.

[Same-level guide](levels/level3.md) · [Round 5](round5.md#user-content-reading-level-3) · [Korean verification contract](../../6차/docs/6차_검증계약.md)

<a id="reading-level-4"></a>

## LEVEL 4 - Advanced

The saved-results entry point in `research_metrics` is distinct from internal `evaluate_frames` calculations. `facility_quality` produces row-level eligibility, `feature_store` verifies source/report hashes and recomputes the full reports, and `spatial_features` performs distance mathematics only for trusted physical identities. The loopback dashboard is read-only and provides no training control.

| Boundary | Validation contract | Failure or interpretation |
|---|---|---|
| Prediction input | Validate mode, targets, split counts, source text IDs and calibration/test dates | Reject missing/duplicate IDs and overlap across targets/splits |
| Seoul H5 | Same snapshot/mode and fixed Seoul-excluded run; exact full Seoul test-ID set | Compare paired target values, region, dates and clusters present on both sides |
| Dashboard | Regional n sums, n-weighted MAE/coverage, RMSE≥MAE, interval-field presence | Require registered hypothesis/target combinations and coherent status/decision combinations |
| Floating-point comparison | Relative tolerance `1e-9`, absolute tolerance `1e-6` | Display aggregation tolerance, not a scientific equivalence margin |
| Confidence intervals | Finite ordered endpoints | Do not reject a valid percentile CI merely because it excludes the point estimate |
| Facility manifest | Source/feature kind consistency, source CSV and report hashes, complete recomputation | Unsupported source kinds such as hospitals are rejected |

Declared targets must have test and calibration CSVs. CSVs for undeclared targets are errors rather than additional measurements. The exact bytes read determine recorded SHA-256/size/count. SYNTHETIC effects never yield paper-support judgments. If all effects are null, the JSON artifact and returned artifact state are both unmeasured.

Facility values with unproven history cannot have `valid_from` earlier than the later of the audit `as_of` date and the KST acquisition date. A current source cannot be retroactively approved for 2022–2025. Source-level `all_rows_eligible` is not granted merely because some rows pass. Park conflicts retain every conflicting row; neither the first/latest row nor its mean becomes a trusted facility. A railway route key remains distinct from a physical station ID.

[Same-level guide](levels/level4.md) · [Round 5](round5.md#user-content-reading-level-4) · [Facility observations](#user-content-facility-observations)

<a id="reading-level-5"></a>

## LEVEL 5 - Expert

The original **H1–H8, 15 target-specific evaluations, prediction-interval alpha=0.1, hypothesis-family confidence=0.95 (nominal family error 0.05), 9,999 bootstrap replicates, time split and fixed Seoul H5** are retained. No hypothesis, effect threshold, statistic or literature citation was added by these validation repairs.

| Invariant | Check | Inferential boundary |
|---|---|---|
| Full Seoul population | Exact complete ID set and paired actual values/date/region/cluster checks | Prevents post hoc subset comparisons; does not establish model quality |
| Count/metric aggregation | `Σn_g=n`, `MAE=Σn_g MAE_g/n`, `coverage=Σn_g coverage_g/n` | Integrity checks on saved summaries |
| Error identities | `MAE=Σ|y−ŷ|/n`, `RMSE=√(Σ(y−ŷ)²/n)`, `RMSE≥MAE` | Formula and hypothesis thresholds unchanged |
| CI and decisions | Finite ordered CI; coherent status and decision direction | Percentile CI need not contain the point estimate |
| Mode and measurement | REAL/SYNTHETIC only; all-null effects mean unmeasured artifacts | Synthetic effects do not support paper hypotheses |
| Historical facility use | Hash-bound full-report recalculation and no backward validity | Does not prove physical identity, historical operation/publication or completeness |

Cluster-bootstrap intervals are approximations conditional on the fitted model. They do not guarantee coverage under temporal shift, cluster dependence or small samples. Existing [hypotheses, formulas and citations](../../6차/docs/논문_가설과_수식.md) and [exploratory expansion formulas](../../6차/docs/확장분석_수식과해석.md) remain authoritative for the earlier protocol; validation equations do not establish a new statistical result.

Among **2,857,449 cleaned contracts**, strict complex linkage covers **385,030 (13.4746%)**, across **3,159 codes**. This is a different denominator from Round 5's source-new audit. Coordinate/name agreement is not independently labeled linkage accuracy, and regional selection bias remains. Aggregates of 2025 target amounts have already been observed during linkage-bias auditing. They were not used to tune hypotheses/model criteria, but the test data cannot be described as completely unseen.

Final feature/comparison freeze, independent linkage truth labels, physical facility identities, historical operation/publication, resource benchmarks and a completed real training run remain outstanding. `strict_asof` is blocked by unavailable original publication vintages; expanded information-group comparisons remain exploratory. Training is `stopped_by_user`, all eight hypotheses remain unmeasured on real data, and there is no completed manuscript/publication evidence or paper PDF. Original source data, models and private verification records are excluded from publication.

[Same-level guide](levels/level5.md) · [Round 5](round5.md#user-content-reading-level-5)

<a id="facility-observations"></a>

## Facility Observations · Shared Audit Reference

The four original sources were checked at two explicit audit dates, without deleting source rows. **Machine eligibility is not feature approval or historical truth.**

| Source | Original rows | Eligible at 2026-11-27 | Eligible at 2025-12-31 | Main limitation |
|---|---:|---:|---:|---|
| Schools | 12,004 | 12,004 | 0 | All 12,004 reference dates are later than the research end; 59 future establishment dates |
| Parks | 18,376 | 7,370 | 4,674 | 879 duplicate-ID groups, 632 coordinate-conflict groups; current whole-source eligibility fails |
| Railways | 898 | 0 | 0 | Reference dates 2019–2021; physical station IDs and opening history unavailable |
| KAPT | 21,805 | 0 | 0 | Unknown source-observation date for 21,805 rows; 226 approvals after the research end |

The current audit uses `reference_start=2026-01-01`; the research-end audit uses `reference_start=2025-01-01`. These are explicitly recorded policies, not universally validated freshness thresholds. Reason flags can overlap and must not be summed into unique row counts. Current school eligibility is neither historical approval nor proof of nationwide completeness.

| Additional observed issue | Count | Treatment and interpretation |
|---|---:|---|
| Park duplicate original rows | 2,259 | Hold all rows; do not choose a representative |
| Park stale current reference dates | 6,374 | Keep the reason and the source row |
| Park unknown establishment/notice dates | 3,468 | A designation notice is not opening/operation evidence |
| Park coordinate / area errors | 1 / 13 | Preserve errors as ineligibility reasons |
| Railway composite-key duplicates / coordinate-conflict groups | 52 / 12 | Route station numbers are not physical station identities |
| KAPT attribute errors | 12 | Hold the affected rows |

`historical_availability_proven=false` and `source_completeness_proven=false` remain unchanged. Eight recalculated reports and passing implementation tests cannot replace independent source truth, historical evidence, feature readiness or measured hypothesis results.
