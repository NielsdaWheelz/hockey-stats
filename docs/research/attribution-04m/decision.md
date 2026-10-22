# empirical attribution benchmark

does existing annual borrowing reduce error for recorded spatial shape in held-out final-season games, compared with an independent-season fit and training-fitted context alone?

purpose: `research`; execution: `complete`; numerics: `verified`.

## evidence and partition

the recorded population is locatable unblocked attempts during reconstructed genuine 5v5, with paired team directions, matched spatial counts/time and zero-event exposure. block-contact locations and unsupported complete player rates are excluded.

the admitted final inventory has 1312 games: 1051 training and 261 assessment (19.893%). training retains 1682.973 directed hours and 68906 recorded unblocked attempts; assessment retains 421.4483 directed hours and 17331 attempts. 0 assessment games have zero retained time and remain sampling/calendar units. directed hours count both team directions and equal twice matched physical game-clock hours; source-ledger retained_seconds remains physical game-clock time.

the fixed split reserves the first floor(month game count / 5) ids after the declared sha256 ordering within each inventory calendar month. [game-scores.csv](game-scores.csv) names every withheld game, date, retained count/time, coverage record and source identity. all earlier seasons are training; final references, players, context means and penalties use final training games only. the first-season spatial reference and forty-mode basis stay fixed.

annual training coverage:

| season | training games | active training players | directed hours | recorded attempts | source zero-time games |
|---|---:|---:|---:|---:|---:|
| 20212022 | 1312 | 1003 | 2088.306 | 87100 | 8 |
| 20222023 | 1312 | 951 | 2096.632 | 87948 | 0 |
| 20232024 | 1312 | 924 | 2057.439 | 86772 | 0 |
| 20242025 | 1312 | 910 | 2032.499 | 84079 | 59 |
| 20252026 | 1051 | 935 | 1682.973 | 68906 | 2 |

all earlier seasons are wholly training; the final row contains final training games only. source zero-time games count the full annual source inventory, including the final season before partitioning. historical source gaps affect incoming history and are separate from final assessment coverage. the research source's zero-time historical games include unresolved captured-source gaps. the frozen ledgers do not distinguish newly catalogued failure types, so their measured attribution impact remains unresolved. no source correction, additional exclusion or later coverage estimate is substituted here.

source-ledger coverage retains its original units and overlapping categories:

| source field | value |
|---|---:|
| measured_games | 1312 |
| score_unavailable_games | 0 |
| unknown_horizon_games | 0 |
| unresolved_membership_games | 297 |
| supported_seconds | 3791019 |
| retained_seconds | 3787959 |
| excluded_seconds | 3060 |
| recognized_attempts | 87486 |
| retained_attempts | 86237 |
| excluded_attempts | 1249 |
| collateral_attempts | 109 |
| unassigned_attempts | 1139 |
| unallocated_ownership_attempts | 0 |
| common_population_seconds | 3787959 |
| common_population_all_attempts | 119438 |
| common_population_unblocked_attempts | 86237 |
| unresolved_membership_seconds | 57215 |

recording and reconstructed membership/exposure gaps can be selective; shared source defects need not cancel. matching counts/time does not establish ignorable missingness. exact source lineage and producer identities are bound in result.json.

## conditional paired differences

negative means the first arm has lower recorded-shape error; positive means higher error. units are (recorded unblocked attempts/60)². these are signed differences of error, without observed self energy; absolute mse and rmse are unavailable. the denominator is twelve times pooled directed hours, rather than an average of game rates. both team directions remain one game.

| contrast | pooled difference | scheme | 95% interval | direction across all schemes |
|---|---:|---|---:|---|
| borrowing − independent | -0.06822603 | games | [-0.1055652, -0.03270329] | `supported_lower_loss` |
| borrowing − independent | -0.06822603 | calendar_7_day | [-0.1065836, -0.03236563] | `supported_lower_loss` |
| borrowing − independent | -0.06822603 | calendar_14_day | [-0.1066949, -0.03626017] | `supported_lower_loss` |
| borrowing − context | -0.2325712 | games | [-0.3013639, -0.1640615] | `supported_lower_loss` |
| borrowing − context | -0.2325712 | calendar_7_day | [-0.310907, -0.1598798] | `supported_lower_loss` |
| borrowing − context | -0.2325712 | calendar_14_day | [-0.310163, -0.1626208] | `supported_lower_loss` |
| independent − context | -0.1643452 | games | [-0.2126443, -0.116549] | `supported_lower_loss` |
| independent − context | -0.1643452 | calendar_7_day | [-0.2190449, -0.1121739] | `supported_lower_loss` |
| independent − context | -0.1643452 | calendar_14_day | [-0.2141384, -0.1159216] | `supported_lower_loss` |

a supported direction requires all three valid intervals to lie strictly on the same side of zero. otherwise direction is unresolved. these conditional diagnostics have no new minimum-gain gate, multiplicity control, equivalence, noninferiority or model nomination. 2,000 draws use one paired matrix per scheme across all contrasts and regions, with seed 404130 and linear percentile quantiles. seven- and fourteen-day blocks begin at the earliest withheld inventory date and include intervening empty blocks. zero-denominator draws remain unavailable. intervals omit fitting/selection, split and population uncertainty.

## native inverse-share contrasts

the native paired difference weights each cell by 1/p and divides by directed hours, without the regional factor of twelve. it has a different spatial emphasis and normalization. each metric retains its own conditional direction; a regional advantage does not establish a native-cell gain.

| contrast | native pooled difference | scheme | 95% interval | direction across all schemes |
|---|---:|---|---:|---|
| borrowing − independent | 6.805161 | games | [-5.068372, 18.38167] | `unresolved` |
| borrowing − independent | 6.805161 | calendar_7_day | [-4.369886, 18.2591] | `unresolved` |
| borrowing − independent | 6.805161 | calendar_14_day | [-4.994725, 18.19651] | `unresolved` |
| borrowing − context | -18.50799 | games | [-36.1781, -0.5649315] | `unresolved` |
| borrowing − context | -18.50799 | calendar_7_day | [-35.16824, -2.177464] | `unresolved` |
| borrowing − context | -18.50799 | calendar_14_day | [-37.41176, 0.2385483] | `unresolved` |
| independent − context | -25.31315 | games | [-37.84373, -12.76837] | `supported_lower_loss` |
| independent − context | -25.31315 | calendar_7_day | [-38.17387, -12.77838] | `supported_lower_loss` |
| independent − context | -25.31315 | calendar_14_day | [-37.13964, -14.56674] | `supported_lower_loss` |

the regional aggregate does not imply the same direction in every region. these fixed regional rows retain their own point differences and directions across all three schemes; intervals remain in comparison.csv.

| region | borrowing − independent point difference | direction across all schemes |
|---|---:|---|
| behind_goal_negative_y | 2.499849e-06 | `unresolved` |
| behind_goal_positive_y | -0.00461337 | `supported_lower_loss` |
| outside_attacking_zone_negative_y | -0.02273507 | `unresolved` |
| outside_attacking_zone_positive_y | -0.00426402 | `unresolved` |
| in_zone_0_10_negative_y | -0.001814816 | `unresolved` |
| in_zone_0_10_positive_y | -0.03721441 | `unresolved` |
| in_zone_10_20_negative_y | 0.02745908 | `unresolved` |
| in_zone_10_20_positive_y | -0.03316436 | `unresolved` |
| in_zone_20_40_negative_y | -0.1151999 | `unresolved` |
| in_zone_20_40_positive_y | -0.1297381 | `unresolved` |
| in_zone_40_plus_negative_y | -0.2961406 | `supported_lower_loss` |
| in_zone_40_plus_positive_y | -0.2012892 | `unresolved` |

## support and bounded diagnostics

support groups are exclusive within each role: positive final training exposure (`current_training`), earlier exposure only (`carried_only`), or neither (`new_to_fit`). the separate `first_in_corpus_final` flag overlaps them and means first observed in this corpus during the final season; it does not mean nhl debut or an ability change. player participation overlaps within a lineup, so on-ice hours are not independent observations.

| role | support group | assessment members | on-ice hours |
|---|---|---:|---:|
| offense | current_training | 861 | 2106.402 |
| offense | carried_only | 4 | 0.6952778 |
| offense | new_to_fit | 1 | 0.1447222 |
| offense | first_in_corpus_final | 85 | 105.8728 |
| defense | current_training | 861 | 2106.402 |
| defense | carried_only | 4 | 0.6952778 |
| defense | new_to_fit | 1 | 0.1447222 |
| defense | first_in_corpus_final | 85 | 105.8728 |

new-to-fit identities receive their declared zero raw prior mean; carried-only identities use the borrowing posterior, including covariance-mediated updates. their assessment exposure remains included. each arm compensates context using its own uncentered maps. support signed residual associations divide summed on-ice residuals by group on-ice hours; zero hours is unavailable. they supply neither individual accuracy, cohort squared loss nor a residual ranking.

the twelve regions partition native cell centers in shooting-team coordinates (feet), with attacks toward positive x and the goal at (89, 0). precedence is x > 89 behind the goal, then x ≤ 25 outside the attacking zone, then radial goal-distance bands <10, [10,20), [20,40) and ≥40 feet. each region is split by negative/positive y; y = 0 contributes half to each side.

[comparison.csv](comparison.csv) retains twelve regional contrasts and the native inverse-share metric; [diagnostics.csv](diagnostics.csv) retains fixed calendar, game mean-shape, support residual and bounded-probe summaries. the bound native diagnostic archive preserves cell coordinates, coverage and observed/predicted means with signed residuals. these native means describe joint recorded shape; they are not player-effect maps. the [figure](comparison.png) shares the signed-loss convention and has its numeric companion in comparison.csv.

## numerical interpretation and remaining question

each saved state has its declared bounded probe with fixed incoming history; final alternatives are rescored alone and together on the same assessment draws. a failed state probe or changed aggregate classification makes numerical interpretation unresolved. regional/native movement remains diagnostic. endpoint winners and inherited `scale_unresolved` are bounded-search limitations; these checks are neither global-optimization guarantees nor propagated-history sensitivity. 
home/period/score context, forty-mode geometry and relative-rate annual carry remain limited assumptions.

| season / arm | probe | scale status | own reasons / inherited limitation | relative native / regional movement |
|---|---|---|---|---:|
| 20212022 / borrowing | verified | resolved | none / false | 2.911417e-08 / 1.651516e-07 |
| 20222023 / borrowing | verified | resolved | none / false | 3.698134e-09 / 1.648781e-08 |
| 20232024 / borrowing | verified | resolved | none / false | 1.279169e-08 / 4.930655e-08 |
| 20242025 / borrowing | verified | resolved | none / false | 9.22877e-09 / 5.047468e-08 |
| 20252026 / borrowing | verified | resolved | none / false | 1.236209e-08 / 5.158894e-08 |
| 20252026 / independent | verified | resolved | none / false | 2.25023e-08 / 7.769517e-08 |

unresolved scientific question: this joint prediction comparison does not identify a uniquely justified prior revision; frozen-source exposure consequences, omitted context and synthetic recovery remain unresolved.

this is joint lineup prediction of recorded spatial shape during the selected season, not separately validated offensive/defensive ability or a forecast available before the withheld games. all five research seasons were already exposed. prediction cannot repair prior synthetic recovery failures or isolate the prior as their cause. synthetic recovery, empirical player uncertainty, richer deployment/age adjustment, complete rates and supported chance valuation remain separate work. nomination: none; admission: not admitted; handoff: none.
