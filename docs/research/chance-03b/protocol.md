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

the following practical gates are fixed before full development assessment. primary selection and exact consequential development-bin ids remain to be recorded before confirmation. these are operational judgments about acceptable error and perturbation, not estimated physical truths or fitting-uncertainty bounds.

- each of the four primary loss comparisons has maximum tolerated excess `epsilon = 0`. an interval upper bound at or below zero supports the requirement; a lower bound above zero rejects it; overlap is insufficient evidence. no positive degradation allowance has an independent justification.
- overall factual calibration must lie within `[-0.0025, 0.0025]` goals per attempt: one quarter of a goal per 100 attempts. each consequential fixed bin must lie within `[-0.01, 0.01]`: one goal per 100 attempts in that bin. the whole 95% interval must fit inside the margin; an interval wholly outside rejects; boundary overlap is insufficient.
- a development bin is consequential if it carries at least 5% of its primary population's attempts **or** predicted goal mass. freeze those exact ids. a confirmation bin meeting either same 5% trigger also requires adequate evidence, even if it was rare during development. support requires at least 4,000 attempts and 100 contributing games, plus the interval criterion. observed goal count is never an exclusion condition. unsupported consequential bins prevent broad support; sparse bins remain visible, and margins do not widen to accommodate their uncertainty.
- on each population separately, each fixed sensitivity alternative must have mean absolute event-value change at most `0.0025`, maximum absolute change at most `0.02` expected goals, absolute total-value change at most 5% of the primary total, and spatial absolute-mass change at most 10% of that total. the mean budget matches the overall calibration budget; the maximum prevents a small aggregate from hiding consequential individual changes. totals and absolute spatial mass guard different forms of cancellation.
- blocked origins must have mean total variation at most `0.10` and maximum at most `0.30` against the primary, and require independent attributable geometry evidence with its uncertainty and selection limits. total variation measures relocated probability mass, not displacement in feet. passing these perturbation budgets cannot establish physical accuracy or downstream player robustness.

inspect all named subgroup summaries. a consequential subgroup is one carrying at least 5% of its factual population's attempts or predicted goal mass. an aggregate calibration discrepancy beyond `0.01` or worse mean proper loss is a diagnostic requiring investigation; aggregate summaries do not supply clustered intervals. an unexplained consequential failure or unsupported location semantics prevents a broad claim. do not manufacture subgroup intervals, discard failing categories or silently change the population. temporal diagnostics use actual game dates and inspect pooled loss/calibration drift and adjacent-game dependence; implicated longer dependence requires additional bounded checks, not a claim that the game bootstrap already covers it.

source matching remains the reviewed [02b contract](../../specs/02b-reconstruction.md). development found strongly selective same-clock exclusions, including recoverable facts under a broader contract. [the source-contract issue](../../issues/same-clock-event-matching.md) records that limitation. this study cannot certify the excluded population or downstream event/exposure compatibility by evaluating retained attempts.

## retained calculations

pool candidate-minus-benchmark per-game loss sums over pooled attempt counts, separately for log loss and brier score in both factual prediction populations. use 2,000 paired game draws with `numpy.random.Generator(PCG64)` and seed `3032026`; recompute the ratio on each draw. report 95% percentile intervals. any zero-denominator draw makes that interval null, with its undefined-draw count and reason; do not discard or replace draws.

report overall and fixed-bin predicted-minus-observed rates with counts and game-resampled intervals. use the existing twenty bins and preserve unsupported bins. report saved aggregate subgroup summaries without suggesting clustered subgroup intervals are available. proper-loss improvements do not themselves prove calibration; see [official calibration guidance](https://scikit-learn.org/stable/modules/calibration.html).

paired assessments must share consumed inputs, populations, coverage, preparation/prediction definitions and one clean executing analysis revision. models may have separately identified fitting revisions. sensitivity scores must share ordered selections and lockstep `(game_id, source_index)` keys/statuses; a null `event_id` is allowed. reject incompatible streams instead of joining or reconstructing evidence again.

within each training window, compare frozen alternatives against the named reference score on the same grid and empirical joint reference weights. report event-value differences, absolute totals, blocked-origin total-variation distance and spatial opportunity mass separately for blocked and unblocked attempts. shared plot scales must expose total as well as shape changes. a supported final-versus-confirmation comparison deliberately changes the training window and empirical reference; identify both refitting and changed reference weights, without attributing their combined change solely to the kernel. observed-record likelihood is a same-grid fit diagnostic, not a measurement of origin accuracy.

## independent origin evidence

select development block examples across recorded geometry and source conditions before inspecting fitted maps. seek attributable replays with explicit location uncertainty. public highlights selected for goals or spectacular saves cannot supply representative block validation. unavailable replay evidence stays unavailable. masked unblocked locations and plausible inferred geometry do not resolve [shot-location evidence](../../issues/shot-location-evidence.md).

support would require independently attributable release locations, stated spatial uncertainty, and representative coverage of relevant source and geometry conditions sufficient to assess spatial error. the four initial source examples come from one game and cannot establish that coverage even if their replays become available. queried replay endpoints supplied no independent release locations. casewise source agreement can establish semantics; it cannot support league-wide origin accuracy. this study therefore has insufficient independent origin evidence before confirmation. confirmation probabilities cannot reverse that judgment; sensitivity may additionally reject spatial stability. later representative origin evidence requires its own declared acquisition/annotation procedure and uncertainty assessment.

## decision and handoff

the scientific decision addresses probability, calibration and spatial origins/values separately, including consequential subgroup failures and limits of sampling intervals conditional on fitted models. unsupported origins cannot be hidden by an unblocked-only cutover. support requires all applicable gates; rejection or insufficient evidence records concrete follow-up issues and withholds 04. a supported decision alone authorizes the specified separate final retrospective fit and its stability comparison, not publication or player attribution.
