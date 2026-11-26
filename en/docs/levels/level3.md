# LEVEL 3 - Practitioner

**Latest: Round 5.** [Read the current round at this level](../round5.md#user-content-reading-level-3). The Round 4 foundation below is retained for context.

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

## Latest · Round 5

| Focus | Current behavior | Boundary |
|---|---|---|
| Acquisition and audit | Python 3.12, fixed data layout, new output folders and checked receipts | Commands do not resume stopped training |

[Round 5 at this level](../round5.md#user-content-reading-level-3) · [Current source](../../../5차/)
