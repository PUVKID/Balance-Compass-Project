# Research round 4 · inputs, time-aware joins and exploratory comparisons

[한국어](../../4차/docs/차수설명.md) · [English overview](../README.md)

Balance Compass studies **apartment lease deposits, monthly rent, and prediction-interval reliability** across time and regions in South Korea. Deposits and monthly rent are separate targets; a monthly-rent prediction is conditional on the observed deposit, not an estimate of the causal effect of changing it.

**Real-data training is stopped. No completed measured model performance is available.** The collected 48 monthly source files for 2022–2025 contain 4,845,086 rows. Collection counts are not training-sample counts. Synthetic checks establish technical behavior, not support for research hypotheses. There is no completed manuscript or publication claim.

| Material or step | Available now | Still required |
|---|---|---|
| Contract input | Original 21 columns, row/source lineage and integrity checks | Final eligible analysis population and experiment freeze |
| Current facility snapshots | 12,004 school rows, 18,376 park rows, 898 railway-station rows acquired | Verified apartment coordinates, contract linkage and historical operation records |
| Apartment identifiers | 307,834 downloaded rows | Reconciliation with the advertised 44,628; the file is quarantined |
| Coordinate quality | One anomalous park coordinate recorded | Validation before using it as a predictor |
| Additional inputs | Acquisition and feature-validation code | Market/supply-demand statistics and historical publication/label records |
| Modeling | Eight existing hypotheses and 15 evaluations retained | Resource checks, frozen experiment and explicitly authorized real training |

| Change from round 3 | Round 4 | Boundary |
|---|---|---|
| Selected nine-column input | Preserve 21 original columns plus tracking IDs | No silent source rewrite |
| External-source candidates | Acquire current snapshots and validate metadata | Contract joins and historical status incomplete |
| Time split | Qualify observations by validity and publication time | Historical label availability remains unproven |
| Existing hypotheses | Add fixed-algorithm, paired information-group comparisons | Exploratory intervals remain separate |
| Technical checks | 100 total, including 19 new checks | Synthetic technical evidence, not real-data performance |

<a id="reading-level-1"></a>
## LEVEL 1 - Beginner

A collected file is like a box of receipts: having the receipts does not mean a prediction has been tested. Round 4 preserves the original fields and prepares information about nearby facilities. The program must still establish which facility observation belongs to each contract and whether that information existed at the relevant time.

| Question | Plain-language answer | What to check |
|---|---|---|
| What enters the study? | Lease-contract rows and separately sourced facility records | Original source, row count and file fingerprint |
| What would come out? | Separate deposit/rent predictions and ranges | Real training is stopped, so these are intended outputs, not measured results |
| How is accuracy read? | MAE is the average absolute difference between predicted and actual amounts | A small average does not make every individual prediction correct |
| Why show a range? | An interval expresses uncertainty around the prediction | Read inclusion rate together with interval width |

Start with the status table, then read the round at this same level. Treat missing results as unavailable; they are not zero. A facility-data download is not a verified link to a home, and a current facility list does not prove its historical state.

[Same-level guide](levels/level1.md) · [Korean round detail](../../4차/docs/차수설명.md#user-content-reading-level-1) · [Full 3 → 4 comparison · Korean](../../4차/docs/차수비교.md)

<a id="reading-level-2"></a>
## LEVEL 2 - Explorer

The pipeline separates source verification, feature construction, model selection, interval calibration and final evaluation. A file fingerprint checks whether the file is unchanged; it does not prove that the file covers every relevant contract or that its values were publicly available in the past.

| Stage | Input | Output and boundary |
|---|---|---|
| Audit | Source CSV, metadata and SHA-256 | Tracked rows and exclusion reasons; the original remains unchanged |
| Feature preparation | Contract key/date, facility coordinates and publication metadata | Matched features, missingness indicators and observation lineage |
| Fit | 2022–2023 contracts | Training-fitted preprocessing and candidate models |
| Select / calibrate | First / second half of 2024 | Validation-MAE selection / separate interval-calibration residuals |
| Evaluate | 2025 contracts | Errors, interval inclusion/width and regional summaries, once an experiment is completed |

Round 4 adds 21-column preservation and exploratory information-group comparisons. The candidate feature catalog does not mean all 62 candidates have been acquired. Current public snapshots must not be relabeled as proven historical observations.

[Same-level guide](levels/level2.md) · [Korean round detail](../../4차/docs/차수설명.md#user-content-reading-level-2) · [Full 3 → 4 comparison · Korean](../../4차/docs/차수비교.md)

<a id="reading-level-3"></a>
## LEVEL 3 - Practitioner

Use the round-4 execution specification as the command reference. Prepare Python 3.12 dependencies and the Rust money parser, validate the source manifest, and choose a new output folder. Existing outputs and original inputs are preserved. This guide does not authorize restarting the currently stopped training run.

| Check | Required action | Failure or limit |
|---|---|---|
| Input | Verify hashes, counts, original columns and row/cluster identifiers | Reject incompatible or unverifiable input |
| Features | Validate source, join key, validity and timezone-aware publication time | Strict execution is blocked without qualifying features and label history |
| Plan | Inspect the default execution plan before using `--execute` | The default does not fit a model |
| Outputs | Read audit, prediction and comparison outputs together | Synthetic technical checks are not real-data results |
| Recovery | Observe locks, atomic state and explicit interruption status | A stopped experiment is not automatically restarted |

The dashboard reads results; it is not a training or collection API. Historical round-3 commands remain in the linked Korean execution reference. Use round-4 instructions for the new feature-expansion path, and distinguish source acquisition from feature qualification.

[Same-level guide](levels/level3.md) · [Korean round detail](../../4차/docs/차수설명.md#user-content-reading-level-3) · [Full 3 → 4 comparison · Korean](../../4차/docs/차수비교.md)

<a id="reading-level-4"></a>
## LEVEL 4 - Advanced

Round 4 separates raw-input preservation, public-source acquisition, feature validation/joining, spatial feature construction and exploratory modeling. The join must keep contract row identity and count unchanged rather than expand an ambiguous one-to-many match.

| Module boundary | Implementation | Design trade-off |
|---|---|---|
| `research_input` / `public_sources` | Preserve original fields and track acquired public snapshots | Collection is not historical eligibility |
| `feature_store` | Reject malformed provenance and ambiguous latest observations; track missingness and record lineage | Unmatched information remains missing |
| `spatial_features` | Haversine/BallTree straight-line distance and radius counts | These are not walking distances or historical facility availability |
| `expansion` | Select Ridge/HGB by full-information validation MAE, then hold the algorithm fixed for group-removal comparisons | All comparisons use the same eligible contracts |
| Preprocessing | Fit missing-value replacement and categories on training rows | Price-aggregate paths without holdout lineage are blocked |

The information-group comparison measures predictive contribution under this protocol. It does not identify a causal treatment effect. The same input, target, contracts and algorithm are necessary to interpret differences; changing them would confound the comparison.

[Same-level guide](levels/level4.md) · [Korean round detail](../../4차/docs/차수설명.md#user-content-reading-level-4) · [Full 3 → 4 comparison · Korean](../../4차/docs/차수비교.md)

<a id="reading-level-5"></a>
## LEVEL 5 - Expert

Strict joins require both a valid interval `[from, to)` and publication strictly before contract-day 00:00 Asia/Seoul. A timezone-less publication timestamp, ambiguous latest observation or duplicate source observation is rejected. The code checks declared timing and provenance; independent historical evidence remains necessary.

| Review dimension | Criterion | Remaining limit |
|---|---|---|
| Temporal eligibility | Latest unique qualifying observation with traceable source/record IDs | Training and calibration labels also need historical availability evidence; strict execution is currently blocked without it |
| Predictive comparison | Paired absolute-error differences on the same contracts; fixed selected algorithm | Exploratory predictive association, not causation |
| Uncertainty | Apartment-cluster resampling, 9,999 percentile draws and approximate 95% intervals | Unknown clusters or fewer than 20 clusters yield no interval |
| Multiplicity | Separate exploratory intervals from the existing 15-evaluation confirmatory family | Pointwise exploratory intervals do not replace family-level control |
| Reproducibility | Frozen sources, hashes, splits, fitted preprocessing and resource checks | A freeze and resource qualification remain incomplete |

Cluster resampling does not resolve every common spatial/temporal shock or model-fitting uncertainty. Candidate input completeness, nationwide performance and coverage under distribution shift are not established by the synthetic regression checks. Read missing or blocked outputs explicitly, and retain the distinction between current snapshots and historical reconstruction.

[Same-level guide](levels/level5.md) · [Korean round detail](../../4차/docs/차수설명.md#user-content-reading-level-5) · [Full 3 → 4 comparison · Korean](../../4차/docs/차수비교.md)

