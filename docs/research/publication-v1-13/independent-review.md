# v1-13 independent adversarial review

reviewer: independent, read-only (this file only). worktree `/Users/nnandal/Documents/code/hockey-stats-v1-13`, branch `implement/v1-13-typed-publication`, base `c80aa0a`.
sources read: `AGENTS.md`, `docs/brief.md`, `docs/research/council.md#v1-13…`, `docs/specs/v1-13-typed-publication.md`, `experimental-application.md` (schema 7, payload additions, display, api), `experimental-card-facts.md`, `experimental-attribution.md` (ledger/mixture), `v1-01-shared-evidence.md` (identity shape), existing `publication.py`, `artifacts.py`, `captures.strict_json`, `server/publication.ts`, `server/main.ts`, `shared/observed.ts`, `operator/publication-cli.ts`, `web/client.ts`.

status legend: BLOCKER = violates a spec/correctness invariant or loses data/meaning; RISK = likely defect, needs evidence; STYLE = habitability/simplicity only.

## 0. final disposition — CLEARED (2026-10-22, frozen source, chronology rerun complete)

**verdict: v1-13 detached fixture acceptance is independently CLEARED for `var/v1-13/candidate-chronology/player-analysis.sqlite`. every finding i classed as a blocker, including G7 and its P1–P3 refinements, is resolved; no concrete correctness blocker remains.**

bound objects
- candidate: uuid `cfed52ea-954b-4d6d-87e6-dc5d8d118476`, sha256 `9ba58c11a8c430098b74eff35b47bbe797f8d345c8911fbc71ae5f432a85c10c`; `verification.json` agrees.
- retained bundle `fixtures/publication-v1-13/results`, manifest `f768b285ea529a07f9a683e54878d8f9ec42c758f899cfefcec3018c59c66078`, byte-identical to the candidate's `results/` (`diff -rq`); `prepared_sha256` = checked facts `6e50f4a4…1dd38cee`.
- frozen code: 73 changed/untracked non-doc paths on base `c80aa0a` (excluding `var/`), sha256 of their sorted `shasum -a 256` listing `5f0b9e5396e1bf4745ffd600f33ac0e1b67b4bc3f23e6174d3bfc6680321e70b`; unchanged across this rerun (only `docs/` receipts moved). any later code edit voids this clearance for the changed boundary.

why G7 is now fixed
- the defect: fixture methods fit through 2025–26 with cutoff 2026-06-01 while supporting 2023–24 rows, violating program §17 ("earlier displayed states cannot consume later responses") and chance §9 ("each state uses that season and preceding fitted states only").
- the data now obeys it: every method fits only its row season and earlier (`method:spatial` 2022–23+2023–24 with a 2022–23 predecessor; the 2024–25 ledger row cites its own `method:ledger:20242025`, fits 2023–24+2024–25); every cutoff is 06-01 of the row's ending year. my own census over all 8,600+ method references (row columns, nested `method_id`, `{kind:"method"}` evidence refs, `context_coverage`/support-catalog `method_ids`) finds 0 violations of: fit seasons ≤ row season; cutoff ≤ ending-year-06-30 and before the next published season's first game; predecessor/annual-state input seasons ⊆ fit seasons.
- the gate now enforces it in both languages. mutation probes on the frozen source: later fit season, autumn cutoff (2024-11-15), summer cutoff (2024-07-15, conservatively rejected by the 06-30 bound), later predecessor input, a 2023–24 support citing the 2024–25 method, failed-fit evidence citing it, and coverage citing it are each rejected by the python build gate and refused at ts reader startup with the specific chronology message; the unmodified bundle/database is accepted. whole prepared/coach/source-result artifacts remain intentionally unrestricted (fit seasons are the consumed filter).
- quantities unchanged: versus the previously reviewed `candidate-reviewed`, only `analysis_method` and the 2024–25 `value_ledger.method_id` differ; `value_ledger` is identical ignoring that column, and every other table is hash-identical. the independent oracle, observed-preservation, b2/b6/r6, g6 and parity results recorded in passes 5–6 therefore carry over unchanged.

final rerun evidence (scratch copies only; candidate sha unchanged; no wal/shm)
- frozen python rebuilds every table except `publication` identically from the retained bundle.
- frozen ts reader starts on the candidate; os-sandboxed `check` (no reads of `var/`, `fixtures/`, `analysis/`; no ip) exits 0, schema 7, 30 dispositions.
- not rerun after the freeze (bounded per root): my 21-case general rejection matrix and the operator activate/restore cycle, both last green on `candidate-reviewed` with unchanged tables; root reports its targeted python checks and compiled reader suite green on the frozen source.

corrections to my own record
- F2 (5v5 overtime impossible) was wrong; withdrawn on the rulebook.
- G7 was misclassified by me as a producer-pr risk; the spec makes it a declared contract, now enforced.
- my passes 5–6 G6 probe never mutated a row (its "accepted" results were vacuous); superseded by the corrected probe recorded in the previous header.

non-blocking residue (recorded, not gates)
- R7 real-scale size/startup cost unmeasured (my estimate ~8–9 GB `analysis_map` + 5–6 GB `goalie_evidence_map`; overview n+1; quadratic ts overlap join): `docs/issues/publication-map-volume.md`.
- several ts refusals still read only "Expected <filter>": fail-closed, weak diagnostics.
- operator leaves `incoming.sqlite` after a refused restore: pre-existing documented contract.
- scope: browser/png/narrow/200% checks and the full current-ui content reseal are root's receipts, not mine. this clearance asserts transport and chronology correctness, not scientific quality or real analytical capability.

## 1. highest-risk invariants (ranked)

1. **completeness closure, not just row validity.** a `provided` family must contain every applicable person×strength×key (×map_kind×view; breakdown 6 types + 3 danger bins) for selected-season persons of the right kind. the easy failure is validating each supplied row and never asserting the cross product. a missing row is corruption; a pending family returns one envelope, not thousands of rows. same for `analysis_family`: exactly seasons×10 rows. `context_coverage`: every skater×5 populations, including pending valued populations.
2. **meaning separation survives every hop.** `not_computed` / `missing_source` / `failed_fit` / `no_exposure` / `not_applicable` / absent player-season / pending row / pending family are distinct in python exchange, sqlite and http. no null without a reason; no reason without the right evidence kind (`reason_detail.evidence` empty only for not_computed/not_applicable/no_exposure). no zero fill, no clamping.
3. **identity and kind.** `person` replaces `player`; observed tables keep their factual columns, only fk targets change. every observed skater appears in `person` with exact existing name/position/teams; observed rows must be validated as `kind='skater'` in both readers (sqlite fk alone cannot check kind). goalies get no skater metrics. season-absent known person → 200 with null selected identity + real history, never another season's name/team.
4. **purpose isolation.** bundle purpose = observed selection purpose = every source/method purpose; synthetic origin ⇒ fixture; real ⇒ exactly `20232024,20242025,20252026`; observed bindings = selection seasons/digests. fixture label must reach every response and page.
5. **exchange strictness.** exact key sets at every nesting level, `type(x) is int` (bool is an int in python), safe integers ≤ 2^53−1, finite numbers, strict_json duplicate-key rejection, member paths relative/inside the bundle/no symlink escape, digest + row count checked while streaming, strictly increasing primary key per member (= sorted + unique), no member reused under two names, members written before manifest.
6. **method_id single storage.** extracted into a nullable fk column, removed from payload json, restored on read; pending rows ⇒ column null; provided modeled rows ⇒ resolving method (failed fits included). no duplicated `method_id` in payload_json.
7. **evidence keys.** `attempt_fact` key `(season,game_id,source_index)`; `event_id` never a key; `attempt_value`/setter/share supplements must match a source event and the same `prepared_sha256`; left join keeps source shots without values (five typed-unavailable fields), never deletes.
8. **interval partition.** half-open positive period-local bounds within horizon; nonoverlap per (game,team,population); shared `interval_id` ⇒ identical bounds and membership across populations; unique ids per side; `on_net_*` integers only for `recorded_goals` (with integer goal masses) and null otherwise. publisher validates, never reconstructs.
9. **map/ledger closure.** native 656 masses, `integrated_value == sum`, display 668 via `K*T` with `T` from `observed_spatial.cell_id(native_center)` (unique containing cell, no nearest fallback, no equal-id join), density `100*mass/area`; unavailable map ⇒ both arrays and integral null with reason. ledger: ten terms sum to league/replacement totals; `penalties_combined = drawn + taken`. tolerance exactly `abs(a-b) <= 1e-9 + 1e-9*max(|a|,|b|)`; no repair on failure.
10. **goalie evidence ratio.** pool goal and expected masses separately on display support, then ratio; null at zero pooled expected or nonpositive league reference; no pseudocount; ratios never summed. danger: 101 edges exactly `0..1` by `.01`, 100 bins, p=1 in last bin.
11. **reader contract.** schema 7 only; one process-lifetime readonly/disableWAL connection; startup validates physical schema + all typed rows + closure by streaming (no full event/map materialization); fixed sql branches with parameters; typed 400/404/500; duplicate/unknown query keys rejected; explicit unknown season 404 (never another); unavailable/pending 200.
12. **operator.** incoming checked with new reader; existing active preserved as opaque bytes (no `check(active)`), predecessor byte identity reported; schema7 restore uses reader; cross-schema restore = manual stop/copy/matching build/restart instructions; one previous db.
13. **candidate build.** `player-analysis.sqlite.incomplete` → verification written → rename `player-analysis.sqlite`; strict tables, explicit `PRAGMA foreign_keys=ON`, delete journal; refuse existing output; failure leaves no final candidate; database usable after inputs become inaccessible; no wal/shm.
14. **observed preservation.** same reducer (`observed.aggregate`) produces byte-identical observed facts before/after on captured fixtures; only metadata/schema changes.
15. **cross-language agreement.** python and typescript validators enforce the same row contracts, tolerances and vocabularies; a payload python accepts and ts rejects (or vice versa) is a defect, not a style issue.

## 2. spec ambiguities to resolve before acceptance (root)

- A1 `input_sha256` "hashes the exact ordered input list": byte serialization unspecified. implementation must pick one canonical form (suggest `json.dumps(list, sort_keys=True, separators=(",",":"), ensure_ascii=False)` utf-8) and both validators must use it; otherwise the field is uncheckable.
- A2 `families[].explanation` for `provided`: spec types it `string|null` but only constrains `not_computed`. recommend `provided ⇒ null` (mirrors row envelope).
- A3 which families are "dependent" for `prepared_sha256: null`. recommend: every family except none — i.e. null only if all ten families are `not_computed` for every season; anything else needs a base identity (fixtures bind synthetic identity).
- A4 `person.teams_json` shape vs observed `player_season.teams_json` `[{id,abbreviation}]`. "exact existing teams" check needs one comparison rule.
- A5 support `reason_counts` vocabulary "declared by the producing population": needs a literal per-population code list in code, or the check is vacuous.
- A6 microstat/fact_value `unit` and `denominator_kind` are "fixed by each field's definition": needs a literal per-key table, else any string passes.

status after pass 1: A1 resolved (python `json_bytes` sorted compact utf-8; ts `canonical` + `JSON.stringify` agree for the ascii-only input list). A2 resolved (`provided ⇒ explanation null`, both). A3 resolved (`provided` family ⇒ `prepared_sha256` non-null; every method must bind it). A4 resolved (`[{id,abbreviation}]`, exact list equality with observed `teams_json`). A6 resolved (python suffix rule, ts per-key literals; same table). A5 open.

## 3. acceptance checklist (concrete, executable)

exchange / python
- [ ] `hockey-stats-analysis publish --observed F --results D --out O` is the only new command; `hockey-stats-observed` entry point removed from `pyproject.toml` and `cli.py`; no fit/score/summarize placeholders.
- [ ] manifest rejects: extra/missing key at each level; duplicate json key; `rows: true`; `rows: 2**53`; `sha256` uppercase; member path `../x`, `/abs`, symlink out of bundle; digest mismatch; row-count mismatch; unsorted/duplicate member rows; duplicate season×family; missing disposition; `not_computed` with nonempty tables or empty explanation; `provided` with missing/extra table; unknown table name; purpose mismatch (bundle vs selection vs source/method); synthetic source under real; real with two seasons; observed binding digest mismatch.
- [ ] estimate rejects: value+reason both set; null value without reason/detail; unavailable with interval uncertainty; interval with level 0/1, lower>upper, empty method/conditional_on; probability 1.0000001 not clamped; empty evidence for `missing_source`/`failed_fit`; dangling reference id; `kind:"method"` reference to a source id.
- [ ] support rejects: unsorted/duplicate reason codes, zero count, unknown code, inferred_inputs outside the four, unsorted prior_seasons, observed rate with zero seconds, non-model fact with prior_only true.
- [ ] storage: `PRAGMA table_list` exact set, all strict; literal column/type/notnull/pk/fk declarations matched by both readers; `foreign_key_check` empty; `method_id` absent from every `payload_json`; pending rows have null method column.
- [ ] closure: drop one person row from a provided family → reject; drop one strength/map_kind/view/stratum → reject; perturb one native cell by 1e-6 → map integral reject; ledger term +1e-6 → reject; `penalties_combined` mismatch → reject; danger edges off by one ulp → reject.
- [ ] evidence: supplement key without source event → reject; supplement bound to other prepared digest → reject; source shot without supplement survives with five typed-unavailable values; duplicate/nullable `event_id` retained and never used to join.
- [ ] intervals: overlapping rows same team/population → reject; same `interval_id` with different bounds or membership across populations → reject; `on_net_for` on non-goal population → reject; zero-length/negative bounds → reject; duplicate player on a side → reject.
- [ ] observed preservation: before/after table dumps of every observed table on the same captured fixtures are identical except `player`→`person` and metadata.
- [ ] build: occupied `--out` refused before work; injected failure leaves only `.incomplete` (or nothing) and no `player-analysis.sqlite`; verification exists before rename; after `chmod 000` on inputs, `check` and server startup succeed; db hash unchanged by reads; no `-wal`/`-shm`.

http / ts
- [ ] all five endpoints decode; envelope `{publication,available_seasons,season,sources,methods,supports}` everywhere; `publication.kind='player_analysis'`, `schema_version=7`, family availability included.
- [ ] league: default newest/skater/overview; matrix rejects wrong strength per family/kind (e.g. `observed` without `5v5`, `overview&strength=5v5`, goalie with `pp`); duplicate `season=`; unknown key; `spatial=` (old api) → 400.
- [ ] player: unknown id 404; known id absent this season → 200, `person:null`, history rows real; no other season's name; goalie profile has no skater values.
- [ ] maps: one/two distinct same-kind players; duplicate/three ids/mixed kinds → 400; goalie selectors rejected on non-goalie families; `covered_all` only for goalie_evidence; ratio scale fixed ±25%, stored values unclipped.
- [ ] evidence: personal_shots requires `strength=5v5`, outcome enum, blocked_contacts default false; unlocated counts returned.
- [ ] context: teammates required only for with_without, 1–2 distinct excluding focal; non-skater → 400; season-absent teammate → zero together time, null rates; on/off only over dressed team-games; intersection independently recomputed matches.
- [ ] 500 on malformed stored row with existing retry copy; abort signal cancels; mixed-publication composition rejected client-side.
- [ ] operator: `check` covers all families incl. deferred; activate preserves predecessor bytes (sha before == sha of previous after); restore schema7 works; schema6 previous → restore refuses with cross-schema instructions; primary db/listener/port 3000 untouched.

content
- [ ] exact strings: "not computed", "tracked primary-pass observations are not available", "historical skating source access is unverified", "fit failed", "no eligible exposure", "uncertainty not estimated", prior-only specialties labeled hypothetical; `fixture` prominent on every current page.

## 4. findings log

passes 0–3 below are historical records; the pass-4 status table is the current disposition of every finding.

### pass 7 — chronology gate (G7), code review before the new build

spec basis verified: `experimental-player-analysis.md:17`, `experimental-chance.md:9`. no `candidate-chronology` exists yet at this pass.

ts rule as written (`analysis-publication.ts:309-316`, inside `checkReferences` with inherited `method_id`): every `fit_seasons` entry ≤ row season; `training_cutoff` year ≤ row ending year. python: no equivalent found yet (in flight).

precision points on the gate itself (not new gates)
- P1 BLOCKER for this gate: the cutoff test is year-granular. for a 2023–24 row it admits `training_cutoff` up to 2024-12-31, while the publication's own inventory shows 2024–25 regular-season games from 2024-10-04 (2025–26 from 2025-10-07). a cutoff of 2024-11-15 therefore consumes later displayed responses with every check green. the spec's wording gives the exact, self-contained rule: when the row season's successor is published, `training_cutoff < min(game.game_date)` of that successor season. this accepts any off-season cutoff (root's planned ~2024/2025 cutoffs, e.g. 2024-06-01) and needs no calendar assumption; for the newest displayed season the year rule remains (no later displayed responses exist). same rule in python. (an earlier draft of this point proposed `≤ last game + 1 day`; withdrawn, it would reject legitimate off-season cutoffs and invents cutoff semantics.)
- P2 coverage of method references: the inherited-`method_id` walk misses method references not spelled `method_id`: `{kind:"method",id}` references (e.g. failed-fit `reason_detail.evidence`), `context_coverage.method_ids`, and the support catalog's `method_ids` (which carry their own `season`). a 2023–24 coverage/support row citing a method fitted on 2025–26 passes. apply the same season rule to every method reference reachable from a season-scoped record.
- P3 consumed state inputs: root keeps whole prepared/coach artifacts unfiltered (their `seasons` may span all three years; `fit_seasons` is the consumed filter). agreed. but `predecessor`/`annual_state` inputs ARE consumed states; one whose `seasons` exceed the row season is consumption of a later state that the fit-season test cannot see. require for those two roles: input seasons ⊆ `fit_seasons` (hence ≤ row season). this completes the same gate; it is not a new one.

rerun planned on the new build: identity/bundle equality; python rebuild identity; quantities unchanged (every non-metadata table hash-equal to `candidate-reviewed`); per-row chronology census from raw sqlite (fit seasons, full-date cutoff vs season inventory, every method reference kind, consumed-state inputs); mutation probes in both languages for each clause (later fit season, late cutoff in the ending year's autumn, later method via evidence/coverage/support refs, later predecessor input); ts startup and sandboxed `check`.

### pass 6 — data/reproducibility review of `candidate-reviewed` (code not yet sealed)

object: `var/v1-13/candidate-reviewed/player-analysis.sqlite`, uuid `a141f80d-7236-4abd-8789-68211d3c1fc4`, sha `0a39537e8ed2b8c3b289c8bad22d5fe038cc4bb7967757d68dc000e4e099082c`, manifest `e84219662eed38fd76b2c78f919028d08348078e9ce516a0618a01b8e5e3693d`; `verification.json` agrees on uuid/db sha/manifest/prepared (`6e50f4a4…`). retained `fixtures/publication-v1-13/results` is byte-identical to the candidate's `results/` (`diff -rq`).

data verdict: **CLEARED.**
- reproducibility: current python rebuilds every table identically from the retained bundle; only `publication_id`/`generated_at` differ.
- change set versus `candidate-final`: only `analysis_method` (`method:spatial` gains a `predecessor` input `{sha256: checked-facts 6e50f4a4…, seasons:[20222023]}`, `fit_seasons` adds 20222023, new `input_sha256` `a134cc89…`, which i recomputed from the inputs) and `analysis_source` (`fixture_source` label/population/definition now name the synthetic 20222023 prior-state scenario). every fact, summary, map, evidence, interval, observed and identity table is hash-identical to `candidate-final`, so the pass-5 independent oracle (context groups, covered_all ratio/composition, ledger 55/110/15), B6/R6/B2 reader results and the observed-vs-schema6 identity carry over unchanged.
- G6 in data: the only prior-only support (`skater_spatial`, `prior_seasons:[20222023]`) now binds: each prior season is earlier than the row season, in the method's `fit_seasons` and in an input's seasons; 1 checked, 0 unbound.
- reader: current ts reader starts on the candidate; probe responses identical to `candidate-final`.
- sandboxed `check` (no reads of `var/`/`fixtures/`/`analysis/`, no ip): exit 0, schema 7, 30 dispositions. copy sha unchanged; no wal/shm.
- python matrix on the new bundle: 21/21 and 4/4 interval probes as specified.

code items still open at this pass (root reports all in flight; rerun on seal)
- G6 rule: probe `prior-season-unbound-by-method` (`prior_seasons:["20192020"]`) is still ACCEPTED by current python. needs both languages.
- G1: root decision to drop `probability == expected_successes/eligible_weight` (unspecified; conditional/common-panel and matched expectations differ). agreed; verify removed.
- T1 / G2 (ts repeated facts, block release location, evidence kinds), R9 (validation before key extraction): verify on seal.
- G3 handoff: temp checks deleted, verification doc with final identities.
- G7 RISK, new, for producer prs (not this fixture): rows may cite a method whose `fit_seasons` extend beyond the row season (here `method:spatial` fits through 20252026 and supports a 20232024 row). the five annual states imply each display season cites its own state with a cutoff no later than that season; the program spec owns that, and v1-13 could cheaply assert `max(fit_seasons) ≤ row season` or `training_cutoff` within it once real annual methods exist. record or decide; not a fixture gate.

### pass 5 — final review of `candidate-final` (interim: root announced a fresh build with a metadata correction; clearance below applies to that build only after the rerun listed at the end)

reviewed object: `var/v1-13/candidate-final/player-analysis.sqlite`, publication `aac8f926-b49a-4afe-ae59-f905dece6d91`, sha `d675289b…9600368`; retained bundle `fixtures/publication-v1-13/results` = candidate `results/` copy (`diff -rq` identical), manifest `42e09869…0aa66`, `prepared_sha256` = checked-facts `6e50f4a4…1dd38cee`. all checks ran on scratch copies; the copy's sha was unchanged after every reader/operator run and no `-wal`/`-shm` appeared.

evidence
- reproducibility: `build_publication` with the latest python source (15:28+ edits) from the retained bundle reproduces every table except `publication` (uuid/time/producer) exactly, twice. so the candidate corresponds to current source, not only to the 15:24 build.
- reader: latest ts reader starts on the candidate (full physical/typed/closure validation) and returns byte-identical probe responses before and after the late ts edits.
- python rejection matrix on the retained bundle: 21/21 + 4 interval probes behave as specified (block release location, failed-fit/missing-source evidence kinds, proportional residual, pending coverage, mirror, 5+5, dressed affiliation, supplement without source, completeness, repeated penalties, horizon, unsafe/bool/nonfinite/probability; valid interval accepted, level 1 and reversed rejected; OT 5v5 accepted).
- independent oracle (my own code from raw sqlite rows, not production sql/kernels): on/off, two-teammate and one-teammate with/without for `recorded_all_attempts`, `recorded_goals` (incl. on-net pairs) and `recorded_locatable_unblocked` — 0 mismatches in seconds, masses, rates; covered_all display ratio recomputed with my own area-weighted gaussian kernel = 100% in all 668 cells, max abs diff 1.1e-16, mapped 1/2/3 + unmapped 2/1/4 = totals 3/3/7; ledger 55/110, combined penalties 15.
- B6 confirmed through the reader: `covered_all` summary/map/danger each carry `actual_states` `{5v5 both goalies: 5/2.5/2}`, `{6v5 attacking goalie absent: 2/.5/1}` → 7/3/3; league 3/12 → mapped ratio 100%, beyond the fixed ±25 legend, stored value unclipped.
- R6 confirmed: execution evidence for setter candidate `9000002` returns the attempt shot by `9000001` (setter row) plus its own shot, with 3 setter and 5 share rows.
- B2 confirmed: season-absent goalie (`9000004`, 20252026) → 200, `person:null`, families/maps/evidence `availability:"absent"`, real history for the two published years.
- observed preservation, independently: `season, game, player_game, player_season, spatial_cell, player_game_spatial, player_season_spatial, player_season_pair` identical column lists and rows versus `baseline-schema6-valid/observed.sqlite` (sha `4d0a479e…`); `player`→`person` name/position/source locators identical for all 216 observed skaters; no observed row joins a non-skater person.
- operation (sandbox denying reads of `var/`, `fixtures/`, `analysis/` and ip networking; disposable dirs): `check` exits 0 (schema 7, 30 dispositions); `activate` over a schema-6 active preserves its bytes as `previous.sqlite` (sha before = after = `4d0a479e…`) and reports them; cross-schema `restore` refuses with matching-build instructions; schema-7 `restore` swaps active/previous exactly.
- content census of the candidate: per-field tracking reasons name the missing observation (22 fields), shot assists use "tracked primary-pass observations are not available", skating "historical skating source access is unverified", 10× "fit failed", 12× "no eligible exposure", not_applicable defense on pp references, one prior-only support; fixture banner/notice strings present in `root.tsx`/`presentation.tsx`; labels live in the shared contract (`player-analysis.ts` `fieldLabels`).

remaining items (none blocks the fixture candidate; all are concrete)
- G1 RISK (spec gap introduced by a validator) latest python adds `execution_breakdown.probability == expected_successes/eligible_weight` (`analysis_publication.py` `validate_payload`, "breakdown probability differs from its own denominator"). no spec anchors that definition: if `expected_successes` is the neutral-reference expectation, `probability` becomes the neutral rate under an unqualified name; if it is the focal fitted expectation, the rule is right but `effect` then needs its own reference. add one line to the appendix (which reference each of `expected_successes`, `probability`, `effect` uses) before v1-06/v1-11 serialize, or drop the check.
- G2 ts parity (operator `check` is the activation gate): no repeated-fact equality (T1), no `outcome=block ⇒ location_kind≠reported_event` (B4-ts), no reason↔evidence-kind rule in `validEstimate` (R4-ts). python enforces all three at build, so a publisher-built candidate is safe; a hand-edited or future-defective candidate would pass `check`. fix (small) or record in `docs/issues/`.
- G3 handoff hygiene required by the spec: delete temporary checks/controllers (`app/src/web/v113-check.tsx`, root's scripts) after final green; write `docs/research/publication-v1-13/verification.md` (absent at review time); keep the retained bundle + `fixtures/publication-v1-13/README.md` + checked facts.
- G4 STYLE: unreachable `pending("player is absent…")` fallbacks at `publication.ts:178,208`; R9 cli traceback on malformed catalog rows; operator leaves `incoming.sqlite` after a refused restore (documented pre-existing contract: "inspect any incoming.sqlite").
- G5 R7/R8/T3 real-scale cost unmeasured; root will record an issue. agreed: not a fixture gate.
- observation, not a defect: context responses now carry only the focal player's coverage. groups are restricted to focal-present intervals on focal dressed team-games, so the focal record is the complete gap disclosure for both panels; selected players are still listed.

- G6 confirmed root's late defect independently: on the current retained bundle (manifest `42e09869…`) a provided `skater_spatial` row whose `support.prior_seasons` is changed to an arbitrary `["20192020"]` still BUILDS (probe `prior-season-unbound-by-method` accepted), so `prior_seasons` is unbound today. the fix should require, per supported row: every prior season strictly earlier than the row season, and contained in the referenced method's `fit_seasons` (and its input seasons); `prior_only ⇒ prior_seasons` nonempty. the same rule belongs in ts `checkReferences`/row validation.

rerun required on the announced fresh build (root: prior-only 5v4 support `prior_seasons:[20222023]` was unbound by method inputs/fit seasons; synthetic predecessor input added): new candidate sha/uuid/manifest; retained bundle == candidate `results/`; python rebuild identity; ts startup + probe identity (numerical values should be unchanged); a probe that an unbound `prior_seasons` entry is now rejected; observed-table identity; operator `check`.

### status refresh — pass 4 (code at 15:24, probes on bundle `var/v1-13/full-results` 15:17; final candidate not yet declared)

all 21 python probes now behave as specified (harness rerun: block release location, failed-fit kind, proportional residual, pending coverage, mirror, 5+5, dressed affiliation, supplements, completeness, repeated penalties; OT 5v5 accepted). `candidate-full8` (sha `ae890768…`, 15:22) predates the 15:24 edits that add `provenance` to source-only payloads; the current ts reader refuses it ("missing key data.provenance"). that is expected drift, not a finding; the final review must use a candidate built by the final code.

| id | status | evidence |
|---|---|---|
| B1 map matrix | fixed | both `map_keys`/`requiredSelectors`; fixture 40 spatial maps/skater |
| B2 absent season | fixed at the api (`absent(...)` in families/maps/evidence/coverage); STYLE residue: `publication.ts:178` (`readSummary`) and `:207` (`collection`) still return `pending("player is absent…")` behind earlier absent checks. unreachable now, but they re-encode the old conflation; make them `absent` or throw |
| B3 provenance partition | fixed, both | `analysis_publication.py:318`, `player-analysis.ts:554` |
| B4 block release location | fixed in python (`:1361`); ts `AttemptFact` (`player-analysis.ts:~1709`) still lacks `outcome=block ⇒ location_kind≠reported_event`. python is the build gate; ts `check` would pass a hand-edited row |
| B5 repeated facts | fixed in python (`_check_repeated_facts`); T1 below for ts |
| B6 covered_all states | python validates `actual_states` and selection (`:1029,:1215,:1263`); ts sums them (`player-analysis.ts:1216-1250`). to verify on the final candidate with root's 5/2.5/2 + 2/.5/1 → 7/3/3 case |
| F1 pending coverage | fixed, python (`:1394`) and api (`unquantified_gap:true`, null totals) |
| F2 OT 5v5 | withdrawn (reviewer error; rulebook) |
| F3 dressed affiliation/observed team | fixed, python (`:1829-1831`) and ts (`analysis-publication.ts:854`) |
| F4 distinct populations | fixed in `full8`: all/goals/locatable masses differ per interval |
| F5 placeholder digests | fixed: methods cite checked-facts `6e50f4a4…`, coach files `9e8ed42c…`/`724ff6aa…`; sources cite capture receipts |
| F6 block/unclassified | fixed in `full8`: 12 `block_contact`, 32 `shot_type null` |
| R1 residual tolerance | fixed (proportional, `:1260`) |
| R2a/R2b membership, mirror | fixed, both |
| R3 skater without observed rows | fixed (ts now checks `player_season → person.kind='skater'`, not the converse) |
| R4 reason↔evidence kind | fixed in python (`:274-275`); ts `validEstimate` still has no kind rule (consistency gap) |
| R5 fact read-back | fixed (`check_results` `:1761-1769`) |
| R6 setter events | root closing; verify on final |
| R7/R8/T3 real-scale cost | open; unmeasured. not a fixture blocker; record before producers serialize |
| R9 cli traceback | open, probe-confirmed again: `KeyError`/`TypeError` escape `analysis_cli.py:24` (exit nonzero, no output) |
| T1 ts repeated-fact equality | open: no counterpart in `analysis-publication.ts` |
| T4 duplicated geometry/kernel | open STYLE |
| N1–N4 | N4 resolved (python reason vocabulary `:196`); others unchanged, minor |

new evidence-quality finding
- E1 RISK (acceptance evidence) `var/v1-13/reader-rejections-green.json`: 10 of 13 cases record only the operator's generic prefix ending in `{`; the cause object is not captured (only `overlapping_context`, `inconsistent_source_horizon`, `incomplete_membership` show their message). a case "rejected" for an unintended reason (a broken edit, integrity failure, wrong digest) is indistinguishable from the intended check. record `error.message`/cause per case and assert the expected text before calling the rejection matrix green.

### pass 3 — ts `validateRequiredRows` / `validateCrossRecords` (`analysis-publication.ts`, working tree)

agreement verified: required selector matrices now match python for maps, breakdowns, goalie grids and adjustment targets (pp states `for_*` only, pk states `against_*` only; python `required_keys` `:1697` identical); ts K·T kernel `area_target·exp(−d²/200)` normalized over targets equals `observed_spatial.pooling()` (column-normalized); goalie ratio formula and `no_exposure` rule match python; method↔publication `prepared_sha256` binding and "provided ⇒ prepared non-null" now enforced in ts (`:104,:115`); 5+5 membership both languages.

remaining ts gaps (operator `check` uses ts, so a hand-edited or stale candidate passes these)
- T1 RISK no repeated-fact equality in ts: python `_check_repeated_facts` exists; ts has no counterpart for microstats goals/a1 vs `player_season.personal_*`/descriptive 5v5, nor penalties vs descriptive focal.
- T2 RISK no team-side mirror check (R2b) and no dressed↔person-team/observed-team check (F3) in either language.
- T3 RISK (scale) overlap test is a self-join over `(season,game,team,population,period)` without a supporting index (`interval_fact` pk leads with `interval_id`): quadratic within each group, ~10^8–10^9 comparisons at real scale. python's ordered single pass is linear; ts could do the same with `ORDER BY … start_seconds` and `forEachRow`. the 5+5 membership query runs two correlated counts per fact row (~6M rows real). measure on a synthetic full-size bundle before calling startup cost acceptable.
- T4 STYLE ts re-derives native geometry from constants (`x=-97.5..100 step 5`, rounded-corner test) and the pooling kernel. acceptable as independent verification (fail-closed), but it is a second implementation of `shot_origins.grid()`/`pooling()`; comment it as such, or compare against the stored `analysis_grid` + `spatial_cell` only. a native center falling outside every display cell writes `raw[undefined]` and is caught only indirectly by the closure check.

### pass 2 — executable probes against python + scrutiny of root's clarifications

method: disposable harness in my scratchpad copies `var/v1-13/full-results`, mutates one member, rebinds digest/row count, then runs `read_results` or `build_publication` with the repo venv. outputs disposable; repo, `var/` and candidates untouched.

| probe | expected | python today |
|---|---|---|
| baseline read / build | accept | accept |
| `outcome:block` + `location_kind:reported_event` | reject | **accepted** (B4 stands) |
| puck management `source_modeled` citing its source | accept | accept (B3 fixed, both languages) |
| `failed_fit` whose only evidence is a source | reject | **accepted** (R4 stands) |
| adjustment residual 1e-8 with exact five-term closure | accept | **rejected** "residual exceeds arithmetic tolerance" (R1 stands) |
| pending `context_coverage` carrying `known_excluded_seconds:3500`, `source_ids` | reject | **accepted** (new F1; the fixture itself does this) |
| `rows:true`, `source_index:2**53`, p=1.0000001, value+reason, `event_id:-1` | reject | reject |
| `end_seconds > period_horizon_seconds` | reject | reject |
| 5v5 context interval moved to period 4 (consistent bounds/horizon 300) | ~~reject~~ accept | accepted — correct (F2 withdrawn) |
| drop one `skater_spatial` pk row | reject | reject (completeness now enforced) |
| `skater_penalties.recorded_drawn` ≠ descriptive focal drawn | reject | reject (B5 fixed) |
| overlapping interval | reject | reject |
| one team row's `for_mass` ≠ other team row's `against_mass`, same interval/population | reject | **accepted** (R2b stands) |
| remove one membership row (4 skaters) | reject | reject ("known 5+5 physical skater membership"; R2a fixed) |
| `dressed_game` for a game/team outside the person's season teams and absent from observed `player_game` | reject | **accepted** (new F3) |
| `attempt_value` key without source attempt | reject | reject |

fixed since pass 1 (verified in code or by probe): B1 map matrix (`map_keys` now excludes defense at `5v4|5v3|4v3|pp`, offense at `4v5|3v5|3v4|pk`; fixture has 40 spatial maps/skater); B3 provenance partition (python `:187`, ts `player-analysis.ts:~550`); B5 repeated facts (`_check_repeated_facts` compares microstats goals/a1 with `player_season.personal_*` and descriptive 5v5, and penalties with descriptive focal); R2a 5+5 membership.

new findings
- F1 BLOCKER-lite (meaning) pending coverage carries measured coverage. `context_coverage` with `availability:not_computed` still accepts `known_excluded_seconds`, `reason_counts`, `source_ids`, `unquantified_gap:false` (`validate_fact` `analysis_publication.py:~1236`; ts `ContextCoverage` likewise). an unfinished population cannot know its excluded seconds; `unquantified_gap:false` on it asserts complete knowledge. require `not_computed ⇒ known_excluded_seconds null, reason_counts [], unquantified_gap true` (or define what they mean), and fix the fixture rows (all 168 pending valued rows claim 3500 s).
- F2 WITHDRAWN (reviewer error). i inferred that 5v5 cannot occur in regular-season overtime from the standard 3-on-3 start. root checked the primary rulebooks: 2025–26 nhl rules table 15 (examples 5/16) and 2024–25 table 17, printed p160 (https://media.nhl.com/site/asset/public/ext/2025-26/2025-26Rules.pdf), allow 5v5 during continuous overtime after penalties expire. the current validators are correct: period-4 5v5 intervals within a 300 s horizon are admissible and need no period 1–3 restriction. lesson recorded: rule impossibility needs the rulebook, not the usual format.
- F3 RISK dressed roster can contradict identity and observed facts. `_check_intervals` checks `dressed_game.team_id ∈ game teams` only. not checked: team ∈ `person.teams` for that season; consistency with observed `player_game(season,player,game,team)` for the same skater; per team-game physical bound (≤ 20 dressed). on/off is defined over dressed team-games, so a wrong dressed row moves time between on/off silently. at minimum enforce the person-team and observed-team agreement where both exist.
- F4 RISK (test adequacy) the context fixture cannot detect population mixing: for every interval `recorded_all_attempts`, `recorded_goals` and `recorded_locatable_unblocked` carry identical for/against masses (e.g. `fixture:0` team 14: 1/2 in all three). a reader that joined or substituted populations would still pass root's expected answers. give each population distinct masses (goals ≤ on-net ≤ unblocked ≤ all attempts) and assert per-population results.
- F5 RISK (fixture honesty) placeholder digests. the current bundle's source receipt is `sha256:"aaaa…"` for `fixtures/publication-v1-13/checked-facts.json`, whose actual digest is `591f724b…6bc35`; method `design_sha256:"bbbb…"`. both validators accept any 64-hex string, so the publication asserts identities nothing has. "hashes establish identity": bind the real checked-facts digest (and a real synthetic design digest) when the fixture is regenerated.
- F6 STYLE the fixture blocks/unclassified types are absent: three attempt facts, no `outcome:block`, no source-unclassified `shot_type:null`. B4 and "source-unclassified attempts remain visible in personal evidence/counts" have no fixture exercise.

scrutiny of root's clarifications (2026-10-22, spec diff)
- `age_years = days(birth→feb-1)/365.25`: sound and executable; both validators recompute it (`analysis_publication.py:281`, `analysis-publication.ts:146`) and agree numerically (integer day difference in both). two gaps: (a) known birth date with null `age_years` is allowed when an identity problem is listed — age is algebraically determined, so require `birth_date ⇒ age_years` exactly; (b) the v1-01 encoder later "converts age to years" for modeling; if it uses another divisor the card's age and the model's age silently differ. one shared constant, or say the card age is display-only.
- publication-row `prepared_sha256`: correct and minimal. note it adds checkability only for methods (inputs must contain `{role:prepared, sha256}` equal to the row); supplements and base facts in one database come from one manifest, so the binding is by construction. ensure the ts reader actually performs the method check (python does, `validate_catalog`), and that `prepared_sha256 IS NULL ⇒ every analysis_family row not_computed` is asserted in sqlite read-back as well as the manifest.
- `interval_fact.period_horizon_seconds`: closes a real gap without a new table; per game/period agreement is enforced (`:1638`). limits: it is a producer assertion with no independent anchor (the publisher cannot falsify a horizon of 1,200 on a truncated period), for 5v5 context in periods 1–3 it is 1,200 whenever the period is fully known. with F2 withdrawn, overtime is a real discriminating case: 5v5 after expired penalties ends at the overtime goal or 300 s, so the horizon carries information the scheduled maximum does not. that strengthens the clarification. python check `minimum=0` vs sqlite `>0` is a trivial mismatch.
- no free-text parsing found in these clarifications. the one remaining free-text dependency is B2: absent player-season is only distinguishable from not-computed by parsing `explanation` ("player is absent from selected season").

### pass 1 — python validators/storage, ts rows/closure/interfaces (working tree, ~2026-10-22, uncommitted)

already caught by root, not repeated: density/ratio scale units, goalie_observed method exemption, danger edges, goalie game leakage into scalar projection, profile decode. grid ids now agree (`native656`/`display668`).

blockers
- B1 cross-language map matrix disagrees. `analysis_publication.py:1309-1311` `map_keys('spatial')` excludes roles only at `pp`/`pk`, so `required_keys` DEMANDS defense maps at `5v4|5v3|4v3` and offense maps at `4v5|3v5|3v4`. `analysis-publication.ts:152` rejects exactly those stored rows ("map role/view differs from its strength") and `player-analysis-selections.ts:66` forbids querying them. a python-complete spatial family therefore cannot start the server. ts is right: appendix "pp offense and pk defense only", attribution "shorthanded offense … has no individual creation model". fix python `map_keys` (and the spatial completeness count follows). the `skater_spatial` exact-pp-state rows then need defense fields `not_applicable`, which neither validator asserts.
- B2 absent player-season is encoded as `not_computed`. `publication.ts:60,71` `pending("player is absent from selected season")`, `:90` `pending("no selected-season observed skater record")`, `selected-publication.ts:55,94` (evidence, context coverage). spec: "missing computation, missing observation, failed fit and absent player-season remain different states"; content requires "not computed" only for unwritten families. the ui will render "not computed" for a season the player did not play. needs its own state (e.g. `person:null` with `families:null`/an `absent` availability literal), not a free-text explanation inside the pending envelope.
- B3 provider-modeled values are forced to impersonate our method, in both languages. `player-analysis.ts:535-537` and `analysis_publication.py:185` map every construction except `recorded|reconstructed` to `kind:"method"`, so `source_modeled` (puck management: "source-provided … never ours", "raw provider values cannot be relabeled our model") must cite an `analysis_method`. correct partition: `recorded|reconstructed|source_modeled → source`; `inferred|model_valued|modeled → method`. `analysis_publication.py:1060` (`construction == 'source_modeled'`) then also needs the source kind.
- B4 blocked attempts can present a recorded release location. `analysis_publication.py:1195` and `player-analysis.ts:~1478-1484` only forbid `block_contact` on non-blocks; `outcome:"block"` with `location_kind:"reported_event"` passes. for nhl blocks the reported coordinate is the contact. require `outcome=='block' ⇒ location_kind ∈ {block_contact, unavailable}`. AGENTS.md: "block contacts do not become release locations".
- B5 spec-required equality of repeated physical values is not enforced in python storage. `check_results` (`analysis_publication.py:1557-1601`) has no comparison of `skater_penalties.recorded_{drawn,taken,served}` with `skater_descriptive.recorded_penalties.focal.*`, nor microstats `goals_per60`/`primary_assists_per60` (and their numerators/denominators) with the observed `player_season.personal_*` owner. spec §metadata: "enforce equality for repeated observed goals/a1 and recorded penalty fields". root says ts `validateCrossRecords` is coming; the python publisher must refuse the candidate too, since it is the build gate.
- B6 `covered_all` loses its actual-state records. spec: "`covered_all` retains separate actual-state records `{attacking_skaters,defending_skaters,attacking_goalie_present,defending_goalie_present}` for extra-attacker evidence". neither `_goalie_summary` (`analysis_publication.py:885`) nor ts `GoalieObserved`/`GoalieEvidenceMap` carry a per-state array, so `covered_all` is an aggregate with no recoverable composition.

risks (likely defects; need a decision or evidence)
- R1 adjustment residual tolerance is absolute, not arithmetic. `analysis_publication.py:~1095` `close(numerical_residual, 0)` is `|r| ≤ ~1e-9` regardless of magnitude; a legitimate float residual of 1e-8 on a 60/hr target is rejected while the sum check already holds. check the five-term sum against `factual_prediction` and require `residual == factual − (baseline+self+teammates+opponents+coaching)` under `close`, not `residual≈0`.
- R2 interval membership cardinality and side consistency unchecked. `_check_intervals` (`analysis_publication.py:1604`) requires nonempty membership overall but not that the fact's own `team_id` side is present, nor 5 skaters per side for 5v5 context; a fact row whose team has no members silently makes every focal "off". also no check that the two team rows of one `(game,interval_id,population)` mirror (`for_A == against_B`); league references would double-count inconsistently.
- R3 catalog skaters without observed rows: python build accepts them (only `observed ⊆ person`, `publication.py` build loop); ts `observed-publication.ts` `missingSeasons` (person skater EXCEPT player_season) rejects them. one rule needed before real v1-01 identity arrives (a dressed-but-unmatched skater is plausible).
- R4 `reason_detail.evidence` kind is not tied to the reason in either language (`analysis_publication.py:138`, `player-analysis.ts` `validEstimate`): `failed_fit` may cite only a source and `missing_source` only a method. spec: "a missing source/failed fit needs its actual source/method record". (root's "source-kind refs" may cover this; listed in case it does not.)
- R5 fact read-back missing. `check_results` compares stored summary rows exactly but never reads back `attempt_fact` (incl. joined supplements), `interval_*`, `dressed_game`, `context_coverage`, `attempt_setter`, `attempt_execution_share`. spec: "serialized scalar read-back, integer counts, IDs and support membership remain exact".
- R6 execution evidence omits the focal's setter-candidate events. `selected-publication.ts:82-85` selects setters/shares only for attempts the focal SHOT; attempts where the focal is a `candidate_id`/setter recipient are unreachable, so inferred setting has no event drill-down. confirm intended scope.
- R7 real-scale storage cost. per skater-season ~56 `analysis_map` rows (40 spatial after B1, 14 execution, 2 territory), each 656 `{cell_id,value}` + 668 `{cell_id,mass,density}` json ≈ 60 kB → ~3 MB/skater-season, ~8–9 GB for ~900 skaters × 3 seasons; `goalie_evidence_map` 144 rows/goalie-season × ~140 kB ≈ 20 MB → ~5–6 GB. ts startup decodes every row. not a fixture blocker, but measure with a synthetic full-size bundle before producers serialize; the spec says fix measured problems at their owner.
- R8 league overview is per-player n+1: `publication.ts` `league` → `families()` per person → ~20 `readSummary` queries and full payload decodes each (≈18k queries for 900 skaters), and the overview embeds whole family payloads (spatial with state weights, penalties with category records, context bands, full observed summary) instead of the "finite scalar projection". measure response bytes/latency; the extra outer `result()` around overview also creates a pending state no owner can produce.
- R9 cli robustness: a catalog row lacking its key raises `KeyError` in `Results.rows` (key extraction precedes `validate_catalog`, `analysis_publication.py:~1340`), and a non-object jsonl line raises `TypeError`; `analysis_cli.py:24` catches neither, so malformed input yields a traceback instead of "publication failed".

consistency nits (python is the gate; ts weaker/stricter)
- N1 python `estimate` requires `lower ≤ value ≤ upper` (`:131`), ts does not; neither bounds probability intervals to [0,1].
- N2 person: python `height_cm ≥ 0` vs sqlite/ts `> 0` (0 passes validation then fails insert); sweater uniqueness python `(team,game)` vs ts `(team,game,number)`; python requires identity problems for null display/birth/age/height/hand, ts does not; identity problem field vocabularies differ (`teams`,`age_as_of`).
- N3 ts `analysis_map` strength accepts any spatial∪goalie strength for any kind (finishing@pp, ice_won@5v4 pass ts); ts `skater_spatial` does not check `state_weights` against the selector (python does, `:996`).
- N4 support `reason_counts` codes are free text in both (A5 open).

### pass 0 — baseline and first in-progress diff (operator, observed reader split)

- R0.1 RISK `app/src/operator/publication-cli.ts` (working tree): the cross-schema restore guidance prints on ANY `check(incoming)` failure during restore, including a corrupt schema-7 previous. message should be conditional on the actual cause (user_version ≠ 7) or worded as "if previous is an older schema…". low impact; misleading operator copy.
- R0.2 ok `publication-cli.ts`: `check(active)` removed; predecessor sha256/bytes reported before rotation. matches spec. verify in disposable directory later.
- R0.3 note `app/src/server/observed-publication.ts` (new, uncommitted): observed reader extracted; joins `person` instead of `player`. must also assert `person.kind='skater'` for every observed row and exact name/position/teams equality (invariant 3). not yet visible.
