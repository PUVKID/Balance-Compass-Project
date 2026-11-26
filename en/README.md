# Balance Compass


The latest round audits all 48 months of input lineage, distinguishes cluster dependence from independent evidence, and guards selected inputs through analysis completion. [Read Round 8 in English](docs/round8.md).

[한국어](../README.md) · **English**

Balance Compass studies **apartment lease deposits, monthly rent, and prediction-interval reliability** across time and regions in South Korea. Deposits and monthly rent are separate targets; a monthly-rent prediction is conditional on the observed deposit, not an estimate of the causal effect of changing it.

**Real-data training is stopped. No completed measured model performance is available.** The collected 48 monthly source files for 2022–2025 contain 4,845,086 rows. Collection counts are not training-sample counts. Synthetic checks establish technical behavior, not support for research hypotheses. There is no completed manuscript or publication claim.

| Reading level | Start here |
|---|---|
| LEVEL 1 - Beginner | [Open guide](docs/levels/level1.md) |
| LEVEL 2 - Explorer | [Open guide](docs/levels/level2.md) |
| LEVEL 3 - Practitioner | [Open guide](docs/levels/level3.md) |
| LEVEL 4 - Advanced | [Open guide](docs/levels/level4.md) |
| LEVEL 5 - Expert | [Open guide](docs/levels/level5.md) |

| Material or step | Available now | Still required |
|---|---|---|
| Contract input | Original 21 columns, row/source lineage and integrity checks | Final eligible analysis population and experiment freeze |
| Current facility snapshots | 12,004 school rows, 18,376 park rows, 898 railway-station rows acquired | Verified apartment coordinates, contract linkage and historical operation records |
| Apartment identifiers | 307,834 downloaded rows | Reconciliation with the advertised 44,628; the file is quarantined |
| Coordinate quality | One anomalous park coordinate recorded | Validation before using it as a predictor |
| National inputs | Population 2020–2025 (21,156 region-months), policy-rate history (63 changes), KAPT information (21,805 codes) | Historical vintages, mortgage rates, inflation, price indices and unsold housing |
| Current complex linkage | 387,989 source-new contracts across 3,162 complex codes (~13.47%) | Manual accuracy checks and unmatched-sample bias; no nationwide representativeness claim |
| Current map | 21,207 valid unique points among 22,641 codes | Quarantined conflicts/missing/invalid coordinates; facility integration outstanding |
| Modeling | Eight existing hypotheses and 15 evaluations retained | Resource checks, frozen experiment and explicitly authorized real training |

## Research rounds

| Research round | Scope | Detailed source | Comparison |
|---|---|---|---|
| 1 | Initial design and Rust money parser; no Python pipeline or dashboard yet | [Round 1 · Korean](../2차/history/1차/차수설명.md) | [Initial scope · Korean](../2차/history/1차/차수설명.md) |
| 2 | Local research pipeline, evaluation and read-only dashboard; nationwide experiment incomplete | [Round 2 · Korean](../2차/docs/차수설명.md) | [1 → 2 · Korean](../2차/docs/차수비교.md) |
| 3 | Strict inputs, target-specific summaries, locks/recovery, eight hypotheses and 15 evaluations | [Round 3 · Korean](../3차/docs/차수설명.md) | [2 → 3 · Korean](../3차/docs/차수비교.md) |
| 4 | Full-column preservation, public-source acquisition, time-aware feature joins and exploratory comparisons | [Round 4 · English](docs/round4.md) | [3 → 4 · Korean](../4차/docs/차수비교.md) |
| 5 | MOIS/BOK/KAPT acquisition, exact complex linkage and current-coordinate validation; training stopped | [Round 5 · English](docs/round5.md) | [4 → 5 · Korean](../5차/docs/차수비교.md) |
| 6 | Saved-prediction identity/split/mode validation, complete Seoul H5, dashboard consistency and facility eligibility | [Round 6 · English](docs/round6.md) | [5 → 6 · Korean](../6차/docs/차수비교.md) |
| 7 | Strict CSV/feature validation, fixed-condition evidence and a model-free preflight CLI; training stopped | [Round 7 · English](docs/round7.md) | [6 → 7 · Korean](../7차/docs/차수비교.md) |
| 8 | Full 48-month lineage audit, selected-manifest execution and analysis completion guards, cluster diagnostics and partial historical evidence | [Round 8 · English](docs/round8.md) | [7 → 8 · Korean](../8차/docs/차수비교.md) |

Rounds 1–3 remain in Korean and are explicitly labeled. Rounds 4–8 and the five current reading guides have English explanations.

[Current source](../8차/) · [Current execution and remaining conditions](docs/round8.md#user-content-reading-level-3) · [Formulas and interpretation · Korean](../4차/docs/확장분석_수식과해석.md)

Revision 6 adds persisted-result, dashboard consistency and facility eligibility validation. Revision 6 is available in Korean and English. Real training remains stopped and paper outcomes are unmeasured. [Revision 6](../6차/docs/차수설명.md).


Revision 7 adds strict CSV/feature input validation, frozen-condition evidence and a model-free preflight CLI. It is available in Korean and English. Real training remains stopped and measured paper outcomes are unavailable. [Revision 7](../7차/docs/차수설명.md).


Revision 8 adds a full 48-month lineage audit, cluster-dependence diagnostics and partial historical-rate evidence. Round 8 is available in Korean and English. Real training is stopped; complete research approval and measured outcomes are unavailable. [Revision 8 · Korean](../8차/docs/차수설명.md).
