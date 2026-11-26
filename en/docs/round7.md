# Round 7 · Strict Inputs and Model-Free Preflight

[한국어](../../7차/docs/차수설명.md) · **English**

[LEVEL 1](#user-content-reading-level-1) · [LEVEL 2](#user-content-reading-level-2) · [LEVEL 3](#user-content-reading-level-3) · [LEVEL 4](#user-content-reading-level-4) · [LEVEL 5](#user-content-reading-level-5)

**Real training remains stopped.** This round repairs reproduced input-boundary errors without training models, acquiring new sources or producing measured hypothesis outcomes. The existing eight hypotheses, 15 evaluations, formulas and citations remain unchanged.

<a id="reading-level-1"></a>

## LEVEL 1 - Beginner

A computer can read “−1 people” or “0.5 stations” as numbers. That does not make them sensible counts. This round rejects impossible feature values and malformed files before they can become model inputs. A preflight check is a checklist before an experiment; passing it does not prove a location, historical availability or a paper's hypothesis.

| Question | Current check | Important distinction |
|---|---|---|
| Is the table well formed? | Reject repeated/empty column names, missing fields, blank rows and broken row widths | A quoted comma or newline can still be valid CSV |
| Does the number make sense? | Counts must be integers; distance cannot be negative | Zero facilities or zero distance may be valid |
| Is every negative value wrong? | Preserve legitimate negative rates, year-on-year changes and basement relative floors | Do not apply a universal zero lower bound |
| Does “passed” mean research is ready? | Preflight checks feature input only | It neither trains a model nor authorizes training |

The technical suite recorded **161 passing checks**, with separate syntax checking. Actual feature input has not been supplied: the observed current preflight result is **missing_input, exit 2**, not a completed feature-validation result. A normal controlled test input is separate from real readiness. Final features, independent linkage truth, historical evidence and resource validation remain outstanding.

[Same-level guide](levels/level1.md) · [Round 6](round6.md#user-content-reading-level-1) · [Shared domains and evidence](#user-content-shared-contract)

<a id="reading-level-2"></a>

## LEVEL 2 - Explorer

The flow is **raw CSV structure → identities and numeric domains → feature/source/time observations → comparable Seoul runs → effects and intervals → displayed evidence**. File rows, feature observations, contracts and complex clusters are different denominators.

| Boundary | Required connection | Rejected shortcut |
|---|---|---|
| CSV bytes | Validate structure, then parse the same bytes | Silently skip blank rows or turn extra fields into an index |
| Observation | Entity, feature, value, validity period, publication time, source and record identity | Validate only a short feature/source list |
| Seoul H5 | Same source population and fixed method settings | Treat different fixed model parameters as only a geographic-transfer effect |
| Statistical decision | Fixed research settings and sufficient cluster/bootstrap evidence | Mark a technical run conclusive merely because an effect exists |

Feature observations use `[valid_from, valid_to)`; an empty end means open-ended validity, not a missing start. Publication timestamps require a timezone. Counts can be zero, but a missing observation is not an observed zero. Existing facility eligibility and historical backdating restrictions from Round 6 remain in force.

The cluster column is mandatory in saved predictions. Unknown cluster **values** can still leave uncertainty uncomputed; omitting the whole column must not silently change the evidence used in H5 comparisons. Real/synthetic mode, declared targets, fixed dates, complete Seoul IDs and source hashes retain Round 6's constraints.

[Same-level guide](levels/level2.md) · [Round 6](round6.md#user-content-reading-level-2) · [Shared domains and evidence](#user-content-shared-contract)

<a id="reading-level-3"></a>

## LEVEL 3 - Practitioner

Run from `7차/` in the documented project environment. The preflight CLI does **not import sklearn/engine or fit a model**. Its output must be a new file, and the parent directory must already exist.

```powershell
python -B -X utf8 -m rentlab.feature_preflight --features features.json --output new_preflight.json
python -B -X utf8 -m rentlab.feature_preflight --output missing_input.json
```

| Input or outcome | Status | Exit | How to read it |
|---|---|---:|---|
| Valid supplied feature input | `validated_input_only` | 0 | Input contract validated; whole-experiment readiness not evaluated |
| No supplied feature manifest | `missing_input` | 2 | Actual current readiness observation; not a passing real-input audit |
| Invalid input | `invalid_input` | 2 | Inspect recorded errors, including broken quotes, NUL or unsupported encoding |
| Report cannot be saved | Distinct failure message | 2 | Preserve the existing file; do not overwrite it |

The report records manifest, observation and validation-code hashes; total observation rows; rows per feature; distinct entity counts; source counts; value range; validity-start range; open-ended rows; and errors. These describe the **feature-observation table**, not contract counts or prediction performance.

Inspect `experiment_readiness=not_evaluated`, `training_started=false` and the unproven historical-availability/source-completeness fields. Contract joins, missingness by period, independent linkage truth, resource use and historical publication evidence require separate checks. Existing real acquisition/training JSON remains unchanged. Do not edit original data to manufacture a passing result.

[Same-level guide](levels/level3.md) · [Round 6](round6.md#user-content-reading-level-3) · [Korean input contract](../../7차/docs/7차_입력무결성.md)

<a id="reading-level-4"></a>

## LEVEL 4 - Advanced

| Component | Validation contract | Boundary retained |
|---|---|---|
| `input_contracts.strict_csv` | Reject duplicate/empty headers, missing columns, blank logical rows, row-width errors and NUL before pandas parsing | Parse the same validated bytes; preserve text IDs and leading zeros without duplicating the full row list |
| `validate_observations` | Apply the complete schema and duplicate rules in both manifest checking and actual joining | Recheck the hash of observation bytes actually read |
| `validate_holdout_settings` | Compare target set, library versions and fixed estimator parameters in runner and writer | Selected models and learned iteration counts are outcomes and may differ |
| Analysis configuration | Validate count/seed types and ranges | Fractional replicate counts or NaN cluster counts are not valid configurations |
| Model-free preflight | Validate supplied feature evidence and write a new report | No model import/fit; no automatic research-ready flag |

Saved prediction CSVs require `source_row_id`, `cluster_id`, `region`, `date`, `actual_won`, `prediction_won`. Quoted commas/newlines remain legal CSV. Identity, cluster, region and date strings retain their text representation; numeric columns may retain numeric types. NUL is rejected because different parsers can truncate identity or numeric cells inconsistently.

Observations require **all eight fields**: `entity_key`, `feature`, `value`, `valid_from`, `valid_to`, `published_at`, `source_id`, `record_id`. Required dates use ISO YYYY-MM-DD, publication time must be timezone-aware, and duplicate entity/feature/start/publication combinations or duplicate source/record pairs are rejected. Both manifest validation and actual feature joining use the same observation validator.

H5 compares targets, library versions and `parameters` inside `estimator_details` and `no_deposit_estimator_details`. REAL mode requires library/main-estimator configuration evidence. Fixed parameter differences cannot be described as only a regional-shift effect. Validation-selected models and learned iteration counts are results, so equality is not forced. Synthetic input cannot support paper hypotheses.

Missing cluster values may keep uncertainty unavailable, but a missing cluster column is an input error. Fixed scientific settings, requested bootstrap count and recorded valid replicates must agree before the dashboard accepts a conclusive state. The exact thresholds and decision directions are given at [LEVEL 5](#user-content-reading-level-5).

[Same-level guide](levels/level4.md) · [Round 6](round6.md#user-content-reading-level-4)

<a id="reading-level-5"></a>

## LEVEL 5 - Expert

The original H1–H8 and 15-evaluation family remain fixed. Prediction-interval miscoverage **alpha=.1** is separate from hypothesis-family error **.05**. The 90% prediction intervals, bootstrap formulas and hypothesis thresholds have not been redesigned.

| Fixed setting | Value | Interpretation |
|---|---:|---|
| Prediction `alpha` / `coverage_tolerance` | .1 / .02 | Existing prediction-interval contract |
| Hypothesis-family confidence / size | .95 / 15 | Existing familywise inference design |
| Default bootstrap replicates | 9,999 | Fewer replicates are technical verification only |
| Minimum clusters | 20 | Required for measured inference evidence |
| Minimum group observations / clusters | 30 / 5 | Existing subgroup eligibility |
| Regional calibration minimum | 100 | Existing calibration rule |
| Seed | 20261126 | Fixed research protocol |

Settings differing from `research_protocol`, or **B<9,999**, remain technical `partial/inconclusive` even if an effect is computable. Increasing B is allowed, but the displayed requested replicate count must equal the configuration. Measured rows require **k≥20** and **ceil(.8×B)≤B_valid≤B**. The 80% valid-replicate rule applies the existing calculation contract to displayed evidence; it is not a newly established statistical guarantee.

| Decision boundary | Required evidence or direction | Rejected inference |
|---|---|---|
| H6 | Low/high each have at least 20 complex clusters and neither exceeds total clusters; their sum cannot exceed total contracts | Conclusive subgroup contrast without sufficient cluster evidence |
| H3 equivalence | CI strictly inside (-.02,.02) → `support`; separated outside the range → `not_support`; otherwise `inconclusive` | Treating point estimates alone as interval evidence |
| Other directional hypotheses | CI lower bound >0 → `support`; upper bound ≤0 → `not_support` | Reversing the registered direction |
| Synthetic mode | Suppress conclusive paper support | Technical fixture outcomes presented as real evidence |
| Percentile CI | Finite ordered endpoints and valid bootstrap evidence | Forcing every interval to contain the point estimate |

The full Seoul population, snapshot, mode and fixed library/estimator settings remain prerequisites. Selected model identity and learned iteration count may differ as outcomes. Cluster percentile intervals remain approximate; temporal shift, cluster/regional dependence and learning uncertainty limit interpretation. No new significance claim, hypothesis, model-performance result, paper or validated novel statistic is introduced. Earlier [formulas and sources](../../7차/docs/논문_가설과_수식.md) and [exploratory expansion formulas](../../7차/docs/확장분석_수식과해석.md) remain preserved.

The combined suite recorded **161 passing checks in 25.416 seconds**, alongside Node `app.js` syntax checking. It includes regression fixtures aligned with the scientific contract; these are implementation checks, not new real-data experiments. The earlier audit's **2,857,449 cleaned contracts and 385,030 complex-linked contracts** retain their distinct denominator and selection-bias limitations. The history of viewing 2025 target aggregates is not hidden or reclassified as an untouched test set.

Independent physical facility identities, historical operation/publication records, independent complex-linkage truth, the final feature/comparison freeze, resource validation and a completed real training run remain outstanding. Actual training is `stopped_by_user`; model performance and hypothesis outcomes are unmeasured. No original data, models, private operational records or unpublished manuscripts are added to the public repository, and no paper PDF or release asset is created.

[Same-level guide](levels/level5.md) · [Round 6](round6.md#user-content-reading-level-5)

<a id="shared-contract"></a>

## Feature Domains and Shared Evidence

| Feature group | Accepted domain | Valid cases preserved |
|---|---|---|
| Population, households, facilities, transactions and day counts | Nonnegative integers; complex units/buildings/maximum floors require positive values | Zero transactions or facilities |
| Distance, area, parking/elevator ratios | Nonnegative | Zero distance or parking |
| Building coverage / floor-area ratio | Existing percentage units; 0–100 / nonnegative | Floor-area ratio 350% |
| Relative floor / rates and changes | Relative floor ≤1; rates/changes finite | Basement relative floor, negative rates and negative YoY |
| Price and price index | Positive | Missing data remains an absent observation |

These preserve the existing variable dictionary's units. They introduce no arbitrary outlier ceiling or new price threshold. An observed zero and a missing observation remain distinct. Domain validation does not certify coordinate truth, linkage correctness or national completeness. Round 6's full source-eligibility recomputation and ban on historically unproven backdating remain applicable.

| Verification layer | Recorded observation | Remaining condition |
|---|---|---|
| Technical tests | 161 pass | No measured model performance |
| Controlled preflight | Valid/missing/invalid/overwrite-rejection cases checked | Contract joins and whole-experiment readiness are separate |
| Actual feature input | No supplied manifest; `missing_input`, exit 2 | Final feature freeze incomplete |
| Training | Stopped | Historical truth, physical labels and resource validation outstanding |
