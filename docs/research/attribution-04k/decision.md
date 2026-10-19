# annual borrowing on observed deployment

simulated effects on observed deployment — not player ability estimates

purpose: `research`; execution: `complete`; numerics: `verified`.

offense: on the fixed gaussian_base mixture, regional rms changes from 0.18209 independently to 0.178 with borrowing; paired mse benefit is 0.0014736 [0.0013634, 0.0015837]. cohort benefits are stable 0.003599 [0.0033744, 0.0038235]; reversal -0.0040702 [-0.0042977, -0.0038426]; onset -3.4268e-05 [-0.00013164, 6.3106e-05]. under null truth, borrowing / independent false-map rms is 0.002602 / 0.00091143; paired mse benefit is -5.9399e-06 [-9.1612e-06, -2.7186e-06].

attempts allowed: on the fixed gaussian_base mixture, regional rms changes from 0.18234 independently to 0.17876 with borrowing; paired mse benefit is 0.0012906 [0.0012057, 0.0013754]. cohort benefits are stable 0.0034878 [0.0032923, 0.0036834]; reversal -0.0045994 [-0.0048894, -0.0043093]; onset -0.00032067 [-0.00041289, -0.00022845]. under null truth, borrowing / independent false-map rms is 0.0026214 / 0.00092626; paired mse benefit is -6.014e-06 [-9.2749e-06, -2.7531e-06].

same-deployment prediction cost, borrowing minus independent: gaussian_half 0.038793 [-0.008159, 0.085745]; gaussian_base -0.47384 [-0.57289, -0.37478]; gaussian_double -3.9092 [-4.159, -3.6593]; gaussian_null 0.10393 [0.047064, 0.1608]; game_shared_base -0.44048 [-0.54698, -0.33397].

positive mse benefit favors borrowing; negative benefit is borrowing harm. positive prediction cost is borrowing harm. rms uses recorded unblocked attempts/60; benefits and costs use its square. brackets are 95% monte carlo t intervals for paired means, conditional on this truth, deployment and shared noise histories. crossing zero establishes neither equivalence nor acceptable cost; no winner or scientific gate is assigned.

| cell | role | borrowing / independent / zero regional rms | independent − borrowing mse, 95% interval |
|---|---|---:|---:|
| gaussian_half | offense | 0.091818 / 0.092719 / 0.093296 | 0.00016629 [0.00012719, 0.0002054] |
| gaussian_half | attempts allowed | 0.091969 / 0.09273 / 0.093282 | 0.00014057 [0.0001093, 0.00017184] |
| gaussian_base | offense | 0.178 / 0.18209 / 0.18659 | 0.0014736 [0.0013634, 0.0015837] |
| gaussian_base | attempts allowed | 0.17876 / 0.18234 / 0.18656 | 0.0012906 [0.0012057, 0.0013754] |
| gaussian_double | offense | 0.32717 / 0.3446 / 0.37318 | 0.011714 [0.011393, 0.012035] |
| gaussian_double | attempts allowed | 0.32897 / 0.34562 / 0.37313 | 0.011236 [0.010971, 0.011502] |
| gaussian_null | offense | 0.002602 / 0.00091143 / 0 | -5.9399e-06 [-9.1612e-06, -2.7186e-06] |
| gaussian_null | attempts allowed | 0.0026214 / 0.00092626 / 0 | -6.014e-06 [-9.2749e-06, -2.7531e-06] |
| game_shared_base | offense | 0.17791 / 0.18203 / 0.18659 | 0.0014808 [0.0013664, 0.0015951] |
| game_shared_base | attempts allowed | 0.17868 / 0.18227 / 0.18656 | 0.001293 [0.0012081, 0.0013778] |

rms uses sqrt(mean regional mse), in recorded unblocked attempts/60. regional mse divides by twelve times the selected player-role count. near and lateral diagnostics use their own single-functional denominators.

| cell | borrowing − independent prediction excess, 95% interval |
|---|---:|
| gaussian_half | 0.038793 [-0.008159, 0.085745] |
| gaussian_base | -0.47384 [-0.57289, -0.37478] |
| gaussian_double | -3.9092 [-4.159, -3.6593] |
| gaussian_null | 0.10393 [0.047064, 0.1608] |
| game_shared_base | -0.44048 [-0.54698, -0.33397] |

prediction cost and recovery benefit use (recorded unblocked attempts/60)². negative prediction excess is retained; positive paired cost means borrowing harms prediction. the reference is the same fitted-context zero-player predictor on identical deployment.

| gaussian base cohort | role | count | independent − borrowing regional mse, 95% interval |
|---|---|---:|---:|
| stable | offense | 548 | 0.003599 [0.0033744, 0.0038235] |
| stable | attempts allowed | 548 | 0.0034878 [0.0032923, 0.0036834] |
| reversal | offense | 137 | -0.0040702 [-0.0042977, -0.0038426] |
| reversal | attempts allowed | 137 | -0.0045994 [-0.0048894, -0.0043093] |
| onset | offense | 137 | -3.4268e-05 [-0.00013164, 6.3106e-05] |
| onset | attempts allowed | 137 | -0.00032067 [-0.00041289, -0.00022845] |
| no prior observation | offense | 118 | -0.00020994 [-0.00028856, -0.00013132] |
| no prior observation | attempts allowed | 118 | -0.00020462 [-0.00027044, -0.0001388] |

negative cohort benefit means borrowing harm. injected changes start at the final season; entry/return flags describe this corpus, not nhl debut or actual ability change. minute, returner, template, near/lateral and directional-bias diagnostics appear in [diagnostics.csv](diagnostics.csv). cohort flags overlap and cannot be summed.

the gaussian null cell reports absolute false-map error against the zero map. zero-target ratios are unavailable. endpoint winners and bounded-search limitations are reported without expanding the grid.

intervals describe monte carlo error across paired records, conditional on one fixed truth/deployment population and the declared gaussian laws. they are neither player intervals nor uncertainty over plausible populations. cells share noise histories. crossing zero establishes neither equivalence nor acceptable prediction cost. no winner, nominee or scientific pass/fail gate is assigned.

- one fixed simulated truth population on observed deployment; real-sized geometry does not make effects empirical
- twenty shared gaussian histories across research cells limit generality and precision; cells are not independent
- forty modes discard native detail; projection discrepancy is not a regional error floor
- league-relative carry approximates physical persistence while annual rates and exposure references change
- stable, reversal and onset proportions are arbitrary; actual entry and return flags are observation history, not nhl debut or ability change
- game-shared gaussian mean perturbations omit count-dependent shot noise and are not the earlier gamma-poisson law or empirical calibration
- same-deployment prediction uses fixed covariates and shared fitted context; it does not validate new lineups or future seasons
- monte carlo intervals condition on this truth, geometry and noise law; they are not player intervals or uncertainty over populations
- bounded scale-search limitations remain visible; no scientific pass gate, nominee, model admission or publication follows

next question: can an empirically justified annual prior preserve gains for stable players while reducing harm under reversals, first observations and null effects within a prospectively chosen prediction-cost budget?

`nomination:null, admission:not_admitted, handoff:null`.

[comparison and intervals](comparison.png) · [all metric records](metrics.csv) · [audit players](players.csv) · [verification](verification.md)
