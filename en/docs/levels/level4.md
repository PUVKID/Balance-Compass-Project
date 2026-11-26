# LEVEL 4 - Advanced

Latest overall: Revision 6 (Korean). Latest English coverage: Round 5. The Round 5 guide below is retained as the latest English edition. Real training remains stopped. [Current source](../../../6차/) · [Revision 6 details](../../../6차/docs/차수설명.md#user-content-reading-level-4).

**Latest: Round 5.** [Read the current round at this level](../round5.md#user-content-reading-level-4). The Round 4 foundation below is retained for context.

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

[Round 4 at this level](../round4.md#user-content-reading-level-4) · [Round 4 source](../../../4차/)

| Earlier round · Korean | Same-level detail |
|---|---|
| 1 | [Round 1](../../../2차/history/1차/차수설명.md#user-content-reading-level-4) |
| 2 | [Round 2](../../../2차/docs/차수설명.md#user-content-reading-level-4) |
| 3 | [Round 3](../../../3차/docs/차수설명.md#user-content-reading-level-4) |

## Latest · Round 5

| Focus | Current behavior | Boundary |
|---|---|---|
| Module boundaries | Exact-name/time lookup, address disagreement and coordinate quarantine | Do not fabricate publication timestamps or representative points |

[Round 5 at this level](../round5.md#user-content-reading-level-4) · [Current source](../../../5차/)

Revision 6 adds persisted-result, dashboard consistency and facility eligibility validation. Revision 6 currently has Korean documentation only. Real training remains stopped and paper outcomes are unmeasured. [Revision 6](../../../6차/docs/차수설명.md#user-content-reading-level-4).
