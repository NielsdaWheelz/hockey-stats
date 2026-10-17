# observable regional penalty selection

execution: `complete`; numerics: `verified`; progress: `failed`.

the prospective comparison fails: sparse / gaussian: regional benefit; sparse / gaussian: prediction retention; sparse / game pace: regional benefit; sparse / game pace: prediction retention; diffuse / gaussian: prediction retention; diffuse / game pace: prediction retention. partial improvements remain below.

158 target/partition diagnostics deteriorate in mean. each appears with its interval in [the adjacent diagnostic table](diagnostics.md); these are not extra vetoes.
contrary diagnostics by cell: sparse / gaussian: 29 across twelve-region vector, within 20 ft, in front of goal, lateral redistribution; transitions included. sparse / game pace: 29 across twelve-region vector, within 20 ft, in front of goal, lateral redistribution; transitions included. diffuse / gaussian: 21 across twelve-region vector, within 20 ft, in front of goal, lateral redistribution; transitions included. diffuse / game pace: 19 across twelve-region vector, within 20 ft, in front of goal, lateral redistribution; transitions included. null / gaussian: 30 across twelve-region vector, within 20 ft, in front of goal, lateral redistribution; transitions included. null / game pace: 30 across twelve-region vector, within 20 ft, in front of goal, lateral redistribution; transitions included.

candidate: pooled history, regional-score selection, 11 spatial modes. control: pooled history, marginal-likelihood selection, 11 spatial modes.

| population / law | candidate / control regional rms | regional benefit, 95% interval | candidate / control error:zero ratio | control gain, 95% interval | prediction cost / allowance | retention margin, 95% interval | benefit / gain / retention |
|---|---:|---:|---:|---:|---:|---:|---|
| sparse / gaussian | 0.067194 / 0.0591 | -0.012266 [-0.01858, -0.0067404] | 1.2152 / 0.94007 | 0.42276 [0.3498, 0.50119] | 2.9838 / 0.0042276 | -2.9796 [-4.047, -2.0049] | failed / supported / failed |
| sparse / game pace | 0.066134 / 0.059105 | -0.010563 [-0.018345, -0.0047707] | 1.1771 / 0.94022 | 0.3283 [0.21385, 0.43332] | 2.6638 / 0.003283 | -2.6605 [-3.911, -1.6563] | failed / supported / failed |
| diffuse / gaussian | 0.11279 / 0.11035 | -0.006544 [-0.014488, 0.00026139] | 0.85408 / 0.81747 | 4.9582 [4.5097, 5.433] | 4.7068 / 0.049582 | -4.6572 [-6.102, -3.3566] | inconclusive / supported / failed |
| diffuse / game pace | 0.11156 / 0.11014 | -0.0037739 [-0.0086408, 0.0009689] | 0.83554 / 0.81443 | 4.9674 [4.5099, 5.4229] | 4.295 / 0.049674 | -4.2453 [-5.4017, -3.1513] | inconclusive / supported / failed |
| null / gaussian | 0.021433 / 0.0024246 | -0.005442 [-0.0078993, -0.0032509] | unavailable / unavailable | -0.057111 [-0.088921, -0.030851] | 1.3318 / -0.00057111 | -1.3323 [-1.8615, -0.84844] | not_applicable / not_applicable / not_applicable |
| null / game pace | 0.020925 / 0.0027888 | -0.0051611 [-0.0075595, -0.0030914] | unavailable / unavailable | -0.075819 [-0.11582, -0.04189] | 1.2857 / -0.00075819 | -1.2865 [-1.7972, -0.83699] | not_applicable / not_applicable / not_applicable |

regional rms = sqrt(mean regional risk / 12), in redistributed recorded unblocked attempts/60 per player-role/region. benefit, gains, cost, allowance and margin use (attempts/60)²; prediction uses the inverse-share full-lineup metric. allowance is 1% of mean control gain. ratios use mean risks; null ratios are unavailable, with absolute false-map risks shown below.

null / gaussian absolute false-map risk: candidate 0.0055126 [0.0033221, 0.007969]; control 7.0543e-05 [3.6919e-05, 0.00011151]; paired change -0.005442 [-0.0078993, -0.0032509]. diagnostic only.
null / game pace absolute false-map risk: candidate 0.0052544 [0.0031986, 0.0076404]; control 9.3326e-05 [5.1273e-05, 0.00014367]; paired change -0.0051611 [-0.0075595, -0.0030914]. diagnostic only.

[paired values and full diagnostics](comparison.csv) · [adjacent diagnostics](diagnostics.md) · [benefit and retention figure](selection.png)

the figure and intervals describe mean experimental performance across complete outer records, conditional on fixed designs and exposed truth populations. they are not individual-player intervals, simultaneous bands or untouched confirmation. within-20-ft and lateral functionals retain their single-functional rms; full target denominators and signed context/projection terms are preserved.

risk:zero ratios and .75 × mean zero risk − mean fitted risk in the csv are historical context, not gates. selection scores are not player precision, prediction risk or post-selection unbiased error.

- the gaussian working covariance can be misspecified under non-null game pace
- the final-season unregularized regional reference is noisy; the selected minimum is not unbiased selected-estimator risk
- constant history can misrepresent changing players; eleven modes omit physical native detail
- a regional benefit does not establish uniform functional or player recovery
- the strict 99% gain-retention policy may remain unresolved with 100 exposed records per cell
- intervals describe mean experimental performance conditional on fixed designs and exposed truth populations; no player intervals or simultaneous bands
- the inseparable 26/31 average retains weight two; its individual difference remains unavailable
- spatial prediction does not establish complete-rate validity, real-player recovery, calibrated uncertainty or supported chance valuation
- no nomination, model admission or publication follows from developmental progress

`nomination:null, admission:not_admitted, handoff:null`.
