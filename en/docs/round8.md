# Round 8 · Input Lineage and Completion Integrity

**English** · [한국어](../../8차/docs/차수설명.md)

Round 8 compares every downloaded contract row with the expanded input, checks how contracts share apartment-complex clusters, and makes the execution manifest explicit. A subsequent repair checks the input and engine again after combined analysis, before recording success.

**Actual training remains `stopped_by_user`. No measured prediction performance, new hypothesis support, completed manuscript or paper PDF was produced.** Input integrity and technical tests do not grant scientific approval or permission to resume training.

| Level | Read this section |
|---|---|
| LEVEL 1 - Beginner | [Understand the distinction](#user-content-reading-level-1) |
| LEVEL 2 - Explorer | [Follow the data](#user-content-reading-level-2) |
| LEVEL 3 - Practitioner | [Select inputs and inspect completion](#user-content-reading-level-3) |
| LEVEL 4 - Advanced | [Inspect implementation boundaries](#user-content-reading-level-4) |
| LEVEL 5 - Expert | [Interpret dependence and historical evidence](#user-content-reading-level-5) |

<a id="reading-level-1"></a>

## LEVEL 1 - Beginner

### Matching receipts is different from testing a prediction

Think of the downloaded contracts as boxes of receipts. Every value was compared with the prepared table, so missing or changed entries can be detected. That does not prove when each value first became public, or that a location was independently verified.

Several contracts can belong to one apartment complex. They can share conditions, so **100 contracts are not automatically 100 independent examples**. The 31 eligible contracts with unknown clusters stay unknown; the program does not invent a separate complex for each row.

| Question | Plain-language answer | Important limit |
|---|---|---|
| What was compared? | All 4,845,086 downloaded rows across 48 months | This is a data audit, not a model score |
| What is the current linked group? | 385,030 eligible contracts link to the current complex map | It is a selected subset, not a claim about all contracts |
| What changed in execution? | The runner can select the expanded input and checks for changes before success | A failed check does not repair the original data |
| Is training complete? | No; the existing user stop remains | No measured performance or paper result is available |

[Full audit evidence](#user-content-shared-audit-evidence) · [Project at this level](levels/level1.md) · [한국어 · same level](../../8차/docs/차수설명.md#user-content-reading-level-1)

<a id="reading-level-2"></a>

## LEVEL 2 - Explorer

### Follow each denominator and source

The flow is **4,845,086 original rows → 2,857,449 eligible rows → 385,030 currently linked contracts**. The external tables contain 427,418 rows in total, including repeated versions; that number is neither a contract count nor a count of distinct facilities.

A school establishment date, a park notice date and a railway reference date describe different things. None alone supplies the complete historical coordinates and operating periods needed for every contract date. The inventory distinguishes acquired, quarantined and candidate sources from approved historical features.

| Step | What was checked | What the check does not establish |
|---|---|---|
| Original → expanded input | All 21 values, row identity and cluster identity, in row order | An immutable copy of the version available at the contract date |
| Expanded → eligible rows | Existing preparation rules and exclusions | A new inclusion rule or new model selection |
| Eligible → current linkage | Existing identifiers and available current map points | Independent location accuracy or nationwide representativeness |
| External tables → evidence | Row counts, hashes, logical row widths and NUL checks | Reacquisition of every raw response or approval of historical use |

[Full counts and splits](#user-content-shared-audit-evidence) · [Project at this level](levels/level2.md) · [한국어 · same level](../../8차/docs/차수설명.md#user-content-reading-level-2)

<a id="reading-level-3"></a>

## LEVEL 3 - Practitioner

### Plan with the intended manifest

The stored legacy table has nine training columns and lacks `source_row_id` and `cluster_id`. Its 4,845,086 rows match the corresponding nine-value projection of the expanded input. **Matching values does not add the missing identity columns.** The expanded input contains 23 columns: the 21 original fields and the two identifiers.

```powershell
python -B -X utf8 -m rentlab.experiment_runner --root COLLECTION_ROOT --manifest EXPANDED_MANIFEST --run-dir NEW_RUN --with-holdout 서울특별시
```

This command omits `--execute`: it prints a read-only plan. The actual selected-manifest plan was checked without model fitting, creating a run directory, or changing the stopped state. Omitting `--manifest` retains `root/자료_manifest.json`. An explicitly selected missing file fails instead of silently falling back during execution.

| Stage | Recorded or checked | Failure behavior |
|---|---|---|
| Plan | Absolute selected manifest path | No training or run-directory creation |
| Execution start | Manifest path and starting SHA; engine SHA | Invalid input is not replaced with legacy input |
| Ordinary run | Manifest and engine compared with starting hashes | A change prevents holdout or successful single-run completion |
| Holdout run | Same selected path and hash comparisons | A change prevents combined analysis |
| Combined analysis return | Manifest and engine checked again before `completed` | A change leaves `failed`, exit 2; partial outputs are not promoted to success |

Five original control tests cover no-write planning, shared paths, explicit missing input, blocking holdout after an ordinary-run mutation, and blocking single-run completion. Two further regressions mutate a **temporary** manifest or engine during the controlled analysis callback. Both reproduced incorrect exit 0 before the repair and produced failed/exit 2 afterward. The project environment passed **168 tests: the original 166 plus these two regressions**. These are controlled technical checks, not real-data training.

The first full-suite attempt in a general Python environment lacked project dependencies; the passing suite used the existing project environment. The model-free feature preflight from Round 7 still checks technical inputs only. The conditions record is not `features.json` or training approval.

[Completion repair · Korean](../../8차/docs/8차_전수검증.md#user-content-analysis-completion-guard) · [Project at this level](levels/level3.md) · [한국어 · same level](../../8차/docs/차수설명.md#user-content-reading-level-3)

<a id="reading-level-4"></a>

## LEVEL 4 - Advanced

### Audit identities and the completion boundary

The full input audit reads each source with its encoding, compares 21 values in logical row order, recomputes `source_row_id` from the source SHA and logical row number, and recomputes `cluster_id` from the district/address/complex-name key. Input and original hashes were checked before and after processing. Preparation used the real Rust money parser, with model-candidate fitting explicitly blocked. The recorded original audit took 164.684 seconds; this is audit duration, not training time.

| Component | Contract | Boundary preserved |
|---|---|---|
| Input identity | All 48 monthly source/expanded row counts, schemas and IDs match | Original acquisition versions are not inferred from current files |
| Manifest selection | One resolved manifest is passed to ordinary, Seoul holdout and combination | Selected absolute path is logged; state also records its SHA |
| Completion guard | Starting manifest/engine SHA checked after ordinary, holdout and combined analysis | Detected mutations fail; outputs are not deleted or reported as approved |
| Independent truth | KAPT names, addresses and KAPT map share a source system | Agreement within that system is not independent validation |
| Freeze records | Original protocol/code/audit hashes preserved; repair hashes recorded separately | No rewritten historical freeze or implied feature approval |

All 385,030 currently linked eligible contracts had `valid_current_map_point` in the available map. This does not verify field-survey coordinates, entrances, walking routes or distances. Unmatched selection bias remains.

The quarantined identification table has 307,834 distinct identifiers: 46,385 apartment, 23,941 row-house and 237,508 multi-family-house rows. Even the apartment subset differs from the advertised 44,628. Multiple housing types and reference dates explain context but do not resolve that discrepancy. The table remains quarantined and is not independent linkage truth.

[Full source inventory · Korean](../../8차/docs/국내자료_출처목록.json) · [Project at this level](levels/level4.md) · [한국어 · same level](../../8차/docs/차수설명.md#user-content-reading-level-4)

<a id="reading-level-5"></a>

## LEVEL 5 - Expert

### Separate integrity, dependence and research approval

Unknown cluster rows remain in the eligible population: eight train, 15 validation, four calibration and four test. The test set includes one monthly-rent and three jeonse contracts without known clusters. Under the existing evidence rules, a complete full-contract cluster-bootstrap confidence interval is therefore unavailable. This is an input limitation, **not an observed valid interval**; no invented clusters or post-hoc row removal repairs it.

| Inference issue | Observation | Interpretation |
|---|---|---|
| Temporal dependence | Monthly test 330,883/377,571 and jeonse test 329,867/372,671 contracts belong to clusters present in training | Temporal evaluation is not unseen-complex generalization; Seoul H5 has a different denominator |
| Regional calibration | At least 100 rows but fewer than five complexes: 20 monthly and 29 jeonse regions | The existing 100-row rule is not independence or exchangeability evidence |
| Concentration | Maximum single-complex share is 100% in an eligible calibration region | No effective sample size was inferred and no new exclusion threshold was introduced |
| Historical availability | Thirteen official rate documents support selected dates/values | They do not certify immutable acquisition vintages, all unchanged-rate meetings, or all feature histories |
| Confirmatory scope | Existing eight hypotheses, 15 evaluations, formulas and thresholds retained | Prior inspection of 2025 aggregates, post-hoc design and unvalidated proposed metrics remain limitations |

Policy-rate evidence covers an initial applicable value and 12 changes in 2022–2025. No intraday publication time was invented; the existing `decision date < contract date` rule remains. Population publication guidance describes month-end data released after noon on the first day of the following month, shifted to the next working day for holidays/weekends. This does not prove absence of retrospective revisions. The existing two-month lag was not replaced by an invented exact historical publication timestamp.

School establishment, railway reference and park notice dates do not establish full historical opening, closure, relocation and coordinate vintages. Complete contract-date facility histories were not obtained from the checked sources; this does not assert that no such source exists elsewhere. Earlier findings remain: 59 schools established after 2025, 879 duplicate park groups, railway reference years 2019–2021, and unknown KAPT history. Raw data were not arbitrarily corrected.

Final feature approval, independent linkage labels, historical label availability, facility/population vintages and authorized resource/training readiness remain unresolved. Repeating software tests does not supply those missing observations.

[Full audit evidence](#user-content-shared-audit-evidence) · [Project at this level](levels/level5.md) · [한국어 · same level](../../8차/docs/차수설명.md#user-content-reading-level-5)

<a id="shared-audit-evidence"></a>

## Shared Counts, Splits and Source Evidence

These are the original Round 8 audit counts. The initial 166-test evidence and subsequent two completion-guard regressions are separate records. No new acquisition or model fitting was needed for the documentation and completion-boundary repair.

| Audit | Count or observation | Meaning and limit |
|---|---|---|
| Original → expanded | 48 months; 4,845,086 rows; all 21 values and two IDs matched | Integrity of downloaded files, not proof of their original public vintage |
| Existing preparation | 2,857,449 eligible; 1,964,806 non-new and 22,831 invalid-construction-year rows excluded | Existing inclusion rules retained |
| External tables | 14 CSVs; 427,418 rows | Hash/count/width/NUL checks; repeated versions included |
| Current linkage | 385,030 / 2,857,449 = 13.4746% | Selected eligible-contract denominator |
| Missing original fields | 31 unknown lot numbers; 1,977 unknown road names; zero blank floor/construction-year strings | Nonblank construction-year text can still be invalid |
| Cancellations | Cancellation-reason date absent from the 21 fields | Cannot claim all cancellations checked or zero cancellations |
| Policy-rate documents | Initial value + 12 changes = 13 official pages | Partial historical evidence only |
| Training state | `stopped_by_user`, unchanged | No measured performance or new hypothesis result |

| Target / split | Eligible contracts | Known clusters | Unknown-cluster contracts | KAPT-linked contracts |
|---|---|---|---|---|
| jeonse / calibration | 202,554 | 22,278 | 0 | 25,080 |
| jeonse / test | 372,671 | 26,014 | 3 | 45,051 |
| jeonse / train | 743,702 | 29,080 | 4 | 98,787 |
| jeonse / validation | 225,883 | 23,115 | 9 | 29,034 |
| monthly / calibration | 180,771 | 24,473 | 4 | 24,704 |
| monthly / test | 377,571 | 30,197 | 1 | 49,671 |
| monthly / train | 575,818 | 30,311 | 4 | 86,531 |
| monthly / validation | 178,479 | 24,756 | 6 | 26,172 |

Train is 2022–2023, validation the first half of 2024, calibration the second half of 2024, and final test 2025. These are ordinary temporal-split diagnostics, not Seoul holdout performance. Target-specific aggregates were not used for new model selection.

| Target | Calibration regions | Regions with ≥100 rows | Of those, <5 complexes | Maximum one-complex share |
|---|---|---|---|---|
| monthly | 3,017 | 537 | 20 | 100% |
| jeonse | 2,708 | 605 | 29 | 100% |

Regions use the original contract district string. Fewer than five complexes is a diagnostic, not a newly applied exclusion rule.

| Decision date | Policy rate, % per year | Official evidence |
|---|---|---|
| 2021-11-25 | 1.0 | [Bank of Korea](https://www.bok.or.kr/portal/bbs/P0000559/view.do?menuNo=200690&nttId=10067646) |
| 2022-01-14 | 1.25 | [Bank of Korea](https://www.bok.or.kr/portal/bbs/P0000559/view.do?menuNo=200690&nttId=10068513) |
| 2022-04-14 | 1.5 | [Bank of Korea](https://www.bok.or.kr/portal/bbs/B0000169/view.do?menuNo=200690&nttId=10070059) |
| 2022-05-26 | 1.75 | [Bank of Korea](https://www.bok.or.kr/portal/bbs/P0000559/view.do?menuNo=200690&nttId=10070765) |
| 2022-07-13 | 2.25 | [Bank of Korea](https://www.bok.or.kr/portal/bbs/P0000559/view.do?menuNo=200690&nttId=10071639) |
| 2022-08-25 | 2.5 | [Bank of Korea](https://www.bok.or.kr/portal/bbs/B0000169/view.do?menuNo=200690&nttId=10072434) |
| 2022-10-12 | 3.0 | [Bank of Korea](https://www.bok.or.kr/portal/bbs/P0000559/view.do?menuNo=200690&nttId=10073227) |
| 2022-11-24 | 3.25 | [Bank of Korea](https://www.bok.or.kr/portal/bbs/P0000559/view.do?menuNo=200690&nttId=10074005) |
| 2023-01-13 | 3.5 | [Bank of Korea](https://www.bok.or.kr/portal/bbs/P0000559/view.do?menuNo=200690&nttId=10074980) |
| 2024-10-11 | 3.25 | [Bank of Korea](https://www.bok.or.kr/portal/bbs/P0000559/view.do?menuNo=200690&nttId=10087410) |
| 2024-11-28 | 3.0 | [Bank of Korea](https://www.bok.or.kr/portal/bbs/P0000559/view.do?menuNo=200690&nttId=10088270) |
| 2025-02-25 | 2.75 | [Bank of Korea](https://www.bok.or.kr/portal/bbs/P0000559/view.do?menuNo=200690&nttId=10089951) |
| 2025-05-29 | 2.5 | [Bank of Korea](https://www.bok.or.kr/portal/bbs/P0000559/view.do?menuNo=200690&nttId=10091639) |

[Population publication guidance](https://jumin.mois.go.kr/statGrapA.do) · [School specification](https://www.data.go.kr/data/15021148/standard.do) · [Railway specification](https://www.data.go.kr/data/15013205/standard.do) · [Park specification](https://www.data.go.kr/data/15012890/standard.do) · [Quarantined identification-table specification](https://www.data.go.kr/data/15106861/fileData.do)

| Remaining condition | Current status |
|---|---|
| Independent apartment-linkage truth | No independently labeled sample; accuracy unmeasured |
| Historical facility, label and population vintages | Not fully established |
| Final feature manifest | Not approved; candidates are not automatically inserted |
| User training stop and resources | Stop preserved; actual training not resumed |
| Research result and manuscript | No measured outcome, completed paper or PDF |

The original [conditions record](../../8차/docs/연구조건_동결.json) retains its original code hashes. The later [completion repair record](../../8차/docs/완료경계_수리.json) binds the changed runner and new regression file separately. Source input hashes, audit hashes, scientific formulas and thresholds were not rewritten.

[Previous Round 7](round7.md) · [Round 8 source](../../8차/) · [Full audit · Korean](../../8차/docs/8차_전수검증.md) · [7 → 8 comparison · Korean](../../8차/docs/차수비교.md)
