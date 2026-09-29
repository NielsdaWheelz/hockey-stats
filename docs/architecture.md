# architecture and statistical design

status: architecture and statistical design in progress, authorized 2026-09-29. the [product brief](brief.md) remains authoritative. the interview began from brief commit `279dff4`; decisions through game-level evidence and source/correction contracts were committed in `1f35648`. publication requirements and representation are selected; scientific design is active. implementation remains unstarted.

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
| application/numerical boundary | settled language split and data responsibilities | explicit inputs, outputs, errors, versions, and one owner per calculation | engineering ownership selected below; concrete exchange schema pending |
| storage and publication | access patterns and boundary | compare alternatives, choose coherent publication and rollback, identify reproducible inputs | explicit publication, active plus one rollback settled; sqlite publication selected after review; runtime compatibility to verify |
| runtime and frontend | interactions, publication, operating envelope | choose effect version, framework and process layout with current evidence | pending |
| updates and failure behavior | selected responsibilities and runtime | operator commands, evidence cutoffs, partial input, retry, invalidation, and interrupted-work recovery | cadence and integrity/recovery principles settled; concrete command and failure contracts pending |
| verification and slice handoff | completed contracts | meaningful scientific/engineering checks and first-slice acceptance; no implementation in this phase | pending |

the sequence identifies dependencies, not a requirement to ask ten questionnaires. a decision supported by confirmed requirements and evidence can be resolved by engineering judgment, with its tradeoff recorded.

## remaining architecture work

the product interview has supplied enough direction to proceed without another preference questionnaire. finish these engineering/design tasks before handing off to slice specifications:

1. select the application runtime, effect version, frontend framework, python environment and module/process layout. verify compatibility with a local sqlite publication and explain dependency/stability tradeoffs. this is the next task.
2. make the operator flow and process/artifact boundaries concrete: acquisition, derivation/fitting, validation, explicit publication and rollback; input identities, completion, errors, cancellation, compatible reuse and missing-drive behavior. define publication schema compatibility and the data concepts needed by the agreed reads; detailed fields belong in their slice specifications.
3. finish the scientific evaluation plan: candidate chance/player models and imputer, reference conditions, uncertainty scope, chronological evaluation and criteria to specify before judging fits. distinguish choices justified now from parameters that need data and benchmarks.
4. review those contracts together and outline the dependency order for implementation slices. recommend faithful source capture and a bounded, independently checked offline fixture corpus as the first data foundation; specify that slice in detail only after the user advances the phase.

the disconnected hdd delays legacy-corpus admission and full-data measurements, not these architecture decisions. actual coverage, reconstruction accuracy, imputation quality, fitted-model validity and resource use remain empirical work during the relevant authorized slices. public deployment and additional card components remain later work. no need to settle every future slice or validate an unimplemented model to finish this phase.

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

- retain completed, validated outputs at meaningful expensive boundaries. reuse requires matching input identities, configuration, implementation, and relevant environment; an incomplete write is not a completed output.
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

## scientific design direction

working scientific judgments on 2026-09-29 within the confirmed brief, informed by primary-source review and independent statistical/product reviews. these establish the meaning to preserve, not a validated model or permission to begin implementation. [reference evidence and version limits](research/statistical-methods.md)

### the map and headline describe the same adjusted quantity

estimate a player's season-level association with creating or suppressing spatial scoring-opportunity rates at genuine 5v5, adjusted for supported context and stabilized by earlier evidence. express the first offensive and defensive magnitudes as changes from the declared league reference in expected goals per sixty minutes. these are model-dependent opportunity values, not goals scored, total player value, or proof of causal isolation.

the adjusted spatial surface is primary. the scalar offensive and defensive summaries come from that same fitted result. a scalar xg regression accompanied only by a map of observed shots would not explain where the adjusted player contribution appears. scalar regularized adjusted plus-minus remains a useful benchmark; descriptive maps remain separately labeled evidence.

for a discrete representation, let each cell contain its contribution to the adjusted rate, in expected goals per sixty minutes. sum the cells to obtain the corresponding offensive or defensive scalar. if the representation instead stores a density, integrate with the declared cell areas. smoothing, clipping and rendering cannot silently change the underlying total. the defensive field describes a change in chances allowed; negative is suppression. any display that reverses this to make favorable values positive must label that transformation consistently.

this adds spatial estimation, regularization and validation work compared with a scalar-only model. it earns that cost by answering the already-promised spatial question. grid size, smoothing and visual resolution must follow supported evidence, not suggest precision absent from the source.

### separate valuing an opportunity from attributing opportunity rates

one scientific stage values an eligible attempt from its location and supported recorded context. another estimates how player presence and context relate to the rate and spatial distribution of those valued opportunities. attempts from the same location may have different values; an interpretable spatial model need not ignore shot type or preceding events.

the chance value uses a declared reference for conversion skill so that the first component does not intentionally award finishing or goaltending value. merely omitting identities from a probability model does not prove that those influences have been removed. compare a transparent location-based probability baseline with an interpretable context-enriched candidate, checking calibration and sensitivity. any nuisance skill terms needed to establish the reference do not require publishing new skill components. do not import the entire reference model catalogue by default.

the event population is part of this contract: probability conditional on an unblocked attempt and probability for an attempt before its outcome are different quantities. the user has selected all-attempt analysis with blocked-origin imputation. an observed block cannot simply receive zero pre-outcome scoring probability, and its coordinate cannot silently stand for the shooting origin. apply the [shot-location evidence contract](issues/shot-location-evidence.md) to implement that scope. unblocked rates remain a useful benchmark, but already reflect whether attempts survive blocking; later components need explicit accounting to avoid overlap.

retain counts/exposure as observations and reconstructed facts, separate from expected-goal values. increased shot volume and increased per-shot quality can both change expected-goal rate, but they are not automatically additive contributions. a later volume/quality decomposition needs a declared reference and interaction accounting; do not invent separate additive skills from their product.

### infer origins without inventing certainty

scientific recommendation: represent each blocked shot's origin as a normalized distribution over plausible spatial cells. the [xg 8 imputation appendix](https://hockeyviz.com/txt/xg8) supplies a geometric baseline; its constants and coordinate conventions are reference choices to examine, not automatically our parameters. retain the captured coordinate, interpreted block location, inferred origin distribution, and method/input identity as distinct information. missing or contradictory source evidence still needs explicit handling.

for fixed origin weights, average the downstream quantity over candidate origins. distribute the attempt's spatial contribution accordingly, conserving one attempt in total. scoring the mean coordinate is generally different from averaging the scoring probabilities; assigning the entire event to the most likely cell likewise discards uncertainty. normalized weights alone do not validate the imputer, and fractional allocations are not independent extra shots.

begin with a compact geometric estimator rather than a separate model-serving system. compare plausible parameter choices and their effects on spatial maps and player estimates. examine independently checked examples where available; synthetic geometry checks cannot establish accuracy on real blocked shots. unblocked shots are not automatically representative training labels for blocked origins. fixed-weight averaging also does not propagate uncertainty in the imputer itself: use sensitivity analysis initially and specify any stronger uncertainty claim explicitly.

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

## responsibility boundary

working engineering decision within the delegated architecture phase, informed by independent systems and statistical reviews on 2026-09-29: effect owns acquisition and application behavior; python owns scientific derivation from captured evidence through analytical outputs. this expands python beyond fitting alone, within the settled application/numerical split. it is not an additional user answer or a completed interface specification.

| owner | responsibility | boundary |
|---|---|---|
| effect | source discovery and retrieval, preserving response bodies and capture metadata, operator commands and child-process lifecycle | identified captures and an explicit job input; parsing needed for discovery must not become a second reconstruction implementation |
| python | source interpretation, reconciled hockey records, shift/on-ice reconstruction, coordinates, coverage, analysis-specific populations, features, models, diagnostics and analytical output assembly | reads identified local captures without implicit network refresh; emits candidate outputs and an explicit completion/validation report |
| effect | validate publication shape and completeness, activate a coherent revision, serve/query outputs, frontend interaction and presentation | consume the published contract; do not duplicate hockey calculations or query unpublished research state |

the scientific path is captures → interpreted hockey records → analysis-specific populations and estimates. these are independently understandable stages, not a requirement for separate services, databases, or a universal schema. python owns the meanings and calculations; effect owns execution and publication. application filtering and presentation may use declared published fields, but a new model, eligibility rule, or analytical quantity belongs to its scientific owner.

why this boundary: reconstruction already changes the evidence a model receives. [hockeyr's parser](https://github.com/danmorse314/hockeyR/blob/master/R/scrape_game.R), rechecked on this date, changes blocked-shot team attribution and constructs derived event fields before fitting-related work. the archived [coordinate normalization](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/packages/core/src/ingestion/reconstruction/coordinate-normalization.ts) infers direction from shot patterns before applying a rotation. these are substantive interpretations to test, not conventions accepted merely because another implementation uses them.

three distinctions belong in the scientific contracts:

- deterministic reconstruction is not necessarily direct observation. preserve the rule and evidence supporting event ordering, on-ice assignments, and normalized coordinates; inference remains attributable even inside the interpreted hockey records.
- shared hockey facts and analysis eligibility differ. source-listed players, dressed players, and inferred on-ice membership are distinct. preserve skater counts and goalie presence; each analysis applies its own declared population.
- source absence, parsing failure, missing fields, unresolved reconstruction, and analytical exclusions differ. missing shifts cannot become zero exposure. coverage needs the relevant denominator, not a single flag claiming a season is complete.

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

explicit publication switches the active identity only after the candidate is complete and checked. a view resolves that identity once and pins subsequent requests to it; a database alone does not prevent requests from mixing revisions. never replace an active revision's contents in place. preserve one previous valid publication and compatible reading behavior for rollback; an expired in-flight revision produces an explicit refresh path. local activation atomically replaces the small active reference after finalization; verify filesystem behavior in the implementation. public deployment must preserve the same complete-activation contract.

material costs: a sqlite reader in the serving runtime, an explicit versioned schema and sql queries, and finalization/compatibility checks. ordinary static-file-only hosting cannot directly execute these database reads; the chosen serving runtime must support a local packaged database. no runtime, provider, latency or size claim has been established yet. newly built publications avoid an in-place production migration requirement; schema changes still require compatible producer/consumer releases and a usable rollback. no orm, generic storage interface, replication service or database platform is implied. the evidence archive and numerical workspace remain separate.

## empirical constraints

the [external dataset](issues/external-data-inventory.md) remains unavailable for inspection. [legacy raw-provenance](issues/legacy-raw-provenance.md) and [fixture-fidelity](issues/legacy-fixture-fidelity.md) defects constrain reuse. these do not prevent designing explicit contracts, but they prevent claiming admitted data coverage, completed validation, or measured full-corpus performance.

the current execution environment denied the read-only cpu/memory query on 2026-09-29; the user subsequently supplied the inventory above. representative runtime, peak memory, numerical-library compatibility, and drive throughput remain unmeasured. resolve them during the relevant implementation slice before making performance claims.
