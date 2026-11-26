# LEVEL 5 - Expert

Latest overall: Revision 6 (Korean). Latest English coverage: Round 5. The Round 5 guide below is retained as the latest English edition. Real training remains stopped. [Current source](../../../6차/) · [Revision 6 details](../../../6차/docs/차수설명.md#user-content-reading-level-5).

**Latest: Round 5.** [Read the current round at this level](../round5.md#user-content-reading-level-5). The Round 4 foundation below is retained for context.

[English overview](../../README.md) · [한국어](../../../docs/읽기안내/레벨5.md)

[LEVEL 1](level1.md) · [LEVEL 2](level2.md) · [LEVEL 3](level3.md) · [LEVEL 4](level4.md)

## Audit the protocol and inference

Strict joins require both a valid interval `[from, to)` and publication strictly before contract-day 00:00 Asia/Seoul. A timezone-less publication timestamp, ambiguous latest observation or duplicate source observation is rejected. The code checks declared timing and provenance; independent historical evidence remains necessary.

| Review dimension | Criterion | Remaining limit |
|---|---|---|
| Temporal eligibility | Latest unique qualifying observation with traceable source/record IDs | Training and calibration labels also need historical availability evidence; strict execution is currently blocked without it |
| Predictive comparison | Paired absolute-error differences on the same contracts; fixed selected algorithm | Exploratory predictive association, not causation |
| Uncertainty | Apartment-cluster resampling, 9,999 percentile draws and approximate 95% intervals | Unknown clusters or fewer than 20 clusters yield no interval |
| Multiplicity | Separate exploratory intervals from the existing 15-evaluation confirmatory family | Pointwise exploratory intervals do not replace family-level control |
| Reproducibility | Frozen sources, hashes, splits, fitted preprocessing and resource checks | A freeze and resource qualification remain incomplete |

Cluster resampling does not resolve every common spatial/temporal shock or model-fitting uncertainty. Candidate input completeness, nationwide performance and coverage under distribution shift are not established by the synthetic regression checks. Read missing or blocked outputs explicitly, and retain the distinction between current snapshots and historical reconstruction.

[Round 4 at this level](../round4.md#user-content-reading-level-5) · [Round 4 source](../../../4차/)

| Earlier round · Korean | Same-level detail |
|---|---|
| 1 | [Round 1](../../../2차/history/1차/차수설명.md#user-content-reading-level-5) |
| 2 | [Round 2](../../../2차/docs/차수설명.md#user-content-reading-level-5) |
| 3 | [Round 3](../../../3차/docs/차수설명.md#user-content-reading-level-5) |

## Latest · Round 5

| Focus | Current behavior | Boundary |
|---|---|---|
| Eligibility and inference | Historical availability and feature readiness remain false | 9,999-replicate approximate intervals are not an exact simultaneous coverage guarantee |

[Round 5 at this level](../round5.md#user-content-reading-level-5) · [Current source](../../../5차/)

Revision 6 adds persisted-result, dashboard consistency and facility eligibility validation. Revision 6 currently has Korean documentation only. Real training remains stopped and paper outcomes are unmeasured. [Revision 6](../../../6차/docs/차수설명.md#user-content-reading-level-5).
