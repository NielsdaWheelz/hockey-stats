# v1-01 independent adversarial review

reviewer: claude (opus 5.5), read-only. started 2026-10-22 14:40 pdt. probes and source snapshots live under `var/v1-01-root/claude-review/` (`snapshot-1/` = sources at 14:44, with sha256s). line numbers refer to the working tree at the time each finding was written; code is churning, so each finding names the function as well.

status vocabulary: **defect** = wrong meaning or crash in written code; **design** = spec/interface flaw that code faithfully reproduces; **evolving** = not-yet-written or knowingly in progress, listed only so final review can check it. root's already-requested fixes (negative scalar validation, pointer array indexes, ordinary live anchors, chronology-unproved known prefixes, selection-parent exclusion, compact serialization, included-mask team/slot coverage) are not repeated.

nothing here claims five-season acceptance. fixture behavior proves interface/semantics only.

## final superseding review — 2026-10-22

supersedes every section below, which remains as history.

**identity.** branch head `c5d597dd` (dirty worktree). frozen package aggregate `source_code_sha256` `b2ac65f8e6dd7c1faec2bade6a4dc446646c322ca17a0e5182d3d80d5a92379f`, recomputed by me and equal to the artifact manifest's value; preparation policy (spec) sha256 `28624b42…8795`. per-file sha256s in `claude-review/snapshot-final/sha256.txt` (e.g. `analysis_context.py` `774bc5eb…`, `analysis_records.py` `afc74806…`, `analysis_support.py` `bbdf6bdf…`, `feature_data.py` `b0db151d…`, `reconstruct.py` `1d97a585…`). artifact `var/v1-01-root/root-r6`, manifest sha256 `603ee00dfe069c99eb5fda3bda9f5d60ea9969fa3820a1df3b5bfcf16cefb7df`; 36 fixture games, 152 s wall, 1.04 gb peak, 1,939,136,248 output bytes.

### 1. correctness — no remaining blocker within the 36-game fixture boundary

every defect i raised is repaired or withdrawn and re-verified on the frozen code or root-r6: d1 goal episode context, d2 invented starts across unresolved spans (now own-row participation behind a completeness gate), d4 unknown labels, d5 unclocked ordering, d7 season names, d8 reason codes, d9 interior masks, d10 goalie on-net taint, r6 overlapping own shift rows (strict overlaps and nesting are now conflict components omitted from known participation and coverage; exact duplicates and touching rows still merge). d3 was withdrawn as unreachable.

independent checks on the frozen code and root-r6 (all under `var/v1-01-root/claude-review/`):

- public readers (`final-checks-3.json`): 36 games, 5 season people files and coverage validate; an `open` audit hook saw the readers open nothing outside the artifact (no source reopen); no network or non-numeric third-party import. source events are identical to the original interpreted events in 36/36 games; 11,623/11,623 chronology links are mirrored.
- support: 3,320/3,320 included attempts lie in a chunk containing their clock; no unresolved or excluded potential attempt lies strictly inside an included segment; 53/53 exact-state time rows and 5/5 per-season event tables equal my own recomputation.
- participation (`probe-participation-3.txt`): every uncensored player's participation equals boxscore toi (1,261 with a `match` check, 34 with `unavailable`); every disagreement is censored. r6 witness `2025020565`/`8482684` (`probe-r6-2.txt`): coverage false, 27 censored spans totalling 1,564 s, prefix `toi_all_seconds` null with known 921 s; synthetic duplicate/touching/overlap/nesting controls behave as specified.
- goalie on-net prefix (`probe-prefixes-4.jsonl`): 75 goalie appearances, every known total equals boxscore `shotsAgainst`, no taint; elapsed vs same-clock event prefixes 0 mismatches over 59,628 pairs.
- owner parity (`parity-3.json`): HEAD and frozen `reconstruct_game` plus the 5v5 projection are byte-identical on all 36 documents. three-season observed/research reducer parity is root's receipt; i did not rerun it.
- strict artifacts (`tamper-3.json`, on my own two-game build from the frozen code): 15 reader corruptions and 9 bad preparation inputs all rejected; the baseline is accepted. writing output inside an input was not exercised, to avoid touching root's inputs; the guard was read.
- immediate labels (`synthetic-labels-3.txt`): stop at 2 s true and 3 s false; reattempt at 5 s true and 6 s false; unknown or invalid successors unavailable.
- downstream readiness: 4,236 ordinary execution attempts selectable with pre-score, 927 of them without matched elapsed support; 36,392 included chunks (104,833 s); 1,252 season people with no abbreviated name.

low notes, not blockers: r6 omission also drops the span all conflicting rows agree on, so `known_*` lower bounds are looser than necessary; the `overlapping_individual_participation` issue names the player only in message text and is not linked from that player's `player_shifts[].issue_indices`; `PersonValues.identity_observations` stays optional, now with an exact conditional check; numpy/scipy load transitively through `shot_origins` at reader import.

### 2. consumer-contract caveats (v1-05/v1-07 and any strength-transition consumer; not producer fixes)

- **r1.** review-awarded goals follow the stoppage that closes their episode in verified source order, so they have no pre-event `live_episode_index`. on fixtures that is 4/195 ordinary goals (`2021020942 /plays/301`, `2022020001 /plays/139`, `2024020022 /plays/236`, `2025020006 /plays/183`) versus 2 of ≈4,000 other ordinary attempts. its presence must not be a predictor unless a declared rule assigns such goals to the closing episode.
- **r2.** `prior_shorthanded_side` compares skater counts only, so an extra-attacker spell reads as the opponent being shorthanded. consumers must not interpret it as penalty state.
- **r3.** `feature_facts.outcome` carries future next-event/stoppage/attempt facts beside predictor groups. select predictor families by name; never take `feature_facts` wholesale.

### 3. representation — measured operating cost, not a correctness failure

about 54 mb per game (1.94 gb for 36), roughly 62 % of it repeated inline evidence; one game takes 0.4 s to parse and 2 s to validate. naive extrapolation is ≈350 gb and hours per full reader pass for 6,560 games. this is an estimate, not a measurement, and it is recorded in `docs/issues/prepared-evidence-size.md`. changing it is a storage-schema amendment for a later decision, correctly excluded from this assignment.

### 4. pending hdd acceptance — not cleared

`/Volumes/Expansion/hockey-stats` is absent. still to come: the exact five-season `real` preparation of 6,560 inventory games; validation of every partition through the public readers; reconciliation of every selected game, original event and per-state count/time/slot coverage; independent spot checks against real originals; and real wall time, memory, output bytes and the capacity decision. owner: `docs/issues/evidence-v1-01-acceptance.md`. fixture results above establish interface and semantics only, never five-season acceptance.

housekeeping for root: `docs/research/evidence-v1-01/verification.md` should cite which evidence closes each acceptance row, including the synthetic-case items. the probes and outputs under `claude-review/` are temporary and may be deleted after root's final green; this file is the compact receipt.

## interim final review — 2026-10-22 15:15 pdt (superseded)

scope: the frozen source/context owners (`snapshot-2/`, sha256s in `snapshot-2/sha256.txt`, taken 14:57) and root's completed fixture artifact `var/v1-01-root/root-green` (manifest sha256 in `claude-review/root-green-manifest.sha256`). root's announced small source-admission/people/date/direct-missing-history patches land after this snapshot; they need only a diff read plus a rerun of `final_checks.py` and `tamper_checks.py`, not a new review.

verdict: **one narrow concrete correctness item remains (r6, overlapping own shift rows accepted as complete participation); nothing else found blocks this assignment within the 36-game fixture boundary.** all ten pass-1 defects are repaired or withdrawn and re-verified by probe. beyond r6: one outcome-correlated source-order caveat for consumers (r1), low-severity contract notes, the measured operating cost s1 (not a correctness blocker), and the evolving receipt/synthetic-case work. **full-corpus acceptance is not cleared**: the external drive is absent, so the 6,560-game partition/reconciliation pass, original-source spot checks on real seasons and real resources remain open under `docs/issues/evidence-v1-01-acceptance.md`.

### status of pass-1 findings

| id | finding | status in frozen code | re-verification |
|---|---|---|---|
| d1 | goals had null episode context | **repaired.** `EventContext.live_episode_index` is now the episode active *before* the focal row; `chronology.episode_index` separately groups anchors and closures (`analysis_context._episodes`) | pre-event availability no longer depends on the focal outcome by construction; fixture census goal 189/195, save 1950/1951, miss 983/984, block 1108/1108. the six residual goals are r1 |
| d2 | coalesced runs invented starts/rest across unresolved spans | **repaired by redesign.** participation is now built from each person's own coherent native shift rows, gated by `feature_data.participation_coverage` (collection count, unique team, no toi/shift-count mismatch); uncertain own/unknown-player rows left-censor the start, censored starts withhold age, age cuts and rest | the pass-1 witnesses (`2022020009` p2 `[1104,1154)`, `2023020012` p3) now show own coherent rows ending at 1104 and restarting at 1154 (`8475906`: `1034–1104`, `1154–1200`); the unresolved interval is an `implausible_elapsed_lineup` caused by others, so the 50 s rest and faceoff start are source-supported, not fabricated |
| d3 | segment member outside `_people` | withdrawn (unreachable by construction) | — |
| d4 | unknown physical action labeled not applicable | **repaired.** unresolved on-net rows stay unavailable; outside-population rows are not applicable; opponent next attempt decides `false` without physical status | census: 14 unresolved → `unavailable`, 76 outside → `not_applicable`; synthetic cutoffs below |
| d5 | unclocked rows sorted to +inf | repaired before pass-1 closed | elapsed vs event prefix: 0 mismatches over ≈60k pairs (rerun) |
| d6 | small items | ledger literal and double attempt preparation remain cosmetic/operating; period-5 shootout assumption stays guarded by `02` game ids | not blockers |
| d7 | season name used boxscore abbreviation | **repaired.** roster first+last, latest dated game | reader census below |
| d8 | "ambiguous" for unknown adjacent membership | **repaired.** `relation == unavailable` → `membership_unavailable`/`horizon_unavailable` | `2024021235` now 110 `membership_unavailable`; `2024020186 /plays/319` and `2025021094 /plays/276` likewise |
| d9 | uncorroborated interior attempts left runs included | **repaired.** `affected_at` masks any run the attempt lies strictly inside, filtering by state only at boundaries | closure: 0 unresolved/excluded potential attempts strictly inside an included segment (all 36) |
| d10 | empty nets / own / awarded goals tainted goalie on-net totals | **repaired.** known empty (`[]` and no goalie role) and reported own/awarded goals neither count nor taint; goalie role must agree with membership | every goalie appearance: complete `on_net_faced` equals boxscore `shotsAgainst`; no residual "unresolved" taint in 36 games |
| s1 | ≈40–54 mb per game, mostly repeated evidence | **accepted operating cost, not a correctness blocker.** recorded by root in `docs/issues/prepared-evidence-size.md` (36-game artifact 1,936,299,469 bytes). changing it is a storage-schema amendment, correctly not done silently in this assignment | measured: one game parses in 0.38 s and validates in 2.0 s. extrapolation (≈350 gb, hours per full reader pass) is an estimate until the real run |

### residual findings (r6 is the only concrete correctness item; r1–r5 do not block this assignment)

**r6. overlapping own shift rows are unioned into "complete" participation (concrete correctness item, narrow; fix before refactor-green).** `analysis_context._player_shifts` merges any same-person rows with `start <= previous end`, and `feature_data.participation_coverage` demotes a player only on a `player_toi`/`player_shift_count` **mismatch**; an `unavailable` check passes. witness `2025020565` (every interval unresolved; 16,746 `repeated_shift_identity` and 6,895 `unresolved_shift_player` issues): defenseman `8482684` has rows `/data/1974` and `/data/1975` `[1144,1176)` (shift 18, record ids 15967428/15971560) and `/data/1976` `[1137,1176)` (shift 19), all `coherent` type 517. the union starts that span at 1137; his summed participation is 1603 s against boxscore toi 1596 s, his toi check is `unavailable` (observed null), and no row is left-censored. rechecked on the current code after root's 15:03 patches: coverage still `true`, 28 rows, 1603 s, 0 censored. across all 36 games (`probe_participation.py` on root-green): 1,261 uncensored players match boxscore toi exactly with a `match` check, 38 match exactly with an `unavailable` check, and this is the only uncensored disagreement; every `mismatch` player is censored. impact (corrected 15:20): not confined to `player_shifts`. the frozen `_prefix_workload(product=True, participation=player_shifts, participation_complete=...)` integrates all-strength `toi_all_seconds` from these spans, so on root-final the player's event prefix at `/plays/194` (p2 1144) reads `toi_all_seconds=928` as complete, 7 s above the 921 his agreeing rows support. no chunk or rate denominator is affected (the game has no segments), but event-context predictors were. smallest fix at the owner: treat strictly overlapping rows with different `(start,end)` for one person as uncertain (left-censor the merged span and withhold its start/rest), or require a `match` check rather than "no mismatch" before declaring individual coverage complete. exact duplicates (same span, repeated identity) can still collapse.

**r1. review-awarded goals are ordered after the stoppage that ends their episode (source-order caveat for consumers, medium-low).** with d1 repaired, the only ordinary attempts without a pre-event episode are goals whose verified `sort_order` places them *after* a same-clock stoppage: `2021020942 /plays/300→301` (stoppage `net-dislodged-by-goaltender`/`video-review`, then goal, both 13:49 p3), `2022020001 /plays/138→139` (`goalie-stopped-after-sog`, 01:24 p2), `2024020022 /plays/235→236` (`video-review`, 02:48 p3), `2025020006 /plays/182→183` (`video-review`, 14:47 p2). in each the goal's `event_id` is lower than the stoppage's, i.e. the goal was recorded first and re-sequenced after review. the code is faithful to the spec's verified source order, so this is not a v1-01 defect; but the pattern is goal-specific (4/195 ordinary goals ≈2 %, versus one save after an unclocked takeaway, `2024020102 /plays/360→361`, and one miss after a same-clock `puck-in-crowd` stoppage, `2024020404 /plays/203→204`, among ≈4,000 other ordinary attempts), so a chance head that consumes `live_episode_index` presence learns a small outcome signal. the decision belongs to the consumer specification (v1-05/v1-07): either forbid presence as a predictor, or declare an explicit rule such as "a goal immediately preceded by a same-clock review stoppage inherits that stoppage's closing episode". record it before those encoders exist.

**r2. `prior_shorthanded_side` counts skaters only (existing-owner semantics, low).** `feature_data._strength_transitions` sets `prior` whenever away and home skater counts differ, so an extra-attacker spell (6v5 goalie pulled) marks the opponent "shorthanded" and a return to 5v5 without a reset creates a transition. the spec says reuse the existing rule; in the all-strength product the field name overstates its meaning. rename or document it in the consumer contract; no code change required here.

**r3. `feature_facts.outcome` keeps the old longer-span outcome group inside the retained "feature" facts (spec-declared, low).** it contains next-event/stoppage/next-attempt facts, i.e. future information, beside predictor groups. the spec names it explicitly, so this is not drift, but v1-05/v1-07 must select predictor families by name and never take `feature_facts` wholesale.

**r4. contract notes (low).** `PersonValues.identity_observations` is `NotRequired` although the spec says absence is never an omitted key; the spec's segment table names "exact state, source status" that the closed `segment` shape omits (state is derivable from the four lists). harmless, but say which text wins.

**r5. evolving, needed before root closes the boundary.** `docs/research/evidence-v1-01/verification.md` does not exist yet (the size issue already links it). the spec's labeled synthetic cases (missing boundary combinations, actual 3/4/5/6-member arithmetic, equal-clock ordering, exact stop/reattempt cutoffs) are not in `analysis/.temporary-v1-01/test_artifacts.py`; my reviewer probes cover cutoffs synthetically and member arithmetic on real fixture states, which root may cite, but the receipt should record which evidence closes each item.

### final independent checks

all under `var/v1-01-root/claude-review/`; reruns use `PYTHONPATH=analysis/src` with the main venv interpreter, verified to import the worktree package.

- **owner parity.** `parity_reconstruct.py`: HEAD `reconstruct_game` + `five_on_five_segments` versus the working tree, all 36 fixture documents, byte-identical json (module paths printed to confirm two different copies loaded). observed/research reducer parity on the three displayed seasons is root's check; I did not rerun it.
- **strict readers and preparation rejections.** `tamper_checks.py` on my own two-game artifact (`small-out`, prepared through `prepare_analysis`): baseline accepted; rejected — changed member bytes, extra game key, `NaN`, unbound evidence `input_ref`, null without problem, negative count, extra manifest key, missing member, cross-wired members, `../` member path, negative resource, purpose relabeled real, changed selection copy, missing manifest, read-as-real; preparation rejects unknown key, duplicate game, duplicate season, boolean schema version, corpus hash mismatch, fixture relabeled real, fixture with `game_ids:null`, duplicate json key and occupied output. output-inside-input was deliberately not exercised to avoid writing into root's inputs; the guard was read in `prepare_analysis`.
- **immediate labels, synthetic** (`synthetic_labels.py`): stop at 2 s true, 3 s false, unknown stoppage reason null/unavailable; reattempt at 5 s true, 6 s false; opponent unresolved next attempt false; same-team unresolved next null/unavailable; invalid next row and last row without terminal both unavailable; equal-clock hit false with delay 0.
- **public-reader pass on root-green** (`final_checks.py`, output `final-checks-1.json`; 213 s, 7.5 gb rss because the probe holds all 36 games): `read_prepared` → 36 `read_prepared_game`, 5 `read_prepared_people`, `read_prepared_coverage` all validate with the current readers. an `open` audit hook saw **no file opened outside the artifact** by the readers (the only outside path was my own selection read): no source reopen. imports pull `numpy`/`scipy` transitively through `shot_origins` (via `feature_data`) but no fitting, publication or network module; harmless, noted only for import cost.
  - retention: all 36 games keep `events[].source` identical to the original interpreted events (keyed by source index); 11,623/11,623 successor links are mirrored by predecessor links.
  - closure: 3,320/3,320 included attempts sit in a chunk containing their clock (or the run's final child at run end); no unresolved/excluded potential attempt lies strictly inside an included segment.
  - coverage reconciliation: 53/53 exact-state time rows equal my independent sums of segment physical and included seconds; per-season event `(kind,outcome)` rows equal my counts in all 5 seasons; selected/status counts 7/5/6/9/9, all `reconstructed`, inventories 1,312.
  - participation after unresolved spans: 1,623 uncensored rows start where an unresolved interval ends (657 faceoff, 966 on-the-fly), 5 unknown. by the own-row toi comparison above these are source-supported except r6.
  - downstream readiness without sources: 4,236 ordinary execution attempts, all with event pre-score; 927 of them lack matched elapsed support and still survive as event evidence (the spec's independence); 36,392 included chunks, 104,833 included seconds.
  - people: 1,252 season persons, 0 abbreviated names, 0 null groups, 0 null age-days, `height_cm` null for all (unit limitation).
  - manifest: 5 corpora, 20/20 reference captures/bodies, 36 envelopes, 216/216 source captures/bodies bound; resources wall 170 s, peak 1.55 gb, output 1,936,652,364 bytes for 36 games.

### root-final (pre-r6) — 15:16 pdt

frozen code `snapshot-3/` (15:09), artifact `var/v1-01-root/root-final` (manifest sha256 in `claude-review/root-final-manifest.sha256`). superseded by the post-r6 build; recorded because the facts carry over except where r6's repair touches `player_shifts`.

- `final_checks.py` (`final-checks-2.json`): identical outcomes to root-green: 36/36 games read, events identical, 11,623/11,623 mirrored links, readers opened nothing outside the artifact, 3,320/3,320 included attempts in a containing chunk, 53/53 time rows and 5/5 event tables reconcile, 4,236 execution rows (927 without elapsed support), 1,252 people with no abbreviated name. no network or non-numeric third-party imports. manifest resources: 157 s wall, 0.99 gb peak, 1,936,749,246 output bytes.
- `probe_participation.py` (`probe-participation-2.txt`): r6 persists exactly as reported (`2025020565`/`8482684`, 1603 vs 1596 s, `unavailable` check, uncensored); all other 1,299 uncensored players match boxscore toi.
- frozen-code reruns: `tamper-2.json` 24/24 corruptions and bad selections rejected (baseline accepted); `parity-2.json` HEAD vs frozen reconstruction identical on 36; `synthetic-labels-2.txt` unchanged; `probe-prefixes-3.jsonl` 75 goalie appearances with known on-net totals all equal boxscore `shotsAgainst`, no taint, 0 mismatches over 59,628 elapsed/event prefix pairs.
- final repairs read: missing raw block coordinate pair now gives `location_kind=unavailable` while a present pair keeps `block_contact` (`_attempt_details`); unknown shift kinds (not 517/505) left-censor participation and demote coverage; direct one-game history uses the interpreted `/game` locator. consistent with the spec.

r1–r3 stay **consumer-contract caveats** for v1-05/v1-07 (and r2 for any strength-transition consumer), not producer fixes.

### r6 repair read — 15:20 pdt (source only; post-fix artifact pending)

diff vs `snapshot-3`: new `feature_data.individual_participation(shift_records)` groups coherent 517 rows by `(player, period)` and exact bounds, walks bounds in order and closes a component when `start >= running end`; a component with one distinct bound set is supported (exact duplicates collapse), more than one is a conflict. `participation_coverage` marks any conflicted player incomplete; `_player_shifts` builds spans only from supported rows and adds a game issue `overlapping_individual_participation` with evidence on every conflicting row. research paths do not call either function (grep), so old defaults are untouched.

`probe_r6.py` (`probe-r6-1.txt`), current code: synthetic controls give exact duplicates → supported, touching `[10,40)+[40,70)` → supported, strict overlap and nesting → conflict, an overlap followed by a clean row → only the clean row supported, another player unaffected. witness `2025020565`/`8482684`: coverage `false`; 27 spans, 1,564 s, all 27 left-censored; the p2 conflict component is omitted (last p2 span `[1054,1103)`); event prefix at `/plays/194` now `toi_all_seconds=null` ("complete individual source participation unavailable") with `known_toi_all_seconds=921`. four overlap issues in that game.

judgement: correct and minimal. two low notes, not blockers: (a) the omitted component drops even the span all conflicting rows agree on (`[1144,1176)`), so `known_*` lower bounds are looser than necessary; (b) the overlap issue names the player only in message text and is not linked from that player's `player_shifts[].issue_indices`, so a consumer summing spans must notice incompleteness through `participation_start_left_censored` on every row or by parsing the game issue. still to do: rerun `probe_participation.py`, `final_checks.py`, `tamper_checks.py` on the post-fix manifest.

### remaining before root closes the detached boundary

1. r6: repair in progress at the coverage owner (root, 15:17). reviewer will read the diff and rerun `probe_participation.py`, `final_checks.py` and `tamper_checks.py` on the post-fix manifest.
2. `docs/research/evidence-v1-01/verification.md`, citing which evidence closes each spec acceptance row, including the synthetic-case items (r5) and root's observed/research parity receipts (`observed-before/after`, `research-before/after`).
3. record r1–r3 as consumer-contract notes where v1-05/v1-07 will read them (issue or spec note), not as v1-01 code changes.
4. delete `analysis/.temporary-v1-01/` after final checks, per the testing policy.

not cleared here: the five-season `real` preparation (6,560 games), its partition/reconciliation, real original-source spot checks, real runtime/memory/storage and the s1 capacity decision. those stay with `docs/issues/evidence-v1-01-acceptance.md` and `docs/issues/prepared-evidence-size.md`.

## pass 1 — reading the owners and the emerging composition (historical; superseded by the final review above)

### d1. goals lose their live episode; outcome-dependent predictor missingness (defect, high)

`analysis_context._episodes` (analysis_context.py:205-249) closes the active episode when it meets any `RESETS` row and only then assigns `event_episode[index]`. `goal` is in `feature_data.RESETS` (feature_data.py:12-15) and not in `ACTION_KINDS`, so every goal gets `live_episode_index=None` and `chronology.episode_index=None`, while every save/miss/block in the same live span gets a value. penalties called during play behave the same way.

consequence: the null pattern of an event-context field is a function of the outcome. any execution/attribution consumer that uses episode presence or episode age as a predictor learns "null ⇒ goal". this is the exact leakage class the spec forbids ("these future labels never enter predictor records"), entering through missingness rather than a value.

fixture witness (probe p2, `claude-review/probe-context-1.json`): across all 36 games, attempts with a non-null `live_episode_index` are `save 1951/1951`, `block 1108/1108`, `miss 984/984`, `goal 0/195`. the missingness is perfectly separable by outcome.

fix at the owner: a reset row belongs to the episode it terminates. assign the episode before closing it (the closing row is `end_source_index`), and let only the *next* faceoff/anchor open a new one. a regression check: within any episode, the set of attempt outcomes with non-null `live_episode_index` must include goals whenever goals end episodes.

### d2. coalesced participation invents starts, ages and rest across unresolved spans (defect, high)

`_player_shifts` (analysis_context.py:270-299) builds a player's coalesced run from resolved intervals only and skips `classification == "unresolved"`. a player continuously on ice through an unresolved native span therefore gets a *new* participation row whose start is the gap's end. that fabricated start then:

- may be classified `on_the_fly` (strictly inside some episode, :352-363) or `faceoff` (:337-351), both claiming a proven start;
- drives chunk `shift_age_seconds` (:810-813) and the `0,10,20,40,60,90` age cuts (:668-674);
- overwrites deployment `age_seconds`/`start_type`/`previous_shift_gap_seconds` for attempts (:863-870);
- yields a finite `rest_seconds` (:314) across the gap, even though the player may never have left.

spec: "unknown native spans remain identified gaps", "no team-average invented shift", "unknown order/kind/timing ends continuity". the gap must left-censor the following run: start kind `unknown`, age/rest null with an unavailable problem (a lower bound may be kept under a separately named field if ever wanted). same treatment when a run starts after an unsupported horizon or at a missing span that is not period start.

fixture witness (probe p3, `claude-review/probe-gaps-1.jsonl`): `2022020009` period 2 has one unresolved interval `[1104,1154)` (all four membership lists null). skaters `8475906` (D) and `8477505` (C) are members of the resolved interval ending at 1104 *and* the one starting at 1154. each receives a new participation row at 1154 with `start.kind="faceoff"`, `rest_seconds=50` (the unresolved span itself, reported as rest) and chunk `shift_age_seconds=0`. `2023020012` period 3 `[1040,1050)` repeats this for `8474102`, `8475287`, `8478507` (`rest=10`, faceoff start, age 0). fifteen of 36 fixture games contain post-gap rows (e.g. `2025020544` 775, `2025020184` 40).

### d3. withdrawn — segment members outside `_people`

withdrawn at 15:10 after reading the interval builder: `reconstruct_game` places a shift row in an interval only through `identities[row["player_id"]]` from `roster_identities` (reconstruct.py interval loop, `identity = identities[row["player_id"]]`), and every unresolved interval has all four lists null by construction. roster-identified ids are a subset of `_people`, so the `KeyError` below is unreachable today. it remains a fragile coupling, not a defect; the original note follows for the record.

`prepare_game` reads `prefix[str(player)]` for every segment member (analysis_context.py:814). `_prefix_workload` only emits players in `_people` identities (`reported & identities.keys()`, feature_data.py prefix loop). `_people` is roster ∪ boxscore; segment membership comes from shift charts. a shift-only id (the case `analysis_support` already names `membership_unavailable`) raises `KeyError` and aborts the whole preparation instead of yielding a located null. spec: "membership and time do not disappear because a predictor is missing". emit an unavailable `PrefixFacts` for such members. `unit_workload` already tolerates it via `.get`; the member loop does not.

### d4. immediate labels: unknown physical action becomes "not applicable" (defect, medium)

`immediate_outcomes` (analysis_context.py:91-106) treats every `details.outcome != "save"` as not applicable. `_attempt_details` sets `outcome=None` whenever the physical action is unresolved (kind-valid timed shot with null clock, goal with unreported modifier, :452-468). those rows are then labeled `not_applicable` for both heads, and coverage counts them as such (`_coverage_game`), overstating label completeness. spec: "unknown ordering/timing remains unknown"; "undecidable links are null/unavailable". branch on `physical_status`: `outside_population` → not applicable; `unresolved` on-net/unknown kind → unavailable; only a known miss/block/goal → not applicable (goal keeps `recorded_goalie_stop=false` when ordinary).

fixture witness (probe p2): 18 attempts with `physical_status="unresolved"` carry `reattempt_within_5s=null` with problem status `not_applicable`; only one ordinary save is correctly `unavailable`.

two smaller label points, same function:

- penalty-shot saves (`physical_status="outside_population"`, `outcome="save"`) receive computed labels. defensible as raw fact, but then the population note must say labels exist outside ordinary play; otherwise set not applicable. pick one explicitly.
- next row is an opposing-team attempt with `physical_status="unresolved"` (:142-155): the label stays null although team alone decides `false`. spec: "require only facts necessary to decide each label".

### d5. elapsed sequence placement of unclocked rows (fixed during review)

the first snapshot sorted unclocked rows to `+inf`, silently restoring completeness for every later chunk marker. the current code (analysis_context.py:728-748) pins an unclocked row to its verified predecessor's clock. resolved; listed so the final review re-checks that `_strength_transitions(product=True)` and `incomplete_faced` see it in that position.

### d7. season display name is the boxscore abbreviation, not the observed resolution (defect, medium)

`analysis_data._people_observations` takes `values["name"] or first+last`. `values["name"]` is `_people`'s boxscore `name`, which is the abbreviated form: the first `2025020001` boxscore player row reads `"R. Donato"` while the same id's roster row reads `"Ryan"`/`"Donato"`. the spec fixes the season name as "the latest supported dated game identity under the existing observed name resolution"; that owner (`observed.py:816-821`) uses roster `first_name + " " + last_name`, carrying the previous name forward when the latest lacks one. the product would therefore show different names from the active observed publication for the same person. reuse the roster first/last rule (preferably by lifting it from `observed.py`, not by a third copy).

### d8. assignment-failure reasons collapse "unknown adjacent membership" into "ambiguous" (defect, medium-low)

`prepare_support` codes every corroborated-but-unassigned attempt `ambiguous_assignment` (analysis_support.py, unassigned branch), whether `membership_interval_link` returned `neither`/multiple runs (genuinely ambiguous) or `unavailable` because a required adjacent interval is unresolved, absent or past an unknown horizon. witness: `2024021235` (successful empty shift response, zero segments) yields 110 `ambiguous_assignment` reasons and 110 `unresolved` attempts; nothing is ambiguous there, elapsed membership simply does not exist. `2024020186` goal `/plays/319` at p3 1163 and `2025021094` goal `/plays/276` at p3 830 are excluded as "ambiguous" because the following interval is unresolved. the receipt is supposed to say what each source supports and what remains unknown; use `membership_unavailable` (or `horizon_unavailable`) for `relation == "unavailable"` and keep `ambiguous_assignment` for `neither`/multi-run cases.

### d9. uncorroborated interior attempts can sit unassigned inside an included run (design gap, medium-low)

`affected_at` filters touching runs by exact state whenever a checked report membership exists, including for interior positions. an uncorroborated attempt (valid report membership, but `penalty_shot` unavailable, non-unique report match or non-`matched` native status) whose reported state differs from the run it lies strictly inside leaves that run `included` while the attempt stays `unresolved`. if the report's state is the wrong one, the run's counts silently miss an attempt; rule 3's state restriction is written for *boundary* attempts with no unique match. for interior positions, an unassigned potential attempt should mask the run it lies in regardless of state (state filtering only decides which *boundary* neighbors are relevant). count-time closure check to add at final review: no potential attempt with disposition `unresolved` lies strictly inside an included segment.

### d10. known empty nets and resolved own/awarded goals poison goalie `on_net_faced` (defect, medium)

`feature_data._prefix_workload(product=True)`, on-net update branch: `physical` is true only for shots and goals whose modifier is `reported` `none|penalty-shot`. empty-net goals carry `goal_modifier_evidence={"status":"unsupported","reported_value":"empty-net"}` with defending goalies `[]`, so `physical and goalie_members == []` is false and the `elif` marks the defending goalie incomplete for the rest of the game. resolved `own-goal`/`awarded` goals with a goalie present do the same. spec: "excluding shootouts/known empty nets"; only *unresolved* physical action or goalie identity leaves a total incomplete.

fixture witness (probe p4, `claude-review/probe-prefixes-1.jsonl`): `known_on_net_faced` equals boxscore `shotsAgainst` for every goalie appearance in all 36 games (good: the counting rule is right), but `on_net_faced` is withheld after `2021020001 /plays/292` and `2024020186 /plays/302` (empty-net goals, defending goalies `[]`) and after `2022020547 /plays/244` and `2025020282 /plays/282` (reported own goals, goalie present). fixture modifier census: 14 empty-net, 3 own-goal, 1 awarded among 236 goals, so roughly one goalie in four loses a complete late-game workload.

fix: decide on membership first. defending goalies `[]` → skip. one identified goalie and a *resolved* non-ordinary modifier (`own-goal`, `awarded`, `empty-net` with a goalie somehow present) → neither count nor taint, matching boxscore. taint only on unknown membership, unmatched/unavailable modifier or unresolved identity.

### s1. game artifacts are ≈42 mb, mostly repeated evidence; five-season output ≈285 gb (design/systems, high for the real handoff)

measured on the four games p1 wrote before failing (`claude-review/out-1/games/20212022/*.json`, compact separators already applied; that partial reviewer output was deleted after measurement): 38–50 mb each, mean 43.5 mb. breakdown of `2021020001` (42.2 mb): `chunks` 20.6 mb (919 chunks, ≈20 kb each, almost all `member_contexts`), `attempts` 12.3 mb, `events` 6.0 mb (`context.prefix_by_player` ≈16.6 kb per event). by content: `evidence` arrays 26.0 mb (62 %), `problems` 5.8 mb (14 %). there are 104,582 inline `input_ref` objects, each repeating the same absolute envelope path and sha256, attached to collection-level pointers such as `{"source":"reconstruction","path":"/intervals"}` or `/plays` that locate nothing more specific than the game.

reading cost: `strict_json` 0.38 s plus `validate_game` 2.03 s for that one file. at 6,560 games: ≈285 gb written, ≈4.4 h just to parse/validate once per consumer pass, and preparation pays the same validation again before each write. none of this is a correctness failure, and wider facts are an accepted cost, but this magnitude was not priced by the spec and makes v1-03/05/08 iteration slow and the external drive the bottleneck.

the representation, not the scope, is at fault. evidence carries no information beyond "this game's envelope, that collection" while costing most of the bytes. options at the right layer, cheapest first: (1) a per-game `evidence` table (or input table plus `Evidence.input_index`, which `analysis_records.Evidence` already declares) referenced by index from facts; (2) game-scoped evidence for collection-wide facts such as prefixes, units and transitions, with per-fact evidence only where a fact cites a specific row; (3) problem reasons as a closed code vocabulary. the spec's "evidence includes immutable input identity and source pointer" is satisfied by a table reference. decide before the five-season pass, because the artifact schema is the contract every later handoff reads.

### d6. smaller items (low)

- `analysis_support.prepare_support` report-only loop hardcodes `period_number == 5` as shootout (analysis_support.py, report-only loop). safe only because selection forces `02` game ids; say so in the code or use the report's period type.
- `analysis_context.prepare_game` hardcodes `ledger: {"status": "available"}` (:974); `GameStatus` has no `available` and `prepare_analysis` overwrites it afterwards. dead, misleading literal; drop it or pass the ledger in.
- `prepare_game` calls `scoring_credits(..., consumed=[])` (:964), discarding the credit reader's consumed receipts. `_bind_sources` already binds the same play-by-play/landing captures, so provenance survives; still, preparation reopens raw capture bodies a second time per game during composition. acceptable at preparation time (readers never reopen), but the duplicate read path should be one owner.
- `prepare_analysis` runs `prepare_game_attempts` twice per game (`game_summary` pass, then compose). correct, roughly doubles the attempt-preparation share of wall time on 6,560 games.

## probes

- p2 `probe_context.py` (composition without artifact validation, all 36 games): every game composes; `len(events) == len(interpreted.events)` in all 36 (no dropped or duplicated source rows at the composition layer).
- p3 `probe_gaps.py`: d2 witnesses.
- p4 `probe_prefixes.py`: goalie known on-net totals reconcile to boxscore `shotsAgainst` everywhere; at chunk-left clocks the elapsed prefix never exceeds the same-clock event prefix in known attempts and equals it in known toi (≈62k member/event pairs, 0 mismatches). `2024021235`, `2025020544`, `2025020565` produce no pairs (no segments or no aligned starts), so this check is silent there.
- p5 `probe_support.py` on the named cases: `2024020186` excludes the 02d run `[657,703)` (5v5, two `strength_conflict` reasons) plus a 3-second 6v5 run `[1160,1163)`; `2022020822` goal `/plays/93` (p2 116, relation `after`) keeps event pre-score 0–1 while its assigned child `[116,118)` carries 1–1, i.e. the specified incoming-goal exception; `2025021094` penalty-shot goal `/plays/164` is `not_applicable`, the short-ot goal `/plays/304` is included in `[40,41)`; `2024021235` has zero segments and 110 unresolved attempts with no time removed (see d8 for their reason code).
- p6 `probe_closure.py` (all 36): no `unresolved`/`excluded` potential attempt lies strictly inside an included segment; every included event lies within its segment; chunk `away_unit`/`home_unit.member_count` equals the parent's actual skater count in all 42,455 chunks across 15 exact states (3v3 … 6v5, 4v6 empty-net), and complete means equal known sums divided by actual count. label census: ordinary saves 474 `recorded_goalie_stop=true`, 1,477 `false`, none unknown; 593 `goalie-stopped-after-sog` stoppages exist, so 119 are not immediate 0–2 s successors of a save (plausible; spot-check at final review).
- p1 (14:44): `prepare --selection claude-review/selection.json --out claude-review/out-1` on the 36-game fixture selection: exit 1 after 31.6 s, peak rss 637 mb, `game/player_shifts/552/start: null fields must have exactly one located problem`. no manifest was written; directory is unreadable as intended. this is the in-progress context/artifact integration, not a new finding.

## delivery cleanup

root retained this review and compact final probe results after final green. temporary probes and source snapshots named above were deleted; `test-deletion.json` records their identities. `source-freeze.json` retains the final production-source identities.
