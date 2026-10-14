# 03o decision

date: 2026-10-14. bounded execution: `complete`. direction: `decomposed_direction`. recommendation: `no_supported_representation`; nominated representation: null. scientific assessment: `not_admitted`.

decomposition reduced recorded-goal log loss in both windows. the reductions are tiny—about `0.0156%` and `0.0181%` of direct loss—and all six primary 95% intervals span zero. the frozen rule therefore nominates neither representation. lower brier and smaller pooled overprediction agree in sign with the point direction, without satisfying the primary nomination rule. this leaves the representation choice unresolved; it does not establish equivalence or refute factorization.

evidence: the [frozen protocol](protocol.md), byte-exact [result](result.json), [goal comparison](figures/comparison.png), [stage diagnostics](figures/stages.png) and [verification](verification.md). original result: `/Volumes/Expansion/hockey-stats/runs/chance-03o-20261013/report/result.json`, sha256 `77ebbcdf7b35101848d15415151a18bab3bdf40c36726d864e9ad616a2280848`, produced under clean `cdd46f9b1bd894298d4057969948973176dc0ea6`. the tables below use display rounding; the bound report retains full precision and complete bins/groups. independent final source/arithmetic reviews passed; verification records their evidence. the committed figures are legibility derivatives rendered from this unchanged bound report under presentation-only renderer revisions ending at `e0474fdd6dc5fec7bc2edcf2498878a7fbd1446d`; verification binds their refinement receipt and distinct image identities. original numerical/protocol/fit/report provenance remains `cdd46f9`.

## populations and meaning

`U` is source-eligible unblocked 5v5 attempts; `O` is recorded on-net; `G` is recorded goals. missed means `missed-shot`, saved means non-goal `shot-on-goal`, and every goal is recorded on-net. saved does not distinguish freezes, rebounds or in-play outcomes. `U=miss+saved+G`; `O=saved+G`. original source goals, exclusions, nullable coverage and zero-contribution games remain unchanged. there are no feature omissions or new filters.

| partition | games | U | O | miss | saved | G |
|---|---:|---:|---:|---:|---:|---:|
| development short training | 1,912 | 128,679 | 87,618 | 41,061 | 80,004 | 7,614 |
| development assessment | 712 | 49,014 | 31,658 | 17,356 | 28,854 | 2,804 |
| season-transfer short training | 2,624 | 177,693 | 119,276 | 58,417 | 108,858 | 10,418 |
| season-transfer assessment | 1,312 | 87,018 | 56,111 | 30,907 | 50,820 | 5,291 |

development trains on all 2023–24 plus 2024–25 before `2025-01-01`, then assesses the remainder of 2024–25. transfer trains on both complete seasons and assesses 2025–26. each assessment follows disjoint training dates. the windows are research-exposed and overlap in training; development assessment later enters transfer training. they are not independent confirmation.

q estimates `p(on_net|unblocked,x)` on U; g estimates `p(goal|on_net,x)` on O. the product estimates recorded goal probability on U. goal implies recorded on-net, so this identity requires no independence assumption. both models predict EVERY U row, including all `17,356/30,907` assessment misses; g's diagnostic label is null on those misses. recorded on-net status selects g's training/diagnostic target, never its predictors or the product. recorded location/type/context and current native actor/tip treatment remain; these are retrospective recorded-attempt probabilities.

## absolute recorded-goal scores

both representations score exactly the same full ordered U population and raw goal labels. positive residual means pooled overprediction; units are percentage points of U. predicted goals are sums of model probabilities, not observed counts.

| window / representation | U | observed goals | predicted goals | mean goal log loss, nats/U | brier/U | predicted − observed, pp |
|---|---:|---:|---:|---:|---:|---:|
| development direct | 49,014 | 2,804 | 2,906.251143 | 0.189367992550 | 0.049837999600 | +0.208616197 |
| development decomposed | 49,014 | 2,804 | 2,870.732294 | 0.189338469328 | 0.049803637955 | +0.136149455 |
| season transfer direct | 87,018 | 5,291 | 5,368.619895 | 0.199719186820 | 0.053234886324 | +0.089199815 |
| season transfer decomposed | 87,018 | 5,291 | 5,322.590065 | 0.199682959818 | 0.053215274218 | +0.036302908 |

primary differences are decomposed minus direct; negative favors decomposition. intervals use 2,000 paired pooled draws per method/window, preserving common sampled units and empty/final-partial calendar blocks. all methods are defined, with zero undefined research draws.

| window | goal-loss delta, nats/U | whole-game 95% interval | seven-day 95% interval | fourteen-day 95% interval |
|---|---:|---|---|---|
| development | −0.0000295232219553 | [−0.000165241223091, +0.000111006306946] | [−0.000170939175088, +0.000105997370481] | [−0.000199462630147, +0.000134198630347] |
| season transfer | −0.0000362270021778 | [−0.000125181884634, +0.0000555364261892] | [−0.000114546735276, +0.0000390069080652] | [−0.000117508236112, +0.0000493375329476] |

both points are below the fixed arithmetic deadband `−1e-10`, giving `decomposed_direction`. neither whole-game upper bound is below it. all primary intervals cross zero, so `supported_representation` is unavailable and the nomination stays null. relative loss changes are `−0.0155903971%/−0.0181389694%`: about `1.4471/3.1524` total nats across the two respective assessment populations.

| window | brier delta/U | whole-game 95% interval | seven-day 95% interval | fourteen-day 95% interval | absolute pooled residual change, pp |
|---|---:|---|---|---|---:|
| development | −0.0000343616450938 | [−0.0000641608946386, −0.00000432145889978] | [−0.0000659693092883, −0.00000567450479353] | [−0.0000688350821909, +0.00000320047070176] | −0.0724667423 |
| season transfer | −0.0000196121064335 | [−0.0000407929544483, +0.00000112468106148] | [−0.0000390337354810, −0.000000555356471579] | [−0.0000409214464768, +0.00000198490942761] | −0.0528969070 |

brier improves at both point estimates, but development's fourteen-day interval and transfer's game/fourteen-day intervals cross zero. pooled residual declines under every interval method: development whole-game/seven-/fourteen-day pp changes have intervals `[−0.079853,−0.065514]`, `[−0.079161,−0.065543]`, `[−0.077830,−0.067077]`; transfer has `[−0.058669,−0.047635]`, `[−0.057015,−0.049102]`, `[−0.057589,−0.048085]`. both arms remain positively biased in aggregate. these secondaries do not replace the declared primary rule.

twenty paired goal bins use DIRECT probabilities and common memberships; twenty own-arm bins remain separate. direct owns paired actor-support groups. the [comparison figure](figures/comparison.png) shows the primary intervals and direct-defined residual bins; the full report retains every count/group without subgroup nomination.

## stage diagnostics on their own targets

these are descriptive checks with U/O denominators. stage likelihoods use different labels/populations, so their numerical losses are not a ranking or competing direct goal scores. a near-zero pooled g residual or improved product residual does not establish either layer's calibration.

| window / stage | population | count | observed positives | predicted positives | mean log loss, nats/target row | brier/target row | residual, pp |
|---|---|---:|---:|---:|---:|---:|---:|
| development q: on-net | U | 49,014 | 31,658 | 32,559.530652 | 0.629481535459 | 0.219902406775 | +1.839332950 |
| development g: goal given on-net | O | 31,658 | 2,804 | 2,815.629887 | 0.255826561524 | 0.072696371045 | +0.036736013 |
| season transfer q: on-net | U | 87,018 | 56,111 | 57,062.776851 | 0.628223844628 | 0.219464356845 | +1.093770083 |
| season transfer g: goal given on-net | O | 56,111 | 5,291 | 5,257.750175 | 0.269949133870 | 0.077749626105 | −0.059257232 |

q overpredicts recorded net-hitting in both pooled populations. its large `0.75–0.80` bins also overpredict, while `0.90–0.95` bins underpredict. g's pooled balance conceals bin structure; its `0.35–0.40` bin overpredicts in both windows. illustrative own-bin facts follow; all twenty bins, including empty/null bins, remain in the [result](result.json). the [stage figure](figures/stages.png) plots populated bins.

| own target bin | development count / residual pp | season-transfer count / residual pp |
|---|---|---|
| q on U: `[0.75,0.80)` | 4,995 / +4.095805 | 7,270 / +3.371026 |
| q on U: `[0.90,0.95)` | 596 / −4.198362 | 1,110 / −4.802924 |
| g on O: `[0.35,0.40)` | 236 / +2.454930 | 473 / +7.321579 |

these points carry neither calibration intervals nor an admission gate. small conditional tails are especially sparse; the full counts accompany their residuals.

own-stage support counts below follow each stage's fitted actor population. `observed_in_state` means evidence in the applied annual state; `other_seasons_only` means evidence elsewhere and a penalty-inferred applied state; `unseen` means zero residual prior mode. transfer applies carried-forward 2024–25 states. none identifies rookies, physical goalie skill or player ability.

| window / stage / actor | target rows | observed in state | other seasons only | unseen |
|---|---:|---:|---:|---:|
| development q / shooter | 49,014 U | 47,165 | 1,006 | 843 |
| development q / goalie | 49,014 U | 48,249 | 510 | 255 |
| development g / shooter | 31,658 O | 30,424 | 700 | 534 |
| development g / goalie | 31,658 O | 31,158 | 334 | 166 |
| season transfer q / shooter | 87,018 U | 81,689 | 631 | 4,698 |
| season transfer q / goalie | 87,018 U | 82,635 | 1,582 | 2,801 |
| season transfer g / shooter | 56,111 O | 52,613 | 409 | 3,089 |
| season transfer g / goalie | 56,111 O | 53,234 | 1,032 | 1,845 |

q/direct source membership, complete annual domain, layouts and actor counts agree. g training uses only O, with annual shooter and goalie row counts `61,143/26,475` development and `61,143/58,133` transfer. q has `966/1,045` training shooters; g has `960/1,036`; each window has `112/121` goalies in both stages. q/g coefficient counts are `6,159/6,147` and `6,335/6,317`. every stage keeps its own counts and coefficient set; composed-own groups have no fictional combined actor support.

## numerical completion and limits

both immutable 03n direct controls were validated/reused without refitting or restamping. all four new fits converged with finite coefficients/objectives under the unchanged 2,000-iteration `L-BFGS-B` contract. each bound report verification receipt records exact saved/replayed objective agreement, difference `0.0`; no additional replay was run to write this decision.

| window / stage | iterations | saved = replayed penalized objective | maximum absolute gradient |
|---|---:|---:|---:|
| development q | 577 | 77017.17863739608 | 0.239330637883576 |
| development g | 423 | 21604.071295540547 | 0.11575537643072664 |
| season transfer q | 682 | 107494.55703062561 | 0.08977247741590477 |
| season transfer g | 476 | 29547.224905848165 | 0.022008583409063254 |

all terminate by `CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH`; none reaches the configured `gtol=1e-6` gradient threshold. native success permits this termination. objective replay verifies numerical/source reconciliation; it does not bound distance from the optimum. optimization error remains unquantified against these small primary differences. the `1e-10` deadband is an arithmetic convention, neither a solver-error bound nor a useful-effect guarantee. the prospective rule was preserved; no tighter solve, extra initialization or post-result fit followed.

this tests an estimator package. richer miss/saved/goal labels buy two maps/coefficient sets, while g has smaller O support. at the training base rates, q's Bernoulli information per U row is about `3.9×/4.0×` direct's; keeping the same absolute penalties makes q's relative shrinkage roughly fourfold weaker by this information comparison. that is a local information heuristic, not a uniform regularization factor for every parameter. the observed direction cannot isolate factorization from changed effective shrinkage, support or parameterization.

the 12,000 paired draws condition on two reused direct models and four stage fits, with zero bootstrap fits. they omit fitting, selection and source uncertainty. source coordinates, membership/type recording and coverage retain their existing limitations. recorded on-net is a scorer's classification; q's goalie/annual logits can absorb recording practices and circumstance differences. nuisance actor effects are not ability cards. these results establish no physical net-hitting accuracy, causal mechanism or published-model parity.

correct target/feature capability stays retained. the bounded study completes without a nominated or admitted model; representation adoption, further fitting, tip-shooter masking, mirror pooling, integration, final models, 04 and publication require separate assignment. later opportunity reference standardization must average the PRODUCT over the same joint actor reference; separately averaged layers cannot generally be multiplied.
