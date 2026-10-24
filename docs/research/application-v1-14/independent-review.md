# v1-14 independent review

reviewer: independent read-only adversarial reviewer. no production edits. findings cite the working tree as of the stated pass; line numbers drift as files change. severity: **block** = wrong rank/value/identity/export meaning; **major** = spec requirement missing or misleading content; **minor** = cosmetic or low-consequence.

status legend: open / repaired (verified) / withdrawn.

## pass 1 — 16:40, analysis-values.ts, analysis-cohorts.ts, observed-comparison.ts

fixture facts used below (live fixture api, publication a8fd30c0): every season's skater overview has 84 rows; every analytical family has exactly ONE provided row per season (82–84 `not_computed`); 12 skaters have observed `not_computed`; one goalie in 2023/2024, none in 2025. so most analytical cohorts are n≤1 and the v1-13 inputs alone cannot exercise ties, f/d splits, cutoffs or incompatible definitions on modeled fields. those need the small v1-14 cases.

### R1 (block, repaired — verified 17:20) — a selected player with no value gets the wrong cohort and every valid peer counts as "incompatible meaning"

`analysis-cohorts.ts:49,53` partitions candidates by the SELECTED datum's `semanticKey`. a datum built by `fromResult` on a `not_computed`/`absent` envelope (`analysis-values.ts:103`) has no method, no source and no `supportPolicyId`, so its key differs from every provided peer's key. result: `members` = other not-computed players (all fail qualification) → empty plot, standing `unavailable` with `n=0`, and `incompatiblePeerCount` = every provided peer.

repro (fixture): profile of any captured skater in 20232024 (e.g. a row with observed provided, ledger `not_computed`), `metric=ledger.league_total`. expected: the distribution shows the one provided ledger peer (if qualified), selected player shown as "family not computed", incompatible count 0. actual: empty cohort, incompatible count 1.

same for observed rates of the 12 observed-`not_computed` skaters: their key lacks the `personal`/`onIce` policy id (`analysis-values.ts:304-314` only adds it when `selected.supportPolicyId` is set, which only happens inside the provided branch), so the 72-player observed cohort is reported as 72 incompatible peers.

fix at the responsible layer: the semantic key is a property of the selector + resolved method/source of the FIELD, not of the selected player's availability. either (a) build the cohort key from the qualifying peers (group peers by key, rank the selected player only within its own key when it has a value, and when it has no value show the dominant/only compatible cohort with the selected player's status), or (b) make `fromResult` carry the family method id where the envelope has none — it cannot, since `not_computed` has no data. (a) is the honest one. `incompatible_peer_count` must count only provided peers whose key differs from the key actually plotted.

### R2 (major, repaired — verified 17:20) — observed support is fabricated into a `Support` record

`analysis-values.ts:131-134` builds a synthetic `Support` for the five observed rates: `reason_counts: []` (discards the published `reason_codes`), `unquantified_gap: coverage_status !== "complete"` (an invented boolean; `PlayerSummary` publishes `coverage_status` and `known_excluded_seconds`, not a gap flag), `current_season_information: included_seconds > 0` (invented), `events: null`, `inferred_inputs: []`. this record then flows into csv `unquantified_gap`/`prior_only`/support columns as if published. root already reported the reason-count part; the gap and current-season booleans are the same defect.

fix: keep observed support as its own typed shape (`observedSupport`, already carried) and export its real fields (`coverage_status`, `reason_codes`, `known_excluded_seconds`); leave non-published `Support` columns empty, not guessed. spec: "the five existing observed `PlayerSummary` fields have no per-row source reference … retain season/corpus identity as provenance; method/source ids stay empty where unlinked."

### R3 (major, repaired — verified 17:20) — microstat population is an invented label; denominator hidden under `workload`

`analysis-values.ts:203` sets `population: \`published ${field} window\`` for all thirty microstat selectors. the fixture's resolved `Source` rows carry the real `population`/`definition` (e.g. `fixture_tracking`, `fixture_skating`, `fixture_puck_management`; `reference_xg_per60`/`primary_pass_xg_per60` resolve to `method:execution`, whose `population` lives on the `Method`). the csv `population` column and the panel will show the invented string, not the published population. spec selector row: "each exact `FactValue`, support, population and denominator".

`analysis-values.ts:208` puts `{numerator, denominator, denominator_kind}` into `workload`. `workload` in the csv header is not defined by the spec for microstats (closest meaning elsewhere is the ledger `reference_minutes` / pp-pk common-workload `state_weights`); the microstat denominator (opponent attempts, tracked plays, included seconds) is a distinct fact and should be its own fixed columns (spec permits "additional fixed columns"). e.g. fixture `blocked_attempt_share`: value 0.25 = 1/4 opponent attempts with `support.included_seconds=600`; the export must make "4 opponent attempts" legible and must not label it workload.

native units verified correct against schema: per60, `fraction` (blocked share, both denial fractions), `xga_saved_per100_plays` (signed, `puck_management`), `mph`, `count`. qualification uses `fact.support.included_seconds` (own window) — correct; for per60 facts the schema forces it to equal the denominator.

### R4 (minor, repaired — verified 17:20) — counterpart usage hard-codes `construction: "reconstructed"`

`analysis-values.ts:186`. the value is source-backed through `SkaterContext.provenance`; the resolved source carries its own `construction`. the key includes both, so comparability is fine, but the displayed/exported `construction` column states a fixed label that can contradict the source. use the resolved source's construction (as microstats already do via `fact.construction`).

### pass-1 repair status (16:55, per root)

R1 repair in progress (keep actual valid peer partitions, no invented dominant definition) — acceptable direction; I will verify that `incompatible_peer_count` then counts only provided peers whose key differs from the plotted partition. R2 repair in progress (observed `support:null` + exact `observedSupport`) — acceptable. R3 repair in progress (population/reference resolve from method/source; denominator gets fixed columns) — acceptable. R4 open.

### checked, no finding

- probability units: `definition()` scales `fraction` by 100 once; ids ending `difference` display "percentage points", others "%". covers execution (4 diffs × 7 states), shootiness `difference`, goalie (6 diffs × ev/pk), territory one-second probabilities, microstat fractions. spatial `*_relative_percent` keeps unit `%` with scale 1 (already percent); spatial effects are per60 differences, not fractions. correct.
- selector inventory: 5 observed + 24 ledger + 16 spatial (5v5 off/def, pp off, pk def × 4) + 70 execution + 14 shootiness + 4 penalties + 6 territory + 2 counterpart + 30 microstats + 26 goalie = 197; matches the spec table. neutral/complete spatial values and shootiness neutral probability are not selectors. opposite specialty roles absent.
- ledger: total `support: null`; `componentSupport` has ten/two/one terms; total and ledger finishing qualify on `overview.observed.metrics.included_seconds` (general); pp/pk components use spatial pp/pk support with the specialty cutoff; setting uses 5v5 execution setting support; penalties share penalty support; ice terms territory support. matches spec.
- execution/goalie qualification reads the per-field `support[field].included_seconds`; shootiness/penalties/spatial read the family support. matches spec.
- rank kernel `midpointPercentile` = `100*(less+equal/2)/n` on unrounded values; inclusive cutoff (`seconds < cutoff*60` is below); zero cutoff still requires `seconds > 0`; skating returns `census_unverified`. observed wrappers now call the same kernel; under `PlayerSummary` invariants (positive seconds ⇒ all rates in that population non-null) the old complete-case member filter is equivalent to per-field filtering, so observed membership is preserved.

## pass 2 — 17:00, client.ts, routes/player.tsx, routes/compare.tsx, peer-distributions.tsx, analysis-history.tsx, export.ts

### R5 (major, repaired — verified final) — absent season and null-position years report "unknown position", and fake a reference-group change

`analysis-cohorts.ts:38,79`: with the default `peers=position`, a datum whose `person` is null (absent season) gets `position=null`, and `standing()` returns `unavailable/"unknown position"` BEFORE `qualificationReason` can say `absent season`. the group is then named "unknown position", so `analysis-history.tsx` marks "annual reference group changed" next to the absent year and the history csv/png carry `standing_reason="unknown position"`, `peer_group="unknown position"`.

repro (fixture): `/players/8473507?season=20232024` (20242025 is `absent`). history row 2024–25: expected `absent season`, no peer group; actual `unknown position`, plus a reference-change marker on 2024–25 and again on 2025–26 versus that row. with `peers=all` the same year correctly says `absent season`, so the reason depends on an unrelated control.

fix: in `standing()` evaluate absence / value unavailability before position; only a present person with a value and null position is "unknown position". an absent year's peer group should be null, and reference-change markers should compare only adjacent years that both have a peer group.

### R6 (major, repaired — verified final) — display scaling prints binary float noise

`analysis-history.tsx:61` (`String(displayValue)`), table cells and png rows; `peer-distributions.tsx:299,373,436-437`; `analysis-history.tsx:413-414,508` (axis endpoints, including padded constant domains). `displayValue = value*100` for fractions: `0.07→"7.000000000000001 %"`, `0.29→"28.999999999999996 %"`, `0.57→"56.99999999999999 %"`. fixture values (0.1, 0.2, 0.4) happen to be clean, so fixture screenshots will not show it; real probabilities will. the spec wants the exact native value retained (it is, in the native-unit column and `value`) and the display scaling "applied once to ticks/text": display text needs a fixed display precision (the existing observed card uses explicit precision via `Quantity`/`formatPercentile`). csv `display_value` may stay unrounded if documented, but on-screen and png text must not show float artifacts.

### R7 (major, repaired — verified final) — the minute control is labelled with the quantity population, not the qualification population

`peer-distributions.tsx:94-97` labels the input `minimum peer included minutes · {metric.population}`. qualification seconds come from `qualificationBasis`, which is often a different population: ledger total/finishing qualify on overview observed ON-ICE 5v5 `metrics.included_seconds`, but the label reads "published standardized workload basket"; ledger pp offense qualifies on pp spatial support; context usage on `coverage.included_seconds`; per-field execution/goalie support. spec: "show only the selected field's relevant control, with its actual population in the label". the label must name the qualification basis (e.g. "on-ice 5v5 included minutes (ledger headline)", "5v4 execution finishing support minutes", "pp spatial support minutes"), and should say general vs specialty.

### R8 (minor, repaired — verified final) — two peer controls on the profile

`routes/player.tsx`: the existing `DescriptiveCard` still renders `<PeerControls settings onChange>` (general control, "personal and on-ice 5v5, separately") and the new selected-field section renders a second `PeerControls` bound to the same url keys. for a specialty field the page simultaneously shows a general minute input and a specialty minute input, each with its own "reset peers" that resets all three settings. either keep one control (the selected-field one) or make the card's control visibly scoped to the observed card.

### R9 (minor, repaired — verified final) — percentile text bypasses the existing formatter

`analysis-history.tsx:64` uses `toFixed(1)`; the observed card uses `formatPercentile` (`<0.1`, `>99.9`). midpoint ranks are strictly inside (0,100) but `toFixed(1)` prints `0.0`/`100.0` once n>1000. reuse `formatPercentile` so the same standing reads the same in card and detail.

### R10 (minor, repaired — verified final) — method findings lose their population

`analysis-history.tsx:137,601`: findings are matched by `QuantityPath`, which has no strength (e.g. `skater_execution.finishing_goals_per100_attempts` covers 5v5 and every specialty state). only `finding.summary` is shown, so a finding scoped to one population appears under every strength's selector. show `finding.population` with the summary (and in the csv `method_findings`, which already carries the whole object — fine).

### R11 (minor, repaired — verified final) — composition compares whole datums, including envelope prose

`client.ts:278` `equal(selected, peer)` compares the complete `AnalysisDatum`, so a difference in a `not_computed` explanation string between the player-family envelope and the overview envelope fails the whole profile. spec requires scalar/support/identity agreement, not explanation equality. today's fixture copies explanations identically (checked 2023 and 2025 for 8473507), and the `PlayerFamilies.spatial/execution/shootiness` path synthesises `pending("strength is not computed")` when a strength row is missing while overview would carry the server's text. low likelihood; note only. narrowing the comparison to value/status/original/support/qualification/method/source would match the contract.

### R12 (minor, repaired — verified final, residual closed) — f→d change is unmarked when `peers=all`

`analysis-history.tsx` only marks `annual reference group changed` when `peer_group` differs. with `peers=all` every year is "all skaters", so a reported-position change (spec: "a position-group change is marked explicitly rather than assigned today's position") is visible only as the per-row position text. mark adjacent `positionGroup` changes independently of peer mode.

### checked, no finding (pass 2)

- loader: one player read, then `{observed/5v5 for selected year} ∪ {selected field × each displayed year}` deduplicated by `(season,kind,family,strength)`; root receipt shows 5 calls for ledger, 5 for sog60 (3 shared observed + map). no evidence/raw/analytical-map reads. catalogs merged with conflict failure; per-year `sameRelease` against the history row's own `SeasonEvidence` (annual corpus, not selected corpus); identity equality with the cohort row; an available scalar without a cohort row fails. cancellation still flows through `Effect.runPromise(..., {signal})`.
- `shouldRevalidateView` now treats `peers,peerMin,specialtyMin,history` as presentation; `metric` changes reload the bounded requests (spec-acceptable).
- comparison: selected-season scalar cohort only, reuses the observed response when the field is observed, never shrinks the cohort to picker members, checks identity of both picked players against the field cohort, two named groups for f/d on one raw scale, joint plot suppressed when keys differ.
- export.ts: svg→image→canvas→png with decode failure, zero-size check, `toBlob` null rejection and object-url revocation; descriptive card now calls it (second consumer). csv: header row, CRLF, every text cell quoted with doubled quotes, numbers unquoted and unrounded, negative numbers untouched, formula prefixes (`= + - @`, leading tab/cr) escaped with an apostrophe only in text cells and documented in the ui and png footer. required 39 header columns present in spec order; extras appended.
- png snapshot: `view` and filename captured at click; a busy guard prevents overlapping renders; failure leaves browsing usable and permits retry.
- history plot: 0–100 axis in percentile mode, raw domain admits negative and pads constants in display units, no lines across unavailable values, changed semantic keys or changed peer groups.

## pass 3 — 17:20, verification of R1–R5

user steering recorded: no dedicated accessibility/voiceover/keyboard acceptance. none of R1–R12 depends on it; ordinary controls, responsive readability and saved outputs remain in scope.

independent check: `var/v1-14/review-checks.mts` (run `app/node_modules/.bin/tsx var/v1-14/review-checks.mts`, read-only against :41924). the implementers' `app/tmp-v1-14/selectors.ts` also runs green on the current tree.

- R1 verified: `analysis-cohorts.ts:51-63` — a selected datum with no value and no resolved method/source/observed policy gets its own empty selected group (`n=null`, incompatible 0) plus one partition per actual valid meaning among peers; partitions count only provided peers of other meanings. observed rates now always carry the population policy in the key (`analysis-values.ts` `metric.observedPopulation`), so the 12 observed-`not_computed` skaters see the 72-player cohort with 0 incompatible (selector check asserts it).
- R2 verified: observed `support:null`, exact `observedSupport`; csv `included_seconds`/`known_excluded_seconds` fall back to the published observed values; `unquantified_gap`/`prior_only` stay empty for observed; panel shows `coverage_status`.
- R3 verified: datum `population` resolves `source.population ?? method.population ?? fixed label`; `numericReference` shows `method.reference`; the semantic key still uses the selector's fixed population/reference plus recipe/reference/policy ids (spec key, no method prose). microstat `numerator/denominator/denominator_kind` are their own csv columns and panel text; microstats no longer write `workload`.
- R4 verified: construction resolves `selected → source → fixed`, so context takes the source's construction.
- annual identity: profile 9000001 `ledger.league_total` 2023 (`method:ledger`) and 2024 (`method:ledger:20242025`) produce the same key (same recipe/reference/policy) → line connects; 2025 `not_computed` breaks with "value unavailable". the selector check also covers a changed `reference_id` (key changes) and a changed source definition (key changes) vs changed receipts (key stable).
- R5 still open in part. absent precedence fixed (`standing()` now returns `absent season` first). but the absent year still carries `peerGroup: "unknown position"` and `n: 0` under `peers=position`. actual output for `/players/8473507` sog60, 2024–25: `{kind:"unavailable", reason:"absent season", n:0, peerGroup:"unknown position", cutoffMinutes:300}`. `analysis-history.tsx:594,749` therefore still print "annual reference group changed" on 2024–25 and on 2025–26, and the png/csv carry `peer_group="unknown position"`. expected: absent → `peer_group` null, `n` null, no reference-change marker; compare markers only between adjacent years that both have a peer group. same path: when the selected season itself is absent and `peers=position`, the distribution shows an empty "unknown position" lane instead of the field's partitions (with `peers=all` it shows them) — absent should take the R1 partition path regardless of peer mode.
- fixture limitation worth stating in verification: with six captured games no observed skater reaches 300 included minutes (8473507 has 1,007 s in 2023–24), so default observed cohorts are empty (`n=0`, everyone below cutoff). observed rank arithmetic is only exercised at small cutoffs (the selector check sweeps 0/1/300 and `all`/`position`); acceptance receipts should say so rather than imply ranked defaults.

### R13 (minor, repaired — verified final) — pending fields are not identifiable in the field selector

`peer-distributions.tsx:248-261` lists all 192 skater / 26 goalie options with plain labels. spec: "a grouped native selector offers the finite fields appropriate to the person kind; pending fields stay identifiable." the publication already says which are pending: `publication.families` (fixture: 2024–25 has execution/shootiness/spatial/penalties/territory/goalie/microstats/descriptive `not_computed`, ledger provided; 2025–26 everything analytical `not_computed`). today a user on 2025–26 picks any analytical option and only learns after a full reload that it is "not computed". mark options (label suffix or optgroup note) from `publication.families` for the selected season, mapping counterpart usage to `descriptive` and observed to always-available. no new request needed.

### R14 (minor, repaired — verified final) — goalie profiles still read the skater observed cohort

`client.ts` `loadProfile` always adds `observedRequest` (`kind=skater,family=observed,strength=5v5`, ~330 kb) even when `detail.kind==="goalie"`; nothing on the goalie page consumes it (no observed card, no map). the goalie composition receipt counts 4 league calls per goalie profile, one of which is this. pre-existing behaviour, but v1-14 now owns the profile loader; skip it for goalies. not blocking.

### content/verification notes (not code defects)

- the v1-13 exchange never provides a goalie `ev`/`pk` value: goalie overview `ev`/`pk` are `not_computed` for the only goalie (9000004) in 2023–24 and 2024–25, and `goalie_result` provides no aggregate rows. so "goalie" content acceptance with an actual magnitude/percentile can only come from runtime mutation; the verification doc should say that explicitly instead of counting the goalie path as exercised by fixture data.
- every analytical family has one provided skater per season, so modeled-field ranks in the fixture are singleton (`50`, `n=1`) at best; ties, f/d splits and cutoffs on modeled fields are exercised only by the selector check's synthetic datums. state this in the verification doc.

## final — closure status

verdict: **no open block or major finding.** domain (population/rank/qualification), systems (loading/identity/reuse) and saved-output content checks pass on the current tree. remaining items are minor and do not gate v1-14. accessibility/voiceover/keyboard audit excluded by user steering. i did not view rendered pages or saved png images; root owns native-browser rendered review. everything below is code reading plus executed checks.

### executed evidence

- `app/node_modules/.bin/tsx var/v1-14/review-checks.mts` and `var/v1-14/review-checks-2.mts` (mine, read-only against :41924) — green:
  - observed `sog60` and `against60`, profile 8473507, 2023–24 and 2025–26, `peers=position` and `all`, `peerMin=0`: app percentile and `n` equal independent `100*(less+equal/2)/n` over raw wire rows (e.g. sog60 position 2023–24 = 43.75 of 24 d; all = 29.861 of 72; against60 position 2025–26 = 18.75). at the default 300 min every fixture skater is below cutoff (8473507: 1,007 s), `outside/below cutoff`, `n=0`.
  - absent 2024–25 → `unavailable/absent season`, `peer_group` null, `n` null, `cutoff` null; no reference-change marker.
  - ledger total 2023 (`method:ledger`) → 2024 (`method:ledger:20242025`): identical semantic key, line connects; 2025 `not_computed` breaks.
  - mixed f/d `sog60` comparison: two named groups (48 f, 24 d), every player once; at an unreachable cutoff both selected appear once as `member=false`.
  - csv: 58 columns (39 required in spec order + fixed extras incl. `numerator,denominator,denominator_kind`), crlf, every row width = header width, formula-prefixed display name quoted and apostrophe-escaped, negative numeric `value` unquoted and unescaped, percentile unrounded; observed rows carry published `included_seconds`/`known_excluded_seconds`, empty `unquantified_gap`, `support_policy_id=matched_personal_credits_v2`.
- implementers' temporary checks re-run on the final tree: `app/tmp-v1-14/selectors.ts` (197 selectors exact against wire fields, qualifiers, partitions, census, annual identity), `app/.v1-14-composition.test.ts`, `.tmp-v1-14/export-check.ts` — green.
- `tsc -p tsconfig.json` and `tsc -p tsconfig.web.json` (both `noEmit`) — no diagnostics. `var/v1-14/typecheck-progress.txt` is a stale 16:35 log with errors that no longer reproduce; don't cite it.

### closures

R1–R12 repaired and verified as recorded above. specifics for the late ones:
- R5: `analysis-cohorts.ts` absent selections take their own group with null peer group/n/cutoff in every peer mode (skater and goalie); `analysis-history.tsx` `referenceChanged` compares only adjacent years that both have a peer group.
- R6: `displayNumber` (6 significant digits) for all on-screen and png display text and axis endpoints; the native-unit column and csv `value` stay exact.
- R7: per-selector `qualificationLabel` with general/specialty prefix (ledger headline → matched on-ice 5v5; pp/pk ledger → pp/pk spatial support; execution/goalie → per-field support; context → known-weight focal coverage; microstats → own source window).
- R8: card control is now headed "observed 5v5 reference"; the selected-field control is separate. acceptable.
- R9: `formatPercentile` reused. R10: findings print `population: summary`. R11: only `not_computed` envelope prose is exempt from the cohort-agreement equality; values/support/original/identity still must match. R12: `positionChanged` marks f↔d independently of peer mode.

### remaining (minor, non-blocking)

- R12 residual: position change is compared only between adjacent slots, so f(2023) → absent(2024) → d(2025) shows no "reported position group changed" marker; the per-row position text still shows it and the line is broken by the absence anyway. comparing against the previous present year would close it.
- R13: the selector does not mark fields whose family is `not_computed` in `publication.families` for the selected season. the spec sentence ("pending fields stay identifiable") can also be read as "pending fields remain listed and, once selected, show their reason", which the build satisfies. downgraded; root's call.
- R14: goalie profiles still fetch the unused skater observed cohort (~330 kb). pre-existing; accepted.
- observed `reference_id` exports as an empty quoted string rather than an empty cell; harmless to csv readers.

### verification-doc content the root should state (from fixture facts)

- default observed cohorts are empty at 300 min (six captured games); ranked observed defaults are only exercised at small cutoffs.
- each analytical family has one provided skater per season → modeled ranks are singleton at best; ties/f-d/cutoffs/incompatible meanings on modeled fields come from synthetic datums or runtime mutation.
- goalie `ev`/`pk` values are never provided by the fixture; goalie magnitude/percentile content is mutation-only.

## final addendum — narrow closures (code read + `tsc -p tsconfig.web.json` clean)

- R12 residual closed: `analysis-history.tsx` `positionChange(points, i)` compares the current present identity with the last earlier PRESENT identity (`findLast(person !== null)`), names the season it changed from, and is shown in the table and png. line connection still uses adjacent `breakReason`, so an absent slot still breaks the line; no gap is bridged.
- R13 closed: each selector carries a finite typed `publicationFamily` (`Family | "observed"`; counterpart usage → `descriptive`, goalie → `goalie`, ledger → `ledger`). option labels append `· pending` when `publication.families` for the selected season says `not_computed`; observed has no family row and is never marked. no new request.
- R14 closed: goalie `loadProfile` issues the player read plus the deduplicated annual goalie cohorts only; the skater observed request is built only for `detail.kind==="skater"`. goalie composition uses an empty observed league view with the detail's own publication/season, so `composeProfile` finds no observed player and no map is requested.

**final status: R1–R14 all repaired and verified. no open findings.** the content notes under "verification-doc content" still stand; the temporary goalie case on proxy :41926 is root's mutation evidence, not fixture data, and should be labelled that way in receipts. i viewed no rendered pages or png outputs. session complete.
