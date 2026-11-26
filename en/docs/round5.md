# Round 5 · National Data and Linkage Validation

[한국어](../../5차/docs/차수설명.md) · **English**

[LEVEL 1](#user-content-reading-level-1) · [LEVEL 2](#user-content-reading-level-2) · [LEVEL 3](#user-content-reading-level-3) · [LEVEL 4](#user-content-reading-level-4) · [LEVEL 5](#user-content-reading-level-5)

**Real-data training remains stopped.** This round acquires and checks source data; it does not report measured predictive performance, a completed manuscript, or a publication. The existing eight hypotheses and 15 target-specific evaluations remain unchanged.

<a id="reading-level-1"></a>

## LEVEL 1 - Beginner

Apartments of the same size can have different lease prices because of their location, building condition, interest rates and nearby facilities. The study asks whether such information helps predict future deposits and monthly rent, while also evaluating ranges intended to contain the actual amount. **More downloaded data does not establish a better prediction.**

| Term | Plain meaning | Important distinction |
|---|---|---|
| Contract row | One reported lease contract | One apartment can have several contracts |
| Household count | Registered households in an area or residential units in a complex | Neither is automatically the number of people or statistical households |
| Base rate | The Bank of Korea policy rate | It is not an individual's mortgage rate |
| Map point | Two numbers describing a location | It need not be an entrance, a surveyed point or a walking route |
| Snapshot | Data downloaded at a particular time | Current parking capacity does not prove the capacity in 2022 |
| Missing or unmatched | A value or identity cannot be established | This is different from an observed zero |

| Collected material | Observed amount | Intended use |
|---|---:|---|
| Lease source, 2022–2025 | 48 months; 4,845,086 rows | Dates, amounts, floor area and other original contract fields |
| Population and households, 2020–2025 | 21,156 region-month rows | Candidate regional information |
| Policy-rate history | 63 change rows | A policy decision made before the contract date |
| Current complex information | 21,805 complex codes | Candidate units, buildings, parking and elevator fields |
| Current complex map | 22,641 codes | Separating 21,207 valid unique current points from problematic cases |

The full lease source includes renewals and unknown contract types. The linkage audit uses only **2,880,280 rows marked as new contracts in the source**. This is still not the final cleaned modeling population.

| Step | Check | When uncertain |
|---|---|---|
| 1 | Read contract date and address | Preserve the original row and source |
| 2 | Find regional population two months before the contract month | Do not choose arbitrarily between administrative layers sharing a name |
| 3 | Find the most recent policy decision strictly before the contract date | Exclude a decision on the same day |
| 4 | Compare complex name, lot address and road name | A similar name alone is insufficient |
| 5 | Inspect the map points for the same complex code | Do not invent a representative point when coordinates disagree |

Parking per unit divides parking spaces by residential units. The elevator ratio adds all six elevator categories and divides by units only when all required values exist and the denominator is positive. Missing categories are not replaced with zero. These ratios define candidate variables; they are not new mathematical theories.

The complex linkage identifies 387,989 contracts, approximately **13.47%** of source new contracts. This subset cannot represent the whole country without further evidence: unmatched apartments could differ in size or region. Manual checks and unmatched-sample bias analysis remain necessary.

Verification recorded 120 automated checks and independent review. Date parsing, spreadsheet references and coordinate-receipt problems were reproduced and repaired. Those checks establish specific technical behavior, not universal data correctness or predictive accuracy. Next steps are complex–coordinate–facility integration, linkage validation, additional market data, an approved feature snapshot and resource checks. Training remains stopped.

[Same-level guide](levels/level1.md) · [Round 4 at this level](round4.md#user-content-reading-level-1)

<a id="reading-level-2"></a>

## LEVEL 2 - Explorer

This round aligns **different observation units** instead of merging rows merely because their addresses appear similar. Originals and transformations remain separate, with lineage to the source row.

| Source | Unit and retained identity | Validation and output |
|---|---|---|
| Lease CSV | Contract; 21 original fields, `source_row_id`, `cluster_id` | Manifest, row-count and hash checks |
| MOIS annual CSV | Region code × month | Twelve months, required headers, population totals and household ratios → normalized CSV |
| BOK HTML | Policy-rate change on a decision date | Reject malformed or duplicate decisions → chronologically ordered changes |
| KAPT XLSX | Complex code | Check headers, references, formulas and duplicate codes → 30 selected research columns plus original row number |
| Map JSON and official JavaScript | Map point associated with a complex code | Verify source hashes, regions, search month and projection → code-level coordinate status |

Of 21,156 population rows, 20,088 are normal, 348 are source blanks, and 720 record both population and households as zero. Missing values and zero-valued abolished regions remain distinct. Province totals and lower-level rows overlap and must not all be summed into a national total. Similar names do not establish continuity after administrative changes.

Population lookup uses the longest exact region prefix at token boundaries for contract month minus two months. Equal-length candidates remain ambiguous; province-level fallback is counted separately. Even equal population values, such as two Sejong codes, do not justify merging codes. The two-month lag is a research assumption, **not evidence of the historical publication time**.

| Population linkage | Source new-contract rows |
|---|---:|
| City/county/district level | 2,579,914 |
| Province-level fallback | 61,674 |
| Unmatched | 186,126 |
| Multiple administrative layers with the same name | 52,566 |

Every one of the 2,880,280 source new contracts had an earlier policy-rate decision by date. This is date coverage, not evidence that the rate improves predictions. Target month, decision/building-approval date, acquisition time and actual publication/revision time are different concepts; historical publication and label-availability vintages remain unavailable.

Complex linkage requires an exact complex name, legal-dong lot address and original road name in the same province. It identified 3,162 KAPT codes and 387,989 contracts. No observed `cluster_id` mapped to different KAPT codes, but this does not replace manual truth checking. Aliases, trailing lot hyphens and administrative changes are not guessed into matches.

| Current map-code status | Codes | Treatment |
|---|---:|---|
| Valid unique point | 21,207 | Retain as a current location candidate |
| Conflicting points | 1,320 | Quarantine; no average or first-point selection |
| Missing coordinates | 95 | Preserve missingness |
| Invalid numeric values or origin 0,0 | 19 | Quarantine |

The map collection queried the 16 boundaries actually shown on the current page, rather than forcing an older list of 17 names. Existing 12,004 school rows, 18,376 park rows and 898 station rows have not yet been integrated with these points. One anomalous park coordinate and physical station-identity reconciliation remain unresolved.

Valid residential-unit denominators exist for 21,793 complexes; 12 are unusable. Even among valid denominators, elevator ratios are missing for 495 rows, maximum floors for 30, and building counts for 15. Population year-on-year growth is only a candidate definition: comparability has been audited, but no actual growth-feature snapshot has been created. Eight hypotheses and 15 evaluations remain separate from exploratory comparisons of additional information groups.

[Same-level guide](levels/level2.md) · [Round 4 at this level](round4.md#user-content-reading-level-2)

<a id="reading-level-3"></a>

## LEVEL 3 - Practitioner

**These commands acquire and audit data; they do not resume training.** Use Python 3.12, both dependency lists, and `pyproj==3.7.2`. The complete existing test suite also requires the Rust amount CLI. Do not rewrite the source XLSX or run Excel recalculation.

```powershell
python -m pip install -r requirements.txt -r requirements_acquire.txt
./scripts/build_rust.ps1
```

Run from `5차/`. Replace `프로젝트루트` with the actual data root; this can differ from the public code checkout. Every output must be a **new, nonexistent path**. Repeat population acquisition separately for each year from 2020 through 2025. The 2020 source supports checking whether lagged population for early-2022 contracts can be compared with the prior year.

```powershell
python -m rentlab.national_sources population --year 2020 --output "프로젝트루트/외부 자료/2차/MOIS_2020"
python -m rentlab.national_sources base-rate --output "프로젝트루트/외부 자료/2차/BOK"
python -m rentlab.kapt_source --output "프로젝트루트/외부 자료/2차/KAPT_검증취득"
python scripts/collect_kapt_map.py --search-month 202609 --output "새지도원문"
python -m rentlab.kapt_coordinates --raw-root "새지도원문" --output "새좌표검증"
python scripts/audit_national_sources.py --project "프로젝트루트" --output "새인구감사.json"
python scripts/audit_complex_linkage.py --project "프로젝트루트" --output "새단지감사.json"
python -m unittest discover -s tests -v
```

| Required data location under the project root | Purpose and safeguards |
|---|---|
| `실제 실험/확장 입력 1차/자료_manifest.json` | List of 48 contract CSVs; verify original rows, hashes and counts |
| `외부 자료/2차/MOIS_2020` through `MOIS_2025` | Annual population originals and normalized data; never overwrite an existing collection |
| `외부 자료/2차/BOK` | Policy-rate change history; do not label it as mortgage rates |
| `외부 자료/2차/KAPT_검증취득` | Current XLSX and research CSV; extraction dated 2026-11-20 |
| Separate new map and coordinate directories | Preserve JSON responses, receipts and official coordinate JavaScript |

The two audit scripts expect the specified input subdirectories. If acquisition uses different names, align the layout or deliberately update the explicit input paths. Preserve new locations together with their manifests instead of moving data over existing originals.

| Collection step | Check | Failure handling |
|---|---|---|
| Population | All 12 requested months, required columns, region identities | Reject HTML responses, partial periods and inconsistent population totals |
| Policy rate | Valid dates, rates and uniqueness | Reject changed decision-row formats or duplicates and inspect the source |
| KAPT | Attachment metadata, spreadsheet references and complex identities | Review changed formats or duplicate codes; do not edit the original |
| Map | All actual page regions, consistent search month and source hashes | Reject missing regions, mismatched month or invalid receipts |
| Coordinates | Source JavaScript hash and code-level status | Quarantine conflicts/missing/invalid values; create no representative point |

The observed counts—63 rate rows, 21,805 complexes and 24,588 map rows—describe this collection, not fixed expectations for future provider updates. KAPT acquisition follows the ordinary public-session, CSRF-token and attachment-list procedure. It does not bypass login, CAPTCHA or access restrictions.

The audit rechecks contract SHA, row counts and changes during processing. National-source and complex-linkage outputs use the source-new denominator, not a cleaned training sample. Population lookup uses month minus two; rates use decision date strictly before the contract. Ratios require valid positive denominators and all required values. Automated checks and reparsing verify technical boundaries; they do not establish prediction accuracy or the absence of every possible error.

Keep `feature_ready=false` and `historical_availability_proven=false`. Historical vintages, facility integration, manual linkage checks, mortgage rates, inflation, price indices, unsold housing, the frozen comparison matrix and measured memory/time benchmarks are outstanding. Round 4's separate `--execute` option does not revoke the instruction to keep training stopped.

[Same-level guide](levels/level3.md) · [Round 4 at this level](round4.md#user-content-reading-level-3)

<a id="reading-level-4"></a>

## LEVEL 4 - Advanced

Existing model-fitting and hypothesis code is retained. New modules isolate acquisition, conservative linkage and current-coordinate validation; **technical success never grants feature readiness automatically**.

| Module | Input → output | Rejection boundary |
|---|---|---|
| `national_sources` | MOIS CP949 CSV / BOK HTML → normalized CSV and receipts | Missing requested months/headers, inconsistent totals, changed decision-row format |
| `kapt_source` | Public attachment list / XLSX → 30 research columns and source row | Duplicate codes, negative/out-of-range shared-string references, formulas in research columns |
| `complex_linkage` | Contract address and complex candidates → status and original complex row | Preserve name/lot/road disagreement and ambiguity |
| `kapt_coordinates` | Map JSON receipts and official JavaScript → coordinate status per code | Verify source/method SHA, region scope, search month and projection parameters |
| Audit scripts | Contract manifest and normalized sources → annual/province linkage aggregates | Verify hashes, counts and modifications during processing |

Collectors first complete responses, CSV and manifest in a temporary directory, then rename to a new destination. Failed acquisition must not appear as a successful data folder. The XLSX remains unchanged locally; unnecessary contact/business-registration columns are not copied into the research CSV.

`population_before_month(records, region, day, lag_months=2)` considers normal rows for contract month minus two and exact token boundaries. The longest match is returned; equal-length alternatives raise `AmbiguousPopulationError`. Province fallback is identified from the returned region level. `rate_before_day(records, day)` returns the latest decision with decision date strictly less than contract date. No `published_at` is fabricated from the assumed lag, and existing `strict_asof` conditions remain enforced.

KAPT linkage removes only an exact complex-name suffix from the legal-dong address. It then checks region+lot and complex name, followed by the original road name in the same province. Multiple candidates remain ambiguous; road mismatch is `address_disagreement`; blank or hyphen-only required keys remain incomplete. No name-similarity maximization or final-sample cleaning is implied.

`derive_features` requires positive integer units; an integer-valued numeric representation such as `200.0` is allowed. NaN, infinity and negative values are rejected. A blank in any of the six elevator categories makes the ratio missing. Maximum floors prefer a positive building-register value, falling back to the general maximum when absent or zero. This does not correct historical facility states or location accuracy.

The collector reads the actual 16 map boundaries sequentially. Receipt region and requested `bjdCode` must agree; every `searchDate` must be the same valid YYYYMM. The page and official coordinate-JavaScript acquisition hashes are checked. The observed query argument is **202609**, with 24,588 source rows and 22,641 codes; it does not prove historical location as of that month.

Coordinate status uses the exclusive priority **invalid → missing → conflicting → valid**. Identical repeated points are checked as one point while retaining source-row counts; differing points are neither averaged nor resolved by taking the first. The entire official `knew_fn_coordinate(flag=1)` PROJ string is preserved. An EPSG identifier in a comment is not substituted. `pyproj 3.7.2` with `always_xy=True` fixes WGS84 longitude/latitude order, without implying entrance or survey precision.

Independent review reproduced four boundaries: partially parsed rate decisions, negative XLSX shared-string references, unchecked page/method hashes, and a hardcoded search month. Regression tests repaired these failures; all 120 checks passed. This is distinct from claiming those corruptions occurred in the acquired source data. Six MOIS originals, all 21,805 KAPT rows and 63 BOK rows were reparsed against normalized output; independent coordinate reconversion matched the CSV hash.

New information-group removal comparisons remain exploratory and use matched contracts and algorithms. Complex–coordinate–facility identities, physical station IDs, unmatched bias, market statistics, historical releases, experiment freeze and resource benchmarks still need validation. A dependency graph or passing tests does not establish historical truth or measured predictive performance.

[Same-level guide](levels/level4.md) · [Round 4 at this level](round4.md#user-content-reading-level-4)

<a id="reading-level-5"></a>

## LEVEL 5 - Expert

This is a reproducible technical audit of acquisition, conservative linkage and current coordinates. The population-growth implementation audits comparability only; it does not emit the actual growth-feature snapshot. Additional features have not been integrated into the eight-hypothesis, 15-evaluation confirmatory path. **The source-new denominator and the final modeling population are separate estimands/populations.**

| Inferential layer | Existing implementation | Unestablished claim |
|---|---|---|
| Eight hypotheses / 15 target evaluations | Prespecified formulas applied after predictions | No real large-scale fitted results |
| Additional information comparison | MAE differences on matched contracts, removal of information groups | Feature snapshot and complete experiment matrix not frozen |
| Uncertainty | Existing clustered bootstrap and multiplicity conditions retained | No exact coverage guarantee under time/region shift |
| Source time | Target month, policy decision date and acquisition timestamp | Original historical releases, label availability and revision vintages absent |

The existing confirmatory path uses **9,999 complex-cluster bootstrap replicates** and Bonferroni-adjusted approximate intervals for 15 evaluations; this is not an exact simultaneous 95% guarantee. Pointwise 95% clustered approximate intervals for exploratory information-group comparisons are separate. Proposed `BC_loss` remains an unvalidated auxiliary composite, not a proper score, model-selection criterion or new theorem. Existing hypothesis and citation scope is unchanged.

### Source scope and eligibility

| Source | Observed scope | Qualification |
|---|---:|---|
| Lease originals | 48 months, 2022–2025; 4,845,086 rows | Hash/count checked; 2,880,280 source-new rows are a pre-cleaning audit denominator |
| MOIS | 2020–2025; 21,156 region-months | Current service's past values; foreigners excluded; aggregate and lower administrative layers overlap |
| BOK | 63 decision-change rows | Current historical table, not mortgage rates or proven historical release timestamps |
| KAPT basic information | 21,805 distinct codes; 2026-11-20 extract | Original XLSX retained locally; 30 research columns plus source-row identifiers |
| KAPT map | 16 on-page regions; 24,588 rows; 22,641 codes | Query 202609 does not establish an as-of historical snapshot |
| Earlier facilities | Schools 12,004; parks 18,376; stations 898 rows | One park-coordinate anomaly and physical station identity remain unresolved |

Official sources: [MOIS population](https://jumin.mois.go.kr/statMonth.do), [BOK base-rate history](https://www.bok.or.kr/portal/singl/baseRate/list.do?dataSecd=00001&menuNo=200643), [KAPT basic-information downloads](https://www.k-apt.go.kr/web/board/goKaptBasicExcelDownload.do), [KAPT](https://www.k-apt.go.kr/), and [pyproj axis-order documentation](https://pyproj4.github.io/pyproj/stable/api/transformer.html).

Population quality partitions into 20,088 normal, 348 source-blank and 720 zero-population-and-household rows. A code's predecessor, split or merger is not inferred. Overlapping administrative layers are not summed into national population.

### Annual linkage denominators

| Source-new year | Denominator | City/county/district | Province fallback | Unmatched | Multiple layers | Exact complex/lot/road |
|---|---:|---:|---:|---:|---:|---:|
| 2022 | 606,292 | 521,922 | 15,214 | 56,187 | 12,969 | 86,906 |
| 2023 | 732,312 | 650,805 | 17,470 | 51,906 | 12,131 | 101,347 |
| 2024 | 789,728 | 721,889 | 14,716 | 39,163 | 13,960 | 105,002 |
| 2025 | 751,948 | 685,298 | 14,274 | 38,870 | 13,506 | 94,734 |
| Total | 2,880,280 | 2,579,914 | 61,674 | 186,126 | 52,566 | 387,989 |

Exact complex linkage covers 3,162 codes and approximately 13.47% of source-new contracts. No observed cluster maps to different KAPT codes, but manual accuracy checks and non-linkage bias remain unresolved. This is linkage eligibility before final sample cleaning, not a national representativeness claim.

### Coordinate states and feature definitions

| Exclusive coordinate status | Codes | Decision |
|---|---:|---|
| `invalid_coordinates` | 19 | Nonfinite/incomplete numeric values or origin 0,0; quarantine |
| `missing_coordinates` | 95 | Some or all original coordinates absent |
| `conflicting_coordinates` | 1,320 | Multiple distinct complete points; no representative |
| `valid_current_map_point` | 21,207 | Unique point, successful conversion and broad Korea-range check |

Missingness and conflict can coexist in raw observations; the priority above makes the reported states exclusive. The count is distinct from all codes having multiple raw coordinate pairs. Neither geographic precision, entrances, walking distances nor historical facility operation is established by a valid point or by decimal precision.

| Candidate | Definition | Eligibility |
|---|---|---|
| Lagged population | `P*(i,t) = P(g(i), month(t)-2)` | Exact name lookup; lag is an assumption, not `published_at` |
| Year-on-year population change | `100 × [P(g,m)/P(g,m-12)-1]` | Same code, both months normal, prior population >0; comparability audit only |
| Parking per residential unit | Parking spaces / residential units | Positive valid denominator; current extract only |
| Elevators per residential unit | Sum of six elevator categories / residential units | Any missing category propagates missingness |
| Policy-rate lookup | `r(t)=r(s*), s*=max{s:s<t}` | Exclude same-day decisions; release-time proof remains separate |

Of 21,805 complex rows, 21,793 have valid unit denominators and 12 do not. Within valid denominators, missingness remains for 495 elevator ratios, 30 maximum-floor values and 15 building counts. Invalid values are never converted to zero. These are defined administrative lag/ratio calculations, not a new theorem or validated novel metric.

The reproduction commands and fixed input layout are given at [LEVEL 3](#user-content-reading-level-3). Source responses, hashes, counts and acquisition timestamps must be preserved. The public repository excludes real contract/external-source records, models, authentication material and private operational evidence. Only ordinary authorized public acquisition is supported.

| Outstanding condition | Current state | Required before the next claim |
|---|---|---|
| Historical releases and revision vintages | Unavailable | Keep strict historical replay blocked |
| Linkage accuracy and representativeness | Automated audit only | Manual truth checking and unmatched-bias analysis |
| Complex–coordinate–facility integration | Each source validated separately | Resolve keys, duplicate complexes and physical station IDs before distances |
| Mortgage rates, inflation, price indices, unsold housing | Only policy-rate history newly acquired | Verify official scope, publication delays and regional applicability |
| Feature snapshot and comparison matrix | Not frozen | Approve eligible features/population, then freeze hashes |
| Large-data memory and runtime | No measured benchmark | Resource check and explicit training authorization |
| Additional features in eight-hypothesis evaluation | Original baseline path retained | Keep exploratory comparisons separate from confirmatory 15 evaluations |

`feature_ready=false` and `historical_availability_proven=false` remain in force. Acquisition, 120 technical checks and independent review do not imply full research readiness. There is no completed manuscript, publication outcome or measured fitted performance.

[Same-level guide](levels/level5.md) · [Round 4 at this level](round4.md#user-content-reading-level-5)
