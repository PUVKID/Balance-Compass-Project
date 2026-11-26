# LEVEL 5 - Expert


**Latest overall: Round 8 (Korean). Latest English: Round 7.** [Read the English round at this level](../round7.md#user-content-reading-level-5). The Round 4 foundation below is retained for context.

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

## Round 5 · Data Acquisition

| Focus | Current behavior | Boundary |
|---|---|---|
| Eligibility and inference | Historical availability and feature readiness remain false | 9,999-replicate approximate intervals are not an exact simultaneous coverage guarantee |

[Round 5 at this level](../round5.md#user-content-reading-level-5) · [Round 5 source](../../../5차/)

Revision 6 adds persisted-result, dashboard consistency and facility eligibility validation. Revision 6 is available in Korean and English. Real training remains stopped and paper outcomes are unmeasured. [Revision 6](../../../6차/docs/차수설명.md#user-content-reading-level-5).

## Round 6 · Prediction Integrity

| Focus | Current behavior | Boundary |
|---|---|---|
| Prediction and facility integrity | Validate identities, splits, modes, Seoul comparisons and hash-bound facility reports | 145 technical checks do not establish measured hypothesis results or historical facility truth |

[Round 6 at this level](../round6.md#user-content-reading-level-5) · [Current source](../../../8차/)


Revision 7 adds strict CSV/feature input validation, frozen-condition evidence and a model-free preflight CLI. It is available in Korean and English. Real training remains stopped and measured paper outcomes are unavailable. [Revision 7](../../../7차/docs/차수설명.md#user-content-reading-level-5).

## Latest · Round 7

| Focus | Current checks | Boundary |
|---|---|---|
| Input and inference integrity | Strict CSV, complete feature observations, fixed H5 methods and bootstrap evidence | Model-free preflight does not grant experiment readiness or authorize stopped training |

[Round 7 at this level](../round7.md#user-content-reading-level-5) · [Current source](../../../8차/)


Revision 8 adds a full 48-month lineage audit, cluster-dependence diagnostics and partial historical-rate evidence. English coverage remains Round 7. Real training is stopped; complete research approval and measured outcomes are unavailable. [Revision 8 · Korean](../../../8차/docs/차수설명.md#user-content-reading-level-5).
