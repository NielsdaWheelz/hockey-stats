# v1-17 — microstat cards

full implementation handoff under the [application contract](experimental-application.md), [field crosswalk](../product-inventory.md#microstat-skater--s02-and-documented-fd-variants) and [quantity definitions](experimental-card-facts.md#microstat-quantities-and-populations). [the plan](../plan.md#next-full-spec-queue) owns assignment. specification only: no implementation, acquisition, fitting or activation is assigned here.

## outcome and boundary

deliver the complete grouped forward/defense microstat cards on skater profiles and the existing two-player comparison page. the user selected **profiles plus comparison** on 2026-11-08. retain comparative/value discovery as the default and observed results as a separate view. show the selected regular season, three-season field history and exact published values; neither forecast projections nor private tracking/model parity is claimed.

twenty slots per known position, twenty-nine distinct slots, thirty scalar keys. the current forward card has five constructible quantities, fourteen tracking gaps and one deferred skating slot containing two measurements. defense has six constructible quantities and fourteen tracking gaps. six is the union, not six available rows on each card. available values still depend on each player's support. the [s02 image](../research/visual-references/README.md) supplies the forward composition; the [public guide](https://hockeystats.com/about/microstat-player-cards) supplies the defense field list. defense arrangement below is our design, not an inspected private screenshot.

scope: one fixed card model/renderer, explicit microstat labels, profile/comparison navigation, selected-field evidence/history, faithful single-player png/card-data csv, and the bounded reference-xg metadata correction below. schema8 already carries all required quantities. no new statistical reducer, fit, rescore, raw preparation, source acquisition, tracking proxy, edge adapter/census, table preset, backend endpoint, schema version, dependency or chart framework. no goalie changes, new component total, extended card export, pair png, comparative-export redesign or activation.

accepted costs: most tracking cells remain unavailable; explicit per-field populations take space; comparison adds paired-layout checks; a correct metadata successor requires a new candidate build/read despite unchanged numbers. the compact png excludes the separate component strip and annual detail. whole-card closure still needs v1-12's real strip. weak reference-xg calibration and attribution remain visible experimental limitations, not a new scientific gate.

## responsibilities and files

| boundary / owner | files and responsibility |
|---|---|
| quantity/source content | existing `app/src/web/analysis-values.ts`, `analysis-cohorts.ts`, `analysis-history.tsx`: exact labels, populations, units, shared selection/ranks/history/evidence; no second metric registry or rank formula |
| card content and interaction | new `app/src/web/microstat-card.tsx`; `microstat-values.ts` only if preparation/export would otherwise obscure the renderer: fixed groups, typed view model, html/svg composition, reasons, strip and card downloads |
| application integration | existing `client.ts`, `explorer.ts`, `peer-distributions.tsx`, `routes/player.tsx`, `routes/compare.tsx`, `styles.css`, `export.ts`: coherent reads, navigation, bounded field picker, responsive composition and shared download plumbing |
| reference-xg provenance | existing `analysis/src/hockey_stats/execution_composition.py`, `analysis_publication.py` and `spatial_composition.py`: correct method meaning, attributed successor and exact inherited-family preservation; no new numerics |
| receipts | `fixtures/publication-v1-17/README.md` if new cases are necessary; `docs/research/application-v1-17/verification.md`; existing source issue and [metadata issue](../issues/microstat-reference-population.md) |

assign a card designer, a field/evidence designer and a history/export designer before implementation; these are responsibilities, not additional services. each defines good content in the acceptance table below. one integrator owns shared-file edits with v1-07, especially selectors, client composition, history/export and publication helpers. v1-07 numerical preparation/fitting can proceed independently. do not run competing large candidate builds/reads against the drive. preserve its drafts, source evidence, expensive fits and outputs.

reuse `FactValue`, `AnalysisDatum`, `AnalysisRow`, `buildAnalysisCohort`, `positionGroup`, `prepareHistoryPoint`, `DatumEvidence`, `csvText`, `downloadBlob` and `svgPng`. extract a small shared card-field preparation helper only where both the comparative strip and this card actually use it. retain existing selected-field views and other cards; remove duplicate microstat labels/formatting introduced by this work, not correct inactive features or historical research tools.

## exact composition

each key below means the existing `microstats.<key>` selector and `skater_microstats.<key>` value. lists fix display order; definitions remain in the factual appendix. skating is a single slot with two independently selected scalar rows.

| layout / group | ordered keys |
|---|---|
| forward · shooting, 6 | `goals_per60`, `reference_xg_per60`, `unblocked_attempts_per60`, `in_zone_attempts_per60`, `rush_attempts_per60`, `high_danger_pass_attempts_per60` |
| forward · passing, 6 | `primary_assists_per60`, `primary_pass_xg_per60`, `primary_shot_assists_per60`, `in_zone_shot_assists_per60`, `rush_shot_assists_per60`, `high_danger_passes_per60` |
| forward · transition, 4 | `zone_entries_per60`, `possession_entries_per60`, `zone_exits_per60`, `possession_exits_per60` |
| forward · other actions, 4 | skating (`skating_max_speed_mph`, `skating_bursts_over20_count`), `forecheck_involvements_per60`, `hits_per60`, `defensive_zone_touches_per60` |
| defense · shooting, 3 | `goals_per60`, `reference_xg_per60`, `unblocked_attempts_per60` |
| defense · passing, 4 | `primary_assists_per60`, `primary_pass_xg_per60`, `primary_shot_assists_per60`, `shot_assisting_passes_per60` |
| defense · transition, 6 | `zone_entries_per60`, `possession_entries_per60`, `zone_exits_per60`, `possession_exits_per60`, `pass_exits_per60`, `carry_exits_per60` |
| defense · defensive actions, 7 | `defensive_zone_retrievals_per60`, `successful_retrievals_per60`, `puck_management_xga_saved_per100_plays`, `entry_denial_fraction`, `possession_entry_denial_fraction`, `hits_per60`, `blocked_attempt_share` |

selected-year `Person.reported_position` selects F/D through `positionGroup`; do not infer position from usage or another season. for unknown position, render the ordered union, deduplicated by slot: shooting 6, passing 7, transition 6, other/actions 10. title it **position unavailable · all microstat fields**. this exceptional twenty-nine-slot layout avoids hiding supported blocking data or inventing a role. no new template picker/url parameter. absent selected-year identity remains explicitly absent; historical identity is labeled as historical and does not select the current layout or peers.

the card has identity/season/teams, four named groups, raw values/units, percentile standing when qualified, construction/support keys and a compact interpretation footer. no duplicated overall value or synthetic microstat score. every slot remains visible/selectable when unavailable.

### field meanings and content

the six existing producers retain their separate populations:

| quantity / authoritative owner | display and support contract |
|---|---|
| `goals_per60`, `primary_assists_per60` · existing personal reduction copied by `microstats.py` | recorded goals/primary assists per60 of matched personal-credit time; preserve exact older personal counts, rates and seconds |
| `unblocked_attempts_per60` · `microstats.py` | label **unblocked attempts**, never generic shots or shots on goal; goals+saves+misses, its own matched time, no coordinate requirement |
| `hits_per60` · `microstats.py` | recorded hitter events per60 of its own reconciled hit/membership support; more hits is not a better-player claim |
| `blocked_attempt_share` · `microstats.py` | label **blocking share**; personal credited blocks / opponent ordinary attempts while present. show percent once; time qualifies the cohort but is not the share's denominator |
| `reference_xg_per60` · execution valuation consumed by `microstats.py` | label **reference xg**; model-valued personal ordinary-attempt opportunities per60 of matched `neutral_all_attempt_value` time, including declared blocked-origin inference. virtual neutral execution, not isolated finishing, realized goals or the tracking provider's model |

all those populations are supported regular-season physical 5v5 with both goalies. keep their zero-event time, different exclusions and source/method evidence. do not recompute counts/rates from detail rows, rounded displays or another family's minutes. goals/a1 equality with existing observed selectors includes values, cohort members, n and ranks under identical viewing settings; semantic keys may differ because they are distinct published paths.

replace generic `title(key)`/“published source window” metadata for these thirty selectors with explicit human labels, construction, population and numeric reference in the existing catalogue. label primary shot assists as observed pass-to-attempt credits, reference expected assists as neutral-valued observed primary-pass opportunities, shot-assisting passes as primary/secondary/tertiary credits, and source puck management as source-modeled xga saved per100 eligible plays. these are not inferred setting, all passes, tracked control inferred from events, or our additive ledger. named per60 rates, fractions, mph, counts and per100-play values retain different units. unknown source protocol remains a source limitation, not a browser definition invented to admit data.

| supplied state | card treatment |
|---|---|
| available recorded/model-valued fact | raw value and unit; compact construction marker; qualified rank or its reason; original support retained |
| verified zero | display 0 and its legitimate standing; no missing style |
| partial support | retain valid value/rank; show partial/unknown coverage key and exact detail |
| unavailable tracking | neutral cell, **tracking unavailable**; name the missing observed action/window in detail. means no admitted observations here, not universal source impossibility |
| deferred skating | both values null; **skating deferred**; preserve **skating acquisition deferred; no admitted measurements** and source evidence. no fabricated composite or bottom rank |
| `not_computed` family or pending ledger | **pending computation** and responsible family; not a source-access claim |
| absent season, invalid/missing denominator or other field reason | retain that specific explanation. zero denominator is not a zero rate/share |
| raw value outside cohort | show value/marker, withhold percentile and state why |

these are presentations of existing result/reason contracts, not new wire enums. read field `reason_detail` and referenced sources/methods; never relabel every null from its key alone. there is no requirement to enable skating ranks or acquire tracking. copied source values remain attributable; source-modeled fields do not acquire our validation claim.

### layout, peers and detail

use the established paper/teal/slate system: identity first; shooting/passing above transition/actions; aligned raw-value and percentile columns. use a neutral sequential standing scale with explicit numbers, not good/bad red/green semantics. raw magnitude/unit remain readable beside standing. **12% blocking share** and **70th percentile** must not look like the same percentage. missing cells get text, no numeric fill or midpoint color. group titles alone cannot supply all per-field units.

the designer supplies complete, real-sparse, partial, absent-season, unknown-position and long-name examples before rendering. small screens stack whole groups in reading order; do not shrink the desktop card. comparison stacks cards when necessary, retaining player names/position on each. for mixed F/D, show each correct composition; never align unrelated quantities by slot index. the existing selected-field comparison compares the same quantity on a common raw-unit axis, even when it is not a compact slot on one player's layout.

reuse same-year F/D peers by default, explicit all-skater option and `peerMin=300` viewing cutoff. each microstat qualifies on its own positive matched seconds/denominator, not overall on-ice time. never create a card-wide eligible cohort. source/meaning compatibility, exact unrounded midpoint ties, empty/singleton groups and unknown position remain the shared cohort owner's rules. singleton standing 50 must show n=1; below-cutoff/unknown qualification keeps raw data but no rank. skating remains `census_unverified` if a raw fixture exists without a census; no census transport is added. display each ranked cell's n and support key; repeated identical support may share a key, not silently merge different populations. discovery filters do not change cohorts.

each slot links to the shared selected-field distribution, definition, numerator/denominator, exact seconds, excluded/unknown support, provenance, experimental limitations and three-season history. the skating slot has a link for each scalar. selected-field annual cohorts use each year's population/position; unavailable values and semantic changes break lines. no history from inferred setting/territory substitutes for missing tracking. population spread is not uncertainty. keep shared raw/percentile history controls and exports. reference-xg's same-season model valuation is not a held-out forecast; its producer limitations remain visible.

place a **modeled component context** strip immediately below the card, outside its png, before field detail. reuse exactly `ledger.five_on_five_offense.league_goals`, `ledger.five_on_five_defense.league_goals`, `ledger.power_play_offense.league_goals`, `ledger.penalty_kill_defense.league_goals`, `ledger.finishing.league_goals`, `ledger.penalties_combined.league_goals`. show raw common-workload league-relative goals, qualified standings, reference 1,000/100/100-minute workload and prior-only role flags through existing comparative selectors. drawing+taking is the published combined quantity. this six-term subset is not a total and is never summed into one. spatial per60 or execution per100 values cannot fill it. all six real fields remain pending until v1-12; renderer/fixture acceptance does not close that integration.

## interfaces and composition

add `view=microstats` to the existing profile/comparison view union. missing/invalid view retains existing canonicalization/defaults. links preserve season, players, peers and cutoffs. default selected microstat is `microstats.unblocked_attempts_per60`; retain an explicitly selected valid microstat or one of the six strip selectors, even if unavailable or absent from one position's compact layout. on entering this view, canonicalize unrelated selected metrics to that default; switching away follows the destination's existing policy. pass exactly those thirty microstat and six strip ids to the existing `PeerDistributions` field picker; do not offer choices the route immediately discards. no strength selector; these fields have fixed populations. keep comparative and observed loaders/renderers intact, including direct goalie behavior.

reuse:

```text
GET /api/players/:id?season=YYYYZZZZ
GET /api/league?season=YYYYZZZZ&kind=skater&family=microstats
GET /api/league?season=YYYYZZZZ&kind=skater&family=overview
GET /api/players/:id/evidence?season=YYYYZZZZ&family=microstats
```

player responses already carry the complete fixed microstat record and annual history; league microstats carries scalar peers. fetch the selected-year microstats cohort once whenever this card is visible, independently of the selected detail metric, and selected-year overview for component qualification. reuse the selected metric's required annual cohorts. three annual microstat reads supply a microstat history, with selected-year requests deduplicated; ledger detail instead needs annual overview cohorts plus the selected microstat cohort. paired cards share cohort requests; player detail/evidence is per player. do not add eager all-field histories, map requests, context reconstruction or a persistent cache. request the existing evidence body only when field detail needs it; family summaries already contain card data.

make `composeProfile`'s required-overview invariant view-specific: microstats requires selected-year overview, adding older overviews only for selected ledger history. comparative retains all annual overviews for its embedded histories; observed retains its current raw/ranked rules. absence of an unrequested overview is valid, not an excuse to weaken checks on requested data. loader construction and route revalidation must implement the same view/family/metric contract.

extend `ProfileView` with a typed selected microstats cohort or equivalent existing request-map access; do not flatten it into an untyped dictionary. add `checkMicrostats` alongside `checkDescriptive`: selected detail, annual selected history and corresponding cohort row must agree on person/kind/season, complete result body, support and availability. no cohort row for an absent-year person. require publication id/purpose, season evidence and compatible catalogs on all joined responses; reject mixed publications or contradictory methods. preserve cancellation, stale-navigation checks and current api 400/404 behavior. unknown field data is an unavailable datum, not a missing player response.

one typed `MicrostatCardModel` binds selected/historical identity, publication/season, layout, peer settings, ordered groups/slots, each scalar's existing `AnalysisRow`, its original fact/support, and six component rows. html, svg/png and csv consume this same click-time model. slot definitions contain only presentation order/group and existing metric ids; the shared catalogue owns labels/semantics. keep native values in datums and apply unit conversions through existing display helpers exactly once. renderer arithmetic is limited to standings, formatting and geometry, never statistical reconstruction.

## bounded reference-xg metadata correction

the current `_method` in `execution_composition.py` correctly identifies the personal-xg target but copies execution common-panel population, qualification and assessment wording into its `microstats` methods. `analysis-values.ts` exposes that wording. the values/support already use matched personal 5v5; changing only the card label would leave false evidence. [issue/evidence](../issues/microstat-reference-population.md).

correct those strings at the producer owner. add one narrow package operation, `correct_reference_xg_metadata(existing_results, output)`, using existing strict exchange readers/writers. it creates an attributed successor of an explicitly pinned combined exchange; it does not call ordinary execution composition, preparation or scoring. this operation is specific to this correction, not a generic migration framework or new CLI. a temporary controller may invoke it and is removed after verification.

only the three displayed-season `reference-xg-v1-06-<season>` method records may change: `population`, the incorrect qualification limitation, and their finding's `population`/`summary`; append the correction receipt to method/finding evidence. new meaning: credited ordinary physical 5v5 attempts on matched `neutral_all_attempt_value` elapsed support, both goalies present; qualifying time is that same personal population. retain block/setup inference and experimental/unknown-accuracy limitations. preserve method/recipe/reference/support-policy ids, target/reference, numerical input/design hashes, fit years/cutoff, existing evidence, assessment status/quantities and every value/support/family member. no numerical inputs changed, so record the donor/correction in evidence, not a fabricated new fit-input identity. the method's annual semantic tuple is unchanged; genuine recipe/reference/support-policy changes must still break history.

the small correction receipt binds donor manifest, affected method ids, exact changed text and checked no-numeric-change scope. hash it before constructing successor method rows; keep final artifact digests in a separate verification receipt to avoid circular hashes. donor remains immutable. stream/copy original family members through the existing writer; require every non-method table/member digest and nonowned catalog record unchanged. validation rejects unrelated edits, wrong donor lineage or already-divergent method meanings; idempotently recognize the exact corrected form, never silently normalize arbitrary prose.

`spatial_composition._accepted_source` currently compares inherited method rows exactly. amend only its reference-xg expectation to use the same producer-owned canonical correction, with bound receipt/unchanged numerical identities; preserve all other equality checks. an old frozen input remains historical evidence, not a second rendered interpretation. no general ignore-metadata comparison. a compatible v1-07 descendant must preserve this correction if it already exists; coordinate the one combined candidate's parent before writing.

build the inactive candidate with the existing `publish --observed FILE --results SUCCESSOR --out NEWDIR`; the ordinary publisher may read/reconstruct its three observed corpora. this is permitted publication assembly, not another raw preparation or numerical campaign. no direct sqlite updates, old database overwrite or renderer override of false source metadata. record the successor/candidate identities and incremental write/strict-read cost. original execution/spatial outputs and every unrelated quantity remain exact.

## exports and operating contract

one single-player png per card, including on comparison; no stitched pair. snapshot selected person/season/settings/values before asynchronous conversion. default png contains identity, all twenty F/D slots, source/construction/support keys and footer; unknown-position union is explicitly labeled. resolve every exported support key inside the image to its population, included minutes and coverage status; show blocking opportunities separately from qualifying minutes. detailed catalogs/reason arrays remain in page/csv. the component strip and selected-field history remain page detail with their own existing exports, not appended to this png. no hover-only essential meaning or remote image/font dependency.

use one svg composition with the same prepared rows/labels as the page and shared `svgPng`/download helpers. output width 1200px; known-position height ≤2000px, unknown-position ≤2600px; body text ≥20px, essential footer ≥18px. wrap long names/labels, retain visible values, and move audit detail to page/csv instead of shrinking text. footer: selected season; supported 5v5 facts plus model-valued reference xg; field-specific units/support; higher percentile means higher quantity; peer setting/cutoff; applicable source/deferred/absence dispositions; compact publication/method identity. derive those dispositions from actual fields and layout: D has no skating slot, and an absent season is not a source failure. fixture html/png says **synthetic fixture**. no blanket “all 5v5 per60”, war claim, provider branding or projection label.

card-data csv emits every scalar in the displayed layout plus the six strip rows: 27 rows for F, 26 for D, 36 for unknown position. skating emits two rows in its one slot; repeated shared fields emit once. identify strip rows separately; they are excluded from the png. prepend exactly `layout,section,slot_id` to `analysisCsvHeaders`, and prepend the matching three cells to `analysisCsvRow`. the existing columns already include `metric_id`, numerator, denominator and denominator kind; do not duplicate them. use native unrounded values/units, reasons, qualification/standing, support, source/method/reference and publication identity. no second evidence encoding or list of formatted strings. selected history/distribution csv/png remain their current owners. worksheet-safe strings and actual browser download behavior reuse `csvText`/`downloadBlob`.

fixture development needs no hdd. real acceptance uses the combined v1-08 exchange/candidate lineage pinned in [v1-07's inputs](v1-07-goalie-continuation.md#inputs-and-operating-contract), or a specifically checked compatible descendant preserving spatial and corrected execution identities. select the parent explicitly; never drop spatial by reverting to an execution-only exchange. the metadata successor and new candidate live under `/Volumes/Expansion/hockey-stats/runs/application-v1-17-<run>/`; no automatic local mirror. protect port 3000, live `app/dist`, active/previous databases, all sources/fits and unrelated worktrees. use an isolated worktree/build/listener. fixture and real purposes cannot mix.

the existing combined candidate is about 13.36gb; earlier strict-reader cost was 414 seconds for the smaller 11.31gb execution candidate. those are reference costs, not promises for this build. validate whole artifacts once at their responsible boundary; independent checks sample already verified evidence plus full relevant scalar equality, not repeated whole-corpus scans. record actual candidate bytes, build/read time/peak memory and representative API/render/export latency. no caching/format/performance campaign follows automatically.

## verification and completion

temporary end-to-end/live red→green→refactor→green checks establish the boundaries below. independent field/numerical-provenance, systems and content reviewers challenge the draft, integrated behavior and final refactor. review the actual figures/downloads, not only generated DOM. delete temporary tests/controllers and test-only dependencies after accepted checks; retain useful attributed fixtures, checked expectations, screenshots/download receipts and issue evidence. no new permanent harness. use existing pinned typecheck/build. retain semantic headings and ordinary keyboard controls; the user's prior exclusion of a separate voiceover/accessibility campaign remains.

| acceptance / designer's definition of good | required evidence |
|---|---|
| complete composition · card designer | exact F20/D20 counts, 29-slot union/30 keys; correct groups and raw/standing distinction. available zero, partial, source gap, deferred, pending and absent states remain legible. no missing-value rank/color. no guessed unknown role |
| field fidelity · quantity/evidence designer | reconcile all six constructible quantities across selected card/detail/api/export using exact published values/support. goals/a1 agree with observed selectors under identical settings. unblocked≠on-net, hit time≠personal time, blocker opportunities≠seconds, xg personal support≠common panel. wrong units/family substitution fails |
| metadata repair · producer reviewer | independently reproduce the wording defect; verify correction whitelist, donor/receipt binding, unchanged inputs/numbers/support/member digests and nonowned methods; future producer emits corrected metadata. unrelated changes refused; future spatial composition accepts only the attributed expected correction. python exchange and typescript publication-startup readers both pass |
| cohorts/history · history designer | exact cutoff/ties; zero/empty/singleton; eligible/outsider; partial support; unknown position with default/all peers; mixed F/D; per-field n; absent year and semantic breaks. every annual value uses its own identity/support. no census-backed skating claim, proxy tracking or borrowed-year role |
| integration · systems reviewer | both navigation paths, season/back/forward/cutoff changes, field/strip selection, unchanged comparative/observed/goalie behavior. one selected microstats cohort independent of detail field; exact request deduplication in comparison. changed-family revalidation, stale navigation, wrong publication/catalog/body and legitimate missing records checked |
| browser/exports · interaction/export designer | real profile→microstats→field detail/history→two-player comparison→season change→actual png/csv. same/mixed positions, long name, 375px and native 200% zoom, download during navigation, correct row counts and unrounded data. inspect saved images for readability/height/clipping; no screenshots passed off as downloaded exports |
| real integration · integrator | three published seasons, real F/D/traded/sparse examples and representative gaps. reconcile the complete available microstat scalar family to the preserved producer outputs; validate pending strip separately. bounded source receipts suffice; no repeated 6,560-game audit or fit. candidate/api/browser/download identities recorded |

record three independent completion states: **software accepted**, **available-field real integration accepted**, and **whole-card integration pending/accepted**. the first two can finish now; the third requires v1-12's six real component rows and their page/detail/history/export reconciliation. inaccessible tracking remains an evidenced limitation; user-deferred skating remains unfinished. neither is a fabricated number or a claim of complete private-data parity.

v1-08's real browser/layout/download checks were explicitly deferred, not passed. they do not satisfy this assignment's own checks. if browser access prevents an assigned check, preserve a concrete blocker/receipt and leave that acceptance pending; only the user may change it. no source/model verdict is rewritten and no running publication changes. final handoff lists touched owners, evidence, unresolved issues and v1-12/v1-20 integration obligations; implementation completion alone assigns no activation.
