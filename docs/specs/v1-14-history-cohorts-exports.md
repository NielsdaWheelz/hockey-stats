# v1-14 — shared history, cohorts and exports

prospective execution amendment: [v1-06](v1-06-execution-scoring.md#common-panels-skills-and-support) defines execution qualification seconds as current exact-strength participation, separate from shared-strength coefficient evidence and common-panel denominators. its schema8 integration carries fixed panel/coefficient/paired-evidence details through selectors/history/csv. this supersedes ambiguous execution “matching seconds” wording below, not other fields' matched exposure or the completed schema7 verification record.

full implementation handoff under [the application contract](experimental-application.md) and [five-card crosswalk](../product-inventory.md#v1-field-crosswalk-and-card-acceptance). [the plan](../plan.md#proposed-pr-boundaries-and-dependencies) owns assignment. settled cohort, reference and export choices suffice; no new product preference is required. writing this specification assigns no implementation or activation.

## outcome and boundary

the existing profile shows a selected published quantity, its peer distribution and three-season history, with faithful png/csv downloads. the existing skater comparison uses the same selected-field/cohort logic. later cards embed these mechanisms without independently calculating ranks, loading annual cohorts or implementing downloads.

reuse merged schema7: its finite overview, player history, family envelopes and source/method/support catalogs already supply the inputs. preserve existing observed cards, tables, maps, comparisons and values. this is browser composition, not a new numerical producer or publication format. no schema/server/api/operator change, new dependency, cache, generic chart framework or second dashboard.

all acceptance can run detached using [v1-13 fixtures](../../fixtures/publication-v1-13/README.md). captured observed facts remain attributed; analytical examples remain visibly synthetic. neither fixtures nor a shared plot complete any real experimental card. v1-15–19 retain their full compositions, analytical maps, specialist tables, expanded discovery/goalie comparison and individual export receipts. no acquisition, fit, full-season rebuild, model admission or change to the live build, databases or port 3000.

accepted costs: up to three annual family-cohort reads per profile, explicit qualification metadata, and missing ranks when evidence does not establish eligibility. these buy correct historical context and reusable presentation. scientific weakness does not suppress a valid experimental magnitude or otherwise-qualified rank. percentile is relative standing of the published quantity, not confidence in an ability difference.

## owners and boundaries

| owner | owned work |
|---|---|
| `app/src/web/analysis-values.ts` | finite typed field selectors, labels/units/reference, qualification and provenance; no dotted-path interpreter or runtime registry |
| existing `observed-comparison.ts`; small `analysis-cohorts.ts` where reuse warrants it | extract the midpoint-rank kernel; per-field cohorts and explicit unavailable standings; current observed wrappers call the same arithmetic |
| `client.ts` | existing typed effect client, annual reads, identity checks, cancellation and request-local reuse |
| `explorer.ts`, existing player/compare routes | finite url selections and peer controls; one selected-field section; preserve existing observed navigation |
| `peer-distributions.tsx`, cohesive `analysis-history.tsx` | empirical distributions, three-slot history/table, shared plotted view models; no probability fitting in the browser |
| new `export.ts`, existing `descriptive-card.tsx` | extract svg→png/download at its second consumer; csv serialization; renderers retain their own geometry/content |
| `fixtures/publication-v1-14/README.md`, `docs/research/application-v1-14/verification.md` | only additional small, attributed cases/checked expectations and delivery evidence; reuse v1-13 inputs |

implement selectors/cohorts, composition, rendering and exports as non-overlapping internal boundaries. a content designer reviews each boundary's labels, states and saved output; an independent domain reviewer checks population/rank meaning, and a systems reviewer checks composition and reuse. these are bounded reviews, not additional services or separately blocking research campaigns.

## finite scalar contract

use explicit accessors over the existing typed unions. resolve `provided`, `not_computed` and absent-season envelopes before selecting a field. reuse `Estimate`, `FactValue`, `Support`, `Person`, catalogs and observed primitives rather than define a second wire schema. the browser does not derive hockey rates, ledger totals, replacement values, reference probabilities or uncertainty.

each finite selector declares:

```text
metric_id; person_kind; api_family; api_strength;
label; unit; population; construction; numeric_reference; rank_direction;
value accessor; qualification accessor; support/provenance accessors;
semantic identity for annual comparison.

standing = ranked {percentile,n,peer_group,cutoff_minutes}
          | outside {reason,n,peer_group,cutoff_minutes}
          | unavailable {reason,n|null,peer_group|null,cutoff_minutes|null}
```

retain the five existing `metric` ids. other ids name fixed family/strength/field combinations, such as `execution.5v5.finishing_goals_per100_attempts`, `ledger.league_total`, `goalie.ev.stopping_goals_per100_on_net` and `microstats.unblocked_attempts_per60`. enumerate these from the table below; strings are identifiers, never executable paths. reuse `QuantityPath` when linking assessment findings, without ranking everything in that enum.

the selected datum carries its original value/status, exact annual person, support and resolved source/method references. preserve `unavailable_reason`/detail and whole-family explanations. scientific findings and unavailable uncertainty remain separate from value availability and viewing eligibility. a reference cohort never becomes the model's numerical baseline.

| selector set | exact value owner / qualification | default cutoff |
|---|---|---|
| existing `sog60,goals60,primaryAssists60,for60,against60` | existing five observed selectors; matching `personal.included_seconds` or `metrics.included_seconds` | general 300 min |
| ledger league/replacement total and ledger finishing in either reference | published `ValueLedger`; qualification from the same year's overview `observed.data.metrics.included_seconds`; carry all constituent specialty/prior-only limitations | general 300 min |
| other ledger components and combined penalties, both references | 5v5/pp/pk components → corresponding `SkaterSpatial.support`; setting → execution's setting support; drawing/taking/combined → shared modeled penalty support; ice won/lost → territory support. no invented ledger exposure | general 300; pp/pk 50 |
| spatial effect scalars | 5v5 offense/defense, pp offense, pk defense: published attempts/xg per60 effects and relative percentages; corresponding spatial support. neutral/complete values remain guides, not additional percentile skills. opposite specialty roles are inapplicable, not pending selectors | general 300; pp/pk 50 |
| execution, exact `ExecutionStrength` states | finishing, setting, four conditional probabilities and four published differences; `SkaterExecution.support[field]` | 5v5 300; each other exact state 50 |
| shootiness, exact `ExecutionStrength` states | probability and difference; `SkaterShootiness.support`; neutral probability is a guide | 5v5 300; each other exact state 50 |
| modeled penalties | drawn/taken rates and published value rates; `SkaterPenalties.support`; recorded all-strength bars do not inherit these cohorts | general 300 |
| territory | ice won/lost use territory support; four one-second subskill probabilities use each transition's support; published hazards remain raw explanatory values | general 300 |
| counterpart usage | teammate/opponent `usage_minutes_per_appearance`; respective `coverage.included_seconds` and known-weight coverage. never use slot-seconds as focal elapsed time | general 300 |
| microstats | all thirty scalar keys in `SkaterMicrostats` (twenty-nine distinct card fields, skating has two); each exact `FactValue`, support, population and denominator | own included minutes, general 300 for non-skating fields; positive mathematical denominator |
| goalie, ev/pk | stopping, six probabilities and their six published differences; `GoalieResult.support[field]` | ev 300; pk 50 |

`api_family=overview` supplies ledger, 5v5 execution/shootiness, spatial, penalties, territory, counterpart usage and goalie scalars. specialty execution/shootiness use their exact family/strength endpoint; `ExecutionStrength` is `5v5,5v4,5v3,4v3,4v5,3v5,3v4`, not aggregate `pp/pk`. no browser aggregation. microstats use `microstats`; existing five rates use `observed/5v5`. do not rebuild overview. descriptive raw counts, reported usage, source goalie totals, neutral forecasts, map cells and uncertainty bounds are not new ranked skills. later factual chart owners reuse the scalar/history/export mechanics with their already-defined guides, without inventing percentile contracts.

for microstat rates/fractions, use their own published window and seconds, never the player's broader season denominator. `FactValue` already validates positive mathematical denominators; no extra success-count threshold. skating has no elapsed cutoff: values remain raw-only with `census_unverified` until v1-04 supplies a checked source-cohort contract and its owning integration enables ranks. non-null league rows, an admitted source or prose coverage alone cannot establish that census. [source follow-up](../issues/microstat-inputs.md) owns this unfinished capability; it does not block other fields.

## cohort calculation

1. select the same publication, season, person kind, metric, strength, definition and numerical reference. partition available peers by the semantic key defined below; show the number excluded for incompatible meaning. use each player's supported value independently; no whole-card complete-case filter. discovery search/team/minimum filters select visible players, not this reference population. compared players with incompatible semantic keys retain separate raw values/references, but no joint plot or implied common rank comparison; show the mismatch rather than fail the whole page.
2. default skaters: `C/L/R/F → f`, `D → d`; null stays unknown. unknown position receives no same-position standing. explicit `peers=all` includes qualifying known skaters of unknown position. goalies use goalie kind, never the skater cohort. mixed F/D comparisons retain two named populations on one raw-unit scale.
3. minute qualification requires nonnull finite value, known positive matching seconds and `seconds >= 60*cutoff`. exact threshold is inclusive; zero successes/rates remain valid. partial support may qualify with gaps visible. a present event-trained estimate with null elapsed qualification stays visible but unranked. do not substitute reported usage, another family or prior seasons to manufacture minutes.
4. rank exact unrounded published values: `100*(count_less + count_equal/2)/n`. no rounded comparison, interpolation or weighting by minutes. outside the cohort → no number; empty → unavailable; singleton → 50 with `n=1`. distinguish unknown position, below cutoff, no exposure, qualification unavailable, quantity/family unavailable, absent season and unverified source census.
5. observed/microstat/conditional probabilities and rate percentiles increase with their named value, including attempts against, taking penalties and goalie conversion. favorable ledger contributions already have their accounting sign; never negate them again. no universal quality colors. model reference, replacement definition and fitted values do not change when peers/cutoffs change.

keep `peerMin` as the existing general/ev whole-minute control, default300; add `specialtyMin`, default50 for pp/pk. both are independent, nonnegative safe integers under the existing parser. show only the selected field's relevant control, with its actual population in the label; all settings survive navigation and have an explicit reset. a zero cutoff still requires positive mathematical support. skating shows its separate source-population explanation, not a minutes control. these remain viewing choices, not scientific thresholds.

headline qualification deliberately permits hypothetical specialty contributions. show their prior-only/zero-role-information flags in details and exports even when the headline qualifies. standalone per100 finishing uses its own execution support; only **ledger** finishing uses the general headline exception.

ledger has no aggregate `Support`: its `included_seconds`, `known_excluded_seconds`, `unquantified_gap` and `prior_only` metadata remain null, not a sum or boolean guess. carry `component_support` keyed by the relevant fixed ledger terms (ten for totals, two for combined penalties, one for a component), each containing its resolved sibling support or an explicit unknown reason. qualification seconds/basis remain separate. one prior-only specialty does not make the whole total prior-only; unknown constituent support must not disappear behind general 5v5 qualification.

## loading, urls and history

retain `/players/:id` and `/compare?a=&b=`. extend the existing `metric` selection with the finite ids above; strength is part of that id, with no second family/strength selection that can contradict it. add `history=raw|percentile`, default raw, for the profile detail. preserve `season`, `peers`, `peerMin`, `specialtyMin` and existing `map` meaning. unknown/duplicate/wrong-kind selections normalize using existing canonical-search rules. a valid unavailable field stays selected with its reason. default skater field remains `sog60`; goalie profile default is ev stopping. do not infer a skater from absent annual identity.

profile composition:

1. read the existing player response. its three history rows supply each year's person, family values and season evidence, including absence; use the response's declared displayed seasons, not an invented career range.
2. resolve the selected field to one api family/strength. load one league response per displayed year, sharing the selected-year observed request with the existing view when identical. deduplicate exact `(season,kind,family,strength)` requests within this loader, across selected fields using that response. no per-tile reads, persistent cache or polling.
3. all inputs share publication identity/purpose and displayed-season inventory. each annual cohort matches that year's history season/corpus, not the selected year's corpus. where the selected person exists, its scalar/support/identity must agree with its cohort row. resolve catalogs consistently; conflicting entries fail composition. old and new publication responses cannot be combined after an explicit server restart; show the ordinary reload/error path.
4. retain existing observed map loading separately. fetching history does not fetch analytical maps, evidence arrays, raw files or fits. cancellation follows the existing effect/client/router signal; never publish stale composed state after navigation.

comparison keeps its existing observed-skater picker and pair validity. add the same selected-field distribution/value table using the selected-season family cohort, plus its plotted-values csv. do not add three-year comparison downloads, goalie picking or a wider discovery system here. the cohort may include qualifying published skaters beyond this interim picker; never shrink it to picker members. profile links reach the history consumer. v1-15/19 own broader selection and complete comparison compositions.

change `shouldRevalidateView`: a metric change may require another family and cannot always be skipped as today. use one explicit descriptor-request comparison if needed; otherwise reloading the bounded requests on metric changes is acceptable. peer cutoffs, peer mode and history scale are local presentation changes. season/person changes reload normally; preserve direct links, browser back and pending-navigation semantics. no cache merely to save same-family requests.

history has one oldest→newest slot per published year. each point/table row retains raw value, standing/reason, annual position/teams, cohort/cutoff/n, support and source/method identity. absent person, unavailable value, unfinished family and unavailable rank differ; zero is a point. percentile mode uses that year's cohort. a position-group change is marked explicitly rather than assigned today's position.

semantic key: fixed metric/unit/population/construction/numerical reference plus the resolved method's `recipe_id,reference_id,support_policy_id`. source-backed values instead add the resolved source's `construction,population,definition` and the selector's fixed support-policy identity. compare these tuples exactly; differing source-definition prose conservatively breaks comparability. source ids/receipts and annual method/input/design hashes are provenance, not key members. no fuzzy label match or browser interpretation of prose. catalogs that reuse one id for conflicting contents are invalid responses, distinct from different legitimate definitions.

the five existing observed `PlayerSummary` fields have no per-row source reference: use their fixed metric/unit/population and publication `population_version` (on-ice) or `personal_population_version` (personal). retain season/corpus identity as provenance; method/source ids stay empty where unlinked. `Person.source` establishes identity, not metric evidence, and cannot fill that gap.

connect adjacent available points only when their semantic keys match. a missing year or changed meaning breaks the segment; mark the reason beside the table. differing annual cohort sizes are normal; differing peer groups get a reference-change marker and a break in percentile lines. raw values remain available after a break. no forecast, extrapolation, interpolated gaps or uncertainty/population bands.

## presentation and exports

extend the existing selected-metric detail, not a parallel analytical dashboard. a grouped native selector offers the finite fields appropriate to the person kind; pending fields stay identifiable. the panel contains magnitude/unit, construction/reference, empirical peer plot, qualification and evidence summary. the profile adds raw/percentile history and a values table with season links. keep existing observed history/game/context information; do not replace source coverage with model coverage.

use empirical dots/steps and selected-player markers, not a fitted density. paired groups share a raw-unit domain and distinct labels. domain calculation must admit signed effects, fractions and constant values: include every actual value/selected out-of-cohort marker, pad a constant domain in its own units, never clamp a negative estimate to zero. percentile axes are 0–100. tables provide keyboard-readable exact values; selection/color alone conveys neither missingness nor meaning. quantities retain native units in data; explicit display scaling (fraction→percent) is applied once to ticks/text and named in exports.

content acceptance per feature:

| feature | what good content means |
|---|---|
| field/distribution | exact quantity, raw magnitude, named numerical reference and annual peer population; higher means stated quantity; n/cutoff and outside-cohort reason visible |
| history | all annual slots and actual per-year context; selected season marked; no false continuity or confidence band; raw values remain accessible in percentile mode |
| missing/support | short specific state, useful magnitude retained where possible; expansion exposes gaps, inference/prior-only flags, method findings and unavailable uncertainty |
| saved output | useful without the webpage: identity, years, quantity/unit, strength/population/reference, cohort/cutoff/n, coverage, method/publication and recorded/experimental/fixture meaning |

deliver exactly three export consumers here: current single-player observed card png through the extracted converter; selected profile history png plus its values csv; selected comparison/distribution values csv. map pngs, whole analytical/comparative/microstat/goalie card pngs and specialist league-table csv remain their card owners' acceptance. the shared csv writer must accept a fixed header and ordered rows so those tables reuse it later.

use one captured view model per click, including selected settings and publication. html, history svg/png and csv use the same selected values/support/standing; navigation during image creation cannot relabel an earlier export. history png contains the plot, compact per-year value/standing/support rows and a readable footer; both raw and percentile modes preserve missingness and annual reference changes. retain the current 1200px export width, dynamic content height and local typography. svg strings are renderer-owned, not arbitrary templates. no remote assets, screenshot service, server export or new rendering library.

extract the existing svg→image→canvas→png path with explicit decode/blob failure and object-url cleanup; an error leaves browsing usable and permits retry. native `toBlob` supports png and can return null; preserve that ordinary failure contract. [browser reference](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toBlob)

csv: utf-8 `text/csv`, ordinary header, CRLF rows, quote/double embedded quotes as required; no comment preamble. numeric cells use unrounded finite values, missing numeric cells stay empty with reason columns. metadata text is quoted, not coerced to numbers; escape spreadsheet-formula prefixes in textual cells only, never negative numeric values, and document that presentation escaping. [format reference](https://www.rfc-editor.org/info/rfc4180/)

history csv is one row per player/year; distribution csv is one row per field/group/player, ordered as its accessible table, including a selected outsider once with `member=false`. always include: `publication_id,purpose,season,corpus_sha256,player_id,player_kind,display_name,position,metric_id,unit,population,construction,numeric_reference,value,display_value,display_unit,value_status,value_reason,percentile,standing_reason,peer_group,cutoff_minutes,cohort_n,incompatible_peer_count,member,included_seconds,qualification_seconds,qualification_basis,known_excluded_seconds,unquantified_gap,prior_only,component_support,method_ids,source_ids,reference_id,support_policy_id,workload,uncertainty_status,uncertainty`. quantity support and qualification support are distinct: ledger has no invented exposure; its qualification cites the declared sibling. observed `support_policy_id` names the applicable publication population version above. fixed structured metadata uses JSON text in quoted cells; preserve the complete supplied uncertainty object, including interval bounds/method/conditioning when present, without calculating intervals or plotting bands. absent uncertainty metadata for a factual count is not an invented interval. expose support reason counts and method limitations in additional fixed columns. export the named visible/plotted selection, not the hidden entire publication. include identity/metric and the selected season (distribution) or season range (history) in the filename.

## acceptance and implementation sequence

1. **contract/red:** use a disposable schema7 fixture publication and hand-calculated expected results. trace the selector table against actual types; independently check each qualification accessor before rendering. current five observed rates, membership and percentiles are the preservation controls. preserve fixture provenance; no production ratings from synthetic values.
2. **selector/cohort green:** implement finite adapters and one rank kernel; independently verify ties, rounding collisions, zeros/nulls, singleton/empty groups, exact cutoff/one second below, partial support, missing position, all-skater override, F/D comparison and goalie separation. one missing field must not remove a valid peer from another. check every specialty/ledger qualification, nullable execution seconds, composite support metadata, prior-only headline flags, incompatible peer definitions and raw-only skating.
3. **composition/history green:** temporary live requests verify three different annual cohorts with independently calculated percentiles, absent middle year, F→D change, stable semantic policy under changed annual method ids and genuine definition/reference change. mixed-publication/corpus/catalog inputs fail. count requests; verify cancellation/direct-link/back/season behavior and no raw/map reads for the new scalar history. compare both profile and comparison values with authoritative fixture rows.
4. **content/export green:** inspect actual browser and saved outputs for observed, signed experimental, goalie, mixed-position and unavailable cases. check raw/percentile plots and csv against the same rows, all exported metadata, long names/labels, constant domains, formula-like text, zero and missing values. exercise export failure/retry and navigation during rendering. native 200% zoom, 320px layout, keyboard labels/table/focus and detached browsing must work. each exported form gets its own receipt.
5. **refactor/review:** remove superseded duplicate rank/download/history composition, preserve existing five-rate observed behavior, then rerun affected boundary checks and pinned typecheck/build in the task worktree. independent domain, systems and rendered-content reviewers clear concrete findings. no unrelated schema/research migration or dependency upgrade.
6. **handoff:** delete temporary tests/controllers and test-only dependencies after final green; retain small attributed fixtures, checked expectations and receipts. record code/input identities, request counts/bytes, representative history render/export time, costs and limitations in the verification doc. update the plan with actual completion only. no full-season map-capacity claim, scientific admission, live rebuild or activation.

done means shared per-field cohort/history/export behavior works on published schema7 data and the bounded existing routes, with exact observed preservation and explicit analytical fixture evidence. complete card compositions and real producer-to-screen/export acceptance remain v1-15–20. source preparation, dated coaching and numerical work can continue independently; shared frontend owners coordinate route/cohort edits rather than create parallel implementations.
