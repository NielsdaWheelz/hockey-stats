# deployment-information verification

this report reads saved analysis and closure values; it performs no source selection, response decoding or eigendecomposition.

research uses the bound corrected real and original synthetic training designs.

numerical status: `verified`.

| check | verified | value | limit |
|---|---|---:|---:|
| eigen_equation | True | 3.71467e-15 | 1e-10 |
| role_gauges | True | 1.50178e-14 | 1e-10 |
| available_contrast_solve | True | 5.54588e-12 | 1e-08 |
| eigen_equation | True | 3.65722e-15 | 1e-10 |
| role_gauges | True | 1.83557e-14 | 1e-10 |
| available_contrast_solve | True | 1.50622e-11 | 1e-08 |
| eigen_equation | True | 3.60047e-15 | 1e-10 |
| role_gauges | True | 1.89816e-14 | 1e-10 |
| available_contrast_solve | True | 3.60587e-11 | 1e-08 |
| eigen_equation | True | 3.56949e-15 | 1e-10 |
| role_gauges | True | 1.93625e-14 | 1e-10 |
| available_contrast_solve | True | 2.36015e-11 | 1e-08 |
| eigen_equation | True | 3.66008e-15 | 1e-10 |
| role_gauges | True | 1.79371e-14 | 1e-10 |
| available_contrast_solve | True | 5.33994e-12 | 1e-08 |
| eigen_equation | True | 4.57923e-15 | 1e-10 |
| role_gauges | True | 1.64586e-14 | 1e-10 |
| available_contrast_solve | True | 1.22688e-11 | 1e-08 |
| eigen_equation | True | 1.08056e-15 | 1e-10 |
| role_gauges | True | 3.24416e-15 | 1e-10 |
| available_contrast_solve | True | 6.52275e-15 | 1e-08 |
| eigen_equation | True | 9.23623e-16 | 1e-10 |
| role_gauges | True | 3.24016e-15 | 1e-10 |
| available_contrast_solve | True | 5.38431e-15 | 1e-08 |
| eigen_equation | True | 1.34146e-15 | 1e-10 |
| role_gauges | True | 3.22312e-15 | 1e-10 |
| available_contrast_solve | True | 5.9027e-15 | 1e-08 |
| eigen_equation | True | 8.44797e-16 | 1e-10 |
| role_gauges | True | 3.23087e-15 | 1e-10 |
| available_contrast_solve | True | 4.25512e-15 | 1e-08 |
| eigen_equation | True | 9.65829e-16 | 1e-10 |
| role_gauges | True | 3.25285e-15 | 1e-10 |
| available_contrast_solve | True | 5.37864e-15 | 1e-08 |
| eigen_equation | True | 1.0003e-15 | 1e-10 |
| role_gauges | True | 3.18171e-15 | 1e-10 |
| available_contrast_solve | True | 1.29702e-14 | 1e-08 |

independent reduced-gauge probes: 12; verified: 12. persistence comparisons: 1948; verified: 1948.

exact inventory:

```json
{
  "spectra": 12,
  "annual_player_contrasts": 9776,
  "historical_player_contrasts": 1944,
  "case_labels": 20,
  "contrast_rows": 11740,
  "distinct_calculations": 11736,
  "absent_case_labels": 0,
  "svd_probes": 12,
  "svd_decompositions": 2,
  "new_responses": 0,
  "new_fits": 0
}
```

resources:

```json
{
  "wall_seconds": 9.648159500000475,
  "peak_memory_bytes": 2602303488,
  "process_seconds": 9.573801999999999,
  "input_bytes": 255462700,
  "input_bytes_scope": "unique bound selected-source files; full archive bytes",
  "output_bytes": 5676732,
  "output_bytes_scope": "tree_before_current_manifest_serialization"
}
```

regional covariance is stored once; contrast q scales it. functional sds retain covariance cross terms. finite information arrays use explicit available-row indices; unavailable values remain null in tables. temporary integration/review receipts and their deletion record belong to the repository verification, not a permanent test suite.
