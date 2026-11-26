# LEVEL 1 - Beginner

This English guide covers revisions 1–4. [Revision 5 is currently documented in Korean](../../../5차/docs/차수설명.md#user-content-reading-level-1); its English translation is not yet available.

[English overview](../../README.md) · [한국어](../../../docs/읽기안내/레벨1.md)

[LEVEL 2](level2.md) · [LEVEL 3](level3.md) · [LEVEL 4](level4.md) · [LEVEL 5](level5.md)

## Understand what is ready

A collected file is like a box of receipts: having the receipts does not mean a prediction has been tested. Round 4 preserves the original fields and prepares information about nearby facilities. The program must still establish which facility observation belongs to each contract and whether that information existed at the relevant time.

| Question | Plain-language answer | What to check |
|---|---|---|
| What enters the study? | Lease-contract rows and separately sourced facility records | Original source, row count and file fingerprint |
| What would come out? | Separate deposit/rent predictions and ranges | Real training is stopped, so these are intended outputs, not measured results |
| How is accuracy read? | MAE is the average absolute difference between predicted and actual amounts | A small average does not make every individual prediction correct |
| Why show a range? | An interval expresses uncertainty around the prediction | Read inclusion rate together with interval width |

Start with the status table, then read the round at this same level. Treat missing results as unavailable; they are not zero. A facility-data download is not a verified link to a home, and a current facility list does not prove its historical state.

[Round 4 at this level](../round4.md#user-content-reading-level-1) · [Current source](../../../4차/)

| Earlier round · Korean | Same-level detail |
|---|---|
| 1 | [Round 1](../../../2차/history/1차/차수설명.md#user-content-reading-level-1) |
| 2 | [Round 2](../../../2차/docs/차수설명.md#user-content-reading-level-1) |
| 3 | [Round 3](../../../3차/docs/차수설명.md#user-content-reading-level-1) |


Revision 6 adds persisted-result, dashboard consistency and facility eligibility validation. The English guide covers revisions 1–4; revisions 5–6 currently have Korean documentation only. Real training remains stopped and paper outcomes are unmeasured. [Revision 6](../../../6차/docs/차수설명.md).
