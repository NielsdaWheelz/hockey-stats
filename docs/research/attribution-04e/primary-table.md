# 04e primary comparisons

year 5; 200 paired datasets per population/law cell. criterion rows give the mean contrast and two-sided percentile 95% monte carlo bounds from 10,000 whole-record resamples. means describe fresh physical truths and training responses, conditional on the fixed deployments and training references; these are not individual-player intervals. [the specification](../../specs/04e-attribution-pooling.md#recovery-comparison-criteria-and-decision) defines the four contrasts and exact support rules.

criterion columns are mean/lower/upper; diagnostic rows use control/candidate. regional and prediction risks have units `(attempts per 60 team minutes)^2`; false-map rms has units `attempts per 60 team minutes`. innovation variances are squared relative-rate coefficients. inactive risk and false-map rms use the all-thirty contrast denominator, including zero contributions from active pairs. all bound selections remain included. null rows have no recovery/retention ratio or nomination gate; control gains are negative in every non-null cell, so retention ratios are unavailable. prediction's zero baseline is the noisy training context, not an oracle.

| population | law | criterion / diagnostic | mean / control | lower / candidate | upper | status |
|---|---|---|---:|---:|---:|---|
| sparse | gaussian | regional_recovery_25pct | -0.041731336 | -0.043897562 | -0.039605533 | failed |
| sparse | gaussian | regional_improvement | 0.0058020449 | 0.0041660398 | 0.0075042002 | supported |
| sparse | gaussian | positive_control_prediction_gain | -2.9622053 | -3.3514755 | -2.5867278 | failed |
| sparse | gaussian | prediction_gain_retention_99pct | -2.1115094 | -2.3239915 | -1.909371 | failed |
| sparse | game_pace | regional_recovery_25pct | -0.05262091 | -0.058859322 | -0.047554275 | failed |
| sparse | game_pace | regional_improvement | -0.0035505688 | -0.0070282237 | -0.00071489044 | failed |
| sparse | game_pace | positive_control_prediction_gain | -13.407124 | -15.210663 | -11.66775 | failed |
| sparse | game_pace | prediction_gain_retention_99pct | -1.9887505 | -2.2628025 | -1.7342585 | failed |
| diffuse | gaussian | regional_recovery_25pct | -0.12725843 | -0.13614039 | -0.11819571 | failed |
| diffuse | gaussian | regional_improvement | 0.051232627 | 0.043560715 | 0.059008608 | supported |
| diffuse | gaussian | positive_control_prediction_gain | -2.7482301 | -3.0792852 | -2.4306159 | failed |
| diffuse | gaussian | prediction_gain_retention_99pct | -1.7529131 | -1.9305046 | -1.5830688 | failed |
| diffuse | game_pace | regional_recovery_25pct | -0.078916666 | -0.091609956 | -0.066328027 | failed |
| diffuse | game_pace | regional_improvement | 0.032557518 | 0.022752943 | 0.041681272 | supported |
| diffuse | game_pace | positive_control_prediction_gain | -12.128521 | -14.01951 | -10.447399 | failed |
| diffuse | game_pace | prediction_gain_retention_99pct | -1.7182759 | -1.9354747 | -1.5057239 | failed |
| sparse | gaussian | inactive regional risk (/30) | 0.0022296155 | 0.0076412517 | — | diagnostic |
| sparse | gaussian | false-map regional rms (/30) | 0.047218804 | 0.087414254 | — | diagnostic |
| sparse | gaussian | median year-five innovation variance | 1e-08 | low 1e-08; high 1e-08 | — | diagnostic |
| sparse | gaussian | bound-selection counts | 150 | low 127; high 159 | — | diagnostic |
| sparse | game_pace | inactive regional risk (/30) | 0.019822345 | 0.028390223 | — | diagnostic |
| sparse | game_pace | false-map regional rms (/30) | 0.14079185 | 0.16849399 | — | diagnostic |
| sparse | game_pace | median year-five innovation variance | 1e-08 | low 1e-08; high 1e-08 | — | diagnostic |
| sparse | game_pace | bound-selection counts | 133 | low 129; high 133 | — | diagnostic |
| diffuse | gaussian | inactive regional risk (/30) | 0 | 0 | — | diagnostic |
| diffuse | gaussian | false-map regional rms (/30) | 0 | 0 | — | diagnostic |
| diffuse | gaussian | median year-five innovation variance | 1e-08 | low 1e-08; high 1e-08 | — | diagnostic |
| diffuse | gaussian | bound-selection counts | 136 | low 132; high 142 | — | diagnostic |
| diffuse | game_pace | inactive regional risk (/30) | 0 | 0 | — | diagnostic |
| diffuse | game_pace | false-map regional rms (/30) | 0 | 0 | — | diagnostic |
| diffuse | game_pace | median year-five innovation variance | 1e-08 | low 1e-08; high 1e-08 | — | diagnostic |
| diffuse | game_pace | bound-selection counts | 138 | low 131; high 134 | — | diagnostic |
| null | gaussian | inactive regional risk (/30) | 0.0025955996 | 0.0094225163 | — | diagnostic |
| null | gaussian | false-map regional rms (/30) | 0.050947027 | 0.097069647 | — | diagnostic |
| null | gaussian | median year-five innovation variance | 1e-08 | low 1e-08; high 1e-08 | — | diagnostic |
| null | gaussian | bound-selection counts | 150 | low 135; high 149 | — | diagnostic |
| null | gaussian | absolute R risk; no ratio/gate | 0.0025955996 | 0.0094225163 | — | diagnostic |
| null | gaussian | absolute P risk; no ratio/gate | 1989.8431 | 1991.791 | — | diagnostic |
| null | game_pace | inactive regional risk (/30) | 0.023242894 | 0.031857264 | — | diagnostic |
| null | game_pace | false-map regional rms (/30) | 0.1524562 | 0.17848603 | — | diagnostic |
| null | game_pace | median year-five innovation variance | 1e-08 | low 1e-08; high 1e-08 | — | diagnostic |
| null | game_pace | bound-selection counts | 138 | low 150; high 132 | — | diagnostic |
| null | game_pace | absolute R risk; no ratio/gate | 0.023242894 | 0.031857264 | — | diagnostic |
| null | game_pace | absolute P risk; no ratio/gate | 1976.0287 | 1977.771 | — | diagnostic |
