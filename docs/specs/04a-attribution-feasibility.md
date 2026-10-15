# pr04a — attribution feasibility and player-consequence sensitivity

status: **completed; research only, not admitted.** [decision](../research/attribution-04a/decision.md), [result](../research/attribution-04a/result.json) and [verification](../research/attribution-04a/verification.md) retain the corrected execution and reviews. the assigned specification survives unchanged in the frozen external snapshot. [plan](../plan.md) owns progression. [04](04-player-attribution.md) retains supported chance-valued player outputs; no admission, publication or player-card handoff follows here.

## question and boundary

can the admitted evidence distinguish useful player differences in recorded 5v5 rates, and how much do those conclusions depend on deployment, observation coverage and provisional valuation?

deliver two chronological annual model chains over **2021–22 through 2025–26**: recorded all-attempt scalar rates and recorded unblocked spatial rates. the latter's scalar is the sum of its map. include age-neutral borrowing, correlated player uncertainty, known-truth recovery and bounded location/valuation sensitivity. the headline target is underlying level across 2025–26, not season-end form. borrowing alone does not establish ability.

settled choices: a **5% difference in the relevant league-average team rate** is meaningful, separately for offense and defense; missing locations exclude affected spatial counts AND exposure, while usable scalar evidence remains; value only final-season maps with the saved **03n direct and 03o q × g transfer models** under one common reference. 03p's nomination does not replace these controls. historical attribution never consumes chance weights.

[magnus 9](https://hockeyviz.com/txt/magnus9EV) motivates spatial stint responses, teammate/opponent terms and annual borrowing. this benchmark omits its aging and richer deployment model. no copied prior constants, private-model parity or causal-isolation claim.

non-goals: new sources, blocked-origin inference, chance fitting/adoption, type/context-specific player maps, age curves, coach estimation, forecasting, rankings/cards, effect/frontend work or a generic attribution framework. retain inactive features. age, rest, shift-start zone/time, post-penalty and coaching adjustments remain [04 follow-ups](04-player-attribution.md#decisions-for-the-full-specification).

## inputs and matched populations

bind 03m's five corrected schema-2 manifests and schema-4 game envelopes, using the selection/audit identities in [03n's protocol](../research/chance-03n/protocol.md). the inventory contains 6,560 regular-season games, 1,312 per season; this does NOT establish complete exposure. no acquisition, source replacement or reinterpretation campaign. preserve current raw data, fits and frozen paths.

read native interpreted/reconstructed games, not `chance_data.prepare_core()`'s chance-eligible cohort. retain native membership/participant corroboration, including its shooter-consistency requirements; apply no additional chance-specific actor, bio, type or preceding-action filter to recorded counts. stable roster skater ids are required; trades retain one annual identity. include supported genuine 5v5, including overtime, with five distinct skaters and one goalie per side. exclude shootouts/penalty shots and known other-strength play. missing overtime need not remove supported regulation.

one population builder owns these rules:

1. reuse corroborated score chronology. its all-or-unavailable game contract remains: a chronology/score failure excludes that game from both chains, with located reasons. no forward filling or partial-score repair.
2. split native elapsed intervals at verified timed goals; retain every positive zero-event segment. goals use pre-goal score; subsequent time uses updated score. coalesce adjacent segments only when period, all memberships and the complete selected context design agree.
3. assign events through reported membership, native `interval_indices`/`shift_relation`, clock and the projected pre-score context stratum. count once. `before|after|both` are evidence, not a universal boundary rule. preserve raw score changes even when equal clipped strata coalesce. do not invent duration for an intermediate same-clock score stratum or borrow an incompatible lineup.
4. `all_attempts` counts exactly `goal|shot-on-goal|missed-shot|blocked-shot`; `unblocked_spatial` counts the first three. `failed-shot-attempt` is not an extra attempt class. unresolved shooting-team ownership is unavailable, not inferred.
5. potentially in-scope events without a unique compatible positive segment quarantine every locally plausible adjacent segment. known period/unknown clock quarantines the period; unknown timed period quarantines the game. known out-of-scope events do not quarantine valid 5v5. distinguish unavailable membership from known other-strength membership.
6. spatial admission additionally requires finite, normalized, in-rink unblocked coordinates. missing/unresolved/out-of-rink coordinates quarantine affected spatial segments. use native orientation, grid and `cell_id`; no clipping, block contacts or inferred origins.
7. apply each population's union of masks to **both team directions**, removing all affected counts/time, including otherwise valid events. spatial masks include scalar masks. emit two attacking-side rows per remaining segment, including zeros.

retain event dispositions, segment masks and collateral losses. full-game `player_exposure.complete=false` does not erase independently supported segments. two attacking rows imply twice the game exposure; each row has five offensive and five defensive indicators. reconcile these identities exactly.

the spatial estimand is recorded unblocked rates on **coordinate-complete admitted exposure**, not full-season unblocked rates. selection may favor particular players, venues or play. report retained/excluded seconds and counts by season, game, team and player, including score failures and unresolved membership. show common-population coverage, without forcing the two scalar estimates to match. no coverage threshold or missing-at-random claim.

## estimator and annual state

fit the two populations separately. spatial responses retain the native 656-cell, five-foot grid: no mirroring, pooling or smoothing. signed effects can be negative. report negative fitted complete rates/cell rates and their exposure-weighted frequency; never clip them into a valid intensity model.

for each annual population, `e_i=seconds_i/3600`, `N_ij` is count, and `r=total_attempts/sum(e_i)` is its league **team** rate per 60. relative responses are `Y_ij=N_ij/(e_i*r)`, weighted by `w_i=e_i*r`. scalar has one column; spatial has 656, with matched scalar `Y·1`. chance weights enter neither rates nor priors.

`X` has offense/defense columns for every skater seen in this population through the current year: five attacking and five defending indicators per row. positive defense means more opponent attempts internally. `Z` has flat context-stratum means for observed attacking home/away × period `1|2|3|overtime` × attacking pre-score difference clipped to `-3..3`. no unobserved strata, context ridge, within-period time curve or automatic feature activation. missing context is not a zero indicator.

use `Y=XB+ZA+error`, independent working row covariance `S/w_i`, and player prior `B ~ matrix_normal(M0,V0,S)`. the [matrix-normal representation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.matrix_normal.html) gives `cov(vec B)=S ⊗ V`: full cross-player/offense-defense covariance without a covariance over every player-cell pair.

scalar `S=1`. spatial `S` is diagonal with `S_jj=(first_season_cell_count_j+0.5)/(first_season_U+0.5*k)`, where `k=656` for real data and four for the synthetic exercise. it sums to one; freeze it after the first season. no future cell counts, per-cell scale search or extra dispersion fit. the half-count prevents false zero variance. residual dispersion one approximates independent poisson bins around the pooled reference; it is a working assumption. intervals condition on estimated references, covariance shape and scales.

- first season: zero means, covariance `a*I`; estimate one common variance `a` using that season only. first-observed does not mean nhl rookie; no copied below-average entry prior.
- subsequent years: carry the COMPLETE preceding centered player mean/covariance, including absent players. add `q_s*I` to the old-player block; append entrants with zero mean, independent variance `a` and zero cross-covariance. estimate one current-year `q_s` from current data and the frozen preceding state. no age-dependent mean/variance. absent years accumulate innovation; never revise earlier saved fits.
- after fitting, let `u` be current admitted player exposure divided by total player exposure. subtract `u'B_off` and `u'B_def` from every corresponding row, including absent players. transform the FULL covariance identically. add five times the two removed means to every context-stratum mean, preserving predictions. save this centered, possibly singular state; never invert it. next year's positive innovation makes its prior proper. no-current-exposure players are `carried_only`.
- borrowing preserves league-relative level, not identical attempts/60 across changing leagues. multiply by current `r` for physical units. the two populations have separate histories, references and entrants.

### scale selection and numerical solve

estimate `a` and each `q_s` using the population-matched **scalar restricted gaussian marginal likelihood**, including for spatial fits. this selects total-rate shrinkage, not spatial-shape shrinkage. no 5%-derived prior, borrowed peer constant or tuning against the final player table.

weighted-residualize `X,Y` within context strata. let `H=Xr'Xr`, `T=Xr'Yr`, `V0=L L'`, and `z=yr-Xr*m0` for the matched scalar. evaluate:

```text
K = I + L' H L
b = Xr' z
objective = logdet(K) + z'z - b' L K^-1 L' b
V = L K^-1 L'
M = M0 + V (T - H M0)
```

context means are stratum-weighted means of `Y-XM`. do not report context uncertainty unless the joint context/player covariance is recovered. use sufficient statistics and cholesky solves, not explicit inverses, dense observation covariance or a kronecker allocation. the same `V` acts on every response column; scalar/region/valuation projections must agree.

variance bounds are `[10^-8,1]` in relative-rate-squared units. evaluate 17 base-10 exponents `-8,-7.5,…,0`; refine the best interior grid point's neighboring bracket once with bounded scalar minimization (`xatol=1e-4,maxiter=40`, exponent units). retain the lowest valid evaluated objective, endpoints included; ties favor smaller variance. record the curve, competing coarse minima and termination. endpoint winners or failed/nonfinite refinement mean `scale_unresolved`; carry the best finite state into later years with that inherited limitation. no widened bounds or extra campaign. if no valid numerical state exists, stop the dependent chain and diagnose the failure; do not substitute zero/previous coefficients. the floor is an explicit minimum-change assumption, not hidden jitter. this is bounded optimization, not a global-optimum certificate.

real-data budget: **ten annual fits**, two chains × five years, each with this scale search. no full-history bootstrap, alternate-prior campaign or chance fitting. gaussian intervals include conditional coefficient uncertainty and historical covariance; they omit uncertainty in scales, selection, dependence and misspecification.

## contrasts and meaningful resolution

for centered player contrast `c` and response functional `v`, report mean `r*c'Mv` and variance `r²*(c'Vc)*(v'Sv)`. matched scalars use `v=1`; regional totals reuse `chance_evaluation.REGION_NAMES`. no independent-player/cell shortcut. suppression negates defense and reverses interval endpoints once at the content boundary.

use pointwise 95% gaussian working-posterior intervals. show every currently observed player's league-relative effect, plus two outcome-blind final-season pairs: greatest shared admitted scalar exposure; and greatest combined scalar exposure among pairs with zero shared exposure. ties use sorted player ids. freeze pairs before fitting; use them across populations, with unavailable retained. no all-pairs ranking or simultaneous-inference claim.

relative contrast labels: `meaningful_positive` when lower endpoint exceeds `.05`; `meaningful_negative` when upper endpoint is below `-.05`; `within_meaningful_band` when the interval lies inside `[-.05,.05]`; otherwise `unresolved`. show attempts/60 too. summarize widths/statuses by exposure without an outcome-selected minutes cutoff. these are meaningful-difference labels, not error budgets or guaranteed precision. no per-cell 5% rule or transferred goal-value threshold.

### synthetic recovery

three cases × 200 replicates × five seasons, with both scalar/spatial chains. freeze schedule/design using `PCG64(40400)`; response streams use `PCG64(40401+case_index)`, zero-based case ids, fixed replicate/year/game/stint/team/cell draw order. rerun scale selection within EVERY replicate/year; fixed design cross-products may be reused.

use four teams, eight active skaters each, 96 balanced round-robin games/year, 50 stints/game, durations cycling 15/30/45 seconds; two attacking rows. use tied score and cycling regulation periods, balanced home assignments. spatial cells are explicitly synthetic, shares `[.1,.2,.3,.4]`, not fake nhl captures. year three replaces player 0 with entrant 32 and temporarily replaces player 8 with entrant 33; year four player 8 returns in place of player 9. retain all previously seen states.

per-team scalar offense truths are `[-.10,-.05,0,0,0,0,.05,.10]`, defense `[.05,0,-.05,0,.10,0,-.10,0]`. spatial effects initially equal each scalar times the four shares; offensive players at team offsets 3/4 receive opposite zero-sum additions `(+.025,-.025,0,0)`. player 1 gains `.025` offense from year four onward; entrants 32/33 have offense `.05/0`, defense zero. blocked scalar effects use the same scalar truths. use baseline unblocked/blocked rates `40/15` per 60; transform truth to each fitted annual reference/centering before comparison.

| case | fixed mechanism |
|---|---|
| mixed | independently select five of eight skaters. unblocked generating rate in cell `j` is `mu_j=40*(share_j+sum(attacking_off_j)+sum(defending_def_j))`; blocked rate is `mu_b=15*(1+sum(attacking_off)+sum(defending_def))`. draw count-unit gaussian responses with means `e*mu_j,e*mu_b`, variances `e*40*share_j,e*15`; sum unblocked plus blocked for all-attempt response |
| paired | same, but players 26/31 always play together or neither: include both with probability `5/8`, choosing three of the other six; otherwise choose five of those six. their offensive truths are `0/.10`; assess supported sum versus unidentified difference |
| count stress | mixed lineups; poisson unblocked-cell/blocked counts with one `gamma(shape=2,scale=.5)` pace multiplier per game, shared across both teams/all stints |

construct/check positive generating means before execution; no clipping or redrawing failed replicates. gaussian synthetic responses may be signed/noninteger and bypass source-count schemas as labeled matrices. the full native grid and source contracts receive separate fixture checks.

report bias, rmse, interval width, pointwise coverage with wilson binomial intervals, false directional/meaningful claims and paired sum/difference recovery by year/entrant/returner. use team-one offense pairs `(2,3),(6,2),(7,2)` and defense pairs `(1,3),(0,1),(4,1)`, replacing unavailable retired-player contrasts with null, not another pair. their initial scalar differences are `0,.05,.10`; include the `(3,4)` zero-sum spatial contrast and paired `(26,31)` sum/difference. coverage's independent unit is the replicate, not correlated players/years. plug-in posterior intervals need not attain frequentist 95% coverage. poor recovery, undercoverage, bound contact or negative fits are scientific results; algebra/accounting failures are software defects. no simulator tuning until a desirable result appears.

### bounded consequence scenarios

location-only responses cannot recover type/context/venue-specific error effects. use these declared **unit stresses**, not inferred truth-error bounds:

- move every cell's mass a nominal five feet toward `(89,0)` and, separately, away; select the nearest VALID native center to the nominal target, including outside-rink targets, with first-argmin native order. no move at zero distance. this transforms model mass, never raw coordinates; do not pass outside targets to the factual `cell_id()` admission path. record actual displacement. each transport conserves mass and the matched scalar.
- perturb each reference valuation surface by `sigmoid(logit(v_j) ± .10)`. this is a log-odds response test, not calibration correction or a known error interval.
- compare direct/decomposed valuations on unchanged maps. no crossed scenario campaign, fitted correction or winner selection.

write transport as `A[dest,source]`, each column summing to one: `M*=M A'`, `S*=A S A'`, `V*=V`. retain the transformed covariance exactly, including singularity; no new half-count smoothing, diagonal approximation or inverse. transform prior response means/covariance and league count-density map identically; keep the chance valuation surface FIXED. otherwise moving both locations and their valuation can erase the sensitivity. fixed column operations commute with the shared estimator; verify on a small independent refit. probability stresses change only post-fit valuation. report magnitudes/signs/pair/map movements; conditional intervals remain separate from scenario envelopes. source-stratum/type-specific propagation and independently justified error magnitudes remain later work. [player-consequence budgets](../issues/player-consequence-budgets.md) stays open.

## final-season provisional valuation

bind transfer components through [03n's result](../research/chance-03n/result.json) and [03o's result](../research/chance-03o/result.json). beneath `/Volumes/Expansion/hockey-stats/runs/`:

| component directory | required completion sha256 |
|---|---|
| `chance-03n-20261013/fits/season_transfer/short/` | `87a0f4744dcf1756916464eafe55d2c7a1bfc15e49b46d4968800f7b0a9fbf8d` |
| `chance-03o-20261013/fits/season_transfer/unblocked_on_net/` | `3b61b35128fb375f5aedb2853f95ea23558848f08f70fd20e8ef281279e627e7` |
| `chance-03o-20261013/fits/season_transfer/on_net_conversion/` | `f15b55183ab6474e15bdcfd7a5478fc25b8b5c1febe3c292d52bcefc2a27d926` |

validate native fit/config/cohort/design bindings with `chance_components.read_component_fit`. no migration, refit, fallback or 03p substitution.

the common empirical joint reference is 2025–26 unblocked events admitted to the spatial population AND eligible under the existing native core projection, with actors present in all three models. reuse `prepare_game_attempts` for type/recent-context/physical-attempt meaning; do not reimplement those derivations. include misses: g's on-net training target does not restrict reference prediction applicability. weight retained events equally; preserve source keys/exclusions, then collapse identical predictor tuples by frequency. do not refilter attribution fits. use native transfer annual-state carry-forward unchanged. freeze joint rows/weights once; never independently average actors, type or context.

score each cell `j` and joint reference tuple `z` through native encoding/logits:

```text
v_direct[j] = sum(weight[z] * p_direct(j,z))
v_product[j] = sum(weight[z] * q(j,z) * g(j,z))
```

these are standardized predictions, not fabricated observations. native computational support does NOT imply empirical support for every crossed cell/reference combination. report observed cell/type support and reference mass on unseen cell/type combinations. common-reference projection accepts extrapolation; it establishes no physical accuracy. empty reference or incompatible inputs makes valuation unavailable, not a switch to other weights.

apply both vectors to the SAME final-season maps/covariance. report league-relative provisional goal-rate effects in goals/60, each valuation's league baseline separately, and paired difference using `v_direct-v_product`. these are effects, not absolute player/team scoring rates. intervals include attribution uncertainty only; chance fits/reference weights stay fixed. this values location, omitting player-specific type/context-mix credit. disagreement is not error against truth; agreement can share bias. no admission or goal-value tolerance.

## owners and capability contracts

`fixed sources → separate matched populations → annual count-rate chains → recovery/projection/valuation → research decision`.

| owner | responsibility / interface |
|---|---|
| `analysis/src/hockey_stats/corpus_inputs.py` | extract existing corpus/envelope readers from `chance_data.py`; one validator/source-binding owner, unchanged native behavior |
| `analysis/src/hockey_stats/game_chronology.py` | extract `_scores` and period helpers into the shared chronology contract consumed by chance preparation and attribution; no recovery redesign |
| `analysis/src/hockey_stats/attribution_data.py` | `prepare_attribution(selection,protocol,out)` streams games/ledgers and sparse counts/sufficient statistics; returns a prepared artifact reference with masks, design and coverage bindings, not dense five-season response matrices; no fitting/acquisition |
| `analysis/src/hockey_stats/attribution.py` | `fit_year(population,previous_state)` returns annual state/diagnostics; `contrast(state,player_contrast,response_weights)` returns mean/variance. one solve, scale-selection, transition and covariance implementation |
| `chance.py`, `chance_components.py` | narrow reference-scoring API sharing predictor-only encoding and native logits; reference rows require no invented outcome or source eligibility |
| `analysis/src/hockey_stats/attribution_valuation.py` | common reference, fixed surfaces, linear transports/projections; no study decisions |
| `analysis/research/attribution_feasibility.py` | manual commands, fixed simulator/scenarios, report and recommendations; no imports through historical controllers |
| `docs/research/attribution-04a/` | frozen protocol, results, decision/figures and verification; statistician owns estimands, source reviewer masks, systems reviewer computation/identity, content designer labels/examples/claims |

reuse `artifacts.py`, source exceptions, finite json, hashes, exclusive outputs and completion conventions. arrays use `.npz` without pickle; large keyed ledgers use streamed jsonl. no new storage dependency, database, feature store, registry or plugin framework. explicit typed inputs, no implicit global state. remove duplicate implementations only at the extracted boundary; preserve historical evidence and supported inactive features.

manifest documents use `schema_version:1`, exact `kind`, implementation identity, consumed `{path,sha256}` references and units. derived manifests bind the protocol digest; `protocol.json` does not hash itself. manifests bind compact jsonl row contracts and npz names/shapes; do not repeat manifest headers on every row or pretend arrays contain json fields:

| artifact | required payload |
|---|---|
| `protocol.json` | kind `attribution_protocol`; fixed years/target, source selection digest, spec snapshot digest, population/design/scale/generator/scenario rules and three component bindings. no derived results or reciprocal prepared-artifact hash; human protocol explains this frozen execution contract |
| `prepared.json` + ledgers/arrays | seasons, source/grid/design identities, population ids, annual rates, ordered players/strata, segment/event/coverage refs. segment key `(game_id,period,start,end,attacking_team)`; event key `(game_id,source_index)`; assignment/mask reasons inspectable |
| `annual.json` + arrays | benchmark, season, previous hash/null, all-seen/current players, entrant/carried status, `r,a,q`, scale curve/status, centered `M,V,S`, context means, centering weights, negative-rate and equation-residual diagnostics, time/memory. check finite shapes/order; no kronecker allocation |
| `reference.json` + rows/surfaces | final population, three component bindings, design/year treatment, joint weights/exclusions/support, two cell vectors; one reference identity throughout |
| `assessment.json` | population/fit statuses, final contrasts, pair ids, recovery, named scenario deltas and valuation limitations; missing is null plus reason |
| `result.json` | evidence refs, population/numerical/recovery statuses, resolution/sensitivity summaries, one recommendation, `admission:not_admitted`, `handoff:null` |

manual commands: `prepare --protocol --selection --out`; `fit-year --prepared --benchmark --season [--previous] --out`; `simulate --protocol --out`; `assess --prepared --chains --simulation --out`. selection is schema 1, kind `attribution_selection`, purpose `research|fixture_exercise`, ordered `{season,corpus_path}` entries and target season; research requires all five exact manifests. the frozen protocol supplies the three component completion bindings and numeric/scenario contracts; downstream artifacts inherit its digest. assessment receives them through that binding, builds the reference and does not fit. first year rejects a previous state; later years require the immediately preceding compatible state. scientifically unavailable branches remain explicit; execution/source/i/o errors cannot become valid missingness. completed annual artifacts survive later failure; manual rerun is recovery, not a new runner/checkpoint engine.

freeze selection RULES before preparation; freeze resulting player-pair ids in `prepared.json` before fitting. derived rates, covariance shape and estimated scales belong in their population/annual artifacts, not a rewritten protocol. fixture purpose allows compact available seasons and synthetic solver exercises without claiming research completion.

bulk inputs and expensive outputs remain external-only under `/Volumes/Expansion/hockey-stats`. detached fixtures/local corpus support software checks; real five-season work needs the drive. no local fit mirror, docker/colima, acquisition or drive investigation. preserve distinct broken-game evidence under the existing fixture policy.

## content, verification and completion

the designer supplies three static figures: selected-player scalar contrasts and meaningful band; corresponding maps with common axes/scales and matched scalars; direct/product valuation scatter with equality line. use the outcome-blind pairs, not attractive results. tables cover all players and five-season coverage; no card/dashboard framework. distinguish observed counts, recorded-rate associations, simulated truth and provisional goals. show signed suppression, units, exposure and conditioning. residuals are not luck; a centered effect map is not observed shot density.

non-overlapping implementation order, with independent adversarial review at each boundary:

1. **population:** temporary integration red → green; independently account for boundary goals, `both`, zero-event time, unknown horizons, missing locations, ownership ambiguity, score failures and collateral masks. reuse complete fixtures; preserve new distinct reproducers. source review before real fitting.
2. **model:** independent small problems verify weighted posterior/covariance, centering/prediction invariance, exact map/scalar projection, pair covariance, entrants/skipped years and no future leakage. compare factorized arithmetic with a small explicit covariance. verify the permanently paired difference is a likelihood null direction; do not manufacture information in it.
3. **projection:** independently verify native reference predictions, `E[q*g]` versus the incorrect product of means, paired-difference covariance and transport conservation. verify chance consumers affected by extraction preserve behavior.
4. **real evidence:** reconcile five inventories, both ledgers and ten annual outputs; independently recompute selected counts/exposure and scalar/region/valuation projections. finite solves `K U=R` require residual `||K U-R||inf/(1+||K||inf*||U||inf+||R||inf)<=1e-8`, covariance symmetry and nonnegative contrast variance within recorded rounding tolerance. no silent jitter/clipping or repeated full fits. report bound/refinement limits and negative rates as such.
5. **closure:** refactor to the named owners, rerun affected checks, obtain independent statistical/source/systems/content review, then **delete all temporary tests, controllers and test-only dependencies**, per this slice's instruction. retain fixtures, scientific simulator/assessment commands and evidence. no lasting harness selected; [07](07-lightweight-testing.md) stays separate.

freeze protocol/spec snapshot, source/component hashes, exact design/generator, numeric settings and output root before real assessment. simulation recovery/coverage need not pass a favorable threshold; scientific failure or inconclusiveness can complete 04a. software/identity failures cannot be disguised as scientific findings.

the decision answers separately: **which populations are usable; which meaningful differences resolve under this working model; which conclusions change under the stated stresses.** give one justified next step/dependencies. unit stresses and conditional intervals cannot close the consequence-budget issue or admit player ability. no automatic follow-on campaign.

costs: two populations/chains, ten coefficient-covariance solves with bounded scale searches, full historical covariance, 600 small synthetic replicates and common-reference scoring. storage is `O(p²+k²+pk)`, not `O(p²k²)`; stream sufficient statistics, avoid dense observation matrices, measure actual time/memory. statistical prices are gaussian/separable uncertainty, scalar-selected shrinkage, unsmoothed maps, selective coverage, omitted deployment mechanisms, age-neutral drift and reference extrapolation. these are explicit research limits, not final ability evidence.
