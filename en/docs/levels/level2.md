# LEVEL 2 - Explorer


**Latest: Round 9.** [Read the current round at this level](../round9.md#user-content-reading-level-2). The Round 4 foundation below is retained for context.

[English overview](../../README.md) · [한국어](../../../docs/읽기안내/레벨2.md)

[LEVEL 1](level1.md) · [LEVEL 3](level3.md) · [LEVEL 4](level4.md) · [LEVEL 5](level5.md)

## Follow the information flow

The pipeline separates source verification, feature construction, model selection, interval calibration and final evaluation. A file fingerprint checks whether the file is unchanged; it does not prove that the file covers every relevant contract or that its values were publicly available in the past.

| Stage | Input | Output and boundary |
|---|---|---|
| Audit | Source CSV, metadata and SHA-256 | Tracked rows and exclusion reasons; the original remains unchanged |
| Feature preparation | Contract key/date, facility coordinates and publication metadata | Matched features, missingness indicators and observation lineage |
| Fit | 2022–2023 contracts | Training-fitted preprocessing and candidate models |
| Select / calibrate | First / second half of 2024 | Validation-MAE selection / separate interval-calibration residuals |
| Evaluate | 2025 contracts | Errors, interval inclusion/width and regional summaries, once an experiment is completed |

Round 4 adds 21-column preservation and exploratory information-group comparisons. The candidate feature catalog does not mean all 62 candidates have been acquired. Current public snapshots must not be relabeled as proven historical observations.

[Round 4 at this level](../round4.md#user-content-reading-level-2) · [Round 4 source](../../../4차/)

| Earlier round · Korean | Same-level detail |
|---|---|
| 1 | [Round 1](../../../2차/history/1차/차수설명.md#user-content-reading-level-2) |
| 2 | [Round 2](../../../2차/docs/차수설명.md#user-content-reading-level-2) |
| 3 | [Round 3](../../../3차/docs/차수설명.md#user-content-reading-level-2) |

## Round 5 · Data Acquisition

| Focus | Current behavior | Boundary |
|---|---|---|
| Linkage units | Contracts, region-months, complex codes and map points remain separate | 13.47% complex linkage does not prove representativeness |

[Round 5 at this level](../round5.md#user-content-reading-level-2) · [Round 5 source](../../../5차/)

Revision 6 adds persisted-result, dashboard consistency and facility eligibility validation. Revision 6 is available in Korean and English. Real training remains stopped and paper outcomes are unmeasured. [Revision 6](../../../6차/docs/차수설명.md#user-content-reading-level-2).

## Round 6 · Prediction Integrity

| Focus | Current behavior | Boundary |
|---|---|---|
| Prediction and facility integrity | Validate identities, splits, modes, Seoul comparisons and hash-bound facility reports | 145 technical checks do not establish measured hypothesis results or historical facility truth |

[Round 6 at this level](../round6.md#user-content-reading-level-2) · [Round 6 source](../../../6차/)


Revision 7 adds strict CSV/feature input validation, frozen-condition evidence and a model-free preflight CLI. It is available in Korean and English. Real training remains stopped and measured paper outcomes are unavailable. [Revision 7](../../../7차/docs/차수설명.md#user-content-reading-level-2).

## Round 7 · Input Integrity

| Focus | Current checks | Boundary |
|---|---|---|
| Input and inference integrity | Strict CSV, complete feature observations, fixed H5 methods and bootstrap evidence | Model-free preflight does not grant experiment readiness or authorize stopped training |

[Round 7 at this level](../round7.md#user-content-reading-level-2) · [Round 7 source](../../../7차/)


Revision 8 adds a full 48-month lineage audit, cluster-dependence diagnostics and partial historical-rate evidence. Round 8 is available in Korean and English. Real training is stopped; complete research approval and measured outcomes are unavailable. [Revision 8 · Korean](../../../8차/docs/차수설명.md#user-content-reading-level-2).

## Round 8 record

| Focus | Current checks | Boundary |
|---|---|---|
| Input lineage and completion | Full 48-month audit, selected manifest and post-analysis hash checks | Data integrity is not independent location truth, historical-vintage approval or measured performance |

[Round 8 at this level](../round8.md#user-content-reading-level-2) · [Current source](../../../9차/)


Revision 9 validates both saved summaries before combined analysis and checks holdout calibration contract identity against the ordinary non-Seoul subset. 171 controlled tests pass; real training remains stopped. Round 9 is available in Korean and English. [Revision 9 · Korean](../../../9차/docs/차수설명.md#user-content-reading-level-2).


## Latest Round 9

Start with ordinary calibration contracts and remove Seoul. The remaining source-row IDs must exactly match the holdout calibration set. Match the observed amount, date, region and apartment-cluster ID for each contract. Row order and model predictions may differ.

| Data transition | Must remain the same | May differ |
|---|---|---|
| Ordinary calibration to non-Seoul subset | Complete set of remaining row IDs | Row order |
| Ordinary to holdout observations | Amount, date, region and cluster | Model prediction |
| Saved summary to preserved copy | JSON values, types and validated bytes | Filename for the analysis result |

[Round 9 at this level](../round9.md#user-content-reading-level-2) · [한국어 같은 수준](../../../9차/docs/차수설명.md#user-content-reading-level-2)
