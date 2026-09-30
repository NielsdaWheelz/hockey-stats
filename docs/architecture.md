# architecture and statistical design

status: architecture direction completed in commit `9ff024a`; [01 capture](specs/01-capture.md), [02a interpretation](specs/02-interpretation.md), [02b reconstruction](specs/02b-reconstruction.md) and [02c corpus/reference admission](specs/02c-corpus.md) are reviewed and merged. [03a](specs/03a-chance-workflow.md) specifies the chance-model workflow; separate 03b owns real training and scientific acceptance. the [product brief](brief.md) remains authoritative. no modeling implementation or scientific acceptance is implied.

## operating scale

this is a website run by one person. retain work according to its replacement cost: source evidence and hours-long fits are worth saving; cheap transformations and website builds are worth rerunning. a local analysis command produces a sqlite file; the website reads it. publication can stop the server, replace the file, restart and require a page reload. one previous database is enough for data rollback; git supplies code history.

the scope review removed hot publication switching, client revision pinning, expired-revision handling, a mandatory effect-to-python job runner and per-stage completion protocol, and an assumed future server-rendering migration. their benefits do not justify them for the current use. costs accepted instead: a few manual commands, brief browsing interruptions, coarser reuse of saved analytical work and rerunning cheap steps. future automation needs evidence of recurring work saved, not a hypothetical failure scenario.

## method

resolve consequential dependencies one at a time. for each question, explain the observable difference, recommend an answer with its costs, and record the user's choice separately from engineering judgment. ask about purpose and operating constraints; investigate empirical matters and own routine technical decisions. new information may reopen a dependent decision, with the reason stated.

statistical meaning comes before model selection. required interactions and operating conditions come before service topology or storage. exact model formulas and quantitative admission rules belong in their scientific specifications; unknown data coverage cannot be settled by preference.

## decision order

| branch | depends on | required outcome | status |
|---|---|---|---|
| temporal meaning of ability | settled player-analysis purpose | distinguish season-level ability, ability at a cutoff, and next-season projections | settled: season-level ability |
| evidence and scientific scope | temporal target, public-data core | define usable observations, inferred inputs, context adjustment, spatial response, and credible validation | spatial attribution and scalar accounting selected below; candidate models, input admission and evaluation remain to verify |
| user interaction | temporal target and distinction between observations and estimates | decide which selections query existing estimates and which require computation; clarify comparison and evidence access | settled: league table, name search, profiles, comparisons, full-season summaries and game rows; no date splits or interactive fits |
| operating envelope | required interaction and operator control | local/detached-drive behavior, available hardware, batch resource use, and initial access needs | local operation and operator-triggered cadence settled; hardware reported; workload measurements deferred to implementation |
| source and correction ownership | evidence needs and operating envelope | capture fidelity, source identities, missingness, reconstruction, correction and replay contracts | working contracts below; endpoint-specific interpretation and admission rules require data evidence |
| application/numerical boundary | settled language split and data responsibilities | explicit input/output files and one owner per calculation | direct commands and shared files selected below; detailed fields belong to slice specifications |
| storage and publication | access patterns and boundary | compare alternatives, choose coherent publication and rollback, identify reproducible inputs | explicit publication, active plus one rollback settled; sqlite publication selected after review; runtime compatibility to verify |
| runtime and frontend | interactions, publication, operating envelope | choose effect version, framework and process layout with current evidence | engineering selection below; integration checks belong to implementation |
| updates and failure behavior | selected responsibilities and runtime | operator commands, evidence cutoffs, partial input, retry, invalidation, and interrupted-work recovery | operator flow, failure behavior, justified gaps and compatible rollback selected below |
| verification and slice handoff | completed contracts | meaningful scientific/engineering checks and first-slice acceptance; no implementation in this phase | verification families and dependency outline below; detailed slice specification awaits phase transition |

the sequence identifies dependencies, not a requirement to ask ten questionnaires. a decision supported by confirmed requirements and evidence can be resolved by engineering judgment, with its tradeoff recorded.

## handoff to slice specifications

the product interview and architecture supplied enough direction to begin specifications. remaining detail belongs to the relevant slice:

1. specify faithful source capture and a bounded, independently checked offline corpus first. the user has now authorized this phase; [the plan](plan.md) assigns subsequent boundaries.
2. carry data-dependent decisions into their scientific specifications: exact likelihoods, reference weighting, priors, eligibility, uncertainty method and quantitative assessment criteria. source audit and separated development work may inform these choices; freeze assessment rules before judging confirmatory results. an architecture interview cannot supply the missing empirical evidence.

the disconnected hdd delays legacy-corpus admission and full-data measurements, not these architecture decisions. actual coverage, reconstruction accuracy, imputation quality, fitted-model validity and resource use remain empirical work during the relevant authorized slices. public deployment and additional card components remain later work. no need to settle every future slice or validate an unimplemented model to finish this phase.

proposed dependency order for the next phase:

1. faithful capture and a bounded offline corpus. this first foundation must demonstrate preserved payload bytes and independently checked facts, without inheriting the legacy fixture labels. verify the chosen sqlite reader and python entry point when their slices need them.
2. interpreted hockey records, 5v5 exposure, coordinate semantics and coverage accounting, with explicit unavailable quantities. historical-corpus admission proceeds when the drive is available.
3. all-attempt chance valuation and blocked-origin inference: implement the specified candidate in 03a, then admit real training evidence and assess it in 03b. history-informed spatial player attribution follows scientifically supported opportunity values. fixture verification alone does not admit a model.
4. publication and browsing can develop against explicitly labeled compact fixture outputs once the shared contract is specified; they need not wait for full-season fitting. integrate the admitted scientific outputs into sqlite publication, explicit activation/rollback, and the league/profile/comparison/game views to complete the first product.

these are dependencies, not fully specified prs or a requirement for four large changes. split each into reviewable slices when its requirements are concrete. finish the personal product before adding current-season operation, public delivery or further card components. the next phase should specify the first foundation in detail, not prematurely freeze every future model or screen.

## settled inputs

the first target remains league-wide 2025–26 regular-season 5v5 skater chance creation and suppression, with observed results alongside history-informed ability estimates. hockeyviz's interpretability and components guide the models; hockeyviz and jfresh cards are the long-term destination. the user is the initial audience. current-season analysis follows the fixed-season result, with local runs initiated whenever the user wants. effect owns application behavior; python owns numerical work. raw captures remain intact. paid inputs are optional later enrichment.

## interview record

### 1. temporal meaning of ability — settled

question: a skater struggles from october through december, then plays substantially better from january through april. should the 2025–26 headline characterize their underlying level across the season, or their ability when the season ended?

recommendation: season-level persistent ability first, estimated from the selected season with earlier information as evidence about persistence. season-end ability requires an explicit account of within-season change and evidence that the model can distinguish change from noise. neither is next-season contribution, which would introduce assumptions about future aging, availability, role, and minutes.

cost of the recommendation: a sustained late improvement remains blended with earlier play. later current-season updates describe the season's underlying level estimated from evidence incorporated so far, not claim to identify today's condition.

separate the period described, the evidence cutoff, and the publication revision. the public [magnus 9 methodology](https://hockeyviz.com/txt/magnus9EV) documents successive season fits with historical priors; a cutoff or card date alone does not settle the temporal target.

user decision: “underlying level across the season.” adopted: season-level persistent ability, with earlier seasons informing the estimate and recorded season results shown separately. this is not a season-end state estimate or a next-season projection. exact evidence weighting, priors, and eligibility remain scientific specification matters.

### 2. user interaction — settled

question: should the first website explore existing validated analyses, or also launch new model fits when the user selects arbitrary periods or changes modeling assumptions?

recommendation: browse, compare, and query published analytical datasets; initiate new fits through explicit research/operator commands. browsing can remain interactive. changing players, comparison cohorts, or displayed recorded-event ranges need not train a model. a filtered event summary does not change the meaning or population of an existing season-level ability estimate.

cost of the recommendation: a new adjusted estimate for a custom period or model configuration requires a separate run and validation before being shown as an established result. it cannot appear merely because a filter changed. browser-initiated fitting would additionally require job status, interruption/recovery, result identities, and a distinction between exploratory and published estimates.

user decision: “explore published analyses; run new fits separately.” adopted: the website queries published analytical datasets; fitting remains a separate research/operator activity. the exact estimator, storage technology, and publication admission checks remain open.

### 3. detached-drive capability — settled

ordinary development and tests already must work without the external drive or live upstream requests. the remaining question is whether detached operation also needs substantive statistical experiments on real historical data.

recommendation: keep the latest complete published analytical dataset locally, alongside bounded development fixtures. this supports browsing real published profiles, comparisons, and maps while detached. full rebuilding and fitting require their explicitly identified historical inputs, which may remain on the external drive.

cost of the recommendation: local storage for published outputs as well as fixtures; no promise of substantive new fits without the drive. measure output size before choosing representation or a storage budget. fixtures cannot silently stand in for a training corpus.

alternative: also retain a separately identified real-data research subset locally for statistical experiments. this consumes more local storage and needs a defined scientific purpose, coverage, and limits; a convenient subset does not establish full-population model validity. whether the website needs network access is a separate access/deployment decision.

user decision: “browse published results and develop the application,” with the same requirement for the eventual public production website. adopted: local browsing and public serving must function from their complete published datasets without the external drive or fitting environment. substantive detached statistical experiments are not required for the initial target.

engineering consequences: each serving environment must hold all data needed for its supported published views, with a coherent revision and evidence cutoff. a failed or interrupted update leaves the previous valid publication available; a known-invalid publication requires an explicit correction or withdrawal. source corrections cannot silently mix new observations with estimates from unidentified older inputs. exact storage and publication mechanisms remain open.

this decision separates serving availability from analytical computation and freshness. interactive queries remain permitted. static-only hosting and public launch timing do not follow from it; questions 4 and 5 settle compute location and operator-controlled cadence. the tradeoff is duplicated published outputs and an explicit publication step; source history and fitting dependencies need not be duplicated into the serving environment.

### 4. compute location and recovery — settled location; recovery design judgment

original question: for the first completed-season release, must data processing and model fitting work while the user's computer is off or unavailable?

user decision: local batch runs “initially -- and always”; assume indefinitely that processing and fitting rely on the local machine and hdd. the user also suggested checkpoints. adopted: the analytical producer runs locally indefinitely, including ingestion, processing, and fitting. public serving remains independent. remote fitting and a planned migration to remote computation are outside the design.

cost: rebuilds and new publications depend on local compute, drive access, and successful execution; long runs can occupy the machine. inspect hardware and benchmark representative work before choosing concurrency, memory budgets, or checkpoint intervals. question 5 subsequently settles operator-triggered execution; scheduling is an optional convenience rather than a requirement.

recovery design judgment:

- save fitted models and any genuinely expensive derivations with their inputs, configuration and implementation identified. check those recorded inputs before reuse. rerun cheap transformations and assembly; do not create a completion record or cache entry for every step.
- resume within a long numerical fit only when the selected fitter supports the required state and compatibility checks. model parameters alone may support a warm start, but do not establish continuation of the interrupted algorithm. account for optimizer/sampler state, random state, and progress where required; otherwise restart that fit while retaining completed predecessors.
- choose checkpoint frequency from measured recomputation cost and storage/write overhead. do not introduce a general workflow engine for this requirement.
- completed computation still must pass the scientific and publication checks. recovery never makes partial output publishable merely because it exists.

primary-source check on 2026-09-29: [pymc sampling documentation](https://www.pymc.io/projects/docs/en/stable/api/generated/pymc.sample.html) describes persisting partial draws during sampling; [stan's sampling configuration](https://mc-stan.org/docs/2_39/cmdstan-guide/mcmc_config.html) describes reusing adapted metrics and step sizes. our inference: output persistence and numerical continuation require separate verification. neither source establishes a generic exact-resume contract for an unselected fitter. no numerical library is chosen here.

### 5. freshness and execution cadence — settled

original question: should next-morning freshness depend on local availability, or require a nightly availability commitment?

user decision: “conditional freshness,” clarified as “i'll run it when i want.” the user rejected enterprise-style freshness promises for this single-user prototype. adopted: operator-triggered local runs, with no next-morning deadline, required nightly availability, or automatic catch-up obligation. this clarification supersedes the earlier preference for next-morning updates as a requirement.

between runs, the website serves the last valid publication and shows its actual evidence cutoff. a run can catch up when the user next invokes it. retain scientific validity, coherent publication, and useful interruption recovery. result age alone is not a validity failure.

tradeoff: published analysis may lag the season for as long as the user chooses. that is accepted behavior. choose local commands and proportional saved work; scheduling or alerts need a demonstrated operator benefit before adding them. the freshness-policy issue is resolved and its record removed.

### 6. local hardware — recorded

user-reported hardware on 2026-09-29: macbook pro, apple m5 pro, 18 cpu cores (6 super and 12 performance), 64 gb ram. these are user-provided facts rather than independently measured performance. device identifiers are unnecessary for planning and are not retained here. external-drive capacity and layout remain part of its later inventory.

engineering recommendation: use this inventory to size a representative benchmark and choose resource limits during implementation. account for the rest of the user's workload when choosing memory and concurrency; 18 cores and 64 gb installed memory are not a requirement to occupy all of them. evaluate scientific adequacy and local feasibility together. no runtime estimate, gpu requirement, or numerical-library choice is established by this inventory.

### 7. evidence drill-down depth — settled

question: when inspecting a player profile, how far should the first version let the user drill into recorded results?

recommendation: a game-by-game breakdown of recorded counts and reconstructed 5v5 exposure for the selected season, with inclusion/coverage information tied to the same publication. this helps identify which games account for the displayed results. the cost is additional published aggregates and a supporting view; event-level investigation remains in local analytical tools.

user decision: “game-by-game breakdown.” adopted: the first profile includes the recommended game table. individual-event browsing is deferred; its investigation remains possible through local analytical tools.

a game table describes results, not an additive decomposition of the adjusted season-level ability estimate. prior-season evidence must be identified separately; selected-season games are not the entire evidence behind a history-informed estimate.

publication consequence: ship the game aggregates, evidence status, and relevant definitions with the profile outputs. for the same declared selection and usable population, additive counts and exposure reconcile to season summaries; rates are computed from their specified aggregate numerators and denominators, not by averaging game rates. if xg or another modeled quantity is included later, its label and model revision must remain explicit.

### 8. website access and publication retention — settled

question: after a corrected analysis replaces an earlier publication of the same season, must the first website let the user revisit the earlier numbers, or is local retention sufficient?

original recommendation: the website serves the active publication, retaining earlier publications locally for reproduction and rollback. the user accepted active-only serving and narrowed retention.

user decision: “serve the active publication. definitely,” with one backup for rollback and no broader archive. adopted: retain the active publication and one previous valid publication. ordinary profile links follow the active revision and display its identity. no historical-publication browsing is required.

user clarification: “no old builds, that's what git history is for.” the reason is replacement cost: old model fits would take hours to recreate, whereas rebuilding the website takes minutes. save expensive analytical artifacts and use git for application code. apply that distinction throughout the system rather than treating every interruption as a reason to add recovery machinery.

the cost is explicit: an older discarded revision may no longer be available to inspect or reproduce. this supersedes earlier broad statements about preserving every prior publication. retention applies to publication revisions, not playing seasons. protect source history, priors/model artifacts, configurations, and implementation references required by the retained publications or current research. keep shared inputs once; a rollback publication does not require another copy of the training corpus.

build candidates and resumable work may temporarily occupy space beyond the two retained publications. discard superseded outputs only after successful activation and identification of the valid rollback target; do not silently reuse a known-invalid release. begin with explicit operator cleanup, not an automatic retention service. the existing legacy archive is unaffected by this new-publication policy.

### 9. finding players to investigate — settled

question: should the first website include a sortable league-wide skater table for finding players to investigate, or begin with name search and comparisons of players already in mind?

recommendation: a compact league-wide table alongside name search. show separate offensive and defensive estimates, selected-season exposure, and meaningful uncertainty or unavailable status; link to profiles and the compact comparison. this supports discovery from the analysis rather than requiring a preselected shortlist.

cost: one additional view, a published player-summary index, and defined sorting behavior. it introduces no new model or combined total-value score. sorting estimated effects does not establish a meaningful difference between adjacent players, and exposure is not a substitute for uncertainty. detailed filters remain subordinate to the confirmed use case.

user decision: “compact league-wide table plus name search.” the user also explicitly wants tables for sorting and ranking, and distribution charts showing where a player lies, as long-term capabilities. adopted: the compact sortable discovery table is in the first target; richer ranking tools and distribution views belong to the long-term destination. this does not add a combined player-value score or require the full comparison toolkit initially.

engineering consequence: distinguish the fitted estimate, its model baseline, the population used to describe relative standing, and the rows currently displayed. selecting rows must not silently refit an estimate or redefine a percentile's reference population. a later distribution chart must identify whether it describes the spread of player estimates or uncertainty about an individual player; those are different distributions. precise chart designs and cohort defaults remain for their specifications.

reference checked on 2026-09-29: [money puck's player-statistics page](https://moneypuck.com/stats.htm) separates a scoring-leaders surface with an ice-time control from linked individual career statistics and shot maps. this supports the navigation pattern, not a requirement to copy its metrics or full filter set. the read-only check did not exercise table interactions.

### 10. observed summaries for selected dates — settled

question: should the first profile show the complete selected-season observed summary with its game-by-game breakdown, or also let the user select dates and recompute observed summaries for that range?

recommendation: complete-season summaries and the already agreed game table first. this supports the settled season-level question and keeps the initial publication/read contract bounded. cost: a quantitative early/late-season split initially requires local analysis; inspecting individual game rows remains available in the website.

alternative: add date-range summaries of recorded counts, supported exposure, and rates. this adds selection and aggregation behavior, coverage handling, and clear labels for the different periods. the season-level ability estimate remains unchanged; a january-only observed rate cannot be presented as a january ability estimate. derived quantities such as xg would retain their model identity and label even when aggregated over selected games.

user decision: “complete-season summary plus game-by-game breakdown. no window/date-range splits.” adopted: publish and browse the complete-season summary and its game evidence; no custom date selections or range aggregation. the hypothetical recorded-event filtering in question 2 does not establish a requirement. date splits are not added to the long-term backlog by default.

### 11. intent to publish — settled

question: after an intended update passes the scientific and publication checks, should it replace the active results automatically, or remain a candidate until the operator explicitly publishes it?

recommendation: prepare a validated candidate, then activate it with an explicit local publish command after inspecting the run report. this keeps successful computation separate from the decision to replace the website's results. cost: one additional operator action; the active publication remains unchanged until then. this is not a web approval workflow or a requirement to review every player manually. inspection supplements the required checks rather than replacing them.

user decision: “explicit publication.” adopted: successful runs produce candidates; a separate operator publish action activates a selected candidate after the required checks. neither research nor intended production computation automatically replaces the website's results. retain coherent activation and one valid rollback publication. inspection is available through the run report; no separate approval service is implied.

### 12. blocked-shot origins — settled scope; estimator requires validation

user decision: “we should impute block shot origin location.” adopted: include blocked attempts through modeled shooting origins in the intended all-attempt analysis. this settles the inclusion direction; source semantics, estimator selection and validation remain scientific work. preserve source block coordinates and record origin inference separately. unblocked-only analysis remains a benchmark, not the default product or an automatic fallback if validation is difficult.

cost: an additional reconstruction model, assumptions about unobserved origins, and sensitivity/uncertainty work. raw fidelity and imputation are compatible because inference never overwrites the evidence. the open [location issue](issues/shot-location-evidence.md) now concerns how to support the chosen imputation, not whether blocked attempts belong in scope.

### 13. publication with coverage gaps — settled

question: if some games cannot be reconstructed reliably, must they block publication of the entire season?

recommendation: permit explicitly incomplete coverage only when the scientific evaluation supports the remaining claims; withhold affected estimates where it does not. report included and excluded evidence and reasons, with per-player consequences where identifiable. an observed subtotal must be labeled as covering included evidence, never as a complete-season total. the analytical target can remain season-level ability, but selective missingness may make that estimate unsupported.

tradeoff: useful results can become available before every source defect is repaired, at the cost of incomplete recorded totals and more coverage explanation. requiring every game gives a stricter completeness condition but may prevent publication indefinitely. neither choice allows biased or numerically failed fits to pass merely because the operator wants a result. exact admission criteria require scientific specification; a league-wide coverage percentage alone cannot establish validity.

user decision: “allow justified, visible gaps.” adopted: publication may contain supported results despite incomplete evidence, with explicit coverage and unavailable unsupported quantities. local withholding is appropriate only when the remaining claims remain supported; a shared input defect can still invalidate the entire fitted model. this does not authorize silent whole-game exclusion or filling missing facts to make a result publishable.

## scientific design direction

working scientific judgments on 2026-09-29 within the confirmed brief, informed by primary-source review and independent statistical/product reviews. these establish the meaning to preserve, not a validated model or permission to begin implementation. [reference evidence and version limits](research/statistical-methods.md)

### the map and headline describe the same adjusted quantity

estimate a player's season-level association with creating or suppressing spatial scoring-opportunity rates at genuine 5v5, adjusted for supported context and stabilized by earlier evidence. express the first offensive and defensive magnitudes as changes from the declared league reference in expected goals per sixty minutes. these are model-dependent opportunity values, not goals scored, total player value, or proof of causal isolation.

the adjusted spatial surface is primary. the scalar offensive and defensive summaries come from that same fitted result. a scalar xg regression accompanied only by a map of observed shots would not explain where the adjusted player contribution appears. scalar regularized adjusted plus-minus remains a useful benchmark; descriptive maps remain separately labeled evidence.

for a discrete representation, let each cell contain its contribution to the adjusted rate, in expected goals per sixty minutes. sum the cells to obtain the corresponding offensive or defensive scalar. if the representation instead stores a density, integrate with the declared cell areas. smoothing, clipping and rendering cannot silently change the underlying total. the defensive field describes a change in chances allowed; negative is suppression. any display that reverses this to make favorable values positive must label that transformation consistently.

this adds spatial estimation, regularization and validation work compared with a scalar-only model. it earns that cost by answering the already-promised spatial question. grid size, smoothing and visual resolution must follow supported evidence, not suggest precision absent from the source.

### separate valuing an opportunity from attributing opportunity rates

one scientific stage values an eligible attempt from its location and supported recorded context. another estimates how player presence and context relate to the rate and spatial distribution of those valued opportunities. attempts from the same location may have different values; an interpretable spatial model can use supported context. the initial 03a candidate uses pre-event score, omits outcome-revealing shot-type missingness, and defers preceding-event features pending evidence of need.

the chance value uses a declared reference for conversion skill so that the first component does not intentionally award finishing or goaltending value. merely omitting identities from a probability model does not prove that those influences have been removed. compare a transparent location-based probability baseline with an interpretable context-enriched candidate, checking calibration and sensitivity. any nuisance skill terms needed to establish the reference do not require publishing new skill components. do not import the entire reference model catalogue by default.

the event population is part of this contract: probability conditional on an unblocked attempt and probability for an attempt before its outcome are different quantities. the user has selected all-attempt analysis with blocked-origin imputation. an observed block has a realized goal outcome of zero, but its reconstructed reference opportunity can be positive; that opportunity value is not a factual forecast conditional on the observed block. its coordinate cannot silently stand for the shooting origin. apply the [shot-location evidence contract](issues/shot-location-evidence.md). unblocked rates remain a useful benchmark, but already reflect whether attempts survive blocking; later components need explicit accounting to avoid overlap.

retain counts/exposure as observations and reconstructed facts, separate from expected-goal values. increased shot volume and increased per-shot quality can both change expected-goal rate, but they are not automatically additive contributions. a later volume/quality decomposition needs a declared reference and interaction accounting; do not invent separate additive skills from their product.

### infer origins without inventing certainty

scientific recommendation: represent each blocked shot's origin as a normalized distribution over plausible spatial cells. the [xg 8 imputation appendix](https://hockeyviz.com/txt/xg8) supplies a geometric baseline; its constants and coordinate conventions are reference choices to examine, not automatically our parameters. retain the captured coordinate, interpreted block location, inferred origin distribution, and method/input identity as distinct information. missing or contradictory source evidence still needs explicit handling.

for fixed origin weights, average the downstream quantity over candidate origins. distribute the attempt's spatial contribution accordingly, conserving one attempt in total. scoring the mean coordinate is generally different from averaging the scoring probabilities; assigning the entire event to the most likely cell likewise discards uncertainty. normalized weights alone do not validate the imputer, and fractional allocations are not independent extra shots.

03a specifies a compact joint latent-origin candidate: a fixed geometric forward law for block location, a learned origin distribution, and two conditional outcome probabilities. infer blocked origins from their joint likelihood; do not train on guessed locations as if measured. compare plausible kernel/prior choices and their effects on values, then spatial player estimates. examine independently checked examples where available; synthetic geometry checks cannot establish accuracy on real blocked shots. unblocked shots are not automatically representative training labels for blocked origins. averaging fitted origin weights does not propagate uncertainty in the fitted model itself: use sensitivity analysis initially and specify any stronger uncertainty claim explicitly.

block information legitimately supports retrospective origin reconstruction. it must not silently become a post-outcome predictor in a model claimed to predict before the shot outcome. the chance-model specification must distinguish reconstruction evidence from the information its probability conditions on, and evaluate the complete pipeline under declared information boundaries.

### candidate fitting and reference conditions

the first candidate is a regularized spatial rate model over reconstructed exposure intervals, with season-specific player effects and history-informed shrinkage. a duration-weighted linear formulation is a tractable starting candidate, not an assumed winner. compare it with the scalar baseline and investigate a nonnegative rate formulation if predicted rates violate their meaning. signed player contrasts may be negative; complete expected opportunity rates may not. never repair an invalid model by silently clipping outputs.

account first for teammates and opponents, score/time and venue, and defensible deployment information. investigate team/system terms and shared deployment rather than claiming a long list of covariates isolates each person's contribution. specify centering, reference conditions and exposure weighting explicitly: a regression coefficient does not acquire a league-average interpretation merely by naming it an effect. evaluate prior strength, historical horizon, aging and entrant treatment with held-out evidence rather than copying another model's constants.

the data contract must retain score/time, skater and goalie presence, substitutions, event order, relevant faceoffs and source uncertainties needed to reconstruct those inputs. exposure intervals must support the covariates they describe; very short or same-timestamp events require explicit handling. the website's lack of date-range controls does not remove temporal detail from scientific inputs.

### evidence required before publication

- verify reconstruction against independent selected facts, including five-skater/goalie presence, clock boundaries, event membership, exposure and coordinate meaning. fixtures verify these contracts; they do not establish population validity.
- evaluate chance probabilities on held-out games/time periods against the transparent baseline, including calibration, proper probability scores and consequential subgroups. preprocessing, priors and tuning must respect each evaluation cutoff. retrospective final fits remain labeled as such.
- evaluate player and spatial results for held-out behavior, regularization sensitivity and shared-deployment ambiguity. examine entrants, traded players and sparse exposure. persistence is evidence to investigate, not an objective to maximize by forcing every season to repeat the previous one.
- reconcile game evidence to season results and spatial estimates to scalar summaries. compare rankings and magnitudes with honest baselines; agreement with a private reference product is not the acceptance criterion.
- quantify supported estimation uncertainty with the relevant dependence retained. aggregate uncertainty from a joint representation rather than summing cell interval endpoints or treating opposing rows of the same game as independent. identify uncertainty conditional on fitted chance values when upstream model uncertainty is not propagated. uncertainty from missing evidence or omitted mechanisms does not disappear because a coefficient interval is narrow.

the scientific specifications must set quantitative admission criteria before judging candidate results. no fit, benchmark or admitted full dataset exists yet. the current design therefore selects an estimand and candidate path, while leaving empirical decisions explicitly open. a user question is needed only if evidence forces a material change to the promised product; preference cannot settle whether an estimator or source reconstruction is valid.

### evaluation contract and decision timing

the final retrospective 2025–26 estimate may use the whole selected season and earlier evidence. candidate evaluation uses separate chronological development and assessment periods, keeping each game and its derived records together. fit learned preprocessing, imputation parameters, chance models, historical priors and tuning without assessment information. later-season evidence cannot silently enter an earlier-season estimate. held-out prediction tests useful persistence; it neither turns the product into a forecast nor establishes that an individual latent coefficient is true. the general leakage constraint is documented in [scikit-learn's evaluation guidance](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage); the game/time grouping is our scientific design judgment.

define one conversion reference across players and both directions, including the population, season weighting and context standardization. distinguish factual goal probabilities from chance values standardized to reference finishing and goaltending. [probability calibration](https://scikit-learn.org/stable/modules/calibration.html) concerns predicted probabilities versus observed outcomes. our consequence: test factual predictions on held-out goals, but do not require a standardized opportunity value to reproduce every shooter's individual conversion rate. in a nonlinear model, setting a skill coefficient to zero need not produce the league-average probability. write the actual reference operation in the scientific specification.

initial uncertainty claims must state what is held fixed. uncertainty conditional on the fitted chance model and imputed-origin weights may be useful when accompanied by separate imputation/model sensitivity results; it cannot be labeled total uncertainty. independently checked origin examples support accuracy claims; geometric plausibility and downstream stability alone do not. aggregate prediction can be good while individual attribution remains ambiguous, so shared-deployment and prior sensitivity are required alongside held-out scores. accepted coverage gaps require examining selective missingness, not just counting exclusions.

03a makes the reference operation concrete: average each training shooter–goalie pair's product of conditional probabilities under a fixed empirical joint distribution, then average over the event's origin distribution. its benchmarks separately assess unblocked conversion and outcome-blind all-attempt predictions. learned parameters and references remain fixed during evaluation. this limits initial mechanism detail and context; [03b](specs/03b-training-acceptance.md) must determine whether the simplification supports the intended use, without silently expanding 03a into a modeling platform.

freeze quantitative criteria after source audit and clearly separated development work, before confirmatory assessment. exact tolerances cannot be invented responsibly before learning the data's precision and failure modes. hard requirements include valid probabilities and complete rates, conserved imputation mass, supported event/exposure populations, coherent identities and reconciled outputs. empirical acceptance addresses calibration, baseline comparisons, instability and the scope of uncertainty. retain rejected candidates' diagnostics when useful; do not search new seeds or redefine thresholds until a favored fit passes. the cost is deliberate validation and sensitivity runs, not a new evaluation service or product surface.

## responsibility boundary

working engineering decision within the delegated architecture phase, informed by independent systems and statistical reviews on 2026-09-29: effect owns acquisition and application behavior; python owns scientific derivation from captured evidence through analytical outputs. this expands python beyond fitting alone, within the settled application/numerical split. it is not an additional user answer or a completed interface specification.

| owner | responsibility | boundary |
|---|---|---|
| effect | source discovery and retrieval, preserving response bodies and capture metadata, ordinary capture/publication commands | identified capture files; parsing needed for discovery must not become a second reconstruction implementation |
| python | source interpretation, reconciled hockey records, shift/on-ice reconstruction, coordinates, coverage, analysis-specific populations, features, models, diagnostics and analytical output assembly | runs directly as a local command over identified captures; saves useful fitted artifacts, run metadata and candidate outputs |
| effect | validate publication shape and completeness, activate a coherent revision, serve/query outputs, frontend interaction and presentation | consume the published contract; do not duplicate hockey calculations or query unpublished research state |

the scientific path is captures → interpreted hockey records → analysis-specific populations and estimates. these are functions and saved outputs where useful, not separate services or a generic job system. python owns the meanings and calculations; effect owns the application and publication. the operator runs analysis directly. application filtering and presentation may use declared published fields, but a new model, eligibility rule, or analytical quantity belongs to its scientific owner.

why this boundary: reconstruction already changes the evidence a model receives. [hockeyr's parser](https://github.com/danmorse314/hockeyR/blob/master/R/scrape_game.R), rechecked on this date, changes blocked-shot team attribution and constructs derived event fields before fitting-related work. the archived [coordinate normalization](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/packages/core/src/ingestion/reconstruction/coordinate-normalization.ts) infers direction from shot patterns before applying a rotation. these are substantive interpretations to test, not conventions accepted merely because another implementation uses them.

three distinctions belong in the scientific contracts:

- deterministic reconstruction is not necessarily direct observation. preserve the rule and evidence supporting event ordering, on-ice assignments, and normalized coordinates; inference remains attributable even inside the interpreted hockey records.
- shared hockey facts and analysis eligibility differ. source-listed players, dressed players, and inferred on-ice membership are distinct. preserve skater counts and goalie presence; each analysis applies its own declared population.
- source absence, parsing failure, missing fields, unresolved reconstruction, and analytical exclusions differ. missing shifts cannot become zero exposure. coverage needs the relevant denominator, not a single flag claiming a season is complete.

pr2b source decision: the user confirmed the official per-event on-ice report as an additional input. [fixture research](../fixtures/README.md#manually-corroborated-exposure-and-boundary-facts) falsified a universal shift-boundary rule. use reported event membership and separately reconstructed elapsed membership; expose disagreements and unavailable joins. [the specification](specs/02b-reconstruction.md) defines this contract; [the source audit](research/source-audit.md) records other public evidence and its next consumer. this adds one necessary source/parser, not a reconciliation platform.

material costs: python must have explicit data contracts, useful errors, and meaningful reconstruction tests as well as statistical checks. two environments still require input/output compatibility and provenance. a website feature needing new hockey facts requires extending published outputs. effect cannot provide static type guarantees inside the python process.

the alternative puts hockey canonicalization in effect and passes numerical tables to python. it gives the application direct typed access to canonical records, but places a language boundary inside scientific derivation. that becomes attractive if independently operated or editable canonical records are themselves a product. current requirements establish published analysis as the product. keep the source audit's useful cases and invariants; do not inherit its implementation to avoid this decision.

## capture, derivation, and correction contracts

working engineering decisions derived from the agreed fidelity, local operation, and game-level evidence requirements. no additional user preference is needed to decide these integrity rules. the exact file layouts and exchange schemas follow when storage and publication are specified.

### capture evidence before interpretation

effect preserves the response-body bytes delivered by the http client, after documented http content decompression and before character decoding, parsing, filtering, or serialization. raw therefore means application-payload evidence: json whitespace, missing fields, unexpected fields, and malformed content survive unchanged at that boundary. source errors remain in the capture.

the capture record identifies the source/request locator, retrieval time, response status, relevant response metadata, body representation, stored byte count and digest, and whether retrieval completed. keep response content type/encoding and relevant validators as source metadata, separately from the stored-body description. http error bodies can be complete captures without being usable hockey data; interrupted bodies are never admitted as complete inputs.

the [fetch standard](https://fetch.spec.whatwg.org/#http-network-fetch), checked on 2026-09-29, specifies content decoding before exposing response bytes and warns that the received content length may then be unreliable. our selected boundary preserves the material needed to reinterpret hockey payloads; it does not preserve the original compressed transfer or network framing. this avoids a lower-level network recorder, at the cost of not reproducing transport-level faults from the saved payload. verify the eventual client's decoding behavior in the ingestion slice. storage compression, if used, must losslessly restore the captured bytes.

capture completion, source parsing, hockey reconstruction, and analytical eligibility are separate facts. no success at one stage implies success at another.

### derive from a fixed input set

an analysis identifies its selected capture records and body digests, expected game/source scope and known gaps, interpretation revision, model/configuration, stochastic configuration where applicable, and relevant numerical environment. revisions identify recoverable implementations or artifacts, not merely descriptive labels. python reads that local selection. re-deriving it never implicitly fetches newer sources or substitutes fixtures when a required input is missing. numerical reproducibility is checked under a specified environment; identical results across arbitrary hardware or library versions are not assumed.

new retrieval is an explicit acquisition operation. a repeated retrieval has its own metadata even if its body is unchanged; storage may share identical bodies without merging retrieval history. a set of captures taken at different times is not represented as a simultaneous upstream snapshot. the cost is retaining evidence and small manifests, plus explicit selection when a revised analysis is wanted.

### preserve supported quantities and explain gaps

keep unaffected facts usable when another part of a game cannot be reconstructed. distinguish missing feeds, parsing failures, missing fields, uncertain reconstruction, and analysis exclusions. the scientific specification decides which inputs support each quantity, including any justified inference. there is no universal coverage percentage, automatic imputation rule, or whole-game exclusion policy.

in the game table, known source-listed/dressed status may be shown with unavailable exposure; roster membership alone does not prove participation. missing shifts are not zero minutes. every rate's numerator and denominator must jointly support its declared meaning. an unblocked-attempt rate can legitimately use all eligible 5v5 exposure, but missing coordinates or player assignments cannot silently become complete spatial or player-attribution evidence. withhold quantities whose support fails their contract; describe the valid remainder and its scope.

the cost is explicit unavailable cells and coverage information, with some analyses unavailable before the source problem is resolved. a convenient complete-looking table is not grounds for inventing observations. scientific admission rules and handling of potentially biased missingness remain empirical specification work.

### correct the responsible layer and publish coherently

an upstream correction creates a new capture. an interpretation defect is repaired in the python interpretation rule and produces a new derivation from identified captures. any evidence-backed local exception must identify the affected records, evidence, and rule; it cannot edit the preserved source or become an unattributed manual value. a generic correction editor is not required.

rebuild dependent outputs under the revised input/interpretation identity, including player models when their inputs change. begin with explicit reruns and reuse only demonstrably compatible completed work; a generalized dependency engine is not implied. python emits a complete candidate publication with its scientific validation and coverage report. effect checks the exchange contract and required artifact completeness before activating one coherent revision. old game summaries and newly fitted profiles cannot be combined under an unidentified revision.

failed work leaves the last valid publication available. retain the inputs and identities needed to explain the active and rollback publications under question 8's bounded policy. a known-invalid affected claim is withdrawn or explicitly marked invalid while repaired; an old valid result is not invalid merely because newer games exist. this costs storage and recomputation after corrections, while preserving intelligible rollback without an unbounded output archive.

## storage and publication

status: revised engineering selection on 2026-09-29 after the user's challenge and two independent reviews. use one completed, immutable sqlite database per publication. this supersedes the json-directory selection; it is an engineering judgment, not a database preference attributed to the user. explicit activation and one previous valid publication are settled. concrete schemas and runtime compatibility belong to the relevant specifications and verification.

| data role | representation | benefit and material cost |
|---|---|---|
| preserved evidence | body files with capture records and input manifests | preserves the capture boundary independently of analytical schemas; inventory and selection need an explicit strategy |
| scientific tables | parquet candidate, with duckdb for queries where useful | reusable columnar tables and direct analytical queries; adds a format/library boundary and requires deliberate schema handling |
| website publication | selected: one completed read-only sqlite database | shared records, relational constraints and selective queries in a portable file; requires a compatible reader, sql schema and queries |
| browser responses and small control records | json | direct application interchange; boundary validation remains necessary and does not define storage layout |

[duckdb's parquet documentation](https://duckdb.org/docs/current/data/parquet/overview) establishes direct queries, column selection, and filter pushdown. this makes it a candidate analytical reader without requiring a second persistent copy of every table. if a native duckdb file is used, its [in-process concurrency contract](https://duckdb.org/docs/current/connect/concurrency) requires coordinating writes within one process; no shared mutable scientific database between the website and producer is proposed.

the earlier json recommendation was reasonable for bounded, independently consumable documents. it supported direct file delivery and required no sql reader. its weakness here was treating a database mostly as an extra query dependency, while underweighting existing shared records: the same player-season estimates support league tables, profiles and comparisons, alongside related game evidence and map outputs. a relational publication can store each scalar estimate once and query it for several views, with keys and constraints expressing relationships. this is a present conceptual benefit, not a claim that ordinary sorting requires sql or that json is unsafe. long-term ranking and distribution tools strengthen the fit without being prerequisites for it.

[sqlite's application-file documentation](https://www.sqlite.org/aff_short.html) describes portable files, selective reads and declarative queries. its [appropriate-use guidance](https://www.sqlite.org/whentouse.html) supports application files and application-server use. our selection uses an embedded library, not a database daemon, shared mutable website database, or managed database service.

the initial read contract remains: compact league-wide table with sorting and name search; profile and map retrieval; selected-player comparisons; complete-season observed summaries and game rows with coverage. richer cohort filters and distribution charts are long-term goals. window/date-range summaries are excluded. effect queries published facts and estimates and returns application responses; numerical models, hockey reconstruction, eligibility, and analytical calculations stay in python. the browser's json response contract is distinct from the sqlite storage schema.

python builds a fresh candidate database with publication metadata, shared player-season results, game evidence and spatial outputs. use a small explicit schema with [strict tables](https://www.sqlite.org/stricttables.html), appropriate uniqueness/check constraints, and [foreign-key enforcement](https://www.sqlite.org/foreignkeys.html) explicitly enabled on writing connections. these catch structural defects; they do not prove correct exposure, model validity, finite numerical output, or game-to-season reconciliation. required scientific checks remain separate. retain explicit meanings for unavailable values; unexpected numerical failure cannot silently become missing evidence.

spatial outputs carry numerical values, coordinate frame, units, baseline, support/missingness and any uncertainty interpretation. sqlite can contain a validated map payload without requiring a relational row per grid cell. exact array encoding follows the scientific contract and measurements. the application renders values without refitting the surface. resolution and precision must preserve scientific meaning. json responses use finite numbers and exact identifiers within their declared contract; [rfc 8259](https://www.rfc-editor.org/rfc/rfc8259.html) describes the relevant numerical interoperability limits.

commit and finalize the candidate as a standalone file, then validate structure, required contents, schema compatibility and scientific results. use ordinary rollback-journal mode for this single-writer build unless measured evidence justifies otherwise; do not publish a live database while ignoring its journal. the [wal documentation](https://www.sqlite.org/wal.html) explains why copying a main file alone is insufficient when committed data remains in a write-ahead log. serving opens the finalized revision [read-only](https://www.sqlite.org/uri.html); production never mutates it.

publish only a completed, checked database. stop the server for replacement, keep the previous database, then restart and reload the page. read one publication for the server's lifetime and return a view's related data together: profile summary, maps and game rows, or the selected players in a comparison. display its publication identity. this avoids cross-request revision pinning, simultaneous serving of old revisions and a hot-switch protocol. a complete view response may transfer data before it is visible; measure actual payloads before adding separate loading paths. leave the existing database intact until the incoming copy is complete. interrupted replacement can be repaired manually from the intact files.

material costs: a sqlite reader in the serving runtime, an explicit versioned schema and sql queries, and finalization/compatibility checks. ordinary static-file-only hosting cannot directly execute these database reads; the selected node runtime must support a local packaged database. no public provider, latency or size claim has been established yet. newly built publications avoid an in-place production migration requirement; schema changes still require compatible producer/consumer releases and a usable rollback. no orm, generic storage interface, replication service or database platform is implied. the evidence archive and numerical workspace remain separate.

## runtime, frontend and process layout

status: engineering selection on 2026-09-29, informed by independent systems, frontend and python-environment reviews. these choices implement the settled requirements; they are not additional user preferences. source and package inspection establish feasibility, not a tested application. recheck release status and pin a compatible dependency set when the first relevant slice begins.

| responsibility | selection | material cost |
|---|---|---|
| application runtime | node 24 lts | a separate runtime from python; the selected sqlite integration has a native addon |
| application behavior | effect v3 stable, currently `3.22.2`, with compatible companion packages | independently versioned packages and possible later v4 migration |
| frontend | react with react router framework mode and vite; client rendered | framework conventions; no player-specific initial html |
| numerical environment | standard arm64 cpython 3.14, managed with uv | a second lock/environment; uv-managed interpreters depend on astral's python distribution |
| serving | one node process with read-only sqlite access and built frontend assets | requires a process-capable serving environment; no direct database queries from the browser |
| local operations | direct capture, python analysis and publication commands | a few manual commands and file boundaries; no application job runner |

### runtime and dependency judgment

the [node release schedule](https://nodejs.org/en/about/previous-releases), checked on the research date, lists `24.21.0` as the latest lts and node 26 as current. bun is viable, but its integrated tooling and performance do not solve an established problem here; expensive numerical work is in python. select node for its explicit support schedule and direct platform fit.

the [effect registry](https://registry.npmjs.org/-/package/effect/dist-tags) reports stable `3.22.2` and `4.0.0-rc.118`. v4 offers consolidated packages and the current official react atom integration. its [release-candidate announcement](https://effect.website/blog/releases/effect/40-rc) still permits narrow breaking changes. no settled requirement needs a v4-only feature, so prefer the stable line now. accept the possible migration cost explicitly; reconsider if v4 becomes stable before implementation. stable core does not make every pre-1.0 companion package stable by implication.

inspection of the published [v3 node sqlite adapter](https://registry.npmjs.org/@effect/sql-sqlite-node/0.53.0) found `better-sqlite3` with declared node 24 support. the inspected v4 adapter instead uses `node:sqlite`, whose [node 24 documentation](https://nodejs.org/dist/latest-v24.x/docs/api/sqlite.html) labels the api release candidate. both inspected node adapters attempt to enable wal by default, including with read-only access configured. the publication reader must therefore explicitly set `readonly: true` and `disableWAL: true`; verify this against the pinned version. the runtime's lts label alone does not establish the stability or configuration of every database api.

### frontend ownership and rendering

[react router framework mode](https://reactrouter.com/start/modes) provides typed route modules, loading/error conventions and code splitting through vite. those are current application responsibilities. use route loading as a thin boundary into effect operations; forward navigation cancellation and translate operation failures into the route's presentation. effect owns the published-data client, validation and application effects. react owns rendering and transient interaction. urls identify meaningful selections. maintain one owner for loaded results rather than duplicate them in router state, effect atoms and another query cache.

initial [spa mode](https://reactrouter.com/how-to/spa) fits the local read-oriented product. deep links require correct server fallback; player-specific initial html is a different requirement. spa mode still renders the root shell at build time, so browser-only dependencies need the framework's appropriate boundary. current v4 react atoms are not required to run stable effect operations from route loaders.

client rendering does not provide player-specific content in the initial html response. accept that limitation now. a public website does not by itself require changing rendering strategy; revisit it only for an actual search, sharing or delivery requirement. no server-rendering migration is planned.

next.js is a valid alternative; its server-component model adds concepts without a present requirement for their distinctive capabilities. a hand-built vite ssr layer is also unnecessary: vite describes its [ssr api](https://vite.dev/guide/ssr) as low-level infrastructure intended for framework authors. use the routing framework's rendering support when required rather than design our own framework.

### environments and module boundaries

use one typescript application project and one installable python analysis package. within the application, separate browser/routes, server/read queries, operator commands, and shared boundary schemas. these are cohesive modules, not separate deployable services or a package per concept. the browser must not import filesystem, database or process implementations. the operator and server may share publication validation/read contracts without sharing a running process. no monorepo task engine is needed for two explicit projects.

development uses the framework development server and the effect backend, with a development proxy for browser api calls. the built local website uses one node server for assets and api reads. python analysis runs independently from the terminal while the website can keep serving its existing file. publishing may restart the server. browsing never launches python.

python 3.14 is in [bugfix support](https://devguide.python.org/versions/). published arm64 wheel metadata for candidate [numpy](https://pypi.org/project/numpy/2.5.3/#files), [scipy](https://pypi.org/project/scipy/1.18.1/#files), [pyarrow](https://pypi.org/project/pyarrow/25.0.1/#files), [scikit-learn](https://pypi.org/project/scikit-learn/1.9.1/#files) and [statsmodels](https://pypi.org/project/statsmodels/0.15.0/#files) releases supports ordinary cpython 3.14; [polars](https://pypi.org/project/polars-runtime-32/1.44.2/#files) provides a compatible stable-abi distribution. this is ecosystem feasibility, not a tested combined environment or a dependency list to install. select numerical packages when the scientific computation warrants them. free-threaded python and acceleration frameworks have no demonstrated requirement yet.

use `pyproject.toml`, `uv.lock`, and an exact `.python-version` when implementing the package; keep its environment on the internal drive. prepare the environment explicitly with [locked synchronization](https://docs.astral.sh/uv/concepts/projects/sync/), then invoke its prepared entry point. an analytical run must not silently update dependencies. retain a node lockfile and runtime identity as well. record relevant numerical backend and thread settings with runs; a dependency lock does not guarantee bitwise numerical reproducibility.

verify the boundaries when implemented: a known sqlite result read without modifying the file, a python command on compact fixtures, a complete page including direct-route reload, and publication/restore of a sample database. check interrupted work where a selected expensive fit or file copy makes that consequential. no subprocess supervisor or exhaustive crash simulator is implied. no runtime compatibility tests have been executed in this architecture phase.

## operator flow and exchange contracts

use ordinary local commands with explicit inputs and outputs. they need not share a command framework. capture and publication use effect; run the python analysis entry point directly. a short task script can save typing if useful.

| action | result |
|---|---|
| capture | body files and a capture inventory identifying completed responses, unavailable sources and failures |
| analyze | python reads the selected captures and configuration; saves expensive fits, a run record, useful diagnostics and a candidate sqlite file |
| publish | inspect results, check the completed database, stop the website, copy it into place while retaining the previous database, restart and reload |
| restore | use the previous database; revert/rebuild code through git if necessary |

analysis follows ordinary program control flow. use named entry points when independent fitting or export is useful; no arbitrary stage-selection language, job receipts or effect subprocess runner. analysis never silently fetches new evidence or upgrades dependencies. capture and analysis can finish without publishing anything.

### useful saved work

keep a small run record with selected source identities, configuration, git revision, relevant environment, saved model/output identities and evaluation results. preserve fitted models and any derivation whose measured cost makes reuse worthwhile. explicitly select a saved fit when reusing it and check its recorded inputs against the intended analysis. cheap interpretation, aggregation, export and website builds can simply run again. no per-function completion manifests, automatic cache search or dependency engine.

use a fitter's supported checkpoint mechanism for expensive runs when it saves meaningful work. otherwise an interrupted fit restarts; completed earlier fits remain available. normal command errors and terminal interruption suffice initially. test interruption for the actual fitter or workers selected, rather than build a process supervisor before there is a workload.

incomplete writes are not usable fits or publications. useful completed captures and fits survive failed later work. report errors directly; an unexpected numerical failure cannot become an accepted coverage gap. a missing drive or input is an error, never a reason to substitute fixtures or silently create another data root. the operator repairs the cause and reruns the relevant command.

### publication and manual recovery

the sqlite file contains publication/schema/model identities, season and evidence cutoffs, reference conditions and units, player-season results, game evidence and coverage, and spatial outputs with their uncertainty meaning. unavailable quantities carry a reason. the website queries these data without recalculating hockey quantities or eligibility. a simple schema version check catches a mismatched reader; maintaining readers for historical schemas is unnecessary.

copy the completed candidate to a temporary destination before replacing the serving file. keep the previous database intact. the server can be stopped during replacement and restarted afterward; manual repair from either intact database is enough if interrupted. no transaction across application versions, database files and browser sessions is needed. one complete response per view and a page reload keep related results together.

restore the previous database directly. if the code no longer reads it, use git and the lockfiles to restore dependencies, rebuild and restart. these are operator steps, not an automated release manager. no old application builds or runtime archives.

material costs: manual command selection and publication, a browser reload, saved expensive artifacts and one previous database. the operator may rerun cheap work or rebuild the website. the benefit is a small, understandable set of commands and files rather than a second system for managing the first.

## empirical constraints

the [external dataset](issues/external-data-inventory.md) remains unavailable for inspection. [legacy raw-provenance](issues/legacy-raw-provenance.md) defects constrain reuse; the archived fixtures remain excluded. [two fresh games](../fixtures/README.md) now have verified capture integrity and checked source facts. those examples do not establish historical-corpus coverage, reconstruction validity or measured full-corpus performance.

the current execution environment denied the read-only cpu/memory query on 2026-09-29; the user subsequently supplied the inventory above. representative runtime, peak memory, numerical-library compatibility, and drive throughput remain unmeasured. resolve them during the relevant implementation slice before making performance claims.
