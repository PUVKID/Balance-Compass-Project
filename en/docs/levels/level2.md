# LEVEL 2 - Explorer

This English guide covers revisions 1–4. [Revision 5 is currently documented in Korean](../../../5차/docs/차수설명.md#user-content-reading-level-2); its English translation is not yet available.

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

[Round 4 at this level](../round4.md#user-content-reading-level-2) · [Current source](../../../4차/)

| Earlier round · Korean | Same-level detail |
|---|---|
| 1 | [Round 1](../../../2차/history/1차/차수설명.md#user-content-reading-level-2) |
| 2 | [Round 2](../../../2차/docs/차수설명.md#user-content-reading-level-2) |
| 3 | [Round 3](../../../3차/docs/차수설명.md#user-content-reading-level-2) |


Revision 6 adds persisted-result, dashboard consistency and facility eligibility validation. The English guide covers revisions 1–4; revisions 5–6 currently have Korean documentation only. Real training remains stopped and paper outcomes are unmeasured. [Revision 6](../../../6차/docs/차수설명.md).
