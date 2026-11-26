# Balance Compass

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
| Additional inputs | Acquisition and feature-validation code | Market/supply-demand statistics and historical publication/label records |
| Modeling | Eight existing hypotheses and 15 evaluations retained | Resource checks, frozen experiment and explicitly authorized real training |

## Research rounds

| Research round | Scope | Detailed source | Comparison |
|---|---|---|---|
| 1 | Initial design and Rust money parser; no Python pipeline or dashboard yet | [Round 1 · Korean](../2차/history/1차/차수설명.md) | [Initial scope · Korean](../2차/history/1차/차수설명.md) |
| 2 | Local research pipeline, evaluation and read-only dashboard; nationwide experiment incomplete | [Round 2 · Korean](../2차/docs/차수설명.md) | [1 → 2 · Korean](../2차/docs/차수비교.md) |
| 3 | Strict inputs, target-specific summaries, locks/recovery, eight hypotheses and 15 evaluations | [Round 3 · Korean](../3차/docs/차수설명.md) | [2 → 3 · Korean](../3차/docs/차수비교.md) |
| 4 | Full-column preservation, public-source acquisition, time-aware feature joins and exploratory comparisons | [Round 4 · English](docs/round4.md) | [3 → 4 · Korean](../4차/docs/차수비교.md) |

Historical documents remain in Korean and are explicitly labeled. The current round and all five English reading guides are available in English.

[Current source](../4차/) · [Execution specification · Korean](../4차/docs/4차_실행안내.md) · [Formulas and interpretation · Korean](../4차/docs/확장분석_수식과해석.md)
