# primary anchor subgroup summaries

these are the existing native aggregate summaries for development (`dev`, 2024–25) and confirmation (`conf`, 2025–26). every native row in the six families is retained. the tables add no sampling intervals, diagnostic rules or acceptance gates.

`r` denotes `unblocked_conversion`: factual conversion at the recorded quantized origin on unblocked attempts, compared with the distance/angle benchmark. `all` denotes `all_attempt_outcome_blind`: the prior-weighted outcome-blind probability over all eligible attempts, compared with the score/role benchmark.

`log delta` and `brier delta` subtract the saved benchmark mean from the saved candidate mean; lower is better. `cal` is candidate predicted probability sum minus observed goals, divided by count. positive calibration means overprediction. values are rounded to eight significant digits; the source artifacts retain exact values.

`null` retains a missing shot-type category or an undefined mean in an empty group. `unknown` is the native role category. zero counts remain visible.

sources:

- development: [/Volumes/Expansion/hockey-stats/chance/03b-20260930/review/development-plot-verification/comparison.json](/Volumes/Expansion/hockey-stats/chance/03b-20260930/review/development-plot-verification/comparison.json); sha256 `c3f50f3631089a5eb8c811697b3d283ed993a50ae9260b43d646d1221904703c`.
- confirmation: [/Volumes/Expansion/hockey-stats/chance/03b-20260930/review/confirmation/comparison.json](/Volumes/Expansion/hockey-stats/chance/03b-20260930/review/confirmation/comparison.json); sha256 `bc1ac96b4b52e69be0cd0d18b1741a426fc71385925c7b0abeb8157631c07884`.

## season

| assessment | group | population | count | log delta | brier delta | cal |
|---|---|---|---:|---:|---:|---:|
| dev | `20242025` | r | 88628 | -0.00054436691 | -0.00017307171 | 0.00012049701 |
| dev | `20242025` | all | 124836 | 0.00036898821 | 4.1484029e-05 | 0.00041241249 |
| conf | `20252026` | r | 86800 | -0.0018337772 | -0.00042883934 | 0.00052780362 |
| conf | `20252026` | all | 120230 | 0.00021330158 | 1.4533049e-05 | -0.0019144445 |

## score

| assessment | group | population | count | log delta | brier delta | cal |
|---|---|---|---:|---:|---:|---:|
| dev | `trailing` | r | 30447 | -0.00050386921 | -0.00015494143 | -0.0018324785 |
| dev | `trailing` | all | 43823 | 0.00021057607 | 2.2120688e-05 | -0.00056386397 |
| dev | `tied` | r | 31570 | -0.00018583952 | -9.5547964e-05 | -0.0004398897 |
| dev | `tied` | all | 44321 | 0.00046799514 | 5.0040962e-05 | -0.00079785787 |
| dev | `leading` | r | 26611 | -0.0010160419 | -0.0002857859 | 0.0030198113 |
| dev | `leading` | all | 36692 | 0.00043859492 | 5.4274497e-05 | 0.0030403356 |
| conf | `trailing` | r | 29840 | -0.0012893849 | -0.00030132987 | -0.00076677353 |
| conf | `trailing` | all | 41807 | 0.00021925986 | 1.8241611e-05 | -0.0029693554 |
| conf | `tied` | r | 31244 | -0.0018596261 | -0.0004365246 | 0.0018555432 |
| conf | `tied` | all | 43398 | 0.00037491172 | 2.4912981e-05 | -0.00090579054 |
| conf | `leading` | r | 25716 | -0.0024340666 | -0.00056745984 | 0.00041683327 |
| conf | `leading` | all | 35025 | 5.9452845e-06 | -2.7549508e-06 | -0.0019050484 |

## role

| assessment | group | population | count | log delta | brier delta | cal |
|---|---|---|---:|---:|---:|---:|
| dev | `F` | r | 60946 | -0.0010311143 | -0.00023047334 | 0.00049354022 |
| dev | `F` | all | 79853 | 0.00057168942 | 6.3333483e-05 | 0.00010823457 |
| dev | `D` | r | 27674 | 0.0005209321 | -4.6855761e-05 | -0.00070745702 |
| dev | `D` | all | 44975 | 1.5436057e-05 | 3.1885597e-06 | 0.00094832865 |
| dev | `unknown` | r | 8 | 0.022483349 | 0.00051442595 | 0.022283962 |
| dev | `unknown` | all | 8 | -0.03529243 | -0.0027592277 | 0.023748665 |
| conf | `F` | r | 60527 | -0.0026593427 | -0.00057910252 | 0.0020123605 |
| conf | `F` | all | 78292 | 0.00022384907 | 1.9704463e-05 | -0.0015572808 |
| conf | `D` | r | 26267 | 6.4239271e-05 | -8.2753078e-05 | -0.0028968402 |
| conf | `D` | all | 41932 | 0.00019637373 | 5.0347748e-06 | -0.0025844134 |
| conf | `unknown` | r | 6 | 0.017133927 | 0.00029309637 | 0.017085704 |
| conf | `unknown` | all | 6 | -0.019114208 | -0.0010852648 | 0.019765299 |

## home_away

| assessment | group | population | count | log delta | brier delta | cal |
|---|---|---|---:|---:|---:|---:|
| dev | `home` | r | 44843 | -0.00087129746 | -0.00021802768 | -0.00064317465 |
| dev | `home` | all | 63185 | 0.00022268408 | 2.8335732e-05 | -0.00047748301 |
| dev | `away` | r | 43785 | -0.00020953656 | -0.00012702944 | 0.00090262166 |
| dev | `away` | all | 61651 | 0.00051893268 | 5.4959482e-05 | 0.0013244504 |
| conf | `home` | r | 44175 | -0.0020161712 | -0.00049000168 | 0.0012250207 |
| conf | `home` | all | 60996 | 0.00016887006 | 4.9198197e-06 | -0.0016400594 |
| conf | `away` | r | 42625 | -0.0016447507 | -0.00036545292 | -0.00019476682 |
| conf | `away` | all | 59234 | 0.00025905479 | 2.4432237e-05 | -0.0021969916 |

## shot_type

`shot_type` rows contain unblocked attempts only. the `all` values are outcome-conditioned descriptions, not calibration gates for the full all-attempt population. missing type remains missing.

| assessment | group | population | count | log delta | brier delta | cal |
|---|---|---|---:|---:|---:|---:|
| dev | `backhand` | r | 6504 | 0.0011275664 | 0.00020509151 | 0.016784623 |
| dev | `backhand` | all | 6504 | 0.00024612228 | 1.9319792e-05 | -0.024440493 |
| dev | `bat` | r | 306 | -0.0052746469 | -0.00092211088 | 0.015956853 |
| dev | `bat` | all | 306 | -0.0047981739 | -0.00051857251 | -0.048320406 |
| dev | `between-legs` | r | 49 | -0.0075668334 | -0.0024808101 | 0.12112417 |
| dev | `between-legs` | all | 49 | 0.00043082564 | 0.00012927848 | 0.052745514 |
| dev | `cradle` | r | 9 | 0.023067339 | 0.0052912932 | 0.090025008 |
| dev | `cradle` | all | 9 | 0.0018105376 | 0.00038207354 | 0.053812611 |
| dev | `deflected` | r | 1513 | -0.0024878163 | -0.0010657323 | 0.024076467 |
| dev | `deflected` | all | 1513 | 0.0012252076 | 9.3119645e-05 | -0.039098515 |
| dev | `poke` | r | 330 | 0.005284206 | 0.0016110703 | -0.015060776 |
| dev | `poke` | all | 330 | 0.0076220573 | 0.00069152265 | -0.091884483 |
| dev | `slap` | r | 9420 | -0.0004449269 | -0.00011527335 | -0.0085091491 |
| dev | `slap` | all | 9420 | -0.00014457913 | -1.4865804e-05 | -0.0045045806 |
| dev | `snap` | r | 18194 | -0.0017123153 | -0.00032804689 | -0.020208872 |
| dev | `snap` | all | 18194 | -0.00024001344 | -6.2412974e-05 | -0.030041018 |
| dev | `tip-in` | r | 7738 | -0.0024830072 | -0.00094916669 | 0.046045375 |
| dev | `tip-in` | all | 7738 | 0.0010373063 | 9.2800106e-05 | -0.014634599 |
| dev | `wrap-around` | r | 744 | 0.0049528202 | 0.00099414714 | 0.063076222 |
| dev | `wrap-around` | all | 744 | -0.00062555848 | -5.70113e-05 | 0.0097639718 |
| dev | `wrist` | r | 43806 | -5.6892424e-05 | -4.7411921e-05 | -0.0019223581 |
| dev | `wrist` | all | 43806 | 0.00052856829 | 4.0008531e-05 | -0.0081155584 |
| dev | `null` | r | 15 | 0.10557089 | 0.033352158 | -0.85027463 |
| dev | `null` | all | 15 | 0.03262659 | 0.0018536324 | -0.9461353 |
| conf | `backhand` | r | 6501 | -0.00069636964 | -0.00021438364 | 0.020240734 |
| conf | `backhand` | all | 6501 | -0.00024886721 | -7.0828934e-05 | -0.024927181 |
| conf | `bat` | r | 418 | -0.0049677197 | -0.0014508075 | 0.031807928 |
| conf | `bat` | all | 418 | 0.00028433808 | -4.9389458e-06 | -0.034057916 |
| conf | `between-legs` | r | 53 | 0.0049130689 | 0.001232924 | 0.039209432 |
| conf | `between-legs` | all | 53 | 0.010206253 | 0.00093861384 | -0.024189274 |
| conf | `cradle` | r | 7 | -0.033126334 | -0.0059095517 | -0.06578898 |
| conf | `cradle` | all | 7 | -0.0043200809 | -0.00041569613 | -0.093332647 |
| conf | `deflected` | r | 1395 | -0.0028111075 | -0.0010667051 | 0.0099861783 |
| conf | `deflected` | all | 1395 | 0.0031243646 | 0.00020427671 | -0.059956763 |
| conf | `poke` | r | 268 | -0.0029032104 | -0.0013947925 | 0.027473527 |
| conf | `poke` | all | 268 | 0.0054178677 | 0.0004733087 | -0.051043862 |
| conf | `slap` | r | 9250 | -0.00048948999 | -0.00014951373 | -0.010988928 |
| conf | `slap` | all | 9250 | 0.00010299859 | -2.4732383e-06 | -0.0073397335 |
| conf | `snap` | r | 21662 | -0.0025075184 | -0.00032649208 | -0.017089619 |
| conf | `snap` | all | 21662 | 8.2330354e-05 | -5.4472513e-05 | -0.027686791 |
| conf | `tip-in` | r | 8344 | -0.0048549937 | -0.0016452066 | 0.05698946 |
| conf | `tip-in` | all | 8344 | -5.4854486e-06 | -4.9660619e-06 | -0.0075383225 |
| conf | `wrap-around` | r | 659 | 0.0021864068 | 0.00015753292 | 0.058476866 |
| conf | `wrap-around` | all | 659 | -0.0023350148 | -0.00020777235 | 0.005335785 |
| conf | `wrist` | r | 38228 | -0.0013669956 | -0.00030357142 | -0.0039463902 |
| conf | `wrist` | all | 38228 | 0.00013839167 | -2.6235048e-05 | -0.012862634 |
| conf | `null` | r | 15 | 0.15167805 | 0.019930767 | -0.88862459 |
| conf | `null` | all | 15 | -0.012545026 | -0.0027334319 | -0.94481742 |

## actor_evidence

the native evidence partitions are `u`/`shooter` and `r`/`shooter`, `r`/`goalie`, each with `seen` and `unseen`. evidence is stage-specific; being seen in `u` does not establish being seen in `r`. no `u`/`goalie` partition exists.

| assessment | model stage | actor | basis | population | count | log delta | brier delta | cal |
|---|---|---|---|---|---:|---:|---:|---:|
| dev | `u` | `shooter` | `seen` | r | 85260 | -0.00054286212 | -0.00017311739 | -2.8975269e-05 |
| dev | `u` | `shooter` | `seen` | all | 120150 | 0.00036411654 | 4.164192e-05 | 0.0003108357 |
| dev | `u` | `shooter` | `unseen` | r | 3368 | -0.00058246001 | -0.00017191537 | 0.0039043468 |
| dev | `u` | `shooter` | `unseen` | all | 4686 | 0.00049389881 | 3.7435667e-05 | 0.0030168622 |
| dev | `r` | `shooter` | `seen` | r | 85158 | -0.00054102893 | -0.00017311768 | -4.1156115e-05 |
| dev | `r` | `shooter` | `seen` | all | 119980 | 0.0003658393 | 4.1718934e-05 | 0.00030429084 |
| dev | `r` | `shooter` | `unseen` | r | 3470 | -0.00062628479 | -0.00017194337 | 0.0040876602 |
| dev | `r` | `shooter` | `unseen` | all | 4856 | 0.00044679028 | 3.5680091e-05 | 0.0030838364 |
| dev | `r` | `goalie` | `seen` | r | 84044 | -0.00045023577 | -0.00015538388 | 0.00043046217 |
| dev | `r` | `goalie` | `seen` | all | 118425 | 0.00041851681 | 4.6819482e-05 | 0.00065423171 |
| dev | `r` | `goalie` | `unseen` | r | 4584 | -0.0022701865 | -0.00049736392 | -0.0055624682 |
| dev | `r` | `goalie` | `unseen` | all | 6411 | -0.00054591179 | -5.7073295e-05 | -0.0040545103 |
| conf | `u` | `shooter` | `seen` | r | 82295 | -0.0019034605 | -0.00043880157 | 0.00023406892 |
| conf | `u` | `shooter` | `seen` | all | 113937 | 0.00019659266 | 1.2677414e-05 | -0.0020421668 |
| conf | `u` | `shooter` | `unseen` | r | 4505 | -0.00056083977 | -0.00024685464 | 0.0058935966 |
| conf | `u` | `shooter` | `unseen` | all | 6293 | 0.00051582253 | 4.8129972e-05 | 0.00039801299 |
| conf | `r` | `shooter` | `seen` | r | 82130 | -0.0019210861 | -0.00044220966 | 0.00022656918 |
| conf | `r` | `shooter` | `seen` | all | 113703 | 0.00019376263 | 1.2524071e-05 | -0.00204915 |
| conf | `r` | `shooter` | `unseen` | r | 4670 | -0.00029829919 | -0.00019369929 | 0.0058255306 |
| conf | `r` | `shooter` | `unseen` | all | 6527 | 0.00055367813 | 4.9530262e-05 | 0.0004321811 |
| conf | `r` | `goalie` | `seen` | r | 84018 | -0.0018350954 | -0.00042936563 | 0.00038761476 |
| conf | `r` | `goalie` | `seen` | all | 116378 | 0.00024476546 | 1.7000612e-05 | -0.0019974284 |
| conf | `r` | `goalie` | `unseen` | r | 2782 | -0.0017939662 | -0.00041294509 | 0.004761588 |
| conf | `r` | `goalie` | `unseen` | all | 3852 | -0.0007372964 | -6.0017845e-05 | 0.00059269496 |
