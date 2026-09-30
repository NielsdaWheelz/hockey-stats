# chance-03b protocol

status: development draft. implementation and fresh acquisition authorized on 2026-09-30. confirmation has not begun. numerical material criteria will be resolved from development evidence and scientific meaning, then committed before confirmation; this draft grants no acceptance.

## claims and evidence

assess `chance-1` on genuine-5v5 regular-season attempts with both reported goalies, under the existing preparation contract. distinguish factual unblocked conversion, outcome-blind all-attempt goal probability, and retrospective reference opportunity. the latter is a standardized value, not a factual probability conditional on a known block. predictive success cannot establish the accuracy of a latent origin.

fresh references and captures live under `/Volumes/Expansion/hockey-stats/`. use all inventoried games when reporting source dispositions; do not drop defective games to obtain a runnable fit. selected `input_error` or `identity_mismatch` stops fitting. missing captures, unavailable identity and unsupported attempts remain attributable gaps. archive inputs and the three fixture captures remain unchanged.

## chronological procedure

development fits 2023–24 and assesses 2024–25. confirmation fits 2023–24 plus 2024–25 using the frozen configurations, then assesses 2025–26 excluding `2025020001`, `2025020006` and `2025021094`. the exclusions follow prior development exposure, regardless of fresh retrieval. the final three-season retrospective fit is conditional on scientific support; its training-mix reference is distinct from confirmation and from a 2025–26 league reference.

inspect source integrity uniformly before fitted confirmation performance. record exact selections, input digests, configuration digests and clean executing revisions externally. preserve failed fits. a substantive revision after confirmation consumes those games as development evidence and cannot claim fresh confirmation from rerunning them. see [selection-bias research](https://www.jmlr.org/papers/v11/cawley10a.html).

## bounded resource measurement

the first eight ids in the admitted 2023–24 inventory are the deterministic preparation/fitting measurement selection. these games are capacity evidence, not season validation. the initial configuration copies the existing fixture numerical anchor solely to measure the unchanged estimator. record preparation, fit, assessment and scoring wall time, peak resident memory and artifact bytes; distinguish profiled runs from ordinary execution. profile demonstrated costs before changing implementation. no season-scale capacity claim follows by multiplying fixture timing.

if measured fit replacement cost warrants it, resolve completed-em-boundary recovery before launching expensive windows. any recovery must bind inputs, configuration and implementation; an interrupted inner optimizer may restart. no job engine or automatic retry is implied.

## development choices to resolve

investigate a small named set of existing kernel, origin-prior and penalty alternatives. define each against an observed development question; no cartesian sweep, new features, new likelihood or changed five-foot grid. numerically fixed penalties carry across windows without silent rescaling. quantify season/source coverage, entrants, score/role/home-away/shot-type summaries, and selective missingness before choosing supported claims.

the bounded 128-game development measurement found 230 of 656 cells without an observed unblocked origin, substantial low-count actor populations, and broad blocked posteriors under the numerical anchor. independent review also identified untested directional concentration. these motivate five full-window candidates, each changing one existing quantity:

| candidate | difference from anchor | scientific question |
|---|---|---|
| `anchor` | none | does the implemented numerical anchor survive a full chronological assessment? |
| `short_kernel` | `kernel_distance_ft: 10` instead of 20 | does halving the displacement scale materially change inferred origins and opportunity, after refitting? |
| `weaker_direction` | `kernel_direction_strength: 2` instead of 4 | does halving directional concentration expose dependence on the assumed direction from release toward goal? |
| `stronger_origin_prior` | `origin_pseudocount: 100` instead of 10 | does tenfold uniform origin regularization expose consequential dependence on sparsely observed cells? |
| `stronger_actor_pooling` | `ridge_actor: 20` instead of 10 | does doubled nuisance-actor pooling improve chronological probability behavior without destabilizing standardized opportunity? |

the range is a bounded perturbation experiment, not a confidence region or a calibrated kernel estimate. neither distance scale nor direction strength is established by the source. distance is an exponential scale, not mean displacement; report implied displacement under the actual finite-rink kernel. the prior and actor changes probe the measured sparse-data problem. all remaining settings, the likelihood and the 656-cell grid stay fixed. investigate all five on development and carry the entire set into confirmation; choose the primary candidate and resolve the practical gates before confirmation.

absent an independently justified positive tolerance, each primary loss excess margin is zero. calibration margins and supported-bin rules must reflect hockey consequences and development precision, independently of whether the candidate passes. origin/value sensitivity requires explicit practical limits and independent evidence judgment. those values and the sensitivity set are unresolved during this draft and must be fixed before confirmation.

## retained calculations

pool candidate-minus-benchmark per-game loss sums over pooled attempt counts, separately for log loss and brier score in both factual prediction populations. use 2,000 paired game draws with `numpy.random.Generator(PCG64)` and seed `3032026`; recompute the ratio on each draw. report 95% percentile intervals. any zero-denominator draw makes that interval null, with its undefined-draw count and reason; do not discard or replace draws.

report overall and fixed-bin predicted-minus-observed rates with counts and game-resampled intervals. use the existing twenty bins and preserve unsupported bins. report saved aggregate subgroup summaries without suggesting clustered subgroup intervals are available. proper-loss improvements do not themselves prove calibration; see [official calibration guidance](https://scikit-learn.org/stable/modules/calibration.html).

paired assessments must share consumed inputs, populations, coverage, preparation/prediction definitions and one clean executing analysis revision. models may have separately identified fitting revisions. sensitivity scores must share ordered selections and lockstep `(game_id, source_index)` keys/statuses; a null `event_id` is allowed. reject incompatible streams instead of joining or reconstructing evidence again.

within each training window, compare frozen alternatives against the named reference score on the same grid and empirical joint reference weights. report event-value differences, absolute totals, blocked-origin total-variation distance and spatial opportunity mass separately for blocked and unblocked attempts. shared plot scales must expose total as well as shape changes. a supported final-versus-confirmation comparison deliberately changes the training window and empirical reference; identify both refitting and changed reference weights, without attributing their combined change solely to the kernel. observed-record likelihood is a same-grid fit diagnostic, not a measurement of origin accuracy.

## independent origin evidence

select development block examples across recorded geometry and source conditions before inspecting fitted maps. seek attributable replays with explicit location uncertainty. public highlights selected for goals or spectacular saves cannot supply representative block validation. unavailable replay evidence stays unavailable. masked unblocked locations and plausible inferred geometry do not resolve [shot-location evidence](../../issues/shot-location-evidence.md).

## decision and handoff

the scientific decision addresses probability, calibration and spatial origins/values separately, including consequential subgroup failures and limits of sampling intervals conditional on fitted models. unsupported origins cannot be hidden by an unblocked-only cutover. support requires all applicable gates; rejection or insufficient evidence records concrete follow-up issues and withholds 04. a supported decision alone authorizes the specified separate final retrospective fit and its stability comparison, not publication or player attribution.
