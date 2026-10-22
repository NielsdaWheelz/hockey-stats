# 02d — source/exposure consistency

full specification, 2026-10-21. [the plan](../plan.md) owns assignment. the user selected **three recovery probes, then conditional expansion to the remaining affected games**. this document assigns no implementation, acquisition, research execution or activation.

## target and boundary

exclude contradictory counts/time coherently, attempt bounded recovery of missing shifts, and deliver one corrected three-season observed **candidate** with attributable consequences. separately measure affected support already retained in frozen attribution records. preserve raw originals, the 05g candidate, active/previous databases, and 04m's protocol, inputs and expensive fits.

| evidence from [05g verification](../research/observed-05g/verification.md) | consequence to address |
|---|---|
| [non-5v5 attempts inside retained 5v5 exposure](../issues/outside-event-exposure.md) | eight strict-interior events in `2023020041`, `2023020685`, `2024020186`; 33/53/46 observed seconds retained despite contradictory event evidence |
| [57 successful empty shift responses](../issues/empty-shift-source.md) | `2024021235`–`2024021291`, 2025-04-08 through 2025-04-15; elapsed support correctly unavailable, despite some supported event memberships |

the 132 seconds describe the observed population, not research loss or physical truth. exclude penalty reconstruction, inferred replacement lineups, alternate feeds/parsers, all-history recapture, research-input regeneration, fitting, new website features and publication. 05h consumes the settled observed support later; 04n remains a scientific decision after 04m and this evidence. complete source recovery is not required for an honest observed product.

## one evidence rule; consumer-owned support

extract the existing observed coalescing rule into pure helpers in `reconstruct.py`:

```python
five_on_five_segments(intervals) -> list[ExposureSegment]
outside_attempt_conflicts(interpreted, reconstruction, segments) -> list[ExposureConflict]
```

`ExposureSegment` contains period, start/end seconds, four sorted skater/goalie membership lists, and original interval indices. it is a maximal positive-duration, same-period run of contiguous native `five_on_five` intervals with identical **full** membership. never join across another state, a gap or a goalie change. an incidental native boundary inside that run is still its interior.

`ExposureConflict` contains api `source_index,event_id`, `report_source_index`, period/clock, `temporal_case:interior|boundary`, and segment indices. preserve source locators and native evidence; these helpers do not change interval classifications, event links, native coverage or envelope schemas.

the predicate is a valid, timed `goal|shot-on-goal|missed-shot|blocked-shot`, a uniquely matched report with `penalty_shot is False`, no supported landing penalty-shot modifier, and reconstructed classification `other`. retain existing source admission: supported report membership does not require an additional api situation value; conflicting situation/report evidence remains `unresolved` under the existing mask. do not extend the trigger to faceoffs, penalties or stoppages.

- `start < clock < end`: interior conflict; the supported non-5v5 lineup cannot match this 5v5 run. retain/check native `shift_relation:neither` evidence. the observed owner excludes the **whole run**, once, with `event_exposure_conflict`.
- `clock == start or end`: boundary diagnostic, without a new exclusion. changing lineups and coarse source clocks do not locate a positive-duration contradiction. retain the event outside the population; report adjacent states/lineups.
- no adjoining 5v5 run: no new conflict. existing unresolved/missing-source handling remains authoritative.

apply the rule before `observed._game` skips valid `other` events. exclude all otherwise included counts assigned to that run with its time. the trigger remains outside, never an extra counted attempt. personal/spatial support inherit the on-ice mask, preserving their additional exclusions, credit attribution and null semantics. repeated evidence and prior-mask overlap cannot remove seconds/counts twice. preserve zero-event time elsewhere.

reuse one segment representation. observed receipts retain conflict locators, segment/native indices and reasons. add `shift_source_empty` when the parsed shift collection check is `match` with `observed=expected=0`; it supplements unresolved elapsed membership, not an invented known-excluded duration. unavailable/malformed shifts are different evidence.

**cost:** whole-run exclusion discards some possibly valid play, but is invariant to redundant same-player shift splits and keeps the existing count/time assignment unit. edge conflicts remain unresolved; the rule does not certify physical correctness. do not widen it after seeing losses or coverage.

## bounded recovery and explicit selection

once execution is assigned, use existing `npm run capture -- --game <id> --out <fresh-directory>` from `app/`, sequentially, with the pinned runtime. each invocation attempts six sources: play-by-play, boxscore, shifts, game-summary, play-report and landing. preserve receipts and available bodies even when unusable; no in-place retry, source-leaf mixing or shift-only cli.

1. probe `2024021235`, `2024021263`, `2024021291`: **18 requests**.
2. interpret/reconstruct each through existing owners; validate through the revised observed per-game owner against the original inventory row. useful means receipt/body integrity and game identity pass, physical included on-ice time is positive, and at least one attempt is included in a retained matched segment. nonempty shifts, command success or event-only membership is insufficient. partial personal/spatial support remains explicit.
3. if at least one probe is useful, capture the other 54 games once: **324 additional requests; 342 maximum**. otherwise stop acquisition and retain remaining original gaps. no retry loop or alternate-provider investigation follows.
4. select each targeted game's entire new bundle iff it meets that predicate; otherwise explicitly select its original bundle with a reason. missing/invalid remote evidence already represented by native `unavailable`, including an unavailable game identity, is a retained gap; do not call the observed owner on a null identity. conflicting admitted identity, receipt/body mismatch, violated native invariants or unexpected software failures stop dependent selection for investigation.

there is no all-sources-http-200 or full-game-completeness requirement beyond existing contracts. compare all six old/new bodies and interpreted facts: non-shift changes are attributable collateral changes, not automatically disqualifying. freeze selection before publication consequences; never choose captures by favorable player results.

use stable paths outside worktrees:

```text
/Users/nnandal/Documents/code/hockey-stats-raw/recapture-02d-<date>/captures/<game_id>/
/Users/nnandal/Documents/code/hockey-stats-local/source-02d-<date>/
  probe-review/                   # initial recovery receipt, envelopes and tree
  final-review/                   # only when expansion occurs
    recovery.json
    selected-games/<game_id> -> exact original or accepted new bundle
    games/                        # attributed review envelopes
  corpora/20242025/
  selection.json
```

these bounded replacement snapshots stay within already-retained local 2024–25. no additional season mirror or synchronization service. retain originals and the selection tree/manifest while referenced.

`recovery.json` is a schema-1 `source_recovery_selection`, binding the old corpus/inventory and clean producer. contain all 1,312 ordered game ids, each original bundle path, optional fresh path, selected path, `disposition:unchanged|recovered|retained_gap`, and reason. targeted rows also bind six old/new receipt hashes, available body hashes, timestamps, native-envelope refs and old/new support/link counts. absent fresh captures carry `not_requested`; failed responses retain their actual state. reject duplicate/extra/missing games, unexplained choices or mismatched symlink targets. this is an audit input, not a runtime fallback search.

if any new bundle is selected, build a fresh 2024–25 native corpus with unchanged reference captures and the explicit tree:

```sh
# from analysis/; all destinations fresh
.venv/bin/hockey-stats-reconstruct --capture <bundle> --out <new-envelope.json>
.venv/bin/hockey-stats-corpus --reference <original-20242025-reference-directory> \
  --games <selected-games> --out <new-20242025-corpus-directory>
.venv/bin/hockey-stats-observed --selection <new-selection.json> --out <new-candidate-directory>
```

if none is selected, reuse the original native corpus. `selection.json` retains `ObservedSelection` schema 1 and exactly `20232024,20242025,20252026`, with two unchanged corpora and selected 2024–25. [05g's receipt](../research/observed-05g/verification.md) binds the original selection, corpus hashes and baseline database; verify them before use.

replace `publication.py:_selection`'s embedded campaign path/hash map with the supplied manifest as authority. retain strict keys, actual hashes, exact seasons, 1,312-game inventories, source/identity validation and fixture separation. no discovery or weaker provenance. compare unchanged games in a regenerated corpus to their old interpreted/native facts, allowing only declared producer/path changes.

## observed cutover and consequences

hard-cut writer/reader to sqlite **schema 5**, updating `PRAGMA user_version` and publication metadata. tables/endpoints stay unchanged; incompatible support meaning and reasons receive an explicit version:

```text
population_version          = matched_attempts_v2
personal_population_version = matched_personal_credits_v2
spatial_population_version  = matched_unblocked_locations_v2
spatial_display_version     = rect5_gaussian10_v1
```

add both reasons to the three inherited reason unions, stored validation and effect schemas. reuse league/player responses, `CoverageDetail`, `GlobalGap` and `Evidence`; no new route, filter or recovery badge. preserve rates per 60, seasonal references, peers, reported identities, history and png meanings. old databases fail clearly under the new reader; no compatibility reader or migration. later activation/rollback pairs database with matching code rebuilt from git. preserve the running 05f/schema-3 site and 05g/schema-4 candidate now.

separate three states, keyed by exact player/game/season/cell identities:

| state | evidence and policy |
|---|---|
| `original` | frozen 05g candidate and original selection |
| `policy_only` | original selection under the new support rule |
| `selected` | new policy plus selected recovery bundles; final candidate |

produce `policy_only` through the authoritative aggregator; retain receipts, not another permanent database. a read-only inspector may decode the explicitly pinned old schema for this audit; it is not an application fallback. require `selected−original = (policy_only−original)+(selected−policy_only)` for additive facts. retain all three values for ratios/statuses/ranks; never subtract nulls as zero.

report changed games/player-seasons, physical/player included/excluded seconds, on-ice attempts, personal credits, spatial cells/counts, rates and reasons per support. separate direct changes from league-reference and peer-cohort/percentile consequences. recompute seasonal physical references, smoothing and peers through existing owners; unchanged counts do not imply unchanged comparative output. independently check default forward/defense cohorts at 300 family-specific minutes, all five percentiles and affected map references. no new ranking algorithm.

the expected original policy-only footprint is three runs/132 physical seconds before prior-mask overlap; measure actual additional losses per support. 2025–26 numerical facts must remain exact under this scope; global versions/producer and empty-source explanations may differ. stop and explain an unexpected difference, never hardcode totals or exemptions. report boundary cases separately, including `2025020202`, `2025020611`, `2025020620`.

## frozen research impact; no counterfactual fit

follow `docs/research/attribution-04b/result.json` to its hash-bound corrected preparation and baseline. metadata inspection confirms both bind original `segments.jsonl`, `events.jsonl`, `coverage.jsonl` under `/Volumes/Expansion/hockey-stats/runs/attribution-04a-20261014-02/prepared/`. execution verifies declared full hashes while streaming; this specification has not verified those bodies.

audit the union of old/new observed conflict games and the 57 missing-shift games. validate source concordance with frozen research inputs before projecting incidents. intersect physical ranges with the ledger's **own** score/context-split rows and scalar/spatial masks. require aligned boundaries and exact count/event assignment; never prorate counts or substitute website masks. report retained time/counts newly excluded, already-excluded overlap, affected players, source locators and each empty game's original disposition. frozen `all_attempts` and `unblocked_spatial` populations stay distinct.

read only required metadata/ledgers. do not invoke `read_real_deployment_designs` merely to audit metadata: it loads unnecessary matrices. reuse artifact/hash readers and ledger contracts; do not revive the removed preparer, regenerate grouped moments, read expensive fits or change 04m code. each incident records `source_status:concordant|different_frozen_evidence|unresolved`. concordant evidence permits a measured frozen-support footprint. verified different evidence completes that comparison with hypothetical new-source research consequences unassessed; never transfer event indices/ranges merely because game and clock agree. unavailable or unresolved required frozen evidence remains pending, never zero impact. compare bound bodies/admission facts, not path or retrieval-date equality alone.

bind result/prepared/baseline/ledger references, incident identities, physical/directed/player units, lost retained events and unresolved scope. recovered games establish new observed support; their hypothetical research eligibility, league references, fitted effects, scales and predictive consequences remain **unassessed**. verified tiny exclusions neither establish immunity nor require a rerun. 04n receives this evidence alongside 04m's unchanged result.

## owners, interfaces and artifacts

| boundary / files | responsibility |
|---|---|
| `analysis/src/hockey_stats/reconstruct.py` | pure evidence helpers and segment/conflict types; no native fact rewriting |
| `analysis/src/hockey_stats/observed.py` | one support mask, inherited reasons and receipts; expose existing per-game calculation as `observe_game` for aggregation/recovery review, preserving its validated input/result contract |
| `analysis/src/hockey_stats/publication.py`, `observed_spatial.py` | manifest authority, schema/population cutover, unchanged display arithmetic and checked candidate |
| `app/src/shared/observed.ts`, `server/publication.ts`, `server/spatial-publication.ts`, `web/presentation.tsx` | strict typed reader, versions/reasons and existing coverage copy; no new frontend feature |
| `analysis/research/source_exposure.py` | bounded offline recovery review, three-state consequences and frozen-ledger impact; reuse source/artifact/observed owners, no acquisition or fitting runner |
| `fixtures/captures/`, `fixtures/README.md` | reuse original cases; preserve distinct recovered revisions separately, with complete available bundles and references |
| `docs/research/source-02d/` | `result.json`, `decision.md`, `verification.md`, compact consequence tables; full receipts/native outputs outside git |

two offline operations write fresh output directories:

```text
python analysis/research/source_exposure.py recovery \
  --corpus <original-20242025-corpus.json> --captures <dated-capture-root> \
  [--probe-receipt <initial-recovery.json>] --out <new-dir>
python analysis/research/source_exposure.py assess \
  --original-selection <05g-selection.json> --selected-selection <02d-selection.json> \
  --baseline <05g-observed.sqlite> --candidate <02d-observed.sqlite> \
  --recovery <recovery.json> --attribution-result docs/research/attribution-04b/result.json \
  --out <new-dir>
```

without `--probe-receipt`, `recovery` requires exactly the three probe bundles, evaluates them and records the remaining 54 targets as `not_requested`. with it, validate/hash the initial receipt, unchanged original corpus/policy/probe sources and at least one useful probe; require the exact 57-game capture set, without recapturing probes. each invocation writes its `recovery.json`, checked review envelopes and `selected-games/` tree inside the fresh output directory. the initial receipt/tree is final if no probe is useful; otherwise bind it in the final receipt. after native preparation, the operator writes the ordinary three-corpus `ObservedSelection` with the verified new corpus digest. `assess` checks its correspondence with the recovery tree. no network requests, scheduler or resumable runner; simple explicit operator iteration suffices for capture.

`assess` writes schema-1 `source_exposure_result`: clean producer/spec/input/output refs, policy id `strict_interior_other_strength_v1`, `execution_status:complete|incomplete`, `candidate_status:ready|not_ready`, recovery totals/status, observed deltas and research-impact ref/status.

references use existing `{path,sha256}` semantics. optional values carry reasons; inventories and units are explicit. `recovery_status:no_recovery|partial|all_targeted_supported` counts validated matched support, not completeness. `research_impact:verified|pending` describes only this bounded frozen-support audit. `activation:not_run`, `admission:not_admitted`, `handoff:null` are fixed. missing required research evidence leaves execution incomplete even if software/candidate checks pass; a completed failed recovery is valid. hypothetical research reprocessing is outside acceptance.

## acceptance and content

implement/review non-overlapping boundaries, sequentially where dependent:

1. **evidence/support:** independent source review verifies `2024020186` loses 46 seconds once despite two triggers; older cases reconcile 33/53 seconds. temporary synthetic cases cover redundant native splits, goalie changes, edges, penalty shots, report-only supported strength, conflicting strength, prior-mask overlap, zero-event time and collateral events in removed runs. direct count/time checks cannot merely call the new helper as oracle. unchanged native replay facts remain exact apart from declared provenance.
2. **recovery/selection:** verify exact 3→57 budget/stop, six-source receipts/collateral differences, no useful probe, partial recovery, failed response, malformed local artifact, wrong identity, stale hash, selection/tree mismatch and preserved originals. fixtures cannot become real. if recovery succeeds, retain one independently checked original/new complete-bundle fixture pair from a recovered game, preferring `2024021235` if it recovers. never overwrite its original fixture; reuse equivalent cases.
3. **publication/consequences:** reconcile all 3,936 inventory games and all three states; unchanged game facts stay exact except declared reasons/versions. on-ice/spatial player seconds equal ten times physical seconds; each for/against count sum equals five times physical attempts. personal credits retain separate goalie/assister conservation. check rates, cell totals, inherited masks, seasonal reductions and references. validate the final candidate through sqlite read-back and strict effect reader; reject old semantics clearly.
4. **research/report:** independently reconcile bound ledgers, score splits, masks, events and additional losses. already-excluded time adds zero loss. distinguish verified different frozen evidence from missing/unresolved evidence; neither implies zero fitted impact. no matrices/fits change. complete acceptance needs the bounded ledger audit, not successful recovery.
5. **content/delivery:** a separate content reviewer checks report/browser evidence for conflicted and recovered/retained-gap games, history, affected map/reference and one png. verify detached candidate browsing and code-paired rollback on disposable paths/listener only. preserve active site/databases; pinned typecheck/build and focused integration checks pass.

temporary end-to-end/live checks follow red → green → refactor → green, then deletion with controllers/test-only dependencies. retain fixtures, checked facts, assessment tools and receipts; no permanent harness. adversarial source/statistical, systems and content review clears each boundary. specification review is not implementation acceptance.

content answers why time vanished, why a gap remains or recovered, which bytes changed, and what research consequence remains unknown. use:

- `event_exposure_conflict`: “event and shift evidence disagree about 5v5 play; the affected interval's counts and time are excluded.”
- `shift_source_empty`: “the captured shift source contains no records; elapsed 5v5 time is unavailable.”

lead `decision.md` with policy, recovery, candidate, research-impact and activation statuses. `observed-deltas.csv` records phase, `entity:game|player_game|player_season|league_reference`, season, applicable game/player/cell ids, support/quantity/unit, before/after/delta and reason. `peer-consequences.csv` identifies phase/season/position group/minute cutoff/metric/player, eligibility, rate and percentile before/after. absent entity keys mean the declared aggregate scope; absent facts carry reasons. keep full comparisons outside git and compact changed/season summaries in the report. `research-impact.json` binds per-game/per-population intersections, source status, retained losses, prior exclusions and unresolved scope. `verification.md` records checks, identities, preservation, requests and measured time/memory/storage. no new figure. close a repaired policy issue only after acceptance; retain unresolved source truth, edges and missing games explicitly in existing issue records.

material costs: stricter support loses possibly valid play; newer complete bundles can change non-shift facts/retrieval dates; native season rebuilding may cost about 42 minutes and a three-season candidate about six, based on 05g rather than a promise. new semantics require code-paired activation later. this measures retained source support, not fitted-result sensitivity. no extra infrastructure compensates for those limits.
