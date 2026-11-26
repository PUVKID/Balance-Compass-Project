# Round 9 · Persisted-result binding

Round 9 continues the audit of the combined ordinary/Seoul-holdout analysis. Real-data training and acquisition remain stopped. It preserves the Round 8 completion guard and its two tests, plus the Korean and English reading guides (baseline 9630bd0). It adds three regression-test methods, bringing the full controlled suite from 168 to 171.

[한국어 상세](../../9차/docs/차수설명.md) · [English overview](../README.md) · [Previous round](round8.md)

## Complete validation contract

| Input or case | Before | Round 9 |
|---|---|---|
| Ordinary saved summary missing or changed | Returned metadata could still reach analysis | Reject before creating the combined folder |
| Holdout saved summary missing or changed | Detected only after copying | Validate both summaries first |
| JSON count 1 changed to true | Python dictionary equality treats these as equal | Type-preserving JSON comparison rejects it |
| Calibration row substituted or removed | Per-file structure/count/date checks could pass | Require exactly the ordinary non-Seoul row population |
| Observed amount/date/region/cluster changed | A well-formed changed file could pass | Compare observations after alignment by row ID |
| Row order or learned prediction changed | Allowed | Remains allowed |

Both checked summary byte sequences are preserved: the ordinary source is named **일반원본_summary.json**, and the holdout source is **홀드아웃/summary.json**. Their SHA-256 hashes are recorded in **입력검증.json**. The analysis writes its own summary.json separately. Original result directories are preserved. The ordinary calibration set is filtered using exact Seoul or Seoul-with-subregion names. Its remaining source_row_id set must equal the holdout set. Dates, regions and cluster IDs are compared as strings; actual_won is compared as finite numeric data. Predictions are learned separately and are not required to match.

The initial negative controls produced seven failures and three errors. Two additional type-mutation controls exposed the true-versus-1 issue, which was then repaired. The final three regression methods cover six missing/value/type summary cases, six calibration-population/observation cases, and a valid reordered calibration set with different predictions. The full 171-test suite was rerun after the type repair. No real-data model was fitted. The 48-month, 4,845,086-row audit is an earlier Round 8 observation, not a new full-data audit in Round 9.

Known limits remain: 31 eligible rows lack cluster identity; independent location ground truth and complete contract-time facility, population and rental-data vintages are unproven. No IDs were fabricated and no observations were silently removed. Model performance, hypothesis support and manuscript completion are unmeasured. [Full Korean validation contract](../../9차/docs/9차_결과대조.md) · [Formulas and citations](../../9차/docs/논문_가설과_수식.md) · [Full source diff](../../9차/docs/전체차이.diff).

<a id="reading-level-1"></a>

## LEVEL 1 - Beginner

### Check the labels before comparing results

A result file and its saved description must tell the same story. Before comparing the two experiments, the program checks both descriptions. A different contract cannot quietly replace a calibration example. Different predictions are expected when a different model is trained.

| Situation | Check | Outcome |
|---|---|---|
| Description and stored result disagree | Both saved summaries | Stop before combined analysis |
| A different contract is substituted | Contract identity | Reject the comparison |
| A new model predicts a different amount | Observed contract is unchanged | Allow the comparison |

[English project guide](levels/level1.md) · [한국어 같은 수준](../../9차/docs/차수설명.md#user-content-reading-level-1) · [Previous round at this level](round8.md#user-content-reading-level-1)

<a id="reading-level-2"></a>

## LEVEL 2 - Explorer

### Follow the contract population

Start with ordinary calibration contracts and remove Seoul. The remaining source-row IDs must exactly match the holdout calibration set. Match the observed amount, date, region and apartment-cluster ID for each contract. Row order and model predictions may differ.

| Data transition | Must remain the same | May differ |
|---|---|---|
| Ordinary calibration to non-Seoul subset | Complete set of remaining row IDs | Row order |
| Ordinary to holdout observations | Amount, date, region and cluster | Model prediction |
| Saved summary to preserved copy | JSON values, types and validated bytes | Filename for the analysis result |

[English project guide](levels/level2.md) · [한국어 같은 수준](../../9차/docs/차수설명.md#user-content-reading-level-2) · [Previous round at this level](round8.md#user-content-reading-level-2)

<a id="reading-level-3"></a>

## LEVEL 3 - Practitioner

### Run controlled checks and inspect failures

Use Python 3.12, the fixed dependencies and the Rust money parser. Run python -B -X utf8 -m unittest discover -s tests -v from the revision folder. The full suite contains 171 controlled tests. A passing suite is not measured research performance and does not authorize restarting stopped training.

| Step | Inspect | Failure handling |
|---|---|---|
| Controlled suite | unittest output: 171 tests | Do not report completion on failure |
| Before combined output | Both summary.json files | Reject missing, changed or differently typed data |
| Calibration check | Calibration prediction CSVs | Reject changed row population or observations |
| Traceability | 입력검증.json and 일반원본_summary.json | Preserve originals separately |

[English project guide](levels/level3.md) · [한국어 같은 수준](../../9차/docs/차수설명.md#user-content-reading-level-3) · [Previous round at this level](round8.md#user-content-reading-level-3)

<a id="reading-level-4"></a>

## LEVEL 4 - Advanced

### Bind metadata and observation keys

combine_results validates both saved JSON summaries against returned summaries before creating the combined-analysis folder. Canonical JSON serialization distinguishes true from 1. The exact validated summary bytes are preserved. write_research_results indexes calibration rows by source_row_id, so comparison is independent of ordering.

| Module contract | Comparison | Evidence |
|---|---|---|
| combine_results | Type-preserving sorted JSON serialization | Ordinary and holdout summary copies with hashes |
| write_research_results | Exact non-Seoul ID set, then ID alignment | Hash of each consumed calibration CSV |
| Observation fields | Three string fields and numeric actual amount | date, region, cluster_id, actual_won |
| Learned outputs | No forced equality | Different prediction_won values remain valid |

[English project guide](levels/level4.md) · [한국어 같은 수준](../../9차/docs/차수설명.md#user-content-reading-level-4) · [Previous round at this level](round8.md#user-content-reading-level-4)

<a id="reading-level-5"></a>

## LEVEL 5 - Expert

### Separate implementation evidence from inference

This change strengthens H5 input traceability; it does not change the estimand, eight hypotheses, fifteen evaluations, fixed time splits or statistical thresholds. Identical declared provenance alone is insufficient when persisted observations disagree. Matching files does not prove historical availability, between-cluster independence, exchangeability under time shift or causal regional effects.

| Research condition | Verified in this revision | Not established |
|---|---|---|
| H5 comparison inputs | Exact non-Seoul calibration population and observations | Causal effect of regional transfer |
| Traceability | Returned metadata, saved JSON and preserved hashes | Historical truth or publication vintage |
| Uncertainty | Existing cluster bootstrap and 15-evaluation rules retained | Coverage guarantees under dependence or shift |
| Outcome claims | 171 controlled tests pass | Real performance, supported hypotheses or completed paper |

[English project guide](levels/level5.md) · [한국어 같은 수준](../../9차/docs/차수설명.md#user-content-reading-level-5) · [Previous round at this level](round8.md#user-content-reading-level-5)
