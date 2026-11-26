# Round 10 · Feature and spatial boundaries

This revision repairs feature-join and station-arithmetic input boundaries. The baseline is the documented Round 9 revision 1c2d797. Real-data acquisition and training remain stopped. It does not change the eight hypotheses, fifteen evaluations, formulas, time splits or statistical thresholds.

[한국어 상세](../../10차/docs/차수설명.md) · [English overview](../README.md) · [Previous Round 9](round9.md)

## Complete contract and observations

| Case | Before | Round 10 |
|---|---|---|
| Two apartments share row label 7 | Label-based assignment could overwrite both station/line counts: expected [1,2], observed [2,2] | Use internal positional indexing; restore the original index and order |
| Numeric and string identifiers are mixed | String coercion could merge observation keys or make line counts inconsistent | Reject non-string observation, contract and spatial identifiers |
| A generated provenance or missingness column already exists | Only the feature-value column was checked | Check value, __record and __missing names before assignment |
| Unknown contract join key | Missing feature | Still missing; no fabricated identifier |

Observation entity_key, source_id and record_id; contract source_row_id and its join key; and spatial cluster_id, facility_id and line identifiers must be strings. Existing missing-value rules remain: an unknown contract join key may remain unmatched, while missing required source-row, observation, facility or line identifiers are rejected. Strings 01 and 1 remain distinct. Do not use automatic string conversion to invent lost leading zeros. Standard feature CSVs are already read with string preservation. The original tables are not modified, and duplicate external row labels are preserved in the returned spatial table.

The all-invalid-coordinate return also preserves distance semantics, the Earth-radius convention and the historical-availability-unproven metadata. An additional assertion exposed one missing-metadata KeyError before this was repaired. Seven new regression methods initially exposed eleven failing subconditions. After repair, all seven and the complete 178-test suite passed after the early-return repair. A separate fixed-seed check used 40 controlled apartment origins, 25 physical stations and 30 station-line records, including duplicate origin indices. Direct haversine atan2 arithmetic agreed with nearest, 500 m and 1000 m station counts, unique nearby lines and transfer-station distance. The maximum nearest-distance difference was below 1.924e-9 m. This is numerical agreement for the supplied artificial coordinates, not measurement error or real-world location accuracy. Seed: 20261127; Earth-radius convention remains 6,371,008.8 m.

Known limits remain: 31 eligible rows lack cluster identity; independent location truth and complete contract-time facility, population and rental-data vintages are unproven. No real-data model was fitted, no source contract or facility data was repaired, and no new 4,845,086-row audit was performed here. That full-data audit remains a Round 8 observation. The original stopped_by_user record retained the same SHA-256. Real predictive performance, hypothesis support, complete manuscript and absolute absence of defects are not established. [Full Korean contract](../../10차/docs/10차_특징경계검증.md) · [Formulas and citations](../../10차/docs/논문_가설과_수식.md) · [Full source diff](../../10차/docs/전체차이.diff).

<a id="reading-level-1"></a>

## LEVEL 1 - Beginner

### Keep each apartment’s values separate

Repeated table-row labels do not mean the apartments are the same. The fix prevents one apartment’s station and line counts from overwriting another’s. Existing contract information cannot be replaced by new feature or provenance columns.

| Situation | Meaning | Action |
|---|---|---|
| Same row label, different apartment | Separate observations | Compute each apartment separately |
| A destination column already exists | Existing information | Reject the join |
| Apartment key is unknown | Insufficient evidence | Keep missing features |

[English project guide](levels/level1.md) · [한국어 같은 수준](../../10차/docs/차수설명.md#user-content-reading-level-1) · [Previous round at this level](round9.md#user-content-reading-level-1)

<a id="reading-level-2"></a>

## LEVEL 2 - Explorer

### Separate row labels, keys and features

A source-row ID identifies a contract; a cluster ID identifies an apartment; the DataFrame index is only a row label. String keys 01 and 1 remain distinct. Numeric 1 is not silently converted into string 1 for matching.

| Transition | Check | Result |
|---|---|---|
| Contract to observation | Exact string key | Match only identical keys |
| Apartment to spatial arithmetic | Unique cluster ID and coordinates | Ignore duplicate row labels internally |
| Feature to output | Value, source and missingness columns | Reject any existing-column collision |

[English project guide](levels/level2.md) · [한국어 같은 수준](../../10차/docs/차수설명.md#user-content-reading-level-2) · [Previous round at this level](round9.md#user-content-reading-level-2)

<a id="reading-level-3"></a>

## LEVEL 3 - Practitioner

### Run the boundary checks

With Python 3.12, fixed dependencies and the Rust parser, run python -B -X utf8 -m unittest discover -s tests -v from the revision folder. The full suite passed 178 controlled tests. Invalid identifier types and existing-column collisions raise ValueError; the program does not repair identifiers automatically. Real-data training remains stopped.

| Check | Input or location | Expected behavior |
|---|---|---|
| Seven regression methods | test_feature_boundaries_v10.py | Check duplicate indices, key types and output columns |
| Valid boundaries | 01/1 and unknown join keys | Preserve distinct values and missingness |
| Independent arithmetic | 40 controlled origins and 25 stations | Compare distances, counts, lines and transfer distance |

[English project guide](levels/level3.md) · [한국어 같은 수준](../../10차/docs/차수설명.md#user-content-reading-level-3) · [Previous round at this level](round9.md#user-content-reading-level-3)

<a id="reading-level-4"></a>

## LEVEL 4 - Advanced

### Separate positional updates from external labels

station_features resets the internal row index and restores the original index at return, including the all-missing-coordinate branch. validate_observations and join_features require string identifiers. Before writing output, join_features checks all three generated column names for every feature.

| Module | Boundary handling | Preservation |
|---|---|---|
| station_features | Positional assignment | Restore original labels and order |
| feature_store | String identifier validation | No forced coercion or key merging |
| join_features | Feature, __record and __missing column set | Reject collisions before assignment |

[English project guide](levels/level4.md) · [한국어 같은 수준](../../10차/docs/차수설명.md#user-content-reading-level-4) · [Previous round at this level](round9.md#user-content-reading-level-4)

<a id="reading-level-5"></a>

## LEVEL 5 - Expert

### Distinguish numerical agreement from location truth

BallTree outputs were compared with direct haversine atan2 arithmetic. This establishes consistency for the supplied coordinates, not surveyed location accuracy, historical facility operation, walking distance or nationwide completeness. The eight hypotheses, fifteen evaluations, fixed splits and scientific thresholds remain unchanged.

| Evidence | Verified scope | Not established |
|---|---|---|
| Direct distance calculation | Maximum difference below 1.924e-9 m | Surveyed location accuracy |
| Counts and transfers | 25 controlled physical stations, 30 line records | National facility completeness or walking distance |
| 178 regression tests | Technical contracts and prior behavior | Real performance, hypothesis support or absolute absence of defects |

[English project guide](levels/level5.md) · [한국어 같은 수준](../../10차/docs/차수설명.md#user-content-reading-level-5) · [Previous round at this level](round9.md#user-content-reading-level-5)
