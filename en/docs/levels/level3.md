# LEVEL 3 - Practitioner


**Latest: Round 9.** [Read the current round at this level](../round9.md#user-content-reading-level-3). The Round 4 foundation below is retained for context.

[English overview](../../README.md) · [한국어](../../../docs/읽기안내/레벨3.md)

[LEVEL 1](level1.md) · [LEVEL 2](level2.md) · [LEVEL 4](level4.md) · [LEVEL 5](level5.md)

## Prepare and inspect an execution

Use the round-4 execution specification as the command reference. Prepare Python 3.12 dependencies and the Rust money parser, validate the source manifest, and choose a new output folder. Existing outputs and original inputs are preserved. This guide does not authorize restarting the currently stopped training run.

| Check | Required action | Failure or limit |
|---|---|---|
| Input | Verify hashes, counts, original columns and row/cluster identifiers | Reject incompatible or unverifiable input |
| Features | Validate source, join key, validity and timezone-aware publication time | Strict execution is blocked without qualifying features and label history |
| Plan | Inspect the default execution plan before using `--execute` | The default does not fit a model |
| Outputs | Read audit, prediction and comparison outputs together | Synthetic technical checks are not real-data results |
| Recovery | Observe locks, atomic state and explicit interruption status | A stopped experiment is not automatically restarted |

The dashboard reads results; it is not a training or collection API. Historical round-3 commands remain in the linked Korean execution reference. Use round-4 instructions for the new feature-expansion path, and distinguish source acquisition from feature qualification.

[Round 4 at this level](../round4.md#user-content-reading-level-3) · [Round 4 source](../../../4차/)

| Earlier round · Korean | Same-level detail |
|---|---|
| 1 | [Round 1](../../../2차/history/1차/차수설명.md#user-content-reading-level-3) |
| 2 | [Round 2](../../../2차/docs/차수설명.md#user-content-reading-level-3) |
| 3 | [Round 3](../../../3차/docs/차수설명.md#user-content-reading-level-3) |

## Round 5 · Data Acquisition

| Focus | Current behavior | Boundary |
|---|---|---|
| Acquisition and audit | Python 3.12, fixed data layout, new output folders and checked receipts | Commands do not resume stopped training |

[Round 5 at this level](../round5.md#user-content-reading-level-3) · [Round 5 source](../../../5차/)

Revision 6 adds persisted-result, dashboard consistency and facility eligibility validation. Revision 6 is available in Korean and English. Real training remains stopped and paper outcomes are unmeasured. [Revision 6](../../../6차/docs/차수설명.md#user-content-reading-level-3).

## Round 6 · Prediction Integrity

| Focus | Current behavior | Boundary |
|---|---|---|
| Prediction and facility integrity | Validate identities, splits, modes, Seoul comparisons and hash-bound facility reports | 145 technical checks do not establish measured hypothesis results or historical facility truth |

[Round 6 at this level](../round6.md#user-content-reading-level-3) · [Round 6 source](../../../6차/)


Revision 7 adds strict CSV/feature input validation, frozen-condition evidence and a model-free preflight CLI. It is available in Korean and English. Real training remains stopped and measured paper outcomes are unavailable. [Revision 7](../../../7차/docs/차수설명.md#user-content-reading-level-3).

## Round 7 · Input Integrity

| Focus | Current checks | Boundary |
|---|---|---|
| Input and inference integrity | Strict CSV, complete feature observations, fixed H5 methods and bootstrap evidence | Model-free preflight does not grant experiment readiness or authorize stopped training |

[Round 7 at this level](../round7.md#user-content-reading-level-3) · [Round 7 source](../../../7차/)


Revision 8 adds a full 48-month lineage audit, cluster-dependence diagnostics and partial historical-rate evidence. Round 8 is available in Korean and English. Real training is stopped; complete research approval and measured outcomes are unavailable. [Revision 8 · Korean](../../../8차/docs/차수설명.md#user-content-reading-level-3).

## Round 8 record

| Focus | Current checks | Boundary |
|---|---|---|
| Input lineage and completion | Full 48-month audit, selected manifest and post-analysis hash checks | Data integrity is not independent location truth, historical-vintage approval or measured performance |

[Round 8 at this level](../round8.md#user-content-reading-level-3) · [Current source](../../../9차/)


Revision 9 validates both saved summaries before combined analysis and checks holdout calibration contract identity against the ordinary non-Seoul subset. 171 controlled tests pass; real training remains stopped. Round 9 is available in Korean and English. [Revision 9 · Korean](../../../9차/docs/차수설명.md#user-content-reading-level-3).


## Latest Round 9

Use Python 3.12, the fixed dependencies and the Rust money parser. Run python -B -X utf8 -m unittest discover -s tests -v from the revision folder. The full suite contains 171 controlled tests. A passing suite is not measured research performance and does not authorize restarting stopped training.

| Step | Inspect | Failure handling |
|---|---|---|
| Controlled suite | unittest output: 171 tests | Do not report completion on failure |
| Before combined output | Both summary.json files | Reject missing, changed or differently typed data |
| Calibration check | Calibration prediction CSVs | Reject changed row population or observations |
| Traceability | 입력검증.json and 일반원본_summary.json | Preserve originals separately |

[Round 9 at this level](../round9.md#user-content-reading-level-3) · [한국어 같은 수준](../../../9차/docs/차수설명.md#user-content-reading-level-3)
