# architecture and statistical design

status: interview in progress, authorized 2026-09-29. no architecture is approved by implication. the [product brief](brief.md) remains authoritative; its committed baseline is `279dff4`.

## method

resolve consequential dependencies one at a time. for each question, explain the observable difference, recommend an answer with its costs, and record the user's choice separately from engineering judgment. ask about purpose and operating constraints; investigate empirical matters and own routine technical decisions. new information may reopen a dependent decision, with the reason stated.

statistical meaning comes before model selection. required interactions and operating conditions come before service topology or storage. exact model formulas and quantitative admission rules belong in their scientific specifications; unknown data coverage cannot be settled by preference.

## decision order

| branch | depends on | required outcome | status |
|---|---|---|---|
| temporal meaning of ability | settled player-analysis purpose | distinguish season-level ability, ability at a cutoff, and next-season projections | settled: season-level ability |
| evidence and scientific scope | temporal target, public-data core | define usable observations, inferred inputs, context adjustment, spatial response, and credible validation | requires investigation; no preference question yet |
| user interaction | temporal target and distinction between observations and estimates | decide which selections query existing estimates and which require computation; clarify comparison and evidence access | settled: published analyses and game-level evidence; new fits separately |
| operating envelope | required interaction and operator control | local/detached-drive behavior, available hardware, batch resource use, and initial access needs | local operation and operator-triggered cadence settled; hardware reported; workload measurements deferred to implementation |
| source and correction ownership | evidence needs and operating envelope | capture fidelity, source identities, missingness, reconstruction, correction and replay contracts | working contracts below; endpoint-specific interpretation and admission rules require data evidence |
| application/numerical boundary | settled language split and data responsibilities | explicit inputs, outputs, errors, versions, and one owner per calculation | engineering ownership selected below; concrete exchange schema pending |
| storage and publication | access patterns and boundary | compare alternatives, choose coherent publication and rollback, identify reproducible inputs | pending |
| runtime and frontend | interactions, publication, operating envelope | choose effect version, framework and process layout with current evidence | pending |
| updates and failure behavior | selected responsibilities and runtime | operator commands, evidence cutoffs, partial input, retry, invalidation, and interrupted-work recovery | cadence settled; recovery and correction contracts pending |
| verification and slice handoff | completed contracts | meaningful scientific/engineering checks and first-slice acceptance; no implementation in this phase | pending |

the sequence identifies dependencies, not a requirement to ask ten questionnaires. a decision supported by confirmed requirements and evidence can be resolved by engineering judgment, with its tradeoff recorded.

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

failed work leaves the last valid publication available. retain the inputs and identities needed to explain earlier results. a known-invalid affected claim is withdrawn or explicitly marked invalid while repaired; an old valid result is not invalid merely because newer games exist. this costs storage and recomputation after corrections, while preserving intelligible rollback and comparisons between revisions.

## empirical constraints

the [external dataset](issues/external-data-inventory.md) remains unavailable for inspection. [legacy raw-provenance](issues/legacy-raw-provenance.md) and [fixture-fidelity](issues/legacy-fixture-fidelity.md) defects constrain reuse. these do not prevent designing explicit contracts, but they prevent claiming admitted data coverage, completed validation, or measured full-corpus performance.

the current execution environment denied the read-only cpu/memory query on 2026-09-29; the user subsequently supplied the inventory above. representative runtime, peak memory, numerical-library compatibility, and drive throughput remain unmeasured. resolve them during the relevant implementation slice before making performance claims.
