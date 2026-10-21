# saved annual-prior accounting

simulated effects on observed deployment; no player ability estimates

under the frozen symmetric allocation, base stable-player gains and reversal harm accompany the largest absolute mean historical-carry terms in both roles. base first-observation harm instead accompanies changed current-signal weighting, offset by realized noise and with small net carry. under null truth, signal is exactly zero while mean noise and carry allocations are positive. these are signed realized allocations under the saved convention, not identified causes or evidence that resetting entry variance would help.

gaussian_base, offense, stable: mean paired mse change -0.00359896; symmetric signal/noise/carry allocations -6.56846e-06, 5.46537e-06, -0.00359786. the largest absolute mean allocation is carry; signal toward benefit, noise toward harm, carry toward benefit.

gaussian_base, offense, reversal: mean paired mse change 0.00407019; symmetric signal/noise/carry allocations -2.60988e-05, 6.83673e-06, 0.00408945. the largest absolute mean allocation is carry; signal toward benefit, noise toward harm, carry toward harm.

gaussian_base, offense, onset: mean paired mse change 3.42683e-05; symmetric signal/noise/carry allocations -2.17002e-05, 3.26899e-06, 5.26995e-05. the largest absolute mean allocation is carry; signal toward benefit, noise toward harm, carry toward harm.

gaussian_base, offense, no_prior_observation: mean paired mse change 0.000209937; symmetric signal/noise/carry allocations 0.000227209, -2.31086e-05, 5.83622e-06. the largest absolute mean allocation is signal; signal toward harm, noise toward benefit, carry toward harm.

gaussian_null, offense, all: mean paired mse change 5.93995e-06; symmetric signal/noise/carry allocations 0, 1.40937e-06, 4.53058e-06. the largest absolute mean allocation is carry; signal exactly zero, noise toward harm, carry toward harm.

gaussian_base, attempts_allowed, stable: mean paired mse change -0.00348781; symmetric signal/noise/carry allocations -3.54461e-05, 3.37973e-06, -0.00345575. the largest absolute mean allocation is carry; signal toward benefit, noise toward harm, carry toward benefit.

gaussian_base, attempts_allowed, reversal: mean paired mse change 0.00459936; symmetric signal/noise/carry allocations -2.03691e-05, 5.02172e-06, 0.00461471. the largest absolute mean allocation is carry; signal toward benefit, noise toward harm, carry toward harm.

gaussian_base, attempts_allowed, onset: mean paired mse change 0.000320669; symmetric signal/noise/carry allocations -2.28034e-05, -3.81781e-06, 0.000347291. the largest absolute mean allocation is carry; signal toward benefit, noise toward benefit, carry toward harm.

gaussian_base, attempts_allowed, no_prior_observation: mean paired mse change 0.000204618; symmetric signal/noise/carry allocations 0.000227164, -2.32987e-05, 7.53177e-07. the largest absolute mean allocation is signal; signal toward harm, noise toward benefit, carry toward harm.

gaussian_null, attempts_allowed, all: mean paired mse change 6.01403e-06; symmetric signal/noise/carry allocations 0, 1.41196e-06, 4.60207e-06. the largest absolute mean allocation is carry; signal exactly zero, noise toward harm, carry toward harm.

positive means borrowing harm, in squared recorded unblocked attempts/60. signed terms interact and retain response-dependent selection; these exact realized accounts do not identify an intervention. the actionable remedy remains unresolved; no next hypothesis is assigned.

positive loss change means borrowing harms recovery; negative means improvement. brackets are two-sided 95% monte carlo intervals across paired histories.

| primary cell | role | receiver | players | borrowing − independent mse | signal | noise | carry |
|---|---|---|---:|---:|---:|---:|---:|
| gaussian_base | offense | all | 940 | -0.0014736 [-0.0015837, -0.0013634] | 1.7726e-05 | 1.7582e-06 | -0.001493 |
| gaussian_base | offense | stable | 548 | -0.003599 [-0.0038235, -0.0033744] | -6.5685e-06 | 5.4654e-06 | -0.0035979 |
| gaussian_base | offense | reversal | 137 | 0.0040702 [0.0038426, 0.0042977] | -2.6099e-05 | 6.8367e-06 | 0.0040895 |
| gaussian_base | offense | onset | 137 | 3.4268e-05 [-6.3106e-05, 0.00013164] | -2.17e-05 | 3.269e-06 | 5.27e-05 |
| gaussian_base | offense | no prior observation | 118 | 0.00020994 [0.00013132, 0.00028856] | 0.00022721 | -2.3109e-05 | 5.8362e-06 |
| gaussian_base | attempts allowed | all | 940 | -0.0012906 [-0.0013754, -0.0012057] | 1.5598e-06 | -7.7895e-07 | -0.0012913 |
| gaussian_base | attempts allowed | stable | 548 | -0.0034878 [-0.0036834, -0.0032923] | -3.5446e-05 | 3.3797e-06 | -0.0034557 |
| gaussian_base | attempts allowed | reversal | 137 | 0.0045994 [0.0043093, 0.0048894] | -2.0369e-05 | 5.0217e-06 | 0.0046147 |
| gaussian_base | attempts allowed | onset | 137 | 0.00032067 [0.00022845, 0.00041289] | -2.2803e-05 | -3.8178e-06 | 0.00034729 |
| gaussian_base | attempts allowed | no prior observation | 118 | 0.00020462 [0.0001388, 0.00027044] | 0.00022716 | -2.3299e-05 | 7.5318e-07 |
| gaussian_null | offense | all | 940 | 5.9399e-06 [2.7186e-06, 9.1612e-06] | 0 | 1.4094e-06 | 4.5306e-06 |
| gaussian_null | offense | stable | 548 | 6.8389e-06 [3.1562e-06, 1.0521e-05] | 0 | 1.6538e-06 | 5.1851e-06 |
| gaussian_null | offense | reversal | 137 | 6.7053e-06 [3.0637e-06, 1.0347e-05] | 0 | 1.6003e-06 | 5.1049e-06 |
| gaussian_null | offense | onset | 137 | 6.7847e-06 [3.1414e-06, 1.0428e-05] | 0 | 1.545e-06 | 5.2397e-06 |
| gaussian_null | offense | no prior observation | 118 | -1.0393e-07 [-4.9518e-07, 2.8732e-07] | 0 | -1.0482e-07 | 8.8834e-10 |
| gaussian_null | attempts allowed | all | 940 | 6.014e-06 [2.7531e-06, 9.2749e-06] | 0 | 1.412e-06 | 4.6021e-06 |
| gaussian_null | attempts allowed | stable | 548 | 6.9412e-06 [3.2088e-06, 1.0674e-05] | 0 | 1.6206e-06 | 5.3206e-06 |
| gaussian_null | attempts allowed | reversal | 137 | 7.0513e-06 [3.1892e-06, 1.0913e-05] | 0 | 1.7171e-06 | 5.3342e-06 |
| gaussian_null | attempts allowed | onset | 137 | 6.5517e-06 [3.0391e-06, 1.0064e-05] | 0 | 1.5936e-06 | 4.9581e-06 |
| gaussian_null | attempts allowed | no prior observation | 118 | -1.2045e-07 [-5.39e-07, 2.981e-07] | 0 | -1.2216e-07 | 1.7146e-09 |

all loss changes, allocations and quadratic terms use (recorded unblocked attempts/60)². the denominator is twelve times each selected receiver count. receiver flags overlap; counts cannot be summed. null trajectory labels are bookkeeping, not changes in a zero truth.

| sensitivity cell | role | all | stable | reversal | onset | no prior observation |
|---|---|---:|---:|---:|---:|---:|
| gaussian_half | offense | -0.00016629 [-0.0002054, -0.00012719] | -0.00036107 [-0.00043164, -0.0002905] | 0.00031523 [0.0002667, 0.00036375] | -2.4258e-05 [-4.5942e-05, -2.5736e-06] | 1.4338e-05 [-2.5904e-06, 3.1267e-05] |
| gaussian_half | attempts allowed | -0.00014057 [-0.00017184, -0.0001093] | -0.00033904 [-0.00039879, -0.00027929] | 0.00037051 [0.00030885, 0.00043217] | 1.0687e-05 [-1.1996e-05, 3.337e-05] | 1.2163e-05 [-2.1387e-06, 2.6465e-05] |
| gaussian_base | offense | -0.0014736 [-0.0015837, -0.0013634] | -0.003599 [-0.0038235, -0.0033744] | 0.0040702 [0.0038426, 0.0042977] | 3.4268e-05 [-6.3106e-05, 0.00013164] | 0.00020994 [0.00013132, 0.00028856] |
| gaussian_base | attempts allowed | -0.0012906 [-0.0013754, -0.0012057] | -0.0034878 [-0.0036834, -0.0032923] | 0.0045994 [0.0043093, 0.0048894] | 0.00032067 [0.00022845, 0.00041289] | 0.00020462 [0.0001388, 0.00027044] |
| gaussian_double | offense | -0.011714 [-0.012035, -0.011393] | -0.032108 [-0.032736, -0.031479] | 0.045433 [0.044608, 0.046258] | 0.00061942 [9.252e-05, 0.0011463] | 0.00233 [0.0020598, 0.0026003] |
| gaussian_double | attempts allowed | -0.011236 [-0.011502, -0.010971] | -0.032336 [-0.032928, -0.031745] | 0.047609 [0.046529, 0.048688] | 0.0026006 [0.0021234, 0.0030778] | 0.0023712 [0.0021366, 0.0026059] |
| gaussian_null | offense | 5.9399e-06 [2.7186e-06, 9.1612e-06] | 6.8389e-06 [3.1562e-06, 1.0521e-05] | 6.7053e-06 [3.0637e-06, 1.0347e-05] | 6.7847e-06 [3.1414e-06, 1.0428e-05] | -1.0393e-07 [-4.9518e-07, 2.8732e-07] |
| gaussian_null | attempts allowed | 6.014e-06 [2.7531e-06, 9.2749e-06] | 6.9412e-06 [3.2088e-06, 1.0674e-05] | 7.0513e-06 [3.1892e-06, 1.0913e-05] | 6.5517e-06 [3.0391e-06, 1.0064e-05] | -1.2045e-07 [-5.39e-07, 2.981e-07] |
| game_shared_base | offense | -0.0014808 [-0.0015951, -0.0013664] | -0.0036255 [-0.0038598, -0.0033912] | 0.0041116 [0.0038762, 0.0043469] | 3.8621e-05 [-6.0985e-05, 0.00013823] | 0.00022293 [0.00014063, 0.00030522] |
| game_shared_base | attempts allowed | -0.001293 [-0.0013778, -0.0012081] | -0.0035052 [-0.0037094, -0.0033009] | 0.0046358 [0.0043189, 0.0049527] | 0.00032599 [0.00023036, 0.00042162] | 0.00021771 [0.00014913, 0.0002863] |

these are the same signed paired loss changes and intervals in every cell; the five cells are sensitivities on shared histories, not independent populations.

| cell | role | borrowing / independent / zero rms |
|---|---|---:|
| gaussian_half | offense | 0.091818 / 0.092719 / 0.093296 |
| gaussian_half | attempts allowed | 0.091969 / 0.09273 / 0.093282 |
| gaussian_base | offense | 0.178 / 0.18209 / 0.18659 |
| gaussian_base | attempts allowed | 0.17876 / 0.18234 / 0.18656 |
| gaussian_double | offense | 0.32717 / 0.3446 / 0.37318 |
| gaussian_double | attempts allowed | 0.32897 / 0.34562 / 0.37313 |
| gaussian_null | offense | 0.002602 / 0.00091143 / 0 |
| gaussian_null | attempts allowed | 0.0026214 / 0.00092626 / 0 |
| game_shared_base | offense | 0.17791 / 0.18203 / 0.18659 |
| game_shared_base | attempts allowed | 0.17868 / 0.18227 / 0.18656 |

rms is the saved sqrt(mean mse), in recorded unblocked attempts/60; its source-mse sd/se remain separately labeled in comparison.csv. null rms is absolute false-map error. no gain ratio is defined against zero null truth.

| cell | same-deployment prediction cost, 95% interval |
|---|---:|
| gaussian_half | 0.038793 [-0.008159, 0.085745] |
| gaussian_base | -0.47384 [-0.57289, -0.37478] |
| gaussian_double | -3.9092 [-4.159, -3.6593] |
| gaussian_null | 0.10393 [0.047064, 0.1608] |
| game_shared_base | -0.44048 [-0.54698, -0.33397] |

prediction cost is borrowing minus independent excess against the same fitted-context zero-player baseline, with the original directed-hour denominator and (recorded unblocked attempts/60)². positive is harm. the unchanged original recovery benefits, near/lateral functionals, prediction excesses and their denominator/zero-target rules remain in comparison.csv.

| primary cell | role | receiver | arm | signal error² | noise² | carry² | signal × noise | signal × carry | noise × carry |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| gaussian_base | offense | all | borrowing | 0.033051 | 0.00010884 | 0.00034455 | 2.0092e-05 | -0.0018401 | 1.9457e-07 |
| gaussian_base | offense | all | independent | 0.033031 | 0.00010876 | 0 | 1.862e-05 | 0 | 0 |
| gaussian_base | offense | no prior observation | borrowing | 0.034184 | 2.0691e-05 | 2.1011e-07 | 2.7757e-05 | 5.5818e-06 | 2.0352e-07 |
| gaussian_base | offense | no prior observation | independent | 0.033958 | 4.3006e-05 | 0 | 2.8034e-05 | 0 | 0 |
| gaussian_base | attempts allowed | all | borrowing | 0.033167 | 0.00010823 | 0.00034135 | -2.7577e-05 | -0.0016346 | 1.4971e-06 |
| gaussian_base | attempts allowed | all | independent | 0.033165 | 0.00010827 | 0 | -2.6924e-05 | 0 | 0 |
| gaussian_base | attempts allowed | no prior observation | borrowing | 0.034853 | 2.1048e-05 | 1.7449e-07 | 8.9061e-06 | 5.3628e-07 | 6.7952e-08 |
| gaussian_base | attempts allowed | no prior observation | independent | 0.034625 | 4.4057e-05 | 0 | 9.6122e-06 | 0 | 0 |
| gaussian_null | offense | all | borrowing | 0 | 2.2406e-06 | 4.5284e-06 | 0 | 0 | 1.7178e-09 |
| gaussian_null | offense | all | independent | 0 | 8.3071e-07 | 0 | 0 | 0 | 0 |
| gaussian_null | offense | no prior observation | borrowing | 0 | 2.165e-07 | 1.1337e-09 | 0 | 0 | 9.6495e-11 |
| gaussian_null | offense | no prior observation | independent | 0 | 3.2165e-07 | 0 | 0 | 0 | 0 |
| gaussian_null | attempts allowed | all | borrowing | 0 | 2.2801e-06 | 4.6079e-06 | 0 | 0 | -1.5971e-08 |
| gaussian_null | attempts allowed | all | independent | 0 | 8.5796e-07 | 0 | 0 | 0 | 0 |
| gaussian_null | attempts allowed | no prior observation | borrowing | 0 | 2.154e-07 | 1.3866e-09 | 0 | 0 | 7.0613e-10 |
| gaussian_null | attempts allowed | no prior observation | independent | 0 | 3.3795e-07 | 0 | 0 | 0 | 0 |

cross columns include the factor of two and retain negative cancellation. all six terms sum to each arm's mse. signal error includes omitted native detail, shrinkage and player mixing. selected covariances depend on responses: noise need not average to zero, its square is not sampling variance, and this is not a classical bias–variance decomposition.

| primary cell | role | no-prior players | reference allocation | update allocation | total carry |
|---|---|---:|---:|---:|---:|
| gaussian_base | offense | 118 | -9.1749e-07 | 6.7537e-06 | 5.8362e-06 |
| gaussian_base | attempts allowed | 118 | 6.5414e-07 | 9.9042e-08 | 7.5318e-07 |
| gaussian_null | offense | 118 | 7.4158e-10 | 1.4675e-10 | 8.8834e-10 |
| gaussian_null | attempts allowed | 118 | 1.7069e-09 | 7.6991e-12 | 1.7146e-09 |

a no-prior player's personal incoming mean is zero. exposure centering can still shift its reference, and coupled updating can transmit other input rows. these are noncausal channels under the frozen prior/reference convention. accounting.csv retains all eight source-mask allocations for every receiving cohort; history-only direct carry is zero. source masks trace saved rows, not ultimate historical origins or named-teammate causal influence.

intervals measure monte carlo error for response-dependent statistics under the fixed truth, design and declared noise law. scales/covariances vary across records; intervals do not condition on the realized fitted states. they are not player intervals or population uncertainty. crossing zero establishes neither equivalence nor acceptable prediction cost.

next hypothesis: none.

unresolved: `mechanism_interaction_unresolved`. the allocations and scale receipts do not distinguish inherited variance, carried covariance, selected update scale and coupling as an actionable intervention. no further diagnosis or experiment follows automatically.

- exact realized accounting conditional on selected covariances and scales; no causal attribution or classical bias–variance decomposition
- response-dependent noise transmission is neither independent of signal and carry nor a sampling variance
- one fixed native truth population and shared histories; five cells are not independent populations
- monte carlo intervals describe response-dependent statistics under fixed truth/design/noise; they are not player intervals
- source allocations depend on the frozen prior/reference convention and trace saved rows, not ultimate historical origins
- current-score weighting cannot identify inherited a separately from covariance, selected q and coupling
- same-deployment prediction retains the original fitted-context baseline and directed-hour denominator
- no intervention, fitted candidate, nomination, model admission or publication; entry-prior resetting remains untested

scale receipts are supporting context only; no refit, entry-prior reset, scale reselection, prediction threshold or new scientific gate is evaluated. truth-defined reversal/onset labels are assessment inputs only. no causal isolation, real-player support or private-model parity is established.

`nomination:null, admission:not_admitted, handoff:null`.

[paired intervals and signed terms](accounting.png) · [frozen comparisons](comparison.csv) · [complete accounting](accounting.csv) · [scale receipts](scales.csv) · [verification](verification.md)
