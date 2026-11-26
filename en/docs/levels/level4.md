# LEVEL 4 - Advanced

[English overview](../../README.md) · [한국어](../../../docs/읽기안내/레벨4.md)

[LEVEL 1](level1.md) · [LEVEL 2](level2.md) · [LEVEL 3](level3.md) · [LEVEL 5](level5.md)

## Inspect implementation boundaries

Round 4 separates raw-input preservation, public-source acquisition, feature validation/joining, spatial feature construction and exploratory modeling. The join must keep contract row identity and count unchanged rather than expand an ambiguous one-to-many match.

| Module boundary | Implementation | Design trade-off |
|---|---|---|
| `research_input` / `public_sources` | Preserve original fields and track acquired public snapshots | Collection is not historical eligibility |
| `feature_store` | Reject malformed provenance and ambiguous latest observations; track missingness and record lineage | Unmatched information remains missing |
| `spatial_features` | Haversine/BallTree straight-line distance and radius counts | These are not walking distances or historical facility availability |
| `expansion` | Select Ridge/HGB by full-information validation MAE, then hold the algorithm fixed for group-removal comparisons | All comparisons use the same eligible contracts |
| Preprocessing | Fit missing-value replacement and categories on training rows | Price-aggregate paths without holdout lineage are blocked |

The information-group comparison measures predictive contribution under this protocol. It does not identify a causal treatment effect. The same input, target, contracts and algorithm are necessary to interpret differences; changing them would confound the comparison.

[Round 4 at this level](../round4.md#user-content-reading-level-4) · [Current source](../../../4차/)

| Earlier round · Korean | Same-level detail |
|---|---|
| 1 | [Round 1](../../../2차/history/1차/차수설명.md#user-content-reading-level-4) |
| 2 | [Round 2](../../../2차/docs/차수설명.md#user-content-reading-level-4) |
| 3 | [Round 3](../../../3차/docs/차수설명.md#user-content-reading-level-4) |
