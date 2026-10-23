# v1-06 — execution scoring and reference

full implementation handoff; [the plan](../plan.md#current-boundary) owns assignment. extends [v1-05](v1-05-execution-base.md), [chance/execution](experimental-chance.md), [publication](experimental-application.md) and the [card crosswalk](../product-inventory.md#v1-field-crosswalk-and-card-acceptance). this document assigns no implementation, fitting or activation.

## outcome and boundary

turn checked annual execution states into actual event values, standardized skater skills/maps and reusable reference panels. deliver five numerical years (`20212022`–`20252026`) and one three-season publication exchange (`20232024`–`20252026`), with real values in existing discovery, profile/history, evidence and export paths. v1-07 needs all five years for continuation targets; v1-08 needs historical neutral quality. three displayed years do not justify discarding those inputs.

the user chose **recorded outcomes beside both reference-execution and actual-actor expectations**, on identical paired attempts. standardized finishing/setting/four-stage skills remain separate from actual type/danger evidence. no six-skill × type/danger expansion, new fit, ablation, scientific admission, calibrated interval, tracking/edge acquisition or headline ledger belongs here. v1-07 owns goalie summaries/continuation; v1-12 owns common-workload accounting; v1-17/18/19 own complete microstat/analytical/goalie compositions. negative scientific findings stay visible without suppressing correctly computed experimental values.

real completion needs verified v1-01 preparation, v1-02 coaches, all twenty v1-05 head states/four saved probes and v1-03 factual results. fixture development can proceed detached; real five-year scoring needs the external inputs. v1-03/05/16 may finish their existing contracts independently; this integration rebases on their checked owners. never modify the live build, active/previous databases, listener, original captures or expensive states.

## owners and non-overlapping work

| owner / files | responsibility |
|---|---|
| `analysis/src/hockey_stats/execution.py` | extend the single public evaluator with neutral references, panel projections and four-group allocation; reuse v1-05 designs, priors, tip rules and stable probability arithmetic |
| cohesive `execution_scores.py` | annual scoring/panel artifacts, strict reader, coverage and streaming; explicit factual-result composition. no runner or generic artifact-merging framework |
| `descriptive.py`, `microstats.py` | reuse v1-03's authoritative interval/source projection; add the two valued populations and `reference_xg_per60` at their existing reduction owners, consuming keyed scores |
| `analysis_publication.py`, `publication.py` | shared result writer, schema cutover, strict closure checks and existing native→display map transport; no coefficient interpretation |
| `analysis_cli.py` | thin `score`/`summarize` commands below; preserve `prepare/facts/fit/publish` |
| `app/src/shared/player-analysis.ts`, existing server readers | mirror the fixed payload changes and person-kind checks; retain existing endpoints and bounded selected reads |
| `app/src/web/{analysis-values,analysis-cohorts,client,export}.ts`, profile route | exact qualification/labels, existing discovery/history/png/csv, one small execution-evidence section; no model arithmetic or new dashboard |
| content/verification | `docs/research/execution-v1-06/verification.md`, useful attributed fixtures and checked expectations; actual source→score→publication→screen receipts |

first settle the interfaces; then numerical scoring, matched reductions and application/content can proceed independently against them. one integration owner edits shared serialization/types/cli and resolves versions. one designer owns execution meanings, one owns evidence/microstat/context content, and one owns history/export fidelity; these are review responsibilities, not new packages. each defines good content through the acceptance rows below before implementation. use native independent mathematical, systems/source and content review at each consequential boundary.

```text
hockey-stats-analysis score --family execution --prepared DIR --coaches FILE
  --state DIR --out NEWDIR
hockey-stats-analysis summarize --family execution --prepared DIR --facts DIR
  --scores FILE --out NEWDIR
hockey-stats-analysis publish --observed FILE --results DIR --out NEWDIR

execution.reference_goal_probability(state, predictors, origin_cells)
  -> ordered neutral joint goal probabilities, marginalized over pre-outcome setters
execution.score_execution(state, prepared_game, coaches) -> keyed event results/dispositions
execution.summarize_execution(state, panel, people, participation) -> fixed projections
execution_scores.read_execution_scores(path, expected_purpose) -> checked annual scores
execution_scores.compose_results(prepared, factual_results, annual_scores, output)
  -> one complete player_analysis_results exchange
descriptive.valued_evidence(prepared_game, factual_evidence_rows, keyed_scores, support_ids)
  -> two valued interval populations and coverage
microstats.reduce_reference_xg(valued_evidence) -> fixed v population reductions
```

`score` takes the season from its annual state. `--scores` is strict json `{schema_version:1,purpose,prepared_sha256,scores:[{season,path,sha256}]}`; real selection contains all five ordered years, with manifest digests and no duplicate/latest discovery. fixtures use an explicitly matching consecutive subset/display subset. reject unknown/repeated flags, wrong purpose/season/preparation/coaches/state identities, drift and occupied destinations. no command fits, captures or activates anything.

## one probability implementation

bind exact v1-05 input/design identities. start from its core/`u` opportunity population, then require the predictors and actor identities needed to evaluate all four heads (`full_probability_context`), independent of realized downstream `r/g` labels. `u` can be supported without a known goalie; that does not permit an invented goalie for joint scoring. retain every broader row's head eligibility and full-score exclusion. supported event-only attempts remain eligible without elapsed coverage. preserve a disposition for every recognized attempt. use point origins for supported unblocked coordinates and all 656 weighted origins for blocks, under the frozen imputer. neither block contacts nor imputed origins become observed release locations.

at each origin and pre-outcome setter branch, reuse `u,q,r,g` and the five terminals:

```text
block = 1-u; miss = u*(1-q); stopped = u*q*(1-r)
continuing = u*q*r*(1-g); goal = u*q*r*g
```

sum terminals to one before and after integration. all integrations use the same `w(origin)*pi(setter)` prior. no product of separately averaged stages, clipping invalid values, posterior weighting or silent neutral fallback. evaluate stable products/ratios before declaring a zero denominator. changing observed assist labels alone cannot change predictions or reference panels.

reference execution neutralizes all four residual groups: shooter, setter, goalie, and joint attacking/defending coaching. preserve centered circumstance offsets, exact strength, type, tip applicability and setup/no-setup mixture. `reference_goal_probability` returns the neutral product at each **requested origin**, not an event-averaged scalar. a later spatial producer supplies its own circumstances; it must not reimplement logits or use this event's observed outcome as a predictor.

save actual, fully neutral and actual-offense/neutral-goalie integrated prefixes `(u,uq,uqr,uqrg)`. the public `attempt_value` fields retain their exact meanings:

| field | value / applicability |
|---|---|
| `actor_all_attempt_opportunity` | actual `E[uqrg]`, every eligible ordinary attempt |
| `neutral_all_attempt_opportunity` | fully neutral `E[uqrg]`, same rows |
| `actor_unblocked_goal_probability` | actual `E[uqrg]/E[u]`, observed unblocked rows only |
| `actor_on_net_goal_probability` | actual `E[uqrg]/E[uq]`, observed on-net rows only |
| `neutral_goalie_on_net_goal_probability` | neutral-goalie `E[uqrg]/E[uq]`, same on-net rows |

other conditional cells are `not_applicable`, not zero. richer saved prefixes also supply v1-07's neutral-goalie unblocked value without overloading an actor-conditioned field. these fitted seasonal opportunities are neither held-out forecasts nor probabilities conditional on an observed block.

retain pre-outcome candidate identities/weights, including off-ice earlier participants, `none`, `unknown` and known goalies. optional retrospective responsibilities are computed only for applicable `g` likelihood rows under the v1-05 rule: known supported setter one-hot, otherwise normalize `pi*g` for a goal or `pi*(1-g)` for a continuing save. other rows have null posteriors. assists outside the candidate universe stay attributed discrepancies; do not enlarge the prior after seeing them.

## common panels, skills and support

one panel per annual exact physical state, drawn from the jointly scoreable opportunity rows above. preserve all 32 states internally with attacking/defending orientation and goalie presence; public skater projections use only the seven existing `ExecutionStrength` states with both goalies. each physical attempt has total weight one. retain source keys, type, tip/role/applicability tags, native origin cells/weights, pre-outcome setup mass and four neutral logits. exactly identical neutral setup branches may collapse to `none/setup`; no approximation, sampling or observed-actor selection.

every focal skater receives the same panel/context distribution. replace only that skater's centered shooter residuals for finishing/stages, or setter residual for setting; keep hand/role circumstances as panel contexts rather than constructing a new personal mix. tips retain zero shooter effect in every head. a supported entry/carry-prior coefficient remains evaluable. an absent required coefficient is unavailable with a located reason, never zero residual.

let `N` be physical attempts, `W=Σw*pi*I(setup)`, and `A,B,C,D` the unnormalized sums of `u,uq,uqr,uqrg`. under the frozen recipe `W=.8*N`.

```text
finishing = 100*(D_focal_shooter-D_neutral)/N
setting   = 100*(D_focal_setter_setup-D_neutral_setup)/W
stages    = (A/N, B/A, 1-C/B, D/C)
```

stage differences are focal-shooter minus neutral ratios, independently evaluated; they are not additive contributions. zero denominators yield unavailable values. deposit the same globally normalized finishing/setting differences into native origin cells, so map sums equal their scalar. never normalize each cell separately or multiply setting by `.8` a second time. use existing `K*T` native→display transport and 10 ft display blur; stored mass, density units and scalar closure remain distinct.

extend `skater_execution` with two small fixed records:

```text
reference_panel = {panel_id,opportunities,setup_weight,
  neutral:{u,uq,uqr,uqrg}, focal_shooter:{u,uq,uqr,uqrg},
  setting_setup:{neutral_goal_mass,focal_goal_mass:null|number}}
coefficient_support = {shooter:{u,q,r,g},setter:{g}}
coefficient entry = {available:boolean,likelihood_events:null|integer,
  prior_only:null|boolean,prior_seasons:[season],reason:null|string}
setter entry additionally = {candidate_events:null|integer,mean_coupled_events:null|integer}
```

prefix entries are unnormalized masses, not probabilities. each focal prefix is separately nullable: `u` needs shooter `u`, `uq` needs `u/q`, `uqr` needs `u/q/r`, `uqrg` needs all four. null propagates downstream only; available earlier stages survive. setting needs the setter `g` coefficient. require `0≤uqrg≤uqr≤uq≤u≤N` wherever available, `0≤setup goal mass≤W`, and neutral setup goal mass ≤ neutral `uqrg`. retain neutral panel metadata when focal coefficients are absent. an empty panel has zero masses and unavailable estimates/maps; absence of a supported actor is not an empty panel.

copy structural information/prior flags from the fitted state, but derive distinct likelihood-event sets through the existing execution-design rules. a structural support counter may include one flag for an entire mean-coupled population; it is NOT an event count. setter candidate/mean-coupled sets can overlap; `likelihood_events` is their union, never an observed-pass count. use null with an explicit reason if exact sets cannot be recovered. absent coefficients have null information, an explicit reason and no fabricated prior.

each estimate's existing `Support.events` counts distinct current physical likelihood-support keys for the contributing actor terms, across all strengths; never sum head counts. use null if the union cannot be recovered honestly. mixed-head `eligible_weight` stays null; mathematical denominators live in `reference_panel`. copy head-specific information into `coefficient_support`; source events and model opportunities cannot masquerade as the same denominator. `prior_only=true` only when every contributing focal term is prior-only; partial prior dependence remains visible. entry-prior-only support may have an empty `prior_seasons`; carried support names its actual years.

for execution selectors only, `Support.included_seconds` explicitly means **current-season exact-strength focal on-ice participation**, from supported v1-01 elapsed membership with both goalies. it qualifies the viewing cohort, not the fitted likelihood or common-panel denominator. include partial coverage/exclusion/gap evidence; never invent downstream-stage seconds or borrow another strength's minutes. event-only evidence and earlier off-ice setter candidates remain valid model inputs. coefficients are shared across strengths: zero pp minutes can mean extrapolation despite current 5v5 information, not necessarily prior-only. keep the existing 300-minute 5v5/50-minute exact-specialty viewing cutoffs, with this qualification basis in page/history/csv. unavailable qualification withholds rank, not an otherwise valid magnitude.

## actual-event accounting and evidence

evaluate all sixteen coalitions of `shooter,setter,goalie,coaching` at each origin/candidate. use exact four-group shapley weights `|S|!*(3-|S|)!/4!` on the same joint goal product; then integrate. retain aggregate coalition values and allocated shares, not a season×event×coalition×cell tensor. allocate each candidate's setter share with its pre-outcome weight. known goalies retain their actual person id but neutral setter residual/share; `none/unknown` also have zero setter deviation. do not relabel a known goalie unknown. both coach directions form one group; transport uses `group=coach,recipient_id=coaching_context`.

shares sum to actor minus fully neutral opportunity before and after integration. goalie event shares retain allowed-goal direction; later favorable-positive goalie stopping reverses its own contrast. source goal minus actual-model opportunity is a descriptive residual, not luck or isolated ability. none of these event shares is a ten-term ledger contribution.

hard-replace the ambiguous **skater** breakdown payload, retaining its existing `(season,player_id,strength,kind,stratum)` key:

```text
{events:integer, observed_goals:integer,
 reference:{expected_goals:number,mean_opportunity:estimate,
            observed_minus_expected_goals:estimate},
 actor:{expected_goals:number,mean_opportunity:estimate,
        observed_minus_expected_goals:estimate},
 support,method_id}
```

`reference` sums fully neutral all-attempt opportunities; `actor` sums actual-actor opportunities. composition pairs the public source-view keys with checked numerical values for the same supported personal ordinary attempts and corroborated physical shooter, including blocks. all fields use those **same** keys. `events` is physical rows, not origins; `observed_goals≤events`, each expected sum lies in `[0,events]`; mean is sum/events and residual is observed minus that sum. support seconds are null here: no elapsed requirement. zero paired rows have zero counts/sums/residuals and unavailable means (`no_exposure`), with source-only counts/reasons retained; this does not assert zero recorded activity. missing required model input yields explained unavailability, not verified empty evidence.

six shot-type rows partition the paired population. three danger rows independently partition it, using each event's fully neutral integrated on-net probability `E[uqrg]/E[uq]`: `<.05`, `[.05,.15)`, `>=.15`. classify each event once; never its origin branches or actor-conditioned risk. add `skater_execution.paired_evidence={source_attempts,paired_attempts,unvalued_source_attempts,danger_unavailable:{events,observed_goals,reference_expected_goals,actor_expected_goals}}` during composition. counts are integers; expected masses are nonnegative. require source=paired+unvalued, paired=type total, and type totals=danger totals+unbinned for counts/goals/each expectation. this exposes omitted values detached without browser probability reconstruction. known source shooter/strength defines the personal source count; unattributable source rows remain season evidence, not assigned to a player. do not add type and danger totals together. keep located exclusion reasons in evidence support.

dispatch the skater shape and the separately owned existing goalie breakdown shape by checked `person.kind`; no additional SQL axis or arbitrary metric names. v1-07 still owns its conditional goalie contract. keep all four standardized subskills at season/exact-strength grain; these type/danger tables do not claim stratum-specific isolated skills.

## matched values and publication

public source events use v1-03's fixed timed-view population; it and numerical eligibility differ, with no assumed containment. preserve every `attempt_fact` unchanged and supplement only matching `(season,game_id,source_index)` keys. fill scored exclusions with precise `not_applicable/missing_source` reasons, rather than leaving completed scoring labeled `not_computed`; preserve raw rows. reconcile intersection, source-only and numerical-only keys separately. preparation and original source indexes must match exactly; no id-only or nearest-time join.

reuse v1-03's interval bounds/membership and located exclusion mechanism; add only these matched populations. `summarize` consumes the already-serialized factual interval/source rows and prepared associations. narrowly extend `descriptive.py`'s projection owner for those inputs; its transient `ObservedGameReceipt` is not available here. do not reopen raw/native roots through provenance, rerun observed aggregation or copy a second reconstruction just to rebuild that receipt:

| population | counts/value and time |
|---|---|
| `neutral_all_attempt_value` | start from `recorded_all_attempts`; require each ordinary attempt's checked fully neutral opportunity and physical shooter/team membership. a required unusable attempt removes both sides' value/counts and time for its affected interval |
| `neutral_locatable_unblocked_value` | start from `recorded_locatable_unblocked`; require that population's unblocked opportunities; blocked scoring failure alone does not remove it. deposit the **unconditional neutral opportunity** at its recorded display cell, not actor or conditional-unblocked probability |
| microstat `v` / `reference_xg_per60` | same matched support as `neutral_all_attempt_value`; sum opportunities by corroborated physical shooter, `3600*sum/seconds` for that skater. this is model-valued observed opportunity, not standardized finishing or observed passes |

also intersect the saved prepared `ordinary_attempt_support` masks through verified native interval identities/bounds, never coincident integer indexes. a coalesced-run exclusion reaches every intersecting old interval; do not revive known conflicts through a narrower event join. own/awarded/unphysical recorded goals stay source evidence with explicit value exclusions, never zero-valued shots. unknown assignment uses all touching supported intervals; unknown clock widens to known period/game, following the existing owner. do not invent excluded seconds outside known time. retain valid zero-event intervals. maps exist only for locatable-unblocked value, with sums closing to that population, never to all-attempt value. fitted player maps remain the separate common-panel outputs. copy all existing observations, three recorded context populations, other microstats and source catalogs exactly; goals/a1 and old personal denominators do not change. unavailable tracking and deferred skating stay unchanged.

composition consumes one compatible factual exchange plus all annual scores, preserves unaffected families/catalogs and replaces execution, its keyed supplements, the one reference-xg field and the two valued context populations. resolve duplicate catalog identities only when identical; reject conflicting definitions or source/preparation bindings. the result writer still takes one complete directory, not arbitrary producer fragments. record method inputs for preparation, coaches, annual state, panel and source results, with recipe/reference/support-policy identities. no incomplete mixture of different scoring versions.

**hard cut to result exchange schema2 and publication schema8** for changed execution payloads. update strict python/effect validators, fixed assessment-field paths, readers, fixture producers and consumers together. old skater breakdowns are rejected, not translated. fix known-goalie setter validation and entry-prior-only support at the same shared owners. observed/factual definitions stay exact. regenerate cheap v1-03 factual exchanges under the current writer if required; do not add an old-format importer or refit expensive v1-05 states. preserve completed schema7 evidence and live schema6 files. completed protocols remain historical; this is their explicit prospective contract amendment.

## saved artifacts and cost

annual manifest required keys: `schema_version:1,kind:"execution-scores",purpose,season,scoring_version:"execution-v1-06-1",recipe,implementation,prepared,coaches,state,training_cutoff,panels,files,coverage,resources,numerical_resolution`. reuse v1-05's exact recipe/implementation/input-ref/resource records; refs bind locators/digests and selected member identities. `files` uniquely binds contained `{path,sha256,role}` members; role is one of the fixed rows below. `panels` enumerates all 32 exact states, panel ids and member paths/counts; `coverage` identifies the required coverage member. use strict finite json/jsonl and named finite numpy arrays, existing artifact helpers, fresh external output and manifest-last completion. reject wrong shapes/axes/duplicate keys/nonfinite or unbound members. provenance locators are not instructions for a reader to reopen originals.

| member / closed record | contract |
|---|---|
| `events.jsonl` / `event` | one `EventScore` for every recognized key, sorted `(season,game_id,source_index)`: key; nullable supported `shooter_id,goalie_id,attacking_coach_id,defending_coach_id`; nullable exact physical state, type/outcome; fixed per-head label eligibility; `status=complete|excluded`, located reasons; `prefixes={actor,neutral,neutral_goalie}` or null; `coalition_goal_mass[16]` or null. completed prefixes are finite integrated `(u,uq,uqr,uqrg)`; excluded rows retain facts/reasons and no invented complete arrays |
| `setters.jsonl`, `shares.jsonl` / `setter,share` | fixed keyed `attempt_setter` / `attempt_execution_share` shapes above; only completed event parents. retain branch priors and optional applicable posteriors. coalition bit order is shooter1, setter2, goalie4, coaching8; entries0/15 equal neutral/actor goal prefixes |
| panel rows/arrays / `panel_events,panel_arrays` | rows bind ordered complete event keys, type, tip, recorded role/hand and coach applicability. arrays: `event_offsets` int64 `N+1`; `origin_cells` int64 `L`; `origin_weights` float64 `L`; `neutral_upstream_logits` float64 `L×3`; `neutral_goal_logits` float64 `L×2` for none/setup; `setup_weights` float64 `N×2`. exactly one origin for a point, 656 for a block; source origin weights sum1, setup weights `.2/.8`. offsets start0/endL and partition rows; no object dtype |
| `people.jsonl`, `coach_ids.jsonl` / `person,coach` | selected-year prepared person identities/kinds and bound coach identities using existing fixed readers' records; retain source identity without requiring those sources at read time. all event/candidate/projection ids resolve; none/unknown/context are only declared sentinels |
| `projections.jsonl`, `maps.jsonl` / `projection,map` | each selected-year skater × seven public strengths, with the fixed skill/panel/coefficient-support records and method bindings; paired public evidence is added during composition. native finishing/setting arrays reference the same player/state/panel; their integrated values close to projections. absent actor or empty panel has explicit unavailable fields, not an omitted key |
| `coverage.json`, `resolution.json` / `coverage,resolution` | total recognized/included/excluded keys, head/strength/type/outcome dispositions, located reasons and unions; numerical status `not_applicable|passed|failed`, baseline/probe identities, frozen selected keys/pairs, comparisons and costs. final year needs passed propagation; earlier years are not applicable |

every panel member must resolve to an included full-joint event in that exact state, once; every included event enters exactly one panel. validate source/panel/person/strength relationships, setup/origin mass, prefix/coalition/share/map closure, unique members and no orphan projections. creation binds to actual inputs; detached readers validate saved internal relationships only. arrays/panels may split into contained members for streaming, with one explicit ordered membership list, never unnamed shards or alternate population semantics.

save keyed events/prefixes/coalitions, setter/share rows, per-key coverage, compact common-panel arrays, fixed person/strength projections/support/maps and diagnostics. panels bind exact state keys, physical-attempt membership/order, origin/setup law, types/tip tags and logits; keep enough context binding to re-evaluate the same rows for numerical probes. save all five years; no branch tensor dump. saved results/panels read detached from raw/prepared/fit roots; later publication composition explicitly opens its supplied preparation/factual results, never follows arbitrary evidence links. an incomplete command does not acquire a success manifest; an explicitly unavailable projection remains a located field result, not an output-directory failure.

measure one representative annual panel and focal projection before completing the campaign. record row/branch counts, selected actor counts, wall time, peak memory, bytes and justified extrapolation; exact scoring may be substantial despite requiring no fits. stream origin/candidate evaluation, player projections and map rows, with deterministic stable summation. no all-player×attempt×origin tensor or whole-publication materialization. exact duplicate neutral-branch compression is allowed; sampled panels, fewer origins/players/strengths or new tolerances are not performance repairs. expensive outputs stay external-only; no runner, retries, checkpoint engine or local fit mirror. measure actual three-season map/database size and build/read costs rather than treating fixture capacity as evidence.

## content, numerical resolution and acceptance

existing profile selected-field distribution/history receives one **recorded attempts and model expectations** section for execution selections, through the existing execution-evidence endpoint. two fixed tables show type and danger counts, recorded goals, both expected sums/means and residuals; expandable keyed source/model evidence retains omitted-value reasons. the endpoint also returns setter/share-recipient events: label those roles; do not equate their total with personal shooting strata. reuse current client identity/cancellation checks and csv machinery. full analytical-card/map composition remains v1-18; verify produced maps through existing typed map requests, not a second interface.

good content makes standardized versus realized mix, reference versus actual execution, fit versus held-out evidence, and prior/extrapolated support clear without an essay in each cell. show stage conditioning and percentage-point differences; inferred setting never becomes a shot assist. replace the existing “neutral execution forecast” label with reference-execution opportunity language. extend the existing finite `AnalysisDatum` projection with nullable fixed execution details: `reference_panel,coefficient_support,paired_evidence`. `analysis-values.ts` and `analysis-history.tsx` retain them into selected-field detail/history/csv, so partial priors, denominators and omitted evidence survive beyond the API. non-execution fields carry no fabricated execution details. history/cohorts use each year's exact recipe/reference/support policy; qualification metadata distinguishes actual participation from panel mass. finishing per100 must not fill the comparative **ledger-finishing** tile. existing selected-field png/csv retain raw magnitude, units, support, experimental construction and no invented interval. a small evidence csv exports the two stratum tables with distinct kind keys and the same provenance.

reuse the four saved final-year one-head tighter v1-05 variants; **no new solve**. bind the unchanged baseline membership/origin/setup weights, re-evaluating neutral logits/centers under each variant. before propagation freeze the union of these `(player,strength)` pairs: min/max finishing and setting per seven strengths (≤28); smallest positive current likelihood support for F/D × shooter/setter (≤4); first prior-only pair for those groups (≤4); min/max each four stage levels across pairs (≤8); largest tip-supported fraction (≤1). ties use fixed strength order then player id; unavailable categories are recorded. at most 45 pairs, every panel row for each pair; this is bounded coverage, not an all-player error bound.

also use v1-05's frozen real/synthetic event probes for integrated prefixes, terminal values and sixteen-coalition/share closure. require probability change `≤1e-5`, per100 scalar absolute change and native-map l1 change `≤1e-3` goals/100. report expected-sum movement on the probed keys and full-panel neutral totals with their exact populations; do not imply a seasonwide actor check or invent a fixed total-xg gate. keep baseline danger membership for paired numerical comparisons and separately count threshold crossings. explain failures and repair their responsible numerical owner; do not silently promote a probe under the baseline identity. real per-hour/basket propagation belongs to v1-08/12 once their rates/participation exist.

| acceptance boundary | independent evidence |
|---|---|
| arithmetic | hand cases for mixture versus product of means: equal weights, `u=q=(.9,.1),r=g=1` give joint goal `.41`, second-stage `Q=.82`, goal given unblocked `.82` and goal given on-net1. setup mass `.8`, conditional contrast `.1` gives setting10 per100, not8. tip-only shooter contrast zero |
| accounting/maps | sixteen-subset shares equal independent 24-permutation allocations and close per branch/event; native/map/display sums close to scalars; no posterior credit or per-cell normalization; recorded outcomes remain separate |
| source/support | all five inventories/dispositions reconcile; event-only and off-ice setter evidence retained; goalie/unknown candidates distinct; entry/carry/partial prior and zero-role exposure correct; no later outcome leaks into predictors/panels |
| payload/cutover | schema8/exchange2 strict roundtrip; wrong keys/identity/version, drift, unknown actors, malformed probability/prefix/map/share/support rejected; coherent fixture migration; valid zero, missing input, absent coefficient and empty panel distinguished |
| matched reductions | independent positive/zero-event interval examples, unknown assignment, unvalued block versus unblocked, scorer conflict, and dressed on/off/teammate intersections; time/counts move together; all old factual outputs exactly preserved |
| real delivery | five annual scores and three-year complete exchange/candidate from actual inputs; all applicable skater fields/maps/strata or legitimate located unavailable results; exact personal xg and valued context sums; actual costs and all numerical probes recorded |
| application | real execution discovery, selected profile/cohort/history, both-expectation evidence, valued context and reference-xg API; independent source keys/scalars/denominators match saved scores. saved png/csv, navigation/selection freshness, narrow/native200% layout on changed content; map API conservation/orientation |
| detached/preservation | candidate check/read/browser without source/fit mounts; database unchanged/no wal/shm; fixtures/real purposes distinct; serving files, source evidence and expensive states unchanged. no activation |

temporary end-to-end fixture/integration/live red→green→refactor→green checks precede real acceptance. include independent mathematical, systems/source and content review; fix demonstrated duplicate arithmetic at its owner, preserve inactive correct features, remove obsolete serialization branches. delete temporary tests/controllers/test-only dependencies after final green; retain useful fixtures, independent checked facts, scientific tools and receipts. no new permanent harness or unrelated historical rerun. failed science alone is not failed software; invalid probabilities, leakage, mismatched support or accounting remain blockers for the affected output.

accepted costs: exact full panels and five-year scoring; fixed imputed origins; virtual-neutral rather than empirical-actor reference; outcome-informed recorded geometry; shared-strength actor extrapolation; reduced matched exposure; point estimates and conditional priors; a cheap factual rebuild for the strict schema cutover; limited propagation probes rather than exhaustive numerical assurance. the four-layer inspiration is documented in [hockeyviz xg8](https://hockeyviz.com/txt/xg8); our panel/reference, setter prior, attribution and evidence definitions are independent. no private-model parity or admitted ability claim follows.
