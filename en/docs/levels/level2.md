# LEVEL 2 - Explorer

Latest overall: Revision 6 (Korean). Latest English coverage: Round 5. The Round 5 guide below is retained as the latest English edition. Real training remains stopped. [Current source](../../../6차/) · [Revision 6 details](../../../6차/docs/차수설명.md#user-content-reading-level-2).

**Latest: Round 5.** [Read the current round at this level](../round5.md#user-content-reading-level-2). The Round 4 foundation below is retained for context.

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

## Latest · Round 5

| Focus | Current behavior | Boundary |
|---|---|---|
| Linkage units | Contracts, region-months, complex codes and map points remain separate | 13.47% complex linkage does not prove representativeness |

[Round 5 at this level](../round5.md#user-content-reading-level-2) · [Current source](../../../5차/)

Revision 6 adds persisted-result, dashboard consistency and facility eligibility validation. Revision 6 currently has Korean documentation only. Real training remains stopped and paper outcomes are unmeasured. [Revision 6](../../../6차/docs/차수설명.md#user-content-reading-level-2).
