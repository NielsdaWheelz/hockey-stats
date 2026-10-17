# null, scale and transition diagnostics

null cells are shared once, under the paired family. they carry no nomination veto. all risks use squared attempts per 60 team minutes; no null ratios are formed.

| law | null risk or difference | mean | 95% interval |
|---|---|---:|---|
| gaussian | R_control | 0.00183871 | [0.00159902, 0.00209366] |
| gaussian | R_candidate | 0.000171862 | [0.00012771, 0.00022229] |
| gaussian | recovery_progress | 0.00166684 | [0.00143088, 0.00191845] |
| gaussian | P_zero | 1987.01 | [1981.05, 1992.98] |
| gaussian | P_control | 1989.84 | [1983.78, 1995.88] |
| gaussian | P_candidate | 1987.38 | [1981.4, 1993.4] |
| gaussian | prediction_progress | 2.46127 | [2.14844, 2.79801] |
| gaussian | own_prediction_gain | -0.375928 | [-0.485124, -0.279952] |
| game_pace | R_control | 0.0125438 | [0.0106796, 0.014593] |
| game_pace | R_candidate | 0.00135536 | [0.000840889, 0.00198415] |
| game_pace | recovery_progress | 0.0111885 | [0.00935848, 0.0131849] |
| game_pace | P_zero | 1963.75 | [1929.81, 1999.46] |
| game_pace | P_control | 1976.03 | [1941.7, 2012.01] |
| game_pace | P_candidate | 1966.09 | [1931.86, 2002.3] |
| game_pace | prediction_progress | 9.93483 | [8.62087, 11.3313] |
| game_pace | own_prediction_gain | -2.34569 | [-3.24386, -1.57519] |

inactive risks apply the full identifiable and reference-centering operator before selecting physically inactive rows. an inactive physical field can have nonzero relative truth. scale limitations are retained and reported without becoming a separate nomination veto.

| family | population | law | arm | inactive recovery | mean q | mean lambda | lower q / n | upper q / n | zero lambda / n | upper lambda / n | unresolved / n | inherited / n | negative complete cells / total |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| paired | sparse | gaussian | control | 0.0015628 | 5.57068e-06 | 0 | 150 / 200 | 0 / 200 | 200 / 200 | 0 / 200 | 200 / 200 | 199 / 200 | 408400896 / 1259520000 |
| paired | sparse | gaussian | candidate | 0.000171553 | 0.261398 | 3.85344e+07 | 56 / 200 | 22 / 200 | 42 / 200 | 77 / 200 | 194 / 200 | 186 / 200 | 408307666 / 1259520000 |
| paired | sparse | game_pace | control | 0.010837 | 2.56353e-05 | 0 | 133 / 200 | 0 / 200 | 200 / 200 | 0 / 200 | 198 / 200 | 194 / 200 | 471331501 / 1259520000 |
| paired | sparse | game_pace | candidate | 0.00127549 | 0.232199 | 4.05337e+07 | 58 / 200 | 19 / 200 | 33 / 200 | 81 / 200 | 195 / 200 | 187 / 200 | 466026370 / 1259520000 |
| paired | diffuse | gaussian | control | 0 | 7.26328e-06 | 0 | 136 / 200 | 0 / 200 | 200 / 200 | 0 / 200 | 200 / 200 | 199 / 200 | 408158243 / 1259520000 |
| paired | diffuse | gaussian | candidate | 0 | 0.253706 | 3.70502e+07 | 52 / 200 | 19 / 200 | 53 / 200 | 74 / 200 | 184 / 200 | 167 / 200 | 408147235 / 1259520000 |
| paired | diffuse | game_pace | control | 0 | 2.15241e-05 | 0 | 138 / 200 | 0 / 200 | 200 / 200 | 0 / 200 | 200 / 200 | 198 / 200 | 472104334 / 1259520000 |
| paired | diffuse | game_pace | candidate | 0 | 0.201925 | 4.10301e+07 | 65 / 200 | 18 / 200 | 47 / 200 | 82 / 200 | 196 / 200 | 182 / 200 | 467004798 / 1259520000 |
| paired | null | gaussian | control | 0.00183871 | 4.83832e-06 | 0 | 150 / 200 | 0 / 200 | 200 / 200 | 0 / 200 | 200 / 200 | 200 / 200 | 409341421 / 1259520000 |
| paired | null | gaussian | candidate | 0.000171862 | 0.312452 | 4.15545e+07 | 52 / 200 | 24 / 200 | 35 / 200 | 83 / 200 | 192 / 200 | 189 / 200 | 409239828 / 1259520000 |
| paired | null | game_pace | control | 0.0125438 | 2.07558e-05 | 0 | 138 / 200 | 0 / 200 | 200 / 200 | 0 / 200 | 198 / 200 | 197 / 200 | 472213258 / 1259520000 |
| paired | null | game_pace | candidate | 0.00135536 | 0.259122 | 4.7548e+07 | 58 / 200 | 24 / 200 | 34 / 200 | 95 / 200 | 194 / 200 | 191 / 200 | 467293141 / 1259520000 |
| independent | sparse | gaussian | control | 0.00375325 | 6.66116e-06 | 0 | 143 / 200 | 0 / 200 | 200 / 200 | 0 / 200 | 199 / 200 | 199 / 200 | 407738750 / 1259520000 |
| independent | sparse | gaussian | candidate | 0.00192832 | 0.168651 | 2.51192e+07 | 51 / 200 | 12 / 200 | 63 / 200 | 50 / 200 | 184 / 200 | 176 / 200 | 407592768 / 1259520000 |
| independent | sparse | game_pace | control | 0.0106083 | 2.17297e-05 | 0 | 140 / 200 | 0 / 200 | 200 / 200 | 0 / 200 | 200 / 200 | 198 / 200 | 471570357 / 1259520000 |
| independent | sparse | game_pace | candidate | 0.00269761 | 0.1553 | 3.65594e+07 | 60 / 200 | 14 / 200 | 56 / 200 | 73 / 200 | 189 / 200 | 181 / 200 | 467238136 / 1259520000 |
| independent | diffuse | gaussian | control | 0 | 1.02781e-05 | 0 | 126 / 200 | 0 / 200 | 200 / 200 | 0 / 200 | 199 / 200 | 197 / 200 | 407263397 / 1259520000 |
| independent | diffuse | gaussian | candidate | 0 | 0.0749366 | 3.05735e+06 | 33 / 200 | 1 / 200 | 75 / 200 | 6 / 200 | 137 / 200 | 124 / 200 | 407034549 / 1259520000 |
| independent | diffuse | game_pace | control | 0 | 3.25133e-05 | 0 | 120 / 200 | 0 / 200 | 200 / 200 | 0 / 200 | 199 / 200 | 199 / 200 | 472664524 / 1259520000 |
| independent | diffuse | game_pace | candidate | 0 | 0.0624989 | 1.20463e+07 | 43 / 200 | 2 / 200 | 87 / 200 | 24 / 200 | 166 / 200 | 153 / 200 | 469777168 / 1259520000 |

| family | population | law | arm | player | role | final-year transition recovery contribution |
|---|---|---|---|---:|---|---:|
| paired | sparse | gaussian | control | 32 | offense | 0.000828024 |
| paired | sparse | gaussian | control | 32 | defense | 0.0010375 |
| paired | sparse | gaussian | control | 33 | offense | 0.000874292 |
| paired | sparse | gaussian | control | 33 | defense | 0.00083966 |
| paired | sparse | gaussian | control | 8 | offense | 0.000902424 |
| paired | sparse | gaussian | control | 8 | defense | 0.000850093 |
| paired | sparse | gaussian | candidate | 32 | offense | 0.000839765 |
| paired | sparse | gaussian | candidate | 32 | defense | 0.00104759 |
| paired | sparse | gaussian | candidate | 33 | offense | 0.000885556 |
| paired | sparse | gaussian | candidate | 33 | defense | 0.000833602 |
| paired | sparse | gaussian | candidate | 8 | offense | 0.000888442 |
| paired | sparse | gaussian | candidate | 8 | defense | 0.000836807 |
| paired | sparse | game_pace | control | 32 | offense | 0.000902714 |
| paired | sparse | game_pace | control | 32 | defense | 0.00105471 |
| paired | sparse | game_pace | control | 33 | offense | 0.000939403 |
| paired | sparse | game_pace | control | 33 | defense | 0.000903781 |
| paired | sparse | game_pace | control | 8 | offense | 0.00102941 |
| paired | sparse | game_pace | control | 8 | defense | 0.00103408 |
| paired | sparse | game_pace | candidate | 32 | offense | 0.000847733 |
| paired | sparse | game_pace | candidate | 32 | defense | 0.00106052 |
| paired | sparse | game_pace | candidate | 33 | offense | 0.000897677 |
| paired | sparse | game_pace | candidate | 33 | defense | 0.000867446 |
| paired | sparse | game_pace | candidate | 8 | offense | 0.000891421 |
| paired | sparse | game_pace | candidate | 8 | defense | 0.000858052 |
| paired | diffuse | gaussian | control | 32 | offense | 0.00358331 |
| paired | diffuse | gaussian | control | 32 | defense | 0.00375347 |
| paired | diffuse | gaussian | control | 33 | offense | 0.00336659 |
| paired | diffuse | gaussian | control | 33 | defense | 0.00354262 |
| paired | diffuse | gaussian | control | 8 | offense | 0.00337821 |
| paired | diffuse | gaussian | control | 8 | defense | 0.00359836 |
| paired | diffuse | gaussian | candidate | 32 | offense | 0.00366456 |
| paired | diffuse | gaussian | candidate | 32 | defense | 0.00381218 |
| paired | diffuse | gaussian | candidate | 33 | offense | 0.00342779 |
| paired | diffuse | gaussian | candidate | 33 | defense | 0.00359049 |
| paired | diffuse | gaussian | candidate | 8 | offense | 0.0033981 |
| paired | diffuse | gaussian | candidate | 8 | defense | 0.00360188 |
| paired | diffuse | game_pace | control | 32 | offense | 0.00356366 |
| paired | diffuse | game_pace | control | 32 | defense | 0.00368834 |
| paired | diffuse | game_pace | control | 33 | offense | 0.00330527 |
| paired | diffuse | game_pace | control | 33 | defense | 0.00349092 |
| paired | diffuse | game_pace | control | 8 | offense | 0.00342249 |
| paired | diffuse | game_pace | control | 8 | defense | 0.00355527 |
| paired | diffuse | game_pace | candidate | 32 | offense | 0.00367143 |
| paired | diffuse | game_pace | candidate | 32 | defense | 0.00381404 |
| paired | diffuse | game_pace | candidate | 33 | offense | 0.00340973 |
| paired | diffuse | game_pace | candidate | 33 | defense | 0.00357604 |
| paired | diffuse | game_pace | candidate | 8 | offense | 0.00340266 |
| paired | diffuse | game_pace | candidate | 8 | defense | 0.00358378 |
| paired | null | gaussian | control | 32 | offense | 9.01087e-06 |
| paired | null | gaussian | control | 32 | defense | 1.12483e-05 |
| paired | null | gaussian | control | 33 | offense | 1.27945e-05 |
| paired | null | gaussian | control | 33 | defense | 1.19693e-05 |
| paired | null | gaussian | control | 8 | offense | 2.44141e-05 |
| paired | null | gaussian | control | 8 | defense | 2.89238e-05 |
| paired | null | gaussian | candidate | 32 | offense | 2.27663e-06 |
| paired | null | gaussian | candidate | 32 | defense | 2.62348e-06 |
| paired | null | gaussian | candidate | 33 | offense | 2.70314e-06 |
| paired | null | gaussian | candidate | 33 | defense | 2.60247e-06 |
| paired | null | gaussian | candidate | 8 | offense | 2.52921e-06 |
| paired | null | gaussian | candidate | 8 | defense | 2.87171e-06 |
| paired | null | game_pace | control | 32 | offense | 8.66122e-05 |
| paired | null | game_pace | control | 32 | defense | 8.58306e-05 |
| paired | null | game_pace | control | 33 | offense | 8.59814e-05 |
| paired | null | game_pace | control | 33 | defense | 8.47856e-05 |
| paired | null | game_pace | control | 8 | offense | 0.000206831 |
| paired | null | game_pace | control | 8 | defense | 0.000190561 |
| paired | null | game_pace | candidate | 32 | offense | 1.99198e-05 |
| paired | null | game_pace | candidate | 32 | defense | 2.32327e-05 |
| paired | null | game_pace | candidate | 33 | offense | 2.10162e-05 |
| paired | null | game_pace | candidate | 33 | defense | 1.88026e-05 |
| paired | null | game_pace | candidate | 8 | offense | 1.92461e-05 |
| paired | null | game_pace | candidate | 8 | defense | 1.77801e-05 |
| independent | sparse | gaussian | control | 32 | offense | 0.000714898 |
| independent | sparse | gaussian | control | 32 | defense | 0.000639856 |
| independent | sparse | gaussian | control | 33 | offense | 0.000772226 |
| independent | sparse | gaussian | control | 33 | defense | 0.000912495 |
| independent | sparse | gaussian | control | 8 | offense | 0.000772221 |
| independent | sparse | gaussian | control | 8 | defense | 0.000620508 |
| independent | sparse | gaussian | candidate | 32 | offense | 0.000730769 |
| independent | sparse | gaussian | candidate | 32 | defense | 0.000645806 |
| independent | sparse | gaussian | candidate | 33 | offense | 0.000783999 |
| independent | sparse | gaussian | candidate | 33 | defense | 0.000952007 |
| independent | sparse | gaussian | candidate | 8 | offense | 0.000788202 |
| independent | sparse | gaussian | candidate | 8 | defense | 0.000612565 |
| independent | sparse | game_pace | control | 32 | offense | 0.00074898 |
| independent | sparse | game_pace | control | 32 | defense | 0.000640367 |
| independent | sparse | game_pace | control | 33 | offense | 0.000791249 |
| independent | sparse | game_pace | control | 33 | defense | 0.00095346 |
| independent | sparse | game_pace | control | 8 | offense | 0.000855481 |
| independent | sparse | game_pace | control | 8 | defense | 0.000742339 |
| independent | sparse | game_pace | candidate | 32 | offense | 0.000749995 |
| independent | sparse | game_pace | candidate | 32 | defense | 0.000648582 |
| independent | sparse | game_pace | candidate | 33 | offense | 0.000811069 |
| independent | sparse | game_pace | candidate | 33 | defense | 0.000959699 |
| independent | sparse | game_pace | candidate | 8 | offense | 0.000785657 |
| independent | sparse | game_pace | candidate | 8 | defense | 0.000633756 |
| independent | diffuse | gaussian | control | 32 | offense | 0.00268077 |
| independent | diffuse | gaussian | control | 32 | defense | 0.00260725 |
| independent | diffuse | gaussian | control | 33 | offense | 0.00289782 |
| independent | diffuse | gaussian | control | 33 | defense | 0.00259846 |
| independent | diffuse | gaussian | control | 8 | offense | 0.00260427 |
| independent | diffuse | gaussian | control | 8 | defense | 0.00235113 |
| independent | diffuse | gaussian | candidate | 32 | offense | 0.00276217 |
| independent | diffuse | gaussian | candidate | 32 | defense | 0.00268032 |
| independent | diffuse | gaussian | candidate | 33 | offense | 0.00299774 |
| independent | diffuse | gaussian | candidate | 33 | defense | 0.00267092 |
| independent | diffuse | gaussian | candidate | 8 | offense | 0.00266608 |
| independent | diffuse | gaussian | candidate | 8 | defense | 0.00248416 |
| independent | diffuse | game_pace | control | 32 | offense | 0.00266214 |
| independent | diffuse | game_pace | control | 32 | defense | 0.00265267 |
| independent | diffuse | game_pace | control | 33 | offense | 0.00290225 |
| independent | diffuse | game_pace | control | 33 | defense | 0.00257943 |
| independent | diffuse | game_pace | control | 8 | offense | 0.00265159 |
| independent | diffuse | game_pace | control | 8 | defense | 0.00250458 |
| independent | diffuse | game_pace | candidate | 32 | offense | 0.00279624 |
| independent | diffuse | game_pace | candidate | 32 | defense | 0.00271919 |
| independent | diffuse | game_pace | candidate | 33 | offense | 0.00300334 |
| independent | diffuse | game_pace | candidate | 33 | defense | 0.00265911 |
| independent | diffuse | game_pace | candidate | 8 | offense | 0.00263631 |
| independent | diffuse | game_pace | candidate | 8 | defense | 0.00250762 |

native complete-rate error retains signed volume–shape cross terms. actual versus spatially projected truth, roles, activation, every year, the thirty-pair score, identifiable pair averages and unsupported differences remain in assessment.json. no map examples were selected.

new fitted histories: 2800; fresh shape selections: 12000; fresh volume selections: 4000. measured fitting wall time: 4553.41 seconds; maximum recorded process memory: 1406124032 bytes; fit output before fit-manifest serialization: 7127497957 bytes. numerical probe work is recorded separately and does not add histories.

numerical status: `verified`. all twenty probes retain original incoming histories; ten final-year substitutions reuse bootstrap indices. classification stability: `true`. this does not test global optimality or propagation of earlier probe changes.
