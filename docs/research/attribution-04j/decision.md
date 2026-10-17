# real-deployment attribution information

execution: `complete`; numerics: `verified`.

these are conditional sampling standard deviations for unbiased linear contrasts under the independent-row working-noise model, not calibrated player uncertainty, observed ability or universal estimation limits. units are redistributed recorded unblocked attempts/60. near sd means the within-20-ft, in-front-of-goal functional. total-shape variance is zero by construction; volume remains outside this analysis.

## final individual contrasts

all-player denominators include unavailable individuals. finite-sd quantiles condition on availability and use linear interpolation. pair means stay outside these distributions; they do not identify inseparable individuals.

| design / assumption / role | available / all | near sd p10 / median / p90 | regional rms sd median |
|---|---:|---:|---:|
| real / final annual / offense | 940 / 940 | 1.22365 / 1.56539 / 3.95915 | 0.897927 |
| real / constant physical history / offense | 940 / 940 | 0.406413 / 0.509134 / 1.92142 | 0.292045 |
| real / final annual / attempts allowed | 940 / 940 | 1.22365 / 1.56539 / 3.95915 | 0.897927 |
| real / constant physical history / attempts allowed | 940 / 940 | 0.406413 / 0.509134 / 1.92142 | 0.292045 |
| synthetic / final annual / offense | 30 / 32 | 1.15785 / 1.16241 / 1.18579 | 0.666774 |
| synthetic / constant physical history / offense | 30 / 32 | 0.517743 / 0.519054 / 0.530982 | 0.297736 |
| synthetic / final annual / attempts allowed | 30 / 32 | 1.15785 / 1.16241 / 1.18579 | 0.666774 |
| synthetic / constant physical history / attempts allowed | 30 / 32 | 0.517743 / 0.519054 / 0.530982 | 0.297736 |

weak conditional precision is shown by the magnitude and spread of sampling sds, with minutes groups in [summary.csv](summary.csv). no absolute accuracy threshold is inferred from those values. structural nonestimability differs from numerical disagreement.

| design / role / assumption | minutes group with largest available median near sd | median | available / all |
|---|---|---:|---:|
| real / offense / final annual | [0,300) | 3.25549 | 264 / 264 |
| real / offense / constant physical history | [0,300) | 1.48637 | 264 / 264 |
| real / attempts allowed / final annual | [0,300) | 3.25549 | 264 / 264 |
| real / attempts allowed / constant physical history | [0,300) | 1.48637 | 264 / 264 |
| synthetic / offense / final annual | [600,1000) | 1.16241 | 30 / 32 |
| synthetic / offense / constant physical history | [600,1000) | 0.519054 | 30 / 32 |
| synthetic / attempts allowed / final annual | [600,1000) | 1.16241 | 30 / 32 |
| synthetic / attempts allowed / constant physical history | [600,1000) | 0.519054 | 30 / 32 |

- synthetic / final annual / offense: not estimable: 2.
- synthetic / constant physical history / offense: not estimable: 2.
- synthetic / final annual / attempts allowed: not estimable: 2.
- synthetic / constant physical history / attempts allowed: not estimable: 2.

## persistence and selected cases

constant physical history retains the final-current population and final exposure weights. history-only identities remain nuisance columns. its precision gain depends on the assumption that physical effects do not change, with separate unknown context means each year.

| design / role | matched available | newly estimable | history / annual near-sd p10 / median / p90 |
|---|---:|---:|---:|
| real / offense | 940 | 0 | 0.243861 / 0.342659 / 0.788955 |
| real / attempts allowed | 940 | 0 | 0.243861 / 0.342659 / 0.788955 |
| synthetic / offense | 30 | 0 | 0.444331 / 0.446335 / 0.451972 |
| synthetic / attempts allowed | 30 | 0 | 0.444331 / 0.446335 / 0.451972 |

| design / case / role / assumption | status | near sd |
|---|---|---:|
| real / historical_scalar_shared / offense / final annual | available | 3.1745 |
| real / historical_scalar_no_shared / offense / final annual | available | 2.51267 |
| real / maximum_final_spatial_shared / offense / final annual | available | 3.1745 |
| real / historical_scalar_shared / attempts allowed / final annual | available | 3.1745 |
| real / historical_scalar_no_shared / attempts allowed / final annual | available | 2.51267 |
| real / maximum_final_spatial_shared / attempts allowed / final annual | available | 3.1745 |
| real / historical_scalar_shared / offense / constant physical history | available | 0.783375 |
| real / historical_scalar_no_shared / offense / constant physical history | available | 0.532315 |
| real / maximum_final_spatial_shared / offense / constant physical history | available | 0.783375 |
| real / historical_scalar_shared / attempts allowed / constant physical history | available | 0.783375 |
| real / historical_scalar_no_shared / attempts allowed / constant physical history | available | 0.532315 |
| real / maximum_final_spatial_shared / attempts allowed / constant physical history | available | 0.783375 |
| synthetic / inseparable_26_31_difference / offense / final annual | not_estimable | unavailable |
| synthetic / inseparable_26_31_mean / offense / final annual | available | 0.509833 |
| synthetic / inseparable_26_31_difference / attempts allowed / final annual | not_estimable | unavailable |
| synthetic / inseparable_26_31_mean / attempts allowed / final annual | available | 0.509833 |
| synthetic / inseparable_26_31_difference / offense / constant physical history | not_estimable | unavailable |
| synthetic / inseparable_26_31_mean / offense / constant physical history | available | 0.227772 |
| synthetic / inseparable_26_31_difference / attempts allowed / constant physical history | not_estimable | unavailable |
| synthetic / inseparable_26_31_mean / attempts allowed / constant physical history | available | 0.227772 |

case overlap is descriptive, not an estimability test. absent members remain `not_in_target_population`; case coefficients and references are explicit in [contrasts.csv](contrasts.csv). duplicate labels preserve their meaning without extra calculation.

## deployment and saved selector evidence

| design / season | current / union players | contexts | directed team hours | rate, recorded attempts/60 |
|---|---:|---:|---:|---:|
| real / 20212022 | 1003 / 1477 | 42 | 2088.31 | 41.70845581877918 |
| real / 20222023 | 951 / 1477 | 42 | 2096.63 | 41.94727099385311 |
| real / 20232024 | 924 / 1477 | 42 | 2057.44 | 42.17476420252795 |
| real / 20242025 | 910 / 1477 | 42 | 2032.5 | 41.367292979989884 |
| real / 20252026 | 940 / 1477 | 42 | 2104.42 | 40.97895462965676 |
| synthetic / 20212022 | 32 / 34 | 6 | 79.2 | 40.0 |
| synthetic / 20222023 | 32 / 34 | 6 | 79.2 | 40.0 |
| synthetic / 20232024 | 32 / 34 | 6 | 79.2 | 40.0 |
| synthetic / 20242025 | 32 / 34 | 6 | 79.2 | 40.0 |
| synthetic / 20252026 | 32 / 34 | 6 | 79.2 | 40.0 |

source coverage, exclusions, rate/reference identities and costs remain in [designs.csv](designs.csv). included exposure does not establish complete-season time. physical elapsed time is half directed team time; pair minutes are not halved.

the real design has 42 contexts and synthetic training deployment has six; the comparison does not isolate teammate mixing. the synthetic design is one training deployment, not 600 independent deployments.

[selector-closure.csv](selector-closure.csv) retains 46 saved summary rows and their original intervals. truth-inspected fixed settings describe expected performance; adaptive rows describe realized performance. prediction excess stays separate from absolute prediction error. no paired interval is invented and no fixed setting becomes a deployable winner. 04i's selected-score optimism and null false-map risks qualify the historical failed selector verdict without changing it.

[four-panel exposure and working-precision figure](information.png) · [complete designs](designs.csv) · [complete contrasts](contrasts.csv) · [denominators and quantiles](summary.csv)

## one subsequent benchmark proposal

use the bound five-season real spatial design and its recorded coverage; retain all final-current players and history-only nuisance identities. report the fixed exposure groups, strongest-partner overlap fractions and structurally available/unavailable targets separately. keep exact inseparable-pair means distinct from individuals.

predeclare a one-attempt/60 transfer between broad regions, with half/double sensitivity. this moves 16 2/3 recorded attempts over 1000 player minutes: a counting-scale scenario chosen independently of observed precision, not an estimated effect distribution or required accuracy. assess stable effects, corpus entry/return and final-season changes including reversal and entry from zero.

retain the declared independent-row working covariance as the primary noise assumption and predeclare a separate game-shared pace sensitivity. ask one estimator question: does annual borrowing improve final-season broad-region recovery over season-independent estimation at a prospectively justified prediction-cost budget? this proposes a next specification; it assigns no fitting or benchmark execution.

the historical recovery and selector verdicts remain unchanged. no player ability, complete-rate adequacy, empirical uncertainty, supported chance valuation, admission or publication follows.

`nomination:null, admission:not_admitted, handoff:null`.
